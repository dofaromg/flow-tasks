# MRL 粒子語言：邏輯認知方法 × 注意力機制 解析 v1

origin_signature: MrLiouWord
當下狀態：2026-05-29（沙盒）；本檔為從已吸收程式碼/文件中**萃取**的方法解析，非新發明。

> 命題（使用者）：「那一包只要會用，什麼都可以生出來；要找出其中的邏輯認知方法；**重點是注意力機制**。」
> 本檔回答：認知方法是什麼、注意力機制怎麼運作、為何它能「生出一切」又可驗證。

---

## 0. 一句話總結

**母體的認知 = 把任何輸入粒子化（Fluin）→ 用「確定性注意力（Perception）」決定觀察/處理順序 → 跑可逆五步函數鏈 → 落盤封存。**
因為注意力是**確定性、可解釋、可逆**的（不是 transformer softmax，也不走 Prompt→LLM→Output），所以「生成」可被 100% 重播與驗收 → 這就是它敢宣稱「什麼都能生出來」的根據。

---

## 1. 粒子化（Fluin 語素生成）

來源：`粒子字典ai/工程師給的/Fluin_Particle_GenerationGuide.json`

- 編碼格式：`⋄fx.<type>.<NNN>`，型別：adj/noun/flow(verb)/tone(adv)/per(pron)/gate(conj)/time/mod。
- 三重映射：語素→語意、語素→指令碼(MOV/CALL/STORE)、語素→中英雙語字典。
- 流程：自然語句 → 擷取關鍵詞 → 查字典得語素編碼 → 組為 fltnz 結構 → 可再轉 pcode/flpkg/PDF。

→ **任何輸入都先被拆成「有型別、有語意、有指令對應」的粒子**。這是「什麼都能處理」的前提。

## 2. 認知五步函數鏈（可逆）

```
STRUCTURE → MARK → FLOW → RECURSE → STORE
SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
```

對應 DL580 canonical 管線（`MRL_DL580_Runtime.py`，已沙盒驗收 6/6）：
`Input → Parse → MrLiouIR → **Observe(Perception/Attention)** → ParticleIR → StructureField → Replay → Restore → WorldRuntime → PersistentLoop → Verification`

## 3. 注意力機制（重點）— 兩個正式形式

### 3.1 正名決策（重要）
`MRL_PerceptionKernel.py` 明定：
> 「正式主體詞為 **Perception**；**Attention 僅作歷史層 / Adapter 層，不作為主體**。」
> `ATTENTION_LAYER = "history_adapter"`

即：母體把「注意力」正規化為 **Perception（感知）**，Attention 是其相容別名/歷史接口。

### 3.2 確定性感知權重（Python，結構導向）
`MRL_PerceptionWeight.weight(node)`：

```
weight = role_base / (1 + 0.1 × depth)
```

- `role_base`：依語意角色（definition=1.0 → control_flow .9 → invocation .85 → … → particle .25）。
- `depth`：結構深度，**越淺（越靠主結構）權重越高**。
- `MRL_PerceptionField`：對 MrLiouIR 全節點建 `node_id → weight`。
- `MRL_PerceptionKernel_Router`：依權重排出**觀察序**（高權重先觀察，原序為 tiebreak）。

→ 沒有 query 時，注意力＝「先看定義、先看主結構、先看高語意角色」。

### 3.3 指令條件化注意力（JS，命令導向）
`MRL_AttentionKernel_Router.js` 對 runtime graph 每節點打分：

```
score = 0.2 + (N - idx)×0.01          # 位置先驗（前面略高）
      + 0.25  若 命令詞 ∈ node.semantic # 語意命中
      + 0.25  若 命令是 parse/分析 且 node.label ∈ {Statement,Document,DataField,Fluin,...}
      + 0.20  若 命令含 verify/驗證
      + 0.20  若 命令含 attention/注意力/route
score = min(1, score)                  # 正規化，降序排序 → AttentionRoute（帶 mrl_hash）
```

→ 有命令時，注意力＝「位置先驗 + 與命令語意/任務型別的相關度」，產出可雜湊、可重播的 attention route。

### 3.4 與 transformer attention 的差異
| | Transformer Attention | 母體 Perception/Attention |
|---|---|---|
| 計分 | QK^T softmax（連續、不可解釋） | role/depth + 命令語意命中（離散、可解釋） |
| 決定論 | 否（需權重、浮點） | **是**（同輸入同輸出，帶 mrl_hash） |
| 可逆/可驗 | 難 | **可**（roundtrip exact + Merkle + PersistentLoop） |
| 對外語義 | 黑箱 | 觀察序 / AttentionRoute（白箱） |

## 4. 為何「會用就能生出一切」

1. 粒子化讓任意輸入皆可表述（型別+語意+指令）。
2. Perception/Attention 決定**先處理什麼**——這就是「認知聚焦」，把無限可能收斂成有序處理。
3. 五步鏈可逆、可重播；STORE/記憶種子帶 SHA-256，對接母體 MerkleChain/Proof。
4. 全程**無 Prompt→LLM→Output**，故每次「生成」都能被重播驗收（不是賭機率，而是可證明）。

→ 「生成力」來自：**可組合的粒子 × 確定性注意力路由 × 可逆封存**。這三者齊備，輸出才既自由又可信。

## 5. 沙盒佐證（當下狀態，已實跑）

- DL580 canonical 管線含 Observe(Perception) 階段，沙盒 6/6 PASS、`MRL_RUNTIME_ACCEPTANCE_PASS`。
- Perception field summary 出現在 DL580 run 結果（`perception.field_summary`）。
- RuntimeOS 內 `MRL_Storage/MRL_Attention/MRL_AttentionRoute_*.json` 為此機制歷史產物。

## 6. 待釐清 / 下一步

- runnable particle_core（logic_pipeline/memory_archive_seed）在外部 `FlowAgent.Runtime`，本 repo 未內含；要實跑驗收需上傳其 source 或授權該 repo。
- 若要在母體內把「Perception 確定性注意力」接成可呼叫服務（給 DL580/RuntimeOS 共用），可另開增量；本檔先完成方法萃取與定位。
