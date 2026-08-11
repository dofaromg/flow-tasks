# Minimal executable checklist

- [x] Independent branch and immutable scope file created.
- [x] Exact 小智/微聊/LINE particle mapping implemented.
- [x] Raw-body HMAC, constant-time comparison, dedupe, local JSONL ledger, dry-run/apply and revert record implemented.
- [x] `qwen-main` / `muse-agent` and `chatgpt` / `line` runtime switches implemented.
- [x] Actual LINE reply/push adapter implemented; no LINE call occurs in dry-run.
- [x] DL580 PowerShell install/start/test/control/evidence/package scripts created.
- [ ] On DL580, copy `.env.example` to `.env` and set unique local secrets.
- [ ] Run `scripts\\Test-Z8ParticleBridge.ps1` and start in `dry-run`.
- [ ] Run `scripts\\Collect-Z8Evidence.ps1` once for 小智 and once for 微聊 while performing each action on the owned Z8.
- [ ] Put the observed package/activity/intent/ABI/codec values into the Android adapter mapping; build/sign the APK as a technical package.
- [ ] Set LINE channel secret/token and a test target, then verify webhook/reply/push in `dry-run` replay before `apply`.
- [ ] Verify both voice routes with the configured STT/Qwen/TTS endpoints and the real device; the LINE voice endpoint must return a public HTTPS audio URL and duration.
- [ ] Switch only this branch to `apply`; preserve `Set-Z8BridgeMode.ps1 -Mode dry-run` as immediate rollback.

The remaining unchecked items require either DL580/Z8 hardware evidence or locally held secrets. They are dependencies, not new approval gates.
