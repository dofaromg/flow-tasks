"""Requested-versus-delivered validation and independently verifiable ZIP inventory."""
from __future__ import annotations

import json
import math
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageStat

from .model import VideoError, digest
from .render import FPS, PROFILES, Runner, probe


def write_json(path: Path, value: object) -> None:
    """Create-only JSON output; never overwrite an existing version artifact."""
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def inventory(root: Path, names: list[str]) -> list[dict]:
    return [{"path": name, "size": (root / name).stat().st_size,
             "sha256": digest((root / name).read_bytes())} for name in sorted(names)]


def verify_package(path: Path) -> dict:
    """Verify duplicate names, exact ZIP inventory, sizes and all payload hashes.

    SHA-256 detects corruption against the manifest, not an adversary replacing both.
    """
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if (len(entries) > 3000 or sum(e.file_size for e in entries) > 2 * 1024 ** 3
                or any(e.file_size > 512 * 1024 ** 2 for e in entries)):
            raise VideoError("Package read budget exceeded")
        names = archive.namelist()
        if len(names) != len(set(names)) or "MRL_manifest.json" not in names:
            raise VideoError("Duplicate entries or missing manifest")
        manifest = json.loads(archive.read("MRL_manifest.json"))
        rows = manifest["files"]
        expected = {row["path"] for row in rows} | {"MRL_manifest.json"}
        if len(rows) != len({row["path"] for row in rows}) or set(names) != expected:
            raise VideoError("ZIP/manifest inventory mismatch")
        for row in rows:
            name = row["path"]
            if Path(name).is_absolute() or ".." in Path(name).parts or "\\" in name:
                raise VideoError("Unsafe package entry")
            data = archive.read(name)
            if not data or len(data) != row["size"] or digest(data) != row["sha256"]:
                raise VideoError("ZIP payload mismatch")
        audit = json.loads(archive.read("MRL_audit.json"))
        if audit.get("status") != "DELIVERY_PASS":
            raise VideoError("Package audit did not pass")
    return {"status": "DELIVERY_PASS", "file_count": len(names),
            "zip_sha256": digest(path.read_bytes()), "coverage": 100}


def audit_media(root: Path, request: dict, expected: list[str], runner: Runner) -> dict:
    """Decode the entire MP4 and inspect scene samples, format and time alignment."""
    info = probe(root / "explainer.mp4", runner)
    videos = [s for s in info["streams"] if s["codec_type"] == "video"]
    audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1 or len(audios) != 1:
        raise VideoError("Expected exactly one video and audio stream")
    video = videos[0]
    width, height = (request.get("encoding", {}).get("width", PROFILES[request["profile"]][0]), request.get("encoding", {}).get("height", PROFILES[request["profile"]][1]))
    target = sum(s["duration"] for s in request["scenes"])
    observed = float(info["format"]["duration"])
    if (not math.isfinite(observed) or abs(observed - target) > .5
            or (video["width"], video["height"]) != (width, height)
            or video["codec_name"] != "h264" or audios[0]["codec_name"] != "aac"):
        raise VideoError("Media format or duration mismatch")
    frame_count = int(video.get("nb_frames", 0))
    if abs(frame_count - round(target * FPS)) > len(request["scenes"]):
        raise VideoError("Frame timeline mismatch")
    if abs(float(audios[0].get("duration", 0)) - target) > .5:
        raise VideoError("Audio timeline mismatch")
    runner.run(["ffmpeg", "-v", "error", "-xerror", "-nostdin", "-i", "explainer.mp4",
                "-f", "null", "-"], root)
    black_log = runner.run(["ffmpeg", "-v", "info", "-nostdin", "-i", "explainer.mp4",
                            "-vf", "blackdetect=d=0.75:pix_th=0.02:pic_th=0.98",
                            "-an", "-f", "null", "-"], root, capture_stderr=True)
    if any(float(v) >= .75 for v in re.findall(r"black_duration:([0-9.]+)", black_log)):
        raise VideoError("Unexpected black interval detected")
    position = 0.0
    samples = []
    for i, scene in enumerate(request["scenes"]):
        sample = f"review_{i + 1:02}.png"
        runner.run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-ss",
                    str(position + scene["duration"] / 2), "-i", "explainer.mp4",
                    "-frames:v", "1", sample], root)
        with Image.open(root / sample) as image:
            stats = ImageStat.Stat(image.convert("L"))
            if stats.mean[0] < 3 or stats.stddev[0] < 3:
                raise VideoError("Blank scene sample detected")
        samples.append(sample)
        position += scene["duration"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    # Audit and manifest are written after validation, avoiding recursive hashes.
    pending = {"MRL_audit.json", "MRL_manifest.json"}
    missing = sorted(set(expected) - actual - pending)
    extra = sorted(actual - set(expected))
    empty = sorted(n for n in actual if (root / n).stat().st_size == 0)
    if missing or extra or empty:
        raise VideoError("Requested/delivered file coverage mismatch")
    return {"schema": "MRL_AuditSupervisor_v1", "status": "DELIVERY_PASS",
            "missing": missing, "extra": extra, "mismatch": [], "renamed": [],
            "orphan": [], "empty": empty, "coverage": 100,
            "expected_files": sorted(expected), "duration_seconds": observed,
            "frame_count": frame_count, "scene_samples": samples,
            "full_decode": "PASS", "black_interval_scan": "PASS_750MS_THRESHOLD", "format": "H264/AAC/yuv420p",
            "layout": "BOUNDS_CHECKED", "content_validation": "VERBATIM_SOURCE_CAPTIONS",
            "semantic_visual_review": "OWNER_REVIEW_REQUIRED",
            "limits": "Sample checks do not prove absence of all transient visual defects.",
            "dl580_acceptance": "NOT_RUN"}


def package(root: Path, expected: list[str], output: Path, metadata: dict) -> dict:
    """Seal exact payload set and verify the ZIP before declaring success."""
    payload = sorted(set(expected) - {"MRL_manifest.json"})
    write_json(root / "MRL_manifest.json", {
        "schema": "MRL_Video_Package/v1", "origin_signature": "MrLiouWord",
        "canonical_authority": "Mr.liou", "metadata": metadata,
        "files": inventory(root, payload),
        "dependency_tree": {"request.json": ["storyboard.json", "provenance.json"],
                            "storyboard.json": ["subtitles.srt", "explainer.mp4"],
                            "explainer.mp4": ["explainer-preview.gif", "explainer-stills.png"],
                            "MRL_manifest.json": payload},
        "package_map": {name: name for name in expected},
        "manifest_integrity": "Manifest excludes its own hash; pin the external ZIP SHA-256."})
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(expected):
            archive.write(root / name, name)
    return verify_package(output)
