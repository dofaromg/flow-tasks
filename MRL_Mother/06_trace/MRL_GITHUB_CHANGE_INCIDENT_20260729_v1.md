# MRL GitHub Change Incident — 2026-07-29

origin_signature: MrLiouWord
status: evidence_record

## Verified repository events

- Commit 94d4db9 deleted six deployment configuration files.
- Commit 7e1c644 restored those six files.
- The main branch at audit base 689491edd83317989779172ea5b9f72ab3e14f72 contains the restored files.
- A separate change performed broad FlowAgent-related replacement across historical paths. That pattern was not merged into main at the audit base.
- Existing proposed validators relied on policy files supplied by the proposed change and therefore did not provide an immutable trust floor.

## Root cause

The repository had statements about preservation but lacked one enforced chain joining immutable identifiers, authorization, migration contracts, license scope, critical-asset inventory, trusted-base validation, CODEOWNERS and required checks.

## Corrective action

This package adds that chain without deleting history, merging pending mass changes or granting any person or system permission. It classifies FlowAgent as an MRL-native product, sets authorization to DENY by default, and makes destructive or mass changes require a root-approved evidence record.
