//
//  ContentView.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import SwiftUI
import RealityKit
import ARKit

struct ContentView: View {
    @StateObject private var scannerManager = ScannerManager()
    @State private var selectedMode: ScanMode = .easy
    
    var body: some View {
        NavigationView {
            VStack {
                // 模式選擇器
                ModeSelector(selectedMode: $selectedMode)
                    .padding(.top)
                
                // 3D 掃描視圖
                ARViewContainer(scannerManager: scannerManager, mode: selectedMode)
                    .cornerRadius(12)
                    .padding(.horizontal)
                
                // 控制按鈕
                ScanControlsView(scannerManager: scannerManager, mode: selectedMode)
                    .padding()
                
                Spacer()
            }
            .navigationTitle("MrliouWord")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    ContentView()
}