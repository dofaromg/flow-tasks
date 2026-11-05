#!/usr/bin/env python3
"""Offline Runtime Artifact Trust Gate. origin_signature: MrLiouWord.

The caller supplies a separately reviewed policy, never trust material from the
artifact itself. Receipts are replay records, never standalone authorizations.
OpenSSL 3+ verifies Ed25519; no runtime artifact is imported or executed.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import shutil
import tempfile

from MRL_hardware_admission_v1 import artifact_digest, digest

ORIGIN = 'MrLiouWord'
VERSION = 'MRL_Artifact_Trust_v1.0.0'
POLICY = Path(__file__).resolve().parents[1] / 'trust/MRL_artifact_trust_policy_v1.json'
HEX256 = re.compile(r'sha256:[0-9a-f]{64}\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')
REPOSITORY = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z')
RELEASE = re.compile(r'v?[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?\Z')


def openssl_command() -> str:
    """Find system OpenSSL, including Git for Windows; no downloads or installs."""
    command = shutil.which('openssl')
    if command:
        return command
    candidate = Path('C:/Program Files/Git/usr/bin/openssl.exe')
    if candidate.is_file():
        return str(candidate)
    raise ValueError('OpenSSL 3+ is required for signature verification')


def canonical(value: object) -> bytes:
    """Canonical signed JSON; reject non-finite numbers."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def load_json(path: Path) -> dict:
    """Read strict JSON, rejecting duplicate keys and non-object roots."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON')))
    if not isinstance(value, dict):
        raise ValueError('expected JSON object')
    return value


def required(obj, names):
    """Equivalent manifest schema validator, including exact key coverage."""
    if not isinstance(obj, dict) or set(obj) != set(names):
        raise ValueError('schema fields mismatch: ' + ','.join(names))
    if any(obj[n] is None or obj[n] == '' for n in names):
        raise ValueError('empty required evidence')


def file_bytes(root: Path, relative: str, expected: str) -> bytes:
    """Reuse canonical path confinement and actual byte hashing."""
    if not isinstance(expected, str) or not HEX256.fullmatch(expected):
        raise ValueError('invalid evidence digest')
    if artifact_digest(root, relative) != expected:
        raise ValueError('evidence bytes drift: ' + relative)
    path = root / relative
    if not path.is_file():
        raise ValueError('evidence must be a file')
    raw = path.read_bytes()
    if 'sha256:' + hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('evidence changed while reading')
    return raw


def verify_signature(public_hex: str, signature_b64: str, payload: bytes) -> str:
    """Verify Ed25519 over canonical manifest bytes, returning SPKI fingerprint."""
    if not re.fullmatch(r'[0-9a-f]{64}', public_hex):
        raise ValueError('invalid Ed25519 public key')
    signature = base64.b64decode(signature_b64, validate=True)
    if len(signature) != 64:
        raise ValueError('invalid Ed25519 signature length')
    der = bytes.fromhex('302a300506032b6570032100' + public_hex)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root/'key.der').write_bytes(der)
        (root/'payload').write_bytes(payload)
        (root/'signature').write_bytes(signature)
        result = subprocess.run([openssl_command(), 'pkeyutl', '-verify', '-pubin',
                                 '-keyform', 'DER', '-inkey', str(root/'key.der'),
                                 '-rawin', '-in', str(root/'payload'),
                                 '-sigfile', str(root/'signature')],
                                capture_output=True, timeout=20, check=False)
        if result.returncode != 0:
            raise ValueError('signature verification failed')
    return 'sha256:' + hashlib.sha256(der).hexdigest()


def verify(manifest: dict, policy: dict, root: Path, purpose='release') -> dict:
    """Fail closed; bind reviewed identity, signed evidence and actual bytes."""
    if purpose not in ('release', 'canary'):
        raise ValueError('unknown verification purpose')
    required(manifest, ('schema', 'origin_signature', 'artifact', 'sbom', 'provenance',
                        'signing', 'exception_approver'))
    if manifest['schema'] != 'MRL_Artifact_Trust_Manifest_v1' or manifest['origin_signature'] != ORIGIN:
        raise ValueError('manifest identity mismatch')
    # v1 deliberately provides no exception bypass.
    if manifest['exception_approver'] != 'NONE':
        raise ValueError('exceptions require a separately reviewed future policy')
    artifact = manifest['artifact']
    required(artifact, ('id', 'kind', 'version', 'repository', 'source_commit', 'digest', 'path'))
    if (artifact['kind'] not in ('wheel', 'oci_manifest', 'native')
            or not RELEASE.fullmatch(artifact['version'])
            or not REPOSITORY.fullmatch(artifact['repository'])
            or not SHA.fullmatch(artifact['source_commit'])
            or not HEX256.fullmatch(artifact['digest'])):
        raise ValueError('invalid immutable artifact identity')
    file_bytes(root, artifact['path'], artifact['digest'])
    if artifact['kind'] == 'oci_manifest':
        # This gate validates exported manifest bytes, not registry tags or layer availability.
        image = json.loads((root/artifact['path']).read_bytes())
        if image.get('schemaVersion') != 2 or not (image.get('layers') or image.get('manifests')):
            raise ValueError('invalid OCI manifest bytes')
    if (policy.get('schema') != 'MRL_Artifact_Trust_Policy_v1'
            or policy.get('origin_signature') != ORIGIN
            or not isinstance(policy.get('keys'), list)
            or not isinstance(policy.get('artifacts'), list)):
        raise ValueError('invalid trusted policy')
    signing = manifest['signing']
    required(signing, ('algorithm', 'fingerprint', 'signature'))
    if signing['algorithm'] != 'Ed25519':
        raise ValueError('unsupported signature algorithm')
    keys = [k for k in policy['keys'] if k.get('fingerprint') == signing['fingerprint']]
    if len(keys) != 1 or keys[0].get('status') != 'active':
        raise ValueError('unapproved, retired or revoked signing key')
    signed = {k: v for k, v in manifest.items() if k != 'signing'}
    actual_fp = verify_signature(keys[0]['public_key_hex'], signing['signature'], canonical(signed))
    if actual_fp != signing['fingerprint']:
        raise ValueError('signing key fingerprint mismatch')
    identity = {k: artifact[k] for k in ('id', 'kind', 'version', 'repository', 'source_commit', 'digest')}
    identity['fingerprint'] = actual_fp
    records = [r for r in policy['artifacts'] if r.get('identity') == identity]
    if len(records) != 1:
        raise ValueError('repository/source/digest/key binding not approved')
    record = records[0]
    for label in ('sbom', 'provenance'):
        required(manifest[label], ('path', 'digest'))
        raw = file_bytes(root, manifest[label]['path'], manifest[label]['digest'])
        # Signed references must also match the separately reviewed allowlist.
        if record.get(label + '_digest') != manifest[label]['digest']:
            raise ValueError('unreviewed ' + label)
        document = json.loads(raw)
        if label == 'sbom':
            if (document.get('bomFormat') != 'CycloneDX' or document.get('specVersion') != '1.5'
                    or not isinstance(document.get('components'), list) or not document['components']
                    or document.get('metadata', {}).get('component', {}).get('hashes') != [
                        {'alg': 'SHA-256', 'content': artifact['digest'][7:]}]):
                raise ValueError('SBOM missing artifact binding/components')
        else:
            if (document.get('_type') != 'https://in-toto.io/Statement/v1'
                    or document.get('predicateType') != 'https://slsa.dev/provenance/v1'
                    or document.get('subject') != [{'name': artifact['id'], 'digest': {'sha256': artifact['digest'][7:]}}]
                    or document.get('predicate', {}).get('buildDefinition', {}).get('resolvedDependencies') != [
                        {'uri': artifact['repository'], 'digest': {'gitCommit': artifact['source_commit']}}]
                    or not document.get('predicate', {}).get('runDetails', {}).get('builder', {}).get('id')):
                raise ValueError('provenance missing source/subject/builder binding')
    if record.get('stage') not in ('isolated_canary', 'release_approved'):
        raise ValueError('invalid artifact approval stage')
    release = record['stage'] == 'release_approved'
    if release:
        clearance = record.get('mrl32_clearance', {})
        required(clearance, ('path', 'digest'))
        evidence = json.loads(file_bytes(root, clearance['path'], clearance['digest']))
        if (evidence.get('identity') != identity or evidence.get('isolation_verified') is not True
                or not isinstance(evidence.get('approved_by'), str) or not evidence['approved_by'].strip()):
            raise ValueError('MRL-32 clearance missing or mismatched')
    if purpose == 'release' and not release:
        raise ValueError('CANARY_ONLY: MRL-32/release approval unresolved')
    return {'status': 'trust_verified' if release and purpose == 'release' else 'isolated_canary',
            'release_allowed': release and purpose == 'release', 'signature_verified': True, 'identity': identity}


def evaluate(manifest: dict, policy: dict, root: Path, purpose='release') -> dict:
    """Emit replayable, non-secret result with input identities and verifier version."""
    receipt = {'schema': 'MRL_Artifact_Trust_Receipt_v1', 'origin_signature': ORIGIN,
               'verifier_version': VERSION, 'verified_at': datetime.now(timezone.utc).isoformat(),
               'purpose': purpose, 'manifest_digest': digest(manifest), 'policy_digest': digest(policy),
               'release_allowed': False, 'status': 'denied', 'signature_verified': False,
               'supply_chain_isolation': 'UNVERIFIED', 'engineering_test': 'SEPARATE',
               'formal_delivery_admission': 'SEPARATE', 'dl580_acceptance': 'UNVERIFIED',
               'exception_approver': 'NONE'}
    try:
        receipt.update(verify(manifest, policy, Path(root), purpose))
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as error:
        receipt['reason'] = str(error)
    return receipt


def replay(previous: dict, manifest: dict, policy: dict, root: Path) -> dict:
    """Reverify original files and signatures under the supplied current trusted policy."""
    current = evaluate(manifest, policy, root, previous['purpose'])
    fields = ('schema', 'origin_signature', 'verifier_version', 'purpose', 'manifest_digest',
              'policy_digest', 'status', 'release_allowed', 'signature_verified', 'identity', 'reason')
    current['replay_matches'] = all(previous.get(k) == current.get(k) for k in fields)
    if not current['replay_matches']:
        current.update(status='denied', release_allowed=False, reason='REPLAY_INPUT_OR_DECISION_DRIFT')
    return current



def evaluate_delivery(host: dict, workload: dict, root: Path, paths: dict,
                      manifests: dict, policy: dict) -> dict:
    """Compose both gates; a trust receipt alone cannot admit a GPU deployment."""
    from MRL_hardware_admission_v1 import evaluate as hardware_evaluate
    hardware = hardware_evaluate(host, workload, root, paths)
    result = {'origin_signature': ORIGIN, 'allowed': False, 'hardware': hardware,
              'trust': {}, 'formal_delivery_admission': 'DENIED'}
    try:
        required(manifests, ('runner', 'runtime'))
        for role, field in (('runner', 'runner'), ('runtime', 'runtime_binary')):
            artifact = manifests[role]['artifact']
            expected = workload[field]
            if any(artifact[k] != expected[k] for k in ('id', 'version', 'digest')):
                raise ValueError('trust/workload identity mismatch: ' + role)
            if artifact['path'] != paths[role]:
                raise ValueError('trust/workload path mismatch: ' + role)
            result['trust'][role] = evaluate(manifests[role], policy, root, 'release')
        result['allowed'] = hardware['allowed'] and all(
            r['release_allowed'] for r in result['trust'].values())
        result['formal_delivery_admission'] = 'ADMITTED' if result['allowed'] else 'DENIED'
    except (ValueError, TypeError, KeyError) as error:
        result['reason'] = str(error)
    return result


def export_evidence(manifest: dict, policy: dict, root: Path, output: Path,
                    purpose='release') -> dict:
    """Create a confined replay directory; copy only explicit public evidence.

    This is evidence export, not formal hardware admission. Private signing keys
    are never read or copied. Input filenames and signed paths remain intact.
    """
    import shutil
    receipt = evaluate(manifest, policy, root, purpose)
    if receipt['status'] not in ('trust_verified', 'isolated_canary'):
        raise ValueError('evidence export denied: ' + receipt.get('reason', 'unknown'))
    refs = [manifest[k] for k in ('artifact', 'sbom', 'provenance')]
    identity = receipt['identity']
    record = next(r for r in policy['artifacts'] if r['identity'] == identity)
    if record.get('stage') == 'release_approved':
        refs.append(record['mrl32_clearance'])
    reserved = {'MRL_TRUST_MANIFEST.json', 'MRL_TRUST_POLICY.json', 'MRL_TRUST_RECEIPT.json'}
    if len({r['path'] for r in refs}) != len(refs):
        raise ValueError('overlapping evidence paths')
    for ref in refs:
        parts = Path(ref['path']).parts
        if any(part in reserved for part in parts):
            raise ValueError('reserved evidence path')
    output.mkdir(parents=True, exist_ok=False)
    try:
        for ref in refs:
            raw = file_bytes(root, ref['path'], ref['digest'])
            target = output / ref['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (output/'MRL_TRUST_MANIFEST.json').write_bytes(canonical(manifest))
        (output/'MRL_TRUST_POLICY.json').write_bytes(canonical(policy))
        # Reverify staged bytes; a source change during copy cannot escape.
        staged = evaluate(manifest, policy, output, purpose)
        if staged['status'] != receipt['status']:
            raise ValueError('staged evidence drift')
        (output/'MRL_TRUST_RECEIPT.json').write_bytes(canonical(staged))
        expected = {r['path'] for r in refs} | reserved
        actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
        if actual != expected:
            raise ValueError('evidence coverage mismatch')
        return staged
    except Exception:
        shutil.rmtree(output)
        raise


def main(argv=None) -> int:
    """CLI: exit 0 for release trust or isolated canary verification, otherwise 2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--policy', type=Path, default=POLICY)
    parser.add_argument('--artifact-root', type=Path, required=True)
    parser.add_argument('--purpose', choices=('release', 'canary'), default='release')
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--export-evidence', type=Path)
    args = parser.parse_args(argv)
    try:
        manifest, policy = load_json(args.manifest), load_json(args.policy)
        result = (replay(load_json(args.replay), manifest, policy, args.artifact_root) if args.replay
                  else evaluate(manifest, policy, args.artifact_root, args.purpose))
        if args.export_evidence:
            if result['status'] not in ('trust_verified', 'isolated_canary'):
                raise ValueError('cannot export denied evidence as verified')
            export_evidence(manifest, policy, args.artifact_root, args.export_evidence, result['purpose'])
    except (ValueError, TypeError, KeyError, OSError) as error:
        result = {'status': 'denied', 'release_allowed': False, 'reason': str(error),
                  'origin_signature': ORIGIN, 'verifier_version': VERSION}
    # Never overwrite historical receipts or any input file.
    with args.receipt.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['status'] in ('trust_verified', 'isolated_canary') else 2


if __name__ == '__main__':
    raise SystemExit(main())
