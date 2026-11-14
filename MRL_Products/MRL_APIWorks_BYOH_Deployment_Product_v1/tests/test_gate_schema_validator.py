"""MRL-45 contract fixtures. Synthetic records carry no release authority."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/mrl45'
SCRIPT = ROOT / 'scripts/MRL_gate_schema_validator_v1.py'
sys.path.insert(0, str(SCRIPT.parent))

import MRL_gate_schema_validator_v1 as gate
import test_artifact_trust as trust_fixtures
import test_license_gate as license_fixtures


def replace_value(record, mutation):
    path = mutation['path']
    container = record
    for key in path[:-1]:
        container = container[int(key)] if isinstance(container, list) else container[key]
    key = int(path[-1]) if isinstance(container, list) else path[-1]
    if mutation.get('remove'):
        del container[key]
    else:
        container[key] = mutation['value']


def copy_catalog(target):
    for relative in (*gate.SCHEMA_FILES.values(), gate.LICENSE_SOURCE):
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)


def check_fixture(root, name, spec, label):
    checks = unittest.TestCase()
    sample = gate.load_json(root / spec['valid'])
    if label == 'valid':
        gate.product_catalog().validate(name, sample)
    elif label == 'bad-ref':
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_catalog(target)
            path = target / gate.SCHEMA_FILES[name]
            schema = gate.load_json(path)
            schema.setdefault('allOf', []).append({
                'if': False, 'then': {'$ref': 'https://mrl.invalid/unregistered/schema.json'},
            })
            path.write_text(json.dumps(schema), encoding='utf-8')
            # The reference cannot be used by the positive instance. Catalog
            # preflight must still deny it before instance validation.
            with checks.assertRaisesRegex(gate.SchemaRejected, 'unresolved-ref'):
                gate.SchemaCatalog(target).validate(name, sample)
    else:
        mutation = spec['cases'][label]
        replace_value(sample, mutation)
        with checks.assertRaises(gate.SchemaRejected) as rejected:
            gate.product_catalog().validate(name, sample)
        checks.assertEqual(rejected.exception.keyword, mutation['keyword'], str(rejected.exception))


def fixture_test(root, name, spec, label):
    def run_fixture():
        check_fixture(root, name, spec, label)

    return unittest.FunctionTestCase(run_fixture, description=f'{root.name.upper()} {name} {label}')


def load_tests(loader, tests, pattern):
    names = set()
    for root in (FIXTURES, FIXTURES.parent / 'mrl36', FIXTURES.parent / 'mrl47'):
        cases = gate.load_json(root / 'cases.json')
        if names.intersection(cases):
            raise ValueError('duplicate Gate Schema fixture inventory')
        names.update(cases)
        for name, spec in sorted(cases.items()):
            labels = ('valid', 'bad-ref', *spec['cases'])
            for label in labels:
                tests.addTest(fixture_test(root, name, spec, label))
    if names != set(gate.SCHEMA_FILES):
        raise ValueError('Gate Schema and fixture inventories differ')
    return tests


class GateSchemaTests(unittest.TestCase):
    def test_retained_contracts_match_provenance(self):
        provenance = gate.load_json(ROOT / 'schemas/MRL_gate_schema_provenance_v1.json')
        for row in provenance['retained_source_files']:
            with self.subTest(path=row['path']):
                raw = (ROOT / row['path']).read_bytes()
                self.assertEqual(len(raw), row['size_bytes'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])

    def test_catalog_rejects_duplicate_effective_id(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_catalog(target)
            path = target / gate.SCHEMA_FILES['billing-receipt']
            schema = gate.load_json(path)
            schema['$id'] = gate.product_catalog().ids['route-receipt']
            path.write_text(json.dumps(schema), encoding='utf-8')
            with self.assertRaisesRegex(gate.SchemaRejected, 'catalog-id'):
                gate.SchemaCatalog(target)

    def test_catalog_rejects_unknown_format_and_dangling_pointer(self):
        for keyword, value, expected in (
            ('format', 'mrl45-typo-date-time', 'unknown-format'),
            ('$ref', '#/$defs/missing', 'unresolved-ref'),
            ('$ref', 'file:///unregistered/mrl45.json', 'unresolved-ref'),
            ('$ref', 'urn:mrl:byoh:route-receipt:0.1-rc0#/properties/pricing/type', 'ref-target-not-schema'),
        ):
            with self.subTest(keyword=keyword, value=value), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                copy_catalog(target)
                path = target / gate.SCHEMA_FILES['billing-receipt']
                schema = gate.load_json(path)
                schema[keyword] = value
                path.write_text(json.dumps(schema), encoding='utf-8')
                with self.assertRaisesRegex(gate.SchemaRejected, expected):
                    gate.SchemaCatalog(target)

    def test_cross_schema_missing_dependency_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_catalog(target)
            (target / gate.SCHEMA_FILES['route-receipt']).unlink()
            with self.assertRaises(FileNotFoundError):
                gate.SchemaCatalog(target)

    def test_unknown_price_stays_unknown(self):
        receipt = gate.load_json(FIXTURES / 'billing-receipt.json')
        receipt.update(price_state='unknown', pricing=None, region=None, source_revision=None)
        gate.product_catalog().validate('billing-receipt', receipt)

    def test_rc0_decision_exchange_and_billing_share_source_values(self):
        names = ('decision-request', 'route-receipt', 'decision-response', 'billing-receipt')
        documents = [gate.load_json(FIXTURES / (name + '.json')) for name in names]
        for name, document in zip(names, documents):
            gate.product_catalog().validate(name, document)
        request, route, response, billing = documents
        self.assertEqual({d['request_id'] for d in documents}, {request['request_id']})
        self.assertEqual(route['receipt_id'], response['route_receipt_id'])
        self.assertEqual(route['receipt_id'], billing['route_receipt_id'])
        self.assertEqual(route['pricing'], billing['pricing'])

    def test_existing_artifact_gate_denies_unapproved_key_after_schema_pass(self):
        fixture = trust_fixtures.ArtifactTrustTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        gate.product_catalog().validate('artifact-trust', fixture.m)
        self.assertTrue(fixture.evaluate()['signature_verified'])
        fixture.p = trust_fixtures.gate.load_json(trust_fixtures.gate.POLICY)
        fixture.denied('unapproved')

    def test_existing_license_gate_denies_rights_after_schema_pass(self):
        fixture = license_fixtures.LicenseGateTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.assertTrue(fixture.evaluate(exhaustive=True)['allowed'])
        fixture.c['commercial_use'] = False
        fixture.approve()
        gate.product_catalog().validate('license-manifest', fixture.manifest)
        fixture.denied('commercial use prohibited')

    def test_existing_license_gate_denies_missing_validator_dependency(self):
        fixture = license_fixtures.LicenseGateTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        with patch.dict(sys.modules, {'MRL_gate_schema_validator_v1': None}):
            fixture.denied('schema validator unavailable')

    def test_cli_has_readable_errors_and_uses_no_network(self):
        sample = FIXTURES / 'billing-receipt.json'
        bootstrap = (
            'import runpy, sys\n'
            'def deny_network(event, args):\n'
            '    if event.startswith("socket."):\n'
            '        raise AssertionError("schema validation tried to use the network")\n'
            'sys.addaudithook(deny_network)\n'
            'script = sys.argv.pop(1)\n'
            'sys.path.insert(0, str(__import__("pathlib").Path(script).parent))\n'
            'runpy.run_path(script, run_name="__main__")\n'
        )

        def cli(*args):
            return subprocess.run([sys.executable, '-c', bootstrap, str(SCRIPT), *map(str, args)],
                                  text=True, encoding='utf-8', capture_output=True, check=False)

        result = cli('check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'SCHEMA_CATALOG_VALID')
        result = cli('validate', 'billing-receipt', sample)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'SCHEMA_VALID')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'billing-invalid.json'
            original = gate.load_json(sample)
            invalid = copy.deepcopy(original)
            invalid['pricing']['effective_at'] = '2026-02-30T00:00:00Z'
            path.write_text(json.dumps(invalid), encoding='utf-8')
            result = cli('validate', 'billing-receipt', path)
            self.assertEqual(result.returncode, 2, result.stderr)
            error = json.loads(result.stdout)
            self.assertEqual((error['keyword'], error['instance_path']), ('format', '/pricing/effective_at'))
            for malformed in ('{"duplicate": 1, "duplicate": 2}', '{"too_large": 1e999}'):
                path.write_text(malformed, encoding='utf-8')
                result = cli('validate', 'billing-receipt', path)
                self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == '__main__':
    unittest.main()
