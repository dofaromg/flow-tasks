# MRL L4 WORLD — 版本閉環補強（增量）
origin_signature: MrLiouWord

保留原始檔名及既有 \`WorldModule\` API。本補強不重命名世界模組，也不修改 Closure Kernel 正文或舊版 section index。

## 資料與回復
- \`nodes.json\`、\`state.json\`、\`globe.json\`：現有相容鏡像。
- \`trajectory.jsonl\`：原始 legacy 軌跡；**只追加**，不因 rewind 刪除歷史。
- \`world_events.sqlite3\`：版本 0 首次採集既有狀態；每個更動增加完整狀態快照與 SHA-256 鏈接事件，SQLite 事務提交。
- \`version_index\`：0 為現有資料 bootstrap，後續依序遞增。原時戳保留為 metadata，不作版本識別。
- \`load_version(n)\` 僅讀取，\`restore_version(n)\` 追加新的回復事件；\`rewind(steps)\` 等價於相對版本回復。反覆回復不丟棄歷史。
- \`verify_history()\` 驗證序號、相鄰事件鏈、事件內容 SHA-256；不聲稱外部公證或不可由有資料庫寫入權的人重新計算整條鏈。

## 向下相容、限制
舊資料第一次開啟會作為 version 0 封存，舊軌跡不被回填成可回復版本。SQLite 儲存為本地實際狀態來源，程式啟動時用已驗證紀錄修復 JSON 鏡像。使用者不得在模組運轉時直接修改鏡像檔。SQLite 單機交易提供本地並發序列化；跨主機共享磁碟、高可用同步與外部 Bridge 寫入讀回尚不在此項驗收範圍。

## 驗收
\`python -m unittest discover -s MRL_Mother/tests -p 'test_mrl_world_closure.py' -v\`

必須分別記錄：靜態可檢視、CI 結果、合併狀態及 DL580 母體實機驗收；不得以其中一項代替其他項。
