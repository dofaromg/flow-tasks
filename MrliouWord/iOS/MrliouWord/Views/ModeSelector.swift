//
//  ModeSelector.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import SwiftUI

struct ModeSelector: View {
    @Binding var selectedMode: ScanMode
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("選擇掃描模式")
                .font(.headline)
                .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 16) {
                    ForEach(ScanMode.allCases, id: \.self) { mode in
                        ModeCard(mode: mode, isSelected: selectedMode == mode) {
                            selectedMode = mode
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }
}

struct ModeCard: View {
    let mode: ScanMode
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: mode.icon)
                        .font(.title2)
                        .foregroundColor(isSelected ? .white : .blue)
                    
                    Spacer()
                    
                    if isSelected {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.white)
                    }
                }
                
                Text(mode.rawValue)
                    .font(.headline)
                    .foregroundColor(isSelected ? .white : .primary)
                
                Text(mode.description)
                    .font(.caption)
                    .foregroundColor(isSelected ? .white.opacity(0.8) : .secondary)
                    .lineLimit(2)
            }
            .padding()
            .frame(width: 160, height: 100)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? Color.blue : Color.gray.opacity(0.1))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.blue.opacity(isSelected ? 0 : 0.3), lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    ModeSelector(selectedMode: .constant(.easy))
}