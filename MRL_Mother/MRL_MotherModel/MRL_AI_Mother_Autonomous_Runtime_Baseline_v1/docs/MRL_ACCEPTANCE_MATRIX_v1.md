# MRL AI Mother Autonomous Runtime Acceptance Matrix v1

| Gate | GitHub package test | User-hardware live acceptance |
|---|---|---|
| Expected file coverage | Required | Inherited |
| SHA-256 package integrity | Required | Recheck after transfer |
| Reject external model host | Required | Required |
| Local-model health | Fake loopback integration server | Real Ollama/llama.cpp model |
| Local inference | Protocol contract | Real model output |
| Memory input/output persistence | Required | Required |
| Memory tamper detection | Required | Required |
| Evidence PASS/FAIL record | Required | Required |
| Passport issuance | Required | Required |
| Passport version chain | Required | Required |
| Return Anchor | Required | Required |
| Recall after request | Required | Required |
| Process restart persistence | Code path present | Required follow-up test |
| External API disconnected | Static Gate | Network-isolated run required |
| Hardware utilization | Not available in CI | Optional performance baseline |
| Model release manifest | Schema validation | Model artifact must match manifest `sha256` |
| Return requires explicit consent | Required | Required |
| Return manifest coverage/SHA-256 | Required | Recheck before submission |
| Background upload disabled | Required | Required |
| Provider receiving endpoint | Out of scope | `RECEIVER_GATE_OPEN` |
| APIWorks public exposure | Out of scope | Blocked until auth/privacy/payment Gate |

## Gate meanings

- `DELIVERY_PASS`: all expected source, schema, script, documentation and evidence files exist; checksums match; automated tests pass.
- `AUTONOMY_GATE_OPEN`: GitHub package is valid, but no real-model acceptance evidence has been captured for a particular user-hardware installation.
- `MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS`: a real supplied MRL model completed inference, Memory, Evidence, Passport and Recall on user-controlled hardware without an external model API.
- `RECEIVER_GATE_OPEN`: local return-bundle creation is implemented, but the authenticated provider receiving API, retention and deletion workflow are not yet released.

## Required live evidence

The live acceptance record must preserve:

1. final Git commit SHA;
2. machine/runtime identity;
3. local backend and model identity;
4. local endpoint and listening process;
5. relevant hardware/runtime inventory;
6. `/health` response;
7. inference request/result hashes;
8. MemoryVault chain head;
9. Evidence Ledger chain head;
10. Passport hash and Return Anchor;
11. external-model-disconnected observation;
12. acceptance timestamp and operator.

No stub response, mock-server response or historical machine record can replace live evidence from the specific installation being accepted.

## 繁體中文驗收摘要

每一台使用者硬體都必須以該次安裝的真實模型重新驗收。模型檔案的實際 SHA-256 必須等於 `MRL_Model_Release_v1.sha256`；不得以 stub、mock server 或其他機器的歷史紀錄代替。驗收紀錄必須同時封存 Git Head、硬體／Runtime 身分、Memory 與 Evidence 鏈頭、Passport hash、外部模型斷線觀察及操作時間。

Example live-acceptance evidence record／真實驗收證據範例：

```json
{
  "schema": "MRL_AI_Mother_Live_Acceptance_v1",
  "git_head": "<verified-commit-sha>",
  "hardware_id": "MRL_hardware_01",
  "runtime": "ollama",
  "model_release_id": "MRL_model_release_01",
  "model_sha256_verified": true,
  "health_ready": true,
  "memory_chain_head": "<sha256>",
  "evidence_chain_head": "<sha256>",
  "passport_hash": "<sha256>",
  "external_model_disconnected": true,
  "accepted_at": "2026-08-28T00:00:00Z",
  "operator": "<operator-id>"
}
```
