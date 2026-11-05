# MRL Tailscale / Bridge receipt v1

origin_signature: `MrLiouWord`  
canonical_authority: `Mr.liou`  
parent: `MRL_Mother/deploy_reference/tailscale`  
source: `config/MRL_Tailscale_Reference.json` (historical reference, **not** current runtime state)

## Existing architecture, not a parallel deployment

- DL580 Windows Server host `WIN-PBVUI7VK2A6`, Tailscale private mesh.
- MRL_Bridge `:7800`, MRL_RuntimeOS `:8790`, and MRL_3DScanner_ProductBridge `:3050` remain **separate** endpoints.
- MRL_Tunnel (Cloudflare) and Tailscale are external connectivity adapters; neither is the MRL mother runtime.
- Continue historical `MRL_AI_SYSTEM/deploy/dl580/MRL_Network_Receipt.ps1`. This script captures a **narrow, additive** Tailscale/Bridge receipt, not a replacement.
- No reconfiguration, service start/stop/restart, remote command, authentication or secret export.

## Execute on DL580 (read-only)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\MRL_Mother\deploy_reference\tailscale\MRL_tailnet_bridge_receipt_v1.ps1 -ProbeLoopback -OutDir D:\mrl\artifacts\network_receipts
```

The script writes one JSON and prints its SHA-256. It inspects Tailscale backend and own tailnet addresses, service status and listening binds. `-ProbeLoopback` additionally performs TCP + GET /health at 127.0.0.1 for `:7800`, `:8790`, `:3050`. Non-200 is FAIL for that endpoint, not proof the whole DL580 is offline. A service bound to tailnet IP alone may be reachable remotely despite a loopback failure.

It intentionally does not record peer identities, all tailnet addresses, machine command lines, request/response bodies, credentials or private files. The receipt contains local hostname and self tailnet IP: keep JSON **on the DL580**, not in a public repository or public issue. Post only receipt path, SHA-256, PASS/FAIL/UNKNOWN and redacted findings in Linear.

## Completion gates

1. **Repository construction**: code committed + exact commit/CI reviewed.
2. **Local receipt**: DL580 script actually executed; JSON non-empty; SHA-256 recalculated.
3. **Cross-device**: iPhone/Mac independently reach authorized endpoints over tailnet, with contemporaneous evidence.
4. **Bridge roundtrip**: separate authenticated app-level request/response evidence; NOT equivalent to Tailscale connectivity.
5. **Deployment**: requires root owner approval; no GitHub green CI can substitute for DL580 live proof.

Until all applicable gates are observed, `remote_roundtrip=UNRUN` and `DL580_DEPLOYMENT=UNRUN`. Preserve source names/versions and original receipts; APPEND_ONLY.
