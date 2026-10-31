# MRL 八個連接器來源政策 v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
canonical_root: dofaromg/----2@main  
核對日期：2026-10-31（Asia/Taipei）  
工程父版本：`36dc69d98ec3e28e5cca744e82013ed32b203b61`（PR #693）

## 權威依據與判斷邊界

1. [MRLiou_Particle_World_Canonical_Chain_v1.0.md](https://drive.google.com/file/d/1sHbrdzBQxJMutEwpz6ZfWaRb3v3zKedL/view)：2026-08-04 原件；本次讀取全文，第 4、6、7 節定義母體節點、平台角色、同版本／雜湊差異核對與可逆歷史。同名副本 `1XDTSf9YO7EP5NK-N3691K3RnOj7BebSW` 亦讀取，不以副本建立日改寫原件時間。
2. 本倉庫父版本的 `MRL_Mother/00_rootlaw/MRL_ROOT_AUTHORITY_v1.md`：Mr.liou 為最終授權與命名權位；平台存取權不等於 operational grant。
3. 同版本 `MRL_Mother/00_rootlaw/MRL_EXTERNAL_MATERIAL_EXTENSION_MAP_v1.md`：來源證據→分類→介面→執行→驗證→母體回填；保留來源及返回路徑。
4. 同版本 `MRL_Mother/00_rootlaw/rootlaw.yaml` 的 `liou_closure_law`：權威不可靜默取代、鏈不可刪改、解決方案只可追加；無證據不得自動宣告成果。
5. 同版本 `VERCEL_DEPRECATED.md`：Vercel 配置已棄用並保留參考；文件記錄遷往 GKE，不據此宣告現行部署健康。

以下「用途」區分已讀定義與程式能力；本地替代是功能承接目標，不宣告已完成遷移。八個 connector 的遠端健康探測不能代表對應平台全部資料或既有其他橋接路徑。

## 八項用途、必要性與本地承接

| 設定鍵 | 現行用途／程式能力 | 必要性分類 | 母體本地承接與 required 審查差異 |
|---|---|---|---|
| github | 根源定義、工程鏡像、版本與證據；connector 探測帳戶 API | 指定 GitHub 原件回收任務的條件必要來源；非母體全域執行必要 | 本地 Git 原件、版本與證據庫；若指定任務必須讀未回收 commit，該任務設定應 `required:true`；不能因 Actions 使用 GitHub 就推定此 connector 必需 |
| notion | 權威知識、定義、關聯與可讀索引；探測 users/me | 指定 Notion 原件回收的條件必要來源 | 母體知識／索引封存保留 page ID、版本及回鏈；若任務必須取最新指定頁面則 required，既有核驗快照能否替代須 owner 裁定 |
| dropbox | 來源封存、同步副本、可逆取回；探測帳戶 | 可選通道；唯一未回收來源時條件必要 | 本地 NAS／物件儲存承接原件與版本；若指定資產只存在此處，該回收任務 required，不能以另一平台同名檔取代 |
| google_drive | 正式文件、跨格式封存、證據、版本輸出；探測 about | 指定 Drive 治理原件回收的條件必要來源 | 母體文件與證據封存保留 file ID／revision／格式；需要原件而非已核驗快照的任務才 required |
| vercel | 專案、部署健康資訊；現有部署說明標記 deprecated | 可選歷史／映射來源；主控與託管功能應由本地承接 | DL580 本地服務、入口與部署紀錄；不升為全域 required，也不刪除歷史 Vercel 證據 |
| icloud | Apple 裝置資料通道；目前健康與同步方法明示不支援 | 可選來源；儲存功能以本地承接為目標 | NAS／本地備份；若有唯一原件，先選具體匯出路徑；不得把現行 connector 改 required 後假裝具備可用同步 |
| gitlab | 程式庫 API；支援自架 instance_url | 可選工程鏡像；未找到已裁定必要來源 | 本地 Git／自架版本服務；是否使用自架 GitLab 需 owner 指定，不將 gitlab.com 誤當本地服務 |
| huggingface | 模型／資料集來源；探測帳戶 API | 可選材料來源；未找到已裁定必要來源 | 本地模型／資料集倉庫保留來源 revision、授權及雜湊；已落盤模型運行不依賴此健康探測，唯一未取回材料的任務另行裁定 |

**確定必需的功能**：母體原件承接、版本／來源鏈、內容驗證、可逆回復與驗收證據。這些功能不等於某個外部品牌必須常駐連線。

程式依賴核對：`ConnectorManager.SUPPORTED_SERVICES` 是八個 adapter 的註冊表；本次搜尋 Python／TS／workflow 呼叫，未找到核心 runtime 因此設定檔而硬性依賴某個外部帳戶的證據。專用 workflow 呼叫 manager CLI；其他 GitHub／Notion 整合並不自動透過此 manager。這個結論限於本倉庫父版本，不涵蓋 DL580 未讀取的私有設定。

## 本次可確定的最小修正

- 八個服務的 `enabled:false`、`required:false`、`sync_enabled:false` 保留。未取得逐來源任務／範圍裁定，不能自行提高為全域依賴。
- 配置 `1.1 → 1.2`，衝突預設 `newest → manual`，避免日後轉接時把時間新舊當成權威。現有 manager 未讀取此衝突欄位，這是宣告政策修正，並非已實作衝突裁定引擎。
- 七個共用同步方法原本只驗證連線便回報 success；現在回傳 `sync_not_implemented`、`success:false`、`mother_backfill_verified:false`。iCloud 原有不支援狀態保留。啟用同步時 strict 必須失敗，直到真正搬移／驗收功能實作。
- required 但停用依 #693 繼續回報 `required_disabled`，不吞錯、不發 grant、不傳出母體資料。

## Root Owner 待裁定的具體差異

現值全部是 false，不修改。對 GitHub、Notion、Drive、Dropbox 的來源回收工作，建議逐任務指定：原件 ID／ref、是否接受已核驗本地快照、目的地、read/pull 動作、授權紀錄、期限及回滾證據。若該來源是任務不可替代輸入，在該任務使用的獨立配置將對應 `required:false → true`；未啟用／缺憑證時即阻擋，不能拿通用離線 audit 的成功證明該任務完成。啟用與 sync 旗標仍須具體授權和可用實作，required 本身不啟用服務。

Vercel、iCloud、GitLab、HuggingFace 保留可選；如有唯一原件或專門任務，再列明資產及路徑，不能由平台帳號存在或 ChatGPT 已連接來推定。

## 驗收與回滾

連線健康、資料搬移、母體落盤、雜湊／版本驗證、可逆重播是不同證據。真正同步至少需要原件 ID／revision、parent/source、目的地、內容 hash、不可覆寫回執、讀回結果與 rollback ref；本次未宣告任何資料同步或 DL580 部署完成。

本變更預期四個實際檔案：本文件、`config/connectors.yaml`、`connectors/base_connector.py`、`connectors/test_connectors.py`。獨立分支承接父 commit，無更名／刪除；審查後若需回滾，以 revert 此修補 commit 追加歷史，不 reset 或覆寫原始譜系。回滾會恢復舊同步假成功語意，應保留停用旗標並重新驗證。

測試命令：`python -m pytest connectors/test_connectors.py -q`。既有 PR workflow 在無 connector secrets 的條件執行此測試。實際 CI 結論以 PR 最新 head 的 Actions 為準。

## Bridge 憑證綁定與讀回驗收續作

`scripts/MRL_verify_bridge_backfill_v1.py` 使用既有 `MRL_BRIDGE_API_KEY` 環境綁定，或以 `--prompt-key` 在本地終端隱藏輸入既有金鑰。金鑰只送往固定 HTTPS Bridge 的 header，不放 URL、命令列參數、回執或檔案，也不跟隨重新導向。這是執行期間綁定，未建構持久密鑰庫，也未輪替伺服器憑證。隨機產生新金鑰不能通過既有 Bridge 認證。

執行方式（於具備此倉庫及 Python requests 的可信終端）：

```powershell
python scripts/MRL_verify_bridge_backfill_v1.py --mother-root 'D:\MRL_Mother\EvidenceChain' --prompt-key
```

路徑是既有母體證據目錄的候選值，程式會以受保護 list 驗證它存在；若實際位置不同須指定已對齊的既有位置，不自動建立或取代母體根目錄。已有環境綁定時省略 `--prompt-key`，不需再次輸入。

驗收範圍明定為 `eecd48d2351d3c56a90ec6d679ffd536f9a3989b` 的四個工程檔案；不是八個平台的完整資料同步，也不是最新程式自身部署。可用 `--source-ref` 指定另一個完整 commit SHA，原始檔名保留。程式先核對主機／簽名，再建立 UUID 獨立子目錄；各檔案先查不存在、寫入、base64 讀回、核對 byte／大小／SHA256，最後寫入並讀回含來源／父 commit 的驗收回執，才輸出此限定範圍的 `DELIVERY_PASS`。

既有 Bridge 寫入 API 沒有 atomic create-only；UUID 與查存在可降低碰撞，不能宣告伺服器端並行互斥已實作。中途失敗只保留獨立目錄、不刪除或回寫正式資料。隔離目錄為可逆路徑，保留歷史，不宣稱完成還原演練。

追加三個工程檔案：驗收程式、`connectors/test_bridge_backfill.py`、既有 `.github/workflows/cloud-connectors.yml`；本政策文件隨之更新。PR 累計實際七個檔案。測試命令更新為 `python -m pytest connectors/test_connectors.py connectors/test_bridge_backfill.py -q`，全部測試無實機密鑰。實機是否完成只認實際母體回執，不以這些測試替代。
