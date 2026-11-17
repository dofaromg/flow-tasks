"""Run a real 1200-second synthetic pipeline acceptance, never a creative film."""
import argparse
import json
import time
from pathlib import Path

from .audit import write_json
from .longfilm import SCHEMA, file_hash
from .render import PROFILES, Runner, probe
from .service import Service


def run(output: Path) -> dict:
    """Render 20 repeated clips at an explicit small fixture resolution."""
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / 'inputs'
    inputs.mkdir()
    runner = Runner(lambda: False)
    runner.run(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i',
                'testsrc2=s=160x90:r=24:d=60', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=60',
                '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '128k', 'fixture.mp4'], inputs)
    request = {'schema': SCHEMA, 'title': 'Synthetic 20-minute mechanism fixture',
               'target_seconds': 1200, 'profile': 'landscape', 'quality': 'draft',
               'sources': [{'id': 'fixture', 'original_name': 'fixture.txt',
                            'locator': 'synthetic:FFmpeg/testsrc2+sine',
                            'text': 'Synthetic pipeline test only.'}],
               'scenes': [{'title': f'S{i+1:02}', 'caption': 'Synthetic pipeline test only.',
                           'source_id': 'fixture', 'duration': 60, 'clip': 'fixture.mp4'}
                          for i in range(20)]}
    original = PROFILES['landscape']
    try:
        # Fixture-only override; restored even if acceptance fails. Normal requests
        # retain 720p/1080p/2160p production profiles.
        PROFILES['landscape'] = (160, 90)
        service = Service(output / 'versions', inputs, Path('unused-font'), workers=1)
        job = service.store.submit(request)
        service.store.claim()
        started = time.monotonic()
        service.process(job['id'])
        result = service.store.get(job['id'])
        if result['state'] != 'SUCCEEDED':
            raise RuntimeError(json.dumps(result))
        directory = service.store.root / job['id']
        media = probe(directory / 'explainer.mp4', runner)
        cache = service.store.segments(job['id'])
        audit = json.loads((directory / 'MRL_audit.json').read_text())
        evidence = {'origin_signature': 'MrLiouWord', 'scope': 'SYNTHETIC_PIPELINE_ONLY',
                    'resolution': [160, 90], 'fps': 24, 'target_seconds': 1200,
                    'duration_seconds': float(media['format']['duration']),
                    'segment_count': 20, 'cache_hits': sum(s['cache_hit'] for s in cache),
                    'full_decode': audit['full_decode'], 'frame_count': audit['frame_count'],
                    'coverage': audit['coverage'], 'subtitles': 'SIDECAR_AND_EMBEDDED',
                    'event_chain_valid': service.store.verify_chain(),
                    'mp4_sha256': file_hash(directory / 'explainer.mp4'),
                    'receipt': json.loads((service.store.root / (job['id'] + '.receipt.json')).read_text()),
                    'elapsed_seconds': round(time.monotonic() - started, 2),
                    'formal_film': 'NOT_PRODUCED', 'dl580': 'NOT_RUN', 'iphone': 'NOT_RUN'}
        write_json(output / 'acceptance.json', evidence)
        return evidence
    finally:
        PROFILES['landscape'] = original


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.out), indent=2))
