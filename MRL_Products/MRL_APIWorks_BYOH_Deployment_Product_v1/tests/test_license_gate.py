"""MRL-37 synthetic rights decisions; no production grant is created by tests."""
import contextlib
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import MRL_license_gate_v1 as gate
import MRL_build_product_bundle_v1 as builder
import MRL_artifact_trust_v1 as trust
from MRL_gate_schema_validator_v1 import product_catalog


def ref(root, name, raw):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}


def approve(registry, manifest, context):
    """In-memory TEST ONLY: never save into the repository's canonical registry."""
    registry['artifact_decisions'] = []
    today = datetime.now(timezone.utc).date()
    for c in manifest['components']:
        registry['artifact_decisions'].append({
            'record_id': 'SYNTHETIC_TEST_ONLY_' + c['id'], 'issued_by': 'MrLiouWord',
            'component_sha256': gate.digest(c), 'context_sha256': gate.digest(context),
            'decision': 'approve', 'third_party_rights_verified': True,
            'custom_terms_reviewed': False, 'review_date': today.isoformat(),
            'starts_on': today.isoformat(), 'expires_on': (today + timedelta(days=1)).isoformat(),
            'evidence_reference': 'test-fixture://NOT_A_REAL_OWNER_GRANT',
            'grantee': 'MRL', 'purpose': 'commercial_customer_delivery', 'environment': 'BYOH',
            'permitted_actions': ['commercial_use', 'redistribute', 'customer_model_use'],
            'prohibited_actions': [], 'rollback': 'discard synthetic fixture'})


class LicenseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'payload'
        self.root.mkdir()
        self.evidence = Path(self.temp.name) / 'evidence'
        self.evidence.mkdir()
        self.context = {'customer': 'SYNTHETIC_CUSTOMER', 'region': 'TW',
                        'mrl_annual_revenue_usd': 10, 'customer_annual_revenue_usd': 20,
                        'customer_model_responsibility': True}
        component = {'id': 'synthetic-model', 'kind': 'model_weights', 'version': '1.0.0',
                     'source': 'test-fixture://SYNTHETIC', 'source_commit': 'a' * 40,
                     'delivery': 'bundled', 'license_id': 'MIT',
                     'files': [ref(self.root, 'weights.bin', b'SYNTHETIC_NOT_A_MODEL')],
                     'documents': [dict(ref(self.evidence, 'LICENSE', b'SYNTHETIC license text\n'), role='license'),
                                   dict(ref(self.evidence, 'NOTICE', b'SYNTHETIC attribution\n'), role='notice')],
                     'commercial_use': True, 'redistribution': True, 'mrl_acquisition': True,
                     'annual_revenue_limit_usd': None, 'threshold_applies_to': 'none',
                     'regions': ['TW'], 'customers': ['SYNTHETIC_CUSTOMER'], 'obligations': ['preserve attribution']}
        self.manifest = {'schema': 'MRL_License_Manifest_v1', 'origin_signature': 'MrLiouWord',
                         'components': [component]}
        self.registry = gate.load_json(gate.REGISTRY)
        self.approve()

    @property
    def c(self):
        return self.manifest['components'][0]

    def approve(self):
        approve(self.registry, self.manifest, self.context)

    def evaluate(self, **kwargs):
        return gate.evaluate(self.manifest, self.context, self.root, self.evidence,
                             self.registry, **kwargs)

    def denied(self, reason=None, **kwargs):
        result = self.evaluate(**kwargs)
        self.assertFalse(result['allowed'], result)
        if reason:
            self.assertIn(reason, result.get('reason', ''), result)

    def test_normal_reviewed_license(self):
        self.assertTrue(self.evaluate(exhaustive=True)['allowed'])

    def test_spdx_label_does_not_grant_rights(self):
        self.registry = gate.load_json(gate.REGISTRY)
        self.denied('Owner')

    def test_unknown_licenses_even_with_fixture_approval(self):
        for label in ('UNKNOWN', 'NOASSERTION', 'NONE', 'UNRESOLVED'):
            self.c['license_id'] = label
            self.approve()
            self.denied('unknown license')

    def test_custom_requires_explicit_review(self):
        self.c['license_id'] = 'LicenseRef-SYNTHETIC'
        self.approve()
        self.denied('custom')
        self.registry['artifact_decisions'][0]['custom_terms_reviewed'] = True
        self.assertTrue(self.evaluate()['allowed'])

    def test_reject_and_needs_counsel(self):
        for status in ('reject', 'needs-counsel', 'pending'):
            self.registry['artifact_decisions'][0]['decision'] = status
            self.denied('rights decision')

    def test_no_implicit_commercial_or_redistribution(self):
        for field, reason in (('commercial_use', 'commercial use'), ('redistribution', 'redistribution')):
            self.c[field] = False
            self.approve()
            self.denied(reason)
            self.c[field] = True

    def test_commercial_threshold_both_entities_boundary_unknown(self):
        self.c.update(annual_revenue_limit_usd=10_000_000, threshold_applies_to='both')
        self.approve()
        self.assertTrue(self.evaluate()['allowed'])
        for who in ('mrl', 'customer'):
            field = who + '_annual_revenue_usd'
            old = self.context[field]
            for revenue in (10_000_000, 10_000_001, None):
                self.context[field] = revenue
                self.approve()
                self.denied('threshold')
            self.context[field] = old
        self.c['threshold_applies_to'] = 'none'
        self.approve()
        self.denied('threshold applicability')

    def test_customer_provided_no_redistribution_grant_or_mrl_acquisition(self):
        self.c.update(delivery='customer_provided', redistribution=False, mrl_acquisition=False)
        self.approve()
        self.assertTrue(self.evaluate()['allowed'])  # local customer file rehashed for runtime
        self.denied('must not be bundled', exhaustive=True)
        (self.root / 'weights.bin').unlink()
        self.assertTrue(self.evaluate(exhaustive=True)['allowed'])
        self.c['mrl_acquisition'] = True
        self.approve()
        self.denied('responsibility', exhaustive=True)
        self.c['mrl_acquisition'] = False
        self.context['customer_model_responsibility'] = False
        self.approve()
        self.denied('responsibility', exhaustive=True)

    def test_customer_model_does_not_waive_commercial_rights(self):
        self.c.update(delivery='customer_provided', mrl_acquisition=False, commercial_use=False)
        self.approve()
        self.denied('commercial use')

    def test_missing_license_notice_terms_empty_and_drift(self):
        for name in ('LICENSE', 'NOTICE'):
            path = self.evidence / name
            raw = path.read_bytes()
            path.unlink()
            self.denied()
            path.write_bytes(b'changed')
            self.denied('drift')
            path.write_bytes(raw)
        self.c['documents'] = [self.c['documents'][0]]
        self.approve()
        self.denied('NOTICE')
        self.c['documents'][0].update(ref(self.evidence, 'LICENSE', b''))
        self.approve()
        self.denied()

    def test_documents_bound_to_decision(self):
        self.c['documents'][0].update(ref(self.evidence, 'LICENSE', b'new conditions'))
        self.denied('Owner')

    def test_artifact_tampering_and_required_coverage(self):
        self.denied('coverage', required_files={'unmapped-runtime.whl'})
        (self.root / 'weights.bin').write_bytes(b'tampered')
        self.denied('drift')

    def test_unexpected_unlicensed_file(self):
        ref(self.root, 'unmapped.dll', b'not licensed')
        self.denied('coverage', exhaustive=True)

    def test_model_and_runtime_require_separate_review(self):
        runtime = copy.deepcopy(self.c)
        runtime.update(id='runtime', kind='runtime', license_id='Apache-2.0',
                       files=[ref(self.root, 'runtime.dll', b'synthetic runtime')])
        self.manifest['components'].append(runtime)
        self.denied('Owner')
        self.approve()
        self.assertTrue(self.evaluate(exhaustive=True)['allowed'])

    def test_region_and_customer_restrictions(self):
        for field in ('region', 'customer'):
            self.context[field] = 'OUTSIDE_REVIEWED_SCOPE'
            self.approve()
            self.denied('restriction')

    def test_grant_actions_issuer_expiry_and_revocation(self):
        for key, value in [('issued_by', 'OTHER'), ('third_party_rights_verified', False),
                           ('expires_on', '2000-01-01'), ('grantee', 'OTHER'),
                           ('permitted_actions', ['commercial_use']),
                           ('prohibited_actions', ['redistribute']), ('starts_on', '2999-01-01')]:
            self.approve()
            self.registry['artifact_decisions'][0][key] = value
            self.denied()

    def test_duplicate_approval_component_and_case_collision(self):
        self.registry['artifact_decisions'] *= 2
        self.denied('ambiguous')
        self.approve()
        self.manifest['components'].append(copy.deepcopy(self.c))
        self.denied()
        self.manifest['components'].pop()
        self.c['files'].append(ref(self.root, 'WEIGHTS.bin', b'collision'))
        self.approve()
        self.denied('colliding')

    def test_schema_missing_extra_types_and_empty(self):
        original = copy.deepcopy(self.c)
        for field in original:
            self.manifest['components'][0] = copy.deepcopy(original)
            del self.c[field]
            self.denied('schema')
        for field, value in [('commercial_use', 'true'), ('files', []), ('id', ''),
                             ('annual_revenue_limit_usd', True), ('source_commit', 'latest'), ('extra', 1)]:
            self.manifest['components'][0] = copy.deepcopy(original)
            self.c[field] = value
            self.denied('schema')

    def test_path_traversal_absolute_windows_and_symlink(self):
        for name in ('../weights.bin', '/weights.bin', 'C:/weights.bin', 'dir\\weights.bin', 'a/./b', 'name.'):
            self.c['files'][0]['path'] = name
            self.approve()
            self.denied('relative path')
        self.c['files'][0]['path'] = 'linked.bin'
        try:
            (self.root / 'linked.bin').symlink_to(self.root / 'weights.bin')
        except OSError:
            self.skipTest('symlink unavailable')
        self.approve()
        self.denied('symlink')

    def test_full_notice_export_reverification_and_tamper(self):
        unrelated = copy.deepcopy(self.registry['artifact_decisions'][0])
        unrelated.update(record_id='UNRELATED_PRIVATE_GRANT', component_sha256='f' * 64)
        self.registry['artifact_decisions'].append(unrelated)
        registry_file = Path(self.temp.name) / 'fixture-registry.json'
        registry_file.write_bytes(trust.canonical(self.registry))
        with patch.object(gate, 'REGISTRY', registry_file):
            gate.package_license(self.root, self.manifest, self.context, self.evidence)
            self.assertTrue(gate.verify_packaged(self.root)['allowed'])
            snapshot = gate.load_json(self.root / 'MRL_LICENSE_REGISTRY_SNAPSHOT.json')
            self.assertEqual(len(snapshot['artifact_decisions']), 1)
            self.assertNotIn('UNRELATED_PRIVATE_GRANT', json.dumps(snapshot))
            original = (self.root / 'NOTICE').read_bytes()
            self.assertIn((self.evidence / 'LICENSE').read_bytes(), original)
            self.assertIn((self.evidence / 'NOTICE').read_bytes(), original)
            (self.root / 'NOTICE').write_bytes(b'forged notice')
            with self.assertRaisesRegex(ValueError, 'NOTICE mismatch'):
                gate.verify_packaged(self.root)
            (self.root / 'NOTICE').write_bytes(original)
            self.registry['artifact_decisions'][0]['decision'] = 'reject'
            registry_file.write_bytes(trust.canonical(self.registry))
            self.assertFalse(gate.verify_packaged(self.root)['allowed'])

    def test_shipped_registry_is_unchanged_unresolved(self):
        self.assertNotIn('artifact_decisions', gate.load_json(gate.REGISTRY))
        self.assertFalse(gate.evaluate(self.manifest, self.context, self.root, self.evidence)['allowed'])

    def test_cli_unknown_license_and_receipt_create_only(self):
        for name, value in [('manifest', self.manifest), ('context', self.context)]:
            (self.evidence / (name + '.json')).write_bytes(trust.canonical(value))
        args = ['--manifest', str(self.evidence / 'manifest.json'), '--context', str(self.evidence / 'context.json'),
                '--artifact-root', str(self.root), '--evidence-root', str(self.evidence),
                '--receipt', str(self.evidence / 'receipt.json')]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.main(args), 2)
            with self.assertRaises(FileExistsError):
                gate.main(args)

    def test_all_three_gates_pass_only_with_separate_model_runtime_rights(self):
        from test_artifact_trust import ArtifactTrustTests
        from test_hardware_admission import fixture, write_artifacts, write_tested_matrix
        import MRL_hardware_admission_v1 as hardware
        synthetic = ArtifactTrustTests()
        synthetic.setUp()
        self.addCleanup(synthetic.doCleanups)
        host, workload = fixture()
        paths = write_artifacts(synthetic.root, workload)
        for role, field in (('runner', 'runner'), ('runtime', 'runtime_binary')):
            workload[field] = {k: synthetic.m['artifact'][k] for k in ('id', 'version', 'digest')}
            paths[role] = 'runtime.whl'
        host['loaded_runner'] = copy.deepcopy(workload['runner'])
        host['loaded_runtime'] = copy.deepcopy(workload['runtime_binary'])
        matrix = synthetic.root / 'matrix.json'
        write_tested_matrix(host, workload, matrix)
        components = []
        for role, field, kind in [('runtime', 'runtime_binary', 'runtime'),
                                  ('model', 'model', 'model_weights'), ('bundle', None, 'mrl_source')]:
            c = copy.deepcopy(self.c)
            c.update(id=workload[field]['id'] if field else 'source-bundle',
                     version=workload[field]['version'] if field else '1.0.0', kind=kind)
            path = synthetic.root / paths[role]
            names = [(Path(paths[role]) / n).as_posix() for n in gate.inventory(path)] if path.is_dir() else [paths[role]]
            c['files'] = [{'path': n, 'sha256': hashlib.sha256((synthetic.root / n).read_bytes()).hexdigest()} for n in names]
            components.append(c)
        self.manifest['components'] = components
        self.approve()
        registry_file = self.evidence / 'registry.json'
        registry_file.write_bytes(trust.canonical(self.registry))
        manifests = {'runner': synthetic.m, 'runtime': synthetic.m}
        args = (host, workload, synthetic.root, paths, manifests, synthetic.p,
                self.manifest, self.context, self.evidence)
        with patch.object(hardware, 'MATRIX', matrix), patch.object(gate, 'REGISTRY', registry_file):
            result = trust.evaluate_delivery(*args)
            self.assertTrue(result['allowed'], result)
            # Exact valid signature and hardware evidence do not override revoked rights.
            self.registry['artifact_decisions'][1]['decision'] = 'reject'
            registry_file.write_bytes(trust.canonical(self.registry))
            result = trust.evaluate_delivery(*args)
            self.assertTrue(result['hardware']['allowed'])
            self.assertTrue(result['trust']['runtime']['release_allowed'])
            self.assertFalse(result['allowed'])
            self.approve()
            self.manifest['components'][1]['kind'] = 'runtime'
            self.approve()
            registry_file.write_bytes(trust.canonical(self.registry))
            result = trust.evaluate_delivery(*args)
            self.assertFalse(result['allowed'])
            self.assertIn('identity/kind', result['license']['reason'])

    def test_customer_delivery_builder_denies_before_publication(self):
        with tempfile.TemporaryDirectory() as out, patch.object(builder, 'DIST', Path(out)):
            with self.assertRaisesRegex(ValueError, 'license gate DENIED'):
                builder.main(['--customer-delivery'])
            self.assertFalse(list(Path(out).iterdir()))

    def test_builder_positive_full_zip_and_stale_owner_denial(self):
        self.builder_roundtrip()

    def test_builder_requires_both_valid_signatures_and_valid_license(self):
        from test_artifact_trust import ArtifactTrustTests
        synthetic = ArtifactTrustTests()
        synthetic.setUp()
        self.addCleanup(synthetic.doCleanups)
        self.builder_roundtrip(synthetic)

    def builder_roundtrip(self, synthetic=None):
        # Enumerate the real source closure, configuration and byte hashes. Every
        # source file receives a TEST ONLY in-memory decision for this fixture.
        files = []
        for source, relative in ((builder.PRODUCT_ROOT, builder.PRODUCT_RELATIVE),
                                 (builder.RUNTIME_ROOT, builder.RUNTIME_RELATIVE)):
            for path in builder.files_under(source):
                files.append({'path': (relative / path.relative_to(source)).as_posix(),
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        config = builder.RUNTIME_ROOT / 'config/MRL_runtime.local.example.json'
        files.append({'path': builder.MUTABLE_CONFIG.as_posix(),
                      'sha256': hashlib.sha256(config.read_bytes()).hexdigest()})
        self.c.update(id='synthetic-source-closure', kind='mrl_source', files=files)
        extra_args = []
        if synthetic is not None:
            exported = self.evidence / 'trust-export'
            trust.export_evidence(synthetic.m, synthetic.p, synthetic.root, exported)
            receipt_file = exported / 'MRL_TRUST_RECEIPT.json'
            receipt = trust.load_json(receipt_file)
            receipt.pop('verified_at')
            receipt_file.write_bytes(trust.canonical(receipt))
            runtime = copy.deepcopy(self.c)
            runtime.update(id='synthetic-runtime', kind='runtime', files=[
                {'path': 'third_party_runtime/0/' + path.relative_to(exported).as_posix(),
                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in exported.rglob('*') if path.is_file()])
            self.manifest['components'].append(runtime)
            (synthetic.root / 'input.json').write_bytes(trust.canonical(synthetic.m))
            policy_file = self.evidence / 'trust-policy.json'
            policy_file.write_bytes(trust.canonical(synthetic.p))
            extra_args = ['--third-party-runtime', str(synthetic.root / 'input.json'),
                          '--runtime-evidence-root', str(synthetic.root)]
        self.approve()
        registry_file = self.evidence / 'fixture-registry.json'
        registry_file.write_bytes(trust.canonical(self.registry))
        for name, value in [('manifest', self.manifest), ('context', self.context)]:
            (self.evidence / (name + '.json')).write_bytes(trust.canonical(value))
        args = ['--customer-delivery', '--license-manifest', str(self.evidence / 'manifest.json'),
                '--license-context', str(self.evidence / 'context.json'),
                '--license-evidence-root', str(self.evidence)]
        args += extra_args
        with patch.object(gate, 'REGISTRY', registry_file), patch.object(builder, 'DIST', self.evidence / 'dist'), \
                patch.object(trust, 'POLICY', policy_file if synthetic else trust.POLICY):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(builder.main(args), 0)
            output = builder.DIST / (builder.BUNDLE_ROOT_NAME + '.zip')
            prior = output.read_bytes()
            with zipfile.ZipFile(output) as archive:
                prefix = builder.BUNDLE_ROOT_NAME + '/'
                receipt = json.loads(archive.read(prefix + builder.MANIFEST_NAME))
                product_catalog().validate('byoh-bundle-manifest', receipt)
                self.assertTrue(receipt['license_admission']['allowed'])
                self.assertFalse(receipt['customer_delivery_approved'])
                self.assertEqual(receipt['third_party_runtime_included'], synthetic is not None)
                with tempfile.TemporaryDirectory() as extracted:
                    archive.extractall(extracted)
                    self.assertTrue(gate.verify_packaged(Path(extracted) / builder.BUNDLE_ROOT_NAME)['allowed'])
            self.registry['artifact_decisions'][0]['decision'] = 'needs-counsel'
            registry_file.write_bytes(trust.canonical(self.registry))
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, 'license gate DENIED'):
                builder.main(args)
            self.assertEqual(output.read_bytes(), prior)


if __name__ == '__main__':
    unittest.main()
