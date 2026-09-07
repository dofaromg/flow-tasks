# MRL 功能模組產品重建規格 v1

## 主權與材料邊界

- 母體主權威帳號：`dofaromg`
- 產品來源識別：`origin: mrl`
- ChatGPT、Claude、Copilot、GitHub、CI 與歷史封存均不得自行成為產品權威。
- 歷史檔案只提供術語、候選公式、範例、架構線索及證據。
- 重建產品必須重新定義介面、移除隨機性、建立測試及留下來源映射。
- 未獲 `dofaromg` 核准前，所有產品保持 `candidate`，不得宣告正式建構或發布。

## Product 01 — MRL MetaCode Core

### 核心介面

```text
Particle(name, type, weight, origin)
ParticleSet(particles)
Route(particle, field)
Tensor(particles, rhythm, persona)
DimensionProjection(tensor, dimension)
Collapse(structure, target, stability_evidence)
```

### 強制條件

- 所有實體攜帶 `origin: mrl`。
- 名稱不得由無來源隨機函式直接產生。
- Collapse 必須提供穩定條件及輸入證據，不能只由模型宣告完成。
- 同一輸入、同一版本及同一政策必須產生相同輸出。

## Product 02 — MRL Authority Core

### 核心介面

```text
record_material(source, hash, classification)
validate_candidate(record)
promote_candidate(record, approver=dofaromg)
release_product(manifest, approver=dofaromg)
verify_lineage(product_id)
```

### 權威規則

- `dofaromg` 是唯一母體主權威帳號。
- GitHub commit 是版本證據，不是語義權威。
- CI 通過是測試證據，不是產品採納權。
- 外部模型輸出最高只能先成為候選材料。

## Product 03 — MRL Relay IR

### 統一記錄

```json
{
  "record_id": "mrl.relay.record.<deterministic-id>",
  "origin": "mrl",
  "source": {
    "provider": "chatgpt|claude|copilot|flowagent|archive",
    "source_reference": "",
    "source_hash": "sha256:"
  },
  "requested_scope": [],
  "claims": [],
  "artifacts": [],
  "verification": {
    "status": "pending",
    "evidence": []
  },
  "authority_level": "L0",
  "canonical_status": "not_adopted"
}
```

### 轉驛原則

- 只轉譯，不覆蓋來源。
- 保留原始輸入及其 hash。
- 不把模型名稱、Session 或平台狀態當作 MRL 身分。
- 支援雙向 Adapter，但任何輸出都要重新經過 Authority Core。

## Product 04 — MRL Deterministic Knowledge Engine

### 重建要求

原始知識引擎候選中的隨機 persona 與 resonance 必須移除，改為：

```text
features = deterministic_extract(input, extractor_version)
persona = classify(features, persona_policy_version)
resonance = score(features, documented_formula)
analysis_id = sha256(canonical_input + policy_versions)
```

### 儲存層

- D1：索引與結構化分析結果。
- R2：完整不可變封包。
- Vector index：衍生搜尋索引，不能取代原始證據。
- Event ledger：記錄分析建立、更新與採納事件。

## Product 05 — MRL Event Ledger

### 最小事件格式

```json
{
  "event_id": "mrl.event.<deterministic-id>",
  "origin": "mrl",
  "source": "mobile|github|relay|local",
  "type": "capture|decision|sync|promotion|release",
  "payload_hash": "sha256:",
  "previous_event_hash": "sha256:",
  "timestamp": "RFC3339",
  "authority_account": "dofaromg"
}
```

### 特性

- append-only
- 可回放
- 可驗證
- 重跑不重複
- payload 與索引分離
- 歷史不覆寫，只能追加更正事件

## 建構閘門

每一項產品進入可建構狀態前必須滿足：

1. 所有來源材料已列入 Material Registry。
2. 有明確的來源到產品映射。
3. 隨機演算法已移除或被固定種子及版本化公式取代。
4. 輸出具備可重播性。
5. 產品 Schema、測試和 Manifest 完整。
6. `dofaromg` 明確核准。

目前這五項均為候選產品定義，尚未宣告完成實作或正式發布。
