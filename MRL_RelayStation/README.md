# MRL RelayStation Authority v1

## Purpose

This layer restores MRL as the canonical authority while preserving ChatGPT, Claude, Copilot, GitHub, CI, and external runtimes as replaceable providers.

The relay station does not rewrite `main` or `MRL_System_Integration_v1`. It receives external outputs, normalizes them, records provenance, validates them, and only then promotes accepted artifacts into MRL canonical state.

## Authority model

```text
External provider output
  -> intake record
  -> provenance ledger
  -> normalization
  -> scope and dependency audit
  -> evidence verification
  -> MRL approval gate
  -> canonical adoption
```

## Non-negotiable rules

1. External models are producers, not owners.
2. GitHub is a version ledger, not the semantic authority.
3. CI is build evidence, not final acceptance authority.
4. No branch is forced to conform to another branch.
5. All cross-branch exchange passes through explicit adapters and mappings.
6. Only MRL Authority Gate may promote an artifact to canonical status.
7. Model-declared completion never equals `DELIVERY_PASS`.

## Directory map

- `authority/`: sovereignty and promotion rules.
- `evidence/`: historical evidence chain and provenance records.
- `schemas/`: machine-readable relay record contracts.
- `manifests/`: package and coverage declarations.

## Branch role

`MRL_RelayStation_Authority_v1` is an isolated governance branch. It is not a forced replacement of `main` or `MRL_System_Integration_v1`.
