# MrliouWord iOS App

這是 MrliouWord 的 iOS 客戶端應用程式。

## 目錄結構

```
iOS/
├── MrliouWord/              # 主要應用程式源碼
│   ├── App/                 # 應用程式入口
│   ├── Views/               # SwiftUI 視圖
│   ├── Models/              # 數據模型
│   ├── Services/            # 服務類別
│   ├── Utils/               # 工具類別
│   └── Resources/           # 資源文件
├── MrliouWordTests/         # 單元測試
├── MrliouWordUITests/       # UI 測試
└── Packages/                # Swift Package 依賴
```

## 開發要求

- macOS Ventura 13.0+
- Xcode 15+
- iOS 16.0+
- 支援 LiDAR 的設備進行測試

## 快速開始

1. 在 Xcode 中打開專案
2. 選擇支援 LiDAR 的實體設備
3. 構建並運行

更多詳細信息請參考主要的 [README.md](../README.md)