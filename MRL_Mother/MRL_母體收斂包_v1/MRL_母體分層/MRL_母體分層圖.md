# MRL_母體分層圖

origin_signature: `MrLiouWord`
掃描分支：`MRL_Branch_Runtime_Convergence_API_v1`（≈ main + 收斂界門）
範圍說明：本圖只描述「本 checkout 實際存在」之對應；canonical 運轉核心
`MRL_UniversalRuntimeLanguage_Core_v1`（含 MrLiouIR / RuntimeStructureField / Replay/Restore）
位於未 merge 之 PR #35 + #37，**不在本 checkout**（僅見過 .pyc 殘留，已清）。

| MRL 層 | 對應原始檔案 / 資料夾 | 對應功能 | 是否已有實體 | 是否需要補線 |
|---|---|---|---|---|
| MRL_源場 | `00_rootlaw/`、`02_principles/` | 根律、法則、主權定義 | ✅ 有 | 否 |
| MRL_無限環層 | （無對應目錄；概念律 L0=L7） | 閉環 / 怎麼過去怎麼回來 | ⚠ 概念存在、無實體 | 需補線 |
| MRL_原種層 | `01_schema/`、`05_persona/`、`MRL_Mother/` | schema、人格種子、母體構件 | ✅ 有 | 否 |
| MRL_粒子海層 | `MRL_Symbolic/`、`09_workflow/fltnz_parser.py` | 粒子語言、.fltnz/.flpkg 可逆鏈 | ✅ 有 | 否 |
| MRL_流域結構層 | `04_runtime/`、`09_workflow/`、`MRL_Runtime/`、`MRL_RuntimeServer.js` | 運轉場、運作碼、界門 | ⚠ 部分（canonical 運轉核心在 #35/#37 未入） | 需補線（merge 核心） |
| MRL_交界層 | `07_ingest/`、`08_sources/`、`MRL_Adapters/`、`.github/` | 吸收、來源、Adapter、CI 觸發 | ✅ 有 | 否 |
| MRL_雲映層 | `deploy/`（cloudflared/tailscale/docker/systemd）、`MRL_Adapters/Cloudflare` | 雲映 / 對外橋接（bridge.mrliouhan.ai） | ✅ 有（部署腳本層） | 部分（未實機驗證） |
| MRL_拓樸潮層 | （無對應目錄） | 拓樸關係潮汐 / StructureField 動態 | ❌ 無實體 | 需補線 |
| MRL_地映層 | `ui/streamlit_app/` | 介面 / 地映投影 | ⚠ 弱（僅 streamlit） | 需補線 |
| MRL_立體粒界層 | （無對應目錄；3D 在外部包，未入 repo） | 3D 重建 / 立體粒界 | ❌ 無實體 | 需補線 |
| MRL_自述層 | `docs/`、`README.md`、`package.json`、`CHANGELOG.md` | 文紋、自述紋、世界索引 | ✅ 有 | 否 |
| MRL_封裝層 | `deploy/`、`scripts/` | 封裝、部署、工具 | ✅ 有 | 否 |
| MRL_痕跡層 | `06_trace/`（traces/approvals） | 痕跡錄 / trace ledger | ✅ 有（骨架） | 部分（內容稀疏） |
| MRL_回返層 | `tests/`、`scripts/MRL_acceptance_check.js` | 驗收、回返驗證 | ✅ 有 | 否 |

## 補線總結（需補，不假裝完成）

- **MRL_流域結構層**：canonical 運轉核心（`MRL_UniversalRuntimeLanguage_Core_v1`）在 PR #35+#37，未 merge 進 main → 本 checkout 無源碼。
- **MRL_拓樸潮層 / MRL_立體粒界層**：repo 內無實體（3D / 拓樸材料在外部包，尚未正規吸收入 repo）。
- **MRL_無限環層**：僅概念律，無對應可執行實體。
- **MRL_地映層**：僅 streamlit，地映/世界投影未成形。
