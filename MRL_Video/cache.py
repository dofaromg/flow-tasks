"""Content-addressed scene checkpoints, shared by child versions on one local worker."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import PIL
from pathlib import Path

from .contract import VideoError, canonical, digest, file_digest


class SceneCache:
    """Only atomic, hash-verified completed scenes are reusable; partials stay private."""

    names = ("frame.png", "video.mp4", "layout.json")

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def restore(self, key: str, png: Path, video: Path) -> dict | None:
        entry = self.root / key
        if not entry.exists():
            return None
        try:
            receipt = json.loads((entry / "receipt.json").read_text(encoding="utf-8"))
            if receipt["key"] != key or set(receipt["files"]) != set(self.names):
                raise VideoError("Invalid scene cache receipt")
            for name in self.names:
                path = entry / name
                if path.is_symlink() or file_digest(path) != receipt["files"][name]:
                    raise VideoError("Scene cache integrity failure")
            layout = json.loads((entry / "layout.json").read_text(encoding="utf-8"))
            shutil.copyfile(entry / "frame.png", png)
            shutil.copyfile(entry / "video.mp4", video)
            return layout
        except (KeyError, ValueError, OSError) as exc:
            # Preserve corrupt evidence instead of silently repairing a trusted checkpoint.
            raise VideoError("Scene cache integrity failure; quarantine damaged entry before retry") from exc

    def save(self, key: str, png: Path, video: Path, layout: dict) -> None:
        with tempfile.TemporaryDirectory(prefix="pending-", dir=self.root) as temporary:
            pending = Path(temporary) / "complete"
            pending.mkdir()
            shutil.copyfile(png, pending / "frame.png")
            shutil.copyfile(video, pending / "video.mp4")
            (pending / "layout.json").write_bytes(canonical(layout))
            receipt = {"key": key, "files": {n: file_digest(pending / n) for n in self.names}}
            (pending / "receipt.json").write_bytes(canonical(receipt))
            for path in pending.iterdir():
                with path.open("rb") as stream:
                    os.fsync(stream.fileno())
            # Worker is single-owner; key includes scene position so siblings cannot collide.
            pending.rename(self.root / key)


def scene_key(scene: dict, index: int, count: int, request: dict,
              font_hash: str, asset_hashes: dict, tools: str) -> str:
    """Pin renderer implementation, tools, font, settings, position and actual source bytes."""
    return digest(canonical({"renderer": file_digest(Path(__file__).with_name("render.py")),
                             "model": file_digest(Path(__file__).with_name("model.py")),
                             "pillow": PIL.__version__, "cache_revision": 1, "scene": scene, "index": index, "count": count,
                             "profile": request["profile"],
                             "settings": {k: request.get(k) for k in ("resolution", "fps", "preset", "crf", "encoding")},
                             "font": font_hash, "assets": {scene[k]: asset_hashes[scene[k]]
                             for k in ("image", "clip", "narration") if scene.get(k)}, "tools": tools}))
