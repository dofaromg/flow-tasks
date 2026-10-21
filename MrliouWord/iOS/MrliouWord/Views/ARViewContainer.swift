//
//  ARViewContainer.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import SwiftUI
import RealityKit
import ARKit

struct ARViewContainer: UIViewRepresentable {
    let scannerManager: ScannerManager
    let mode: ScanMode
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        
        // 配置 AR 視圖
        arView.automaticallyConfigureSession = false
        
        // 添加基本的照明
        let anchor = AnchorEntity(world: .zero)
        arView.scene.addAnchor(anchor)
        
        return arView
    }
    
    func updateUIView(_ uiView: ARView, context: Context) {
        // 根據模式更新 AR 視圖配置
        updateARConfiguration(uiView, for: mode)
    }
    
    private func updateARConfiguration(_ arView: ARView, for mode: ScanMode) {
        let configuration = ARWorldTrackingConfiguration()
        
        switch mode {
        case .easy:
            configuration.sceneReconstruction = .mesh
        case .explore:
            configuration.sceneReconstruction = .meshWithClassification
        case .professional:
            configuration.sceneReconstruction = .meshWithClassification
            configuration.frameSemantics = [.sceneDepth, .smoothedSceneDepth]
        }
        
        if !scannerManager.isScanning {
            arView.session.run(configuration)
        }
    }
}