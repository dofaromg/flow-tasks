"""Dependency-free media contracts. origin_signature: MrLiouWord."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

FPS = 24
PROFILES = {"landscape": (1280, 720), "portrait": (720, 1280), "square": (960, 960),
            "fullhd": (1920, 1080), "uhd": (3840, 2160)}

class VideoError(ValueError):
    """A bounded, user-actionable production error."""


def canonical(value: object) -> bytes:
    """Stable UTF-8 bytes for hashes and version comparison."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    """Hash large local media with bounded memory."""
    with path.open("rb") as stream:
        return stream_digest(stream)[0]


def stream_digest(stream) -> tuple[str, int]:
    """Return SHA-256 and byte count without buffering a full movie."""
    h = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size


def dimensions(request: dict) -> tuple[int, int]:
    """Select exact even dimensions; 360p is an explicitly named draft profile."""
    if request.get("schema") == "MRL_LongFilm_Request/v1":
        return PROFILES[request["profile"]]
    if "encoding" in request:
        return request["encoding"]["width"], request["encoding"]["height"]
    base = {"landscape": (1280, 720), "portrait": (720, 1280), "square": (960, 960)}
    if "resolution" not in request:
        return base[request["profile"]]
    short = {"360p": 360, "720p": 720, "1080p": 1080, "2160p": 2160}[request["resolution"]]
    long = short * 16 // 9
    return {"landscape": (long, short), "portrait": (short, long), "square": (short, short)}[request["profile"]]


def keys(obj: dict, allowed: set[str], name: str) -> None:
    if not isinstance(obj, dict) or set(obj) - allowed:
        raise VideoError(f"Invalid {name} fields")


def text(value: object, limit: int, name: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        raise VideoError(f"Invalid {name}")
    return value


def number(value: object, low: float, high: float, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise VideoError(f"Invalid {name}")
    return float(value)


def local_file(root: Path, name: str, max_bytes: int = 50 * 1024 * 1024) -> Path:
    """Only explicit relative files below the operator's source root are readable."""
    text(name, 240, "asset path")
    if "\\" in name or ":" in name or Path(name).is_absolute():
        raise VideoError("Asset paths must be relative, forward-slash paths")
    parts = Path(name).parts
    if ".." in parts:
        raise VideoError("Asset traversal rejected")
    base = root.resolve()
    current = base
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise VideoError("Symlink assets rejected")
    resolved = current.resolve()
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise VideoError("Local asset unavailable")
    if resolved.stat().st_size > max_bytes:
        raise VideoError("Asset exceeds configured byte budget")
    return resolved

