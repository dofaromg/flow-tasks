//
//  ScanMode.swift
//  MrliouWord
//
//  Created on 2026-01-12
//

import Foundation

enum ScanMode: String, CaseIterable {
    case easy = "輕鬆模式"
    case explore = "探索模式"
    case professional = "專業模式"
    
    var description: String {
        switch self {
        case .easy:
            return "AI 自動處理，90%成功率"
        case .explore:
            return "可調參數，互動式學習"
        case .professional:
            return "完全控制，無限可能"
        }
    }
    
    var icon: String {
        switch self {
        case .easy:
            return "sparkles"
        case .explore:
            return "magnifyingglass"
        case .professional:
            return "gearshape.2"
        }
    }
}