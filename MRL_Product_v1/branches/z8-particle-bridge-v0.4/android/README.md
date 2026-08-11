# Android additive adapter

This is a buildable Android 8.1-compatible independent app. It stores the DL580 endpoint and HMAC secret locally, sends signed `z8.xiaozhi.voice` / `z8.line.text` test events, and exposes a signature-protected explicit broadcast contract for the final observed hooks.

It does not guess or replace the existing 小智/微聊 packages. Automatic observation remains bound to `android/evidence-contract.json` and the two owned-device captures.

Build on DL580 after installing JDK 17, Android SDK 34 and Gradle 8.2+:

```powershell
.\scripts\Build-Z8AndroidAdapter.ps1
```

The debug APK is technically code-signed by the Android debug keystore. That signature is package integrity only; it is not an official contract or control gate.
