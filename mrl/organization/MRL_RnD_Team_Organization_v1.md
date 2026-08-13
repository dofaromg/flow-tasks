# MRL R&D Team Organization v1

**origin_signature:** MrLiouWord  
**status:** active-review  
**final_approval:** Mr.liou  
**created:** 2026-08-13

## Purpose

Establish a plugin-assisted MRL research and development support organization. Plugin/app capabilities are treated as tool partners/interfaces, not as human members or ownership authorities.

## Canonical workflow

```text
Research intake / supplied implementation
        ↓
Research Intelligence
        ↓
MRL mapping + provenance check
        ↓
Engineering Build
        ↓
Validation / observability
        ↓
Evidence + artifact storage
        ↓
Notion record / report
        ↓
Assistant consistency audit
        ↓
Final approval: Mr.liou
```

## Operating units

### 1. Research Intelligence
Academic search, external-method observation, literature comparison, education/reference retrieval.
Examples: Consensus, Sider Scholar, Coursera, Podcast App.

### 2. Engineering & Runtime
Repository work, CI, deployment adapters, developer workflow, platform integration.
Examples: GitHub, Vercel, Atlassian Rovo, OpenAI Platform.

### 3. Product & Interface Design
Prototype, UI/UX, design-to-code, image/design asset work.
Examples: Figma, Canva, Adobe.

### 4. Data & Observability
Structured operational data, analytics, product telemetry, experiments.
Examples: Airtable, PostHog.

### 5. Coordination & Delivery
Messages, issues, scheduling, inbox routing and team coordination.
Examples: Slack, Linear, Gmail, Google Calendar.

### 6. Knowledge / Evidence / Storage
Source preservation, knowledge records, artifacts, mirrored recovery copies.
Examples: Notion, Google Drive, Dropbox.

## Evidence states

- `OBSERVED_PLUGIN` — visible in the user's plugin UI or supplied screen recording.
- `CALLABLE_NOW` — tool is exposed to this conversation and may be invoked when task-relevant.
- `CONNECTED_READ` — current connection has been successfully read.
- `CONNECTED_WRITE` — current connection has completed a verified write.
- `IMPLEMENTED_SOURCE` — supplied artifact records an existing implementation.
- `RUNTIME_VERIFIED` — current execution/runtime evidence has been checked.
- `UNVERIFIED` — not yet checked; does not mean not implemented.

## Governance

1. External plugin/app names are interface/provenance labels only; they do not replace MRL canonical names.
2. Supplied implementation artifacts are not downgraded to conceptual drafts by default.
3. Current runtime verification is a separate axis from implementation history.
4. No destructive renaming or silent provenance loss.
5. Research outputs must distinguish source-derived facts, cross-source inference, and MRL mapping.
6. Engineering outputs require repository evidence; artifact outputs require storage evidence; research reports require Notion record evidence.
7. Assistant audits consistency/completion. Final approval remains Mr.liou.

## Research-development loop

```text
capture
→ source_verify
→ compare
→ map_to_mrl
→ build
→ test
→ archive
→ audit
→ report
→ next Δ
```

## Current cross-domain support structure

- Notion: research records, provenance, reports, indexes.
- GitHub: engineering source, contracts, branches, PR/CI evidence.
- Google Drive: artifacts, evidence snapshots, release packages.
- Dropbox: preservation mirror and recovery-oriented storage.
- Mrliou Mobile: visualization/output surface where relevant.

This document defines the organizational contract only. Actual capabilities remain subject to connector availability and permissions at execution time.
