# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
