# MRL Runtime Recovery Checklist v1

origin_signature = `MrLiouWord`

圖例（誠實標記;`unverified != completed`）：
- `[x]` = 存在於 repo 且本地驗收通過（PIDScope A–F）
- `[~]` = 部分 / skeleton / 僅 endpoint
- `[ ]` = 尚未存在（target）

## Runtime Core
- [ ] MRL_UniversalParser_Core
- [ ] MRL_MrLiouIR (compiler/engine；目前僅 label)
- [ ] MRL_ParticleIR (engine)
- [x] MRL_RuntimeStructureField（canonical;PIDScope 結構場,A/B/D PASS,local）
- [~] MRL_Perception（僅 `/mrl/perceive` endpoint;無 Perception_Core 模組）
- [ ] MRL_WorldRuntime

## Memory Layer
- [x] Replay（registry replay exact,C PASS,local）
- [x] Restore（recovery checkpoint/restore,B PASS,local）
- [~] Verify（scope isolation D PASS = 一種驗證;完整 verify chain = target）
- [x] Trace（registry.trace,local）
- [ ] Merkle（durable）
- [ ] Provenance（durable）

## Product Layer
- [ ] WebConsole
- [~] Runtime API（僅 RuntimeServer health/state/perceive/convergence）
- [ ] Artifact UI
- [ ] Streaming
- [ ] Multi-session
- [ ] Auth

## Reconstruction Layer
- [ ] COLMAP Adapter
- [ ] OpenMVS Adapter
- [ ] Mesh Runtime
- [ ] Perception Fusion（歷史名 Attention Fusion）
- [ ] Context Graph → Context StructureField

## Runtime Persistence
- [x] Snapshot（checkpoint,local）
- [ ] Runtime Resume（durable / 跨 session）
- [x] Runtime Recovery（B PASS,local）
- [x] Runtime Replay（C PASS,local）
- [~] Runtime Verification（scope isolation local;full chain = target）
- [ ] DL580 reboot survival

## Acceptance
PASS condition：
- runtime loop alive
- replay exact
- restore exact
- verify exact
- provenance valid

FAIL condition：
- skeleton only
- no persistence
- no replay
- unverifiable runtime

目前狀態：PIDScope Ownership 層 A–F local PASS;durable / reboot-survival / product / reconstruction 層 = target,未驗證不計完成。
