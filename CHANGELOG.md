# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed — MRL 3DScanner ProductBridge main integration (2026-10-21)

- Integrate the remaining PR #678 safety changes onto exact main cc5b0059,
  preserving its Tailscale-only entry, startup wait, names and source lineage.
- Keep upload responses, iOS Codable and local PowerShell acceptance consistent;
  strip legacy scan file paths, limit scan listing, validate task/ACL definitions,
  contain Node descendants and defer recovery writes until every listener binds.
- Preserve original patch hashes and admit only the audited main/#678 predecessor
  hashes for upgrades; add API, task-drift, native Windows recovery and Swift tests.
- GitHub-hosted CI and DL580/iPhone/reboot acceptance are distinct evidence gates.
- origin_signature: MrLiouWord; canonical_authority: Mr.liou.

### Fixed — DL580 naming restoration preflight (2026-10-14)

- PR #669 now defaults to evidence-only preflight on DL580 D:, with unique receipts,
  log/file SHA-256, original timestamps, reference counts and read-only database catalog checks.
- Preserve the a459a758 user-requested revert in Git history; add fail-closed parsing,
  reference-before-path ordering, reference I/O failure handling and database conflict handling
  from 8386e5b for review. Do not infer missing targets from same-leaf folders.
- Hold all restoration, including explicit -Apply, until the actual rename log,
  authoritative per-item names, original reference bytes and database/application settings
  have been reconciled. Preflight exit 3 is HOLD, never a restoration PASS.
- PowerShell/DL580 execution remains NOT_RUN in this repair session; source inspection
  and readback do not establish local deployment or runtime acceptance.
- origin_signature: MrLiouWord; canonical_authority: Mr.liou.

### Fixed — MRL Codespace Monitoring recovery (2026-10-13)

- Restore the existing a071fa7 / d629afe monitoring fixes after f00d493 reverted
  them to the main version; retain all three historical commits and original paths.
- Fail on unavailable CODESPACES_TOKEN, API or parsing failures, incomplete listing,
  and required label/issue operations; update an existing warning instead of
  creating another, and serialize monitoring jobs across refs.
- Add credential-free regression execution to this workflow for PRs and before
  scheduled/manual monitoring. PRs never run the token-backed monitoring job.
- CODESPACES_TOKEN needs Codespaces read on the selected repository for a
  fine-grained PAT, or codespace scope for a classic PAT; issue operations keep
  using GITHUB_TOKEN. Secret values are neither inspected nor stored.
- Keep the existing 30-day retention estimate; it is not an authoritative
  per-Codespace deletion deadline. No Codespace is deleted by this workflow.

### Added — Multi-cloud connector orchestration

- Add one-command authentication checks and synchronization across all eight
  cloud connector types, with strict CI exit behavior and JSON output.
- Add a scheduled/manual GitHub Actions connector audit backed only by secrets.
- Correctly load typed authentication settings and iCloud username/app-password
  credentials from the environment.

### Fixed — MRL external synchronization operations

- Preserve external sync candidates through content-addressed branches and draft PRs;
  never directly push protected main, force-update, auto-merge or erase review history.
- Record source commit, original paths, SHA-256 and actual outcomes; fail on partial
  source failures and preserve configured skip conflicts for files and directories.
- Keep receipts and recoverable candidates when publishing is blocked; separate
  engineering transport status from commercial release and rights grants.
- Add offline sync/publication regression tests and an owner operations runbook.

## [3.0.0] - 2026-02-09

### Changed
- **Version Update**: Updated project version from v1.0.0 to v3.0.0 across all documentation
- Updated version references in:
  - README.md - Main project documentation
  - package.json - Node.js package version
  - All deployment documentation (DEPLOYMENT_*.md files)
  - API specifications (P.MetaEnv.openapi.*)
  - Structure documentation (STRUCTURE.md)
  - Configuration files (MrliouAgi.json)
  - Python modules (world.py)

### Added

#### 2026-01-03 - FlowHub Integration Export Package
- **Commit**: [`ffebfa0`](https://github.com/dofaromg/flow-tasks/commit/ffebfa0ecb172f43257bb565d7b0012e4b511763)
- Added complete FlowHub integration export package with patches and git bundle
- Created FLOWHUB_EXPORT_PACKAGE.md documentation (180 lines)
- Created FLOWHUB_INTEGRATION_GUIDE.md with integration instructions (283 lines)
- Generated 6 patch files for incremental application (total 76 KB)
- Created flowhub-integration.bundle for complete commit history (24 KB)
- Package includes Wire-Memory Integration validation and Memory Cache Disk Mapping system
- Provides three integration methods: Git Bundle (recommended), Patch files, and Manual copy
- All content ready for application to dofaromg/flowhub repository
- **Co-authored-by**: dofaromg <217537952+dofaromg@users.noreply.github.com>

---

## Version History References

For detailed version history and commit references, see:
- [FlowHub Export Package Documentation](FLOWHUB_EXPORT_PACKAGE.md)
- [FlowHub Integration Guide](FLOWHUB_INTEGRATION_GUIDE.md)
## [2026-01-12] - MrliouWord iOS 3D Scanner Initial Implementation

### Added
- **MrliouWord iOS 3D Scanner Project** - Revolutionary 3D content creation ecosystem
  - Three-mode scanning system (Easy/Explore/Professional)
  - SwiftUI + ARKit + LiDAR core architecture
  - AI snapshot modeling integration
  - 7 core Swift source files (414 LOC)
  - Complete project documentation (README.md, XCODE_SETUP.md)
  - Implementation summary: [MRLIOUWORD_IMPLEMENTATION_SUMMARY.md](MRLIOUWORD_IMPLEMENTATION_SUMMARY.md)
  - Reference commit: [c785f4d](https://github.com/dofaromg/flow-tasks/commit/c785f4d33e92a46ce2515da4ab7360f1685ed43b)

### Documentation
- Added MrliouWord section to main README.md
- Created comprehensive implementation summary with bilingual support (EN/中文)
- Xcode setup guide for project configuration

### Project Structure
```
MrliouWord/
├── iOS/MrliouWord/
│   ├── App/ (MrliouWordApp.swift, ContentView.swift)
│   ├── Models/ (ScanMode.swift)
│   ├── Services/ (ScannerManager.swift)
│   └── Views/ (ARViewContainer, ModeSelector, ScanControlsView)
├── README.md
├── XCODE_SETUP.md
└── LICENSE
```

### Technical Highlights
- Modern SwiftUI architecture with reactive state management
- ARKit + LiDAR integration for high-precision 3D scanning
- CoreML AI pipeline for on-device machine learning
- Modular service layer for extensibility

---

## [Previous Changes]

For changes before 2026-01-12, please refer to the git commit history.



## 2026-09-18 — bounded MRL sync publication

- Default to candidate bundle preparation; require explicit main dispatch for branch/PR publication.
- Reject mismatched Git destinations, multiple push URLs and URL rewrites before network access.
- Preserve source authorship and separate origin authority, trigger account and bot executor.
- Add negative publication and attribution regression tests. origin_signature: MrLiouWord.


## 2026-09-18 — Mrliou structure-index authorization enforcement

- Connect the existing DENY-by-default MRL authorization registry to the structure-index workflow, scanner/generator entry points and combined runner. No active grants are added.
- Reject absent, malformed or nonmatching grants before source/index access; recheck before artifact upload and remove always-upload fallback to historical index files.
- Validate with disposable synthetic repositories; PR events do not run the production index job. Preserve prior evidence, original canonical artifact names and unrelated deployment routes.
- See `docs/Mrliou_Structure_Authorization_v1.md` for exact grant scope, trust limits and separate patch/CI/main enforcement states.
- origin_signature: MrLiouWord; implementation assistance: ChatGPT / Codex; provider: OpenAI; rights transfer: NOT_GRANTED.


### 2026-09-18 — MRL structure authorization R03 re-audit

- Propagate recursive authorization denial; recheck direct scanner reads and in-memory renderers, enforce actual path/depth, and reject symlinked historical indexes.
- Carry authorized depth through smart-updater and common runner without widening grants.
- Add seven behavioral regressions and delivery payload/dependency integrity validation. Preserve prior evidence and origin_signature: MrLiouWord.
