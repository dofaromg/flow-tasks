"""Run the real monitoring workflow's Bash blocks against a synthetic gh.

No network, real credential, Codespace mutation or GitHub issue mutation is used.
Run: python -m unittest discover -s tests -p test_codespace_monitoring.py -v
"""
import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/codespace-monitoring.yml'
TITLE = '⚠️ Codespace Retention Warning - Action Required'
MOCK_GH = r'''#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
cfg = json.loads(Path('scenario.json').read_text())
a = sys.argv[1:]
with open('calls.jsonl', 'a') as f:
    f.write(json.dumps(a) + '\n')
def result(value, code=0):
    if value is not None:
        print(json.dumps(value))
    sys.exit(code)
if a[:2] == ['codespace', 'list']:
    assert a[a.index('--repo') + 1] == 'dofaromg/flow-tasks'
    assert a[a.index('--limit') + 1] == '1000'
    if cfg.get('api_fail'):
        result(None, 1)
    if 'raw_response' in cfg:
        print(cfg['raw_response'])
        sys.exit(0)
    result(cfg.get('codespaces', []))
if a[:2] == ['label', 'create']:
    assert '--repo' in a
    if cfg.get('label_fail') or cfg.get('label_exists'):
        print('HTTP 403' if cfg.get('label_fail') else 'already exists', file=sys.stderr)
        result(None, 1)
    result(None)
if a[:1] == ['api'] and '/labels/' in a[1]:
    result(None, 0 if cfg.get('label_exists') else 1)
if a[:2] == ['issue', 'list']:
    assert '--repo' in a and '--limit' in a
    if cfg.get('issue_list_fail'):
        result(None, 1)
    p = subprocess.run(['jq', '-r', a[a.index('--jq') + 1]],
                       input=json.dumps(cfg.get('issues', [])), text=True,
                       capture_output=True)
    sys.stdout.write(p.stdout)
    sys.exit(p.returncode)
if a[:2] in (['issue', 'create'], ['issue', 'edit'], ['issue', 'close']):
    assert '--repo' in a
    key = 'issue_' + a[1] + '_fail'
    result(None, 1 if cfg.get(key) else 0)
print('Unexpected gh invocation', file=sys.stderr)
sys.exit(99)
'''


def codespace(days=25, last_used=None):
    timestamp = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return {'name': 'synthetic-mrl-space', 'repository': 'dofaromg/flow-tasks',
            'state': 'Available', 'lastUsedAt': last_used or timestamp.isoformat()}


class CodespaceMonitoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
        cls.steps = {s['name']: s['run'] for s in
                     cls.workflow['jobs']['monitor-codespaces']['steps'] if 'run' in s}

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cwd = Path(self.directory.name)
        (self.cwd / 'gh').write_text(MOCK_GH)
        (self.cwd / 'gh').chmod(0o755)
        self.output = self.cwd / 'outputs'
        self.output.touch()

    def run_step(self, name, scenario=None, token=True):
        cfg = scenario or {}
        (self.cwd / 'scenario.json').write_text(json.dumps(cfg))
        if name == 'Create Issue for Warnings':
            (self.cwd / 'codespaces.json').write_text(json.dumps(cfg.get('codespaces', [codespace()])))
        env = {'PATH': str(self.cwd) + ':' + os.environ.get('PATH', '/usr/bin:/bin'),
               'GH_TOKEN': 'synthetic-test-value' if token else '',
               'GITHUB_REPOSITORY': 'dofaromg/flow-tasks',
               'GITHUB_OUTPUT': str(self.output), 'LANG': 'C.UTF-8'}
        return subprocess.run(['bash', '-eo', 'pipefail', '-c', self.steps[name]],
                              cwd=self.cwd, env=env, text=True, capture_output=True)

    def calls(self):
        path = self.cwd / 'calls.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('has_warnings=false', self.output.read_text())

    def test_missing_credential_fails_without_calling_api(self):
        result = self.run_step('Check Codespace Status', token=False)
        self.assert_failed(result)
        self.assertIn('::error', result.stdout)
        self.assertEqual(self.calls(), [])

    def test_codespaces_api_failure_is_not_empty_success(self):
        self.assert_failed(self.run_step('Check Codespace Status', {'api_fail': True}))

    def test_empty_list_is_success(self):
        result = self.run_step('Check Codespace Status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'has_warnings=false\n')

    def test_warning_and_overdue_policy(self):
        for days in (23, 25, 30, 35):
            with self.subTest(days=days):
                self.output.write_text('')
                result = self.run_step('Check Codespace Status', {'codespaces': [codespace(days)]})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('has_warnings=true', self.output.read_text())
                self.assertIn('warning_count=1', self.output.read_text())

    def test_active_codespace_has_no_warning(self):
        result = self.run_step('Check Codespace Status', {'codespaces': [codespace(22)]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_text(), 'has_warnings=false\n')

    def test_invalid_response_and_timestamp_fail(self):
        for cfg in ({'raw_response': 'not json'}, {'raw_response': '{}'},
                    {'codespaces': [{'name': 'invalid', 'lastUsedAt': None}]},
                    {'codespaces': [codespace(last_used='invalid-date')]}):
            with self.subTest(cfg=cfg):
                self.output.write_text('')
                self.assert_failed(self.run_step('Check Codespace Status', cfg))

    def test_listing_limit_is_incomplete(self):
        self.assert_failed(self.run_step('Check Codespace Status', {'codespaces': [codespace()] * 1000}))

    def test_new_warning_creates_one_issue(self):
        result = self.run_step('Create Issue for Warnings')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(a[:2] == ['issue', 'create'] for a in self.calls()), 1)

    def test_existing_or_duplicate_warnings_update_without_creation(self):
        for issues in ([{'number': 42, 'title': TITLE}],
                       [{'number': 42, 'title': TITLE}, {'number': 43, 'title': TITLE}]):
            with self.subTest(issues=issues):
                (self.cwd / 'calls.jsonl').write_text('')
                result = self.run_step('Create Issue for Warnings', {'issues': issues, 'label_exists': True})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any(a[:2] == ['issue', 'create'] for a in self.calls()))
                self.assertTrue(any(a[:3] == ['issue', 'edit', '42'] for a in self.calls()))

    def test_label_creation_failure_fails_before_issue_mutation(self):
        result = self.run_step('Create Issue for Warnings', {'label_fail': True})
        self.assert_failed(result)
        self.assertFalse(any(a[:2] in (['issue', 'create'], ['issue', 'edit']) for a in self.calls()))

    def test_issue_query_create_edit_errors_fail(self):
        for cfg in ({'issue_list_fail': True}, {'issue_create_fail': True},
                    {'issues': [{'number': 42, 'title': TITLE}], 'issue_edit_fail': True}):
            with self.subTest(cfg=cfg):
                self.assert_failed(self.run_step('Create Issue for Warnings', cfg))

    def test_empty_cycle_closes_only_matching_warning(self):
        cfg = {'issues': [{'number': 42, 'title': TITLE}, {'number': 99, 'title': 'Other issue'}]}
        result = self.run_step('Close Old Warning Issues', cfg)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([a[2] for a in self.calls() if a[:2] == ['issue', 'close']], ['42'])

    def test_close_query_and_mutation_errors_fail(self):
        for cfg in ({'issue_list_fail': True},
                    {'issues': [{'number': 42, 'title': TITLE}], 'issue_close_fail': True}):
            with self.subTest(cfg=cfg):
                self.assert_failed(self.run_step('Close Old Warning Issues', cfg))

    def test_workflow_separates_unprivileged_regression_from_monitoring(self):
        self.assertIn('pull_request', self.workflow['on'])
        monitor = self.workflow['jobs']['monitor-codespaces']
        self.assertEqual(monitor['if'], "github.event_name != 'pull_request'")
        self.assertEqual(monitor['needs'], 'regression')
        self.assertEqual(monitor['concurrency']['cancel-in-progress'], 'false')
        check = next(s for s in monitor['steps'] if s.get('id') == 'check')
        self.assertEqual(check['env']['GH_TOKEN'], '${{ secrets.CODESPACES_TOKEN }}')
        self.assertNotIn('Authenticate GitHub CLI', self.steps)
        for name in ('Create Issue for Warnings', 'Close Old Warning Issues'):
            step = next(s for s in monitor['steps'] if s.get('name') == name)
            self.assertEqual(step['env']['GH_TOKEN'], '${{ secrets.GITHUB_TOKEN }}')
            self.assertTrue(step['if'].startswith('steps.check.outputs.has_warnings'))

    def test_every_bash_block_has_valid_syntax(self):
        for name, script in self.steps.items():
            with self.subTest(name=name):
                result = subprocess.run(['bash', '-n'], input=script, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
