"""Contract, concurrency, recovery, HTTP and real FFmpeg acceptance tests."""
import json
import os
import shutil
import threading
import time
import urllib.error
import urllib.request
import wave
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from MRL_Video.audit import verify_package
from MRL_Video.model import VideoError, local_file, validate
from MRL_Video.render import Runner, ensure_glyphs, soundtrack, srt
from MRL_Video.service import Service
from MRL_Video.store import Store
from MRL_Video.web import Server

ROOT = Path(__file__).parents[1]
FONT = Path(os.environ.get("MRL_VIDEO_TEST_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))


@pytest.fixture
def request_data():
    return json.loads((ROOT / "examples/demo.json").read_text())


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "data")


def test_extractive_plan_is_source_bound(request_data):
    plan = validate(request_data)
    assert len(plan["scenes"]) == 4
    assert sum(s["duration"] for s in plan["scenes"]) == 32
    assert all(s["caption"] in plan["sources"][0]["text"] for s in plan["scenes"])
    assert validate(plan) == plan


@pytest.mark.parametrize("field,value", [("profile", "4k"), ("music", "yes"),
    ("require_narration", 1), ("template", "unknown"), ("schema", "other"), ("title", "")])
def test_invalid_fields_fail(request_data, field, value):
    request_data[field] = value
    with pytest.raises(VideoError):
        validate(request_data)


def test_unknown_fields_not_silently_ignored(request_data):
    request_data["tts"] = "pretend"
    with pytest.raises(VideoError):
        validate(request_data)


def test_source_digest_mismatch(request_data):
    request_data["sources"][0]["sha256"] = "0" * 64
    with pytest.raises(VideoError):
        validate(request_data)


def test_caption_claim_requires_named_evidence(request_data):
    request_data = validate(request_data)
    request_data["scenes"][0]["caption"] = "The DL580 passed live acceptance."
    with pytest.raises(VideoError):
        validate(request_data)


@pytest.mark.parametrize("duration", [float("nan"), float("inf"), True, -1, 30, .5, 8.0001])
def test_bad_scene_duration(request_data, duration):
    plan = validate(request_data)
    plan["scenes"][0]["duration"] = duration
    with pytest.raises(VideoError):
        validate(plan)


def test_total_runtime_and_required_narration(request_data):
    plan = validate(request_data)
    plan["scenes"] = plan["scenes"][:1]
    with pytest.raises(VideoError):
        validate(plan)
    plan = validate(request_data)
    plan["require_narration"] = True
    with pytest.raises(VideoError):
        validate(plan)


@pytest.mark.parametrize("name", ["../secret", "/etc/passwd", "C:/secret", "a\\b", "missing"])
def test_asset_escape_rejected(tmp_path, name):
    with pytest.raises(VideoError):
        local_file(tmp_path, name)


def test_symlink_rejected(tmp_path):
    source = tmp_path / "real.txt"
    source.write_text("data")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation not permitted")
    with pytest.raises(VideoError):
        local_file(tmp_path, "link.txt")


def test_idempotent_submit_and_conflict(store, request_data):
    a = store.submit(request_data, "stable")
    assert a == store.submit(request_data, "stable")
    request_data["title"] = "different"
    with pytest.raises(VideoError):
        store.submit(request_data, "stable")
    assert store.verify_chain()


def test_parallel_submissions_have_unique_versions(store, request_data):
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = list(pool.map(lambda _: store.submit(request_data), range(16)))
    assert sorted(job["version_index"] for job in jobs) == list(range(1, 17))
    assert store.verify_chain()


def test_atomic_claim_has_one_owner(store, request_data):
    jid = store.submit(request_data)["id"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda _: store.claim(), range(8)))
    assert claims.count(jid) == 1
    assert claims.count(None) == 7


def test_parent_diff_and_original_preserved(store, request_data):
    parent = store.submit(request_data)
    changed = dict(request_data, profile="portrait")
    child = store.submit(changed, parent_id=parent["id"])
    assert child["parent_id"] == parent["id"]
    assert store.diff(parent["id"], child["id"]) == {"profile": {"before": "landscape", "after": "portrait"}}
    assert store.request(parent["id"])["profile"] == "landscape"
    with pytest.raises(VideoError):
        store.submit(changed, parent_id="MRL_missing")


def test_restart_marks_interrupted_no_blind_replay(store, request_data):
    jid = store.submit(request_data)["id"]
    assert store.claim() == jid
    store.recover()
    assert store.get(jid)["state"] == "INTERRUPTED"
    assert store.claim() is None
    assert store.verify_chain()


def test_cancel_queued_and_completion_race(store, request_data):
    first = store.submit(request_data)["id"]
    assert store.cancel(first)["state"] == "CANCELLED"
    second = store.submit(request_data)["id"]
    assert store.claim() == second
    store.cancel(second)
    store.update(second, "SUCCEEDED", "DELIVERY_PASS")
    assert store.get(second)["state"] == "CANCELLED"


def test_hash_chain_tamper_detected(store, request_data):
    store.submit(request_data)
    with store.connect() as db:
        db.execute("UPDATE events SET payload='tampered'")
    assert not store.verify_chain()


def test_queue_capacity(store, request_data):
    for _ in range(32):
        store.submit(request_data)
    with pytest.raises(VideoError):
        store.submit(request_data)


def test_worker_single_owner(tmp_path):
    a = Service(tmp_path, tmp_path, FONT)
    b = Service(tmp_path, tmp_path, FONT)
    a.start()
    try:
        with pytest.raises(VideoError):
            b.start()
    finally:
        a.close()
    assert a.lock.exists()  # Stable inode; the OS lock itself has been released.
    b.start()
    b.close()


def test_runner_cancels_process(tmp_path):
    import sys
    runner = Runner(lambda: False)
    runner.deadline = time.monotonic() + .2
    with pytest.raises(VideoError):
        runner.run([sys.executable, "-c", "import time; time.sleep(20)"], tmp_path)
    assert time.monotonic() - runner.deadline < 2


def test_missing_glyph_fails():
    if not FONT.exists():
        pytest.skip("Font unavailable")
    with pytest.raises(VideoError):
        ensure_glyphs(FONT, "\U0010ffff")


def test_subtitle_timeline(request_data):
    value = srt(validate(request_data))
    assert "00:00:00,000 --> 00:00:08,000" in value
    assert "00:00:24,000 --> 00:00:32,000" in value
    assert value.count(" --> ") == 4


def test_narration_silence_and_overrun_rejected(tmp_path, request_data):
    plan = validate(request_data)
    plan["scenes"][0]["narration"] = "voice.wav"
    for length in [8 * 22050, 9 * 22050]:
        with wave.open(str(tmp_path / "voice.wav"), "wb") as wav:
            wav.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
            wav.writeframes(b"\0\0" * length)
        with pytest.raises(VideoError):
            soundtrack(plan, tmp_path, tmp_path / "out.wav", Runner(lambda: False))


@pytest.fixture
def api(tmp_path):
    service = Service(tmp_path / "queue", tmp_path, FONT)
    server = Server(("127.0.0.1", 0), service, "test-key-" * 5)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    yield server, base
    server.shutdown()
    server.server_close()
    thread.join()


def http(base, path, data=None, headers=None):
    req = urllib.request.Request(base + path, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read(), response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers


def test_api_auth_host_and_submission(api, request_data):
    server, base = api
    assert http(base, "/health")[0] == 200
    assert http(base, "/api/jobs")[0] == 401
    assert http(base, "/api/jobs", headers={"Host": "evil.example"})[0] == 400
    auth = {"x-api-key": "test-key-" * 5, "Idempotency-Key": "http-id"}
    status, raw, _ = http(base, "/api/jobs", json.dumps(request_data).encode(), auth)
    assert status == 202
    jid = json.loads(raw)["id"]
    assert http(base, "/api/jobs/" + jid, headers=auth)[0] == 200
    assert http(base, f"/artifacts/{jid}/explainer.mp4", headers=auth)[0] == 400
    assert http(base, "/api/jobs", b"bad json", auth)[0] == 400
    assert http(base, "/api/jobs", json.dumps(request_data).encode(), dict(auth, Origin="https://evil.example"))[0] == 403


def test_ui_login_cookie_csrf_escape(api, request_data):
    from urllib.parse import urlencode
    server, base = api
    page = http(base, "/")[1].decode()
    assert 'type="password"' in page
    cookie = server.cookie()
    auth = {"Cookie": "MRL_video_session=" + cookie}
    page = http(base, "/", headers=auth)[1].decode()
    assert 'name="csrf"' in page
    assert http(base, "/submit", urlencode({"request": json.dumps(request_data)}).encode(), auth)[0] == 403
    assert http(base, "/api/jobs", json.dumps(request_data).encode(), auth)[0] == 403
    request_data["title"] = "<script>alert(1)</script>"
    job = server.service.store.submit(request_data)
    page = http(base, "/jobs/" + job["id"], headers=auth)[1].decode()
    assert "<script>alert" not in page
    assert "&lt;script&gt;" in page
    assert not server.valid_cookie("invalid")
    assert not server.valid_cookie("0." + server.sign("session:0"))


def test_api_branch_cancel_diff(api, request_data):
    _, base = api
    auth = {"x-api-key": "test-key-" * 5}
    raw = http(base, "/api/jobs", json.dumps(request_data).encode(), auth)[1]
    parent = json.loads(raw)["id"]
    request_data["profile"] = "square"
    status, raw, _ = http(base, f"/api/jobs/{parent}/branch", json.dumps(request_data).encode(), auth)
    assert status == 202
    child = json.loads(raw)["id"]
    assert json.loads(http(base, f"/api/diff/{parent}/{child}", headers=auth)[1])["profile"]["after"] == "square"
    assert http(base, f"/api/jobs/{child}/cancel", b"{}", auth)[0] == 202
    assert json.loads(http(base, f"/api/jobs/{child}", headers=auth)[1])["state"] == "CANCELLED"


@pytest.mark.parametrize("profile", ["landscape", "portrait", "square"])
@pytest.mark.skipif(os.environ.get("MRL_VIDEO_MEDIA_TEST") != "1", reason="Enable explicit real-media acceptance")
def test_real_media_roundtrip(tmp_path, request_data, profile):
    assert shutil.which("ffmpeg") and FONT.exists()
    request_data["profile"] = profile
    law = None
    if profile == "landscape":
        import math
        import struct
        from PIL import Image
        Image.new("RGB", (240, 160), "#4979a2").save(tmp_path / "input.png")
        with wave.open(str(tmp_path / "voice.wav"), "wb") as wav:
            wav.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
            wav.writeframes(b"".join(struct.pack("<h", round(5000 * math.sin(2 * math.pi * 440 * n / 22050))) for n in range(22050)))
        request_data = validate(request_data)
        request_data["scenes"][0]["image"] = "input.png"
        request_data["scenes"][0]["narration"] = "voice.wav"
        law = tmp_path / "law.md"
        law.write_text("Synthetic law binding fixture; not canonical MRL law.")
    service = Service(tmp_path / "media", tmp_path, FONT, law=law)
    jid = service.store.submit(request_data)["id"]
    assert service.store.claim() == jid
    service.process(jid)
    job = service.store.get(jid)
    assert job["state"] == "SUCCEEDED", job
    package = service.artifact(jid, "package.zip")
    receipt = verify_package(package)
    assert receipt["coverage"] == 100
    with zipfile.ZipFile(package) as archive:
        audit = json.loads(archive.read("MRL_audit.json"))
        assert audit["full_decode"] == "PASS"
        assert audit["missing"] == audit["extra"] == []
        assert len(audit["scene_samples"]) == 4
    assert service.store.verify_chain()
    server = Server(("127.0.0.1", 0), service, "test-key-" * 5)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        status, data, _ = http(base, f"/artifacts/{jid}/explainer.mp4", headers={"x-api-key": "test-key-" * 5, "Range": "bytes=0-99"})
        assert status == 206 and len(data) == 100
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    # Corrupt a single ZIP payload while leaving its manifest unchanged.
    damaged = tmp_path / "damaged.zip"
    with zipfile.ZipFile(package) as original, zipfile.ZipFile(damaged, "w") as changed:
        for name in original.namelist():
            changed.writestr(name, b"tampered" if name == "subtitles.srt" else original.read(name))
    with pytest.raises(VideoError):
        verify_package(damaged)
    (service.store.root / jid / "explainer.mp4").write_bytes(b"tampered")
    with pytest.raises(VideoError):
        service.artifact(jid, "explainer.mp4")


def test_wrap_preserves_words():
    from PIL import Image, ImageDraw, ImageFont
    from MRL_Video.render import wrap
    draw = ImageDraw.Draw(Image.new("RGB", (300, 200)))
    font = ImageFont.truetype(str(FONT), 22)
    lines = wrap(draw, "Each caption maps to a source excerpt.", font, 180)
    assert " ".join(lines) == "Each caption maps to a source excerpt."


def test_expired_or_invalid_api_key(api):
    _, base = api
    assert http(base, "/api/jobs", headers={"x-api-key": "wrong"})[0] == 401


def test_missing_font_job_fails_without_delivery(tmp_path, request_data):
    service = Service(tmp_path / "queue", tmp_path, tmp_path / "absent.ttf")
    jid = service.store.submit(request_data)["id"]
    service.store.claim()
    service.process(jid)
    assert service.store.get(jid)["state"] == "FAILED"
    assert not (service.store.root / f"{jid}.zip").exists()
    with pytest.raises(VideoError):
        service.artifact(jid, "package.zip")


def test_crash_releases_worker_lock(tmp_path, request_data):
    import subprocess
    import sys
    root = tmp_path / "crash"
    script = ("from pathlib import Path; from MRL_Video.service import Service; import os; "
              f"s=Service(Path({str(root)!r}),Path({str(tmp_path)!r}),Path({str(FONT)!r})); "
              "s.start(); os._exit(0)")
    subprocess.run([sys.executable, "-c", script], check=True, env=dict(os.environ))
    service = Service(root, tmp_path, FONT)
    service.start()
    service.close()


def test_login_sets_private_cookie(api):
    import http.client
    from urllib.parse import urlencode, urlsplit
    _, base = api
    address = urlsplit(base)
    connection = http.client.HTTPConnection(address.hostname, address.port)
    data = urlencode({"key": "test-key-" * 5})
    connection.request("POST", "/login", data, {"Content-Type": "application/x-www-form-urlencoded"})
    response = connection.getresponse()
    assert response.status == 303
    cookie = response.getheader("Set-Cookie")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    assert "test-key-" not in cookie
    response.read()
    connection.close()


@pytest.mark.skipif(not os.environ.get("MRL_VIDEO_TEST_CJK_FONT"), reason="Local CJK font not configured")
@pytest.mark.skipif(os.environ.get("MRL_VIDEO_MEDIA_TEST") != "1", reason="Enable real-media acceptance")
def test_traditional_chinese_roundtrip(tmp_path):
    font = Path(os.environ["MRL_VIDEO_TEST_CJK_FONT"])
    request_data = {"schema": "MRL_Video_Request/v1", "title": "MRL 母體來源解說",
                    "profile": "portrait", "sources": [{"id": "source1", "original_name": "合成驗收資料",
                    "locator": "fixture:zh-Hant", "text": "來源文字保留原始名稱。\n每幕字幕對應原文。\n修改後建立新的子版本。\n交付封包先檢查完整性。"}]}
    service = Service(tmp_path / "zh", tmp_path, font)
    jid = service.store.submit(request_data)["id"]
    service.store.claim()
    service.process(jid)
    assert service.store.get(jid)["state"] == "SUCCEEDED", service.store.get(jid)
    assert verify_package(service.artifact(jid, "package.zip"))["status"] == "DELIVERY_PASS"

