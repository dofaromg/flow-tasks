# MRL FLPKG Local v1

`origin_signature: MrLiouWord` · `canonical_authority: Mr.liou` · GitHub [#711](https://github.com/dofaromg/flow-tasks/issues/711)

本機工作台可執行粒子邏輯鏈、獨立封裝生成結果或來源目錄、吸收本地 ANE 診斷、查詢與管理工作、驗證 ZIP 及還原檔案。Python 3.10+，使用標準庫，不須 pip、雲端金鑰或 GPU。原始粒子邏輯由既有 `LogicPipeline.simulate()` 執行，屬粒子邏輯運算。iPhone ANE 診斷匯入不會呼叫 Apple 私有服務。

## Windows Server／DL580

將 ZIP 解壓縮至新目錄，例 `D:\mrl\MRL_FLPKG_Local_v1`。資料目錄使用本機 NTFS 並授予啟動帳戶讀寫權限。工作台預設以前景執行，視窗關閉後可重啟。使用 PowerShell：

```powershell
Set-Location D:\mrl\MRL_FLPKG_Local_v1
.\Start_MRL_FLPKG.ps1 -Data D:\mrl\mrl_flpkg_data -Port 8765
```

也可直接執行：

```powershell
py -3 -X utf8 .\mrl_local.py --data D:\mrl\mrl_flpkg_data serve --port 8765
```

在 DL580 本機瀏覽器開啟 `http://127.0.0.1:8765/`。先提交「粒子生成」，填入一段文字。狀態顯示 done 後，複製工作 ID，提交「FLPKG 封裝」並貼到「生成工作 ID」。封裝完成後按「驗證」，成品在資料目錄的 `artifacts\`。

## macOS／Linux

```sh
sh ./start_mrl_flpkg.sh --port 8765
python3 -X utf8 mrl_local.py --data /path/to/mrl_flpkg_data serve --port 8765
```

以上兩種啟動方式擇一。第二種可指定資料目錄。預設資料在 `$LOCALAPPDATA/MRL_FLPKG`（若存在）或 `~/.local/share/MRL_FLPKG`。工作台與 API 只監聽 127.0.0.1，使用本機會話 token，適用於信任的本機操作環境。部署請使用支援 hard link 與 SQLite 檔案鎖的本機檔案系統，例如 NTFS、APFS 或 ext4。Git 工作樹上可直接執行；ZIP 包含固定版本的上游檔案。

## CLI 與驗收

```sh
python3 -X utf8 mrl_local.py submit generate "MRL 粒子"
python3 -X utf8 mrl_local.py worker --once
python3 -X utf8 mrl_local.py submit package --source-job GENERATION_ID
python3 -X utf8 mrl_local.py worker --once
python3 -X utf8 mrl_local.py verify-job PACKAGE_ID
python3 -X utf8 mrl_local.py inspect /path/to/artifacts/PACKAGE_ID.flpkg.zip
python3 -X utf8 mrl_local.py extract /path/to/artifacts/PACKAGE_ID.flpkg.zip /path/to/new-directory
python3 -X utf8 mrl_local.py submit diagnostic /path/to/local.ips
python3 -X utf8 mrl_local.py worker --once
python3 -X utf8 mrl_local.py status
python3 -X utf8 mrl_local.py quota 10737418240 deny
python3 -X utf8 -m unittest -v
```

Windows 可將 `python3` 替換成 `py -3`。各命令需使用同一個 `--data`（如需指定，放於子命令前）。`serve` 已啟動背景 worker；獨立 `worker --once` 用於未啟動工作台的 CLI 驗收。重新封裝時可指定 `--options '{"label":"R02"}'`，用原生成 ID，無須重跑生成。目錄封裝時直接提供來源路徑；它須與工作台資料目錄分離。舊版重建器名稱及介面保留。工作台自身的檢視和解包支援舊 SHA-1 manifest，新增封裝另有 SHA-256。

## 寫入政策與復原

- 每個資料目錄是一個 worker 與配額範圍。SQLite 跨程序租約令同資料目錄只有一個工作執行，其餘工作留在佇列。不同 worker 可使用不同資料目錄。
- 配額使用滾動 24 小時的應用程式輸出 bytes。入場先保留，分塊在寫入前入帳，失敗或重啟不退回已入帳的嘗試，未用的保留會釋放。ZIP 使用儲存模式與保守的頭部上界，設定上限時要留封裝開銷。計量涵蓋生成、快取副本、封裝及診斷輸出。SQLite、系統與手動解包的 I/O 在此範圍之外。
- `alert` 記錄超限並允許執行；`queue` 等待已使用額度釋放（約每 30 秒重試），單件高於上限直接拒絕；`throttle` 超限後按設定速率寫入；`deny` 拒絕。新配置影響下一次入場，當前工作保留原入場決策。
- 輸出先進 `stage`、寫入同步、讀回核對，再發布至 `artifacts`。工作中斷後重啟會核對已發布成品並處理暫存，未完成工作標為 interrupted。用重試建立子工作，原工作與事件保留。
- 緩存鍵包括種子內容 SHA-256、生成程式與常數檔 SHA-256、Python 版本、主機架構、target 及 canonical JSON options。target 和 options 屬工作上下文，不改寫上游邏輯。暖命中略過生成，仍寫一份獨立輸出。讀回比對持久紀錄後才可使用快取，損壞項目移至同目錄的 `.invalid.*`。
- SQLite 與資料目錄同時備份。停機後將整個資料目錄備份至本機安全位置；復原時選新目錄啟動，保留原資料。日誌與工作歷史以 SQLite 保留，檔案與暫存均留在本機。

## 診斷邊界與譜系

診斷只讀本機原始檔，輸出原始 SHA-256、已解析欄位、衍生量與推論欄位。速率比不可當成每日累計超額，pageins 不等於實際檔案讀取，私有函式庫共現不能證明一條呼叫鏈。原檔由操作者保管，未知欄位不修改、不拷貝到分析 JSON。測試使用合成診斷。

上游固定基準 [608b66e0](https://github.com/dofaromg/flow-tasks/tree/608b66e0db23e7cc4eef21ea752668ac800620b3)。ZIP 內 `particle_core/src/logic_pipeline.py`、`pipeline_constants.py` 及 `下載重建器腳本MRLiou_FLPKG_Rebuilder.py` 保留原名及位元組。GitHub 內的操作模組引用既有核心路徑。已驗證本地 Linux，Windows Server／DL580 實機驗收須在目標主機執行。
