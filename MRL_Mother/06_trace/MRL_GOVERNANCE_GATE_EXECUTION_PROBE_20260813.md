# MRL Governance Gate Execution Probe — 2026-08-13

origin_signature: MrLiouWord
canonical_root: MRL
purpose: Verify that the repository-level MRL Root Governance Gate actually executes on a pull request event before any further governance claim is treated as enforced.

## Scope

- No rename.
- No deletion.
- No protected-path mutation.
- No authority change.
- No provenance reduction.
- No runtime behavior change.

## Acceptance

This probe is successful only if the GitHub Actions workflow `MRL Root Governance Gate` produces an actual workflow run for the pull request and the trusted validator executes against base/head refs.

A commit message, document statement, or locally reported `DELIVERY_PASS` is not sufficient evidence of enforcement.
