# MRL AI Mother Autonomous Runtime Acceptance Matrix v1

| Gate | GitHub package test | DL580 live acceptance |
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
| GPU utilization | Not available in CI | Required for performance baseline |
| APIWorks public exposure | Out of scope | Blocked until auth/privacy/payment Gate |

## Gate meanings

- `DELIVERY_PASS`: all expected source, schema, script, documentation and evidence files exist; checksums match; automated tests pass.
- `AUTONOMY_GATE_OPEN`: GitHub package is valid, but no real DL580 local-model acceptance evidence has been captured.
- `MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS`: a real local model completed inference, Memory, Evidence, Passport and Recall on DL580 without an external model API.

## Required live evidence

The live acceptance record must preserve:

1. final Git commit SHA;
2. machine/runtime identity;
3. local backend and model identity;
4. local endpoint and listening process;
5. GPU inventory and utilization snapshot;
6. `/health` response;
7. inference request/result hashes;
8. MemoryVault chain head;
9. Evidence Ledger chain head;
10. Passport hash and Return Anchor;
11. external-model-disconnected observation;
12. acceptance timestamp and operator.

No stub response, mock-server response or historical DL580 record can replace this live evidence.

