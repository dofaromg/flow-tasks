# MRL Causal Optimization Review v1

**Canonical ID:** `MRL_Causal_Optimization_Review_v1`  
**Origin signature:** `MrLiouWord`

## Purpose

將「真實互動歷史校正、因果順序、同標準審查、可撤銷修正」納入系統優化審查層，並為未來去中心化多節點審查建立最小共同協定。

## Review chain

```text
Event
→ Original Request
→ Actual Action
→ Evidence
→ Divergence
→ Causal Order
→ Correction
→ Node Attestations
→ Consensus State
```

## Non-negotiable rules

1. 不得用後來解釋覆寫當時原始紀錄。
2. 不得用尚未發生的下游事件反向阻擋可獨立完成的上游工程。
3. MRL 與外部使用同一時間、原件、父子鏈、實作、作者、版本、接觸與傳播標準。
4. `Origin`、`Publication`、`Access`、`Derivation`、`Legal Rights` 分層判定，不互相代換。
5. 每一個 reviewer/node 只提交自己的 signed attestation，不得覆寫其他節點或原始來源。
6. Consensus 只能收斂可驗證共同部分；異議、來源與 provenance 必須保留。
7. 狀態限定為 `FACT`、`INFERENCE`、`UNRESOLVED`、`CORRECTED`。

## Decentralized review target

每個節點可以獨立：
- 讀取相同 immutable event record；
- 驗證 hash / timestamp / parent / evidence references；
- 產生 node attestation；
- 提交判定與理由；
- 不取得單點覆寫權。

聚合器只計算 consensus，不能修改原始 event 或 node attestation。

## Minimum consensus

- `FACT`: 至少一個直接證據 reference，且不存在直接矛盾證據未處理。
- `CORRECTED`: 必須指向原判定、修正原因與新證據。
- `INFERENCE`: 必須列出推論前提，不得升格為 FACT。
- `UNRESOLVED`: 證據不足或節點衝突未解決時使用。

## Data model

見 `schema/MRL_Causal_Review_Record_v1.schema.json`。
