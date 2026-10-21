//
//  ScanControlsView.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import SwiftUI

struct ScanControlsView: View {
    @ObservedObject var scannerManager: ScannerManager
    let mode: ScanMode
    
    var body: some View {
        VStack(spacing: 16) {
            // 掃描進度條
            if scannerManager.isScanning || scannerManager.scanProgress > 0 {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("掃描進度")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Spacer()
                        
                        Text("\(Int(scannerManager.scanProgress * 100))%")
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    
                    ProgressView(value: scannerManager.scanProgress)
                        .progressViewStyle(LinearProgressViewStyle())
                }
                .padding(.horizontal)
            }
            
            // 控制按鈕
            HStack(spacing: 20) {
                if scannerManager.isScanning {
                    Button("停止掃描") {
                        scannerManager.stopScanning()
                    }
                    .buttonStyle(SecondaryButtonStyle())
                } else {
                    Button("開始掃描") {
                        scannerManager.startScanning(mode: mode)
                    }
                    .buttonStyle(PrimaryButtonStyle())
                    
                    if scannerManager.scanResult != nil {
                        Button("查看結果") {
                            // 顯示掃描結果
                        }
                        .buttonStyle(SecondaryButtonStyle())
                    }
                }
            }
        }
    }
}

// 自定義按鈕樣式
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundColor(.white)
            .padding(.horizontal, 32)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 25)
                    .fill(Color.blue)
                    .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            )
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundColor(.blue)
            .padding(.horizontal, 32)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 25)
                    .stroke(Color.blue, lineWidth: 2)
                    .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            )
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

#Preview {
    ScanControlsView(scannerManager: ScannerManager(), mode: .easy)
}