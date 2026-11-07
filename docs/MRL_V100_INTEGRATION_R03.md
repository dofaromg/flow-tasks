# MRL V100 Admission Gate 整合補丁 R03

origin_signature: MrLiouWord
canonical_authority: Mr.liou
承接：MRL-34 / MRL-59 / MRL-63。核對日：2026-11-08（Asia/Taipei）。

本交付是供審查的程式補丁。DL580 當期 Passport、真實模型/runner/runtime
位元組、正式接受憑證、服務配置及 owner Go 均未取得；實機狀態為 UNKNOWN。
沒有連線到母體，沒有合併、部署、服務操作、driver/CUDA/韌體變更。

## 來源與承接

| 項目 | 完整 Git SHA | 結果與取用 |
|---|---|---|
| #700 | 3372f149d9efef46e6457e9e4df8e09d49f775e6 | 逐卡 SKU/CC/VRAM、精確組合、receipt bytes/hash、跨軌隔離 |
| #701 舊正文基準 | 7a480be831824788c6cb4dfe03089f8b8f2a86af | 歷史測試基準，不能代替最新測試 |
| #701 最新 | ea9c08874add64c7eaed70bc2bf7c6ecedfcc448 | 路徑分包、唯一商品 gate、before/forward/return receipt |
| #704 直接父版本 | 82b657edc314c502e365ebf1f3e3a1d3e1ae4a4e | 已包含 #700、#701 的 Git 祖先，繼續修補既有整合 |
| 兩提案共同基線 | 608b66e0db23e7cc4eef21ea752668ac800620b3 | 不用它覆寫現行 main；原分支與歷史保留 |

已讀取兩 PR 實際 patch、逐檔原碼、最新 head CI、job steps/logs、review threads，
並比較 #701 舊基準至新 head。新增 reversible-change 程式/文件/測試，清除測試未用 imports；
核心 admission 與 route builder 沒有被該提交移除。最新 head 的實際 Linux/Windows job
各跑 41 個商品測試與 2 個 orchestrator 測試成功，另有 BYOH Product CI 成功。

原始證據：

- #700：https://github.com/dofaromg/flow-tasks/pull/700
- #700 exact head CI：https://github.com/dofaromg/flow-tasks/actions/runs/41609641939
- #701：https://github.com/dofaromg/flow-tasks/pull/701
- #701 exact head CI：https://github.com/dofaromg/flow-tasks/actions/runs/41613416544
- #701 BYOH：https://github.com/dofaromg/flow-tasks/actions/runs/41613416597
- #704：https://github.com/dofaromg/flow-tasks/pull/704
- #704 hosted CI 尚為 action_required；不能把 #700/#701 綠燈搬成 #704 或本補丁綠燈。
- #700 尚有兩個未解、未過時的 CodeQL 測試未用項目；#701 三 threads 已 resolved/outdated。

## 此次補齊

1. 修復 #704 nvidia-smi CSV 把四欄解成五個變數的實際錯誤；完整六卡資料核對 UUID、
   SKU、CC、VRAM、driver 與 OS，拒絕重複 index、未知卡、非完整 inventory。
   負載平衡後、set_device 前及模型取得前沿用同一商品 gate。
2. 核對實體 bundle、runner、runtime、完整分片模型集合的 bytes/path digest。
   原生 PyTorch 路徑另外核對實際 import 位置與本程序已映射 runtime DLL/SO；
   單靠 Passport 中 loaded_* 字串無法取代這個檢查。
   尚無受審 adapter 的外部 runner/容器在 orchestrator 維持 UNKNOWN。
3. 受控 loader 只取得已驗證的本機暫存快照串流，不重開原路徑。模型來源改名替換、
   分片新增、內容改動都會在返回/登錄快取前拒絕；回收暫存檔。
   這是可信 loader 的介面契約，不能隔離惡意 Python callback 或外部直接 CUDA 程式。
4. 快取增加受控載入 provenance；舊 register_model、替換物件、不同配置、未綁定模型名
   都不能經 get_admitted_model 取得。兩個既有 engine 的模型入口不再以假模型替代缺件。
5. 不同硬體 route 不得共用 bundle digest/acceptance。接受憑證綁定 source_commit、
   bundle id/digest、track、configuration_digest 和 rollback change_id。
6. rollback 必須通過完整 before→forward→return hash chain；回復 artifact 的 size/hash
   集合必須與 before 相同，只有 state 字串一致不足以通過。符號連結、缺件或篡改拒絕。

沒有另建 collector、matrix、門禁或 builder。utils/mrl_hardware_admission.py 繼續轉接
MRL_APIWorks_BYOH_Deployment_Product_v1 的唯一准入器；正式 acceptances 仍為空。

## 套用與離線測試

在乾淨的工程 checkout 以同一 Git repository 執行（不在母體工作目錄執行）：

```bash
git switch -c mrl-34/MRL_59_V100_Integration_R03 82b657edc314c502e365ebf1f3e3a1d3e1ae4a4e
git apply --check /path/to/MRL_V100_Admission_Gate_R03.patch
git apply /path/to/MRL_V100_Admission_Gate_R03.patch
git diff --check
python -m unittest discover -s MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/tests -v
python -m unittest discover -s tests -p test_gpu_hardware_admission.py -v
python -m unittest discover -s tests -p test_mrl_hardware_admission.py -v
python -m unittest discover -s tests -p test_mrl_admitted_model_cache.py -v
python MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/scripts/MRL_verify_product_source_v1.py
python MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1/scripts/MRL_verify_package_v1.py
```

`/path/to/` 是下載補丁的位置；不屬於母體部署命令。若從 #701 套用，使用
`MRL_V100_Admission_Gate_R03_from_PR701.patch`，父版本必須為
ea9c08874add64c7eaed70bc2bf7c6ecedfcc448，禁止兩份補丁疊加。
Windows 不要完整 checkout 既有非法 Windows 檔名；沿用 CI 的 Linux git archive 精確依賴
匯出/Windows 解壓測試，不改原名或停用 Git 路徑安全機制。

## 依賴與快取銜接

- 政策、hash、snapshot、receipt、建包及合成測試：Python 3.10+ 標準函式庫；CI Python 3.12。
- 實際 GPUOrchestrator：現有 PyTorch、PyYAML、nvidia-smi 與原驅動/CUDA；不安裝或升級。
- engine 尚依賴原有 numpy/模型實作；本補丁不提供權重、GPU binary 或授權。
- native PyTorch runtime digest 必須是本程序實際載入的 DLL/SO 單檔；runner 可為
  包含 torch.__file__ 的完整唯讀目錄。其他 backend/image 平台綁定待 adapter 審查。
- loader 使用 ModelCache.load_admitted_model(name, loader, **inputs)。loader 的唯一輸入
  是 {相對 shard 名: 可 seek 的唯讀串流}，單檔 key 為 `.`；不得自行下載或重開原件。
- 聚合模型的 workload.model.components 可列出經審查的快取名稱；整個 model 目錄 digest
  綁定所有元件。修改 components 會改變 configuration_digest，必須重新驗收。
- 權重格式/真實 loader 未提供時不自動猜測 torch.load 或執行 remote code；維持 UNKNOWN。

## 部署前驗收與操作審查

MRL-44 的當期唯讀 Passport 是唯一採集來源，不重建平行 collector。
必須補齊逐卡 UUID/SKU/Board PN/VBIOS/PCI ID/CC/VRAM、OS build、ROM/iLO、driver model/version、
Toolkit、實際 loaded CUDA/runtime ABI、runner、quantization、model/bundle/config/service digest。
nvidia-smi 顯示的最大 CUDA capability 不作為實際 Toolkit/runtime。

在母體本地保留原始 stdout/stderr、exit、時間、工具版本與 immutable evidence 副本；
任何缺件維持 UNKNOWN。不得把本機合成 fixture、Windows 2022 CI 或歷史 539.56 快照登錄為新接受憑證。

逐項產出同一 change_id 的審查包後，才向 Mr.liou 提出具體 Go：

| 操作 | 必填的實際參數與停止條件 | 風險與回復 |
|---|---|---|
| 隔離 GPU/model smoke | 已 hash 的 runner 絕對路徑、固定輸入/seed/精度、輸出 digest/容差、timeout | GPU 記憶體/負載；失敗立即停止候選，不碰原服務 |
| 服務切換 | 當期實測 service 名、before binary/config pointer、候選並列目錄、精確 argv、停止/啟動/health 預期 exit | 未驗收配置會拒絕分配；只切指定服務，保留舊 pointer 與 immutable 副本 |
| session/job replay | 已封存 session/job/input 的 hash、API 端點、預期輸出/容差、timeout | 模型數值/記憶回歸；失敗停止後續並照核准 return 回切 |
| return 演練 | before bundle/config/service definition 的 bytes/hash、逐步反向 argv | 恢復原 pointer 與配置、啟動舊服務、重跑同一 smoke/health/session/data 檢查 |
| 正式啟用 | forward PASS、return PASS、核准後再 forward PASS 的完整回執 | 任何 UNKNOWN/失敗不得啟用；receipt 不自動授予部署權 |

本次無當期 service PathName、候選 runtime/model bytes 或 before 配置，故不產生猜測的
Restart-Service/sc.exe/systemctl 命令，也不請求空白授權。下一次審查必須顯示帶實參的命令、
風險、回復與停止條件。driver、CUDA、ROM/iLO 變更另案；不包含在預設 forward。

可先執行本地的政策 CLI；只有 exit 0 表示准入，exit 1/2 都必須阻擋。
smoke/replay 繼續沿用 MRL_hardware_smoke_v1.py 和 MRL_capture_node_evidence_v1.py，
具體 GPU/model 命令經 owner 核准後才執行。before/forward/return 繼續由
MRL_reversible_change_v1.py 產生 create-only receipts；metadata/人工 passed 字串不能替代原始執行紀錄。

內部精確硬體接受、來源測試通過、正式合併、實際部署與公開支援分別審查。
此補丁可交付，MRL-34/MRL-59/MRL-63 尚不能因此標記 Done。
