"""Exercise the Actions credential gate without credentials or network access."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / '.github/workflows/cloud-connectors.yml').read_text())
VERIFY = next(step for step in WORKFLOW['jobs']['audit']['steps']
              if 'connector_manager --connect-all' in step.get('run', ''))


class CloudCredentialGateTests(unittest.TestCase):
    def run_gate(self, credentials, exit_code=0):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / 'called'
            executable = root / 'python'
            executable.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$CALL_MARKER"\n'
                                  'exit "$STUB_EXIT"\n')
            executable.chmod(0o755)
            env = {'PATH': f'{root}:/usr/bin:/bin', 'CALL_MARKER': str(marker),
                   'STUB_EXIT': str(exit_code), **credentials}
            result = subprocess.run(['bash', '-e', '-c', VERIFY['run']],
                                    env=env, text=True, capture_output=True)
            called = marker.read_text() if marker.exists() else None
            return result, called

    def test_reports_every_missing_secret_before_authentication(self):
        result, called = self.run_gate({})
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(called)
        for expression in VERIFY['env'].values():
            secret_name = expression.split('secrets.')[1].split()[0]
            self.assertIn(f'Missing Actions secret {secret_name} ', result.stdout)

    def test_one_missing_credential_blocks_authentication(self):
        credentials = dict.fromkeys(VERIFY['env'], 'synthetic-test-value')
        credentials.pop('GOOGLE_DRIVE_TOKEN')
        result, called = self.run_gate(credentials)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.count('Missing Actions secret '), 1)
        self.assertIsNone(called)
        self.assertNotIn('synthetic-test-value', result.stdout + result.stderr)

    def test_configured_gate_preserves_full_strict_audit(self):
        result, called = self.run_gate(dict.fromkeys(VERIFY['env'], 'synthetic-test-value'))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(called.splitlines(), ['-m', 'connectors.connector_manager',
                         '--connect-all', '--include-disabled', '--strict', '--json'])
        self.assertNotIn('synthetic-test-value', result.stdout + result.stderr)

    def test_authentication_failure_still_fails_job(self):
        result, called = self.run_gate(dict.fromkeys(VERIFY['env'], 'synthetic-test-value'), 7)
        self.assertEqual(result.returncode, 7)
        self.assertIsNotNone(called)

    def test_audit_and_sync_use_identical_secret_mappings(self):
        sync = next(step for step in WORKFLOW['jobs']['audit']['steps']
                    if 'connector_manager --sync-all' in step.get('run', ''))
        self.assertEqual(VERIFY['env'], sync['env'])
        self.assertEqual(VERIFY['env']['GITHUB_TOKEN'], '${{ secrets.CLOUD_GITHUB_TOKEN }}')
        self.assertNotIn('environment', WORKFLOW['jobs']['audit'])


if __name__ == '__main__':
    unittest.main()
