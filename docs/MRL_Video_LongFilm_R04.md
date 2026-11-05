# MRL_Video 長片整合 R04

origin_signature: MrLiouWord · canonical_authority: Mr.liou

本增量（1.2.0）接續 PR #705 的 `9adfe7afe1f14312b07119e72be65b41f5c78a98`，並合併施工期間出現的 `70f2d5f0ed9cde8bc92b30473651b19a6070cf15`，吸收 Dropbox `MRL_LongFilm_20min_R03` 的 R03 → R02 → R01 譜系。沿用同一 Service、SQLite queue、版本、私有工作室、Bridge 短命令及交付驗收；沒有另建平台。原始 R03 與 R01/R02 不改寫；來源索引見 `../evidence/MRL_Video_LongFilm_Sources_20261104.json`。

## 輸入與時間線

v1 保留短片契約，並承接同日 `70f2d5f0ed9cde8bc92b30473651b19a6070cf15` 新增的 `longfilm: true`／`encoding`：最多 1200 秒、每幕 2–20 秒、24 FPS、自訂偶數尺寸、CRF 16–28 與 ultrafast/veryfast/fast/medium/slow。v2 必須提供完整 `scenes` 與 `target_seconds`：30–1200 秒、1–600 幕、每幕 2–60 秒。逐幕毫秒精度且必須對齊整幀，總長必須等於 target，拒絕靠大量幀取整掩蓋時間差。字幕、逐幕音訊樣本和影片採相同時間線。24/25/30 FPS；360p 草稿、720p、1080p、2160p，直橫方形；libx264 CRF 18–28、veryfast/fast/medium。提高輸出解析度不等於提高來源細節，2160p 設定不等於已通過 4K 長片驗收。

`examples/longfilm_20min.json` 是 20 幕 × 60 秒的合成字幕卡範例，必須換入真實經審閱故事與素材才是創作作品。原本來源摘錄約束保持；clip 內容及其語意仍需人工審閱，逐字字幕檢查不替代它。

每幕可用 `image` 或 `clip`。`clip` 指向 source-root 內相對路徑，可加 `clip_start` 秒數，先核對可讀性、影片及音訊是否足夠，再統一尺寸、幀率、像素比例與時基。原始檔案以原相對名稱快照、串流 SHA-256 記錄，不修改來源。片段只接受 MP4/MOV/Matroska/WebM 容器，FFprobe 與片段讀取限制 demuxer 與 file/pipe 協定，拒絕用播放清單轉向網路。`narration` 明確覆蓋該幕原音；未提供時沿用 clip 音訊。沒有音訊的 clip 必須明列 `allow_silent: true`；旁白契約仍為本地 PCM16/22050Hz/mono WAV。音樂與原音混合，整片音軌只 AAC 編碼一次，避免每段 AAC padding 累積。

```json
{"title":"Scene 1","caption":"來源中的逐字字幕","source_id":"s1","duration":10,
 "layout":"steps","clip":"approved/S01.mp4","clip_start":2}
```

拼接採精確硬切，不把普通剪輯宣稱 Gloria latent continuation。字幕另交付 SRT；輸入 clip 的畫面不自動燒字。字幕卡保留淡入淡出。GIF 最多約 30 幀覆蓋全片、聯絡表最多 24 幕，逐幕審查圖仍完整交付。

## 快取、取消與失敗續跑

每幕完成編碼與完整解碼後，才以原子目錄更名封存 `MRL_scene_cache/<key>`。key 綁定 renderer bytes、FFmpeg/FFprobe、字體、原始素材 SHA、幕位置/總數、分鏡及畫質設定。復用前逐檔核對 SHA；損壞即失敗，保留證據，需操作者隔離損壞 entry 後重試，不悄悄覆寫。尚未完成的幕永遠不視為可復用。

既有 `MRL_segment_cache` 曾觀察到已驗證片段由 12,282,553 bytes 縮至 11,534,336 bytes；原始紀錄指出縮小在合成前被拒絕，但沒有足夠的生命週期資料判定根因。後續 `layout.json` 每幕驗收記錄加入 hash、device/inode、size、mtime/ctime 與 open-handle 穩定性快照；驗證前後、預覽讀取前後與合成前都比對快照。快取發布前核對 staging copy 與封存 hash，並 fsync payload/receipt，再分別以 atomic replace 發布。回歸測試重現該尺寸縮小並核對完整預期/觀察診斷；這補強偵測與證據，不代表該次外部縮小根因已被證實或解決。

```bash
python -m MRL_Video --root /local/mrl/video/versions --source-root /local/mrl/video/inputs \
  --font /local/fonts/font.ttf --timeout 21600 run MRL_Video/examples/longfilm_20min.json
# 已有 worker 時以 submit 入列；Bridge 只跑短命令。
python -m MRL_Video --root /local/mrl/video/versions resume MRL_<unsuccessful_id> --idempotency retry-01
```

`resume` / 工作室續跑按鈕 / `POST /api/jobs/{id}/resume` 只接受 FAILED/CANCELLED/INTERRUPTED，追加同一 request 的子版本，保留原版、事件與失敗現場。worker 正常啟動後處理新子版本；若目前未啟動，resume 僅入列。重取素材快照再算 hash；來源變更不會復用舊幕。音軌、總合成、完整驗收及 ZIP 重新執行。相同設定的新版重用成功場景；修改場景僅重製受影響場景。手動取消後不自動反覆續跑。

執行上限 1 個 worker、1–4 幕同時製作、每個 encoder 2 threads；全任務預設 6 小時、可設 60 秒至 24 小時。長片音訊逐幕串流寫入，ZIP 與大型素材用串流 hash；最多 5000 entries、64 GiB ZIP 解壓總量、單檔 8 GiB，輸入素材單檔 2 GiB。可用磁碟空間不足仍會失敗並保留現場；沒有跨機分散式執行或自動快取淘汰。

## 母體既有能力承接

| 工作 | 既有來源 | R04 接口 |
|---|---|---|
| 模型/錨點控制 | R02 `mrl_video.py prepare/submit/collect`；MRL_comfy-mcp；MRL_ComfyUI | 沿用既有批准工作流，完成的影片以 clip 本地輸入；不重新發送不明狀態生成工作 |
| 角色與影片 | R01 Wan/SDXL/Qwen/LivePortrait 範本及來源索引 | 保留原名、角色/鏡頭來源；R04 不改模型或其精度 |
| 音訊 | R01 Chatterbox/VibeVoice；歷史 voice_agent :7820 | 已核准 WAV 或 clip 原音；不強制外部 TTS |
| 執行/回返 | PR705 canonical Bridge `/MRL_exec` → CLI submit/status | worker 長任務獨立運行，回傳版本與 ZIP 收據 |

歷史 ComfyUI :8188／voice_agent :7820 來自封存文件，未以本輪探測背書。三個 Notion 媒體/工作流子頁目前讀回空白，僅作父子導航，能力依 R01/R02 原碼與 GitHub 來源核對。DL580 六張 V100 的模型能力與 CUDA 組合須沿既有硬體准入工程驗收；本增量 CPU 編碼不安裝或升級 CUDA，也不宣稱 V100 具有可用硬體編碼路徑。

## 驗收分層

1. 程式：原有短片回歸、新長片契約/邊界、快取鍵、保留失敗版本、損壞拒絕。
2. 實際媒體：本地 clip 原音裁切與接縫取樣、完整解碼、精確幀數/影片/音軌時長、黑區間、逐幕圖、ZIP 對帳。1200 秒測試為 640×360 字幕卡與本地音調，不是 20 分鐘 AI 創作或 1080p/4K 長片品質證明。
3. DL580：批准部署後核對實際 Python/FFmpeg/字體、磁碟、版本、真實素材、6h 任務預算、Bridge submit→status→收據 hash 讀回。
4. iPhone：私有 gateway 登入、seek/Range、字幕/音畫、整片播放及下載；需實機。
5. 正式合併/部署：Owner 另行批准。模型生成、人物一致性、故事連貫、人工觀影和權利判定均不由 fixture PASS 代替。

```bash
MRL_VIDEO_MEDIA_TEST=1 python -m pytest MRL_Video/tests -q
MRL_VIDEO_MEDIA_TEST=1 MRL_VIDEO_LONG_TEST=1 MRL_VIDEO_LONG_OUTPUT=/local/mrl/fixture-evidence \
  python -m pytest MRL_Video/tests/test_longfilm.py -q
```

實際新證據見 `evidence/MRL_Video_LongFilm_Validation_20261104.json`。原 `MRL_Video_Validation_20261103.json` 保留當時範圍。

同日並行提交的兩份 `MRL_Longfilm_*_20261104.json` 證據保留原 bytes 與名稱；原 v1 長片測試繼續執行。原有不合格快取的自動重製行為改為明確拒絕並保留損壞證據；舊 `MRL_segment_cache` 不刪除、不改名，新 renderer 的 key 及 `MRL_scene_cache` 格式不把舊快取直接升格。

後續並行提交 `0d689cbf…` 與 `fb42de6a…` 已一併承接：保留 `MRL_LongFilm_Request/v1`、原 episode import、SQLite 逐段狀態、retry、PCM 合片與內嵌字幕；`MRL_Video_Request/v2` 作為同一 worker 的顯式圖卡/素材分鏡介面。各原始證據保留原名與版本，舊報告不被當作此提交重新驗收的結果。

快取格式分開保留：v2 圖卡的 `MRL_scene_cache` 損壞會保留並拒絕；既有 clip 引擎的 `MRL_segment_cache` 先核對收據與媒體，損壞不視為命中，依原流程重製衍生快取。兩者均不覆寫來源素材或已完成版本，正式成片與 ZIP 仍須獨立驗收。

承接 `d1fdd2e8…` 的循環匯入修復，共用型別、檢查、串流 hash、尺寸與 FPS/PROFILES 放入無相依 `contract.py`，保留 model/render 的原公開匯入名稱；本地完整內部匯入圖確認無循環，仍待新提交 CodeQL 掃描。
