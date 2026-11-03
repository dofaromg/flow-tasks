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

## R01 — PR #699 recovery hardening (2026-11-03 Asia/Taipei)
origin_signature: MrLiouWord

Parent: PR #699 head `f29989d54b6ff4c68d27038878eb9571028d6188`.
Legacy API comparison: main `36dc69d98ec3e28e5cca744e82013ed32b203b61`,
`MRL_Mother/05_persona/world_module.py`. PR #695 TimeMachine remains a separate
module and provenance lineage; no files from it are replaced here.

- Remove unused `Dict` and `WorldClosureIntegrityError` imports; tests import the
  integrity exception from its defining module.
- Load legacy JSON lazily inside the first bootstrap transaction. Existing
  verified journals recover missing, stale or malformed JSON mirrors without
  parsing those mirrors first. Malformed first-import data fails without
  overwriting source JSON. Schema creation and bootstrap commit together;
  an existing empty events table fails closed rather than inventing version 0.
- Verify history for version reads as well as writes, and close SQLite
  connections deterministically, including on Windows.
- Preserve all prior event rows and hashes during restoration. Restore replaces
  all three components, including removal of entries absent from the target.
  Restore trajectory metadata now includes the appended version index.

### Compatibility and operational boundaries

The 10 legacy public method parameter lists are retained: set_node, get_node,
list_nodes, set_state, get_state, snapshot, set_globe_coord, get_globe_coord,
trajectory and rewind. Snapshot retains legacy fields and adds version_index.
Rewind intentionally changes semantics: it appends a complete-state restoration
instead of deleting trajectory entries; zero/negative/bool steps and insufficient
version history return failure without mutation. Legacy trajectory entries are
not retroactively converted into restorable snapshots.

The commit point is SQLite COMMIT. A later mirror/trajectory error propagates to
the caller even though the version is already durable; reopen and inspect history
before retrying. Reopening repairs all JSON mirrors without adding a version.
The three JSON replacements are individually atomic, not one multi-file atomic
transaction. trajectory.jsonl is a legacy auxiliary log: a crash after COMMIT may
leave a missing trace entry; no automatic trace backfill is claimed. Use history()
for the authoritative event list. This change does not provide live coherence
between multiple WorldModule instances or coordinate concurrent JSON/trajectory
writers. Operate one WorldModule writer per data directory.

Hash verification detects changed content and broken internal links; without an
independent anchored tip it cannot prove that a valid suffix was not deleted or
that an actor with database write access did not recompute the chain. No external
notarization is claimed. Process-exit tests do not establish physical power-loss
or DL580 storage/controller durability.

### Validation and delivery accounting

Expected and delivered changed files (5; no renames, missing or extra files):
1. `.github/workflows/mrl-world-closure.yml`
2. `MRL_Mother/05_persona/world_closure_store.py`
3. `MRL_Mother/05_persona/world_module.py`
4. `MRL_Mother/tests/test_mrl_world_closure.py`
5. `MRL_Mother/05_persona/MRL_WorldClosure_Integration_v1.md`

Dependency tree: WorldModule → WorldClosureStore → Python stdlib sqlite3;
tests → both modules; workflow → regression tests. No new third-party dependency.
No ZIP delivery requested; repository commit is the delivery unit.

Local command: `python -m unittest discover -s MRL_Mother/tests -p 'test_mrl_world_closure.py' -v`
Result: 18/18 PASS (original 6 retained plus 12 added).
Python compilation and `git diff --check`: PASS.
CI runs the same suite on ubuntu-latest and windows-latest, Python 3.11.
Regression coverage includes complete legacy JSON import, exact trajectory-byte
prefix retention, repeated restore of all components, unchanged historical rows,
invalid inputs, copy isolation, corruption/empty-history detection, atomic-replace
failure, partial mirror failure, trajectory append failure, and actual child
process exit before/after COMMIT.

Record independently: local tests PASS; exact-head CI requires the new commit's
GitHub run results; review threads require fresh inspection; merge NOT PERFORMED;
DL580 deployment and physical-device acceptance NOT PERFORMED. Owner approval is
required before merge or deployment.


### CI follow-up (R01)

Commit `37fb25e842b03bc9ccce3570b50675e99611e3fb`, run 41553315995:
Linux passed; Windows checkout failed before tests because the existing archive
path `:mnt:data.txt` is invalid on Windows. No archive file was renamed or removed.
The workflow now uses non-cone sparse checkout of the two runtime modules and
complete regression test file, with explicit PR head SHA selection. Both platforms
therefore test the actual head, independently of the temporary PR merge ref.


Windows Git also rejects the invalid archive path during non-cone sparse
checkout (run 41553494212, head 34a78314374320233fa9835d42142b5f8e85677b).
The final workflow fetches the exact head, asserts the fetched SHA, and uses
`git archive` to extract only the three required source/test files, without
checking out the incompatible archive tree. The public repository is fetched
read-only without credentials. Git path protections remain enabled.
