# MRL Runtime Trust 本地伺服器驗收套件 v1.1.0

origin_signature: MrLiouWord  
canonical_authority: Mr.liou

此版本承接 flow-tasks PR #706 的真實驗證引擎，增加可運行的本地操作介面、HTTP API、Windows/Linux 啟動程式、離線完整性驗證及本機驗收收據。原模組名稱與父子目錄保留；母 Runtime 來源一併交付。

## Windows／DL580 開始使用

1. 將 ZIP 解壓到**全新的目錄**，例如 `D:\mrl\acceptance\MRL_Runtime_Trust_Local_v1_1_0`。不要覆蓋現有服務目錄。
2. 需要 Python 3.10+ 與 OpenSSL 3+。不需要 pip、Node、npm、雲端金鑰或外部網站。若既有 Git for Windows 提供 OpenSSL，驗證引擎會自動尋找。
3. 雙擊根目錄 `Start_MRL.cmd`。程式會打開本機操作台，預設 `http://127.0.0.1:8766`。每次啟動附有不同的工作階段登入片段；請用啟動視窗提供的完整網址。
4. 點「執行完整範例」：實際驗簽、離線重播、修改 digest 後拒絕。完成後點「下載證據 ZIP」。範例使用臨時測試金鑰，未改動正式政策。
5. 點「執行本機測試」或雙擊 `Run_Local_Acceptance.cmd`。後者同時核對完整交付包、來源與母 Runtime 清單，並產生帶本機名稱的收據。
6. 收據保存於根目錄 `MRL_local_data\receipts`，命令列驗收保存於 `MRL_local_data\acceptance`。關閉時在啟動視窗按 Ctrl+C。

若 Python 沒在 PATH，可在 CMD 執行：

```bat
set "MRL_PYTHON=D:\YourPython\python.exe"
Start_MRL.cmd
```

要讀取既有 `D:\mrl` 內的檔案，可在套件根目錄執行：

```bat
Start_MRL.cmd --evidence-root D:\mrl --state-dir D:\mrl\acceptance_receipts --port 8766
```

亦提供 PowerShell：`local_console/MRL_Start_Local.ps1`（位於保留的商品目錄內），支援 `-PythonPath`、`-EvidenceRoot`、`-StateDir`、`-Port`、`-NoBrowser`。若本機 PowerShell 禁止 script，直接使用 CMD 啟動器即可，不必放寬機器的執行政策。

## Linux

```sh
sh Start_MRL.sh
# 指定既有證據目錄
sh Start_MRL.sh --evidence-root /srv/mrl --state-dir /srv/mrl-acceptance --no-browser
```

預設只監聽 loopback。遠端操作可使用你自己的 SSH tunnel：`ssh -L 8766:127.0.0.1:8766 your-server`，再使用伺服器啟動時提供的工作階段網址。此程式不修改防火牆、不新增外部公開端點。

## 實際檔案驗證

將自己的 Runtime、Manifest、SBOM、provenance 放在 evidence-root 內。操作台欄位可填相對路徑或範圍內的絕對路徑，不能藉符號連結跳出目錄。

| 操作 | 必要輸入 | 實際執行 |
|---|---|---|
| Runtime 來源驗證 | Artifact Trust Manifest、產物目錄、release/canary | 呼叫原始來源信任引擎；當前正式政策固定來自商品 trust 目錄 |
| 來源重播 | Manifest、原始 trust receipt、產物目錄 | 重算雜湊、重新驗簽，與當前正式政策比較 |
| 組合准入 | 當期 host/Passport、workload、artifact-paths、runner/runtime manifests、產物目錄 | 同時執行既有硬體與來源信任門禁 |
| Gateway 本機驗收 | 本機 Gateway URL、既有 Runtime 資料目錄 | 沿用 `MRL_capture_node_evidence_v1.capture`，建立驗收 session、呼叫模型、讀回記憶及交易證據 |
| Gateway 重播 | 再填先前 node receipt | 核對相同主機、gateway、session 與持久化資料；可在手動重啟 Gateway 後執行 |

Manifest 精確欄位與 SBOM／provenance 格式見 `docs/MRL_ARTIFACT_TRUST_v1.md`。來源收據是 `MRL_Artifact_Trust_Receipt_v1`；操作台外層收據為另一層工作紀錄，兩者不混用。下載 ZIP 內 `evidence/MRL_TRUST_RECEIPT.json` 可給原引擎重播。Gateway 重播則使用外層收據中的完整 `node_evidence` object，另存 JSON 後填入欄位。

首次 Gateway 驗收會在你指定的既有 Runtime 新增驗收 session 及記憶／交易事件。這是點擊該操作後執行的資料寫入，不會啟停模型、重啟服務、安裝驅動或更改埠號。只應指定你要驗收的本機服務與資料目錄。Gateway 預設為 `http://127.0.0.1:7811`；保留 Bridge 3000 及既有服務。

## 驗收邊界

本套件程式、操作介面、母 Runtime 及測試完整交付。Python/OpenSSL 必須使用本機已有安裝；模型權重、GPU 驅動、PyTorch 與真實上游 runtime binaries 不包含於此來源套件。母 Runtime 的既有啟動／設定腳本保留在其原始路徑，若你已有服務，可直接使用操作台驗收，不必重建。

- 範例／單元測試 PASS 是工程結果，不會授權任何第三方 Runtime。
- 正式信任政策仍是 `keys=[]`、`artifacts=[]`；操作台不提供政策放行或金鑰輪替按鈕。
- LiteLLM 1.106.6 的 cosign profile 尚無 adapter，真實 upstream image digest、簽章及 SBOM/provenance 尚未補齊；保持未驗證，不能用範例代替。
- Gateway 往返可留下實際模型／主機資料，但母體重啟、GPU 硬體煙霧測試、MRL-32 隔離及客戶交付各自驗收，不能僅因 UI 出現綠色就認定全部完成。
- 原始簽章與來源門禁、origin_signature、版本歷史均保留；無正式合併、部署、安全政策解除或憑證輪替。

## 離線校驗與故障排除

```sh
python MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1/local_console/MRL_verify_local_package_v1.py .
```

`MRL_PACKAGE_MANIFEST.json` 保存逐檔 size/SHA-256、exact source commit 與依賴樹；`MRL_Package_Expected_File_List.txt` 保存完整名單。校驗會列出 Missing／Extra／Mismatch／Coverage。只允許 `MRL_local_data`、`MRL_runtime_data` 、商品目錄內的 dist 測試輸出與 Python cache 作為執行後新增資料。

- 埠號被占用：傳入 `--port 8767`；不會停止佔用中的服務。
- 403：使用同一次啟動所印出的完整網址；重啟後舊 token 失效。
- 路徑超出範圍：重新啟動並指定正確 evidence-root。
- OpenSSL unavailable：使用本機 OpenSSL 3+ 或既有 Git for Windows；不會自動下載未知執行檔。
- 驗證拒絕：查看 `decision.reason`，補齊產物與來源證據；不要把正式政策換成下載包內的測試政策。
- 瀏覽器／斷線：工作繼續執行，重新整理後可在「已保存收據」讀取結果。

所有輸入留在本機；不載入外部字型、CDN 或追蹤程式。API 需要啟動當次 token，拒絕其他 Origin／Host；不接受任意 shell 指令。所有收據使用獨佔建立及讀回雜湊，下載 ZIP 再做完整內容比對。
