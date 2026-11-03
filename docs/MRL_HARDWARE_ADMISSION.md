# MRL-34 Hardware Admission v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
Task: https://linear.app/dofaromgg/issue/MRL-34

## Existing lineage and scope

Base: `608b66e0db23e7cc4eef21ea752668ac800620b3` (`main`). Extend
`utils/gpu_orchestrator.py`; preserve `configs/gpu_allocation.yaml` and its
six-card allocation. Main tree and open PRs were inspected: the existing module
allocates GPUs but contains no deployment compatibility gate. Branch enumeration
found no named hardware-admission implementation; this does not claim exhaustive
inspection of every historical branch. No live DL580 probe was performed here.

`docs/HARDWARE_SETUP.md` is historical generic setup guidance, including CUDA
11.8 examples. It is not an admission allowlist or an instruction to upgrade the
DL580. The owner's 2026-10-22 Windows/539.56/CUDA 12.2 observation is preserved in
the new matrix with incomplete evidence status. Runtime ABI, runner version,
quantization, model hash, package hash and full acceptance receipt are absent.
No production combination is promoted to verified by this change.

## Interfaces and dependency tree

- `configs/MRL_hardware_manifest_v1.schema.json`: complete manifest interchange.
- `configs/MRL_hardware_matrix_v1.json`: reviewed policy, historical observations,
  internal verified combinations, and separate `public_support` declarations.
- `utils/mrl_hardware_admission.py`: dependency-free Python 3.10+ evaluator and CLI.
- `utils/gpu_orchestrator.py::allocate_admitted_gpu`: calls evaluator, compares
  SKU/CC/VRAM against selected torch device properties, returns only configured
  GPU IDs. It rejects missing devices and mixed track/package allocations.
- `tests/test_mrl_hardware_admission.py`: synthetic acceptance/denial regressions.
- `.github/workflows/MRL_hardware_admission.yml`: Linux/Windows, Python 3.10/3.12.

Manifest -> exact reviewed matrix row -> SHA-256-bound local acceptance receipt.
Orchestrator -> admission -> observed GPU comparison -> selected IDs.
CI -> tests + production matrix validation. No GPU installation is needed in CI.
The workflow uses non-cone sparse checkout because the historical root filename
`:mnt:data.txt` cannot be materialized on Windows. Only the required hardware
modules, policy and tests are checked out; original names remain untouched.

Every manifest field is mandatory, including nullable CUDA/ROCm. NVIDIA requires
CUDA and null ROCm; AMD requires ROCm and null CUDA. Unknown vendors and missing
or unrecognized values deny. No version ranges or driver minimums are inferred:
only the complete, exact tested driver/OS/runtime ABI/runner/quantization/model
and bundle combination can pass. VRAM is actual integer MiB from the device,
not the nominal marketing capacity or the sum across six cards.

Volta, V100 SKU, or NVIDIA CC 7.0 independently activate the V100 policy. Identity
must agree on NVIDIA/Volta/7.0/dl580-v100; CUDA must be 12.x. TensorRT runners are
conservatively denied in this v1. CUDA 13/vLLM-Omni CUDA 13 cannot be admitted even
if accidentally added to an allowlist. CUDA 12.x alone does not imply runtime
compatibility. NVIDIA documents removal of Volta offline compilation/library
support in CUDA 13:
https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/

Modern NVIDIA and AMD/ROCm combinations need their own exact hardware acceptance.
Track-separated bundle IDs, bundle digests, acceptance IDs and receipt digests
are enforced across the reviewed matrix. No modern GPU is publicly supported by
this initial empty registry. `public_support` is informational only and cannot
authorize admission; an internal acceptance does not publish support.

## Run the gate

Run from the repository root (works on Windows and Linux):

```bash
python -m utils.mrl_hardware_admission --validate-matrix
python -m utils.mrl_hardware_admission --manifest /path/to/observed-manifest.json
python -m unittest discover -s tests -p test_mrl_hardware_admission.py -v
```

The manifest's exact fields and types are in the schema. Exit 0 means admitted;
exit 2 means denied, malformed input or unavailable evidence. Deployment callers
must check the exit status and stop before loading a model/container. Matrix
validation exit 0 only validates policy structure; `verified_count: 0` means no
combination is admitted. A successful policy test is never a hardware acceptance.

New Python deployment integrations use:

```python
ids = orchestrator.allocate_admitted_gpu(engine_name, trusted_device_manifests)
# Only load the previously hash-verified bundle onto these IDs after admission.
```

Existing `allocate_gpu` remains a legacy allocation API to avoid silently changing
the running mother environment. Its existing callers in `ultimate_engines/` do
not enforce this new gate. Activating the gate for those services is a separate
owner-approved deployment step. Admission assumes trusted inventory and reviewed
policy; it is not remote hardware attestation. The caller must verify the actual
bundle/model bytes against their manifest digests and prevent substitution after
the check. Device checks in the orchestrator verify SKU/CC/VRAM, not the entire
runtime installation. A tenant cannot choose the policy file or supply receipts.

## Smoke test and acceptance procedure (requires approved live execution)

1. Before any new deployment, retain the currently running bundle and its digest,
   service configuration, six GPU assignments and previous acceptance. Record a
   new version; never rewrite the historical observation or previous receipt.
2. Read `nvidia-smi --query-gpu=index,name,driver_version,memory.total,compute_cap
   --format=csv,noheader` for all six devices. An unsupported query field is an
   evidence gap, not a pass. Record OS build. Distinguish the `nvidia-smi` maximum
   CUDA capability from the toolkit and runtime's actually loaded CUDA libraries.
3. Read the exact installed runtime version, CUDA/ROCm build, supported SM targets,
   Python/platform ABI and compiled extension ABI from the selected environment.
   Record model runner version, quantization and SHA-256 of model and bundle.
   Build a complete manifest per GPU; do not fill unknown fields with guesses.
4. On an isolated approved CUDA 12.x candidate environment, run deviceQuery and a
   synchronized tensor operation on each selected GPU. Run the actual model using
   the chosen runner/quantization and verify a known deterministic request against
   the recorded expected output/tolerance. Capture command, stdout/stderr, exit
   code, environment identity and artifacts. No real model smoke was run here.
5. Create an immutable JSON receipt under `configs/MRL_hardware_evidence/` with
   `origin_signature`, `status: hardware_verified`, complete `manifest`, unique
   `acceptance_id`, `observed_at`, `source` (original raw evidence location), and
   `checks` containing exactly `device_query`, `runtime_smoke`, `model_smoke`, all
   boolean true only when the corresponding real checks pass. Preserve full raw
   evidence in the owner's system. Tests generate synthetic receipts only in a
   temporary directory; those must never be copied into the production registry.
6. In an owner-reviewed change append a `verified_combinations` row with the exact
   `manifest` and `acceptance: {id, path, digest}`. Path is relative to the matrix
   directory; digest is `sha256:` plus the receipt file's 64-character SHA-256.
   The receipt repeats the manifest and acceptance ID and is checked byte-for-byte
   by digest and by content. Verify package/model bytes separately before launch.
7. Run gate, then the approved deployment's smoke again. Publish external support
   only by a separate explicit `public_support` decision; keep internal tests and
   public claims separate. Modern GPU bundles require distinct acceptance records.

## Rollback

On any denied gate or failed smoke, stop the candidate before service activation.
Keep the current DL580 services and driver untouched. If an approved deployment
was activated and then fails, stop only that candidate, restore the previously
recorded bundle/service configuration and GPU assignments, recheck original
hashes, and run its previous acceptance smoke. Append a rollback event with old
and new digests plus evidence; never delete or relabel a failed receipt. Driver
and CUDA upgrades, service changes and formal merge require Mr.liou approval.
This PR performs none of those operations.

## Remaining gates

Live full-stack DL580 receipt and complete inventory are still required before
any production allowlist row. Synthetic CUDA 12.x acceptance tests demonstrate
the gate logic only. Existing engine startup migration, caller-side byte hashing
and actual deployment verification remain explicit integration work, not claims
of completed mother acceptance. GitHub CI results must be read at the PR exact
head; local test success does not establish hosted CI success.
