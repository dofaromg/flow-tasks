# Mrliou Cloud Connector Actions Wiring v1

origin_signature: MrLiouWord

## Verified failure and scope

- Repository: `dofaromg/flow-tasks`.
- Run: https://github.com/dofaromg/flow-tasks/actions/runs/36215035721 (schedule, attempt 1, 2026-09-26T03:30:53Z).
- Source: `c4797c441ba6a12768258127fe6d0ad70cbf3523`; workflow `.github/workflows/cloud-connectors.yml`.
- Checkout, Python 3.11 setup and dependency installation succeeded. Connector verification exited 1 after all eight services returned `not_configured`; all nine injected credential fields were empty. The runpy/Node deprecation warnings were not this failure's cause.
- All eight entries in `config/connectors.yaml` have `enabled: false` and `sync_enabled: false`. `--include-disabled --strict` deliberately attempts all eight anyway. Removing that flag alone would permit an all-skipped, empty audit to exit 0. This repair preserves the complete audit and strict failure behavior.

## Exact secret-to-environment mapping

Configure Actions secrets in the repository **running this workflow**, or an eligible organization scope granting this repository access. Do not put credential values in variables, Git, issues or logs.

| Actions secret | Process environment | Connector credential |
|---|---|---|
| `CLOUD_GITHUB_TOKEN` | `GITHUB_TOKEN` | github.token |
| `NOTION_TOKEN` | `NOTION_TOKEN` | notion.token |
| `DROPBOX_TOKEN` | `DROPBOX_TOKEN` | dropbox.token |
| `GOOGLE_DRIVE_TOKEN` | `GOOGLE_DRIVE_TOKEN` | google_drive.token |
| `VERCEL_TOKEN` | `VERCEL_TOKEN` | vercel.token |
| `ICLOUD_USERNAME` | `ICLOUD_USERNAME` | icloud.username |
| `ICLOUD_APP_PASSWORD` | `ICLOUD_APP_PASSWORD` | icloud.app_password |
| `GITLAB_TOKEN` | `GITLAB_TOKEN` | gitlab.token |
| `HUGGINGFACE_TOKEN` | `HUGGINGFACE_TOKEN` | huggingface.token |

`ICLOUD_USERNAME` is an account identifier, not a password; retaining its existing secret mapping avoids exposing account information or renaming configuration. Audit and sync use identical mappings. `connectors/connector_manager.py::_load_env_credentials` agrees with every process name. `CLOUD_GITHUB_TOKEN` is intentionally different from the process name; no spelling mismatch was found.

The automatic `secrets.GITHUB_TOKEN` used by checkout is not `secrets.CLOUD_GITHUB_TOKEN`. Successful checkout proves nothing about the latter. The GitHub adapter calls `/user`; do not silently substitute a repository installation token for a credential expected to identify an authorized user.

## Scope and visible-setting limits

Neither this job nor the original workflow selects a GitHub `environment`. Credentials stored only in an Environment are unavailable to it. Secrets in another repository, another account, Dependabot settings, or a local `.env` are not automatically provided to this scheduled Actions run. An organization secret must grant the running repository access.

The available repository connector does not expose secrets/variables administration metadata. Empty effective values establish that this run received no credentials; they do **not** distinguish absent settings, another name, another repository, or inaccessible Environment/organization scope. No secret values were requested or retrieved. No environment name is invented by this patch.

Settings: https://github.com/dofaromg/flow-tasks/settings/secrets/actions

## Minimal branch repair

The existing verification step now lists all missing Actions secret **names**, fails before authentication if any are absent, and identifies the lack of Environment selection. Its display name reflects the existing all-declared-service scope. No connector is enabled, disabled, removed, renamed or supplied a fallback token. Sync remains opt-in.

The code repair improves diagnosis; it cannot provision secrets or make missing integrations pass.

## Validation and remaining gates

1. Run `python -m pytest -q tests/test_cloud_connector_workflow_wiring.py connectors/test_connectors.py` with the repository test dependencies. The new tests use synthetic values and a local Python stub: no real authentication or network call.
2. Run the branch's `Cloud connector audit` via workflow_dispatch with `sync=false`. Verify the run's `head_sha` equals the reviewed branch commit. A missing configuration must produce named errors and failure before authentication; no value should be printed.
3. Only after configuration is supplied through approved GitHub settings, repeat on the same branch with `sync=false`. Credential presence is not authentication success; inspect actual per-service statuses and exit code.
4. `connectors/icloud_connector.py::check_connection` currently always returns `not_configured`, including when a password exists. WebDAV/CalDAV implementation is a separate functional blocker to an eight-service PASS. Keep this failure visible; neither weaken `--strict` nor remove iCloud to manufacture a pass.
5. Authentication does not establish synchronization: all `sync_enabled` flags remain false, and live sync is outside this repair's verification.

References: [GitHub secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets), [GitHub variables](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-variables).
