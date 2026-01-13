# MrliouWord Xcode Project Setup Guide

## Overview

The MrliouWord iOS project contains all the necessary Swift source files but requires Xcode to create the project file (.xcodeproj). This is the standard approach for iOS development.

## Source Files Included

✅ All Swift source files are present and ready:

- **App Layer** (`iOS/MrliouWord/App/`)
  - `MrliouWordApp.swift` - App entry point
  - `ContentView.swift` - Main view

- **Views** (`iOS/MrliouWord/Views/`)
  - `ARViewContainer.swift` - AR view wrapper
  - `ModeSelector.swift` - Mode selection UI
  - `ScanControlsView.swift` - Control buttons

- **Models** (`iOS/MrliouWord/Models/`)
  - `ScanMode.swift` - Scan mode enumeration

- **Services** (`iOS/MrliouWord/Services/`)
  - `ScannerManager.swift` - AR scanning logic

## Creating the Xcode Project

### Prerequisites
- **macOS** Ventura 13.0+
- **Xcode** 15+
- **iOS 16.0+** deployment target

### Step 1: Create New Project in Xcode

1. Open Xcode
2. Select "Create a new Xcode project"
3. Choose **iOS** → **App** template
4. Configure the project:
   - **Product Name**: MrliouWord
   - **Organization Identifier**: com.mrliou
   - **Bundle Identifier**: com.mrliou.MrliouWord
   - **Interface**: SwiftUI
   - **Language**: Swift
   - **Minimum Deployments**: iOS 16.0

### Step 2: Set Project Location

1. Navigate to this directory: `MrliouWord/`
2. Replace the generated project with this structure

### Step 3: Add Source Files

1. Delete the generated template files
2. Add the existing source file groups:
   - Right-click project → "Add Files to MrliouWord..."
   - Select `iOS/MrliouWord/` directory
   - ✅ Check "Create groups"
   - ✅ Check "Add to targets: MrliouWord"

### Step 4: Configure Build Settings

#### Info.plist Keys (Privacy)
Add these usage descriptions:
```xml
<key>NSCameraUsageDescription</key>
<string>MrliouWord需要使用相機來進行3D掃描</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>MrliouWord需要定位資訊來提供AR體驗</string>
```

#### Required Frameworks
The following frameworks will be automatically linked:
- SwiftUI (implicit)
- ARKit
- RealityKit
- Combine

#### Capabilities
- ✅ Enable "ARKit" capability

### Step 5: Configure Deployment Target

- Set **iOS Deployment Target** to `16.0`
- Supported devices: iPhone, iPad

### Step 6: Build and Run

1. Select a device with LiDAR sensor:
   - iPhone 12 Pro or later
   - iPad Pro (2020 or later)
2. Press **Cmd + R** to build and run

## Project Structure

```
MrliouWord/
├── MrliouWord.xcodeproj    (Create this in Xcode)
├── iOS/
│   ├── MrliouWord/
│   │   ├── App/
│   │   │   ├── MrliouWordApp.swift
│   │   │   └── ContentView.swift
│   │   ├── Views/
│   │   │   ├── ARViewContainer.swift
│   │   │   ├── ModeSelector.swift
│   │   │   └── ScanControlsView.swift
│   │   ├── Models/
│   │   │   └── ScanMode.swift
│   │   └── Services/
│   │       └── ScannerManager.swift
│   └── README.md
├── LICENSE
├── .gitignore
└── README.md
```

## Troubleshooting

### Build Errors

**Issue**: "Cannot find type 'ARView' in scope"
- **Solution**: Ensure RealityKit is imported in ARViewContainer.swift

**Issue**: "Camera permission error"
- **Solution**: Add NSCameraUsageDescription to Info.plist

**Issue**: "LiDAR not available"
- **Solution**: Run on physical device with LiDAR sensor (iPhone 12 Pro+, iPad Pro 2020+)

### Runtime Issues

**Issue**: AR session fails to start
- **Solution**: Check device supports ARWorldTrackingConfiguration

**Issue**: Scanning doesn't work
- **Solution**: Ensure adequate lighting and move device slowly

## Next Steps

1. Create the Xcode project following the steps above
2. Build and test on a LiDAR-capable device
3. Implement additional features from the roadmap
4. Configure code signing for distribution

## Support

For issues or questions:
- Check the main [README.md](README.md) for project overview
- Review [iOS README](iOS/README.md) for iOS-specific details
- Submit issues on GitHub

---

**Note**: The `.xcodeproj` file is intentionally not included in the repository as it's platform-specific and best generated using Xcode's project creation wizard. This ensures compatibility with your Xcode version and macOS environment.
