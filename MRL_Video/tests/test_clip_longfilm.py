"""Real clip assembly, cache corruption, interruption and frame-clock acceptance."""
import json
import os
from pathlib import Path

import pytest

from MRL_Video.audit import verify_package
from MRL_Video.episode_adapter import import_episode
from MRL_Video.longfilm import SCHEMA, assert_file_snapshot, file_hash, file_snapshot, timeline
from MRL_Video.model import VideoError, validate
from MRL_Video.render import PROFILES, Runner, probe, srt
from MRL_Video.service import Service
from MRL_Video.store import Store


def request(duration=4, count=2):
    return {'schema': SCHEMA, 'title': 'Synthetic pipeline fixture', 'target_seconds': duration*count,
            'profile': 'landscape', 'quality': 'draft',
            'sources': [{'id': 'fixture', 'original_name': 'fixture.txt', 'locator': 'synthetic:test',
                         'text': 'Synthetic pipeline test. Second clip.'}],
            'scenes': [{'title': f'S{i}', 'caption': 'Synthetic pipeline test.', 'source_id': 'fixture',
                        'clip': 'clip.mp4', 'duration': duration} for i in range(count)]}


@pytest.mark.parametrize('mutate', [
    lambda r: r.update(target_seconds=1200),
    lambda r: r['scenes'][0].update(duration=4.01),
    lambda r: r['scenes'][0].update(transition='unknown'),
    lambda r: r['scenes'][0].update(caption='Invented'),
    lambda r: r['scenes'][0].update(allow_silent='yes'),
    lambda r: r.update(quality='unknown'),
    lambda r: r.update(extra=True),
])
def test_contract_rejections(mutate):
    r = request()
    mutate(r)
    with pytest.raises(VideoError):
        validate(r)


def test_20min_frame_clock():
    r = validate(request(60, 20))
    rows = timeline(r)
    assert rows[-1]['end_frame'] == 28800
    assert rows[-1]['audio_end_sample'] == 57600000
    assert all(a['end_frame'] == b['start_frame'] for a, b in zip(rows, rows[1:]))
    assert '00:19:00,000 --> 00:20:00,000' in srt(r)
    assert validate(r) == r


def test_segment_shrink_after_seal_is_rejected_with_identity_diagnostics(tmp_path):
    segment = tmp_path / 'segment_001.mkv'
    with segment.open('wb') as stream:
        stream.truncate(12_282_553)
    sealed = file_snapshot(segment)
    with segment.open('r+b') as stream:
        stream.truncate(11_534_336)
    with pytest.raises(VideoError, match='Segment changed after validation') as error:
        assert_file_snapshot(segment, sealed, 'Segment changed after validation')
    details = json.loads(str(error.value).split(': ', 1)[1])
    assert details['expected']['size'] == 12_282_553
    assert details['observed']['size'] == 11_534_336
    assert details['expected']['sha256'] != details['observed']['sha256']
    assert details['expected']['file_identity'] == details['observed']['file_identity']


def test_import_preserves_original(tmp_path):
    p = tmp_path/'original_episode.json'
    ep = {'episode_id': 'MRL', 'target_seconds': 8, 'characters': [{'id': 'OriginalCast'}],
          'shots': [{'id': 'S1', 'seconds': 4, 'media': 'clip.mp4', 'line': 'Original line.'},
                    {'id': 'S2', 'seconds': 4, 'media': 'clip.mp4', 'line': 'Next line.'}]}
    raw = json.dumps(ep)
    p.write_text(raw)
    imported = import_episode(p)
    assert p.read_text() == raw
    assert imported['sources'][1]['text'] == raw
    assert imported['scenes'][0]['clip'] == 'clip.mp4'


def test_recovery_creates_child(tmp_path):
    store = Store(tmp_path)
    old = store.submit(request())
    store.claim()
    store.prepare_segments(old['id'], 2)
    store.segment_state(old['id'], 0, 'RUNNING', 'a'*64)
    store.recover()
    assert store.segments(old['id'])[0]['state'] == 'INTERRUPTED'
    new = store.retry(old['id'])
    assert new['parent_id'] == old['id'] and new['version_index'] > old['version_index']
    assert store.request(old['id']) == store.request(new['id'])
    assert store.verify_chain()
    with pytest.raises(VideoError):
        store.retry(new['id'])


@pytest.fixture
def media(tmp_path, monkeypatch):
    if not os.environ.get('MRL_VIDEO_MEDIA_TEST'):
        pytest.skip('Set MRL_VIDEO_MEDIA_TEST=1 for FFmpeg tests')
    # Explicit synthetic fixture resolution, never a production quality claim.
    monkeypatch.setitem(PROFILES, 'landscape', (160, 90))
    assets = tmp_path/'inputs'
    assets.mkdir()
    runner = Runner(lambda: False)
    runner.run(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i',
                'testsrc2=s=160x90:r=24:d=4', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=4',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', 'clip.mp4'], assets)
    return Service(tmp_path/'versions', assets, Path('unused-font'), workers=1), assets


def process(service, r, parent=None):
    job = service.store.submit(r, parent_id=parent)
    assert service.store.claim() == job['id']
    service.process(job['id'])
    return service.store.get(job['id'])


def test_real_cache_subtitles_and_tamper(media):
    service, assets = media
    first = process(service, request())
    assert first['state'] == 'SUCCEEDED', first
    root = service.store.root/first['id']
    assert verify_package(service.store.root/(first['id']+'.zip'))['coverage'] == 100
    info = probe(root/'explainer.mp4', Runner(lambda: False))
    audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    assert abs(float(audio['duration']) - 8) < .05
    before = file_hash(root/'explainer.mp4')
    child = process(service, request(), first['id'])
    assert child['state'] == 'SUCCEEDED', child
    assert all(s['cache_hit'] for s in service.store.segments(child['id']))
    assert file_hash(root/'explainer.mp4') == before
    # Poisoned payload must be rejected and rebuilt, never accepted on filename alone.
    cached = next((service.store.root/'MRL_segment_cache').glob('*.mkv'))
    cached.write_bytes(b'corrupt')
    next_job = process(service, request())
    assert next_job['state'] == 'SUCCEEDED', next_job
    assert not service.store.segments(next_job['id'])[0]['cache_hit']
    assert service.store.verify_chain()
    (root/'explainer.mp4').write_bytes(b'corrupt')
    with pytest.raises(VideoError):
        service.artifact(first['id'], 'explainer.mp4')


def test_failure_resume_keeps_completed_segments(media):
    service, assets = media
    r = request()
    r['scenes'][1]['in_seconds'] = 3
    failed = process(service, r)
    assert failed['state'] == 'FAILED'
    assert service.store.segments(failed['id'])[0]['state'] == 'SUCCEEDED'
    r['scenes'][1]['in_seconds'] = 0
    r['scenes'][1]['transition'] = 'fade'
    child = process(service, r, failed['id'])
    assert child['state'] == 'SUCCEEDED', child
    assert service.store.segments(child['id'])[0]['cache_hit']
    assert not service.store.segments(child['id'])[1]['cache_hit']


def test_silent_and_traversal(media):
    service, assets = media
    runner = Runner(lambda: False)
    runner.run(['ffmpeg', '-v', 'error', '-n', '-i', 'clip.mp4', '-an', '-c:v', 'copy', 'silent.mp4'], assets)
    r = request()
    for s in r['scenes']:
        s['clip'] = 'silent.mp4'
    assert process(service, r)['state'] == 'FAILED'
    for s in r['scenes']:
        s['allow_silent'] = True
    accepted = process(service, r)
    assert accepted['state'] == 'SUCCEEDED', accepted
    r['scenes'][0]['clip'] = '../clip.mp4'
    assert process(service, r)['state'] == 'FAILED'


def test_fullhd_real_profile(media):
    service, assets = media
    r = request(duration=2, count=1)
    r.update(profile="fullhd", quality="fullhd")
    job = process(service, r)
    assert job["state"] == "SUCCEEDED", job
    info = probe(service.store.root/job["id"]/"explainer.mp4", Runner(lambda: False))
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], int(video["nb_frames"])) == (1920, 1080, 48)


def test_retry_reuses_frozen_parent_assets(media):
    service, assets = media
    old = service.store.submit(request())
    service.store.claim()
    service.process(old['id'])
    assert service.store.get(old['id'])['state'] == 'SUCCEEDED'
    # Simulate a terminal interrupted status after rendering, then change the live
    # input. A child retry must use the frozen parent snapshot.
    with service.store.connect() as db:
        db.execute("UPDATE jobs SET state='INTERRUPTED' WHERE id=?", (old['id'],))
    (assets/'clip.mp4').write_bytes(b'changed live source')
    child = service.store.retry(old['id'])
    service.store.claim()
    service.process(child['id'])
    assert service.store.get(child['id'])['state'] == 'SUCCEEDED'
    assert all(r['cache_hit'] for r in service.store.segments(child['id']))


def test_delayed_audio_is_rejected(media):
    service, assets = media
    runner = Runner(lambda: False)
    runner.run(['ffmpeg', '-v', 'error', '-n', '-i', 'clip.mp4', '-itsoffset', '1',
                '-i', 'clip.mp4', '-map', '0:v', '-map', '1:a', '-c', 'copy', 'delayed.mp4'], assets)
    r = request()
    for scene in r['scenes']:
        scene['clip'] = 'delayed.mp4'
    job = process(service, r)
    assert job['state'] == 'FAILED'
    assert 'start timestamps' in job['error']
