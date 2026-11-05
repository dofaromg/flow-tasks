"""Import existing R01/R03 or Creator Studio episodes without renaming originals."""
from pathlib import Path
import json

from .longfilm import SCHEMA, validate_longfilm
from .model import VideoError, digest


def import_episode(path: Path, profile: str = 'landscape', quality: str = 'draft') -> dict:
    """Bind original episode bytes and explicit shot lines to local clip paths."""
    raw = path.read_text(encoding='utf-8')
    episode = json.loads(raw)
    shots = episode.get('shots')
    if not isinstance(shots, list) or not shots:
        raise VideoError('Episode has no explicit shots')
    # No automatic repeated story or invented replacement lines.
    scenes = [{'title': str(s['id']), 'caption': s['line'], 'source_id': 'episode_lines',
               'duration': s['seconds'], 'clip': s['media']} for s in shots]
    source_hash = digest(raw.encode('utf-8'))
    request = {'schema': SCHEMA, 'title': episode.get('title', episode['episode_id']),
               'profile': profile, 'quality': quality, 'target_seconds': episode['target_seconds'],
               'sources': [{'id': 'episode_lines', 'original_name': path.name,
                            'locator': 'owner:episode-lines#sha256=' + source_hash,
                            'text': '\n'.join(s['line'] for s in shots)},
                           {'id': 'episode_original', 'original_name': path.name,
                            'locator': 'owner:episode-original', 'text': raw, 'sha256': source_hash}],
               'scenes': scenes}
    return validate_longfilm(request)
