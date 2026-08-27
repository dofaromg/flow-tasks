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
| Model release manifest | Schema validation | Receipt hash must match |
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
