"""Local production service shared by CLI, HTTP and existing MRL Bridge execution."""
from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path

from . import __version__
from .audit import audit_media, package, verify_package, write_json
from .model import VideoError, digest, file_digest, local_file, dimensions
from .cache import SceneCache
from .render import Cancelled, Runner, render
from .store import Store


class Service:
    """One bounded production worker per storage root; jobs survive restarts."""

    def __init__(self, root: Path, source_root: Path, font: Path, workers: int = 2, law: Path | None = None, timeout: int = 21600):
        self.store = Store(root)
        self.timeout = max(60, min(timeout, 86400))
        self.source_root = source_root.resolve()
        self.font = font.resolve()
        self.law = law.resolve() if law else None
        self.workers = max(1, min(workers, 4))
        self.stop = threading.Event()
        self.thread = None
        self.lock = self.store.root / "MRL_worker.lock"
        self.lock_fd = None

    def start(self) -> None:
        """OS-held single-writer lock, released by the kernel after a crash."""
        if self.thread is not None:
            raise VideoError("Worker already started")
        self.lock_fd = os.open(self.lock, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            # Lock byte zero on Windows and the entire file on Unix.
            if os.name == "nt":
                import msvcrt
                os.lseek(self.lock_fd, 0, os.SEEK_SET)
                msvcrt.locking(self.lock_fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.lock_fd)
            self.lock_fd = None
            raise VideoError("Another production worker owns this storage root") from None
        try:
            os.ftruncate(self.lock_fd, 0)
            os.write(self.lock_fd, str(os.getpid()).encode())
            os.fsync(self.lock_fd)
            self.store.recover()
            self.thread = threading.Thread(target=self.loop, daemon=False)
            self.thread.start()
        except BaseException:
            self._unlock()
            raise

    def _unlock(self) -> None:
        if self.lock_fd is not None:
            # Do not unlink the stable lock inode: an already-open contender could
            # otherwise hold a different inode and become a second writer.
            if os.name == "nt":
                import msvcrt
                os.lseek(self.lock_fd, 0, os.SEEK_SET)
                msvcrt.locking(self.lock_fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            os.close(self.lock_fd)
            self.lock_fd = None

    def close(self) -> None:
        self.stop.set()
        if self.thread:
            self.thread.join()
        self._unlock()

    def loop(self) -> None:
        while not self.stop.is_set():
            jid = self.store.claim()
            if jid:
                self.process(jid)
            else:
                self.stop.wait(.25)

    def process(self, jid: str) -> None:
        """Never overwrite a prior artifact directory; failures retain partial work."""
        work = self.store.root / jid
        runner = Runner(lambda: self.stop.is_set() or bool(self.store.get(jid)["cancel_requested"]), self.timeout)
        try:
            work.mkdir(exist_ok=False)
            if not self.store.verify_chain():
                raise VideoError("Event chain integrity failure")
            request = self.store.request(jid)
            longfilm = request["schema"] == "MRL_LongFilm_Request/v1"
            write_json(work / "request.json", request)
            write_json(work / "storyboard.json", request["scenes"])
            snapshots = work / "sources"
            snapshots.mkdir()
            provenance = []
            for source in request["sources"]:
                name = f"sources/{source['id']}.txt"
                data = source["text"].encode("utf-8")
                (work / name).write_bytes(data)
                provenance.append({"id": source["id"], "original_name": source["original_name"],
                                   "locator": source["locator"], "snapshot": name,
                                   "sha256": digest(data), "size": len(data)})
            assets = work / "assets"
            assets.mkdir()
            asset_rows = []
            names = sorted({s[k] for s in request["scenes"] for k in ("image", "clip", "narration") if s.get(k)})
            input_root = self.source_root
            parent = self.store.get(jid)["parent_id"]
            prior_assets = {}
            if longfilm and parent and self.store.request(parent) == request:
                prior = self.store.root / parent
                if (prior / "provenance.json").is_file():
                    prior_assets = {r["original_name"]: r for r in json.loads(
                        (prior / "provenance.json").read_text(encoding="utf-8"))["assets"]}
                    input_root = prior / "assets"
            for name in names:
                runner.check()
                original = local_file(input_root, name, 2 * 1024 ** 3)
                if name in prior_assets and file_digest(original) != prior_assets[name]["sha256"]:
                    raise VideoError("Parent asset integrity failure")
                destination = assets / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    with original.open("rb") as source:
                        shutil.copyfileobj(source, stream, 1024 * 1024)
                if destination.stat().st_size > 2 * 1024 ** 3:
                    raise VideoError("Asset exceeds budget")
                asset_rows.append({"original_name": name, "snapshot": "assets/" + name,
                                   "sha256": file_digest(destination), "size": destination.stat().st_size})
            write_json(work / "provenance.json", {"sources": provenance, "assets": asset_rows,
                       "captions": [{"scene": i + 1, "source_id": s["source_id"],
                                     "quote": s["caption"]} for i, s in enumerate(request["scenes"])],
                       "titles": "operator-supplied or template editorial labels; not verified source claims"})
            expected = ["request.json", "storyboard.json", "provenance.json", "layout.json", "metadata.json",
                        "subtitles.srt", "soundtrack.wav", "concat.txt", "explainer.mp4",
                        "explainer-preview.gif", "explainer-stills.png", "MRL_audit.json", "MRL_manifest.json"]
            if longfilm:
                expected.remove("soundtrack.wav")
                expected.append("timeline.json")
            law_sha = None
            if self.law is not None:
                data = self.law.read_bytes()
                if not data or len(data) > 1024 * 1024:
                    raise VideoError("Invalid canonical law file")
                (work / "core").mkdir()
                (work / "core/law.md").write_bytes(data)
                law_sha = digest(data)
                expected.append("core/law.md")
            expected += [row["snapshot"] for row in provenance + asset_rows]
            if longfilm:
                expected += [f"segment_{i+1:03}.mkv" for i in range(len(request["scenes"]))]
            expected += [f"{prefix}_{i + 1:02}.{ext}" for i in range(len(request["scenes"]))
                         for prefix, ext in ((("scene", "png"), ("review", "png")) if longfilm else
                                             (("scene", "png"), ("scene", "mp4"), ("review", "png")))]
            def phase(value):
                runner.check()
                self.store.update(jid, "RUNNING", value)
            if longfilm:
                from .longfilm import render_longfilm
                details = render_longfilm(request, work, assets, runner, phase, self.store, jid, self.workers)
            else:
                details = render(request, work, self.font, assets, runner, phase, self.workers,
                                 SceneCache(self.store.root / "MRL_scene_cache"))
            write_json(work / "layout.json", details)
            job = self.store.get(jid)
            metadata = {"module": "MRL_Video", "module_version": __version__,
                        "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
                        "job_id": jid, "version_index": job["version_index"],
                        "version_string": job["version_string"], "parent_id": job["parent_id"],
                        "request_sha256": job["request_sha256"], "profile": request["profile"],
                        "source_commit": request.get("source_commit"), "font_sha256": details["font_sha256"],
                        "renderer": "CPU/libx264", "external_network_calls": 0,
                        "law_sha256": law_sha, "law_binding": "HASHED_LOCAL_SNAPSHOT" if law_sha else "NOT_CONFIGURED",
                        "dl580_acceptance": "NOT_RUN", "iphone_acceptance": "NOT_RUN",
                        "deployment": "NOT_DEPLOYED", "dimensions": details.get("dimensions", list(dimensions(request))),
                        "fps": details.get("fps", 24), "cache_hits": details["cache_hits"]}
            write_json(work / "metadata.json", metadata)
            phase("AUDIT")
            result = audit_media(work, request, expected, runner)
            write_json(work / "MRL_audit.json", result)
            phase("PACKAGE")
            receipt = package(work, expected, self.store.root / f"{jid}.zip", metadata)
            write_json(self.store.root / f"{jid}.receipt.json", receipt)
            runner.check()
            if not self.store.verify_chain():
                raise VideoError("Event chain integrity failure")
            self.store.update(jid, "SUCCEEDED", "DELIVERY_PASS")
        except Cancelled:
            self.store.update(jid, "CANCELLED", "CANCELLED")
        except Exception as exc:
            # Do not persist arbitrary exception text containing local paths or secrets.
            message = str(exc) if isinstance(exc, VideoError) else type(exc).__name__
            self.store.update(jid, "FAILED", "DELIVERY_FAIL", message)

    def artifact(self, jid: str, name: str) -> Path:
        """Only serve successful, allowlisted artifacts, rechecking payload integrity."""
        if self.store.get(jid)["state"] != "SUCCEEDED":
            raise VideoError("Artifacts are not accepted")
        if name == "package.zip":
            path = self.store.root / f"{jid}.zip"
            verify_package(path)
            return path
        allowed = {"explainer.mp4", "explainer-preview.gif", "explainer-stills.png",
                   "subtitles.srt", "MRL_audit.json", "MRL_manifest.json"}
        if name not in allowed:
            raise VideoError("Artifact unavailable")
        root = self.store.root / jid
        manifest = json.loads((root / "MRL_manifest.json").read_text(encoding="utf-8"))
        path = root / name
        if name == "MRL_manifest.json":
            verify_package(self.store.root / f"{jid}.zip")
            with __import__("zipfile").ZipFile(self.store.root / f"{jid}.zip") as archive:
                if path.read_bytes() != archive.read(name):
                    raise VideoError("Manifest readback mismatch")
        else:
            row = next(row for row in manifest["files"] if row["path"] == name)
            if file_digest(path) != row["sha256"]:
                raise VideoError("Artifact readback mismatch")
        return path

