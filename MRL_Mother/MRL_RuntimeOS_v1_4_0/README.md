# MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0

origin_signature: MrLiouWord
version: v1.4.0
product_type: Enterprise Runtime Platform / Core Executable

## 本版定位

本包不是玩具版。它是在 `MRL_UniversalRuntimeLanguage_Core_v1_3_0` 基礎上，補入真正產品級 RuntimeOS 功能層：

- 真 AI 模型接線：`MRL_RuntimeOS_AIModelGateway_Service_v1`
- 真技能模組註冊與執行：`MRL_RuntimeOS_SkillModule_Service_v1`
- 真 Artifact 分片傳輸與落盤：`MRL_RuntimeOS_ArtifactTransfer_Service_v1`
- 真 Blender 3D 模型橋接源碼吸收：`MRL_RuntimeOS_3DModelBridge_Service_v1`

## 已沙盒驗收

```bash
npm run acceptance
```

驗收項包含：

- MultiLanguageAdapters
- MetaIR / ParticleIR
- ContextGraph / RuntimeGraph
- AttentionRoute / RuntimeExecute
- RoundTripVerify
- RuntimeNode / RuntimeMesh
- AIModelGatewayProtocol
- SkillModuleRegistry / SkillExecution
- ArtifactTransfer
- Blender3DModelBridgeSource

## 真實狀態

- Node RuntimeOS：已可運行。
- AIModelGateway：已實作 Ollama / OpenAI-compatible 真 connector；沙盒用協定 fixture 驗收，DL580 需要真模型 host。
- Blender 3D Model Bridge：已整合使用者上傳 source；`bpy` 需在 Blender runtime 內驗收。
- DL580 常駐：待實機部署驗收。

## 啟動

```bash
npm install
npm start
```

## API 重點

- `GET /api/mrl/health`
- `POST /api/mrl/runtime/execute`
- `GET /api/mrl/runtimeos/ai/health`
- `POST /api/mrl/runtimeos/ai/generate`
- `GET /api/mrl/runtimeos/skills/list`
- `POST /api/mrl/runtimeos/skills/execute`
- `POST /api/mrl/runtimeos/artifacts/begin`
- `POST /api/mrl/runtimeos/artifacts/chunk`
- `POST /api/mrl/runtimeos/artifacts/assemble`
- `GET /api/mrl/runtimeos/blender/bridge/manifest`
