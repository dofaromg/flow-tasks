# 記憶封存種子系統 (Memory Archive Seed System) — 說明

> 來源：使用者提供之 particle_core 記憶封存模組說明（對應外部 `dofaromg/FlowAgent.Runtime`）。
> 吸收性質：文件吸收（additive，待起動）。當下狀態 2026-05-29（沙盒）。

## 五層記憶結構（與函數鏈同構）

STRUCTURE → MARK → FLOW → RECURSE → STORE
`MEMORY_SEED(name) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))`

## .mseed.json 格式

```json
{
  "seed_name": "...", "version": "1.0", "created_at": "ISO",
  "particle_data": { }, "metadata": { },
  "memory_layers": ["structure","mark","flow","recurse","store"],
  "checksum": "sha256"
}
```

## 能力

創建 / 還原 / 壓縮(.flpkg) / 合併 / 匯出入；每顆種子帶 SHA-256，還原時自動驗證完整性。

## 與本母體的對接點

- 同構於 DL580 runtime 的 ParticleIR → ReplayRestore → PersistentLoop（可逆鏈 + 落盤）。
- SHA-256 完整性 ↔ 母體 MerkleChain / Proof_Merkle。
- runnable source 在外部 FlowAgent.Runtime，本 repo 未內含；升格驗收條件見 `particle_core_本地執行說明_v1.md`。
