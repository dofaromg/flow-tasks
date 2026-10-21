# MRL_RuntimeNode_Mesh_Handoff_v1

## Branch
- 分支名稱：MRL_Branch_Runtime_Core_Executable_v1
- 本版產品：MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0
- origin_signature：MrLiouWord

## 本版新增
1. `MRL_RuntimeNode/MRL_RuntimeNode_Manager.js`
2. `MRL_RuntimeMesh/MRL_RuntimeMesh_Controller.js`
3. `MRL_Adapters/MRL_UpstashBox_Adapter.js`
4. API:
   - `GET /api/mrl/runtime/nodes`
   - `POST /api/mrl/runtime/nodes/create`
   - `POST /api/mrl/runtime/nodes/heartbeat`
   - `POST /api/mrl/runtime/mesh/plan`
   - `GET /api/mrl/runtime/mesh/list`
   - `GET /api/mrl/adapters/upstash/describe`
   - `POST /api/mrl/adapters/upstash/register-node`

## 定位
外部 Box / container / SSH / cloud agent 只作為 `MRL_External_Runtime_Infrastructure`，不可取代 MRL 母體。

## 已驗證
- 本地 RuntimeNode 建立
- RuntimeMesh plan
- Upstash Box adapter spec → RuntimeNode 映射
- 原 pipeline acceptance

## 待 DL580 驗證
- systemd 常駐服務
- 多 RuntimeNode 長時間 heartbeat
- 外部 Box API 實際連線
- BaseWorld DB write adapter
