# MRL Bridge atomic create_only v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
source: dofaromg/flow-tasks PR #694  
parent: ddd011c00497bb03bb52892b9c12582a554e734f  
Date: 2026-11-01 Asia/Taipei

## Contract and dependency tree

PR694 client → /version.capabilities.file_write_create_only (boolean true) → authenticated POST /MRL_file/write create_only:true → configured root policy → filesystem O_CREAT|O_EXCL (wx+) → descriptor write/fsync/byte readback/SHA256 → created_exclusively:true → existing PR694 independent HTTP readback.

Conflict returns 409; invalid paths/input 400; permission/read-only errors 403; missing root 503; storage/readback errors 500. Empty base64 is valid. Non-create-only writes are rejected. Legacy GET /MRL_write returns 405 so it cannot bypass the new file write policy. Other privileged execution APIs retain existing administrative powers; this change is not a sandbox for a compromised administrator/API key.

MRL_BRIDGE_WRITE_ROOT must explicitly identify an existing local directory (DL580 intended namespace: D:\MRL_Mother). Missing configuration advertises false and denies writes; invalid configured roots fail startup. The service recursively creates only ordinary child directories. UNC/device/drive-relative paths, ADS, reserved devices, short-name aliases, trailing dots/spaces, mixed separators and traversal are rejected on Windows. Existing symlinks/junctions/alias parents are refused, final symlinks conflict at exclusive open.

Security prerequisite: root and every ancestor require owner/service-only mutation ACLs. Node core has no portable Windows handle-relative no-reparse open; lstat/realpath checks alone cannot exclude concurrent hostile local parent replacement. Do not enable this service on shared writable ancestry, network filesystems or unverified reparse configurations. Exclusive creation is atomic; readers may see a partial file while it is written, so it is not atomic publication. Acknowledgement occurs only after fsync/readback. Process crash can leave a partial exclusively created file; preserve it for owner review rather than overwrite/retry that name.

## Reversible deployment and rollback

1. Read installed /version and authenticated system/service configuration. Record running server path, SHA256, service identity, Node version, dependencies and ACLs; never infer installed SHA from GitHub.
2. Keep original installation, service configuration and data untouched. Stage this branch into a new version directory with its dependencies. Record all source hashes. Validate ACLs and local-volume semantics under the service account.
3. Configure existing MRL_BRIDGE_API_KEY through the existing protected secret mechanism, and MRL_BRIDGE_WRITE_ROOT=D:\MRL_Mother. Never place keys in Git/logs/command arguments. Start staged service on a separate loopback port; run tests, then change service executable/config reference during authorized cutover. Record previous reference for rollback.
4. Use PR694 verifier against the authorized endpoint with a bound credential. It creates a UUID-isolated child and reads back four engineering files plus receipt, verifying bytes/size/SHA256. That proves only the stated receipt scope. Preserve originals and isolated evidence.
5. On failure restore previous service reference/configuration and restart; preserve both versions and evidence. Do not revert data by overwriting originals. Failed individual writes remove only the inode created by that operation; cleanup errors are surfaced and logged as rollback_failed. Empty created directories remain for inspection.

## Validation and status

Local Node regression: 8 groups pass, including twelve independent racing processes (one winner), binary SHA256, refusal to overwrite, parent/final symlinks, Windows path attacks, injected permission errors, write/fsync rollback, and actual server route handlers using dependency stubs. This does not exercise a live authenticated Express/TLS stack. CI adds exact-head Linux/Windows Node regression plus unchanged PR694 Python client regression. Windows CI and exact-head results must be checked after push. Permission failure is deterministic fault injection; deployment still requires real service-account ACL acceptance.

Local Python client tests unavailable: pytest/requests absent. Repository npm run lint/build attempted, both unavailable because next is not installed. No passing claim is made for those checks.

Live GET /version at 2026-11-01 20:04 Asia/Taipei returned HTTP 200: MRL_Bridge_API 3.1.0, Node v20.11.1, win32/x64, hostname WIN-PBVUI7VK2A6, origin_signature MrLiouWord, no capabilities field. This identifies the response, not installed source SHA or service executable path. MRL_BRIDGE_API_KEY is unbound in this execution channel. Authenticated deployment/write-readback remain NOT VERIFIED. No credential was read or printed. No deployment performed; no mother DELIVERY_PASS. Landing Manifest ambiguity remains unresolved until installed-path/hash and independently read-back evidence are obtained.

## Expected delivery and package map

Five actual engineering files, no ZIP:
- MRL_Bridge/server.js: existing API integration, version 3.1.1
- MRL_Bridge/mrl_create_only.cjs: atomic writer and policy
- MRL_Bridge/mrl_create_only.test.cjs: regression and route contract
- .github/workflows/MRL-bridge-create-only.yml: cross-platform exact-head CI
- MRL_Bridge/MRL_create_only_v1.md: provenance, deployment, rollback, limitations

No original files renamed/deleted. Scope includes engineering PR and CI configuration; live CI completion and DL580 acceptance remain separate gates.

## Deployment-path review and CI follow-up

Existing repository installer scripts/MRL_install_bridge_translation_center.ps1 targets service MRL_Bridge and D:\\mrl\\bridge with Node D:\\MrlToolchain\\node\\node.exe. It checks a different historical audit inventory (five older modules) and copies over active files. It is not a supported installer for this new dependency: do not invoke it for this branch. Preserve that installer and audit; use the staged-version service-reference procedure above. No authenticated remote administration channel or secret setter was established in this execution session.

Initial CI exposed missing PyYAML at client test collection; the dependency is now explicit. Linux Node and unchanged PR694 client tests succeeded at 28bd8f23456a9dbbacfd2674130ba995a2803235. Windows checkout failed on unrelated existing root filename :mnt:data.txt; the dedicated matrix now sparse-checks only required test/runtime paths while retaining full Git history for provenance git-show reads. No historical file is renamed or removed. Latest-head Windows results remain the acceptance gate.
