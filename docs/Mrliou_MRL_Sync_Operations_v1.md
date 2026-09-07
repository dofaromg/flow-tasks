# Mrliou_MRL_Sync_Operations_v1

origin_signature: MrLiouWord

Version: 1.0.0

Scope: existing flow-tasks external-sync engineering transport; not a product release.

## Purpose / 營運目的

Keep the existing source routes usable while retaining MRL control, source attribution,
review decisions and repository history. GitHub is the engineering transport and version
host; a workflow result neither determines origin nor grants commercial rights.
本次只修既有公開同步器的工程路徑，不發布私人母體、SelfMemory、客戶資料或商務原件。

## Baseline and signals / 已知狀態

Baseline main: `25e8ac661ec82995ca90aeb6cf962990bae31356`.

| Surface | Observed result | Operational interpretation |
| --- | --- | --- |
| [flow-tasks run 34073726069](https://github.com/dofaromg/flow-tasks/actions/runs/34073726069) | Source copy completed; direct main push rejected by GH013 | Repair the publisher; retain main rules and trusted-governance |
| [mrliouword-system run 34075538266](https://github.com/Mrliou/mrliouword-system/actions/runs/34075538266) | Failure with zero step records | Exact run annotation still needed; do not classify as a Python/core failure |
| [mrlioudb run 34076315144](https://github.com/dofaromg/mrlioudb/actions/runs/34076315144) | Clone succeeded, existing Hello World file skipped, no changes | Successful execution is not proof of fresh data or full MRL database sync |

The flow-tasks enabled source remains `octocat/Hello-World`, branch `master`, with
`README -> examples/synced_files/hello_world_readme.txt`. The three disabled sources
remain disabled. `repos_sync.yaml` and the existing `skip` policy are unchanged.
No DNS, application route, payment account, other repository, PR #633, repository
ruleset, CODEOWNERS, naming registry or license file is changed by this repair.

## Delivery contract / 實際交付契約

1. Read the protected main workflow/configuration; PR events run offline tests only.
2. Copy selected source data without executing imported source code.
3. Keep source URL, branch, exact source commit, original source path, destination,
   SHA-256 and size in the run receipt; publication adds the destination repository
   and base commit for recovery. `origin_signature` identifies the MRL receipt,
   not a reassignment of external source authorship.
4. Fail the run if any enabled source fails, a required file/directory is absent,
   integrity differs, or a post-sync command fails. Disabled sources are not failures.
5. Classify equal existing data as `unchanged`; preserve different existing data as
   `skipped_conflict` under the existing skip policy, for both files and directories.
6. Publish only the receipt's successfully copied paths. Unexpected worktree changes
   abort publication. No blanket `git add .`, deletion, rename or imported hook run.
7. Address the candidate branch by base SHA and resulting tree SHA:
   `Mrliou_MRL_external_sync/<base12>-<tree12>`. Repeated identical runs reuse an open
   PR; existing decided or changed candidates are retained, never reopened/force-pushed.
8. Preserve a binary patch and incremental Git bundle **before** remote writes, then
   push only the candidate branch and create a draft PR with the source receipt.
9. Report candidate delivery separately from main integration and commercial release.
   Only an owner-approved merge may change main through its existing protection.

Using content-addressed branches instead of rewriting one shared sync branch is deliberate:
old candidates, decisions and base lineage remain addressable; a changed source or base
produces a distinct candidate rather than silently replacing history.

Automated publication covers receipted regular-file copies only. The existing optional
submodule support and post-sync commands remain in the local synchronizer, but gitlinks,
`.gitmodules` and extra generated files require a separate owner-reviewed change;
they are not silently included in this publisher. Current enabled routes use neither.

## Rights and operating boundaries / 商務規範對應

| Concern | Implemented boundary |
| --- | --- |
| MRL identity and tool role | MRL receipt signature, separate source identity and transport role |
| Rights | `rights_transfer=NOT_GRANTED`; no inference of a license from clone/access |
| Commercial release | `NOT_APPROVED_BY_SYNC`; no deployment, sale, license expansion or auto-merge |
| Existing operations | Source/destination routes, main protections and conflict policy retained |
| Cost | No empty commit or PR on unchanged data; repeated candidates reuse their PR |
| Exit and recovery | Binary patch, incremental bundle, source SHA and hashes; owner can export |
| Truthful status | Copy success, preserved conflict, failure and PR delivery are separate outcomes |

These are engineering controls, not legal conclusions or a replacement for contracts.
Commercial approval, customer rights, supplier terms and retained rights remain separate
owner decisions. Nothing in this change grants a third party MRL core/source rights or
changes third-party rights. New/private source routes require explicit scope review;
do not add credentials, private vaults or whole-world exports to this public workflow.

## Required-check handoff / 主線接入

`GITHUB_TOKEN` events do not behave like a human or independent GitHub App event.
GitHub documents approval-required `pull_request` runs for token-created PRs;
this repository's `trusted-governance` instead uses `pull_request_target`.
Therefore **do not assume a bot-created PR has acquired the required check**.

After inspecting the candidate, the owner marks its draft PR **Ready for review**.
The existing `ready_for_review` activity in `mrl-root-governance-gate.yml` provides
an owner-triggered path to validate the proposed head from trusted main. Confirm the
result corresponds to the current head; don't substitute a main-only manual run.
If no matching run is available, retain the candidate and report the execution/permission
blocker. Do not bypass rules, fake status, broaden tokens or weaken protection.

If GitHub disallows Actions-created PRs, publication fails visibly after preserving the
branch and bundle. The owner may create the PR from that exact branch through the
normal interface. The workflow never changes repository policy to make itself succeed.

Reference: [GitHub workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

## mrlioudb schedule continuity / 另一倉庫不混修

Open the existing [workflow page](https://github.com/dofaromg/mrlioudb/actions/workflows/sync-external-repos.yml).
Use its keep-enabled notice when offered; if already disabled, use Enable workflow.
Do not change its code or make an empty commit solely to suppress the warning.
Preserve the current source routes. Verify the enabled state and the next actual run;
a previous successful run does not prove that the schedule remains enabled now.

GitHub may disable public-repository schedules after 60 days of repository inactivity.
Reference: [Disabling and enabling workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).

## Local checks / 離線驗收

```bash
python -m pytest -q -o addopts='' tests/test_mrliou_sync.py
python -m py_compile scripts/sync_external_repos.py tests/test_mrliou_sync.py
bash -n scripts/mrliou_publish_sync.sh
git diff --check
```

The tests use temporary local source repos and a local bare destination. Only the PR
service is simulated; no production GitHub branch, payment or external source is mutated.
Tests cover copies, provenance, unchanged content, conflicts, disabled/unknown sources,
partial failure, path traversal, symlinks, protected controls, integrity, post-command
failure, actual Git publication, PR denial, no-op and repeat candidate reuse.

## Recovery / 可逆性

- Source failure: no candidate publication. Preserve receipt; resolve that source only.
- PR creation failure: candidate branch + binary patch + bundle remain; don't re-run
  with more powerful credentials without owner authorization.
- Patch recovery: in a clean checkout at the receipt's base, inspect then use
  `git apply --check candidate.patch`; apply only after owner selection.
- Bundle recovery: `git bundle verify candidate.bundle`; the bundle is incremental
  and requires the recorded base commit. It is not a full repository backup.
- Bad candidate: close without merge and retain the branch/receipt. No force resets.
- Repair rollback: make an explicit reverting commit/PR; don't delete history. Reverting
  to the historical direct-main workflow restores that known failure as well.
- Artifacts have 90-day retention. Export important candidates before expiry; PR body
  retains the receipt while Git retains published branch history. This is not a promise
  of perpetual artifact hosting.

## Requested / Generated scope

Exactly seven engineering files are in this repair:

| Path | Role | Dependencies |
| --- | --- | --- |
| `.github/workflows/sync-external-repos.yml` | Existing job, repaired transport | sync script, publisher, tests, existing config |
| `scripts/sync_external_repos.py` | Existing synchronizer plus outcome/receipt safety | Python stdlib, PyYAML, Git, existing config |
| `scripts/mrliou_publish_sync.sh` | Candidate publisher | receipt, Bash, Python, Git, GitHub CLI |
| `tests/test_mrliou_sync.py` | Offline regression coverage | synchronizer, publisher, workflow, pytest |
| `docs/Mrliou_MRL_Sync_Operations_v1.md` | Operations, boundaries and recovery | actual code and current run references |
| `CHANGELOG.md` | Additive change history | repaired behavior |
| `config/Mrliou_MRL_Sync_Delivery_v1.json` | Expected file/dependency map | six payload files plus this manifest |

File/hash validation is an internal delivery check, not an external determination of
MRL identity. Local tests, remote checks, merge and scheduled end-to-end operation are
separate milestones; report each according to observed results.
