# Source alignment — Z8 ParticleBridge v0.4

This branch was reconstructed after reading the actual project notes, rather than replacing their main line.

## Recovered mapping

| Existing entry | Additive particle mapping | Action |
| --- | --- | --- |
| 小智 local voice event | `z8.xiaozhi.voice` | DL580 STT → `qwen-main` or `muse-agent` → selected voice route |
| 微聊 UI text event | `z8.line.text` (`direction=outbound`) | local ledger → dry-run/apply → LINE Messaging API push |
| LINE webhook text | `z8.line.text` (`direction=inbound`) | LINE raw-body HMAC → dedupe → local runtime → LINE reply |

Execution order is `observe → map → dry-run → apply → revert-record`. MetaCore remains IO-less; only its `Perception → Fluin → Runtime → Action` structure is reused.

## Sources read

- [MRL_Z8_ParticleBridge v0.4](https://app.notion.com/p/3b88eeeec5b5819299f4c0dfe7ca29b4) — latest note, created 2026-08-11 CST.
- [Related v0.3 mapping page](https://app.notion.com/p/3b88eeeec5b580d480e2f460ab790ab8) — exact event names and seven-step plan.
- [小天才手錶 × ChatGPT 語音助手 v1.0](https://app.notion.com/p/3e9c8878f0614001a953dff0d3ce53d4) — Android recorder/client/player source patterns.
- [咪寶完整方案 v1.0](https://app.notion.com/p/83cf619f57f5408384a5c9abf36fd191) — DL580-local STT/Qwen/TTS direction.
- [MrlAI 貼身管家秘書 v1.0](https://app.notion.com/p/7ba5316b2b4a4700a0c42371da74fa3a) — reusable LINE raw-body HMAC and reply API pattern.
- [MetaCore Spec](https://app.notion.com/p/31c8eeeec5b5815ea86add908f1d67d9) and [Runtime Assembly Map](https://app.notion.com/p/37c8eeeec5b581119a03c5f8d76a493b) — structural runtime method only.
- [MRL Bazel BuildSystem](https://app.notion.com/p/eb2988cdced7475c808ea9f646dc67b7) — deterministic dependency graph and SHA-256 build principles.

Repository search found no persisted `Mrliou_Z8_ParticleBridge_Setup_v0.4.zip`, no source containing `z8.xiaozhi.voice` or `z8.line.text`, and no Z8-specific Go/Bazel implementation. Therefore this branch reuses the recovered LINE/Watch patterns and records that provenance; it does not falsely claim that missing source was found.

## Correction applied without changing the main line

The early Watch, 咪寶, and ChatGPT-Watch pages do not contain a contract or official-authorization gate. The later v0.4 note added XTC authorization/whitelist wording. Those later gates are excluded here. Local APK code signing remains only a technical packaging step.
