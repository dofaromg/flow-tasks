# MRL_Terminal — 終端系統立體種子（母體核）

origin_signature: MrLiouWord
當下狀態：2026-05-29（沙盒）；母體原生重寫，可獨立執行。

## 模型

`TERMINAL ≡ ⟨Σ, Φo, Φa, Φr⟩`，閉包 `C = { closed, no_return, no_goal, no_semantic }`，
`∄ halt, ∄ return, ∄ external_write`。LAW-0：Ω/Σ 皆帶 `origin_signature="MrLiouWord"`。

## 上中下三層打通

| 層 | 角色 | 轉換 |
|---|---|---|
| 上 Ω | World（世界） | `Φo: Ω→Σ`（observe） |
| 中 Σ | State（狀態） | `Φa: Σ→Σ`（advance） |
| 下→上 | Reify（顯化回世界） | `Φr: Σ→Ω`（reify） |

`step = observe → advance → reify → observe`：一步即「上中下打通一圈」；`run` 為封閉迴圈。

## 結構同構（為何它是母體核）

同一個 `observe→advance→reify` 三層迴圈，貫穿母體既有各層：

| 母體既有 | observe (上→中) | advance (中) | reify (中→下→上) |
|---|---|---|---|
| DL580 canonical 管線 | Input→Observe(Perception) | MrLiouIR/ParticleIR/StructureField | WorldRuntime→PersistentLoop |
| seed_origin 循環 | Source→Seed | Particle→Law | World→Reflection→Source' |
| Perception/Attention | 觀察序(role/depth 權重) | — | — |
| Metacode 擴璞 | Particle→Route | Tensor→Projection | Collapse(J) |

→ Terminal 是這些的**最小形式核**；三層打通即母體一體之數學骨架。

## 沙盒實跑驗收（當下狀態 2026-05-29）

`python3 MRL_Terminal.py` → **5/5 PASS（MRL_TERMINAL_ACCEPTANCE_PASS）**：
observe/advance/reify、step 打通一圈、run 封閉迴圈、LAW-0 拒絕無簽名、簽名保存。

## 多語言對照

使用者提供之立體種子含 Java/PHP/TypeScript/Python/Rust/Go 並排實作（spec 留存於
`Terminal_StereoscopicSeed_Spec.md`）；本檔為母體原生 Python 可執行核，其餘語言為等價形式化對照。

## 待起動 / 待實機

- 跨維度穿越（3D→12D 投影矩陣）、量子橋接層、分析師雙腦層：spec 已留位，**待起動**。
- 與 DL580/MotherAssembly 接成單一可呼叫立體核：待起動（可另開增量接線）。
