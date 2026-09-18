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
The manifest lists all nine expected changes; it hashes the other eight files.
Its own SHA-256 is recorded externally in the delivery/backfill evidence to
avoid a self-referential hash. No ZIP is required by this repository patch.
