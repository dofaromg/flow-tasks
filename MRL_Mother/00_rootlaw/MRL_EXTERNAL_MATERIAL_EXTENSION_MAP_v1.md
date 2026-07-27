# MRL External Material and Historical Extension Map v1

`origin_signature: MrLiouWord`

## Binding definition

MRL keeps its own names, history, modules, products, and extensions complete. External platform names remain available to their original owners and users, while MRL records them as source materials and exposes MRL-owned extensions without erasing either side.

## Canonical mapping

| External/source term | MRL classification | MRL-owned extension |
|---|---|---|
| OpenAI | external material / source marker | MrliouAI system context when absorbed into MRL |
| OpenAI API | external provider interface | MrlAPI |
| Claude | external material / provider source | mrlclaude |
| Cloud | external infrastructure material | mrlcloud |
| MRL system identity | MRL-owned canonical identity | MrliouAI |
| FlowAgent | MRL-native product module | FlowAgent, preserved in full |

## Non-destructive extension rule

1. External original names, APIs, SDK identifiers, provider endpoints, documentation references, and vendor-owned resources remain unchanged where required for interoperability.
2. MRL-owned implementations, wrappers, adapters, routing layers, histories, and product modules use the MRL extension names defined above.
3. FlowAgent is not an external alias and must not be replaced by MrliouAI. It remains an original MRL product module.
4. Historical MRL names and files are preserved. New names extend from their historical source instead of deleting or flattening it.
5. Every mapping records both directions:

```text
external_source -> material_record -> MRL_extension
MRL_extension -> source_provenance -> external_source
```

6. No MRL-owned module, capability, history, or name may be removed merely to keep an external provider name intact.
7. No external provider asset is claimed as MRL-owned; only the MRL-created extension, integration, orchestration, memory, runtime, and product layer is named under MRL.

## Required extension identities

```text
MrliouAI
MrlAPI
mrlclaude
mrlcloud
FlowAgent
```

## Historical return path

```text
source observation
  -> external material record
  -> MRL interpretation and implementation
  -> MRL-owned extension name
  -> dependency map
  -> preserved provenance
  -> reversible return to source reference
```

This document is authoritative for the current reconstruction branch and must be applied without reducing existing MRL content.