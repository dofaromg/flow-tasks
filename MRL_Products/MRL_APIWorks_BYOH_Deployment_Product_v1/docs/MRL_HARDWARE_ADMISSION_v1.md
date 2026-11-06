# MRL-34 Hardware Admission v1

origin_signature: MrLiouWord
Parent: MRL_APIWorks_BYOH_Deployment_Product_v1
Baseline: dofaromg/flow-tasks@608b66e0db23e7cc4eef21ea752668ac800620b3

## 血緣與整合 / Lineage

沿用 `utils/gpu_orchestrator.py`、`configs/gpu_allocation.yaml` 與商品建包器。
`allocate_gpu()` 在負載平衡完成後、返回 GPU 配置前呼叫唯一商品准入器。
完整 GPU inventory 與現場 UUID、torch GPU 名稱、CC、VRAM、nvidia-smi driver、OS 比對；
Passport 所載 loaded runner/runtime/image 必須與 workload 完全相同。PyTorch runner
另核對 torch 版本及其 CUDA runtime。配置、實際 artifact bytes 或欄位缺失時 fail closed。
這是分支上的行為變更，未安裝或部署到母體；既有 GPU 分配偏好不改。
其他自行繞過 orchestrator 的外部程式不受此 Python API 控制；本 gate 不是 OS 隔離機制。

既有 `docs/HARDWARE_SETUP.md` 是通用 Linux/video-system 安裝指南，含 CUDA 11.8、
驅動重裝及 BIOS 範例，並不是 DL580 現場快照或 MRL-34 升級授權。
既有 `MRL_Mother/04_runtime/runtime_manifest.yaml` 是四層 Runtime/Container/CLI 關係，
`DL580_WaveStack/MRL Runtime Stack Manifest.json` 保留 Bridge 3.1.0 血緣。
`docs/evidence/dl580/` 是既有 Bridge 證據，不證明新 GPU bundle 驗收。

歷史硬體記錄原樣另存 `hardware/MRL_DL580_historical_snapshot_v1.json`：
Windows Server 2019 build 17763、6×V100-SXM2-32GB、driver 539.56、當時報告 CUDA 12.2。
來源是 owner 提供的先前現場紀錄；此次沒有重新探測 DL580。
原紀錄沒有 runner binary、模型與 bundle digest、實際 linked runtime ABI 或重啟回執。
因此保留歷史觀測，不補造 exact acceptance，也不撤銷任何舊驗收原件。

## 分開判斷的條件

| 欄位 | 含義與准入條件 |
|---|---|
| GPU identity / architecture / compute capability | UUID、SKU、Volta / 7.0 逐卡比對；不以「NVIDIA」概括 |
| Driver | OS 裝置驅動；driver API 的相容性與硬體支援範圍，不等同 Toolkit |
| Toolkit | 編譯工具鏈；明確版本，或預編譯 native workload 的 `not_used` |
| CUDA runtime / runtime ABI | runner 實際 linked CUDA 版本與 `cuda-12`；不可抄 nvidia-smi 標頭代替 |
| OS / CPU ABI | family、OS version、arch 必須一致；Windows 不能被 Linux 容器驗收覆蓋 |
| Runner / runtime / model / quantization | exact id、version、實際 byte digest 與精度，全部納入 configuration digest |
| Bundle / image | bundle、runner、runtime、模型實際 bytes SHA-256；sharded directories 用排序 file-set digest；容器必須 image@sha256 |
| Acceptance | reviewed release matrix 的 exact configuration + 真實 device/runtime/model/restart receipt，不接受 caller 的 passed 旗標 |

CUDA 13 移除 CC <7.5 的離線編譯支援；MRL 政策進一步拒絕 Volta 路徑的
CUDA runtime/Toolkit/image major 非 12，以及 TensorRT RTX、TensorRT >=10.5。
這不等於 R580 driver 不能執行 CUDA 12 binary。R580+CUDA12 不因 driver 分支號被誤判，
但仍需 exact acceptance；Volta 高於最後支援分支 R580 則拒絕。
CUDA 12 驅動底線採保守 MRL 政策：Linux 525.60.13、Windows 528.33。
這只是必要條件，不是所有 CUDA 12.x、PTX JIT、API feature 或 runner 都通用的充分條件。
較新 PTX、cuDNN、runner wheel 未含 sm_70 都必須另由 exact artifact smoke 驗收。
不同 CUDA 12.x 不會互相自動授權。

## 機器介面

`hardware/MRL_hardware_matrix_v1.json` 是隨來源 SHA 保護的 release policy。
`acceptances` 目前為空：沒有把歷史或 synthetic test 推成正式相容。
每個 route 分開保存 bundle_id、digest、internal_acceptance、public_support、evidence_refs。
未建出的 GPU runtime artifact digest 為 null，代表 unknown，不能拿 descriptor hash 代替 binary hash。
現代 NVIDIA CUDA12、CUDA13 與 AMD ROCm 都各自 unknown。

Host 必要欄位：`schema=MRL_Hardware_Manifest_v1`、origin_signature、observation=current、
os{family,version,arch}、driver{vendor,version}、loaded_runner、loaded_runtime、
loaded_image、非空 gpus[]，每卡 {id,uuid,vendor,architecture,sku,compute_capability,vram_mib}。
現場 inventory 必須完整，不能排除不相容卡。
歷史 snapshot 有完整硬體欄位，但 observation=historical，不能直接當 current 使用。

Workload 必要欄位：`schema=MRL_Workload_Manifest_v1`、origin_signature、track、gpu_ids、
bundle_id、bundle_digest(`sha256:`+64hex)、os、cuda_runtime、runtime_abi、toolkit、
runner{id,version,digest}、runtime_binary{id,version,digest}、model{id,version,digest}、
quantization、image{id,cuda_major}（native 時 id=native、cuda_major=0）。
`artifact_paths` 在操作者的 `configs/gpu_allocation.yaml` 中與 `artifact_root` 一起提供，
分別指向實際 bundle/model/runner/runtime 檔案或目錄；路徑本身不取代 digest。
`tests/test_hardware_admission.py::fixture` 是可執行的 synthetic 格式範例，
其 digest 只用於測試，不是交付 runner、模型或驗收資料。

從商品目錄執行：

```powershell
python scripts\MRL_hardware_admission_v1.py `
  --host D:\mrl\evidence\current_host.json `
  --workload D:\mrl\evidence\current_workload.json `
  --artifact-root D:\mrl\candidate `
  --artifact-paths D:\mrl\evidence\artifact_paths.json
```

CLI 是 policy/digest 預檢，不查詢實際 GPU，也不能自行授權啟動。部署只可經
`GPUOrchestrator.allocate_gpu()`；該路徑在回傳前查詢 live OS/driver/GPU 並重新執行同一
canonical gate。`set_device()` 與 `DataParallel` 也必須使用最近一次 admitted 的完全相同 GPU IDs。
CLI 不提供 alternate matrix 或 force-pass；Python API 也不接受 caller-supplied matrix。
配置 `configs/gpu_allocation.yaml` 的 hardware_admission.host_manifest、
workloads[engine_name]、artifact_root 與 artifact_paths[engine_name] 指向操作者保存的資料；
不得把歷史檔 observation 改成 current。
configuration_digest 是 canonical JSON SHA-256，包含整個 host 與 workload。
新 driver、runner、模型、精度或 bundle 都需要獨立 exact acceptance。
證據 receipt 必須列出並通過 device_query、runtime_smoke、model_smoke、restart_smoke。
receipt/evidence digest 是完整性識別，不是數位簽章；release review 負責證據真實性。

`scripts/MRL_hardware_smoke_v1.py` 重用操作者提供的 current Passport JSON，不另建硬體
collector；它查詢 nvidia-smi/torch、驗證實際 artifacts，並執行操作者明確提供的
argv-only runtime/model smoke commands。命令規格包含 deterministic stdout SHA-256；
script 只保存 command 的 exit code 與 stdout/stderr digest，不保存原始輸出。通過時
狀態仍是 `smoke_passed_pending_restart_and_owner_review`，絕不自行建立
`hardware_verified` receipt。`--replay-record` 會驗證舊紀錄與當前 configuration/digests
相同後重跑。此 script 不重啟服務、不安裝軟體、不升級 driver/CUDA。

## 獨立 bundle

沿用現有建包器（一般商品 ZIP 保留原名）：

```powershell
python scripts\MRL_build_product_bundle_v1.py --hardware-route MRL_APIWorks_BYOH_DL580_V100_CUDA12_v1
python scripts\MRL_build_product_bundle_v1.py --hardware-route MRL_APIWorks_BYOH_Modern_NVIDIA_CUDA13_v1
```

每軌輸出不同檔名、內容、ZIP SHA-256 sidecar；ZIP 內 MRL_HARDWARE_ROUTE.json
與 MRL_PRODUCT_BUNDLE_MANIFEST.json 保存 route、unknown 狀態與獨立驗收欄位。
這些是來源部署包，沒有包含 NVIDIA 驅動、CUDA、runner binary 或模型權重；
其 ZIP digest 不能冒充尚未建出的 GPU runtime artifact digest。
正式 runtime bundle 將實際 byte digest 放入 workload，再經 smoke+restart 與 release review 登錄。

## Smoke / rollback（需 owner 核准才對母體執行）

Prepare the local smoke/replay record only after the actual current Passport output and all
artifact bytes are available:

```powershell
python scripts\MRL_hardware_smoke_v1.py `
  --host <current-passport-derived-host.json> `
  --workload <exact-workload.json> `
  --artifact-root <immutable-candidate-root> `
  --artifact-paths <artifact-paths.json> `
  --smoke-commands <approved-smoke-argv.json> `
  --output <local-evidence-dir\smoke.json>

python scripts\MRL_hardware_smoke_v1.py `
  --host <same-current-passport-derived-host.json> `
  --workload <same-exact-workload.json> `
  --artifact-root <same-immutable-candidate-root> `
  --artifact-paths <same-artifact-paths.json> `
  --smoke-commands <same-approved-smoke-argv.json> `
  --replay-record <local-evidence-dir\smoke.json> `
  --output <local-evidence-dir\replay.json>
```

`MRL_capture_node_evidence_v1.py --replay-receipt <prior-apiworks-receipt.json>` is a
separate local API/memory/passport replay, not GPU acceptance. No restart is performed by
either smoke command. Do not copy raw output, private paths, credentials, or model data to GitHub.

The existing receipt tool can build immutable before/forward/return plans and verify their
artifact hashes without running commands:

```powershell
python scripts\MRL_reversible_change_v1.py record --root <local-evidence-root> --spec <before.json> --output <before-receipt.json>
python scripts\MRL_reversible_change_v1.py record --root <local-evidence-root> --spec <forward.json> --output <forward-receipt.json>
python scripts\MRL_reversible_change_v1.py record --root <local-evidence-root> --spec <return.json> --output <return-receipt.json>
python scripts\MRL_reversible_change_v1.py verify --root <local-evidence-root> --before <before-receipt.json> --forward <forward-receipt.json> --return-receipt <return-receipt.json>
```

Each forward/return command plan must use explicit argv arrays and `requires_owner_go: true`.
These commands only record/verify; they never activate or roll back a service.

After separate owner approval and review of exact digests, the existing
`MRL_Mother/deploy_reference/dl580/MRL_systemd_service.template` names the service
`mrl-runtime`. Its activation candidate is:

```bash
sudo install -o root -g root -m 0644 <owner-reviewed-mrl-runtime.service> /etc/systemd/system/mrl-runtime.service
sudo systemctl daemon-reload
sudo systemctl start mrl-runtime
systemctl status mrl-runtime --no-pager
journalctl -u mrl-runtime -n 100 --no-pager
```

Rollback candidate, only after owner approval:

```bash
sudo systemctl stop mrl-runtime
sudo install -o root -g root -m 0644 <verified-before-mrl-runtime.service> /etc/systemd/system/mrl-runtime.service
sudo systemctl daemon-reload
sudo systemctl start mrl-runtime
systemctl status mrl-runtime --no-pager
```

The service template has `<MRL_HOME>`/`<MRL_USER>` placeholders; no node-specific values
or GPU service mapping were available to fill them. Do not execute these commands from this
issue. Preserve all prior bundles and receipts; unknown or failed combinations remain denied.

風險：本分支啟用後未配置證據的 GPU allocation 會阻擋；正式部署前先準備 exact acceptance。
此次僅在工程分支建構，沒有重啟、升級或修改母體。

## 官方依據（2026-11-03 查核）

- https://developer.nvidia.com/blog/navigating-gpu-architecture-support-a-guide-for-nvidia-cuda-developers/
- https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html
- https://docs.nvidia.com/cuda/archive/12.2.0/cuda-toolkit-release-notes/index.html
- https://docs.nvidia.com/cuda/archive/12.9.2/cuda-toolkit-release-notes/index.html
- https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html
- https://docs.nvidia.com/deeplearning/tensorrt-rtx/latest/getting-started/support-matrix.html
- https://docs.nvidia.com/deeplearning/tensorrt/10.x.x/architecture/architecture-overview.html

R535 不同產品支援表與日期需各自核對；不據此文件推定母體需升級。
