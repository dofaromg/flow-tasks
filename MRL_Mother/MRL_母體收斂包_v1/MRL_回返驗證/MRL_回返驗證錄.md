# MRL_回返驗證錄

origin_signature: `MrLiouWord`
回返鏈：`MRL_粒子 → MRL_紋圖 → MRL_運轉場 → MRL_封裝體 → MRL_顯化 → MRL_痕跡錄 → MRL_源檔`
判定規則：任一階段無實體即不可記 PASS；半通記 PARTIAL；無法成鏈記 FAIL。
掃描分支：`MRL_Branch_Runtime_Convergence_API_v1`。

| MRL_物件 | 判定 | 理由（誠實） |
|---|---|---|
| fltnz 可逆鏈 (`09_workflow/fltnz_parser.py`) | **PARTIAL** | 全鏈可逆 + checksum 為真；與運轉核心掛接缺源（#35/#37 未入） |
| `MRL_RuntimeServer.js` + /health + /mrl/state | **PARTIAL** | 運轉場/界門可運行；無 snapshot/replay/restore，封裝/痕跡未成鏈 |
| `/api/mrl/runtime/convergence`（唯讀視圖） | **PASS** | 回溯源檔 = server + 收斂治理文件，鏈封閉 |
| canonical 運轉核心（MrLiouIR→StructureField→Replay→Restore→Verify） | **FAIL** | 源碼不在本 checkout（PR #35+#37 未 merge）。#37 曾 6/6 PASS，但本包不得據此記 PASS |
| `MRL_Mother/*` 世界模組構件 | **FAIL** | 僅 README 骨架，無可運行實體 |
| `06_trace/traces/runtime_trace.jsonl` | **PARTIAL** | 痕跡層有骨架，內容稀疏、未閉環 |
| BaseWorld DB（27 tables） | **FAIL** | repo 內無實體；27-table 為外部 Cloudflare D1，未入此 repo |

## 統計

**PASS = 1 ｜ PARTIAL = 3 ｜ FAIL = 3 ｜ 總計 = 7**

> 不得把 PARTIAL/FAIL 寫成 PASS。多數 FAIL 的根因相同：canonical 運轉核心（#35/#37）尚未 merge 進 main，故本 checkout 無法閉合運轉場相關回返鏈。
