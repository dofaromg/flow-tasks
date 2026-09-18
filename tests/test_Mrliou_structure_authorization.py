"""Behavioral tests use disposable synthetic repositories, never the MRL tree."""
import copy
import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

SOURCE = Path(__file__).resolve().parents[1]
GUARD = '.copilot/Mrliou_structure_authorization.py'
SCANNER = '.copilot/scanner/structure_scanner.py'
GENERATOR = '.copilot/generator/emoji_indexer.py'
OUTPUTS = ('.copilot/structure-scan.json', '.copilot/structure-index.json',
           '.copilot/structure.fltnz', 'STRUCTURE.md')
REGISTRY = 'config/MRL_AUTHORIZATION_REGISTRY_v1.json'


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'fixture'
        self.root.mkdir()
        for relative in (GUARD, SCANNER, GENERATOR, REGISTRY, 'run_structure_index.py',
                         '.copilot/triggers/smart_updater.py'):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, target)
        self.registry = json.loads((self.root / REGISTRY).read_text())
        # Real grants, if introduced later, must never authorize tests.
        self.registry['active_grants'] = []
        self.write_registry()
        (self.root / 'fixture.py').write_text('print("synthetic fixture only")\n')
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('GITHUB_')}
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'

    def write_registry(self):
        (self.root / REGISTRY).write_text(json.dumps(self.registry))

    def run_cli(self, script, *args, env=None):
        return subprocess.run([sys.executable, str(self.root / script), *args],
                              cwd=self.root, env=env or self.env,
                              capture_output=True, text=True, timeout=20)

    def run_code(self, code):
        return subprocess.run([sys.executable, '-c', code], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=20)

    def grant(self, github=False):
        now = datetime.now(timezone.utc)
        actor = 'fixture-actor' if github else 'local:' + getpass.getuser()
        grant = {
            'record_id': 'SYNTHETIC-TEST-ONLY', 'grantee': {
                'actor': actor, 'triggering_actor': actor},
            'scope': {'repository': 'dofaromg/flow-tasks', 'assets': ['.'], 'max_depth': 8,
                      'destination': ('github-actions-artifact:dofaromg/flow-tasks'
                                      if github else 'local-checkout'),
                      'events': ['workflow_dispatch'] if github else ['local'],
                      'ref': 'refs/heads/main' if github else 'local'},
            'actions': ['structure.scan', 'structure.generate', 'structure.upload'],
            'issued_by': 'MrLiouWord', 'issued_at': (now - timedelta(days=1)).isoformat(),
            'expires_at': (now + timedelta(days=1)).isoformat(),
            'evidence_reference': 'synthetic-fixture-only', 'rollback': 'remove fixture grant',
            'status': 'active', 'prohibited_actions': [], 'purpose': 'structure-index',
            'environment': 'github-actions' if github else 'local',
        }
        self.registry['active_grants'] = [grant]
        self.write_registry()
        return grant

    def github_env(self, **changes):
        env = dict(self.env, GITHUB_ACTIONS='true', GITHUB_REPOSITORY='dofaromg/flow-tasks',
                   GITHUB_REF='refs/heads/main', GITHUB_ACTOR='fixture-actor',
                   GITHUB_TRIGGERING_ACTOR='fixture-actor', GITHUB_EVENT_NAME='workflow_dispatch',
                   GITHUB_WORKFLOW_REF='dofaromg/flow-tasks/.github/workflows/structure-indexer.yml@refs/heads/main')
        env.update(changes)
        return env

    def assert_denied(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('"decision": "ALLOW"', result.stdout)

    def test_empty_grants_block_all_entrypoints_and_preserve_old_artifacts(self):
        for relative in OUTPUTS:
            (self.root / relative).write_text('HISTORICAL_EVIDENCE_DO_NOT_CHANGE')
        before = {p: (self.root / p).read_bytes() for p in OUTPUTS}
        for script, args in [(GUARD, ['preflight']), (GUARD, ['upload']), (SCANNER, []),
                             (GENERATOR, []), ('run_structure_index.py', []),
                             ('run_structure_index.py', ['--check-triggers'])]:
            with self.subTest(script=script, args=args):
                r = self.run_cli(script, *args)
                self.assert_denied(r)
                self.assertIn('NO_RECORDED_GRANT', r.stdout + r.stderr)
                self.assertNotIn('HISTORICAL_EVIDENCE_DO_NOT_CHANGE', r.stdout + r.stderr)
                self.assertEqual(before, {p: (self.root / p).read_bytes() for p in OUTPUTS})

    def test_denial_creates_no_artifacts(self):
        for script in [SCANNER, GENERATOR, 'run_structure_index.py']:
            self.assert_denied(self.run_cli(script))
            self.assertTrue(all(not (self.root / p).exists() for p in OUTPUTS))

    def test_generator_denies_before_input_read(self):
        result = self.run_cli(GENERATOR, '--input', '/definitely/missing/input.json')
        self.assert_denied(result)
        self.assertIn('NO_RECORDED_GRANT', result.stderr)
        self.assertNotIn('FileNotFoundError', result.stderr)

    def test_missing_registry_denied(self):
        (self.root / REGISTRY).unlink()
        self.assert_denied(self.run_cli(SCANNER))

    def test_unreadable_registry_denied(self):
        (self.root / REGISTRY).unlink()
        (self.root / REGISTRY).mkdir()
        self.assert_denied(self.run_cli(SCANNER))

    def test_invalid_json_variants_denied(self):
        for raw in ['{', 'null', '[]', '{"active_grants":NaN}',
                    '{"active_grants":[],"active_grants":[]}']:
            with self.subTest(raw=raw):
                (self.root / REGISTRY).write_text(raw)
                self.assert_denied(self.run_cli(GUARD, 'preflight'))

    def test_weakened_policy_denied(self):
        self.grant()
        original = copy.deepcopy(self.registry)
        for key, value in [('default_decision', 'ALLOW'), ('explicit_grant_required', False),
                           ('explicit_grant_required', 'true'), ('silence_is_authorization', True),
                           ('delegation_requires_explicit_scope', False)]:
            with self.subTest(key=key, value=value):
                self.registry = copy.deepcopy(original)
                self.registry['authorization_model'][key] = value
                self.write_registry()
                self.assert_denied(self.run_cli(SCANNER))

    def test_registry_origin_and_schema_denied(self):
        self.grant()
        original = copy.deepcopy(self.registry)
        for key, value in [('origin_signature', 'external'), ('root_authority', 'external'),
                           ('schema_version', '2'), ('required_fields', []), ('active_grants', {})]:
            self.registry = copy.deepcopy(original)
            self.registry[key] = value
            self.write_registry()
            self.assert_denied(self.run_cli(SCANNER))

    def test_grant_restrictions_denied(self):
        self.grant()
        original = copy.deepcopy(self.registry)
        cases = [('status', 'revoked'), ('issued_by', 'external'), ('purpose', 'other'),
                 ('environment', 'github-actions'), ('grantee', {'actor': '*'}),
                 ('expires_at', '2000-01-01T00:00:00Z'), ('issued_at', '2999-01-01T00:00:00Z'),
                 ('expires_at', '2999-01-01'), ('actions', ['structure.generate']),
                 ('prohibited_actions', ['structure.scan']), ('evidence_reference', ''),
                 ('rollback', ''), ('actions', ['*']), ('actions', 'structure.scan')]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.registry = copy.deepcopy(original)
                self.registry['active_grants'][0][key] = value
                self.write_registry()
                self.assert_denied(self.run_cli(SCANNER))

    def test_exact_scope_required(self):
        self.grant()
        original = copy.deepcopy(self.registry)
        for key, value in [('repository', 'other/repo'), ('assets', ['MRL_Mother']),
                           ('destination', 'https://example.invalid'), ('events', ['*']),
                           ('ref', 'refs/heads/main'), ('max_depth', 7), ('max_depth', True)]:
            with self.subTest(key=key):
                self.registry = copy.deepcopy(original)
                self.registry['active_grants'][0]['scope'][key] = value
                self.write_registry()
                self.assert_denied(self.run_cli(SCANNER))

    def test_unknown_constraints_are_not_ignored(self):
        grant = self.grant()
        grant['requires_approval'] = True
        self.write_registry()
        self.assert_denied(self.run_cli(SCANNER))

    def test_duplicate_grants_denied(self):
        grant = self.grant()
        self.registry['active_grants'].append(copy.deepcopy(grant))
        self.write_registry()
        self.assert_denied(self.run_cli(SCANNER))
        self.registry['active_grants'][1]['record_id'] = 'SECOND'
        self.write_registry()
        self.assert_denied(self.run_cli(SCANNER))

    def test_valid_local_grant_runs_synthetic_pipeline(self):
        self.grant()
        result = self.run_cli('run_structure_index.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(all((self.root / p).stat().st_size > 0 for p in OUTPUTS))
        scan = json.loads((self.root / OUTPUTS[0]).read_text())
        self.assertGreater(scan['statistics']['total_files'], 0)
        self.assert_denied(self.run_cli(GUARD, 'upload'))

    def test_each_direct_cli_with_valid_local_grant(self):
        self.grant()
        for script in [SCANNER, GENERATOR]:
            result = self.run_cli(script)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reduced_depth_grant_runs_only_requested_depth(self):
        grant = self.grant()
        grant['scope']['max_depth'] = 2
        self.write_registry()
        result = self.run_cli('run_structure_index.py', '--depth', '2')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / OUTPUTS[0]).read_text())['metadata']['max_depth'], 2)
        self.assert_denied(self.run_cli(SCANNER, '--depth', '3'))

    def test_generator_rejects_excess_depth_before_reading_input(self):
        grant = self.grant()
        grant['scope']['max_depth'] = 2
        self.write_registry()
        (self.root / OUTPUTS[0]).write_text('INVALID_JSON_MUST_NOT_BE_READ')
        result = self.run_cli(GENERATOR)
        self.assert_denied(result)
        self.assertIn('NO_UNIQUE_MATCHING_GRANT', result.stderr)
        self.assertNotIn('JSONDecodeError', result.stderr)

    def test_no_registry_override_or_force_bypass(self):
        env = dict(self.env, MRL_AUTHORIZATION_REGISTRY='/tmp/allow.json',
                   MRL_AUTHORIZED='true', MRL_FORCE_ALLOW='true', FORCE_UPDATE='true')
        self.assert_denied(self.run_cli(SCANNER, env=env))
        self.assert_denied(self.run_cli(SCANNER, '--force'))

    def test_wrong_root_and_input_output_paths_denied(self):
        self.grant()
        for script, args in [(SCANNER, ['--root', '..']),
                             (SCANNER, ['--output', '../scan.json']),
                             (GENERATOR, ['--input', '../scan.json']),
                             ('run_structure_index.py', ['--root', '..'])]:
            with self.subTest(script=script, args=args):
                self.assert_denied(self.run_cli(script, *args))
        self.assertEqual(self.run_cli(SCANNER).returncode, 0)
        self.assert_denied(self.run_cli(GENERATOR, '--output-dir', '..'))

    def test_scan_does_not_follow_symlink_outside_repository(self):
        self.grant()
        secret = Path(self.tmp.name) / 'outside-private'
        secret.mkdir()
        (secret / 'PRIVATE_SENTINEL').write_text('not authorized')
        (self.root / 'linked-private').symlink_to(secret, target_is_directory=True)
        self.assertEqual(self.run_cli(SCANNER).returncode, 0)
        result = (self.root / OUTPUTS[0]).read_text()
        self.assertNotIn('PRIVATE_SENTINEL', result)
        self.assertNotIn('linked-private', result)

    def test_symlinked_output_and_registry_denied(self):
        self.grant()
        outside = Path(self.tmp.name) / 'outside.json'
        outside.write_text('UNCHANGED')
        (self.root / OUTPUTS[0]).symlink_to(outside)
        self.assert_denied(self.run_cli(SCANNER))
        self.assertEqual(outside.read_text(), 'UNCHANGED')
        (self.root / REGISTRY).unlink()
        (self.root / REGISTRY).symlink_to(outside)
        self.assert_denied(self.run_cli(GUARD, 'preflight'))

    def test_revocation_between_scan_and_generate(self):
        self.grant()
        self.assertEqual(self.run_cli(SCANNER).returncode, 0)
        self.registry['active_grants'] = []
        self.write_registry()
        self.assert_denied(self.run_cli(GENERATOR))
        self.assertTrue(all(not (self.root / p).exists() for p in OUTPUTS[1:]))

    def test_imported_objects_do_not_bypass_authorization(self):
        for module, statement in [('scanner.structure_scanner', 'StructureScanner()'),
                                  ('generator.emoji_indexer', 'EmojiIndexer(scan_data={"fixture":1})')]:
            result = self.run_code("import sys;sys.path.insert(0,'.copilot');from "
                                   + module + ' import *;' + statement)
            self.assert_denied(result)
            self.assertIn('NO_RECORDED_GRANT', result.stderr)

    def test_revocation_before_individual_generator_write(self):
        self.grant()
        result = self.run_code("""
import sys,json
sys.path.insert(0,'.copilot')
from generator.emoji_indexer import EmojiIndexer
x=EmojiIndexer(scan_data={'fixture':1})
p='config/MRL_AUTHORIZATION_REGISTRY_v1.json'
r=json.load(open(p));r['active_grants']=[]
with open(p,'w') as f: json.dump(r,f)
x.generate_json()
""")
        self.assert_denied(result)
        self.assertFalse((self.root / OUTPUTS[1]).exists())

    def test_github_preflight_all_actions_and_upload_revalidation(self):
        grant = self.grant(github=True)
        env = self.github_env()
        result = self.run_cli(GUARD, 'preflight', env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt['registry_sha256'], hashlib.sha256((self.root / REGISTRY).read_bytes()).hexdigest())
        self.assert_denied(self.run_cli(GUARD, 'upload', env=env))
        for script in [SCANNER, GENERATOR]:
            self.assertEqual(self.run_cli(script, env=env).returncode, 0)
        self.assertEqual(self.run_cli(GUARD, 'upload', env=env).returncode, 0)
        grant['status'] = 'revoked'; self.write_registry()
        self.assert_denied(self.run_cli(GUARD, 'upload', env=env))

    def test_upload_cannot_use_scan_only_grant(self):
        grant = self.grant(github=True)
        grant['actions'] = ['structure.scan', 'structure.generate']
        self.write_registry()
        self.assert_denied(self.run_cli(GUARD, 'preflight', env=self.github_env()))
        self.assert_denied(self.run_cli(GUARD, 'upload', env=self.github_env()))

    def test_untrusted_workflow_contexts_denied(self):
        self.grant(github=True)
        for key, value in [('GITHUB_REPOSITORY', 'fork/repo'), ('GITHUB_REF', 'refs/pull/1/merge'),
                           ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'pull_request_target'),
                           ('GITHUB_WORKFLOW_REF', 'other'), ('GITHUB_ACTOR', 'other'),
                           ('GITHUB_TRIGGERING_ACTOR', 'other')]:
            with self.subTest(key=key):
                self.assert_denied(self.run_cli(GUARD, 'preflight', env=self.github_env(**{key: value})))

    def test_zero_negative_excessive_and_injected_depth_denied(self):
        self.grant()
        for depth in ['0', '-1', '9', '8; touch injected']:
            self.assert_denied(self.run_cli(SCANNER, '--depth', depth))
        self.assertFalse((self.root / 'injected').exists())


class WorkflowContractTests(unittest.TestCase):
    def test_all_artifact_paths_are_exact_and_upload_is_success_gated(self):
        source = (SOURCE / '.github/workflows/structure-indexer.yml').read_text()
        upload = source.split('      - name: 📤 Upload Artifacts\n', 1)[1].split('      - name:', 1)[0]
        self.assertNotIn('always()', upload)
        for condition in ["success()", "steps.authorization.outputs.allowed == 'true'",
                          "steps.scan.outcome == 'success'", "steps.index.outcome == 'success'",
                          "steps.upload_authorization.outputs.allowed == 'true'"]:
            self.assertIn(condition, upload)
        paths = upload.split('          path: |\n')[1].split('          include-hidden-files:')[0]
        self.assertEqual([line.strip() for line in paths.splitlines()], list(OUTPUTS))
        self.assertIn('if-no-files-found: error', upload)

    def test_pr_runs_only_synthetic_tests_and_no_generation(self):
        source = (SOURCE / '.github/workflows/structure-indexer.yml').read_text()
        self.assertIn("github.event_name != 'pull_request'", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn('needs: authorization-regression', source)
        tests = source.split('  authorization-regression:\n')[1].split('  update-structure-index:')[0]
        self.assertIn('python -m unittest discover', tests)
        self.assertNotIn('upload-artifact', tests)
        self.assertNotIn('structure_scanner.py', tests)

    def test_summary_never_reads_historical_scan_and_comment_follows_upload(self):
        source = (SOURCE / '.github/workflows/structure-indexer.yml').read_text()
        summary = source.split('      - name: ✅ Summary\n')[1]
        self.assertNotIn('structure-scan.json', summary)
        self.assertNotIn('python', summary)
        self.assertLess(source.index('id: upload\n'), source.index('💬 Comment on Issue'))
        self.assertIn("steps.upload.outcome == 'success'", source)
        self.assertNotIn("--depth ${{", source)


if __name__ == '__main__':
    unittest.main()
