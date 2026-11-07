# MRL 本地安裝交付 R03

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
parent: MRL_Financial_Core_v1  
日期：2026-11-07（Asia/Taipei）

此 Python 模組的替代建置路徑為 GitHub Actions → Windows／Linux 獨立 ZIP →
本地離線驗證、安裝及自測。執行時不依賴 Cloudflare Pages、Workers、Next.js 或 OpenNext。
原站台的 Cloudflare 建置紀錄保留，不能把它的失敗改名成成功，也未修改其他站台的部署設定。

## 安裝包的實際內容

- 原本母體目錄結構下的帳本、外部接頭、測試、原始來源、版本與文件。
- 原 ToolRegistry 與母體 module_registry，供本地接回既有模組時核對。
- 按目標作業系統下載的實際依賴 wheels，包含原生程式庫；不是 requirements 清單取代依賴。
- requirements.lock，每一項固定版本及 wheel SHA-256；安裝使用 --no-index、--require-hashes。
- PACKAGE_MANIFEST.json，逐檔名稱、大小、SHA-256、總數與來源 commit；ZIP 另有 .sha256。
- Windows／Linux 安裝入口及 bootstrap.py 的 verify、install、self-test、ledger、external 命令。

Python 3.12 x64 解譯器必須先存在；ZIP 不含 Python 安裝程式。此包不是 Windows 服務，
也不會自動啟動金融操作、修改既有母體檔案或取得新帳戶權限。
ABI／平台不同的 ZIP 不可混用；Mac 與其他 Python 版本未在此版驗收。

## 使用步驟

1. 從 PR 對應的 MRL Financial Core workflow 成功執行下載自己的作業系統 artifact。
2. 依 GitHub 回執核對 ZIP SHA-256，解壓至新的版本目錄；ZIP 與 .sha256 留在目錄外。
3. Windows 執行 MRL_INSTALL_WINDOWS.cmd；Linux 執行 sh MRL_INSTALL_LINUX.sh。
4. 安裝器先核對所有檔案，再於該版本目錄建立 .mrl-finance-venv，用內附 wheels 離線安裝，
   執行 50 項帳本、連接器及套件完整性測試。全部成功才產生 MRL_INSTALL_RECEIPT.json。

如果 Windows 沒有 py launcher，可用已安裝的 Python 3.12 執行：

```text
python MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/delivery/bootstrap.py install
```

重複安裝會拒絕覆寫既有 venv／回執。請使用新的版本目錄；不會替你刪掉舊版或金融資料。
原帳戶設定、根授權登錄、銀行 Token、個案資料及外部操作 journal 應留在原本受保護位置，
不包含於安裝包，亦不會被此安裝器替換。保留上一版即可回退模組程式；帳務回退須另依原事件鏈處理。

## 安裝後入口

```text
python MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/delivery/bootstrap.py verify
python MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/delivery/bootstrap.py self-test
python MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/delivery/bootstrap.py ledger -- --help
python MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/delivery/bootstrap.py external -- --help
```

verify 拒絕缺檔、多檔、空檔、雜湊／大小不符、路徑逃逸、名稱碰撞及 symlink。
安裝環境與安裝回執是產生的本地狀態，與原始套件清單分開。來源樹不應放入 bytecode cache。
ZIP／manifest 校驗證明內容一致性，不能取代來源信任、相依授權與獨立安全審查。
已安裝 venv 的後續變更不在原始 ZIP 校驗範圍；GitHub exact-head CI 的驗收對象是乾淨的新安裝。

ledger／external 命令使用安裝好的版本環境；外部命令保留操作者環境中明確配置的 Token，
安裝與自測則清除該 Token，並只使用模擬 provider。既有所有權、根授權、逐筆簽核及直播環境限制保持有效。
即使安裝成功，也不代表任何銀行／錢包已接通、交易已結算或 DL580 已驗收。

## 建置與驗收

CI 明確 checkout PR head，於 Linux 上輸出必要原始碼後，把同一份原始碼交給兩個平台。
各平台下載 wheels、建立 ZIP、CRC／逐檔讀回校驗、解壓至新目錄，再真正用 ZIP 內的依賴離線安裝並自測。
只有這條完整路徑成功才上傳可下載的 ZIP、SHA-256 與安裝回執。完整來源與校驗紀錄回填原 PR #713。

本地工作目錄的測試包標記 WORKSPACE_SNAPSHOT；GitHub checkout 的包標記 GITHUB_EXACT_HEAD。
不能把本地未提交來源冒充某個 Git commit 的精確成品。source_sha 必須與對應 PR／workflow 原始碼版本一起核對。
