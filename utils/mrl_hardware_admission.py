"""MRL-34 exact-combination admission. origin_signature: MrLiouWord.

Registry and its receipts are owner-reviewed policy, never supplied by a tenant.
No CUDA imports, device writes, installs, or environment mutation occur here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ORIGIN = 'MrLiouWord'
DEFAULT_MATRIX = Path(__file__).resolve().parents[1] / 'configs/MRL_hardware_matrix_v1.json'
FIELDS = ('vendor architecture sku compute_capability vram_mib driver os '
          'runtime runtime_version runtime_abi cuda rocm quantization '
          'model_runner model_runner_version model_digest track bundle_id bundle_digest').split()
DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
VERSION = re.compile(r'[0-9]+(?:\.[0-9]+){1,3}\Z')


def validate_manifest(manifest):
    """Require complete, typed observations; unknown values never match a profile."""
    if not isinstance(manifest, dict) or set(manifest) != set(FIELDS):
        raise ValueError('manifest fields must exactly match MRL hardware manifest v1')
    for key in FIELDS:
        value = manifest[key]
        if key == 'vram_mib':
            if type(value) is not int or value <= 0:
                raise ValueError('vram_mib must be a positive integer')
        elif key in ('cuda', 'rocm'):
            if value is not None and (not isinstance(value, str) or not VERSION.fullmatch(value)):
                raise ValueError(f'invalid {key} version')
        elif not isinstance(value, str) or not value.strip() or value.lower() in ('unknown', 'unverified'):
            raise ValueError(f'missing/unknown {key}')
    if manifest['track'] not in ('dl580-v100', 'modern-gpu'):
        raise ValueError('unknown track')
    for key in ('bundle_digest', 'model_digest'):
        if not DIGEST.fullmatch(manifest[key]):
            raise ValueError(f'invalid {key}')
    if not VERSION.fullmatch(manifest['driver']):
        raise ValueError('invalid driver version')
    vendor = manifest['vendor']
    if vendor == 'NVIDIA':
        if manifest['cuda'] is None or manifest['rocm'] is not None:
            raise ValueError('NVIDIA requires CUDA and no ROCm')
        if not re.fullmatch(r'[0-9]+\.[0-9]+', manifest['compute_capability']):
            raise ValueError('invalid NVIDIA compute capability')
    elif vendor == 'AMD':
        if manifest['rocm'] is None or manifest['cuda'] is not None:
            raise ValueError('AMD requires ROCm and no CUDA')
    else:
        raise ValueError('unknown vendor')


def policy_denial(manifest):
    """MRL V100 policy applies even when a registry accidentally allows a row."""
    volta = (manifest['architecture'].lower() == 'volta'
             or 'v100' in manifest['sku'].lower()
             or (manifest['vendor'] == 'NVIDIA' and manifest['compute_capability'] == '7.0'))
    if volta:
        if (manifest['vendor'], manifest['architecture'], manifest['compute_capability'], manifest['track']) != (
                'NVIDIA', 'Volta', '7.0', 'dl580-v100'):
            return 'V100_IDENTITY_OR_TRACK_MISMATCH'
        if not manifest['cuda'] or manifest['cuda'].split('.')[0] != '12':
            return 'V100_REQUIRES_VERIFIED_CUDA_12'
        if 'tensorrt' in manifest['model_runner'].lower():
            return 'V100_TENSORRT_NOT_ADMITTED'
    elif manifest['track'] == 'dl580-v100':
        return 'NON_V100_IN_DL580_TRACK'
    return None


def load_matrix(path=DEFAULT_MATRIX):
    """Validate reviewed allowlist and hash-bound on-disk hardware receipts."""
    path = Path(path).resolve()
    matrix = json.loads(path.read_text(encoding='utf-8'))
    if matrix['schema_version'] != 'MRL.hardware_matrix/v1' or matrix['origin_signature'] != ORIGIN:
        raise ValueError('invalid matrix identity')
    rows = matrix['verified_combinations']
    if not isinstance(rows, list):
        raise ValueError('verified_combinations must be a list')
    ownership = {}
    for row in rows:
        manifest = row['manifest']
        validate_manifest(manifest)
        if policy_denial(manifest):
            raise ValueError('registry violates V100 policy')
        evidence = row['acceptance']
        receipt_path = (path.parent / evidence['path']).resolve()
        if not receipt_path.is_relative_to(path.parent):
            raise ValueError('receipt must remain within matrix directory')
        raw = receipt_path.read_bytes()
        if 'sha256:' + hashlib.sha256(raw).hexdigest() != evidence['digest']:
            raise ValueError('acceptance receipt digest mismatch')
        receipt = json.loads(raw)
        if (receipt['origin_signature'] != ORIGIN or receipt['status'] != 'hardware_verified'
                or receipt['manifest'] != manifest or receipt['acceptance_id'] != evidence['id']
                or not receipt['observed_at'] or not receipt['source']
                or set(receipt['checks']) != {'device_query', 'runtime_smoke', 'model_smoke'}
                or any(value is not True for value in receipt['checks'].values())):
            raise ValueError('incomplete hardware acceptance receipt')
        # Tracks must never share package identity, bytes, or acceptance records.
        for key, value in [('bundle_id', manifest['bundle_id']), ('bundle_digest', manifest['bundle_digest']),
                           ('acceptance_id', evidence['id']), ('receipt_digest', evidence['digest'])]:
            previous = ownership.setdefault((key, value), manifest['track'])
            if previous != manifest['track']:
                raise ValueError('cross-track bundle or acceptance reuse')
    return matrix


def admit(manifest, matrix_path=DEFAULT_MATRIX):
    """Return a JSON-serializable decision; every error denies admission."""
    result = {'origin_signature': ORIGIN, 'admitted': False, 'reason': 'UNKNOWN_COMBINATION'}
    try:
        validate_manifest(manifest)
        denial = policy_denial(manifest)
        if denial:
            return dict(result, reason=denial)
        matrix = load_matrix(matrix_path)
        for row in matrix['verified_combinations']:
            if row['manifest'] == manifest:
                return dict(result, admitted=True, reason='VERIFIED_EXACT_COMBINATION',
                            acceptance_id=row['acceptance']['id'], track=manifest['track'])
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as error:
        return dict(result, reason='INVALID_OR_INCOMPLETE_EVIDENCE', detail=str(error))
    return result


def main(argv=None):
    """Exit 0 only for admitted manifests; invalid/unknown input exits 2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=DEFAULT_MATRIX)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--validate-matrix', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.validate_matrix:
            matrix = load_matrix(args.matrix)
            result = {'matrix_valid': True, 'verified_count': len(matrix['verified_combinations'])}
            code = 0
        else:
            if args.manifest is None:
                parser.error('--manifest is required unless --validate-matrix is used')
            result = admit(json.loads(args.manifest.read_text(encoding='utf-8')), args.matrix)
            code = 0 if result['admitted'] else 2
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        result, code = {'admitted': False, 'reason': 'INVALID_INPUT', 'detail': str(error)}, 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
