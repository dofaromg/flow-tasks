# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
