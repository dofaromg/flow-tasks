# Mrliou Structure Authorization v1

origin_signature: MrLiouWord  
Source / naming authority: Mr.liou / MrLiouWord  
Implementation assistance: ChatGPT / Codex; provider: OpenAI  
Rights transfer: NOT_GRANTED

## Problem and bounded repair

At main `848f5d62aa807bf61529ceb740517297ab308603`, structure-indexer did not
consume `config/MRL_AUTHORIZATION_REGISTRY_v1.json`. Its `if: always()` upload
could also upload checked-in historical index files after an earlier failure.
The registry requires DENY by default and has no active grants.

This repair connects that registry to the workflow, both direct Python CLIs,
and `run_structure_index.py` (including its trigger-check path). Imported scanner
and generator constructors also check authorization; recursive scans and output
methods recheck it. The shared guard uses Python's standard library.

The actual registry is **unchanged**. This patch creates **no operating grant**.
The instruction to implement this repair is not converted into a scan/upload
grant. No historical artifact is deleted, renamed, regenerated, or overwritten
by a denied invocation. Other workflows, deployment routes, PR #649's evidence
unit and PR #650 are outside the changed-file set.

## Fail-closed contract / 拒絕行為

- The registry is anchored beside the installed repository code. No CLI option
  or environment variable selects a different registry or bypasses denial.
- Empty, missing, unreadable, malformed, duplicate-key, unknown-version or
  weakened-policy registries deny before scanning or reading index input.
- Expired, future, revoked, incomplete, wrong-authority, wrong-grantee,
  wrong-purpose, wrong-environment and nonmatching-scope grants do not permit
  an operation. Ambiguous matching grants and unknown grant constraints deny.
- A GitHub run must be this repository's main structure-indexer workflow;
  event, actor and rerun actor must match the explicit grant. A PR/fork never
  runs the production index job. PR validation uses synthetic fixtures only.
- Before production scanning, one grant must cover scan, generation and the
  exact same-repository GitHub Actions artifact destination. Authorization is
  checked again immediately before upload.
- Upload requires successful authorization, scan, generation and upload
  recheck. Failure/cancellation cannot fall through `always()` into an upload.
  Missing/empty artifact files and symlinked artifact paths fail. The four
  original paths, artifact naming convention and retention period are retained.
- The always-run summary reports outcomes only. It never reads old scan data.
  The diff report stays local. The issue success comment follows a successful
  upload and cannot announce a denied/failed upload as complete.
- Scan root and generator input/output are bound to this checkout and the
  existing canonical paths. Symlink traversal outside the checkout is blocked.
  DL580 paths, other local directories and arbitrary upload destinations are
  not authorized by this consumer.
- Local explicit grants may allow local scan/generation; this guard refuses
  local `structure.upload`. `force_update` is not an authorization override.

An empty-registry workflow run is expected to fail at authorization with
`DENY / NO_RECORDED_GRANT`; it is not a successful index generation. The
regression test job can independently succeed by verifying that refusal.

## Exact grant consumer contract (no real grant included)

The pre-existing registry defines mandatory grant fields, but has no active
records or executable scope interpretation. This consumer recognizes the
following narrow shape; unsupported shapes fail closed rather than inferring
permission. Only MrLiouWord can issue an actual grant through the controlled
registry process. Fixture records in tests are disposable test data.

| Field | Required interpretation |
|---|---|
| `record_id` | Nonempty unique record identifier |
| `grantee` | Exact object containing `actor` and `triggering_actor`; GitHub runtime values, or both `local:<OS username>` |
| `issued_by` | Exactly `MrLiouWord` |
| `issued_at`, `expires_at` | Timezone-aware ISO timestamps; start <= current time < expiry |
| `status` | `active` to permit; revoked/inactive never permit |
| `actions` | Exact action names: `structure.scan`, `structure.generate`, `structure.upload`; no wildcard |
| `prohibited_actions` | Explicit action list; requested actions must not intersect |
| `purpose` | Exactly `structure-index` |
| `environment` | `github-actions` or `local`, matching execution context |
| `evidence_reference`, `rollback` | Nonempty provenance and revocation instructions |
| `scope.repository` | Exactly `dofaromg/flow-tasks` |
| `scope.assets` | Exactly `["."]`: an explicit grant for the existing whole-checkout scanner; this is **not** a default grant or partial-path implementation |
| `scope.max_depth` | Integer 1–8; requested depth cannot exceed it |
| `scope.destination` | `github-actions-artifact:dofaromg/flow-tasks` for that workflow, or `local-checkout` for local use |
| `scope.events` | Explicit matching events from push/schedule/workflow_dispatch/issue_comment/local |
| `scope.ref` | `refs/heads/main` for GitHub, `local` for local use |

All fields above are required and unknown grant/scope fields are rejected.
Partial-path requests need a separately reviewed path-filter implementation;
they cannot be widened to a whole-checkout grant by this patch. No Mother or
SelfMemory topology is copied into the tests or the repair documentation.

The top-level `current_status.checked_at` is historical metadata, not a cached
authorization result. Decisions come from the current validated policy and
active records. Successful guard receipts contain only decision, registry
SHA-256 and `origin_signature`; denial contains a fixed reason code.

## Trust boundary and limits

The code and registry must come from a trusted, reviewed checkout. This is an
application authorization gate, not a sandbox against a host administrator who
can edit Python code, registry contents or process environment. Local username
matching is not cryptographic identity verification. `issued_by` and evidence
references rely on controlled registry issuance, not a newly invented signature
service. Existing governance/review protections are retained.

Already-running old workflow revisions and previously generated/downloaded
artifacts are not retroactively blocked. Nor does this change restrict other
workflows, GitHub Apps, clones, platform processing or downstream use. Historical
authorization/attribution investigations remain separate and unresolved.

## Validation and state updates

Run from the repository root:

```bash
python -m unittest discover -s tests -p test_Mrliou_structure_authorization.py -v
python .copilot/Mrliou_structure_authorization.py preflight
```

The first command runs synthetic positive/negative, direct-CLI, imported-object,
revocation, preserved-artifact, scope, symlink and workflow-contract tests.
With the actual empty registry, the second command must exit 1 with
`NO_RECORDED_GRANT`, and must not scan the repository or generate an artifact.

Record these states separately in the additive backfill:

1. `PATCH_IMPLEMENTED`: exact source head and frozen changed-file list exist.
2. `LOCAL_FAIL_CLOSED_VERIFIED`: tests and empty-registry refusal are recorded.
3. `PR_CI_VERIFIED`: exact PR head's synthetic test job succeeds; production
   index job is skipped; this is not a successful production scan.
4. `MAIN_ENFORCEMENT_VERIFIED`: reviewed repair is merged and a run of the new
   main revision proves authorization refusal, downstream steps skipped and
   zero structure artifacts. Until then,
   `STRUCTURE_INDEX_AUTHORIZATION_ENFORCEMENT = OPEN` on deployed main.

File-delivery coverage is only this repair's expected changed files. It must
not be relabeled as whole-system, historical-investigation or commercial closure.
The manifest lists all eleven expected changes; it hashes the other ten files.
Its own SHA-256 is recorded externally in the delivery/backfill evidence to
avoid a self-referential hash. No ZIP is required by this repository patch.


### Dependency correction discovered by PR CI

Initial PR head `186f1f966ac145e069f245644f45df3184e6cc34` passed the 30 authorization tests but failed the existing sync integrity test: the append-only CHANGELOG grew from 4,419 to 5,284 bytes. The initial nine-file scope is explicitly revised to ten files, adding only `config/Mrliou_MRL_Sync_Delivery_v1.json` as an integrity dependency. Its live CHANGELOG size/hash are refreshed and its entire previous CHANGELOG entry is preserved under `additive_integrity_history`, tied to the original main SHA. No sync workflow, publisher, test, source route or old commit is changed. This is a repair of a regression introduced by this patch, not a pre-existing external blocker.


### Review follow-up: direct smart updater and comment isolation

At `048010a47e2b2ec675ddeff917664fdd400f9937`, direct `smart_updater.py --force` printed `NO_RECORDED_GRANT` but returned exit 0. The updated entrypoint checks authorization before reading/scanning, propagates authorization revocation, and returns exit 1 on denied or failed updates. An authorized no-change result still returns 0. Metrics writes also recheck authorization and their canonical path. No force flag grants permission.

The regression job now ignores ordinary issue comments, preserving the exact `@copilot update-structure-index` trigger. Pull requests still run synthetic tests; production indexing remains restricted to main. Trigger-module changes are included in PR path filters.

Delivery scope is explicitly revised from ten to eleven files by adding `.copilot/triggers/smart_updater.py`. Local verification: 36 authorization tests plus 54 existing sync tests, 90 total and 53 subtests passed. This is local evidence; main closure still requires the separate post-merge run described above. Previous stage records remain historical evidence.


### R03 re-audit and corrective construction

The R02 real-main empty-registry denial remains valid evidence, but did not cover all imported-method and mid-recursion paths. Seven additional behavioral tests failed on that version: swallowed recursive authorization denial, direct file reads after revocation, outside/symlink file reads, caller-reset recursive depth, reduced-depth smart-updater operation, symlinked historical-index reads, and in-memory rendering after revocation. These cases are now corrected. Ordinary filesystem PermissionError handling remains distinct from AuthorizationDenied.

All source-reading scanner paths validate canonical containment, symlink ancestors and actual depth before reading. The smart updater accepts `--depth` and carries it through trigger checking, scanning and generation; the shared runner passes its requested depth. Authorization is rechecked at direct read/render/classification boundaries. No registry grant is added. This remains cooperating-code enforcement, not isolation against an administrator changing code, process memory or files concurrently between checks and use.

R03 expected delivery is exactly nine changed files against `dfadd64d5f6d7e9842f289c08fe87ddfb93b2e22`: scanner, generator, smart updater, common runner, authorization tests, this document, CHANGELOG, sync delivery manifest, and structure authorization delivery manifest. Earlier eleven-file delivery and its hashes are retained in `delivery_history`; its historical status must not be mistaken for this revision's verification. No ZIP is requested; package mapping is the Git commit tree. The delivery integrity regression checks real nonempty payloads, bytes, SHA-256, expected count and dependency existence; external evidence checks the manifest itself and actual changed-file set. R03 main verification must be recorded after merge, not predicted here.
