# Dependency Tree

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
│  └─ MRL_apiworks_gateway_v1
│     └─ MRL_mother_runtime_v1
├─ local runtime service
│  └─ Ollama or llama.cpp on loopback
├─ schemas
│  ├─ MRL Universal Passport
│  ├─ MRL Memory Event
│  └─ MRL Evidence Event
└─ acceptance
   ├─ package verifier
   ├─ Python integration tests
   └─ PowerShell DL580 live acceptance
```

Python runtime dependencies: standard library only.  
External model API dependency: forbidden by baseline Gate.  
Local model weights: intentionally not committed; tracked by future Model Passport.

