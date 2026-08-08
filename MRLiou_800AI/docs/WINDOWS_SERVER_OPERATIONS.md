# Windows Server Operations Runbook

## Canonical paths

- Runtime configuration: `config\windows_server.runtime.json`
- API token: `secrets\api_token.txt`
- Runtime log: `logs\windows-runtime.log`
- Trace chain: `logs\trace.jsonl` and `logs\trace_state.json`
- Reversible snapshots: `data\snapshots\`
- Audit runs: `runs\`

## Startup model

The installer can register `MRLiou-800AI-Runtime` as a Scheduled Task that runs under `SYSTEM`, starts at server boot, restarts on failure, and prevents duplicate instances.

## Health checks

```powershell
Invoke-RestMethod http://127.0.0.1:8787/health
.\scripts\windows\Get-RuntimeStatus.ps1
```

A healthy response includes `ok: true`, `origin_signature: MrLiouWord`, a trace anchor, and `authentication_enabled: true`.

## Log inspection

```powershell
Get-Content .\logs\windows-runtime.log -Tail 100
Get-Content .\logs\trace.jsonl -Tail 20
```

## Firewall rollback

```powershell
.\scripts\windows\Close-Firewall.ps1 -Port 8787
```

## Recovery

1. Stop the runtime.
2. Preserve the current project directory.
3. Restore `config`, `data`, `logs`, and `runs` from a backup archive.
4. Restore `secrets` only from a trusted encrypted backup.
5. Run verification.
6. Start the Scheduled Task.

All corrective changes should remain additive and versioned according to the Liou Closure Law.
