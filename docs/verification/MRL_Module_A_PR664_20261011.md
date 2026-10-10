# Module-A container follow-up to PR #664

origin_signature: MrLiouWord

## Scope and lineage

- Requested by Mr.liou on 2026-10-11 (Asia/Taipei).
- Exact parent: `d9acaa56fecb4593484a87c17b7384c3bf44f4fb` from PR #664.
- Follow-up branch: `Mrliou/fix-module-a-container-pr664-20261011`.
- All edited sources are MRL-native configuration, runtime, tests or evidence.
- Preserve #664's FlowGate deny-overrides, optional binding guard, history and
  single `/info` registration. No FlowOS source change, history rewrite, main
  merge, registry push, GCP authentication or production deployment is performed.

## Repair

The old module-a-only Docker context cannot contain sibling `apps/common/`.
The module-a matrix entry now uses `./apps`. Its Dockerfile installs the unchanged
module-a requirements and copies only `app.py`, `core.py` and `common/` into
`/app/module-a/` and `/app/common/`. The existing parent-directory import then
works without PYTHONPATH injection or source mounts. Other services, image tags,
registry settings, deployment manifests, CMD and healthcheck are unchanged.

Real Flask also reproduced a separate input-shape defect: nonempty JSON lists,
strings, numbers and booleans produced 500 via `data.get`. A two-line dictionary
check returns the existing `400 {"ok": false, "error": "invalid_input"}` contract.
The runtime tests verify that unexpected exception details stay in server logs
and are absent from HTTP responses. No broad exception handler is added.

## Verification and honest boundaries

The adjacent JSON records complete local stdout/stderr, package versions,
source SHA-256 values, expected files, dependency mapping and baseline comparison.
Local real-Flask tests: **20 passed**. Local HTTP startup uses `python app.py` and
real loopback requests. Neither result is presented as Docker validation.

The local environment has no Docker CLI or daemon: **container build/start/HTTP
are UNVERIFIED locally**. `Module-A Container Smoke` supplies an independent,
read-only GitHub-hosted PR job; it checks out the exact proposed head, runs real
Flask tests, builds the Dockerfile, starts its unchanged CMD, checks imported
source hashes and route uniqueness inside the image, and exercises HTTP with no
source bind mounts. It never pushes images or authenticates to a registry.
Actual runner results and artifacts must be read before declaring Docker PASS.
The JSON is a timestamped local snapshot, not a claim about future runner results.

**Deployment acceptance: NOT PERFORMED.** Local or runner smoke PASS does not
establish GKE/ArgoCD deployment readiness. Orchestrator's similar build-context
issue remains outside this module-a-only request.

## Reproduce

From the repository root, with real dependencies installed:

```sh
python -m pip install -r apps/module-a/requirements.txt pytest
python -m pytest -v tests/test_module_a_runtime.py
python scripts/verify_module_a_container.py --report module-a-container.json
```

The container verifier exits 0 only after build, startup, image checks and HTTP
checks pass; 2 means Docker CLI unavailable; other failures exit 1. It retains
build output, command exit codes, HTTP bodies, image/container inspection and
server logs. The test container is removed after evidence capture and its unique
test image tag is removed. No existing container or image tag is modified.

The PR workflow uploads the full evidence directory even after a failed step.
Review the exact tested source commit and image ID in `container.json`.

## Delivery map

Expected changed files: 8 (3 modified sources/configuration, 5 added verification
files). The adjacent JSON contains the exact list and dependency tree. No archive
was requested; ZIP/manifest-count checks are not applicable. The JSON's own hash
is recorded externally in the PR delivery audit to avoid a self-referential hash.

`CHANGELOG.md` remains byte-identical because existing delivery manifests pin its
hash; this scoped note records the change without unrelated manifest rewrites.
Rollback the follow-up commit(s) only; preserve PR #664 and its FlowGate fixes.
File-delivery completeness, runtime tests, container tests and deployment status
are separate results. Owner retains final review and merge decisions.
