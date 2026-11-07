"""Long-film timeline, checkpoint recovery and real local media acceptance."""
import array
import copy
import json
import math
import os
import time
import wave
from pathlib import Path

import pytest

from MRL_Video.audit import audit_media, verify_package
from MRL_Video.cache import scene_key
from MRL_Video.model import VideoError, dimensions, file_digest, validate
from MRL_Video.render import Runner, SAMPLE_RATE, render, Cancelled
from MRL_Video.service import Service
from MRL_Video.store import Store

FONT = Path(os.environ.get("MRL_VIDEO_TEST_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
MEDIA = pytest.mark.skipif(os.environ.get("MRL_VIDEO_MEDIA_TEST") != "1", reason="Opt-in real media")


def request(seconds=30, count=3):
    """An explicit synthetic editorial timeline, never model-generation evidence."""
    return {"schema": "MRL_Video_Request/v2", "title": "MRL synthetic timeline fixture",
            "target_seconds": seconds, "profile": "landscape", "resolution": "360p",
            "fps": 24, "preset": "veryfast", "crf": 23, "music": False,
            "sources": [{"id": "fixture", "original_name": "synthetic-timeline.txt",
                         "locator": "test:synthetic", "text": "Synthetic timeline and local audio."}],
            "scenes": [{"title": f"Chapter {i + 1}", "caption": "Synthetic timeline and local audio.",
                        "source_id": "fixture", "duration": seconds / count,
                        "layout": "steps"} for i in range(count)]}


def execute(service, value, parent=None):
    job = service.store.submit(value, parent_id=parent)
    assert service.store.claim() == job["id"]
    service.process(job["id"])
    return service.store.get(job["id"])


def test_20min_contract_and_frame_alignment():
    value = validate(request(1200, 20))
    assert sum(s["duration"] for s in value["scenes"]) == 1200
    assert dimensions(value) == (640, 360)
    value["scenes"][0]["duration"] = 59.999
    with pytest.raises(VideoError, match="whole frames"):
        validate(value)


@pytest.mark.parametrize("field,value", [("target_seconds", 1201), ("target_seconds", True),
    ("fps", 23.976), ("fps", True), ("resolution", "8k"), ("preset", "external"),
    ("crf", 19.5), ("crf", 0), ("scenes", []), ("scenes", None)])
def test_reject_unsupported_settings(field, value):
    data = request()
    data[field] = value
    with pytest.raises(VideoError):
        validate(data)


def test_target_mismatch_and_legacy_limit():
    data = request()
    data["target_seconds"] = 31
    with pytest.raises(VideoError, match="timeline"):
        validate(data)
    old = json.loads((Path(__file__).parents[1] / "examples/demo.json").read_text())
    old["scenes"] = request(1200, 20)["scenes"]
    with pytest.raises(VideoError):
        validate(old)


@pytest.mark.parametrize("resolution,size", [("720p", (1280, 720)), ("1080p", (1920, 1080)),
                                               ("2160p", (3840, 2160))])
def test_resolution(resolution, size):
    data = request()
    data["resolution"] = resolution
    assert dimensions(validate(data)) == size


def test_cache_key_tracks_source_bytes_font_and_settings():
    data = validate(request())
    scene = dict(data["scenes"][0], clip="clip.mp4")
    args = (scene, 0, 3, data, "font", {"clip.mp4": "source1"}, "ffmpeg1")
    initial = scene_key(*args)
    assert initial != scene_key(scene, 0, 3, data, "font", {"clip.mp4": "source2"}, "ffmpeg1")
    assert initial != scene_key(scene, 0, 3, dict(data, resolution="1080p"), "font", args[5], "ffmpeg1")
    assert initial != scene_key(scene, 0, 3, data, "font2", args[5], "ffmpeg1")
    assert initial != scene_key(scene, 0, 3, data, "font", args[5], "ffmpeg2")


def test_resume_preserves_interrupted_version(tmp_path):
    store = Store(tmp_path)
    first = store.submit(request())
    store.claim()
    store.recover()
    child = store.resume(first["id"], "retry")
    assert child["parent_id"] == first["id"]
    assert store.get(first["id"])["state"] == "INTERRUPTED"
    assert store.request(child["id"]) == store.request(first["id"])
    assert store.verify_chain()
    with pytest.raises(VideoError):
        store.resume(child["id"])


@MEDIA
def test_failure_reuses_completed_scenes_and_rejects_corruption(tmp_path, monkeypatch):
    service = Service(tmp_path / "versions", tmp_path, FONT, workers=1)
    value = request()
    original = Runner.run
    def fail_audio(self, args, cwd, capture_stderr=False):
        if "soundtrack.wav" in args:
            raise VideoError("Injected composition failure after scene checkpointing")
        return original(self, args, cwd, capture_stderr)
    with monkeypatch.context() as m:
        m.setattr(Runner, "run", fail_audio)
        first = execute(service, value)
    assert first["state"] == "FAILED", first
    child = service.store.resume(first["id"])
    assert service.store.claim() == child["id"]
    service.process(child["id"])
    child = service.store.get(child["id"])
    assert child["state"] == "SUCCEEDED", child
    work = service.store.root / child["id"]
    details = json.loads((work / "layout.json").read_text())
    assert details["cache_hits"] == 3
    assert verify_package(service.store.root / (child["id"] + ".zip"))["coverage"] == 100
    assert service.store.get(first["id"])["state"] == "FAILED"
    # Exact same source/settings reuse cache. A one-byte change must be rejected.
    key = details["layouts"][0]["cache_key"]
    cache_file = service.store.root / "MRL_scene_cache" / key / "video.mp4"
    with cache_file.open("ab") as stream:
        stream.write(b"corrupt")
    third = execute(service, value, child["id"])
    assert third["state"] == "FAILED"
    assert "cache integrity" in third["error"]


@MEDIA
def test_clip_audio_trim_sync_and_silent_policy(tmp_path):
    runner = Runner(lambda: False)
    runner.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "12",
                "-c:v", "libx264", "-preset", "veryfast", "-threads", "2", "-c:a", "aac", "clip.mp4"], tmp_path)
    value = request()
    for scene in value["scenes"]:
        scene.update(clip="clip.mp4", clip_start=2)
    service = Service(tmp_path / "versions", tmp_path, FONT, workers=1)
    job = execute(service, value)
    assert job["state"] == "SUCCEEDED", job
    work = service.store.root / job["id"]
    audit = json.loads((work / "MRL_audit.json").read_text())
    assert audit["frame_count"] == 720
    assert audit["av_end_delta_seconds"] < .1
    with wave.open(str(work / "soundtrack.wav"), "rb") as wav:
        audio = array.array("h")
        audio.frombytes(wav.readframes(wav.getnframes()))
    # Audible signal on both sides of every join, not a silent replacement track.
    for t in (0.1, 9.9, 10.1, 19.9, 20.1, 29.9):
        start = int(t * SAMPLE_RATE)
        assert max(abs(x) for x in audio[start:start + 500]) > 100
    bad = copy.deepcopy(value)
    bad["scenes"][0]["clip_start"] = 3
    assert execute(service, bad)["state"] == "FAILED"
    runner.run(["ffmpeg", "-v", "error", "-i", "clip.mp4", "-an", "-c:v", "copy", "silent.mp4"], tmp_path)
    for scene in value["scenes"]:
        scene["clip"] = "silent.mp4"
    assert execute(service, value)["state"] == "FAILED"
    for scene in value["scenes"]:
        scene["allow_silent"] = True
    assert execute(service, value)["state"] == "SUCCEEDED"


@pytest.mark.skipif(os.environ.get("MRL_VIDEO_LONG_TEST") != "1", reason="Opt-in actual 1200-second production")
def test_actual_20min_output(tmp_path):
    root = Path(os.environ.get("MRL_VIDEO_LONG_OUTPUT", str(tmp_path)))
    root.mkdir(parents=True, exist_ok=True)
    value = request(1200, 20)
    # Real local PCM input, two seconds per chapter; remainder is intentional silence.
    voice = root / "fixture-tone.wav"
    tone = array.array("h", (round(1800 * math.sin(2 * math.pi * 440 * n / SAMPLE_RATE))
                             for n in range(2 * SAMPLE_RATE)))
    import sys
    if sys.byteorder == "big":
        tone.byteswap()
    with wave.open(str(voice), "wb") as stream:
        stream.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        stream.writeframes(tone.tobytes())
    for scene in value["scenes"]:
        scene["narration"] = voice.name
    service = Service(root / "versions", root, FONT, workers=2)
    job = execute(service, value)
    assert job["state"] == "SUCCEEDED", job
    work = service.store.root / job["id"]
    audit = json.loads((work / "MRL_audit.json").read_text())
    assert abs(audit["duration_seconds"] - 1200) < .1
    assert audit["frame_count"] == 28800
    assert audit["full_decode"] == "PASS"
    assert audit["av_end_delta_seconds"] < .1
    assert "00:20:00,000" in (work / "subtitles.srt").read_text()
    receipt = verify_package(service.store.root / (job["id"] + ".zip"))
    evidence = {"scope": "SYNTHETIC_20MIN_MEDIA_PIPELINE_ONLY", "job": job, "audit": audit,
                "package": receipt, "mp4_sha256": file_digest(work / "explainer.mp4"),
                "mp4_size": (work / "explainer.mp4").stat().st_size,
                "generative_model_run": False, "dl580_acceptance": "NOT_RUN",
                "iphone_acceptance": "NOT_RUN", "deployment": "NOT_DEPLOYED"}
    (root / "MRL_20min_evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    # Wrong declared duration is independently detected against the actual output.
    wrong = copy.deepcopy(validate(value))
    wrong["scenes"][0]["duration"] -= 2
    with pytest.raises(VideoError, match="duration"):
        audit_media(work, wrong, audit["expected_files"], Runner(lambda: False))


@MEDIA
def test_actual_1080p_output(tmp_path):
    value = request(30, 1)
    value["resolution"] = "1080p"
    service = Service(tmp_path / "versions", tmp_path, FONT, workers=1)
    job = execute(service, value)
    assert job["state"] == "SUCCEEDED", job
    audit = json.loads((service.store.root / job["id"] / "MRL_audit.json").read_text())
    assert audit["dimensions"] == [1920, 1080]
    assert audit["frame_count"] == 720
    assert audit["full_decode"] == "PASS"


# Retained concurrent-head v1 longfilm compatibility and regression coverage.
def plan(count=60):
    return validate(dict(schema='MRL_Video_Request/v1',title='Longfilm fixture',
        sources=[dict(id='s',original_name='synthetic',locator='test fixture',text='Test scene.')],
        scenes=[dict(title='Test',caption='Test scene.',source_id='s',duration=20,layout='quote') for _ in range(count)],
        longfilm=True,music=False,encoding=dict(width=320,height=320,crf=28,preset='ultrafast')))

def test_limits_and_frame_alignment():
    p=plan()
    assert sum(s['duration'] for s in p['scenes'])==1200
    assert validate(p)==p
    p['scenes'].append(p['scenes'][0])
    with pytest.raises(VideoError): validate(p)
    p=plan(2);p['scenes'][0]['duration']=19.999
    with pytest.raises(VideoError): validate(p)
    p=plan(2);p['longfilm']=False;p['scenes']*=2
    with pytest.raises(VideoError): validate(p)

@pytest.mark.skipif(os.environ.get('MRL_VIDEO_MEDIA_TEST')!='1',reason='opt-in real media')
def test_resume_and_cache_invalidation(tmp_path):
    p=plan(2)
    first=tmp_path/'first';first.mkdir()
    phases=[]
    def phase(value):
        phases.append(value)
        if value=='COMPOSE_AUDIO': raise Cancelled('simulated restart')
    with pytest.raises(Cancelled):render(p,first,FONT,tmp_path,Runner(lambda:False),phase)
    second=tmp_path/'second';second.mkdir()
    details=render(p,second,FONT,tmp_path,Runner(lambda:False),lambda x:None)
    assert details['cache_hits']==2
    p['encoding']['crf']=27
    third=tmp_path/'third';third.mkdir()
    details=render(p,third,FONT,tmp_path,Runner(lambda:False),lambda x:None)
    assert details['cache_hits']==0
    cache=tmp_path/'MRL_scene_cache'/details['layouts'][0]['segment_key']/'video.mp4';cache.write_bytes(b'corrupt')
    fourth=tmp_path/'fourth';fourth.mkdir()
    # R04 preserves damaged evidence and rejects rather than silently overwriting.
    with pytest.raises(VideoError, match='cache integrity'):
        render(p,fourth,FONT,tmp_path,Runner(lambda:False),lambda x:None)

@pytest.mark.skipif(os.environ.get('MRL_VIDEO_LONG_TEST')!='1',reason='explicit full 20 minute acceptance')
def test_full_20minute_delivery(tmp_path):
    service=Service(tmp_path/'versions',tmp_path,FONT)
    request=plan()
    jid=service.store.submit(request)["id"]
    assert service.store.claim()==jid
    started=time.monotonic();service.process(jid)
    job=service.store.get(jid)
    assert job['state']=='SUCCEEDED',job
    root=service.store.root/jid
    audit=json.loads((root/'MRL_audit.json').read_text())
    assert abs(audit['duration_seconds']-1200)<.1
    assert audit['frame_count']==28800
    result={'origin_signature':'MrLiouWord','fixture':'synthetic source-backed cards; no generative model',
            'wall_seconds':time.monotonic()-started,'audit':audit,
            'render':json.loads((root/'layout.json').read_text()),'job':jid}
    Path(os.environ.get('MRL_VIDEO_BENCHMARK','/tmp/MRL_longfilm_benchmark.json')).write_text(json.dumps(result,indent=2))



def test_cache_flush_uses_writable_file_descriptors(tmp_path, monkeypatch):
    """Windows _commit rejects read-only descriptors even when POSIX fsync accepts them."""
    from MRL_Video.cache import SceneCache
    actual_fsync = os.fsync
    flushed = []
    def require_writable(fd):
        os.write(fd, b"")  # EBADF on a read-only handle, reproducing the Windows requirement.
        flushed.append(fd)
        actual_fsync(fd)
    monkeypatch.setattr(os, "fsync", require_writable)
    png, video = tmp_path / "frame.png", tmp_path / "video.mp4"
    png.write_bytes(b"unit-test-png-bytes")
    video.write_bytes(b"unit-test-video-bytes")
    cache = SceneCache(tmp_path / "cache")
    cache.save("a" * 64, png, video, {"status": "tested"})
    restored = cache.restore("a" * 64, tmp_path / "restored.png", tmp_path / "restored.mp4")
    assert flushed and restored == {"status": "tested"}
    assert (tmp_path / "restored.mp4").read_bytes() == video.read_bytes()
