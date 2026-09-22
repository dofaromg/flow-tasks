# Dependency Tree

## 中文定位

這份相依樹說明 BYOH 母體 Runtime 如何以附加子系統銜接既有
`MRL_MotherModel_v0_1`，不取代父層。Runtime 只連接使用者硬體上的
loopback 模型；Memory、Evidence、Passport、回傳封包與商業契約各自保留
獨立責任與證據邊界。

```text
MRL_AI_Mother_Autonomous_Runtime_Baseline_v1
├─ existing parent: MRL_MotherModel_v0_1
├─ runtime
│  ├─ MRL_mother_runtime_v1
│  │  ├─ MRL_local_model_adapter_v1
│  │  ├─ MRL_memory_vault_v1
│  │  │  └─ MRL_hash_chain_v1
│  │  ├─ MRL_evidence_ledger_v1
│  │  │  └─ MRL_hash_chain_v1
│  │  └─ MRL_passport_registry_v1
│  ├─ MRL_return_bundle_v1
│  │  └─ explicit policy + user-selected files
│  └─ MRL_apiworks_gateway_v1
│     └─ MRL_mother_runtime_v1
├─ user-owned hardware runtime
│  └─ Ollama or llama.cpp on loopback
├─ schemas
│  ├─ MRL Universal Passport
│  ├─ MRL Memory Event
│  ├─ MRL Evidence Event
│  ├─ MRL Model Release
│  └─ MRL Return Bundle
├─ commercial contract layer
│  ├─ BYOH model delivery and return contract
│  └─ Services Agreement blueprint
└─ acceptance
   ├─ package verifier
   ├─ Python integration tests
   └─ PowerShell hardware-neutral live acceptance
```

Python runtime dependencies: standard library only.  
External model API dependency: forbidden by baseline Gate.  
Model weights: delivered through an approved model channel and verified against an MRL Model Release manifest; not committed to the construction repository.

Practical dependency flow／實際相依流程：

```powershell
cd MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts
.\MRL_start_runtime_v1.ps1
# In a second window／在第二個視窗：
.\MRL_acceptance_v1.ps1
```

The second command verifies the checksummed package, tests the local Runtime,
and accepts only a loopback model that can complete the audited Memory →
Evidence → Passport loop. 第二個指令會驗證封包、測試本機 Runtime，並且只有
完成 Memory → Evidence → Passport 證據閉環的 loopback 模型才會通過。
