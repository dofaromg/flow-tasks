# MRL 長片分段整合 · 2026-11-04

origin_signature: MrLiouWord · canonical_authority: Mr.liou

來源基線：PR #705 `9adfe7afe1f14312b07119e72be65b41f5c78a98`；施工期間新增 `70f2d5f0ed9cde8bc92b30473651b19a6070cf15`，已保留並疊加整合。圖卡 `longfilm: true` 與影片素材 `MRL_LongFilm_Request/v1` 各有既有功能和實測。這是原有 MRL_Video 的增量；MRL_VideoGen、Ultimate 及原模組名稱保留。沒有改動母體服務、部署、合併或對外發布。

## 喚醒與沿用

| 原件 | 本次讀取與沿用 | 邊界 |
|---|---|---|
| MRL_LongFilm_20min_R03/mrl_longfilm.py | 素材根限制、時長審核、明示靜音、create-only 合片；新 episode adapter 接原 shots/line/media | 原件未改；R03 的既有 1200 秒紀錄是 64×64、2 FPS 重複色塊 |
| baseline_R02/mrl_video.py | 人物錨點、原 API 圖綁定、prepare/submit/collect 與 provenance；接收其已完成本地影片輸出 | 不重做模型層、不盲目重送遠端生成；本次未呼叫 ComfyUI |
| baseline_R02/baseline_R01/MRL_Episode_Pilot_01.json | 原名、人物、台詞與原始 episode 全文保存在來源快照；import-episode 轉入新佇列 | 原例只有 60 秒；沒有把它循環偽造為正式 20 分鐘劇本 |
| MRL_Creator_Studio_v0.7.0_R07/longform.py | 延續持久分段、版本事件與既有 shots 契約；接 R07 產出的本地片段 | 保留原 SQLite、素材與父版本；不搬移、不覆寫 |
| R07/render_engine.py | 沿用 draft/fullhd/uhd 的編碼參數、CPU 有界執行與合片時複製 video stream 方法 | 音軌改用 PCM 分段後一次 AAC，避免逐段 AAC padding |
| main_ultimate.py / README_ULTIMATE.md | 已讀人物與聲音服務入口，對位既有 engine factories | 既有模型有待實機核對；本次不宣稱人物、TTS 或口型已接通 |
| PR #705 MRL_Video | 直接沿用 Store、Service、Runner、來源快照、SRT、影片驗收、ZIP 與私有 HTTP | 單機執行；尚未跨機分散排程 |

歷史來源連結：
- https://github.com/dofaromg/flow-tasks/pull/705
- https://www.dropbox.com/l/scl/AAOvzP5uOw-o2iNFfQJPbtzlKH1tdvNjOaw
- Creator Studio R07：`libfile_3b9adcd1cf40819196da5cafec8a04e1`
- 整合復盤 R01：`libfile_19ee6a7d84d48191831f03fa7c9ea236`

## 實作與用法

新 schema `MRL_LongFilm_Request/v1` 接受 1～600 段，每段 2～120 秒、總長至 1200 秒。各段在 24 FPS 的整數幀上對齊，時間軸以幀與 48 kHz sample 表示。原短片 schema 保持原有 30～60 秒限制。

```bash
# 原 episode 不改名、不覆寫。每鏡需有非空、可對照來源的 line。
python -m MRL_Video import-episode original_episode.json --out request_longfilm.json --profile fullhd --quality fullhd
python -m MRL_Video --root /local/mrl/video/versions --source-root /local/mrl/video/clips --font /local/fonts/font.ttf run request_longfilm.json
# 失敗或中斷後，保留原版本並建立子版本；worker 繼續處理新任務。
python -m MRL_Video --root /local/mrl/video/versions retry MRL_JOB_ID
```

既有 submit/run/branch/API 都接受新 schema。`GET /api/jobs/{job_id}/segments` 回傳逐段佇列狀態。每段 clip 是 source-root 下的相對路徑，受原有 50 MiB 單素材限制；更大片段需先在既有模組切段。缺音訊須逐段明示 `allow_silent: true`；來源音畫起始時間相差超過一幀時拒絕製作，避免分別歸零掩蓋原始不同步。

`transition: cut` 保留完整鏡頭；`fade` 沿用 0.25 秒淡入／淡出，不重疊或縮短時間軸。現有片內轉場、人物、配樂與語音會保留在來源音畫中；本輪不把它們重新生成。字幕側錄及 MP4 內嵌 mov_text 使用同一全片時鐘。

片段快取鍵包含原始 bytes hash、裁切區間、解析度、品質、轉場、FFmpeg build 與 renderer hash。每次重用核對快取 payload hash、解碼、格式及幀數；壞快取重新製作。合片前再次對照每段 hash；成功的前段可在新版本重用。相同 request 的重試優先讀父版素材快照並驗 hash；原版成品不改。快取可刪除後重建，會增加製作時間。

品質與解析度分別指定：landscape/portrait/square/fullhd/uhd 是畫面尺寸；draft/fullhd/uhd 是 encoder preset/CRF。放大低解析度素材不等於恢復原始細節。全片 GIF 限 24 張取樣、contact sheet 最多 24 格，完整影片仍逐段取樣、全片解碼、黑畫面掃描。包裝採串流 hash，讀取預算 4096 項／總 32 GiB／單項 8 GiB。

## 測試與驗收

```bash
MRL_VIDEO_MEDIA_TEST=1 python -m pytest MRL_Video/tests -q
python -m MRL_Video.fixture_acceptance --out new_fixture_directory
```

CI 對同一 exact-head source artifact 在 Linux/Windows 執行回歸與完整 1200 秒 fixture。fixture 是 160×90、24 FPS 的 testsrc2＋音調，20 次重用同一 60 秒片段；它驗證合片、快取、字幕、時長、全片解碼與交付，不能證明生成模型、劇情或人物品質。1080p 另有 2 秒真實編碼驗收；4K 尚未做完整長片驗收。

CodeQL 七項原指摘的修正：CLI KeyboardInterrupt 改為明示停止狀態；移除測試中三個未使用 import；HTTP GET/POST/file 統一 return 路徑。在 fb42de6 的新掃描中原七項 threads 已解決；該掃描另指出循環匯入，已抽出無相依的 contract.py 保留舊公開匯入名稱，待下一個 exact head 再掃描。

R03 已取得程式與範本，尚無經核准的 1200 秒故事／完整實際生成素材。正式成片、人物一致性、口型、DL580、canonical Bridge 往返及 iPhone 播放仍待驗收。

## 回復與核准範圍

這次只更新 PR 工程分支。合併前可用 `git revert <本次增量commit>` 回復程式；不需要更動既有服務。資料 root 留在操作人本地，舊版本和 ZIP 保留；SQLite 新增 segments 表為相容增量，回舊程式可忽略。若未來批准部署，先備份完整 root，再依原 acceptance runbook 啟動獨立 worker；不要讓新舊 worker 同時使用同一 root。回復時停止新 worker，切回先前程式與備份，保留新資料供追溯。
