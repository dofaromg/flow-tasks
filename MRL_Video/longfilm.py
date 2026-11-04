"""Reusable local clip timeline, frame-exact normalization and verified cache.

origin_signature: MrLiouWord. Consumes existing MRL module outputs; never calls
models or services. PCM segments avoid repeated AAC encoder delay at joins.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from .contract import VideoError, canonical, digest, keys, local_file, number, text
from .render import FPS, PROFILES, probe, srt

SCHEMA = 'MRL_LongFilm_Request/v1'
QUALITIES = {'draft': ('veryfast', 25), 'fullhd': ('fast', 18), 'uhd': ('medium', 18)}


def file_hash(path: Path) -> str:
    """Hash large media in bounded memory."""
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_longfilm(request: dict) -> dict:
    """Explicit clip timeline; reject rounding drift, invented captions and options."""
    keys(request, {'schema', 'title', 'sources', 'scenes', 'profile', 'quality',
                   'target_seconds', 'source_commit'}, 'long-film request')
    title = text(request.get('title'), 100, 'title')
    sources = request.get('sources')
    if not isinstance(sources, list) or not 1 <= len(sources) <= 32:
        raise VideoError('Provide 1..32 sources')
    ids = set()
    for source in sources:
        keys(source, {'id', 'original_name', 'text', 'locator', 'sha256'}, 'source')
        import re
        sid = text(source.get('id'), 48, 'source id')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', sid) or sid in ids:
            raise VideoError('Duplicate or invalid source id')
        ids.add(sid)
        body = text(source.get('text'), 50000, 'source text')
        text(source.get('original_name'), 200, 'original name')
        text(source.get('locator'), 500, 'locator')
        if source.get('sha256', digest(body.encode())) != digest(body.encode()):
            raise VideoError('Source digest mismatch')
    if sum(len(s['text']) for s in sources) > 200000:
        raise VideoError('Source budget exceeded')
    profile = request.get('profile', 'landscape')
    quality = request.get('quality', 'draft')
    if profile not in PROFILES or quality not in QUALITIES:
        raise VideoError('Unsupported profile or quality')
    target = number(request.get('target_seconds', 1200), 2, 1200, 'target_seconds')
    scenes = request.get('scenes')
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 600:
        raise VideoError('Provide 1..600 explicit clip segments')
    normalized = []
    frames = 0
    for scene in scenes:
        keys(scene, {'title', 'caption', 'source_id', 'duration', 'clip', 'in_seconds',
                     'allow_silent', 'transition'}, 'segment')
        text(scene.get('title'), 100, 'segment title')
        caption = text(scene.get('caption'), 240, 'caption')
        source = next((s for s in sources if s['id'] == scene.get('source_id')), None)
        if source is None or caption not in source['text']:
            raise VideoError('Each caption must be a verbatim excerpt from its named source')
        text(scene.get('clip'), 240, 'clip')
        duration = number(scene.get('duration'), 2, 120, 'segment duration')
        start = number(scene.get('in_seconds', 0), 0, 86400, 'clip in point')
        if abs(duration * FPS - round(duration * FPS)) > 1e-6:
            raise VideoError('Segment duration must align to 24 FPS frames')
        if type(scene.get('allow_silent', False)) is not bool:
            raise VideoError('allow_silent must be boolean')
        transition = scene.get('transition', 'cut')
        if transition not in {'cut', 'fade'}:
            raise VideoError('Unsupported transition')
        frames += round(duration * FPS)
        normalized.append(dict(scene, duration=duration, in_seconds=start,
                               allow_silent=scene.get('allow_silent', False), transition=transition))
    if abs(frames / FPS - target) > 1e-6:
        raise VideoError('Timeline duration must equal target_seconds')
    commit = request.get('source_commit')
    if commit is not None:
        import re
        if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise VideoError('source_commit must be an exact Git SHA')
    return dict(request, title=title, scenes=normalized, profile=profile,
                quality=quality, target_seconds=target)


def timeline(request: dict) -> list[dict]:
    """One integer frame clock for subtitles, clip boundaries and audio samples."""
    position = 0
    rows = []
    for i, scene in enumerate(request['scenes']):
        end = position + round(scene['duration'] * FPS)
        rows.append({'segment': i, 'start_frame': position, 'end_frame': end,
                     'start_seconds': position / FPS, 'end_seconds': end / FPS,
                     'audio_start_sample': position * 2000, 'audio_end_sample': end * 2000,
                     'clip': scene['clip'], 'in_seconds': scene['in_seconds'],
                     'caption': scene['caption'], 'source_id': scene['source_id']})
        position = end
    return rows


def check_segment(path: Path, frames: int, dimensions: tuple, runner) -> dict:
    """Reject unreadable segments or timebases incompatible with concatenation."""
    info = probe(path, runner)
    videos = [s for s in info['streams'] if s['codec_type'] == 'video']
    audios = [s for s in info['streams'] if s['codec_type'] == 'audio']
    if (len(videos) != 1 or len(audios) != 1
            or videos[0]['codec_name'] != 'h264' or audios[0]['codec_name'] != 'pcm_s16le'
            or (videos[0]['width'], videos[0]['height']) != dimensions
            or videos[0]['r_frame_rate'] != '24/1' or audios[0]['sample_rate'] != '48000'
            or audios[0]['channels'] != 2
            or abs(float(info['format']['duration']) - frames / FPS) > .025):
        raise VideoError('Segment media contract mismatch')
    counted = json.loads(runner.run(['ffprobe', '-v', 'error', '-count_frames',
                                    '-select_streams', 'v:0', '-show_entries',
                                    'stream=nb_read_frames', '-of', 'json', str(path.resolve())], path.parent))
    if int(counted['streams'][0]['nb_read_frames']) != frames:
        raise VideoError('Segment frame count mismatch')
    runner.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path.resolve()),
                '-f', 'null', '-'], path.parent)
    return info


def render_longfilm(request, work, assets, runner, phase, store, jid, workers):
    """Queue/cache each segment, then stream-copy video with one final AAC encode."""
    width, height = PROFILES[request['profile']]
    preset, crf = QUALITIES[request['quality']]
    clock = timeline(request)
    cache = store.root / 'MRL_segment_cache'
    cache.mkdir(exist_ok=True)
    # Changing renderer, tool build or quality invalidates cached outputs.
    identity = {'renderer': file_hash(Path(__file__)),
                'ffmpeg': runner.run(['ffmpeg', '-version'], work),
                'profile': request['profile'], 'quality': request['quality'], 'dimensions': [width, height]}
    store.prepare_segments(jid, len(clock))
    phase('BUILD_SEGMENTS')

    def build(index):
        scene = request['scenes'][index]
        row = clock[index]
        source = local_file(assets, scene['clip'], 2 * 1024 ** 3)
        frames = row['end_frame'] - row['start_frame']
        spec = {**identity, 'input_sha256': file_hash(source), 'frames': frames,
                'in_seconds': scene['in_seconds'], 'allow_silent': scene['allow_silent'],
                'transition': scene['transition']}
        key = digest(canonical(spec))
        target = work / f'segment_{index + 1:03}.mkv'
        cached, receipt = cache / (key + '.mkv'), cache / (key + '.json')
        store.segment_state(jid, index, 'RUNNING', key)
        hit = False
        try:
            runner.check()
            if cached.is_file() and receipt.is_file():
                try:
                    saved = json.loads(receipt.read_text(encoding='utf-8'))
                    hit = saved['sha256'] == file_hash(cached) and saved['spec'] == spec
                except (ValueError, KeyError):
                    hit = False
            if hit:
                shutil.copyfile(cached, target)
                check_segment(target, frames, (width, height), runner)
            else:
                info = probe(source, runner)
                video = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
                if video is None:
                    raise VideoError('Clip has no video')
                available = float(video.get('duration') or info['format']['duration'])
                if not math.isfinite(available) or available + .001 < scene['in_seconds'] + scene['duration']:
                    raise VideoError('Clip shorter than requested interval')
                audio = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
                if not audio and not scene['allow_silent']:
                    raise VideoError('Silent segment requires allow_silent')
                if audio:
                    if abs(float(audio.get('start_time', 0)) - float(video.get('start_time', 0))) > 1 / FPS:
                        raise VideoError('Source audio/video start timestamps are not aligned')
                    audio_duration = float(audio.get('duration') or info['format']['duration'])
                    if audio_duration + .025 < scene['in_seconds'] + scene['duration']:
                        raise VideoError('Clip audio shorter than requested interval')
                args = ['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', str(scene['in_seconds']),
                        '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm',
                        '-i', str(source.resolve())]
                if not audio:
                    args += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
                filters = (f'scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,'
                           f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,setpts=PTS-STARTPTS')
                if scene['transition'] == 'fade':
                    filters += f",fade=t=in:st=0:d=0.25,fade=t=out:st={scene['duration']-.25}:d=0.25"
                args += ['-map', '0:v:0', '-map', '0:a:0' if audio else '1:a:0',
                         '-vf', filters, '-af', 'aresample=48000,asetpts=PTS-STARTPTS',
                         '-t', str(scene['duration']), '-c:v', 'libx264', '-preset', preset,
                         '-crf', str(crf), '-threads', '2', '-pix_fmt', 'yuv420p',
                         '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', target.name]
                runner.run(args, work)
                check_segment(target, frames, (width, height), runner)
                # Atomic cache publication; unique staging avoids concurrent duplicate keys.
                with tempfile.TemporaryDirectory(dir=cache) as staging:
                    tmp = Path(staging)
                    shutil.copyfile(target, tmp / 'clip.mkv')
                    (tmp / 'receipt.json').write_bytes(canonical({'spec': spec, 'sha256': file_hash(target)}))
                    os.replace(tmp / 'clip.mkv', cached)
                    os.replace(tmp / 'receipt.json', receipt)
            runner.run(['ffmpeg', '-v', 'error', '-n', '-ss', str(scene['duration']/2),
                        '-i', target.name, '-frames:v', '1', f'scene_{index+1:02}.png'], work)
            store.segment_state(jid, index, 'SUCCEEDED', key, hit)
            return {**row, 'cache_key': key, 'cache_hit': hit, 'sha256': file_hash(target),
                    'quality': request['quality'], 'transition': scene['transition']}
        except BaseException:
            store.segment_state(jid, index, 'FAILED', key)
            runner.failed.set()
            raise

    # Bounded batches avoid enqueueing hundreds of futures after cancellation.
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for start in range(0, len(clock), workers):
            runner.check()
            results.extend(pool.map(build, range(start, min(len(clock), start + workers))))
    for i, result in enumerate(results):
        runner.check()
        if file_hash(work / f'segment_{i+1:03}.mkv') != result['sha256']:
            raise VideoError('Segment changed after validation')
    phase('COMPOSE_VIDEO')
    (work / 'subtitles.srt').write_text(srt(request), encoding='utf-8')
    (work / 'concat.txt').write_text(''.join(
        f"file 'segment_{i+1:03}.mkv'\nduration {s['duration']}\n"
        for i, s in enumerate(request['scenes'])), encoding='utf-8')
    # One final encode of the continuous PCM timeline prevents per-clip AAC padding.
    runner.run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '1', '-i', 'concat.txt',
                '-i', 'subtitles.srt', '-map', '0:v:0', '-map', '0:a:0', '-map', '1:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-c:s', 'mov_text',
                '-t', str(request['target_seconds']), '-movflags', '+faststart', 'explainer.mp4'], work)
    # Keep preview memory/size bounded independently of feature length.
    runner.run(['ffmpeg', '-v', 'error', '-n', '-i', 'explainer.mp4', '-vf',
                f"fps=1/{max(2, request['target_seconds']/24)},scale=240:-1",
                '-frames:v', '24', 'explainer-preview.gif'], work)
    board = Image.new('RGB', (640, 180 * math.ceil(min(24, len(results))/2)))
    for n in range(min(24, len(results))):
        i = n * len(results) // min(24, len(results))
        with Image.open(work / f'scene_{i+1:02}.png') as tile:
            tile.thumbnail((320, 180))
            board.paste(tile, (n % 2 * 320, n // 2 * 180))
    board.save(work / 'explainer-stills.png')
    from .audit import write_json
    write_json(work / 'timeline.json', {'fps': FPS, 'sample_rate': 48000, 'segments': results,
                                      'origin_signature': 'MrLiouWord'})
    return {'segments': results, 'cache_hits': sum(r['cache_hit'] for r in results),
            'font_sha256': None, 'renderer': 'CPU/libx264 + PCM timeline',
            'semantic_review': 'OWNER_REVIEW_REQUIRED'}
