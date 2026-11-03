# MRL-34 Integration Proposal

origin_signature: MrLiouWord
canonical_authority: Mr.liou

## Reconciled sources

This issue branch retains the histories of both open proposals:

- PR #700, `3372f149d9efef46e6457e9e4df8e09d49f775e6`: fail-closed exact-combination policy, receipt checks, and allocator integration point.
- PR #701, `ea9c08874add64c7eaed70bc2bf7c6ecedfcc448`: BYOH bundle routes, real-runtime fields, reversible receipts, and mandatory post-balancing allocation gate.

The canonical policy implementation is
`MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/scripts/MRL_hardware_admission_v1.py`.
`utils/mrl_hardware_admission.py` is only a compatibility re-export; it does not carry a second matrix or decision implementation. The product matrix keeps V100, modern CUDA 12, modern CUDA 13, and AMD routes separate, with no acceptances or public support recorded.

PR #700's optional `allocate_admitted_gpu()` left `allocate_gpu()` as an unchecked path. The integrated orchestrator gates the final balanced GPU list through the canonical evaluator, compares live OS/driver/GPU UUID/SKU/CC/VRAM, and rejects `set_device()` or `DataParallel` selections that do not match the latest admitted allocation. It binds that selection to the workload's `gpu_ids`.

The canonical evaluator hashes actual bundle, sharded model, runner, and runtime bytes. Directory digests are computed from the sorted relative file names, byte sizes, and per-file SHA-256 values; symlinks, special files, and empty artifact directories fail closed. Container images must be digest-pinned and match the workload CUDA major. Admission receipts are content-hash checked and require passing device, runtime, model, and restart checks.

The existing model cache stores opaque objects and has no loader provenance binding an object to the verified file set. Engine paths recheck admission around cache retrieval, but this does not prove that cached weights came from those bytes. Keep live activation blocked until the production loader consumes or attests the same immutable artifacts.

## Expected files and dependency tree

- Expected package coverage: `MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/EXPECTED_FILE_LIST.txt`.
- Package integrity: `MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/SHA256SUMS.txt` and `scripts/MRL_verify_product_source_v1.py`.
- Baseline evidence: `docs/evidence/mrl-34/MRL_34_ENGINEERING_EVIDENCE_R01.json`; integration snapshot, byte inventory, package map, and current validation: `docs/evidence/mrl-34/MRL_34_ENGINEERING_EVIDENCE_R02.json`.
- Runtime: existing MRL-44 Deployment Passport output -> host manifest; operator workload and artifact paths -> canonical byte/policy gate -> `GPUOrchestrator.allocate_gpu()` -> exact selected GPU IDs -> revalidate at device selection and before/after model-cache retrieval -> load. Smoke/replay evidence -> owner-reviewed hardware receipt -> internal acceptance matrix. Public support remains a separate decision.

The checkout does not contain a source file identifiable as MRL-44's read-only Deployment Passport collector. The generic Passport registry and APIWorks ledger collector are not hardware collectors and are not substituted for it. The runtime config therefore requires an operator-provided current Passport-derived host manifest and blocks when required current fields are absent. Do not copy historical 539.56/CUDA 12.2 observations into it.

## Review and validation status

The live PR #700 review findings (unused import and local) were corrected. PR #701's unused-import threads were already resolved and outdated at the inspected head. Exact-head Linux/Windows CI for both proposal heads was green when inspected; it did not evaluate this integration change. Hosted MRL Hardware Admission and CodeQL runs for this branch are `action_required` with zero jobs, so no hosted Linux/Windows tests ran on the delivered branch. Local test results and exact run details are recorded in R02.

All acceptance fixtures are explicitly test-only and stored in temporary directories. No live DL580 device query, runtime/model smoke, service restart, or formal hardware receipt was produced. No deployment, driver/CUDA upgrade, service activation, or merge is authorized by this proposal. Owner approval and real-node evidence remain required.
