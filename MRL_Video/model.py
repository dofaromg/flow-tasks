"""Strict, model-independent storyboard contract and deterministic source planner."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path


class VideoError(ValueError):
    """A bounded, user-actionable production error."""


def canonical(value: object) -> bytes:
    """Stable UTF-8 bytes for hashes and version comparison."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def local_file(root: Path, name: str) -> Path:
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
    if resolved.stat().st_size > 50 * 1024 * 1024:
        raise VideoError("Asset exceeds 50 MiB")
    return resolved


def validate(request: dict) -> dict:
    """Normalize a request; never silently ignore unsupported options."""
    keys(request, {"schema", "title", "sources", "scenes", "profile", "music",
                   "require_narration", "template", "source_commit"}, "request")
    if request.get("schema") != "MRL_Video_Request/v1":
        raise VideoError("Unsupported request schema")
    title = text(request.get("title"), 100, "title")
    template = request.get("template", "explainer")
    if template not in {"explainer", "tutorial", "release", "promo"}:
        raise VideoError("Unsupported template")
    commit = request.get("source_commit")
    if commit is not None and (not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit)):
        raise VideoError("source_commit must be an exact Git SHA")
    sources = request.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 32:
        raise VideoError("Provide 1..32 sources")
    ids = set()
    for source in sources:
        keys(source, {"id", "original_name", "text", "locator", "sha256"}, "source")
        sid = text(source.get("id"), 48, "source id")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", sid) or sid in ids:
            raise VideoError("Duplicate or invalid source id")
        ids.add(sid)
        text(source.get("original_name"), 200, "original source name")
        body = text(source.get("text"), 50000, "source text")
        text(source.get("locator"), 500, "source locator")
        actual = digest(body.encode("utf-8"))
        if source.get("sha256", actual) != actual:
            raise VideoError("Source digest mismatch")
    if sum(len(s["text"]) for s in sources) > 200000:
        raise VideoError("Source text budget exceeded")
    profile = request.get("profile", "landscape")
    if profile not in {"landscape", "portrait", "square"}:
        raise VideoError("Unsupported profile")
    music = request.get("music", True)
    narration = request.get("require_narration", False)
    if type(music) is not bool or type(narration) is not bool:
        raise VideoError("music and require_narration must be booleans")
    scenes = request.get("scenes")
    if scenes is None:
        # Extractive planning: no claims invented, no external model or API.
        excerpts = [(s, p.strip()) for s in sources
                    for p in re.split(r"[\n。!?]+|(?<=\.)\s+", s["text"])
                    if 4 <= len(p.strip()) <= 180]
        if len(excerpts) < 4:
            raise VideoError("Auto planning needs four source excerpts; provide scenes otherwise")
        labels = {"explainer": ["Question", "Context", "Mechanism", "Result"],
                  "tutorial": ["Prepare", "Start", "Check", "Finish"],
                  "release": ["Version", "Change", "Validation", "Next"],
                  "promo": ["Problem", "Capability", "Evidence", "Next step"]}[template]
        scenes = [{"title": labels[i], "caption": excerpt,
                   "source_id": source["id"], "duration": 8,
                   "layout": "steps" if template == "tutorial" else "diagram"}
                  for i, (source, excerpt) in enumerate(excerpts[:4])]
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 8:
        raise VideoError("Provide 1..8 scenes")
    total = 0.0
    normalized = []
    for scene in scenes:
        keys(scene, {"title", "caption", "source_id", "duration", "layout", "image",
                     "narration"}, "scene")
        text(scene.get("title"), 100, "scene title")
        caption = text(scene.get("caption"), 240, "caption")
        sid = scene.get("source_id")
        source = next((s for s in sources if s["id"] == sid), None)
        if source is None or caption not in source["text"]:
            raise VideoError("Each caption must be a verbatim excerpt from its named source")
        duration = number(scene.get("duration", 8), 2, 20, "scene duration")
        # Millisecond precision keeps subtitles and frame/sample alignment bounded.
        if abs(duration * 1000 - round(duration * 1000)) > 1e-6:
            raise VideoError("Scene duration must use millisecond precision")
        layout = scene.get("layout", "diagram")
        if layout not in {"diagram", "steps", "quote"}:
            raise VideoError("Unsupported scene layout")
        for name in ("image", "narration"):
            if name in scene:
                text(scene[name], 240, name)
        if narration and not scene.get("narration"):
            raise VideoError("Narration required for every scene")
        total += duration
        normalized.append(dict(scene, duration=duration, layout=layout))
    if not 30 <= total <= 60:
        raise VideoError("Total runtime must be 30..60 seconds")
    return {"schema": "MRL_Video_Request/v1", "title": title, "sources": sources,
            "scenes": normalized, "profile": profile, "music": music,
            "require_narration": narration, "template": template,
            **({"source_commit": commit} if commit else {})}
