# MRL Z8 ParticleBridge v0.4

Independent additive branch for the original plan:

```text
小智 voice event ──> z8.xiaozhi.voice ──> DL580 local runtime ──> selectable voice route
微聊 UI text     ──> z8.line.text      ──> local ledger       ──> LINE Messaging API
LINE webhook      ──> z8.line.text      ──> local runtime      ──> LINE reply
```

The default is `dry-run`. The branch does not replace 小智, 微聊, the Z8 system, or historical files. It adds no contract, whitelist, official-authorization, or approval gate.

## DL580 quick start

```powershell
Set-Location D:\MRL_Product_v1\branches\z8-particle-bridge-v0.4
Copy-Item .env.example .env
notepad .env
.\scripts\Test-Z8ParticleBridge.ps1
.\scripts\Start-Z8ParticleBridge.ps1
```

Send a signed dry-run 微聊 event from another PowerShell window:

```powershell
.\scripts\Invoke-Z8Event.ps1 -Source weiliao -Text "測試" -TargetId "U_TEST"
```

Switch only this branch's engine or voice route:

```powershell
.\scripts\Set-Z8Runtime.ps1 -Engine qwen-main -VoiceMode chatgpt
.\scripts\Set-Z8Runtime.ps1 -VoiceMode line
```

The local listener exposes:

- `GET /health`
- `POST /v1/z8/events` — signed Z8 event input
- `POST /webhook/line` — LINE raw webhook input
- `POST /v1/control/mode` — `dry-run` or `apply`
- `POST /v1/control/engine` — `qwen-main` or `muse-agent`
- `POST /v1/control/voice` — `chatgpt` or `line`
- `POST /v1/control/revert` — record branch-level revert for an event

See [source alignment](docs/SOURCE_ALIGNMENT.md) and the [minimal checklist](docs/BUILD_CHECKLIST.md).

`line` voice mode sends an actual LINE audio message. Its local `LINE_VOICE_ENDPOINT` must prepare an HTTPS audio asset and return `{ "audio_url": "https://...", "duration_ms": 1000 }`; LINE itself is the transport, not a speech synthesizer.
