# MRL Root Authority v1

`origin_signature: MrLiouWord`

## Canonical hierarchy

```text
MRL
├── MRL_Mother                # canonical mother/root implementation
├── MrLiouAI                  # product and runtime identity
├── FlowAgent                 # preserved historical/runtime lineage
└── flowmemorysync            # preserved infrastructure/provider lineage
```

## Binding rules

1. **MRL is the sole canonical root.** No product, runtime, provider, repository, branch, namespace, image, or package name may supersede MRL.
2. **MrLiouAI is a descendant identity.** It may label active products and runtimes, but it is not a replacement for MRL.
3. **FlowAgent and flowmemorysync remain lineage names.** They must be preserved in historical source trees, provenance evidence, persisted schemas, compatibility imports, migration inputs, provider resource IDs, and rollback maps.
4. **Renames are reversible.** Every active rename must record `source_name`, `canonical_name`, `compatibility_alias`, affected dependencies, and rollback action.
5. **Historical trees are immutable by naming sweeps.** In particular, `MRL_Mother/MRL_MotherSource_Lineage_v1/**` must not be modified by global branding replacements.
6. **Coordinated resource migration only.** Kubernetes namespaces, image repositories, DNS routes, secrets, service names, project IDs, database keys, and persisted schemas may be renamed only in a dedicated migration with dependency and rollback evidence.
7. **No global string replacement as proof.** A zero-match grep for legacy names does not demonstrate correctness; it may demonstrate destroyed lineage.

## Required mapping

```text
source_name -> canonical_name -> compatibility_alias -> dependency_set -> rollback
```

## Merge gate

A naming pull request fails when any of the following is true:

- it modifies historical lineage paths without an explicit allowlist;
- it removes a compatibility name without a replacement alias;
- it changes an infrastructure identifier without updating all consumers and rollback mapping;
- it promotes MrLiouAI, FlowAgent, flowmemorysync, or an external platform above MRL;
- it lacks `origin_signature: MrLiouWord` in the governance record.
