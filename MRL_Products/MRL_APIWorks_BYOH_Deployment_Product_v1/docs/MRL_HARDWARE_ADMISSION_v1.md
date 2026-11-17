# MRL-34 Hardware Admission v1

origin_signature: MrLiouWord
Parent: MRL_APIWorks_BYOH_Deployment_Product_v1
Baseline: dofaromg/flow-tasks@608b66e0db23e7cc4eef21ea752668ac800620b3

## 血緣與整合 / Lineage

沿用 `utils/gpu_orchestrator.py`、`configs/gpu_allocation.yaml` 與商品建包器。
`allocate_gpu()` 在負載平衡完成後、返回 GPU 配置前呼叫唯一商品准入器。
完整 GPU inventory 與現場 torch GPU 名稱、CC、VRAM、nvidia-smi driver、OS 比對；
PyTorch runner 另核對 torch 版本及其 CUDA runtime。配置不存在時 fail closed。
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
| GPU architecture / compute capability | V100 = Volta / 7.0；逐卡 inventory，不以「NVIDIA」概括 |
| Driver | OS 裝置驅動；driver API 的相容性與硬體支援範圍，不等同 Toolkit |
| Toolkit | 編譯工具鏈；明確版本，或預編譯 native workload 的 `not_used` |
| CUDA runtime / runtime ABI | runner 實際 linked CUDA 版本與 `cuda-12`；不可抄 nvidia-smi 標頭代替 |
| OS / CPU ABI | family、OS version、arch 必須一致；Windows 不能被 Linux 容器驗收覆蓋 |
| Runner / model / quantization | exact id、version、artifact digest 與精度，全部納入 configuration digest |
| Bundle / image | 獨立 bundle_id、實際 SHA-256；容器必須 image@sha256，禁止 latest/tag-only |
| Acceptance | reviewed release matrix 的 exact configuration + 真實 smoke/restart 證據，不接受 caller 的 passed 旗標 |

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
os{family,version,arch}、driver{vendor,version}、非空 gpus[]，每卡
{id,vendor,architecture,sku,compute_capability,vram_mib}。現場 inventory 必須完整，不能排除不相容卡。
歷史 snapshot 有完整硬體欄位，但 observation=historical，不能直接當 current 使用。

Workload 必要欄位：`schema=MRL_Workload_Manifest_v1`、origin_signature、bundle_id、
bundle_digest(`sha256:`+64hex)、os、cuda_runtime、runtime_abi、toolkit、
runner{id,version,digest}、model{id,version,digest}、quantization、
image{id,cuda_major}（native 時 id=native、cuda_major=0）。
`tests/test_hardware_admission.py::fixture` 是可執行的 synthetic 格式範例，
其 digest 只用於測試，不是交付 runner、模型或驗收資料。

從商品目錄執行：

```powershell
python scripts\MRL_hardware_admission_v1.py --host D:\mrl\evidence\current_host.json --workload D:\mrl\evidence\current_workload.json
```

Exit 0=admitted、1=rejected、2=unknown；只有 0 可啟動 workload。
CLI 不提供 alternate matrix 或 force-pass。Python API 的 matrix 參數供 policy 單元測試使用；
部署必須從已審查 checkout 載入 release matrix，不把工作負載提供者當 acceptance authority。
配置 `configs/gpu_allocation.yaml` 的 hardware_admission.host_manifest 與 workloads[engine_name]
指向操作者保存的現場資料；不能只把歷史檔 observation 改 current。
configuration_digest 是 canonical JSON SHA-256，包含整個 host 與 workload。
新 driver、runner、模型、精度或 bundle 都需要獨立 exact acceptance。
證據 digest 是完整性識別，不是數位簽章；release review 負責證據真實性。

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

1. 保存當前服務、完整 GPU/OS/driver inventory、現有 runner/model digest、設定及回復點；只讀查詢：
   `nvidia-smi --query-gpu=index,name,driver_version,memory.total,compute_cap --format=csv`。
   `nvcc --version` 僅證明 Toolkit；runner build metadata 才證明其 CUDA runtime/ABI。
2. 在既有 CUDA12 runner 的隔離工作目錄執行同模型、固定輸入、固定精度 smoke；
   記錄 device UUID、sm_70 kernel 是否可載入、exit code、輸出 digest、VRAM、服務健康。
   不升級 driver/Toolkit，不測 CUDA13 啟動：負案例僅在准入器層驗證阻擋。
3. 將既有 `MRL_capture_node_evidence_v1.py` 的本機推論與 ledger 讀回回執，
   連同 bundle/runner/model digest、exact source commit 存到節點本地證據目錄。
   取得核准並重啟選定服務後重播原 session，確認 GPU 與記憶持久化，保存新回執。
4. 人工審查實機資料後，以追加 reviewed acceptance entry 登錄 release matrix：
   bundle_id、configuration_digest、status=passed、evidence_kind=real_hardware_smoke_and_restart、
   source_commit(40hex)、evidence_ref、evidence_digest。舊 entry 不刪；對外支援狀態另審。
5. 若 smoke/重播失敗，停止候選 runner，恢復原服務設定與先前 binary digest，
   啟動原服務並讀回原健康與 session。候選紀錄保留；未知或失敗不寫 passed。
   若僅撤回本 PR，回到 baseline checkout 即可；不要以關閉 gate 代替某 workload 通過。

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
