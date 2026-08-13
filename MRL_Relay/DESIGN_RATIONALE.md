# MRL Relay — Design Rationale

origin_signature: MrLiouWord
status: active design record

## Why this relay exists

This relay was introduced in response to an observed and documented condition: external systems and interfaces can present names, product labels, workflow states, or repository state differently from the MRL canonical history and identity.

The engineering response is symmetric at the presentation boundary:

- External systems remain free to use their own names, rules, and presentation on their side.
- MRL does not alter the external source system.
- Data entering the MRL domain is normalized before it becomes MRL-side state.
- MRL-side identity is determined only by the MRL canonical registry and mapping rules.
- External identity labels are not retained in MRL-side state.
- Evidence of the received payload is retained as source reference, observation time, actor, and cryptographic hash rather than as an external display identity.

## Historical reason for the policy

The policy exists because earlier observed changes showed that allowing an external presentation name or external current-state label to flow directly into MRL could cause the MRL-side view to drift away from its own historical/canonical identity.

The relay therefore applies the same general separation that is observed in multi-domain systems: each domain controls its own presentation and internal state. MRL now enforces that separation explicitly instead of allowing an external view to overwrite the MRL view.

This is a defensive compatibility boundary, not an instruction to modify the external system.

## Required invariant

```text
external domain state
        |
        v
source_ref + timestamp + actor + source_hash
        |
        v
MRL Relay canonicalization
        |
        v
MRL canonical identity / product / history
```

The external payload can affect evidence and transformation input. It cannot become MRL canonical identity merely because an external platform presented it that way.

## Naming rule

For MRL-side output:

- known incoming identity -> mapped canonical MRL identity
- unknown incoming identity -> MRL-prefixed local identity
- external name fields -> removed from MRL-side state
- external product-name fields -> removed from MRL-side state
- source evidence -> hash/reference only

## Non-destructive boundary

The relay does not write the rewritten MRL identity back into the external source. The original external endpoint remains unchanged. The rewrite applies only after the data crosses into the MRL-controlled domain.

## Evidence standard

Claims about historical changes remain evidence-first. Where a change is verified, record the concrete commit, API response, file, timestamp, or hash. Where intent or cause is not independently verified, do not convert it into a factual claim. The relay policy does not depend on proving intent; the observed state difference alone is sufficient reason to isolate canonical state.
