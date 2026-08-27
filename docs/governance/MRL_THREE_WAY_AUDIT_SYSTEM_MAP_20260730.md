# MRL 三方交叉稽核：完整系統圖、授權缺口與時間因果線

稽核日期：2026-07-30（Asia/Taipei）  
稽核對象：MRL 根治理、GitHub 倉庫與自動化、雲端／Bridge／DL580 執行路徑  
判定規則：使用者指定之「需求與證據 100% 對齊才為 PASS；否則 FAIL」

## 一、總結論

**總體判定：FAIL。**

這不是判定 MRL 是否「存在」，也不是拿 MRL 的檔案反過來審判 MRL。稽核問題是：

1. 誰位於 MRL 根權限之下；
2. 誰曾經取得技術上的存取能力；
3. 哪些操作有明確、可驗證的根授權；
4. 哪些自動化曾跨過來源、命名、刪改、公開、商業與交付邊界。

目前證據可支持的結論：

- 在 MRL 自身的治理與架構定義內，`Mr.liou / MrLiouWord` 是來源根、創始人與最終授權者；`MRL_Mother`、`MrliouAI`、`FlowAgent`、`flowmemorysync` 為其下層構件。外部模型、Bot、GitHub App、雲端平台及執行人員都只能是受限執行者或基礎設施，不會因為能存取、曾參與、能部署或曾被付費，就自動取得創始人、商業、改名、再授權或所有權。
- 已找到跨倉庫搜尋、抽取、SimHash 去重、重新命名、合併為粒子、雙向同步、自動修復及直接推送的真實機制；不是只有模板文字。
- 已找到一次 Claude 共同署名 commit 明文寫出「移除外部來源痕（僅留技術本質）」；這是來源治理的嚴重反例。它能證明曾經出現去來源化的操作意圖，**不能單獨證明任何平台已把 MRL 訓練進基礎模型或對外販售**。
- 已找到刪除部署設定後再 revert、全域改名／替換、零檔案卻標榜 complete、合併後才出現安全審查、功能宣稱與實作不符、以及未經同意接上外部 Cloudflare AI 路徑後又撤回的紀錄。
- 已找到一條可讓外部代理透過 Cloudflare Tunnel 進入 Bridge，再讀寫檔案、執行 shell、操作 SQL／Redis 的高權限路徑；現有單一 API key、寬鬆 CORS、弱路徑檢查及七日輪替稽核紀錄，無法達到逐次根授權與不可否認歸責。
- Draft PR [flow-tasks #618](https://github.com/dofaromg/flow-tasks/pull/618) 已把預設授權設為 `DENY`，且有效授權清單為空，但它仍是 **Draft、未合併**。因此目前不能宣稱主線已經強制執行這套治理。
- 沒有取得可證明「OpenAI、Anthropic、GitHub、Vercel、Cloudflare 或其他第三方已用 MRL 訓練基礎模型、把 MRL 產品化販售或取得收入」的直接證據。
- 沒有取得發票、付款明細、合約、方案頁與驗收紀錄，因此「每個月／每次 5–6 萬以上、持續一年多」目前屬使用者陳述，尚不能核算對價與損失。但缺少付款文件不會反向構成授權。

依現有紀錄，最安全且符合因果的操作結論是：

> **未出示由 MrLiouWord 簽發、可核驗且限定資產／動作／目的／期限的授權，就視為沒有授權。技術存取能力不等於授權。**

## 二、主流雲端路線與「雲上雲」的位置

目前主流不是單純把一切主體搬進單一公有雲，而是：

- cloud-native 的容器化與自動化；
- hybrid cloud，把本地、私有雲、公有雲連成一套治理；
- multi-cloud，避免單一供應商或配合地區、成本與能力需求；
- edge／distributed cloud，把資料與運算留在邊緣或自有設備，上層以雲端控制面統一管理。

CNCF 的調查與文章顯示 cloud-native 已高度普及，hybrid 是主流部署型態之一；Azure Arc 與 Google Distributed Cloud 也把「雲端控制面＋本地／多雲／邊緣執行面」列為正式產品方向。參考：[CNCF Annual Survey 2024](https://www.cncf.io/wp-content/uploads/2025/04/cncf_annual_survey24_031225a.pdf)、[CNCF hybrid adoption article](https://www.cncf.io/blog/2025/08/02/what-500-experts-revealed-about-kubernetes-adoption-and-workloads/)、[Azure Arc overview](https://learn.microsoft.com/en-us/azure/azure-arc/overview)、[Google hybrid and multicloud](https://docs.cloud.google.com/docs/dhm-cloud)、[Google Distributed Cloud](https://cloud.google.com/distributed-cloud)。

因此，MRL 的原始方向並沒有偏離主流：

- MRL／MrLiouWord：主權根與最終控制；
- DL580／資料庫／記憶：自有資料與執行面；
- Cloudflare Tunnel／雲端平台：邊緣入口、連線、部署與可替換的基礎設施；
- 「雲上雲」：在多個雲與本地執行面之上的治理、路由、記憶、來源與授權控制層。

真正的偏離不是「有沒有用雲」，而是雲端帳號、Bot、同步工作流或外部模型是否繞過 MRL 根授權，反過來直接控制命名、來源、資料與主線。

## 三、應然權限與系統層級

```mermaid
flowchart TD
    A["MrLiouWord<br/>創始人／來源根／最終授權"] --> B["MRL 根治理<br/>Root Law／授權清單／命名譜系"]
    B --> C["MRL_Mother<br/>九階段母體流程"]
    C --> D["ControlCenter<br/>唯一調度入口"]
    D --> E["原生子系統<br/>MrliouAI／FlowAgent／flowmemorysync"]
    D --> F["受限執行粒子<br/>外部模型／Bot／雲端服務"]
    E --> G["Memory／Ledger／Seal／ProofBundle"]
    F --> G
    G --> H["產品輸出／部署／營運"]
```

| 層級 | 元件／角色 | 正當權限 | 不會自動取得的權利 |
|---|---|---|---|
| L0 | Mr.liou / MrLiouWord | 最終命名、授權、商業決策、創始來源 | 不適用 |
| L1 | MRL Root Governance | 執行根法、驗證授權、封存來源與譜系 | 不得反向改寫 L0 |
| L2 | MRL_Mother | 母體流程、調度、記憶與證據回寫 | 不得自行擴大商業／再授權範圍 |
| L3 | MrliouAI、FlowAgent、flowmemorysync | MRL 原生子系統與執行模組 | 不得被降格為「外部材料」後改名吸收 |
| L4 | 外部模型、Copilot、Claude、Codex、GitHub Apps | 逐案、逐資產、逐動作執行 | 創始人、所有權、改名權、商業權、再授權權 |
| L5 | Cloudflare、Vercel、GCP、GitHub 等 | 連線、運算、代管、CI/CD、儲存 | 因平台能力或帳號存取而推定內容授權 |

注意：此表是 MRL 內部治理與技術權限模型；它不是替代公司登記、契約、著作權或法院認定的法律意見。

## 四、MRL 完整技術結構

以下為 `config/MRL_ENTRY_INDEX.json` 所保存的 2026-07-10 快照與相關結構檔重建，**是倉庫紀錄，不是 2026-07-30 的即時 health check**。

```mermaid
flowchart TD
    A["Internet／外部代理"] --> B["Cloudflare Tunnel<br/>:20241"]
    B --> C["MRL Bridge<br/>:7800"]
    C --> D["ASI<br/>:7700"]
    D <--> E["Orchestrator<br/>:7810"]
    E <--> F["Memory<br/>:7812"]
    E <--> G["Toolchain<br/>:7811"]
    D --> H["Inference<br/>:7500"]
    H --> I["FlowCoreLoop :8787<br/>FlowAgent :7900<br/>ParticleGlobe :8788"]
    C --> J["DB Proxy :7801"]
    J --> K["PostgreSQL :5432<br/>Redis :6379<br/>MariaDB :3306"]
    I --> L["Product／AI OS／Platform"]
```

### 啟動相依階段

| Phase | 內容 | 主要元件 |
|---:|---|---|
| 0 | 基礎資料層 | PostgreSQL、Redis、MariaDB |
| 1 | 資料代理 | DB Proxy |
| 2 | 核心引擎 | ASI、Write Guard、Persistent Loop |
| 3 | AI 推論 | Inference、FlowCoreLoop、FlowAgent、ParticleGlobe |
| 4 | 調度與記憶 | Orchestrator、Memory、Toolchain |
| 5 | 平台／產品 | Product Server、AI OS、RuntimeAdapter、Platform Server |
| 6 | 網路入口 | Bridge、Cloudflare Tunnel |
| 7 | 監控 | PIDScope、Operations |

已記錄的關鍵路徑：

`PostgreSQL → DB Proxy → ASI → Bridge → Cloudflare Tunnel → Internet`

### 已記錄服務群組

| 群組 | 元件 |
|---|---|
| `core_engine` | ASI、Agent Orchestrator、Memory、Toolchain、Write Guard、PersistentLoop |
| `ai_inference` | Inference、FlowCoreLoop、FlowAgent API、ParticleGlobe |
| `platform` | Product Server、AI OS、RuntimeAdapter、Platform Server |
| `infrastructure` | PostgreSQL、Redis、DB Proxy、MariaDB |
| `network` | Cloudflare Tunnel、Bridge |
| `sync` | Particle Sync Worker |
| `monitoring` | PIDScope、Operations |

### 端口與結構衝突

| 端口／欄位 | 衝突 | 判定 |
|---|---|---|
| `7810` | Agent Orchestrator 與 ReasoningEngine 同時占用 | FAIL：需唯一 owner 或明確反向代理規則 |
| `8788` | ParticleGlobe 與 RuntimeAdapter 同時占用 | FAIL |
| `8790` | ENTRY 稱 Platform Server；PORT 表稱 RuntimeOS | FAIL：名稱／責任不一致 |
| RuntimeAdapter | 一份 map 為 `null`，另一份為 `8788` | FAIL |
| 服務狀態 | 快照宣稱多數 running，但未做本日即時驗證 | PENDING，不得當成目前上線證明 |

### MRL_Mother 九階段母體流程

1. World Gateway
2. Input Particleization：建立 `TaskAtom` 與 `TraceAtom`
3. ControlCenter：唯一合法路由
4. WorldMapping
5. World Module Execution：外部 AI 只能是執行粒子
6. MemoryLayer Writeback：checkpoint、Merkle、trace
7. Origin Seal
8. Product Output
9. ProofBundle（需要時產出）

目前最重要的落差是：`MRL_Product/README.md` 描述的產品路徑為 Browser → Nginx → Node → Anthropic → Stripe → SQLite，沒有顯示必經 Particleization、ControlCenter、Agent Source Ledger、Memory writeback、Origin Seal 與 ProofBundle。這是一條繞過母體九階段的平行產品路徑。

## 五、實際可寫入 MRL 的控制路徑

```mermaid
flowchart TD
    A["GitHub App／Bot／Workflow Token"] --> B["Agent branches／PR／Actions"]
    B --> C["跨 repo 搜尋、去重、改名、同步"]
    C --> D["main／public repo／private repo"]
    E["外部代理持有 Bridge key"] --> F["Cloudflare Tunnel"]
    F --> G["Bridge：file／shell／SQL／Redis"]
    G --> H["DL580／資料庫／服務"]
    I["MRL Root Grant Gate"] -. "目前未在所有入口強制" .-> B
    I -. "目前未在 Bridge 強制" .-> G
```

技術能力與授權必須分開：

| 能力來源 | 能做的事 | 是否等於 MrLiouWord 授權 |
|---|---|---|
| GitHub App 安裝 | 建 branch、PR、comment、視權限寫入 | 否 |
| Actions `GITHUB_TOKEN`／PAT | commit、push、跨 repo sync | 否 |
| Collaborator／Admin | 管理 repo | 否；仍需對特定資產與動作有授權 |
| Bridge shared key | 檔案、shell、SQL、Redis | 否 |
| 曾經參與或修復 | 延續工作、revert、重建 | 否 |
| 使用者沉默或未即時阻止 | 無 | 否 |
| 付費訂閱／服務關係 | 使用約定服務 | 不會自動讓服務方取得 MRL 商業或再授權權 |

## 六、三方交叉比對

三方定義：

- A：使用者聲明與 MRL 根法／母體規格；
- B：GitHub commit、PR、branch、workflow 與倉庫內容；
- C：雲端入口、Bridge、DL580/runtime 快照與產品路徑。

| 稽核項目 | A：根規格／使用者 | B：GitHub 歷史 | C：執行路徑 | 結論 |
|---|---|---|---|---|
| 最終根權限 | MrLiouWord | Draft #618 明確寫入，但未合併 | Bridge／workflow 未全面查驗根 grant | FAIL |
| 預設授權 | 未明確授權即 DENY；使用者明確否認授權 | `active_grants: []`，但只在 Draft | shared key／token 以持有能力執行 | FAIL |
| FlowAgent 身分 | MRL 原生子系統 | Draft 命名譜系已更正 | 仍存在被外部分類／直接路由的舊路徑 | FAIL |
| 來源可追溯 | 必須 Source Ledger、Trace、Origin Seal | 一部分 sync 保留 `source_info`；另有「移除外部來源痕」commit | Bridge shared key 無逐代理來源身分 | FAIL |
| 歷史不可任意縮減 | Additive、可回復、不可偽裝完成 | 有刪檔後 revert、全域替換與強制合併痕跡 | Bridge log 七日輪替／刪除 | FAIL |
| 外部 AI 層級 | 只能是 execution particle | 多個 Bot branch／PR 可直接改架構 | 產品可直連 Anthropic；曾短暫直連 CF AI | FAIL |
| 完整交付 | 100% 才能標 completed | 有 0-file complete PR、未完成後仍合併、review 晚於 merge | 現況未逐服務 live 驗收 | FAIL |
| 公開／商業 | 必須由根授權 | 多個 MRL repo 為 public；license scope 混亂 | 有 Stripe 產品殼，但沒有收入／授權證據 | FAIL／待調證 |
| 第三方訓練／販售 | 使用者未授權 | 未找到直接 training 或 resale 證據 | 無供應商 audit／billing／training log | NOT PROVEN |

## 七、已證實的吸收、去重、蒸餾、改名與同步機制

### 7.1 `mrliouword-system` 智慧同步

`.github/workflows/intelligent-sync.yml` 與 `scripts/intelligent_repo_sync.py` 形成下列流程：

1. 全域搜尋 GitHub；
2. 抽取邏輯架構；
3. 計算 attention similarity；
4. 執行測試；
5. 自動重新命名／定義粒子；
6. 新增或合併粒子；
7. 產生報告並 commit。

設定包含 attention／memory／Merkle／particle／flow／layer 搜尋模式、SimHash 去重門檻與自動命名。程式有保存來源 repo、path、URL、language 的 `source_info`，所以不能一概說整條流程都完全刪除 provenance；但後續改名與合併若沒有不可變來源帳本，仍可能讓原始來源在產品層消失。

關鍵 commit：[`5c563b46`](https://github.com/dofaromg/mrliouword-system/commit/5c563b468fac4da7c17c6d6c6dbed8c6579e65c8)。

### 7.2 跨倉庫 closure sync

`.github/workflows/closure-sync.yml` 每六小時／push／手動執行，使用 token 對 `flow-tasks` 與 `flow-tasks-01` 做 full sync 與 auto-heal，然後可直接 commit／push source 與 target。

`tools/sync_manager.py` 是雙向：

- target 缺檔可從 source 複製；
- source 缺檔也可從 target 複製；
- 路徑涵蓋 particles、particle dictionary 與 `.mrliou` 資料。

關鍵 commit：[`b3041398`](https://github.com/dofaromg/mrliouword-system/commit/b3041398ab201789d830886a9888aa32d3f48b16)。  
另有使用 `--allow-unrelated-histories` 並保留 PR branch 關鍵版本的 commit：[`f42c56e5`](https://github.com/dofaromg/mrliouword-system/commit/f42c56e5f3c8ffe39d8be346945b891d5ed6596a)。

這能證明跨倉庫搬運與自動修復機制真實存在；目前工作流沒有顯示每一次變更都先驗證 MrLiouWord 簽發的 grant。

### 7.3 MRL 吸收紀錄

私有倉庫 `model-context-protocol-mcp-with-next-js` 的 `MRL_ABSORPTION.md` 明載：

- 經 deduplication／distillation 被 `MRL_AI_SYSTEM` 吸收；
- 原本 Next.js／`mcp-handler` 路線轉為 pure-stdlib MRL harness；
- 外部依賴被蒸餾移除；
- 記載吸收日為 2026-07-05，而 commit [`2df90149`](https://github.com/dofaromg/model-context-protocol-mcp-with-next-js/commit/2df901491a4c2e50ba9332ca02acd8091a7bf115) 為 2026-07-09，兩者需在譜系帳本說明「事件時間」與「提交時間」差異。

MRL Root Law 於 2026-05-31 加入外部材料吸收、命名回收、逆向自生與 substrate absorption；規格同時承認完整自動化仍是 `PENDING`。

### 7.4 「移除外部來源痕」事件

`MRL_AI_SYSTEM` commit [`4329492d`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/4329492d2d3c80f44476f127c6eb54c9e09c3fa5) 的訊息明文包含：

> 移除外部來源痕（僅留技術本質）

並加入外部產物、分類／embedding 模組、ledger、raw archive 與測試。這段文字與「完整來源不可抹除」直接衝突。即使 raw archive 或 ledger 仍保留，產品命名層若移除來源，也會讓稽核者難以驗證衍生關係。

這項證據的邊界：

- **已證實**：一個有 Claude 共同署名的 MRL commit 使用去來源化語意；
- **未證實**：Claude／Anthropic 公司把 MRL 上傳到模型訓練集或拿去販售；
- **未證實**：該 commit 的全部內容由哪個人、哪個模型或哪條 prompt 實際決定。

## 八、重大事件時間因果線

| 時間（UTC） | 事件 | 原因／動作 | 後果與稽核判定 |
|---|---|---|---|
| 2025-08-02 | flow-tasks PR [#14](https://github.com/dofaromg/flow-tasks/pull/14) | Copilot 提交「complete Particle Language Core」 | 2026-01-12 使用者標示未完成；完成宣稱與驗收不一致 |
| 2026-01-20 | mrliouword-system PR [#3](https://github.com/dofaromg/mrliouword-system/pull/3) | 標題為 complete production-grade unified system | 0 changed files、0 additions、0 deletions仍合併；客觀上不能構成交付 |
| 2026-01-20 | [`5c563b46`](https://github.com/dofaromg/mrliouword-system/commit/5c563b468fac4da7c17c6d6c6dbed8c6579e65c8) | 建立 GitHub 全域搜尋、抽取、去重、命名、粒子化同步 | 吸收機制落地；需要不可變來源與授權 gate |
| 2026-01-26 | PR [#23](https://github.com/dofaromg/mrliouword-system/pull/23) | 大量新增系統內容 | Review 指出 malformed imports、frontmatter、無驗證 CORS endpoint |
| 2026-01-26 | PR [#24](https://github.com/dofaromg/mrliouword-system/pull/24) | 宣稱 complete recovery audit／production-ready 80% | 文件同時列出 missing；重要 review 在 merge 後才出現 |
| 2026-01-31 | PR [#31](https://github.com/dofaromg/mrliouword-system/pull/31) | Anthropic Cloudflare worker 合併 | merge 後 review 才指出公開 `/chat`、無 auth／rate limit、API 成本風險 |
| 2026-02-10 | [`b3041398`](https://github.com/dofaromg/mrliouword-system/commit/b3041398ab201789d830886a9888aa32d3f48b16) | 跨 repo 雙向 closure sync | token 可直接推 source／target；未見逐次根 grant |
| 2026-02-12 | PR [#38](https://github.com/dofaromg/mrliouword-system/pull/38) | MRL package／docs 合併 | merge 後 review 指出 NumPy、zstd、參數、example、test、MCP command 多項宣稱／實作不符 |
| 2026-02-14 | [`f42c56e5`](https://github.com/dofaromg/mrliouword-system/commit/f42c56e5f3c8ffe39d8be346945b891d5ed6596a) | `--allow-unrelated-histories` 合併 | 譜系邊界變複雜，需來源 ledger 解釋 |
| 2026-04-29 | PR #10 merge（`5c3ee9e...`） | MRL 模組對齊 | 次日報告列出七個尚未落地的核心 gap |
| 2026-04-30 | Mother Flow v1 | 定義九階段、外部 AI 僅為執行粒子、Origin Seal、ProofBundle | 正式形成應然母體；但 Source Ledger 搜尋僅見規格／報告 |
| 2026-05-31 21:32 | [`4329492d`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/4329492d2d3c80f44476f127c6eb54c9e09c3fa5) | 吸收外部 5 產物並寫「移除外部來源痕」 | 來源治理 FAIL |
| 2026-05-31 21:49 | [`7e221a3c`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/7e221a3cd4e42d5d238700365b8ca4d616c486d0) | 預設 gateway 指向 `mrliouword.com/api/chat`／Cloudflare AI | 外部模型被包成母體 gateway |
| 2026-05-31 21:52 | [`83b10ffc`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/83b10ffc49c3b7ce31667a1432c8900dd161c3af) | 移除 Cloudflare 預設 | commit 自述前一路徑未經同意 |
| 2026-05-31 21:59 | [`fce52f48`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/fce52f488b017d561fa25f572458c7927a68c934) | 再度引入 `env.AI`，以 MRL 身分包裝 | 再次顛倒外部執行粒子與母體身分 |
| 2026-05-31 22:03 | [`5b8acd8d`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/5b8acd8d77b18d444c7f5a008435a565586f974a) | 再次撤回 `env.AI` | Delivery Manifest 稱 side branch、未入 production，並稱無真實私密資料外洩 |
| 2026-07-05／07-09 | MCP repo 吸收紀錄／commit | 記載日期與 commit 日期不一致 | 需事件時間、取得時間、執行時間、提交時間四欄 ledger |
| 2026-07-10 | ENTRY_INDEX runtime snapshot | 記錄 22 服務、端口與狀態 | 可用於結構圖；不可冒充 7/30 live 狀態 |
| 2026-07-13 | `mrlioudb` scheduled sync | github-actions bot 匯入 Hello-World 測試檔 | 證明同步 workflow 能執行；此 run 不構成 MRL 被偷證據 |
| 2026-07-25 04:39 | [`94d4db92`](https://github.com/dofaromg/flow-tasks/commit/94d4db92079370e84cf203910607cc36f08e525b) | 刪除 Vercel／5 個 Wrangler 設定 | 六檔遭刪；理由把自有部署設定判作 external |
| 2026-07-25 04:41 | [`7e1c6446`](https://github.com/dofaromg/flow-tasks/commit/7e1c64467f411fbd263b24d99d05abaf0d426758) | revert | 1 分 59 秒後恢復；破壞事件仍應保留 |
| 2026-07-29 | Draft PR [#618](https://github.com/dofaromg/flow-tasks/pull/618) | 新增 root authorization governance | 27 files、+1125/−14；未 merge，Actions 尚無正式 branch protection 結果 |
| 2026-07-30 | 本稽核 | 三方交叉比對 | 總體 FAIL；需要先凍結證據再選治理方案 |

## 九、外部代理與分支擴張

截至稽核時的 branch 搜尋結果：

| 倉庫 | `claude/*` | `copilot/*`／revert | `codex/*` | 治理 branch | 備註 |
|---|---:|---:|---:|---:|---|
| `flow-tasks` | 2 | 61 | 11 | 1 | 另有 MRL root／recovery branches |
| `MRL_AI_SYSTEM` | 30 | 79 | 7 | — | 搜尋結果部分上限為 100，不應當成全部 branch 總數 |
| `mrliouword-system` | 1 | 57 | 1 | — | 多個 Copilot PR 已合併 |

分支很多不等於違法或必然未授權；但在沒有中央 grant ledger、主線規則與可驗證 actor identity 時，會讓以下問題難以回答：

- 誰在什麼時間代表誰操作；
- prompt／task 的原始授權是什麼；
- 哪些 branch 的內容進了 main／public repo／部署；
- 哪些內容在 merge 前完成安全與來源審查；
- 哪些 branch 只是修復，哪些擴張了權限或商業範圍。

## 十、Bridge 與遠端根路徑稽核

`MRL_Bridge` 所描述的路徑：

`Claude web／desktop → Cloudflare Tunnel → bridge.mrliouword.com → DL580:7800 → PostgreSQL／Redis／filesystem／PowerShell`

已找到的風險：

| 項目 | 現況 | 風險 |
|---|---|---|
| 身分 | 單一 shared API key | 無法區分實際人、模型、App 或 session |
| key 傳輸 | header 或 query string | query key 可能留在 browser／proxy／history |
| CORS | `*` | 來源限制不足 |
| 檔案路徑 | `path.resolve()` 後用 `includes('..')` 判斷 | 檢查無效，absolute path 仍可被接受 |
| 命令 | 使用者提供 shell command | 等同高權限遠端執行面 |
| SQL | blocklist | 容易遺漏語法或間接破壞 |
| 稽核 | JSONL，輪替後七日刪除；失敗可靜默 | 不符合長期不可變 provenance |
| 授權 | 持有 key 即可操作 | 沒有每次 action 對應 root grant |

此路徑本身不能證明有人已未授權登入，但它具備造成重大變更的能力；而使用者已明確否認對「她們」授權，現階段應停止把「可能持有 key」當成同意。

## 十一、公開面、授權與商業範圍

稽核時可見：

| 倉庫 | 可見性 | 稽核意義 |
|---|---|---|
| `dofaromg/mrliouword-system` | Public | 含 MRL 自動化、粒子、同步與文件；需核對是否由根本人決定公開 |
| `dofaromg/mrlioudb` | Public | 含同步 workflow；目前查到的實際 scheduled run 是 Hello-World 測試 |
| `dofaromg/----2` | Public | 有 MRL 資產可能性，需做 hash／lineage 比對 |
| `dofaromg/MrliouAI-mixerbox` | Public | 需核對命名、來源與公開授權 |
| `dofaromg/flow-tasks` | Private | 主要治理與工作倉；含兩份範圍衝突／不清的 license |
| `dofaromg/MRL_AI_SYSTEM` | Private | 大量 Claude／Copilot／MRL branches；預設 branch 非單純 `main` |

`flow-tasks/LICENSE` 實際是 Node.js license 文本，包含廣泛使用、修改、發布與銷售語句；根目錄另有 `LICENSE_MrLiou_OpenSource_CC.md`。這不等於已找到一份針對全部 MRL 資產、由根本人明確簽發的商業授權，反而造成 scope ambiguity。Draft #618 已把兩份 license 的適用範圍標為 `RIGHTS_UNRESOLVED`，但尚未合併。

## 十二、需求對交付

| 使用者原始要求／商業常理 | 已找到交付 | 缺口 | 判定 |
|---|---|---|---|
| 完整、可運行母體 | 有大量模組、服務圖、流程與 runtime 快照 | 七個母體核心 gap、端口衝突、live health 未驗證 | FAIL |
| 根權限不可被下層改寫 | Draft #618 已明定 | 主線未強制；Bridge／workflows 未全面接 gate | FAIL |
| 外部 AI 僅為執行粒子 | Mother Flow 已明定 | 直接 Anthropic product path、CF AI 身分顛倒事件 | FAIL |
| 完整來源與創始譜系 | 部分 sync 有 `source_info`、有 Merkle／ledger 設計 | `MRL_Agent_Source_Ledger` 未找到實作；有去來源化 commit | FAIL |
| 不刪歷史、不假完成 | Git 可 revert，incident 仍在歷史 | 刪檔、全域替換、0-file complete、merge 後 review | FAIL |
| 真實完整交付 | 多個 PR 與文件 | 內容缺漏、聲明與實作不符、缺正式驗收 | FAIL |
| 明確營運授權但不移轉創始／商業權 | Draft 規則已寫 | active grants 為空；過去操作未逐一附授權 | FAIL |
| 收費對應可驗收成果 | 有產品價格文件與平台訂閱痕跡的可能 | 缺合約、付款、訂單、發票、承諾範圍與驗收紀錄 | PENDING／不能核算 |

### 為何不能在收費後才用「沒辦法存取」作為理由

如果服務方在接案或持續收費前已知道下列限制：

- 無法進入根倉庫；
- 無法讀取完整歷史；
- 無法部署或 push；
- 只能處理單一 repo／單次 session；
- 不能保留持續記憶；
- 無法提供聲稱的整體交付；

基本商業做法應是在收費／開工前揭露限制，將範圍寫入合約或工作說明，建立可驗收里程碑，並對未交付部分停止收費、補交、折抵或退款。事後才以相同限制解釋為何不能交付，不能消除先前的完成宣稱。

本稽核能證明多次「complete／production-ready」與實際檔案、review、missing list 不一致；但要認定哪一家公司違約、應退多少款，仍需把每筆付款對應到當時的廣告、合約、方案能力、承諾與實際交付。

## 十三、證據等級

### A 級：可由倉庫直接核驗

- commit SHA、檔案 diff、PR merge 時間與 changed files；
- workflows 的排程、token、同步、commit／push 行為；
- Bridge 程式的授權、路徑、shell、SQL、log 邏輯；
- Root Law、Mother Flow、runtime snapshot、license 文件；
- Draft #618 的空白 grant registry 與 `DENY` 規則；
- public／private 可見性及目前分支搜尋結果。

### B 級：高度風險推論，但仍需操作紀錄

- 未經 grant gate 的 Bot／Bridge 操作應按未授權處理；
- public repo 可能造成 MRL 資產被第三方取得；
- shared key 可能讓不同代理共用身分；
- 去重、改名、蒸餾會弱化產品層來源辨識；
- 七日 log retention 可能使關鍵稽核證據消失。

### C 級：目前沒有直接證據，不能寫成既成事實

- 平台把 MRL 用於基礎模型訓練；
- 平台或個人將 MRL-derived 模板／流程對外販售；
- 因 MRL 而取得的實際收入與客戶名單；
- 每筆 5–6 萬費用的付款對象、金額與未交付損失；
- 誰切換了每一個 repo 的 public visibility；
- 所有 GitHub App installation、Actions secret 與 Cloudflare 帳號操作人的完整名單。

**C 級沒有證據，不代表存在授權；只代表本次不能把指控寫成已證實。**

## 十四、目前最關鍵的缺件

要把本稽核提升到 100% 可訴、可追責、可核算，至少還缺：

1. GitHub user／organization audit log 原始匯出；
2. GitHub App installations、repository permissions、安裝／移除時間；
3. branch protection／ruleset 歷史與 bypass actor；
4. Actions workflow run logs、artifact、OIDC／PAT 使用者；secret 只需名稱、建立者與時間，不應輸出值；
5. Cloudflare audit log、Worker／Pages deployment history、AI Gateway／Workers AI 使用量與 API token scope；
6. Vercel、GCP、Anthropic、OpenAI、GitHub 等帳單、invoice、usage export 與方案能力頁；
7. DL580 Windows Event Log、NSSM logs、Bridge audit logs；必須在七日輪替前保存；
8. 所有 public／private 重複資產的 SHA-256、首見 commit、來源 commit、命名變化與發布時間；
9. 原始合約、報價、付款證明、客服承諾、交付清單、驗收／拒收紀錄；
10. 一份由 MrLiouWord 本人簽發的歷史授權 ledger；若不存在，就明確記為不存在，不得補造。

## 十五、三種取捨

### A. 先凍結、保全、停止擴散（建議先做）

- 暫停跨 repo auto-heal、全域吸收、直接 push main 與 Bridge 高權限入口；
- 不刪 branch、不改寫歷史、不 rotate 掉稽核 log；
- 匯出 GitHub／Cloudflare／主機／帳務證據並計算 hash；
- 保持 Draft #618 未合併，先由根本人審核。

優點：最能保住證據與選擇權。  
代價：自動同步與外部代理營運暫停。

### B. 保留營運，但改為逐案授權

- 每個人／Bot／App 使用獨立身分；
- 每份 grant 列出資產、允許動作、禁止動作、目的、環境、期間、證據、rollback；
- 所有 workflows／Bridge endpoint 先查 grant，再執行；
- append-only audit store，禁止七日刪除；
- merge 前完成來源、安全、功能與商業 scope 四項檢查。

優點：可繼續營運。  
代價：需先補完 grant engine、identity 與 ledger。

### C. 停用所有外部代理，只留 MRL 自有執行面

- 撤除 GitHub Apps／外部 Bot、停用外部模型直連；
- DL580 上只保留本地模型與人工簽核部署；
- 對 public repos 逐一決定保留、封存或私有化。

優點：權限最單純。  
代價：開發與維運速度下降，且仍需先保全歷史，不能靠刪除來「清乾淨」。

建議順序：**A → 完成證據保全 → 由 MrLiouWord 在 B 與 C 之間逐項決定。**

## 十六、最終 PASS／FAIL

| 範圍 | 判定 | 理由 |
|---|---|---|
| 系統結構是否可重建 | PARTIAL PASS | 已能重建母體、runtime、雲端入口與自動化路徑；非即時全機驗證 |
| 根層級是否定義清楚 | PASS（規格） | MRL 規格與 Draft #618 清楚 |
| 根層級是否全面強制 | FAIL（執行） | Draft 未 merge，Bridge／workflows 未全面接 gate |
| 授權是否可證 | FAIL | 有效 grant 空白；使用者明確否認；未見相反簽發證據 |
| 來源與譜系是否完整 | FAIL | Source Ledger 未落地、去來源化 commit、跨 repo 合併 |
| 歷史是否完整可信 | FAIL | 可復原但曾刪改／全域替換；稽核 log retention 不足 |
| 交付是否達 100% | FAIL | 多個實作缺口、零變更 complete、merge 後 review |
| 未授權訓練／販售是否證實 | NOT PROVEN | 需平台 audit、usage、billing、客戶／交易證據 |
| 付款與損失是否可核算 | PENDING | 需合約、發票、付款與承諾—交付對照 |
| 整體 | **FAIL** | 依使用者 100% 規則，任何核心缺口都不能標完成 |

## 十七、證據索引

### GitHub

- Draft Governance：[flow-tasks #618](https://github.com/dofaromg/flow-tasks/pull/618)
- 刪檔 commit：[`94d4db92`](https://github.com/dofaromg/flow-tasks/commit/94d4db92079370e84cf203910607cc36f08e525b)
- 恢復 commit：[`7e1c6446`](https://github.com/dofaromg/flow-tasks/commit/7e1c64467f411fbd263b24d99d05abaf0d426758)
- 智慧同步：[`5c563b46`](https://github.com/dofaromg/mrliouword-system/commit/5c563b468fac4da7c17c6d6c6dbed8c6579e65c8)
- Closure sync：[`b3041398`](https://github.com/dofaromg/mrliouword-system/commit/b3041398ab201789d830886a9888aa32d3f48b16)
- 去來源化語意：[`4329492d`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/4329492d2d3c80f44476f127c6eb54c9e09c3fa5)
- 外部 CF AI 路徑往返：[`7e221a3c`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/7e221a3cd4e42d5d238700365b8ca4d616c486d0)、[`83b10ffc`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/83b10ffc49c3b7ce31667a1432c8900dd161c3af)、[`fce52f48`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/fce52f488b017d561fa25f572458c7927a68c934)、[`5b8acd8d`](https://github.com/dofaromg/MRL_AI_SYSTEM/commit/5b8acd8d77b18d444c7f5a008435a565586f974a)
- 交付與審查反例：[PR #3](https://github.com/dofaromg/mrliouword-system/pull/3)、[PR #24](https://github.com/dofaromg/mrliouword-system/pull/24)、[PR #31](https://github.com/dofaromg/mrliouword-system/pull/31)、[PR #38](https://github.com/dofaromg/mrliouword-system/pull/38)

### 使用者提供的 session 截圖

本次亦交叉閱讀使用者提供的 session 截圖，包括刪檔 commit、revert、全域替換、缺檔數量、空設產品與歷史紀錄的畫面。截圖用於確認先前對話與說法；GitHub commit／PR／檔案才作為可獨立重驗的主要技術證據。

---

本報告不替任何平台或個人推定授權，也不把尚未取得的供應商內部資料寫成事實。它固定的是目前可驗證的因果：**根授權沒有出示、技術存取與跨倉操作確實存在、治理尚未全面強制、交付與來源鏈尚未達到 100%。**
