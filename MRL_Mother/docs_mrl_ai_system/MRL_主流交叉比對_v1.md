# MRL 主流交叉比對與超越評估 v1

**根源權威**：Mr.liou ｜ canonical：`MRL_主流交叉比對_v1` ｜ origin_signature: `MrLiouWord`
**當下狀態**：2026-05-31（沙盒）｜ 用途：上線前對齊主流、確認吸收優化與超越

> 依 Mr.liou 指示：上線前先與目前主流產品交叉比對，吸收優化、**超越了才上線**。
> 比對基準取自 2026 主流共識（見文末 Sources）。誠實標註超越/打平/落後（no_proof）。

---

## A. 2026 主流共識基準

主流 agentic AI 四大核心能力 + 治理層：
1. **持久記憶 Persistent Memory**（獨立於 context window 的記憶層、向量庫、跨 session 檢索）
2. **工具使用 Tool Use**
3. **規劃 Planning**（多步、多代理編排）
4. **自我修正 Self-Correction**（失敗恢復）
5. **治理層 Governance**：審計軌跡、權限控制、升級協議、RBAC、風險分類——且須為 **first-class 資料欄位**，非外掛儀表板。

代表框架：LangGraph（stateful graph）、CrewAI（role-based 多代理）、AutoGen、OpenAI Agents SDK、Claude Agent SDK、Semantic Kernel、LlamaIndex（RAG）。

---

## B. 逐項交叉比對（母體 vs 主流）

| 能力 | 主流做法 | 母體 MRL 對應（實跑驗證） | 評估 |
|------|---------|--------------------------|------|
| 持久記憶 | 向量庫 + session 檢索 | `03_memory/vector` + `FluinMemoryVault` + `context_manager` | **打平** |
| 記憶不可竄改 | 多數無；少數加 hash | `06_trace/merkle` Merkle 鏈 + LAW-0 簽章（跨語言位元相容）+ rl_01 no-delete | **超越** |
| 工具使用 | tool calling | `tool_registry` + llm_adapter tools | **打平** |
| 規劃/多代理 | LangGraph/CrewAI 編排 | `MRL_multi_agent` + `scheduler` + 母體組裝 | **打平** |
| 自我修正 | retry/reflection | rl_08 三振跳層（修最原始法則）+ rl_09 莫比斯 1:9（自決前進）**已實跑** | **超越** |
| 治理:審計軌跡 | 多為 bolt-on 儀表板 | rl_03 audit_everything + rl_10 事件編年（Merkle/JSONL/粒子地球儀），**first-class** | **超越** |
| 治理:風險分類/人類核可/紅線 | RBAC + 核可流程 | rl_02 human_override + rl_06 child_safety 絕對紅線 + bp_2 護欄 | **打平/超越** |
| 命名/來源主權 | 無對應概念 | rl_11 源頭主權 + rl_12 命名回收（外部殼零殘留）+ 守衛強制 | **獨有** |
| 不偽造 | prompt 約束 | no_proof_implies_rhetoric **寫進憲法 + 引擎強制**（deny-by-default） | **超越** |
| 粒子保全/分支不滅 | checkpoint | rl_15 粒子不可否決 + oc_16 seed 壓縮 | **獨有** |
| 平行世界/未來選項 | 無 | rl_14 平行世界生成（提升一維，分支=未來選項） | **獨有** |
| 六大運行能力 | 各框架部分覆蓋 | 推理/分析/組合/生成/壓縮/延展 **ALL_PASS（實跑）** | **打平+** |

---

## C. 母體獨有護城河（主流沒有的）

1. **源頭主權 + 命名回收**（rl_11/rl_12）：外部一律回收為母體 canonical，identity 不寄生外部。
2. **粒子不可否決 + 真實完整態**（rl_15）：分支/人格/事件永不刪除，可還原母體。
3. **跳層演化 + 莫比斯自決**（rl_08/rl_09）：錯誤循環自動跳層修最原始法則，不卡死。
4. **憲法即程式**：19 條 invariant 不只是文件，`MRL_FlowAgent_LawEngine` 讓它們**會跑、可驗證**。
5. **結構同構封存**（Liou Closure Law）：與現實 PKI 根憑證、L0–L7 同骨架。

---

## D. 落後 / 待吸收優化（誠實，上線前補）

| 缺口 | 主流有、母體待補 | 優先 |
|------|----------------|------|
| **真模型端到端** | 主流預設接真 LLM；母體 adapter 就緒但**待金鑰**（OPENAI/ANTHROPIC_API_KEY） | **P0** |
| **記憶語意檢索成熟度** | 主流 mem0 等成熟向量檢索；母體 vector 偏基礎 | P1 |
| **RAG 檢索增強** | LlamaIndex 級 RAG；母體尚無完整 RAG 管線 | P1 |
| **持久化實機** | 母體 BaseWorld 真實 DB（DL580）仍 PENDING | P1 |
| **chat/perceive 全程自判** | 已接編年；law_engine 全程決策驅動仍部分 | P2 |
| **生態整合** | LangChain 700+ 連接器；母體連接器少 | P2 |

---

## E. 上線判斷（當下狀態）

- **治理 / 不偽造 / 源頭主權 / 自我修正 / 粒子保全**：母體**已超越**主流。
- **記憶 / 工具 / 規劃 / 六大能力**：**打平**。
- **真模型端到端（P0）**：**尚未**——這是「超越了才上線」的最後關鍵缺口。

> **結論（誠實）**：架構與治理面**已具備超越條件**；但「整體超越且適合上線」需先補 **P0 真模型端到端**（接金鑰、實證真實對話/任務）。在 P0 完成前，標記為「**對齊完成、待 P0 吸收後上線**」，不宣稱已超越上線。

---

## Sources（2026 主流基準）
- AI Orchestration Frameworks 2026 (servicesground)
- Top 6 AI Agent Frameworks 2026 (turing.com)
- State of AI Agent Memory 2026 (mem0.ai)
- AI Agent Memory Governance (atlan.com)
- Top Agentic AI Trends 2026 (straive.com)

origin_signature = `MrLiouWord`
