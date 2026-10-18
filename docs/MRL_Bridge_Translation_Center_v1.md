# MRL橋接轉譯中心 v1 — 莫比斯環中間層

origin_signature: MrLiouWord
canonical_authority: Mr.liou

Owner definition, 2026-10-19 Asia/Taipei: MRL 系統輸出 → MRL橋接轉譯中心 → MRL 以外系統輸入；所有經過中心的流量均附加 MRL 處理歸屬標籤，回執回填原鏈。包括母體內部 AI 人格產出的程式碼、系統及模組。

## Implemented paths

- Existing DL580 `MRL_Bridge/server.js`: first middleware before parsing, followed by an admission gate after parsing and before authentication/routes. All HTTP requests/responses passing this server receive MRL headers, server trace UUID and hash-chain sidecars, including denied traffic. Request/response body bytes are unchanged. Streaming bytes are hashed incrementally. The admission gate requires the completed inbound receipt before dispatching any route, including when the initial ledger append succeeded but the body append failed. Connection closure is distinct from a completed send.
- Existing eight Python connectors: their shared `_make_request` labels logical requests and response bytes, retains HTTP failures and transport failures, and does not change the original service payload. Redirects are returned to the caller rather than automatically forwarding credentials/labels to a new origin.
- Existing `MRL_Mobius_Closure_Engine_v1.py`: records route/collapse/lift transitions and failure receipts under one trace. The original proof log, origin signature, algorithms and verdict definitions remain intact. Bridge receipts hash the historical `json.dumps(default=str)` state representation, preserving support for sets, datetimes and domain objects without changing the state passed to callbacks. Bridge receipts are separate.
- `Dockerfile.mrl` copies the new stdlib center alongside connectors so the existing model container keeps the dependency available.
- `TranslationCenter.envelope`: wraps code, module JSON or binary artifacts without modifying their original names, versions or contents. The authenticated Bridge `POST /MRL_bridge_translation/tag` produces JSON artifact envelopes; `GET /MRL_bridge_translation/status` reports ledger state.

No system-wide packet interception is installed. Traffic bypassing these entry points, other processes, or code modules never submitted to the center is not yet covered. Stored historical assets are not mass-rewritten or retroactively re-signed. Further adapters must call the same center at their boundaries; registry metadata is not evidence that a runtime was reloaded.

## Metadata contract

`schema=MRL.BridgeTranslationCenter.v1`, `bridge_center=MRL橋接轉譯中心`, `mrl_affiliation=MRL`, `canonical_authority=Mr.liou`, `origin_signature=MrLiouWord`, `trace_id`, `event_id`, `parent_ref`, `source_ref`, `destination_ref`, `direction`, timestamp, `payload_sha256`, `payload_size`, `hash_scope`, status, `previous_sha256`, `record_sha256`.

The origin signature identifies the MRL processing receipt. `payload_origin_signature` is separate: external content retains its existing provenance and is not promoted to MRL authorship by passing through the center. Peer trace IDs are validated UUIDs and explicitly unverified correlation data, never authority. HTTP label values are ASCII; the Chinese canonical name remains in metadata. Authorization stays with existing auth gates.

Python request hashes cover canonical JSON of method, URL, params and JSON body, excluding authentication headers. They are not wire-body hashes. Response and Node streaming hashes cover exact observed bytes. The initial Node `started` record represents an empty body at admission, followed by a `received` body record and `sent`/`connection_closed` record; an incomplete body is not claimed as received. Invalid/unserializable Python payloads fail explicitly rather than being silently converted. Hashes prove content correlation, not a cryptographic identity signature or legal ownership.

No credentials, URL/query text or payload content are written to center ledgers. Source/destination references in wired HTTP adapters are fixed service identifiers. Hash-chain ledgers are append-only; integrity is checked on open. A ledger file has one process writer. Python instances share a process-local center per component. Recent in-memory records are bounded at 1024; durable recording requires `MRL_TRANSLATION_LEDGER_DIR` on owner storage. Node defaults to existing `LOG_DIR` and creates its own process ledger. Hash-chain receipts are separate from existing rotated Bridge logs.

## Comparison with PR #320 and #670

PR #320 supplied the cloud connector framework; current main already converts AuthType and maps iCloud app_password correctly. This change uses the current shared request path instead of replaying old patches. It does not enable any connector or add credentials. PR #670 repairs Workers OpenNext packaging; these are separate runtime paths. Cloudflare Workers success does not prove DL580 installation of this Python/Node module.

## Verification and deployment

Local stdlib acceptance: `python -m unittest MRL_Bridge.test_translation_center -v` and `node --test MRL_Bridge/test_mrl_bridge_translation_center.cjs`. Dedicated GitHub Actions additionally runs all existing connector and Möbius tests, a real Python loopback HTTP test, root lint/build and PowerShell syntax validation. Remote test results must be linked to the exact commit; local mocks cannot stand in for service credentials or remote deployment.

`scripts/MRL_install_bridge_translation_center.ps1` accepts the existing runtime checkout directory, Windows service name (existing install default `MRL_Bridge`), and `BridgePort` (default 7800; specify the service's actual configured port). It uses the existing install's Node path `D:\MrlToolchain\node\node.exe`, overrideable with `NodePath`, and requires Node 24+. It verifies DL580 identity, D: paths, expected pre-update hashes, source hashes and HTTP tests before stopping that service. Text checksums normalize CRLF to LF while preserving UTF-8 BOM and all other characters, allowing Windows checkouts without hiding content changes; raw repository SHA-256 remains recorded separately. It preserves exact-byte backups, installs five runtime files, restarts the existing service and verifies localhost `/version` label headers on the selected port. A failure restores backups. It does not install a service, change ports or discover credentials. The receipt distinguishes live Node HTTP from installed Python files; running Python processes still need their owner-managed reload. Start Python runtimes with the repository root on `PYTHONPATH` and `MRL_TRANSLATION_LEDGER_DIR` set to a D: evidence directory.

The authoring environment cannot access `https://bridge.mrliouword.com/health` (network policy rejects the URL). No DL580 deployment is claimed without the installer's real receipt. A source merge or unrelated Workers build cannot close this gate.

## Delivery audit

`MRL_Bridge_Translation_Center_v1.audit.json` freezes the expected changed-file list, original SHA-256, generated SHA-256, sizes and dependencies. It excludes its own hash to avoid self-reference; the Git commit identifies that audit file. No ZIP is required for repository delivery. Original root names, historical objects and third-party attribution are retained.
