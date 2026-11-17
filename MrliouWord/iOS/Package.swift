// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MRLTagCore",
    products: [.library(name: "MRLTagCore", targets: ["MRLTagCore"])],
    targets: [
        .target(name: "MRLTagCore", path: "MrliouWord/Models",
            exclude: ["AppModel.swift", "ScanMode.swift"], sources: ["MRLTagSelection.swift", "MRLTagTransfer.swift"]),
        .testTarget(name: "MRLTagCoreTests", dependencies: ["MRLTagCore"], path: "Tests")
    ]
)

