"""MRL-33 synthetic signatures; no fixture key or acceptance is production trust."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import MRL_artifact_trust_v1 as gate


class ArtifactTrustTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.private = self.root/'test-key.pem'
        subprocess.run([gate.openssl_command(), 'genpkey', '-algorithm', 'ED25519', '-out', str(self.private)],
                       check=True, capture_output=True)
        public = subprocess.run([gate.openssl_command(), 'pkey', '-in', str(self.private), '-pubout', '-outform', 'DER'],
                                capture_output=True, check=True).stdout
        self.fp = 'sha256:' + hashlib.sha256(public).hexdigest()
        self.artifact = self.write('runtime.whl', b'SYNTHETIC_TEST_ONLY_NOT_EXECUTABLE')
        identity = {'id': 'synthetic-runtime', 'kind': 'wheel', 'version': '1.106.6',
                    'repository': 'https://github.com/MRL-test-only/runtime',
                    'source_commit': 'a'*40, 'digest': self.artifact}
        sbom = {'bomFormat': 'CycloneDX', 'specVersion': '1.5',
                'metadata': {'component': {'hashes': [{'alg': 'SHA-256', 'content': self.artifact[7:]}]}},
                'components': [{'name': 'synthetic-runtime', 'version': '1.106.6'}]}
        provenance = {'_type': 'https://in-toto.io/Statement/v1',
                      'predicateType': 'https://slsa.dev/provenance/v1',
                      'subject': [{'name': identity['id'], 'digest': {'sha256': self.artifact[7:]}}],
                      'predicate': {'buildDefinition': {'resolvedDependencies': [
                          {'uri': identity['repository'], 'digest': {'gitCommit': identity['source_commit']}}]},
                          'runDetails': {'builder': {'id': 'TEST_ONLY_BUILDER'}}}}
        self.m = {'schema': 'MRL_Artifact_Trust_Manifest_v1', 'origin_signature': gate.ORIGIN,
                  'artifact': dict(identity, path='runtime.whl'),
                  'sbom': {'path': 'sbom.json', 'digest': self.write('sbom.json', gate.canonical(sbom))},
                  'provenance': {'path': 'provenance.json', 'digest': self.write('provenance.json', gate.canonical(provenance))},
                  'exception_approver': 'NONE'}
        identity['fingerprint'] = self.fp
        clearance = {'identity': identity, 'isolation_verified': True, 'approved_by': 'TEST_ONLY'}
        self.p = {'schema': 'MRL_Artifact_Trust_Policy_v1', 'origin_signature': gate.ORIGIN,
                  'keys': [{'fingerprint': self.fp, 'public_key_hex': public[-32:].hex(), 'status': 'active'}],
                  'artifacts': [{'identity': identity, 'sbom_digest': self.m['sbom']['digest'],
                                 'provenance_digest': self.m['provenance']['digest'], 'stage': 'release_approved',
                                 'mrl32_clearance': {'path': 'clearance.json',
                                    'digest': self.write('clearance.json', gate.canonical(clearance))}}]}
        self.sign()

    def write(self, name, raw):
        (self.root/name).write_bytes(raw)
        return 'sha256:' + hashlib.sha256(raw).hexdigest()

    def sign(self):
        payload = gate.canonical({k: v for k, v in self.m.items() if k != 'signing'})
        (self.root/'payload').write_bytes(payload)
        signature = subprocess.run([gate.openssl_command(), 'pkeyutl', '-sign', '-rawin', '-inkey',
                                    str(self.private), '-in', str(self.root/'payload')],
                                   capture_output=True, check=True).stdout
        self.m['signing'] = {'algorithm': 'Ed25519', 'fingerprint': self.fp,
                             'signature': base64.b64encode(signature).decode()}

    def evaluate(self, purpose='release'):
        return gate.evaluate(self.m, self.p, self.root, purpose)

    def denied(self, reason=None):
        result = self.evaluate()
        self.assertEqual(result['status'], 'denied', result)
        self.assertFalse(result['release_allowed'])
        if reason:
            self.assertIn(reason, result['reason'])

    def test_normal_source_and_offline_replay(self):
        receipt = self.evaluate()
        self.assertTrue(receipt['release_allowed'], receipt)
        self.assertTrue(receipt['signature_verified'])
        self.assertTrue(gate.replay(receipt, self.m, self.p, self.root)['replay_matches'])
        self.assertEqual(receipt['dl580_acceptance'], 'UNVERIFIED')

    def test_digest_drift(self):
        (self.root/'runtime.whl').write_bytes(b'drift')
        self.denied('drift')

    def test_old_key_retired_and_revoked(self):
        for status in ('retired', 'revoked'):
            self.p['keys'][0]['status'] = status
            self.denied('signing key')

    def test_new_key_not_implicitly_trusted(self):
        self.m['signing']['fingerprint'] = 'sha256:' + 'f'*64
        self.denied('signing key')

    def test_wrong_key_material_even_with_claimed_fingerprint(self):
        self.p['keys'][0]['public_key_hex'] = 'b'*64
        self.denied('signature')

    def test_repository_identity_mismatch(self):
        self.m['artifact']['repository'] = 'https://github.com/attacker/runtime'
        self.sign()
        self.denied('binding not approved')

    def test_source_commit_drift_with_valid_signature(self):
        self.m['artifact']['source_commit'] = 'b'*40
        self.sign()
        self.denied('binding not approved')

    def test_invalid_signature_and_unsigned_manifest_edit(self):
        self.m['artifact']['version'] = '1.106.7'
        self.denied('signature')

    def test_missing_each_required_field(self):
        original = copy.deepcopy(self.m)
        for key in list(original):
            self.m = copy.deepcopy(original)
            del self.m[key]
            self.denied()
        self.m = copy.deepcopy(original)
        for key in list(original['artifact']):
            self.m = copy.deepcopy(original)
            del self.m['artifact'][key]
            self.denied()

    def test_sbom_and_provenance_drift(self):
        for key in ('sbom', 'provenance'):
            with self.subTest(key=key):
                path = self.root/self.m[key]['path']
                raw = path.read_bytes()
                path.write_bytes(b'{}')
                self.denied('drift')
                path.write_bytes(raw)

    def test_empty_evidence_even_if_signed_and_review_hash_updated(self):
        for key in ('sbom', 'provenance'):
            self.m[key]['digest'] = self.write(self.m[key]['path'], b'{}')
            self.p['artifacts'][0][key+'_digest'] = self.m[key]['digest']
            self.sign()
            self.denied()

    def test_mutable_tags(self):
        for version in ('latest', 'main', 'main-latest', 'v1', '1.2'):
            self.m['artifact']['version'] = version
            self.sign()
            self.denied('immutable')

    def test_empty_production_policy_denies(self):
        self.p = gate.load_json(gate.POLICY)
        self.denied('signing key')

    def test_canary_cannot_promote_to_release(self):
        self.p['artifacts'][0]['stage'] = 'isolated_canary'
        self.p['artifacts'][0].pop('mrl32_clearance')
        canary = self.evaluate('canary')
        self.assertEqual(canary['status'], 'isolated_canary', canary)
        self.assertFalse(canary['release_allowed'])
        self.denied('CANARY_ONLY')

    def test_release_requires_mrl32_clearance(self):
        self.p['artifacts'][0].pop('mrl32_clearance')
        self.denied()

    def test_replay_under_changed_policy_denies(self):
        previous = self.evaluate()
        self.p['keys'][0]['status'] = 'revoked'
        current = gate.replay(previous, self.m, self.p, self.root)
        self.assertFalse(current['release_allowed'])
        self.assertFalse(current['replay_matches'])

    def test_forged_receipt_and_changed_bytes_not_authorization(self):
        previous = self.evaluate()
        (self.root/'runtime.whl').write_bytes(b'tampered')
        self.assertFalse(gate.replay(previous, self.m, self.p, self.root)['release_allowed'])

    def test_path_traversal_and_symlink(self):
        self.m['artifact']['path'] = '../runtime.whl'
        self.sign()
        self.denied('relative')
        self.m['artifact']['path'] = 'linked.whl'
        try:
            (self.root/'linked.whl').symlink_to(self.root/'runtime.whl')
        except OSError:
            self.skipTest('symlink unavailable')
        self.sign()
        self.denied('symlink')

    def test_duplicate_json_and_non_object(self):
        for raw in (b'{"x":1,"x":2}', b'[]', b'{"x":NaN}'):
            self.write('bad.json', raw)
            with self.assertRaises(ValueError):
                gate.load_json(self.root/'bad.json')

    def test_export_has_exact_public_evidence_and_replays(self):
        output = self.root/'export'
        receipt = gate.export_evidence(self.m, self.p, self.root, output)
        expected = {'runtime.whl', 'sbom.json', 'provenance.json', 'clearance.json',
                    'MRL_TRUST_MANIFEST.json', 'MRL_TRUST_POLICY.json', 'MRL_TRUST_RECEIPT.json'}
        self.assertEqual({p.name for p in output.iterdir()}, expected)
        self.assertNotIn('test-key.pem', expected)
        replay = gate.replay(receipt, gate.load_json(output/'MRL_TRUST_MANIFEST.json'),
                             gate.load_json(output/'MRL_TRUST_POLICY.json'), output)
        self.assertTrue(replay['replay_matches'], replay)
        self.p['keys'][0]['status'] = 'revoked'
        with self.assertRaises(ValueError):
            gate.export_evidence(self.m, self.p, self.root, self.root/'denied-export')
        self.assertFalse((self.root/'denied-export').exists())

    def test_builder_gates_third_party_bytes_and_zip_readback(self):
        import MRL_build_product_bundle_v1 as builder
        import zipfile
        self.write('input-manifest.json', gate.canonical(self.m))
        self.write('test-policy.json', gate.canonical(self.p))
        args = ['--third-party-runtime', str(self.root/'input-manifest.json'),
                '--runtime-evidence-root', str(self.root)]
        with patch.object(gate, 'POLICY', self.root/'test-policy.json'):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(builder.main(args), 0)
            output = builder.DIST/(builder.BUNDLE_ROOT_NAME+'.zip')
            prior_digest = hashlib.sha256(output.read_bytes()).hexdigest()
            with zipfile.ZipFile(output) as archive:
                prefix = builder.BUNDLE_ROOT_NAME+'/third_party_runtime/0/'
                self.assertEqual(archive.read(prefix+'runtime.whl'), (self.root/'runtime.whl').read_bytes())
                self.assertNotIn(prefix+'test-key.pem', archive.namelist())
                manifest = json.loads(archive.read(builder.BUNDLE_ROOT_NAME+'/'+builder.MANIFEST_NAME))
                self.assertTrue(manifest['third_party_runtime_included'])
                self.assertEqual(manifest['formal_delivery_admission'], 'REQUIRES_SEPARATE_COMPOSED_GATE')
            (self.root/'runtime.whl').write_bytes(b'drift')
            with self.assertRaises(ValueError):
                builder.main(args)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), prior_digest)
        # The shipped empty policy cannot package even cryptographically valid fixtures.
        with self.assertRaises(ValueError):
            builder.main(args)

    def test_new_key_requires_explicit_policy_and_exact_binding(self):
        old = copy.deepcopy(self.p['keys'][0])
        subprocess.run([gate.openssl_command(), 'genpkey', '-algorithm', 'ED25519', '-out', str(self.private)],
                       check=True, capture_output=True)
        public = subprocess.run([gate.openssl_command(), 'pkey', '-in', str(self.private), '-pubout', '-outform', 'DER'],
                                capture_output=True, check=True).stdout
        self.fp = 'sha256:' + hashlib.sha256(public).hexdigest()
        self.sign()
        self.denied('signing key')
        self.p['keys'] = [dict(old, status='retired'),
                          {'fingerprint': self.fp, 'public_key_hex': public[-32:].hex(), 'status': 'active'}]
        self.denied('binding not approved')
        self.p['artifacts'][0]['identity']['fingerprint'] = self.fp
        clearance = {'identity': self.p['artifacts'][0]['identity'], 'isolation_verified': True,
                     'approved_by': 'SYNTHETIC_POLICY_APPROVAL_ONLY'}
        self.p['artifacts'][0]['mrl32_clearance']['digest'] = self.write('clearance.json', gate.canonical(clearance))
        self.assertTrue(self.evaluate()['release_allowed'])


    def test_canary_purpose_never_returns_release_admission(self):
        self.assertFalse(self.evaluate('canary')['release_allowed'])
        self.assertEqual(self.evaluate('canary')['status'], 'isolated_canary')

    def test_composed_hardware_and_trust_admission(self):
        from test_hardware_admission import fixture, write_artifacts, tested_matrix
        import MRL_hardware_admission_v1 as hardware
        h, w = fixture()
        paths = write_artifacts(self.root, w)
        for role, field in (('runner', 'runner'), ('runtime', 'runtime_binary')):
            w[field] = {k: self.m['artifact'][k] for k in ('id', 'version', 'digest')}
            paths[role] = 'runtime.whl'
        h['loaded_runner'] = copy.deepcopy(w['runner'])
        h['loaded_runtime'] = copy.deepcopy(w['runtime_binary'])
        matrix = self.root/'matrix.json'
        tested_matrix(h, w, matrix)
        manifests = {'runner': self.m, 'runtime': self.m}
        with patch.object(hardware, 'MATRIX', matrix):
            result = gate.evaluate_delivery(h, w, self.root, paths, manifests, self.p)
            self.assertTrue(result['allowed'], result)
            self.assertFalse(gate.evaluate_delivery(h, w, self.root, paths, {}, self.p)['allowed'])
            empty_policy = gate.load_json(gate.POLICY)
            denied = gate.evaluate_delivery(h, w, self.root, paths, manifests, empty_policy)
            self.assertTrue(denied['hardware']['allowed'])
            self.assertFalse(denied['allowed'])
            # Valid trust cannot replace missing actual hardware acceptance.
            matrix.write_text(gate.POLICY.parent.parent.joinpath(
                'hardware/MRL_hardware_matrix_v1.json').read_text(encoding='utf-8'), encoding='utf-8')
            denied = gate.evaluate_delivery(h, w, self.root, paths, manifests, self.p)
            self.assertFalse(denied['allowed'])
            self.assertTrue(denied['trust']['runtime']['release_allowed'])


    def test_cli_receipt_and_replay_and_missing_file(self):
        self.write('manifest.json', gate.canonical(self.m))
        self.write('policy.json', gate.canonical(self.p))
        args = ['--manifest', str(self.root/'manifest.json'), '--policy', str(self.root/'policy.json'),
                '--artifact-root', str(self.root), '--receipt', str(self.root/'receipt.json')]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(args), 0)
        previous = gate.load_json(self.root/'receipt.json')
        self.assertTrue(previous['release_allowed'])
        args[-1] = str(self.root/'replay.json')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(args + ['--replay', str(self.root/'receipt.json')]), 0)
        (self.root/'runtime.whl').unlink()
        args[-1] = str(self.root/'denied.json')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(args), 2)


if __name__ == '__main__':
    unittest.main()
