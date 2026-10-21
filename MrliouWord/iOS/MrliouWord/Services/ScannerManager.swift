//
//  ScannerManager.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import Foundation
import ARKit
import Combine

class ScannerManager: ObservableObject {
    @Published var isScanning = false
    @Published var scanProgress: Float = 0.0
    @Published var scanResult: ScanResult?
    
    private var arSession: ARSession?
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        setupARSession()
    }
    
    private func setupARSession() {
        guard ARWorldTrackingConfiguration.isSupported else {
            print("ARWorldTracking not supported")
            return
        }
        
        arSession = ARSession()
    }
    
    func startScanning(mode: ScanMode) {
        guard let session = arSession else { return }
        
        let configuration = ARWorldTrackingConfiguration()
        
        // 根據模式調整配置
        switch mode {
        case .easy:
            configuration.sceneReconstruction = .mesh
            configuration.frameSemantics = .sceneDepth
        case .explore:
            configuration.sceneReconstruction = .meshWithClassification
            configuration.frameSemantics = [.sceneDepth, .smoothedSceneDepth]
        case .professional:
            configuration.sceneReconstruction = .meshWithClassification
            configuration.frameSemantics = [.sceneDepth, .smoothedSceneDepth]
        }
        
        session.run(configuration)
        isScanning = true
        
        // 模擬掃描進度
        simulateScanProgress()
    }
    
    func stopScanning() {
        arSession?.pause()
        isScanning = false
        scanProgress = 0.0
    }
    
    private func simulateScanProgress() {
        Timer.publish(every: 0.1, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self, self.isScanning else { return }
                
                self.scanProgress += 0.01
                if self.scanProgress >= 1.0 {
                    self.completeScan()
                }
            }
            .store(in: &cancellables)
    }
    
    private func completeScan() {
        isScanning = false
        scanProgress = 1.0
        
        // 創建掃描結果
        scanResult = ScanResult(
            id: UUID(),
            timestamp: Date(),
            modelURL: nil, // 實際實現中會有真實的模型URL
            previewImage: nil
        )
    }
}

struct ScanResult {
    let id: UUID
    let timestamp: Date
    let modelURL: URL?
    let previewImage: Data?
}