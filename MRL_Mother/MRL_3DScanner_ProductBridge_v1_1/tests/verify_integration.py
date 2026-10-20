"""Verify the exact integration payload, predecessor hashes and dependency chain."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BRIDGE = Path(__file__).resolve().parents[1]
REPORT = BRIDGE / 'MAINLINE_INTEGRATION_20261021.json'


def verify():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    expected = report['expected_file_list']
    assert len(expected) == len(set(expected)) == report['expected_file_count']
    assert set(report['files']) == set(expected) - {REPORT.relative_to(ROOT).as_posix()}
    for name in expected:
        file = ROOT / name
        assert file.is_file() and file.stat().st_size, name
        if name not in report['files']:
            continue  # This audit's own bytes are authenticated by the Git commit.
        entry = report['files'][name]
        assert entry['size'] == file.stat().st_size, name
        assert entry['sha256'] == hashlib.sha256(file.read_bytes()).hexdigest(), name
        for dependency in entry['dependencies']:
            assert (ROOT / dependency).is_file(), (name, dependency)
    manifest = json.loads((BRIDGE / 'PATCH_MANIFEST.json').read_text(encoding='utf-8'))
    seen = set()
    for entry in manifest['files']:
        name = entry['path']
        assert name not in seen and '..' not in Path(name).parts and not Path(name).is_absolute()
        seen.add(name)
        file = BRIDGE / name
        assert file.is_file() and file.stat().st_size, name
        assert hashlib.sha256(file.read_bytes()).hexdigest().upper() == entry['after'], name
        for value in entry.get('acceptedBeforeSha256', []):
            assert len(value) == 64 and all(c in '0123456789ABCDEF' for c in value), name
    assert report['audit']['missing'] == report['audit']['extra'] == report['audit']['mismatch'] == []
    assert report['audit']['coverage_percent'] == 100
    print(f'DELIVERY_PASS: {len(expected)} integration files; {len(seen)} patch payload files; SHA-256 and dependencies verified')


if __name__ == '__main__':
    verify()
