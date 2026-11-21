# MRL Model / Runtime License Gate v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
Task: MRL-37  
Parent: PR #706, `bd4052bff5b96548a7fad8e618804e633525cfc5`

## 來源與邊界

沿用 `config/MRL_LICENSE_SCOPE_REGISTRY_v1.json` 作唯一權利裁定來源。
Root Law：`MRL_Mother/00_rootlaw/MRL_ROOT_AUTHORITY_v1.md`、
`MRL_LICENSE_SCOPE_BOUNDARY_v1.md`、`MRL_AUTHORIZATION_AND_OPERATING_RIGHTS_v1.md`。
既有 Registry、Root Law、Artifact Trust production policy 未增加任何權利或信任項目。
`RIGHTS_UNRESOLVED`、四項禁止推定政策均維持原值。
BYOH 訂單、單節點範圍、模型權重排除及資料回傳契約繼續適用。

工程測試通過、Owner 法律權利審查、正式合併、客戶交付批准是不同關卡。
本工具只比對已審查記錄，不判定某授權名稱在法律上必然允許商用。
MIT／Apache 標籤不產生授權；第三方權利不得由 MRL 的內部裁定憑空創設。
目前 production Registry 沒有 `artifact_decisions`，因此所有真實商業交付拒絕。
沒有將 LFM 或任何其他外部模型升格為核准模型；LFM 仍預設不隨包交付。
US$10M 等門檻需取得原條款、適用主體與 Owner 裁定，不能從名稱自動填入。

## Manifest 與精確裁定

`licenses/MRL_license_manifest_schema_v1.json` 是封閉的 JSON Schema。
`MRL_license_gate_v1.py` 透過 MRL-45 的 Draft 2020-12 驗證器讀取原始 Schema 與相容性設定。
執行授權 Gate 前，依 [Schema 驗證說明](MRL_GATE_SCHEMA_VALIDATION_v1.md) 安裝雜湊鎖定的依賴。
每個 component 分別記錄 `model_weights`、`runtime`、`container_base`、
`optional_addon` 或 `mrl_source`，並記錄 id、版本、來源、source commit、
每個實際檔案 SHA-256、LICENSE／NOTICE／terms 文件 SHA-256、條件、限制。
可用單一 component 列出同一授權範圍內的多個檔案，不能推及未列出的檔案。
所有 bundled bytes 必須被覆蓋；重複路徑、大小寫碰撞、symlink、路徑逃逸均拒絕。

Manifest 是主張，不能自行授權。未來經 Owner 明確批准後，才可在現有 Registry
的 `artifact_decisions` 加入裁定，不能由命令列傳入替代 Registry：

| 欄位 | 必要內容 |
|---|---|
| `record_id`, `issued_by` | 唯一裁定編號、`MrLiouWord` |
| `component_sha256` | 該 component 的 canonical JSON SHA-256 |
| `context_sha256` | 完整客戶情境 canonical JSON SHA-256 |
| `decision` | `approve`／`reject`／`needs-counsel`；僅 approve 可繼續 |
| `third_party_rights_verified` | 明確 true；需有外部權利依據 |
| `custom_terms_reviewed` | custom／LicenseRef 必須明確 true |
| `review_date`, `starts_on`, `expires_on` | ISO 日期，當日 UTC 必須在有效期內 |
| `grantee`, `purpose`, `environment` | `MRL`、`commercial_customer_delivery`、`BYOH` |
| `permitted_actions`, `prohibited_actions` | 精確涵蓋 commercial_use、redistribute 或 customer_model_use |
| `evidence_reference`, `rollback` | 審查依據及回復方式 |

canonical JSON 沿用 PR #706：UTF-8、排序 keys、無多餘空白、不允許 NaN。
同一 component/context 不得有多筆生效裁定；變更或撤銷須保留歷史證據並另經 Owner 批准。
`approve()` 僅存在測試 fixture，從未寫入 production Registry。

情境必須包含：`customer`、`region`、`mrl_annual_revenue_usd`、
`customer_annual_revenue_usd`、`customer_model_responsibility`。
營收是非負 USD 整數或 null；適用門檻時 null 拒絕。
門檻採保守的「必須低於」規則：等於或高於均拒絕；`both` 分別核對 MRL 與客戶。
外部條款採不同邊界時需提出具體程式與政策修訂，由 Owner 先審查。

## 客戶自帶模型

`delivery=customer_provided` 僅適用模型權重，必須 `mrl_acquisition=false`、
客戶責任確認 true，仍需 commercial_use 及精確 Owner 裁定。
打包時禁止模型權重出現在 ZIP；本機 Runtime 准入則重算客戶模型的每個檔案雜湊。
客戶自帶不會替 Runtime、容器或其他模組授權，也不允許 MRL 代為取得受限權重。

## 可執行入口

在 repository 根目錄，先執行唯讀檢查並建立不可覆寫回執：

```bash
python MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/scripts/MRL_license_gate_v1.py \
  --manifest /approved/license-manifest.json --context /approved/customer-context.json \
  --artifact-root /staged/payload --evidence-root /approved/license-documents \
  --exhaustive --receipt /receipts/license-check.json
```

正式商品候選 ZIP 必須沿用既有建構器：

```bash
python MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/scripts/MRL_build_product_bundle_v1.py \
  --customer-delivery --license-manifest /approved/license-manifest.json \
  --license-context /approved/customer-context.json \
  --license-evidence-root /approved/license-documents
```

選配第三方 Runtime 仍使用既有 `--third-party-runtime`／`--runtime-evidence-root`。
信任檢查先匯出精確來源證據，再對包含證據及客戶設定的完整 staging 進行授權檢查。
來源簽章通過但授權失敗會拒絕，既有 ZIP 不被替換。
僅對新建 ZIP 的衍生 trust receipt 省略不穩定的 verified_at，保留所有驗證與身分欄位；
不改原始來源或歷史回執。離線 replay 不以 wall-clock 時間作身分，
因此送審的完整檔案 hash 可在重建時保持一致。
ZIP 先寫入暫存檔，逐項讀回 hash/size/coverage，驗證完整 NOTICE 與授權證據後才替換輸出。
仍需另外完成硬體實測、訂單與 Owner 客戶交付批准；builder 從不輸出客戶已批准。

未帶授權參數的既有 source build 只建立 `ENGINEERING_ONLY` 工程 ZIP，
`license_admission.allowed=false`、`customer_delivery_approved=false`。
輸出改為 `PRODUCT_ENGINEERING_BUNDLE_PASS`；授權已審候選包則為
`PRODUCT_RIGHTS_REVIEWED_CANDIDATE_PASS`。兩者均不聲稱客戶已批准交付。
這種工程模式禁止加入任何第三方 Runtime bytes。

完整 NOTICE 包含所有已驗證 LICENSE／NOTICE／terms 原文，不以 Manifest 取代。
`MRL_LICENSE_EVIDENCE/` 保存原相對路徑，Registry snapshot 僅供血緣，僅含本交付匹配的裁定與 canonical Registry hash，
不匯出其他客戶或無關授權記錄。
檢查已解壓包時，可在上述檢查命令加 `--verify-packaged`，artifact-root 指向包根目錄。
它以目前 canonical Registry 重查、重算檔案與 NOTICE，不信任舊回執或包內 Registry。
canonical Registry 缺失時拒絕，不以 snapshot 自行補權。
可修改 customer_config 在修改後也需重新審核情境及對應 bytes，舊授權收據不能重用。

`MRL_runtime_delivery_admission_v1.py` 新增必要 license-manifest、license-context、
license-evidence-root，並保留既有所有參數。硬體、runner/runtime 來源信任、
所有 workload bytes 授權三者須同時通過；模型與 Runtime 的 id／版本／種類分別綁定。
此技術准入仍不能替代 Owner 正式交付批准。

## 風險、回復與核准

本分支增加保守拒絕，舊的 Runtime CLI 呼叫需補授權參數。
若要正式合併，須先審查本 PR 的 exact diff、三層父 PR 狀態與 CI；本次未合併。
任何未來權利啟用必須逐項展示 component/context hash、原條款、裁定、有效期、
客戶與地區、允許／禁止動作、對外宣稱、影響及回復，取得 Mr.liou 明確批准。
部署或更動母體服務另須批准；本工程沒有操作 DL580。
未啟用前可保留不用此分支或關閉 Draft PR。啟用後回復需先停用待交付包、
撤回未使用裁定並重新驗證；保留所有舊裁定／回執／SHA，不刪除歷史。
