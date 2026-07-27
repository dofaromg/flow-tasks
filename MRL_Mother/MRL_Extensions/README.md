# MRL Extensions

`origin_signature: MrLiouWord`

This namespace contains MRL-owned extensions derived from external materials without modifying or claiming the original external platforms.

## Extension identities

### MrliouAI
MRL system identity and integration surface. It does not replace the MRL-native FlowAgent product module.

### MrlAPI
MRL-owned API gateway, routing, policy, memory, trace, and orchestration layer. External APIs retain their provider names at the adapter boundary.

### mrlclaude
MRL-owned Claude material adapter and derived workflow layer. `Claude` remains the external source/provider name.

### mrlcloud
MRL-owned cloud abstraction, deployment, synchronization, and infrastructure control layer. Vendor cloud identifiers remain unchanged where technically required.

### FlowAgent
Original MRL product module. Preserve its name, history, files, packages, interfaces, and runtime lineage in full.

## Boundary pattern

```text
External provider or platform
  -> MRL_Adapters/<Provider>
  -> material/provenance record
  -> MRL_Extensions/<MRL-owned extension>
  -> FlowAgent or other MRL-native product module
```

The external adapter boundary and MRL-owned implementation boundary must remain distinguishable.