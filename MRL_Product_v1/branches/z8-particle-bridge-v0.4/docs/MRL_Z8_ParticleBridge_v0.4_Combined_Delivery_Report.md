# MRL_Z8_ParticleBridge v0.4 — 主任務合併交付報告

**origin_signature:** MrLiouWord  
**報告日期:** 2026-08-11 CST  
**專案分支:** `z8-particle-bridge`  
**專案位置:** `MRL_Product_v1/branches/z8-particle-bridge-v0.4`  
**主任務狀態:** `DELIVERY_PASS`  
**DL580 下一階段:** `NOT_STARTED`

## 1. 主任務範圍凍結

本報告只封口本次主任務，不執行 DL580 或 Z8 實機階段。凍結範圍如下：

1. 讀取並比對最新 `MRL_Z8_ParticleBridge v0.4` 與相關 v0.3 映射頁。
2. 找回早期 Watch、咪寶、LINE、MetaCore、Runtime Assembly、Bazel 方法來源。
3. 保留原 Z8、小智與微聊，以獨立加法分支實作粒子映射。
4. 實作 DL580 可執行的本地 Bridge Runtime，但不在本主任務啟動 DL580 部署。
5. 實作 LINE Messaging API 的 webhook、reply、push、audio message、HMAC 與去重。
6. 實作 `qwen-main`／`muse-agent` 與 `chatgpt`／`line` 切換。
7. 交付 Windows PowerShell、Android additive adapter、測試、封包與稽核證據。
8. 排除後來才加入的 XTC 合約、白名單、官方授權或批准閘門；APK 簽章僅為封包完整性技術步驟。

## 2. 來源對齊結果

| 來源 | 取回內容 | 使用方式 |
| --- | --- | --- |
| [MRL_Z8_ParticleBridge v0.4](https://app.notion.com/p/3b88eeeec5b5819299f4c0dfe7ca29b4) | 加法分支、兩入口、Channel Map、LINE HMAC/ledger | 保留技術部分；排除後加官方閘門 |
| [相關 v0.3 映射頁](https://app.notion.com/p/3b88eeeec5b580d480e2f460ab790ab8) | `z8.xiaozhi.voice`、`z8.line.text`、dry-run/apply/revert | 作為事件名稱與主流程基線 |
| [小天才手錶 × ChatGPT 語音助手 v1.0](https://app.notion.com/p/3e9c8878f0614001a953dff0d3ce53d4) | Android 錄音、Client、Player、Activity 模式 | 延伸為獨立 Android adapter |
| [咪寶完整方案 v1.0](https://app.notion.com/p/83cf619f57f5408384a5c9abf36fd191) | DL580 本地 STT → Qwen → TTS | 本地 Runtime 路徑 |
| [MrlAI 貼身管家秘書 v1.0](https://app.notion.com/p/7ba5316b2b4a4700a0c42371da74fa3a) | LINE raw-body HMAC、reply endpoint | 實作正式 LINE adapter |
| [MetaCore](https://app.notion.com/p/31c8eeeec5b5815ea86add908f1d67d9)／[Runtime Assembly Map](https://app.notion.com/p/37c8eeeec5b581119a03c5f8d76a493b) | `Perception → Fluin → Runtime → Action` | 只採結構方法；MetaCore 維持 IO-less |
| [MRL Bazel BuildSystem](https://app.notion.com/p/eb2988cdced7475c808ea9f646dc67b7) | 確定性依賴圖、內容雜湊、可重現封包 | `MODULE.bazel`、`BUILD.bazel`、Manifest、SHA-256 |

GitHub 與來源頁搜尋未找到先前宣稱的 `Mrliou_Z8_ParticleBridge_Setup_v0.4.zip` 實體、`z8.xiaozhi.voice`／`z8.line.text` 既有 Z8 程式碼或 Z8 專用 Go/Bazel 實作。因此本次交付是依已取回來源重建的新封包，不把舊頁面的 46,500 bytes／舊 SHA 宣稱成已找回的檔案。

## 3. Concrete Channel Map

| 原始入口 | 粒子 | 方向 | Runtime／正式動作 |
| --- | --- | --- | --- |
| 小智 voice | `z8.xiaozhi.voice` | outbound | HMAC → ledger → STT → Qwen/Muse → ChatGPT voice 或 LINE audio |
| 微聊 UI text | `z8.line.text` | outbound | HMAC → ledger → dry-run/apply → LINE Messaging API push |
| LINE webhook text | `z8.line.text` | inbound | LINE raw-body HMAC-SHA256 → dedupe → Qwen/Muse → LINE reply |

控制鏈固定為：`observe → map → dry-run → apply → revert-record`。`revert-record` 可停止或標記本分支映射，但不虛稱能收回 LINE 已投遞訊息。

## 4. Dependency Tree

```text
MRL_Z8_ParticleBridge v0.4
├── Node.js >= 20 (zero npm runtime dependencies)
│   └── src/server.js
│       ├── config.js + env.js
│       ├── security.js
│       ├── ledger.js
│       └── runtime.js
│           ├── mapping.js
│           │   ├── constants.js
│           │   ├── canonical.js
│           │   └── errors.js
│           ├── line.js → LINE Messaging API
│           └── model.js
│               ├── LOCAL_STT_ENDPOINT
│               ├── QWEN_ENDPOINT | MUSE_ENDPOINT
│               ├── CHATGPT_VOICE_ENDPOINT
│               └── LINE_VOICE_ENDPOINT → public HTTPS audio asset
├── PowerShell 5.1+
│   ├── install/start/test/control/package
│   └── adb read-only evidence collector
├── Android additive adapter
│   ├── Android SDK 34 + Gradle 8.2+ + JDK 17 (build-time)
│   └── minSdk/targetSdk 27 (Android 8.1 baseline)
└── Bazel metadata
    ├── MODULE.bazel
    └── BUILD.bazel filegroups
```

## 5. Requested vs Generated

| Requested | Generated | Result |
| --- | --- | --- |
| Latest note and related page comparison | Source alignment table and provenance links | PASS |
| Concrete mapping | Three-direction Channel Map and runtime implementation | PASS |
| Dependencies | Runtime/build/physical-boundary dependency tree | PASS |
| Missing steps | Separated into DL580 next stage; not silently removed | PASS |
| Independent branch; preserve original | `z8-particle-bridge`, additive-only lock | PASS |
| 微聊 → LINE API | push, webhook, reply, HMAC, dedupe, ledger | PASS |
| 小智 voice particle | STT/model/two voice routes | PASS |
| ChatGPT／LINE voice switch | control endpoint and PowerShell switch | PASS |
| Installable delivery | Windows setup ZIP plus Android buildable source | PASS |
| Tests and rollback | 22 tests, dry-run default, revert record | PASS |
| Combined delivery report | This report plus machine-readable audit JSON | PASS |

## 6. Package Map and Audit Gate

| Area | Expected | Generated |
| --- | ---: | ---: |
| Root/build metadata | 6 | 6 |
| Android adapter | 11 | 11 |
| Config | 2 | 2 |
| Documentation/evidence | 4 | 4 |
| PowerShell/audit scripts | 10 | 10 |
| Runtime source | 12 | 12 |
| Tests | 5 | 5 |
| **Source payload total** | **50** | **50** |
| Package `MANIFEST.sha256` | 1 | 1 |
| **ZIP file total** | **51** | **51** |

Audit result:

- Missing: 0
- Extra: 0
- Renamed: 0
- Orphan: 0
- Empty: 0
- Substitute/placeholder content: 0
- Secret candidates: 0
- Runtime tests: 22/22 PASS
- Source coverage: 100%
- ZIP ↔ Manifest coverage: 100%

Exact filenames and per-file SHA-256 are carried by the real `MANIFEST.sha256` inside the ZIP; the manifest is evidence for the included files and does not replace any file.

## 7. Remaining Boundary — Not Part of This Closed Main Task

The following is deliberately held as the next DL580/Z8 task, per the corrected execution order:

- Run the package on the physical DL580.
- Collect the owned Z8 package／Activity／Intent／ABI／codec evidence.
- Insert those observed values into the automatic Android observation binding.
- Build and physically validate the APK.
- Enter locally held LINE/model secrets and run real account/device traffic tests.

No DL580 deployment, device write, account login, credential entry, Apply, APK installation, or physical test was performed while closing this report.

## 8. Completion Gate

`Expected source 50 = Generated source 50`  
`Expected ZIP 51 = Generated ZIP 51`  
`Missing 0 / Extra 0 / Mismatch 0 / Coverage 100%`  

**主任務判定：DELIVERY_PASS**  
**下一階段判定：DL580_NOT_STARTED**
