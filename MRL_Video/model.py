"""Storyboard validation and stable public reexports. origin_signature: MrLiouWord."""
from __future__ import annotations

import re
from pathlib import Path

from .contract import VideoError, digest, dimensions, keys, text, number
from . import contract


def canonical(value: object) -> bytes:
    """Preserve the original public contract entry point."""
    return contract.canonical(value)


def local_file(root: Path, name: str, max_bytes: int = 50 * 1024 * 1024) -> Path:
    """Delegate existing callers and the extended byte budget to the shared contract."""
    return contract.local_file(root, name, max_bytes)


def file_digest(path: Path) -> str:
    """Preserve the streaming hash entry point."""
    return contract.file_digest(path)


def stream_digest(stream) -> tuple[str, int]:
    """Preserve the streaming package hash entry point."""
    return contract.stream_digest(stream)

def validate(request: dict) -> dict:
    """Normalize a request; never silently ignore unsupported options."""
    if isinstance(request, dict) and request.get("schema") == "MRL_LongFilm_Request/v1":
        from .longfilm import validate_longfilm
        return validate_longfilm(request)
    v2 = isinstance(request, dict) and request.get("schema") == "MRL_Video_Request/v2"
    extra = {"target_seconds", "resolution", "fps", "preset", "crf"} if v2 else {"longfilm", "encoding"}
    keys(request, {"schema", "title", "sources", "scenes", "profile", "music",
                   "require_narration", "template", "source_commit"} | extra, "request")
    if request.get("schema") not in {"MRL_Video_Request/v1", "MRL_Video_Request/v2"}:
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
    legacy_long = request.get("longfilm", False)
    if type(legacy_long) is not bool:
        raise VideoError("longfilm must be boolean")
    longfilm = v2 or legacy_long
    fps = 24
    options = {}
    if not v2:
        if "longfilm" in request:
            options["longfilm"] = legacy_long
        if "encoding" in request:
            encoding = request["encoding"]
            keys(encoding, {"width", "height", "crf", "preset"}, "encoding")
            width, height = dimensions({"profile": profile})
            encoding = dict(width=encoding.get("width", width), height=encoding.get("height", height),
                            crf=encoding.get("crf", 20), preset=encoding.get("preset", "fast"))
            for key in ("width", "height"):
                if type(encoding[key]) is not int or not 320 <= encoding[key] <= 3840 or encoding[key] % 2:
                    raise VideoError("Resolution must use even dimensions within 320..3840")
            if encoding["width"] * encoding["height"] > 3840 * 2160:
                raise VideoError("Resolution exceeds 4K budget")
            if type(encoding["crf"]) is not int or not 16 <= encoding["crf"] <= 28:
                raise VideoError("CRF must be 16..28")
            if encoding["preset"] not in {"ultrafast", "veryfast", "fast", "medium", "slow"}:
                raise VideoError("Unsupported encoder preset")
            options["encoding"] = encoding
    if v2:
        target = number(request.get("target_seconds"), 30, 1200, "target_seconds")
        resolution = request.get("resolution", "1080p")
        fps = request.get("fps", 24)
        preset = request.get("preset", "fast")
        crf = request.get("crf", 20)
        if resolution not in {"360p", "720p", "1080p", "2160p"}:
            raise VideoError("Unsupported resolution")
        if type(fps) is not int or fps not in {24, 25, 30}:
            raise VideoError("fps must be 24, 25 or 30")
        if preset not in {"veryfast", "fast", "medium"}:
            raise VideoError("Unsupported encoder preset")
        if type(crf) is not int or not 18 <= crf <= 28:
            raise VideoError("crf must be an integer 18..28")
        options = dict(target_seconds=target, resolution=resolution, fps=fps, preset=preset, crf=crf)
        if not isinstance(request.get("scenes"), list):
            raise VideoError("Long films require an explicit reviewed storyboard")
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
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= (600 if longfilm else 8):
        raise VideoError("Scene count exceeds request schema budget")
    total = 0.0
    normalized = []
    for scene in scenes:
        keys(scene, {"title", "caption", "source_id", "duration", "layout", "image",
                     "narration"} | ({"clip", "clip_start", "allow_silent"} if v2 else set()), "scene")
        text(scene.get("title"), 100, "scene title")
        caption = text(scene.get("caption"), 240, "caption")
        sid = scene.get("source_id")
        source = next((s for s in sources if s["id"] == sid), None)
        if source is None or caption not in source["text"]:
            raise VideoError("Each caption must be a verbatim excerpt from its named source")
        duration = number(scene.get("duration", 8), 2, 60 if v2 else 20, "scene duration")
        # Millisecond precision keeps subtitles and frame/sample alignment bounded.
        if abs(duration * 1000 - round(duration * 1000)) > 1e-6:
            raise VideoError("Scene duration must use millisecond precision")
        if longfilm:
            if abs(duration * fps - round(duration * fps)) > 1e-6:
                raise VideoError("Long-film scene durations must align to whole frames")
            if scene.get("clip") and scene.get("image"):
                raise VideoError("Choose clip or image for a scene")
            if ("clip_start" in scene or "allow_silent" in scene) and not scene.get("clip"):
                raise VideoError("Clip options require a clip")
            if "clip" in scene:
                text(scene["clip"], 240, "clip")
                if Path(scene["clip"]).suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
                    raise VideoError("Clip must use a supported local video container")
                number(scene.get("clip_start", 0), 0, 86400, "clip_start")
                if type(scene.get("allow_silent", False)) is not bool:
                    raise VideoError("allow_silent must be boolean")
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
    if v2 and abs(total - target) > 1e-6:
        raise VideoError("Scene timeline does not match target_seconds")
    if not v2 and not 30 <= total <= (1200 if legacy_long else 60):
        raise VideoError("Total runtime must be 30..60 seconds")
    return {"schema": request["schema"], **options, "title": title, "sources": sources,
            "scenes": normalized, "profile": profile, "music": music,
            "require_narration": narration, "template": template,
            **({"source_commit": commit} if commit else {})}

