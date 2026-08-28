# MRL AI Mother Autonomous Runtime Baseline v1

**Canonical ID:** `MRL_AI_Mother_Autonomous_Runtime_Baseline_v1`  
**Origin signature:** `MrLiouWord`  
**Position:** `MRL_Mother/MRL_MotherModel` additive child package  
**Purpose:** establish the first executable local-model → memory → passport → evidence → APIWorks loop without requiring an external model API.

## What this package adds

The existing `MRL_MotherModel_v0_1` preserves evidence, module registries and additive recovery state. This package does not replace it. It adds an executable autonomous runtime beneath that existing mother model:

1. **Local model Gate** — accepts Ollama or llama.cpp on loopback only.
2. **MemoryVault** — persists user and model events in an append-only SHA-256 chain.
3. **Evidence Ledger** — records inference PASS/FAIL and the exact memory hashes involved.
4. **Universal Passport** — issues additive, versioned passports retaining source identity and Return Anchor.
5. **APIWorks Gateway** — exposes health, mother-run and audited memory-recall endpoints.
6. **Acceptance Gate** — refuses to count a stub or external model endpoint as autonomous inference.
7. **BYOH delivery boundary** — GitHub delivers the construction package; the user runs it on hardware they control.
8. **Explicit return bundle** — packages only user-selected files with consent, purpose, coverage and SHA-256 evidence; it never uploads automatically.

## Honest completion boundary

`DELIVERY_PASS` means the GitHub package is present, non-empty, checksummed and its loopback integration tests pass. It does **not** mean a real model has been accepted on every user hardware environment.

`MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS` requires a real supplied MRL model to run on the user's own hardware and the PowerShell acceptance flow to pass. No specific server, GPU or cloud is canonical.

## Quick start on user-owned hardware

1. Copy the example configuration and set the exact installed local model name.
2. Start Ollama or llama.cpp locally.
3. Start the MRL gateway:

```powershell
cd MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts
.\MRL_start_runtime_v1.ps1
```

The launcher stores mutable Memory, Evidence and Passport data in the sibling
`MRL_AI_Mother_Runtime_Data` directory, outside this checksummed package.

4. In a second PowerShell window, run:

```powershell
cd MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts
.\MRL_acceptance_v1.ps1
```

## APIWorks baseline surface

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Local model, memory and evidence Gate state |
| `POST` | `/v1/mother/run` | Local inference plus memory, Evidence and Passport issuance |
| `GET` | `/v1/memory/recall` | Audited world/session replay |

Example request:

```json
{
  "prompt": "Recall the MRL source-to-product law.",
  "world_id": "MRL_main",
  "session_id": "MRL_session_example"
}
```

No API key, model weight or production secret belongs in this package.

## Model delivery and file return

MRL publishes model artifacts separately with an `MRL_Model_Release_v1` manifest containing the model identity, version, supported runtime, size and SHA-256. The user verifies that receipt before local loading.

Local data stays local by default. To prepare files for voluntary return:

```powershell
.\MRL_prepare_return_bundle_v1.ps1 `
  -Files "..\..\MRL_AI_Mother_Runtime_Data\memory.jsonl" `
  -Purpose "support evidence" `
  -HardwareId "MRL_user_hardware_01" `
  -ModelReleaseId "MRL_model_release_01" `
  -Consent
```

This creates a checksummed ZIP; it does not transmit it. See [BYOH and Data Return Contract](docs/MRL_BYOH_DATA_RETURN_CONTRACT_v1.md) and [Commercial Agreement Structure](docs/MRL_COMMERCIAL_SERVICES_AGREEMENT_BLUEPRINT_v1.md).

## Verification

```powershell
python scripts\MRL_verify_package_v1.py
python -m unittest discover -s tests -v
```

See [Architecture](docs/MRL_ARCHITECTURE_v1.md) and [Acceptance](docs/MRL_ACCEPTANCE_MATRIX_v1.md).
