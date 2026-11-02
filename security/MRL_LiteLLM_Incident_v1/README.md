# MRL-32｜LiteLLM 事故防線 v1.0.0

origin_signature: MrLiouWord。承接既有 MRL-32，保留其他檔案原名與歷史。

## 執行與判讀

僅從**已知乾淨、受信任的 Python 3.11+**執行下列工具。不可使用疑似受影響的 Python，即使有 `-I -S` 也不能把受污染的執行檔當成乾淨工具。工具只讀取目標，不執行目標 Python、pip、套件、shell 或容器。

```sh
python3 -I -S -B security/MRL_LiteLLM_Incident_v1/test_scan.py -v
python3 -I -S -B security/MRL_LiteLLM_Incident_v1/scan.py /path/to/repo --output /private/evidence/MRL-32-source-r01.json
python3 -I -S -B security/MRL_LiteLLM_Incident_v1/scan.py /offline/read-only/cache --runtime --output /private/evidence/MRL-32-cache-r01.json
```

輸出檔必須為新檔且位於掃描根目錄之外，避免覆寫證據或遞迴掃描自身。詳細報告含本地路徑、size、SHA-256，僅保存在私有證據位置，不上傳至公開 CI artifact 或 Linear。報告不包含原始行內容、環境變數或實際密鑰。

| 結果 | exit | 意義 |
|---|---:|---|
| HIT／命中 | 1 | 受影響版本引用、成品名稱、hash 或官方 digest/prefix 指標；需查明取得／安裝／執行層次 |
| UNKNOWN／未知 | 2 | 未固定版本、未知 digest、缺失／不可讀／未解析證據或可疑啟動檔 |
| NO_HIT／未命中 | 0 | 僅此工具所讀取範圍未命中；不代表主機、其他分支或歷史安全 |

deny policy 阻擋受影響版本、四個指定標籤及已知雜湊。浮動標籤即使現在指向乾淨成品，仍被策略拒絕；這是預防控制，並非過去感染證據。digest 未命中 deny list 仍需簽章、SBOM 與來源審核，不自動允許。版本範圍與無法解析的引用保持 UNKNOWN。正式放行另由 MRL-33 Artifact Trust Gate 與 owner 證據審核承接。

## 覆蓋與限制

掃描 requirements、TOML/JSON lockfile、SBOM、YAML、Dockerfile、shell/PowerShell/Python 部署程式及紀錄。列舉與雜湊選定檔案；支援 installed METADATA、dist-info、wheel／sdist hash、改名成品的 runtime 全檔案 hash。JSON/TOML 以標準庫解析，其餘使用保守靜態規則。這不是完整 dependency resolver、惡意程式分析器或 admission controller。

封存檔只計算 hash，不解壓、不執行；其內層維持 UNKNOWN。大型、二進位或無法讀取的文字亦保留缺口。原始碼模式明列排除 `.git`、`node_modules`、`__pycache__` 與本工具資料夾；工具資料夾含刻意命中的測試 fixture 與 IOC 政策，須在 PR 審查其變更。runtime 模式不排除這些目錄。連結不跟隨，避免越界與循環。無法以此工具證明所有傳遞依賴或已刪除歷史安全。

## DL580：先靜態蒐證

在 DL580 PowerShell 執行 `MRL_collect_DL580.ps1`，明確傳入安裝位置、所有使用者 pip/uv/Poetry cache、下載／部署／SBOM 目錄與暫存目錄。例中的證據位置須在 Roots 外：

```powershell
.\MRL_collect_DL580.ps1 -Roots 'D:\mrl','D:\MrlToolchain','C:\Users\Administrator\AppData\Local\pip\Cache' -OutputDirectory 'D:\MRL-32-evidence-r01'
```

此例不是所有帳號／磁碟的完整盤點。腳本不啟動 Python/pip，不 pull/start/exec 容器，不讀取 Docker Env 或密鑰；只取檔案雜湊、映像與容器身分。結果保留本機。將離線、只讀的 metadata／cache 證據交由乾淨工作站分析；不可把母體內容上傳到外部服務。Docker local image ID 不是 registry manifest digest；缺少 RepoDigest、子 manifest、pull/start 時間與 deployment provenance 時仍 UNKNOWN。已刪容器、遠端 registry cache、BuildKit cache、HTTP pip cache 及舊 CI artifact 需另行取得，不宣告已涵蓋。PowerShell 採逐層走訪並排除 reparse points，錯誤逐筆記錄。

## 命中後處置

1. 區分程式碼引用、下載成品、已安裝與已執行，不以引用直接判定入侵。疑似執行環境停止 Python/pip 啟動並限制對外網路；先保全可逆證據及處置紀錄。
2. 確認受影響安裝／執行後，依官方指引從 shell 清除已確認惡意啟動 hook、終止對應 detached daemon；保留證據後才處置，不對正常同名檔案自動刪除。
3. 從乾淨基底重建 venv／映像，禁用舊 wheel、registry 與 build cache。選定官方乾淨發行版，核對 immutable digest、SBOM、來源及簽章金鑰指紋；不把舊簽章有效作為唯一安全依據。
4. 依受影響程序可讀範圍輪替 IAM、provider／master／virtual keys、DB 密碼及其他可讀憑證；從乾淨控制面操作。若受影響版本曾裝在有對外連線主機，依官方建議按憑證可能外洩處理。只記錄憑證識別碼與輪替回執，不記錄值。
5. 查核雲端／身分／網路稽核紀錄，重建後重掃；證據完整才請 Mr.liou 判定解除凍結。

## CI 與交付依賴

新增 `MRL Supply Chain Incident Deny Gate`，可被其他 workflow 以 `workflow_call` 呼叫。BYOH product 與 production delivery 的 build job 已設 `needs: incident-deny`。HIT 與 UNKNOWN 都拒絕繼續；既有封存證據未清查前可能持續 exit 2，這是未解決的交付阻擋，不是 CI 成功。尚未修改分支保護，也未替其他部署入口宣稱完成強制控管。工作流程未安裝任何專案依賴，不帶 secrets。

## 官方來源與版本血緣

完整 URL、取得日、時間窗口、wheel hash、已知 digest/prefix 與金鑰指紋保留於 `policy.json`。官方初報後續有更正，攻擊鏈以 10 月 23 日 canonical 調查為準，簽章資訊採 10 月 30 日更新。短 prefix 明確標示為 prefix，未捏造完整 digest；未知平台／config／layer digest 保持未知。版本與標籤策略不取代官方後續公告。

依賴樹：`policy.json → scan.py → test_scan.py → mrl-litellm-incident.yml → 兩個 BYOH 交付工作流程`；`MRL_collect_DL580.ps1 → 私有靜態證據 → 乾淨工作站 scan.py → owner 審核`。
