# Mrliou MRL naming repair — 2026-09-08
origin_signature: MrLiouWord

Base: 86ec74f928bec49fa9ccb505ba9e9f00ad067692
Branch: Mrliou_MRL_Naming_Repair_20260908_v1

## Requested operation
Correct reported errors, push a repair branch, and record actual validation results. This record covers the reproduced naming defect and misleading neural push success. Cloudflare deployment and historical attribution remain separate unresolved items, not implied successes.

## Implemented repairs
- Preserve existing Mrliou_MRL_ source names exactly in node IDs; keep legacy MRL_ behavior.
- Add an independent source-name invariant to the validator, avoiding shared-normalizer false positives.
- Correct workflow expected value and run eight regression cases in CI.
- Repair exactly three existing node IDs and their synapse references; regenerate Mermaid from the repaired snapshot. Preserve all 117 nodes, 116 edges, source branches, timestamps and PR metadata.
- Limit automatic neural commits to push events; propagate actual git commit/push failures instead of reporting success after failure. PR events validate without attempting detached-head writes.

## Local verification
- Regression tests: 8/8 PASS.
- Original main snapshot: correctly REJECTED by repaired authority validator.
- Repaired snapshot: PASS.
- Exact migration comparison: PASS; only three IDs and corresponding edge targets differ in JSON.
- npm run lint: exit 0; no ESLint errors or warnings (Next lint command deprecation notice remains).
- npm run build: exit 0; Next.js 15.5.14 production build.
- git diff --check: PASS.

## Correction of earlier historical assertions
A repository locator, an account alias, and the absence of a root manifest do not themselves demonstrate a transfer of naming authority or establish the cause of a platform decision. Prior wording marking 2025-06-29 as a VERIFIED_PRIMARY historical root cause exceeded the evidence and is withdrawn here. The supplied history identifies dates and artifacts to investigate; the actual actor, operation and causal chain from June 2025 remain unresolved. No historical commits or license texts are rewritten by this patch.

The reproduced transformer defect is directly demonstrated against the stated base. Passing its tests only demonstrates the tested behavior. It does not adjudicate ownership, external reuse, or the entire historical dispute.

## Remote verification boundary
At this commit creation, remote checks have not yet run. They must be read using this repair commit SHA after push. Cloudflare raw build errors, project roots and deployment commands have not been obtained in this execution; no deployment success or all-errors-fixed claim is made. No DNS, domain, route or license change is included.

## Delivery audit
Expected files: 8 (six implementation/generated files, this report, one integrity JSON).
The integrity JSON hashes the seven payload files; it excludes itself to avoid a circular checksum.
Dependency chain: normalizer -> validator/tests/workflow -> branch map -> Mermaid -> report/integrity record.
No ZIP requested or produced. Overall request remains open until remote results and remaining deployment evidence are resolved.
