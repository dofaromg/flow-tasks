# MRL_Video · 本地解說影片製作模組

origin_signature: **MrLiouWord** · canonical_authority: **Mr.liou** · version: **1.2.0**

把來源文字、分鏡及本地片段轉成真正的 H.264/AAC 影片，保留來源、版本、字幕、素材與交付證據。
All production runs locally. No cloud model, external API, CUDA runtime or downloaded media is required.

## 與既有系統的關係

- 延伸 `main_ultimate.py`／`README_ULTIMATE.md` 的影片用途；既有服務及原命名保留。
- 對應母體介面已存在的 `MRL_VideoGen` 工具識別；本次沒有冒稱已改動該介面路由。
- 以錄影中的 **Video explainer maker** 工作流程為參考，獨立實作本地執行器，不執行外部 YAML。
- canonical Bridge 的 `/MRL_exec` 可執行短時間 CLI 入列及查詢命令；獨立 worker 執行長任務。
- GitHub 是工程來源；原始母體文件、旁白及成片留在操作人指定的本地目錄。
- 預設服務僅監聽 `127.0.0.1:7812`。跨裝置使用接到既有私有 TLS／Tailscale 入口；不自動開防火牆。

## 已實作功能

| 功能 | 行為 |
|---|---|
| 四種故事範本 | explainer／tutorial／release／promo，無模型的來源摘錄規劃 |
| 嚴格來源對應 | 每幕字幕必須是指定來源的逐字摘錄；標題明列為編輯標籤 |
| 自訂分鏡 | v1：1～8 幕、30～60 秒；v2：1～600 幕、每幕 2～60 秒、總長最多 1200 秒 |
| 三種畫面 | v1 三種原始畫面；v2 360p／720p／1080p／2160p，24／25／30 FPS |
| 三種版面 | diagram／steps／quote，可提供本地圖片；節點圖為裝飾，不主張來源拓撲 |
| 實際影音製作 | Pillow 文字排版、淡入淡出、FFmpeg 編碼／合成與 AAC 配樂 |
| 字體檢查 | 先檢查所有字元；缺字即失敗，不輸出亂碼冒充完成 |
| 配樂與旁白 | 原創程式合成四和弦；可選每幕本地 PCM16／22050Hz／mono WAV 旁白 |
| 持久任務 | SQLite WAL、交易式 claim、最多 32 個待處理／執行中任務 |
| 有界執行 | 每次一項任務，每項 1～4 個場景執行緒，預設共用 6 小時期限（可設 60 秒～24 小時），可取消 |
| 版本記憶 | 遞增 version_index、version_string、parent_id；載入／比較／分支，不覆寫原件 |
| 失敗恢復 | OS 單 worker 鎖；重啟將執行中任務標示 INTERRUPTED，已入列任務繼續 |
| 事件鏈 | 交易內追加 SHA-256 鏈；可核對篡改，非遠端公證／數位簽章 |
| 原則綁定 | 可提供既有 law.md，封存快照並記錄 SHA-256；不創造或改寫原典 |
| 手機工作室 | 不依賴 JavaScript；登入、JSON 分鏡編輯、狀態、自動刷新、預覽、下載與子版本 |
| 私有 API | x-api-key、冪等鍵、Host 檢查、拒絕跨來源寫入、表單 CSRF、短期 HttpOnly cookie |
| 成片驗收 | 完整解碼、格式／片長／幀數／音訊長度、逐幕取樣、全片黑畫面區間掃描 |
| 完整交付 | 成品、GIF、聯絡表、SRT、逐幕檔案、來源、素材、分鏡、稽核與精確 ZIP 清單 |

## 安裝與啟動

需 Python 3.10+、FFmpeg／FFprobe（含 libx264、AAC）、可涵蓋內容的本地字體。
FFmpeg、字體與可選旁白來源的授權由操作者依部署情境確認；本模組不打包這些第三方程式／字體。

```bash
python -m pip install -r MRL_Video/requirements.txt
# 使用既有 secret binding，不把 key 寫入命令、JSON 或 git。
# MRL_VIDEO_API_KEY 優先，否則沿用 MRL_BRIDGE_API_KEY；長度至少 24 字元。
python -m MRL_Video --root /local/mrl/video/versions \
  --source-root /local/mrl/video/inputs --font /local/fonts/NotoSansCJK-Regular.ttc \
  --law /local/mrl/core/law.md serve
```

`--law` 可省略；metadata 會明示 `NOT_CONFIGURED`，不聲稱已綁定原典。
Windows 前景啟動器（可交給母體既有服務管理器維護）：

```powershell
.\scripts\MRL_Start_Video.ps1 -Python 'D:\MrlToolchain\python\python.exe' `
  -Font 'C:\Windows\Fonts\msjh.ttc'
```

實際 Python、字體、repository 位置須在 DL580 核對。啟動器不自動安裝套件或改動現有服務。

## 製作第一支影片

不啟動 HTTP 的單次本地製作（獨占同一 worker root）：

```bash
python -m MRL_Video --root /local/mrl/video/versions \
  --source-root /local/mrl/video/inputs --font /local/fonts/font.ttf \
  run MRL_Video/examples/demo.json --idempotency first-demo
```

HTTP worker 已啟動時，改用 `submit`，避免啟動第二個 worker：

```bash
python -m MRL_Video --root /local/mrl/video/versions submit MRL_Video/examples/demo.json
python -m MRL_Video --root /local/mrl/video/versions list
python -m MRL_Video --root /local/mrl/video/versions status MRL_<returned_id>
```

範例是 **synthetic fixture**，並非母體實機證據。自動分鏡需要至少四段 4～180 字元的原文。
若需要自行安排分鏡，加入 `scenes`：

```json
{
  "title": "本幕標題",
  "caption": "必須逐字存在於來源文字",
  "source_id": "source1",
  "duration": 8,
  "layout": "steps",
  "image": "pictures/step1.png",
  "narration": "voice/step1.wav"
}
```

這是**單幕結構**，須放在完整 request.scenes 陣列，並符合總時長。
圖片與旁白以 source-root 下相對路徑指定；拒絕跨目錄及 symlink。製作開始時快照，原檔不改名。
來源文字保存 original_name／locator／hash；快照檔名為 source ID，不冒稱原始名稱已改變。
音訊超長、靜音或格式不符即失敗。`require_narration: true` 要求每幕都有旁白。
`music: false` 可明確要求無背景樂。未提供旁白時，畫面字幕仍會產生；不會偽稱已做 TTS。

## 版本與交付

```bash
python -m MRL_Video --root /local/mrl/video/versions load-version MRL_<id>
python -m MRL_Video --root /local/mrl/video/versions branch revised.json --parent MRL_<id>
python -m MRL_Video --root /local/mrl/video/versions diff MRL_<old> MRL_<new>
python -m MRL_Video --root /local/mrl/video/versions events MRL_<id>
python -m MRL_Video --root /local/mrl/video/versions verify-chain
python -m MRL_Video verify-package /local/mrl/video/versions/MRL_<id>.zip
```

每個版本擁有獨立目錄，成功後提供 ZIP 及外部 receipt（ZIP SHA-256）。
ZIP 含 `MRL_manifest.json` 與實際內容；manifest 不含自身 hash，避免遞迴。
receipt 是 ZIP 外部的比對依據，請保存到既有證據系統；可同時修改 manifest 與 ZIP 的人仍可偽造，不能當作簽章。
`DELIVERY_PASS` 表示此 request 的程式化交付檢查通過；語意、美感、對外發布及 DL580 實機是獨立狀態。
失敗保留現場，下載入口拒絕 FAILED／CANCELLED／INTERRUPTED 任務。修正使用新子版本。
1.2.0 增加內容位址片段快取與失敗子版本續跑；仍為單機執行。完整契約、影音片段輸入、母體來源與長片驗收分層見 [長片整合 R04](../docs/MRL_Video_LongFilm_R04.md)。

## API 與母體橋接

完整端點見 `openapi.json`；request schema 見 `request.schema.json`（v1）與 `request-v2.schema.json`（v2）。
JSON API 使用 `x-api-key`；瀏覽器 cookie 不可寫入 JSON API。
`Idempotency-Key` 相同且內容、parent 相同時回傳原任務；不同內容會拒絕。

透過已存在的 `/MRL_exec` 呼叫短命令（示意 payload，路徑須以母體現場為準）：

```json
{
  "cmd": "& 'D:\\MrlToolchain\\python\\python.exe' -m MRL_Video --root 'D:\\mrl\\video\\versions' submit 'D:\\mrl\\video\\inputs\\request.json'",
  "cwd": "D:\\mrl\\flow-tasks",
  "timeout": 15,
  "shell": "powershell.exe"
}
```

先用母體既有部署程序放入模組與 request；API key 綁在既有 Bridge header。
worker 須先獨立啟動；不能在 Bridge 30 秒執行窗口跑完整渲染。
查詢時同樣以短命令執行 status。HTTP 7812 的跨裝置私有入口仍須依既有 gateway 設定並驗收。
`config/MRL_Video_Bridge.json` 是已實作 CLI／API 的對接契約，不是部署成功證明。

## 測試與已知邊界

```bash
python -m pytest MRL_Video/tests/test_video.py -q
MRL_VIDEO_MEDIA_TEST=1 python -m pytest MRL_Video/tests/test_video.py -q
python -m compileall -q MRL_Video
```

設定 `MRL_VIDEO_TEST_FONT` 指向測試字體；預設測試使用 DejaVu Sans。
設定 `MRL_VIDEO_TEST_CJK_FONT` 可加跑中文製片驗收；缺字會拒絕製作。
CI 在 Linux 以 exact head 匯出模組，再讓 Linux／Windows 下載同一份來源執行；避開 Windows Git 對歷史檔名的限制，原始檔案不改名。
模組變更紀錄放在 `CHANGELOG.md`，保留根目錄已被其他交付清單固定的變更紀錄。
工作室為單一可信 Owner 的私有本地工具，不提供租戶隔離／公開網際網路入口；HTTP 本身不提供 TLS。
同一 root 只允許一個生產 worker，metadata/SQLite 必須位於可信本地磁碟，並依母體機制備份。
沒有自動 TTS、數字人、照片生成影片或 GPU 推論；不將既有小影系統的功能宣稱當成本模組實作。
目前僅 programmatic review；人工仍需檢查標題、圖片、來源意思與視覺呈現。
部署驗收程序見 `../docs/MRL_Video_Acceptance.md`。


既有 1.1.0 的 v1 `longfilm: true`／`encoding` 仍可使用：最多 1200 秒、每幕 2–20 秒、24 FPS，自訂偶數尺寸與既有 CRF／preset。v2 另提供精確 target_seconds、60 秒片段與 clip。舊 `MRL_segment_cache` 留存，不重新命名；新實作使用 `MRL_scene_cache` 並因 renderer 變更重新建立已驗證快取。

並行提交的 `MRL_LongFilm_Request/v1`、episode import、SQLite segment progress、retry 與內嵌字幕繼續由既有 `longfilm.py` 承接，詳見 [片段長片接線](../docs/MRL_LongFilm_Integration_20261104.md)。
