#!/usr/bin/env bash
# MrLiouWord engineering transport only; never push, reset, or force main.
set -euo pipefail

: "${MRL_SYNC_REPORT:?Run-local receipt is required}"
: "${MRL_SYNC_ARTIFACT_DIR:?Run-local artifact directory is required}"
: "${GITHUB_REPOSITORY:?Explicit repository is required}"
: "${GITHUB_OUTPUT:?Workflow output file is required}"
: "${GITHUB_STEP_SUMMARY:?Workflow summary file is required}"
git rev-parse --show-toplevel >/dev/null
BASE_SHA=$(git rev-parse HEAD)
# A hidden staged edit must not hitchhike on the receipt's allowed files.
if ! git diff --cached --quiet; then
  echo 'Pre-existing staged changes; no publication performed.' >&2
  exit 1
fi
mkdir -p "$MRL_SYNC_ARTIFACT_DIR"

# Stage only successfully copied files, never backups, secrets or unrelated edits.
python - "$MRL_SYNC_REPORT" "$MRL_SYNC_ARTIFACT_DIR" <<'PY'
import hashlib
import json
import os
import pathlib
import subprocess
import sys

report = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
if report.get('success') is not True or report.get('errors'):
    raise SystemExit('Refusing to publish a failed or incomplete synchronization')
root = pathlib.Path.cwd().resolve()
artifact = pathlib.Path(sys.argv[2]).resolve()
if artifact.is_relative_to(root):
    raise SystemExit('Artifacts must stay outside the source worktree')
report['destination_base_commit'] = subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], text=True).strip()
report['destination_repository'] = os.environ['GITHUB_REPOSITORY']
paths = set()
for entry in report['files']:
    if entry['status'] != 'copied':
        continue
    path = pathlib.Path(entry['destination'])
    if path.is_absolute() or any(p in {'.', '..', '.git', '.github'} for p in path.parts):
        raise SystemExit('Unsafe publication path')
    file = root / path
    if (not file.resolve().is_relative_to(root) or not file.is_file() or
            any(p.is_symlink() for p in [file, *file.parents] if p != root)):
        raise SystemExit('Publication path is not a regular file within the repository')
    if hashlib.sha256(file.read_bytes()).hexdigest() != entry['destination_sha256']:
        raise SystemExit('Output changed after receipt generation')
    paths.add(path.as_posix())
changed = set()
for args in [('diff', '--name-only', '-z', 'HEAD'),
             ('ls-files', '--others', '--exclude-standard', '-z')]:
    changed.update(p for p in subprocess.check_output(['git', *args]).decode().split('\0') if p)
if changed - paths:
    raise SystemExit('Unrelated working-tree changes; no publication performed')
payload = b''.join(p.encode() + b'\0' for p in sorted(paths))
(artifact / 'paths.nul').write_bytes(payload)
body = ('## MRL external-source synchronization candidate\n\n'
        'Engineering transport only. Source identities and paths are preserved.\n'
        'No product release, license grant, ownership transfer or auto-merge.\n'
        'Repository owner decides integration; trusted-governance must check this head.\n'
        'GITHUB_TOKEN-created PRs may require owner workflow approval or a supported '
        'human PR event. A missing check is not a successful check.\n\n'
        '## Source / output receipt\n\n```json\n' +
        json.dumps(report, ensure_ascii=False, indent=2) + '\n```\n')
if len(body.encode()) > 60000:
    raise SystemExit('Receipt exceeds PR body budget; preserve artifact for bounded review')
pathlib.Path(sys.argv[1]).write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(artifact / 'pr-body.md').write_text(body, encoding='utf-8')
PY

if [[ ! -s "$MRL_SYNC_ARTIFACT_DIR/paths.nul" ]]; then
  echo 'state=no_candidate' >> "$GITHUB_OUTPUT"
  echo 'No new candidate. Consult receipt for unchanged files or preserved conflicts.' >> "$GITHUB_STEP_SUMMARY"
  exit 0
fi
git --literal-pathspecs add --pathspec-from-file="$MRL_SYNC_ARTIFACT_DIR/paths.nul" --pathspec-file-nul
if git diff --cached --quiet; then
  echo 'state=no_candidate' >> "$GITHUB_OUTPUT"
  exit 0
fi
TREE_SHA=$(git write-tree)
# Content-addressed candidates avoid force-updating an existing review/history.
SYNC_BRANCH="Mrliou_MRL_external_sync/${BASE_SHA:0:12}-${TREE_SHA:0:12}"
git diff --cached --binary > "$MRL_SYNC_ARTIFACT_DIR/candidate.patch"
git -c user.name='github-actions[bot]' \
    -c user.email='github-actions[bot]@users.noreply.github.com' \
    commit -m 'fix(MRL): preserve external sync candidate for owner integration'
git bundle create "$MRL_SYNC_ARTIFACT_DIR/candidate.bundle" "${BASE_SHA}..HEAD"
echo "candidate_branch=$SYNC_BRANCH" >> "$GITHUB_OUTPUT"

REMOTE_SHA=$(git ls-remote --heads origin "refs/heads/$SYNC_BRANCH" | cut -f1)
if [[ -n "$REMOTE_SHA" ]]; then
  git fetch --no-tags origin "refs/heads/$SYNC_BRANCH"
  if [[ "$(git rev-parse FETCH_HEAD^{tree})" != "$TREE_SHA" ]]; then
    echo 'Existing candidate has changed; preserving its history, no force push.' >&2
    exit 1
  fi
else
  git push origin "HEAD:refs/heads/$SYNC_BRANCH"
fi

# A permission denial retains the branch and bundle; never broaden credentials.
PR_STATE=$(gh pr list --repo "$GITHUB_REPOSITORY" --head "$SYNC_BRANCH" \
  --base main --state all --json state --jq '.[0].state // empty')
if [[ "$PR_STATE" == 'CLOSED' || "$PR_STATE" == 'MERGED' ]]; then
  echo 'Candidate was already decided; preserve that decision and stop.' >&2
  exit 1
elif [[ "$PR_STATE" == 'OPEN' ]]; then
  PR_URL=$(gh pr list --repo "$GITHUB_REPOSITORY" --head "$SYNC_BRANCH" \
    --base main --state open --json url --jq '.[0].url')
else
  PR_URL=$(gh pr create --repo "$GITHUB_REPOSITORY" --base main --head "$SYNC_BRANCH" \
    --draft --title 'fix(MRL): external sync candidate — source lineage retained' \
    --body-file "$MRL_SYNC_ARTIFACT_DIR/pr-body.md")
fi
echo 'state=candidate_pr_ready' >> "$GITHUB_OUTPUT"
echo "pr_url=$PR_URL" >> "$GITHUB_OUTPUT"
echo "Candidate preserved: $PR_URL — main unchanged, integration and commercial release not implied." >> "$GITHUB_STEP_SUMMARY"
