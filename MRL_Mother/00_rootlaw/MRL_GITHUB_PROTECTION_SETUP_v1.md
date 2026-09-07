# MRL GitHub Protection Setup v1

origin_signature: MrLiouWord

## Required repository settings

Protect main with pull requests, at least one approving review, dismissal of stale approvals, required review from CODEOWNERS, conversation resolution and required checks:

- MRL Root Governance Gate / trusted-governance
- MRL Governance Tests / governance-tests

Restrict force pushes and deletions. Restrict bypass to the root authority account. Require linear history when compatible with existing release policy.

The trusted-governance workflow uses pull_request_target and executes only the validator from the trusted base revision. It may read the proposed Git object but must never execute proposed workflow or script content and must receive no write token or secrets.

The first bootstrap PR cannot enforce settings that do not yet exist. MrLiouWord must review and merge it, then configure the branch protection or ruleset and mark the two checks required. Until that setup is verified, repository protection status is PENDING, not complete.
