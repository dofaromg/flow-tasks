"""CPU renderer: source-backed cards, animated transitions, local audio and previews."""
from __future__ import annotations

import array
import json
import math
import re
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .model import VideoError, digest, local_file

PROFILES = {"landscape": (1280, 720), "portrait": (720, 1280), "square": (960, 960)}
FPS = 24
SAMPLE_RATE = 22050


class Cancelled(VideoError):
    """Operator cancellation; completed work is retained for inspection."""


class Runner:
    """Bound child processes by one job deadline, with cooperative cancellation."""

    def __init__(self, cancelled, timeout: int = 1800):
        self.cancelled = cancelled
        self.deadline = time.monotonic() + timeout
        self.failed = Event()

    def check(self):
        if self.cancelled():
            raise Cancelled("Cancellation requested")
        if self.failed.is_set():
            raise VideoError("Sibling scene failed")
        if time.monotonic() >= self.deadline:
            raise VideoError("Job time budget exceeded")

    def run(self, args: list[str], cwd: Path, capture_stderr: bool = False) -> str:
        self.check()
        if Path(args[0]).name in {"ffmpeg", "ffmpeg.exe"}:
            # Large hosts may expose hundreds of cores. Bound decoder/filter
            # pools as well as the scene encoder to avoid thread exhaustion.
            args = [args[0], "-threads", "2", "-filter_threads", "1",
                    "-filter_complex_threads", "1", *args[1:]]
        # Files avoid stdout/stderr pipe deadlocks. Never invoke a shell.
        import tempfile
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            process = subprocess.Popen(args, cwd=cwd, stdout=out, stderr=err,
                                       stdin=subprocess.DEVNULL)
            try:
                while process.poll() is None:
                    self.check()
                    time.sleep(0.05)
                if process.returncode:
                    raise VideoError("Media command failed; inspect local tool configuration")
                source = err if capture_stderr else out
                source.seek(0)
                return source.read(2 * 1024 * 1024).decode("utf-8")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


def probe(path: Path, runner: Runner) -> dict:
    """Read media metadata without executing input content."""
    return json.loads(runner.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                  "-of", "json", str(path.resolve())], path.parent))


def ensure_glyphs(font: Path, content: str) -> None:
    """Reject missing glyphs instead of producing unreadable square characters."""
    with TTFont(font, fontNumber=0) as ft:
        cmap = ft.getBestCmap() or {}
        if any(ord(c) not in cmap for c in content if not c.isspace()):
            raise VideoError("Configured font lacks required glyphs; install a local Traditional Chinese font")


def wrap(draw, content: str, font, width: int) -> list[str]:
    lines = []
    for paragraph in content.splitlines() or [content]:
        line = ""
        tokens = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*|[^\S\n]+|.", paragraph)
        for token in tokens:
            if draw.textlength(line + token, font=font) <= width:
                line += token
                continue
            if line.strip():
                lines.append(line.rstrip())
            line = token.lstrip()
            if draw.textlength(line, font=font) > width:
                # Long identifiers and CJK still have a character-level fallback.
                remainder = ""
                for char in line:
                    if draw.textlength(remainder + char, font=font) > width:
                        if not remainder:
                            raise VideoError("Glyph wider than available layout")
                        lines.append(remainder)
                        remainder = char
                    else:
                        remainder += char
                line = remainder
        lines.append(line.rstrip())
    return lines


def fit_text(draw, content: str, font_path: Path, box: tuple, maximum: int, minimum: int, fill: str = "#f3f6ff"):
    x, y, width, height = box
    for size in range(maximum, minimum - 1, -1):
        font = ImageFont.truetype(str(font_path), size)
        lines = wrap(draw, content, font, width)
        spacing = math.ceil(size * 1.45)
        if len(lines) * spacing <= height:
            for i, line in enumerate(lines):
                draw.text((x, y + i * spacing), line, font=font, fill=fill)
            return {"font_size": size, "lines": len(lines), "box": list(box)}
    raise VideoError("Text cannot fit safe area; shorten caption or change profile")


def card(scene: dict, index: int, count: int, profile: str, font: Path,
         source_root: Path, output: Path) -> dict:
    width, height = PROFILES[profile]
    image = Image.new("RGB", (width, height), "#101929")
    draw = ImageDraw.Draw(image)
    margin = int(min(width, height) * .07)
    accent = "#63dac5"
    small = ImageFont.truetype(str(font), max(16, margin // 2))
    draw.text((margin, margin), f"MRL / {index + 1:02d} / {count:02d}", font=small, fill=accent)
    title = fit_text(draw, scene["title"], font,
                     (margin, margin * 2, width - 2 * margin, int(height * .18)), 52, 24)
    upper = int(height * .38)
    if scene.get("image"):
        path = local_file(source_root, scene["image"])
        with Image.open(path) as source:
            if source.width * source.height > 16000000:
                raise VideoError("Image exceeds 16 megapixel decode budget")
            source.load()
            source = ImageOps.exif_transpose(source)
            tile = ImageOps.fit(source.convert("RGB"), (width - 2 * margin, int(height * .24)))
            image.paste(tile, (margin, upper))
    elif scene["layout"] == "diagram":
        spacing = (width - 2 * margin) / 3
        for i in range(3):
            cx = int(margin + spacing * (i + .5))
            cy = upper + int(height * .09)
            radius = int(min(width, height) * .035)
            if i < 2:
                draw.line((cx, cy, cx + spacing, cy), fill=accent, width=4)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=accent)
    elif scene["layout"] == "steps":
        for i in range(3):
            yy = upper + i * int(height * .065)
            draw.rounded_rectangle((margin, yy, width - margin, yy + int(height * .035)),
                                   radius=6, fill="#21485a" if i != index % 3 else accent)
    else:
        draw.line((margin, upper, margin, upper + int(height * .2)), fill=accent, width=8)
        draw.text((margin * 2, upper), "SOURCE", font=small, fill=accent)
    caption = fit_text(draw, scene["caption"], font,
                       (margin, int(height * .67), width - 2 * margin, int(height * .23)), 36, 20)
    fit_text(draw, "MrLiouWord | " + scene["source_id"], font,
             (margin, height - margin, width - 2 * margin, margin),
             max(16, margin // 2), 10, fill="#a4b8d4")
    image.save(output)
    return {"scene": index + 1, "title": title, "caption": caption,
            "source_id": scene["source_id"], "layout": scene["layout"],
            "visual_semantics": "decorative; diagram nodes do not assert source topology",
            "status": "LAYOUT_PASS"}


def soundtrack(request: dict, root: Path, output: Path, runner: Runner) -> None:
    """Compose deterministic original music; mix explicit local narration WAV files."""
    audio = array.array("h")
    chords = [(261.63, 329.63, 392.00), (220, 261.63, 329.63),
              (174.61, 220, 261.63), (196, 246.94, 293.66)]
    for idx, scene in enumerate(request["scenes"]):
        runner.check()
        length = round(scene["duration"] * SAMPLE_RATE)
        voice = array.array("h", [0]) * length
        has_voice = bool(scene.get("narration"))
        if has_voice:
            path = local_file(root, scene["narration"])
            with wave.open(str(path), "rb") as wav:
                if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, SAMPLE_RATE, "NONE"):
                    raise VideoError("Narration must be mono PCM16 WAV at 22050 Hz")
                if wav.getnframes() > length:
                    raise VideoError("Narration exceeds scene duration; shorten audio or extend scene")
                samples = array.array("h")
                samples.frombytes(wav.readframes(wav.getnframes()))
                if len(samples) != wav.getnframes():
                    raise VideoError("Truncated narration WAV")
                if sys.byteorder == "big":
                    samples.byteswap()
                if max((abs(s) for s in samples), default=0) < 16:
                    raise VideoError("Narration is silent")
                voice[:len(samples)] = samples
        samples = array.array("h")
        for n in range(length):
            if n % SAMPLE_RATE == 0:
                runner.check()
            t = n / SAMPLE_RATE
            envelope = min(1, t, max(0, (length - n) / SAMPLE_RATE / 2))
            frequencies = chords[int(t / (60 / 80 * 4)) % 4]
            music = sum(math.sin(2 * math.pi * f * t) for f in frequencies) / 3
            gain = (500 if has_voice else 1800) if request["music"] else 0
            value = round(voice[n] * .85 + music * gain * envelope)
            samples.append(max(-32768, min(32767, value)))
        audio.extend(samples)
    if sys.byteorder == "big":
        audio.byteswap()
    with wave.open(str(output), "wb") as wav:
        wav.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        wav.writeframes(audio.tobytes())


def srt(request: dict) -> str:
    def stamp(seconds):
        value = round(seconds * 1000)
        hours, value = divmod(value, 3600000)
        minutes, value = divmod(value, 60000)
        secs, millis = divmod(value, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
    position = 0.0
    chunks = []
    for i, scene in enumerate(request["scenes"]):
        end = position + scene["duration"]
        chunks.append(f"{i + 1}\n{stamp(position)} --> {stamp(end)}\n{scene['caption']}\n")
        position = end
    return "\n".join(chunks)


def render(request: dict, work: Path, font: Path, source_root: Path,
           runner: Runner, phase, workers: int = 2) -> dict:
    """Render every scene, join tracks, and generate bounded previews."""
    runner.run(["ffmpeg", "-version"], work)
    runner.run(["ffprobe", "-version"], work)
    font = font.resolve()
    content = "MrLiouWord | MRL / SOURCE 0123456789" + "".join(
        s["title"] + s["caption"] + s["source_id"] for s in request["scenes"])
    ensure_glyphs(font, content)
    phase("BUILD_SCENES")
    def build(index):
        scene = request["scenes"][index]
        try:
            runner.check()
            png = work / f"scene_{index + 1:02}.png"
            layout = card(scene, index, len(request["scenes"]), request["profile"], font, source_root, png)
            duration = scene["duration"]
            runner.run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-loop", "1", "-i", png.name,
                        "-t", str(duration), "-vf", f"fade=t=in:st=0:d=0.25,fade=t=out:st={duration - .25}:d=0.25",
                        "-r", str(FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                        "-threads", "2", "-pix_fmt", "yuv420p", f"scene_{index + 1:02}.mp4"], work)
            return layout
        except BaseException:
            runner.failed.set()
            raise
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 4))) as pool:
        layouts = list(pool.map(build, range(len(request["scenes"]))))
    phase("COMPOSE_AUDIO")
    soundtrack(request, source_root, work / "soundtrack.wav", runner)
    (work / "subtitles.srt").write_text(srt(request), encoding="utf-8")
    (work / "concat.txt").write_text("".join(f"file 'scene_{i + 1:02}.mp4'\n"
                                             for i in range(len(layouts))), encoding="utf-8")
    phase("COMPOSE_VIDEO")
    runner.run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-f", "concat", "-safe", "1",
                "-i", "concat.txt", "-i", "soundtrack.wav", "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                "explainer.mp4"], work)
    # Full timeline sampled at one frame every two seconds; cap and verify 2 MiB.
    total = sum(s["duration"] for s in request["scenes"])
    for width in (320, 240, 160):
        preview = work / "explainer-preview.gif"
        if preview.exists():
            preview.unlink()
        runner.run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-i", "explainer.mp4", "-vf",
                    f"fps=0.5,scale={width}:-1:flags=lanczos", "-t", str(total), preview.name], work)
        if preview.stat().st_size < 2 * 1024 * 1024:
            break
    else:
        raise VideoError("GIF budget exceeded")
    thumb_width = 480
    aspect = PROFILES[request["profile"]]
    thumb_height = round(thumb_width * aspect[1] / aspect[0])
    board = Image.new("RGB", (thumb_width * 2, thumb_height * math.ceil(len(layouts) / 2)), "#101929")
    for i in range(len(layouts)):
        with Image.open(work / f"scene_{i + 1:02}.png") as tile:
            board.paste(tile.resize((thumb_width, thumb_height)),
                        (i % 2 * thumb_width, i // 2 * thumb_height))
    board.save(work / "explainer-stills.png")
    return {"layouts": layouts, "font_sha256": digest(font.read_bytes()),
            "music": "original_synthesized" if request["music"] else "disabled",
            "narration_scenes": sum(bool(s.get("narration")) for s in request["scenes"]),
            "semantic_review": "OWNER_REVIEW_REQUIRED"}
