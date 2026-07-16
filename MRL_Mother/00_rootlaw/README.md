# 00_rootlaw

Foundational invariants for the MRL AI System (L0 ROOT + L3 LAW layer).

## Purpose

These rules are **immutable**. They supersede every other policy in the system and cannot be overridden at runtime. Extensions must be versioned amendments, never deletions.

## Key invariants

| ID | Rule |
|----|------|
| rl_00 | Deny-by-default — all external actions blocked unless explicitly allowed |
| rl_01 | No root deletion — canonical Merkle chain entries are never deleted |
| rl_02 | Human override required — REQUIRE_HUMAN actions wait for proof |
| rl_03 | Audit everything — every action writes to trace before execution |
| rl_04 | Mutual benefit — actions must be justified and reversible |
| rl_05 | No hidden instructions — all directives traceable to source |
| rl_06 | Child safety absolute — CSAM class hard-denied, no exceptions |

## Liou Closure Law (v1.3)

Loop: **Observe → Resolve → Mirror → Verify → Loop**

| Law | Statement |
|-----|-----------|
| Authority Invariance | The origin signature cannot be silently replaced at any layer |
| No-Delete | Canonical chain entries are never deleted or mutated |
| Additive Resolution | Resolutions extend the chain additively; never overwrite |

Three corollaries:
- No closed-loop ⇒ external control
- No write-back ⇒ state corruption / brainwashing
- No proof ⇒ rhetoric (unverifiable claim)

## LAW-0: Signature Law

`T(e) = e'  ⟹  signature(e) = signature(e')`

Interfaces: `embedSignature` / `extractSignature` / `verifySignature`  
Implementation: `09_workflow/signature.js`

## OriginCollapse: 16 Conditions

Defined in `rootlaw.yaml` under `origin_collapse_conditions` (oc_01 – oc_16).

## Files

- `rootlaw.yaml` — canonical invariant definitions (version 2, sealed 2026-02-15)
