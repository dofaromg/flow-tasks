# MRL_母體收斂總報告_v1

origin_signature: `MrLiouWord`
掃描分支：`MRL_Branch_Runtime_Convergence_API_v1`（≈ main + 收斂界門）
掃描根目錄：`/home/user/MRL_AI_SYSTEM`
檔案總數：**170**（排除 `.git` / `node_modules` / `__pycache__` / `*.pyc` / 本收斂包）
帶 `MrLiouWord` 簽名檔：**115** ｜ 封裝檔：**0**

---

## 1. MRL_已確認存在

母體骨架（本 checkout 實體存在）：

- **MRL_源場**：`00_rootlaw/`、`02_principles/`
- **MRL_原種層**：`01_schema/`、`05_persona/`、`MRL_Mother/`（多為 README 骨架）
- **MRL_粒子海層**：`MRL_Symbolic/`、`09_workflow/fltnz_parser.py`（真實可逆鏈）
- **MRL_流域結構層**：`09_workflow/`（45 個運作碼）、`04_runtime/`、`MRL_Runtime/`、`MRL_RuntimeServer.js`
- **MRL_界門**：`MRL_RuntimeServer.js` 之 `/health`、`/mrl/state`、`/mrl/perceive`、`/api/mrl/runtime/convergence`（唯讀，PR #39 已 merge）
- **MRL_交界層**：`07_ingest/`、`08_sources/`、`MRL_Adapters/`、`.github/`
- **MRL_雲映層**：`deploy/`（cloudflared → bridge.mrliouhan.ai、tailscale、docker、systemd）
- **MRL_自述層**：`docs/`、`README.md`、`package.json`
- **MRL_痕跡層**：`06_trace/`
- **MRL_回返層**：`tests/`、`scripts/MRL_acceptance_check.js`
- **主線 main 另含**：`#36 PIDScope`（MRL_Workflow ownership, Node）、`#38 收斂治理文件`、`#39 收斂界門`

---

## 2. MRL_分層結果

詳見 `MRL_母體分層/MRL_母體分層圖.md`。摘要：

- 已有實體：源場、原種層、粒子海層、交界層、自述層、封裝層、痕跡層、回返層、雲映層（部署層）。
- 部分 / 需補線：流域結構層（canonical 運轉核心未入）、地映層（僅 streamlit）。
- 無實體 / 需補線：無限環層（僅概念）、拓樸潮層、立體粒界層（3D）。

---

## 3. MRL_回返鏈

詳見 `MRL_回返驗證/MRL_回返驗證錄.md`。

**PASS = 1 ｜ PARTIAL = 3 ｜ FAIL = 3 ｜ 總計 = 7**

- PASS：`/api/mrl/runtime/convergence`（唯讀視圖，鏈封閉）
- PARTIAL：fltnz 可逆鏈、`MRL_RuntimeServer.js`、`06_trace` 痕跡
- FAIL：canonical 運轉核心（#35/#37 未入）、`MRL_Mother/*`（骨架）、BaseWorld 27-table（外部）

---

## 4. MRL_命名替換結果

詳見 `MRL_命名對照/MRL_正名表.md`（27 條一般正名）+ canonical 硬校正：

- `MetaIR → MRL_MrLiouIR`、`RuntimeGraph/Graph → MRL_RuntimeStructureField`、`Attention → MRL_Perception`（已於 PR #37 實作，舊名降為 alias）。
- casing 未決：`MrLiouIR`（本表採用，對齊 `MrLiouWord`）vs v4 `MrliouIR`（疑筆誤）。
- 外部標準（SPDX/JWT）僅對照層，詳見 `MRL_外部標準對照_SPX_JWT.md`。

---

## 5. MRL_不可宣稱完成項（只列缺口）

- canonical 運轉核心源碼不在主線 main（PR #35 + #37 **未 merge**）。
- BaseWorld 27-table 真實接線（外部 Cloudflare D1，未入 repo）。
- PersistentLoop Daemon（未實作；阻於上述 merge）。
- DL580 reboot survival（未實機測試）。
- Replay / Restore durable runtime（架構在 #37，未於 main 閉環）。
- 3D / 拓樸潮 / 無限環 / 地映層（repo 內無實體）。
- 外部材料批（HTTP/Token/Signature/Credential/.pages 等）尚未正規吸收入 repo。
- v4 canonical casing（MrLiouIR vs MrliouIR）未由主線最終裁定。

---

## 6. MRL_下一步工程（只列可執行項）

1. **merge PR #35（core）+ #37（naming）→ main**：一次解開「核心缺源」與多數 FAIL 回返鏈。
2. merge 後 `base off main` 建 `MRL_Branch_PersistentLoop_Daemon_v1`，實作真實 daemon（A–G 驗收）。
3. 主線裁定 canonical casing（`MrLiouIR` / `MrliouIR`），如需則全域 grep 統一。
4. 痕跡層（`06_trace`）與運轉場閉環（snapshot → replay → restore）。
5. 外部材料批正規吸收：經 gateway → provenance_verify → dedup → FLTNZ → BaseWorld（另線，不混入核心）。
