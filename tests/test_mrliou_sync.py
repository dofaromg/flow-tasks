"""Offline regression tests: MRL source/transport/history boundaries."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('sync_external_repos', ROOT / 'scripts/sync_external_repos.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def init_repo(path):
    path.mkdir()
    git(path, 'init', '-b', 'main')
    git(path, 'config', 'user.email', 'fixture@example.invalid')
    git(path, 'config', 'user.name', 'Offline fixture')
    (path / 'seed.txt').write_text('seed\n')
    git(path, 'add', 'seed.txt')
    git(path, 'commit', '-m', 'fixture seed')
    return path


@pytest.fixture
def manager(tmp_path):
    source = init_repo(tmp_path / 'source')
    (source / 'README').write_text('source data\n')
    (source / 'nested').mkdir()
    (source / 'nested/data.txt').write_text('nested data\n')
    git(source, 'add', '.')
    git(source, 'commit', '-m', 'fixture content')
    repo = {'name': 'fixture', 'url': source.as_uri(), 'branch': 'main',
            'enabled': True, 'files': [{'src': 'README', 'dest': 'imports/README'}]}
    config = tmp_path / 'config.yaml'
    config.write_text(yaml.safe_dump({'repositories': [repo],
                                    'settings': {'conflict_strategy': 'skip'},
                                    'exclude_patterns': ['.git', '__pycache__', '*.pyc']}))
    result = MODULE.RepoSyncManager(str(config))
    result.repo_root = init_repo(tmp_path / 'destination')
    return result, source, repo


def test_source_identity_and_digest(manager):
    m, source, _ = manager
    assert m.sync()
    entry = m.receipt['files'][0]
    assert entry['source_commit'] == git(source, 'rev-parse', 'HEAD')
    assert entry['source_sha256'] == hashlib.sha256(b'source data\n').hexdigest()
    assert entry['source_sha256'] == entry['destination_sha256']
    assert entry['destination'] == 'imports/README'
    assert entry['status'] == 'copied'
    assert m.receipt['origin_signature'] == 'MrLiouWord'
    assert m.receipt['rights_transfer'] == 'NOT_GRANTED'


def test_existing_file_conflict_preserved(manager):
    m, _, _ = manager
    target = m.repo_root / 'imports/README'
    target.parent.mkdir()
    target.write_text('MRL existing data')
    assert m.sync()
    assert target.read_text() == 'MRL existing data'
    assert m.receipt['files'][0]['status'] == 'skipped_conflict'


def test_identical_content_is_noop(manager):
    m, _, _ = manager
    assert m.sync()
    m.receipt['files'] = []
    assert m.sync()
    assert m.receipt['files'][0]['status'] == 'unchanged'


def test_partial_source_failure_is_failure(manager):
    m, source, repo = manager
    m.config['repositories'].append({**repo, 'name': 'missing', 'url': (source / 'absent').as_uri()})
    assert not m.sync()


def test_missing_file_is_failure(manager):
    m, _, repo = manager
    m.config['repositories'][0]['files'].append({'src': 'missing', 'dest': 'imports/missing'})
    assert not m.sync()
    assert m.receipt['errors']


def test_unknown_source_is_failure(manager):
    assert not manager[0].sync('unknown')


def test_disabled_source_is_not_failure(manager):
    m, _, _ = manager
    m.config['repositories'].append({'name': 'disabled', 'enabled': False})
    assert m.sync()


def test_all_disabled_noop(manager):
    m, _, _ = manager
    m.config['repositories'][0]['enabled'] = False
    assert m.sync()
    assert m.receipt['files'] == []


@pytest.mark.parametrize('path', ['../escape', '/tmp/escape', '.git/config', '.github/workflows/evil.yml',
                                 'scripts/mrliou_publish_sync.sh', 'scripts/sync_external_repos.py',
                                 'repos_sync.yaml', '.env'])
def test_unsafe_destinations_rejected(manager, path):
    m, _, _ = manager
    m.config['repositories'][0]['files'][0]['dest'] = path
    with pytest.raises(ValueError):
        m.sync()


def test_source_symlink_rejected(manager):
    m, source, _ = manager
    (source / 'link').symlink_to('README')
    git(source, 'add', 'link')
    git(source, 'commit', '-m', 'fixture symlink')
    m.config['repositories'][0]['files'][0]['src'] = 'link'
    with pytest.raises(ValueError):
        m.sync()


def test_destination_symlink_rejected(manager):
    m, source, _ = manager
    (m.repo_root / 'imports').symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError):
        m.sync()


def test_directory_honors_skip_and_exclusions(manager):
    m, source, _ = manager
    m.config['repositories'][0]['files'] = []
    m.config['repositories'][0]['directories'] = [{'src': 'nested', 'dest': 'imports'}]
    (source / 'nested/__pycache__').mkdir()
    (source / 'nested/__pycache__/hidden.txt').write_text('exclude')
    git(source, 'add', '.')
    git(source, 'commit', '-m', 'fixture exclusion')
    (m.repo_root / 'imports').mkdir()
    (m.repo_root / 'imports/data.txt').write_text('existing')
    assert m.sync()
    assert (m.repo_root / 'imports/data.txt').read_text() == 'existing'
    assert not (m.repo_root / 'imports/__pycache__').exists()
    assert m.receipt['files'][0]['status'] == 'skipped_conflict'


def test_missing_directory_is_failure(manager):
    m, _, _ = manager
    m.config['repositories'][0]['directories'] = [{'src': 'missing', 'dest': 'imports'}]
    assert not m.sync()


def test_file_cannot_masquerade_as_directory(manager):
    m, _, _ = manager
    m.config['repositories'][0]['directories'] = [{'src': 'README', 'dest': 'imports'}]
    assert not m.sync()


def test_integrity_failure_is_failure(manager, monkeypatch):
    m, _, _ = manager
    monkeypatch.setattr(MODULE.shutil, 'copy2', lambda src, dest: dest.write_text('corruption'))
    assert not m.sync()
    assert m.receipt['files'][0]['status'] == 'integrity_failed'


def test_post_command_failure_not_success(manager):
    m, _, _ = manager
    m.config['settings']['post_sync_commands'] = ['git definitely-not-a-command']
    assert not m.sync()


@pytest.fixture
def publication(manager, tmp_path):
    m, _, _ = manager
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    git(m.repo_root, 'remote', 'add', 'origin', str(remote))
    git(m.repo_root, 'push', 'origin', 'main')
    base = git(m.repo_root, 'rev-parse', 'HEAD')
    assert m.sync()
    artifacts = tmp_path / 'artifacts'
    m.write_receipt(str(artifacts / 'receipt.json'), True)
    # Simulate only the PR service. Local real Git exercises history and bundles.
    tools_dir = tmp_path / 'tools'
    tools_dir.mkdir()
    gh = tools_dir / 'gh'
    gh.write_text('''#!/usr/bin/env bash
set -eu
echo "$*" >> "$GH_CALL_LOG"
if [[ "$*" == *"pr create"* ]]; then
  if [[ "${GH_DENY:-0}" == 1 ]]; then exit 1; fi
  echo 'https://github.com/fixture/repo/pull/1'
elif [[ "$*" == *"--json state"* ]]; then
  echo "${GH_STATE:-}"
else
  echo 'https://github.com/fixture/repo/pull/1'
fi
''')
    gh.chmod(0o755)
    env = {**os.environ, 'PATH': str(tools_dir) + os.pathsep + os.environ['PATH'],
           'MRL_SYNC_REPORT': str(artifacts / 'receipt.json'),
           'MRL_SYNC_ARTIFACT_DIR': str(artifacts),
           'GITHUB_OUTPUT': str(tmp_path / 'outputs'),
           'GITHUB_STEP_SUMMARY': str(tmp_path / 'summary'),
           'GITHUB_REPOSITORY': 'fixture/repo',
           'GH_CALL_LOG': str(tmp_path / 'gh.log')}
    return m, remote, base, env, artifacts


def publish(p, **overrides):
    return subprocess.run(['bash', str(ROOT / 'scripts/mrliou_publish_sync.sh')],
                          cwd=p[0].repo_root, env={**p[3], **overrides},
                          capture_output=True, text=True)


def test_publish_preserves_main_and_bundle(publication):
    p = publication
    result = publish(p)
    assert result.returncode == 0, result.stderr
    assert git(p[1], 'rev-parse', 'main') == p[2]
    assert git(p[0].repo_root, 'rev-parse', 'HEAD^') == p[2]
    assert (p[4] / 'candidate.patch').stat().st_size > 0
    subprocess.run(['git', 'bundle', 'verify', str(p[4] / 'candidate.bundle')],
                   cwd=p[0].repo_root, check=True, capture_output=True)
    assert 'candidate_pr_ready' in Path(p[3]['GITHUB_OUTPUT']).read_text()
    assert 'source_commit' in (p[4] / 'pr-body.md').read_text()
    receipt = json.loads((p[4] / 'receipt.json').read_text())
    assert receipt['destination_base_commit'] == p[2]
    assert receipt['destination_repository'] == 'fixture/repo'


def test_publish_permission_failure_preserves_candidate(publication):
    p = publication
    result = publish(p, GH_DENY='1')
    assert result.returncode != 0
    assert git(p[1], 'rev-parse', 'main') == p[2]
    assert 'Mrliou_MRL_external_sync/' in git(p[1], 'branch', '--list')
    assert (p[4] / 'candidate.bundle').exists()
    assert 'candidate_pr_ready' not in Path(p[3]['GITHUB_OUTPUT']).read_text()


def test_publish_refuses_unrelated_file(publication):
    p = publication
    (p[0].repo_root / 'unrelated.txt').write_text('do not stage')
    assert publish(p).returncode != 0
    assert git(p[0].repo_root, 'rev-parse', 'HEAD') == p[2]
    assert git(p[1], 'branch', '--list') == '* main' or git(p[1], 'branch', '--list').strip() == 'main'


def test_publish_refuses_modified_payload(publication):
    p = publication
    (p[0].repo_root / 'imports/README').write_text('changed since receipt')
    assert publish(p).returncode != 0
    assert git(p[0].repo_root, 'rev-parse', 'HEAD') == p[2]


def test_publish_refuses_hidden_staged_change(publication):
    p = publication
    seed = p[0].repo_root / 'seed.txt'
    seed.write_text('unrelated staged content')
    git(p[0].repo_root, 'add', 'seed.txt')
    seed.write_text('seed\n')  # Net worktree diff is empty, but the index is not.
    assert publish(p).returncode != 0
    assert git(p[0].repo_root, 'rev-parse', 'HEAD') == p[2]
    assert git(p[0].repo_root, 'show', ':seed.txt') == 'unrelated staged content'


def test_publish_refuses_failed_receipt(publication):
    p = publication
    p[0].write_receipt(str(p[4] / 'receipt.json'), False)
    assert publish(p).returncode != 0
    assert git(p[0].repo_root, 'rev-parse', 'HEAD') == p[2]


def test_publish_reuses_identical_candidate(publication, tmp_path):
    p = publication
    assert publish(p).returncode == 0
    first = git(p[1], 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads')
    new = tmp_path / 'retry'
    subprocess.run(['git', 'clone', '--branch', 'main', str(p[1]), str(new)],
                   check=True, capture_output=True)
    p[0].repo_root = new
    p[0].receipt['files'] = []
    assert p[0].sync()
    p[0].write_receipt(str(p[4] / 'receipt.json'), True)
    result = publish(p, GH_STATE='OPEN')
    assert result.returncode == 0, result.stderr
    assert first == git(p[1], 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/heads')
    assert Path(p[3]['GH_CALL_LOG']).read_text().count('pr create') == 1


def test_publish_does_not_reopen_closed_candidate(publication):
    result = publish(publication, GH_STATE='CLOSED')
    assert result.returncode != 0
    assert 'pr create' not in Path(publication[3]['GH_CALL_LOG']).read_text()


def test_publish_preserves_changed_remote_candidate(publication, tmp_path):
    p = publication
    assert publish(p).returncode == 0
    branch = next(row.split()[1] for row in git(p[1], 'show-ref', '--heads').splitlines()
                  if 'Mrliou_MRL_external_sync/' in row)
    (p[0].repo_root / 'imports/README').write_text('owner review edit')
    git(p[0].repo_root, 'add', 'imports/README')
    git(p[0].repo_root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-m', 'owner edit')
    git(p[0].repo_root, 'push', 'origin', f'HEAD:{branch}')
    owner_head = git(p[1], 'rev-parse', branch)
    new = tmp_path / 'retry'
    subprocess.run(['git', 'clone', '--branch', 'main', str(p[1]), str(new)],
                   check=True, capture_output=True)
    p[0].repo_root = new
    p[0].receipt['files'] = []
    assert p[0].sync()
    p[0].write_receipt(str(p[4] / 'receipt.json'), True)
    assert publish(p, GH_STATE='OPEN').returncode != 0
    assert git(p[1], 'rev-parse', branch) == owner_head
    assert git(p[1], 'rev-parse', 'main') == p[2]
    assert Path(p[3]['GH_CALL_LOG']).read_text().count('pr create') == 1


def test_no_change_creates_no_commit(manager, tmp_path):
    m, _, _ = manager
    m.config['repositories'][0]['enabled'] = False
    assert m.sync()
    artifacts = tmp_path / 'artifacts'
    m.write_receipt(str(artifacts / 'receipt.json'), True)
    before = git(m.repo_root, 'rev-parse', 'HEAD')
    env = {**os.environ, 'MRL_SYNC_REPORT': str(artifacts / 'receipt.json'),
           'MRL_SYNC_ARTIFACT_DIR': str(artifacts), 'GITHUB_REPOSITORY': 'fixture/repo',
           'GITHUB_OUTPUT': str(tmp_path / 'outputs'), 'GITHUB_STEP_SUMMARY': str(tmp_path / 'summary')}
    p = subprocess.run(['bash', str(ROOT / 'scripts/mrliou_publish_sync.sh')],
                       cwd=m.repo_root, env=env, capture_output=True)
    assert p.returncode == 0, p.stderr
    assert git(m.repo_root, 'rev-parse', 'HEAD') == before
    assert 'no_candidate' in (tmp_path / 'outputs').read_text()


def test_workflow_boundaries():
    workflow = yaml.safe_load((ROOT / '.github/workflows/sync-external-repos.yml').read_text())
    events = workflow.get('on', workflow.get(True))  # YAML 1.1 parser compatibility
    assert events['schedule'] == [{'cron': '0 0 * * 1'}]
    assert workflow['permissions'] == {'contents': 'read'}
    job = workflow['jobs']['sync']
    assert "github.event_name != 'pull_request'" in job['if']
    assert "refs/heads/main" in job['if']
    assert job['needs'] == 'test'
    assert 'runner.' not in yaml.safe_dump(job.get('env', {}))
    assert not any(s.get('continue-on-error') for s in job['steps'])
    text = (ROOT / '.github/workflows/sync-external-repos.yml').read_text()
    assert 'git add .' not in text and 'git push origin' not in text
    assert '${{ github.event.inputs.repo_name }}' not in text


def test_runner_paths_are_prepared_at_step_scope(tmp_path):
    workflow = yaml.safe_load((ROOT / '.github/workflows/sync-external-repos.yml').read_text())
    prepare = workflow['jobs']['sync']['steps'][0]
    env_file = tmp_path / 'github-env'
    result = subprocess.run(['bash', '-eu', '-o', 'pipefail', '-c', prepare['run']],
                            env={**os.environ, 'RUNNER_TEMP': str(tmp_path),
                                 'GITHUB_ENV': str(env_file)}, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert env_file.read_text().splitlines() == [
        f'MRL_SYNC_ARTIFACT_DIR={tmp_path}/Mrliou_MRL_sync',
        f'MRL_SYNC_REPORT={tmp_path}/Mrliou_MRL_sync/receipt.json']


def test_enabled_route_shape():
    config = yaml.safe_load((ROOT / 'repos_sync.yaml').read_text())
    enabled = [r for r in config['repositories'] if r.get('enabled', True)]
    for repo in enabled:
        assert repo['name'] and repo['url'] and repo['branch']
        assert repo.get('files') or repo.get('directories') or repo.get('submodule')


def test_delivery_manifest_integrity():
    manifest_path = 'config/Mrliou_MRL_Sync_Delivery_v1.json'
    manifest = json.loads((ROOT / manifest_path).read_text())
    entries = manifest['files']
    assert len(entries) == manifest['expected_file_count'] == 7
    assert len({entry['path'] for entry in entries}) == 7
    for entry in entries:
        payload = (ROOT / entry['path']).read_bytes()
        assert payload
        assert all((ROOT / dep).is_file() for dep in entry['dependencies'])
        if entry['path'] != manifest_path:
            assert len(payload) == entry['size_bytes']
            assert hashlib.sha256(payload).hexdigest() == entry['sha256']
