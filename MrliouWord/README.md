# MrliouWord - 智慧3D掃描器

🚀 **革命性的3D內容創作生態系統**

## 🎯 專案願景

MrliouWord 是一款結合 LiDAR 精密掃描和 AI 快照建模的智慧3D掃描器，旨在成為「3D內容創作的TikTok」。

### 核心特色
- **三模式系統** - 輕鬆/探索/專業模式，同一引擎不同曝光
- **AI 快照建模** - 單張照片生成3D模型
- **社群分享生態** - 一鍵分享到多平台
- **智能品牌標識** - 自動浮水印系統

## 🎮 三模式設計

### 1️⃣ 輕鬆模式
- AI 自動處理，90%成功率
- 一鍵完成，無需思考
- 給第一次使用和追求效率的用戶

### 2️⃣ 探索模式  
- 可調參數，隨時重置
- 互動式學習體驗
- 給好奇心重的探索用戶

### 3️⃣ 專業模式
- 完全控制，無限可能
- 專業級參數調整
- 給創作者和工程師使用

## 🛠 技術架構

### 客戶端 (iOS)
- **SwiftUI** - 現代化UI框架
- **ARKit + LiDAR** - 3D掃描核心
- **CoreML + Vision** - AI處理引擎
- **RealityKit** - 3D渲染展示

### 後端服務
- **Supabase** - 後端即服務
- **Cloudflare R2** - 雲端存儲
- **Mixpanel** - 用戶行為分析

### AI 引擎
- **多模型融合** - 提升成功率到90%+
- **智能失敗恢復** - 自動建議優化
- **實時品質評估** - 即時反饋

## 📱 硬體需求

### 開發環境
- **Mac電腦** - macOS Ventura 13.0+
- **Xcode 15+** - iOS開發必須

### 測試設備  
- **iPhone 12 Pro+** - 需要LiDAR感測器
- **iPad Pro** - 2020年後支持LiDAR的型號

## 🚀 快速開始

> **📝 重要提示**: 本專案包含所有必要的 Swift 源代碼文件，但需要使用 Xcode 創建項目文件。請參閱 [XCODE_SETUP.md](XCODE_SETUP.md) 獲取詳細的項目設置說明。

### 1. 環境設置
```bash
# 克隆專案
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks/MrliouWord

# 參閱 XCODE_SETUP.md 創建 Xcode 項目
# 或使用 Xcode 的 "New Project" 功能並添加現有源文件
```

### 2. 依賴安裝
```bash
# CocoaPods (如果使用)
pod install

# Swift Package Manager 依賴已在專案中配置
```

### 3. 運行專案
- 選擇支援 LiDAR 的實體設備
- Cmd + R 運行專案
- 享受 3D 掃描的魅力！

## 📊 商業模式

### 免費版
- 月掃描 5 次
- AI 快照 2 次  
- 帶浮水印匯出

### 創作者版 ($4.99/月)
- 無限掃描和AI快照
- 移除浮水印
- 進階編輯功能

### 專業版 ($14.99/月)  
- 團隊協作
- API 存取
- 企業級功能

## 🎯 發展路線圖

### Phase 1 (1-2個月)
- [x] 三模式系統設計
- [ ] 基礎掃描功能
- [ ] AI 快照建模
- [ ] 社群分享功能

### Phase 2 (3-6個月)
- [ ] Web 展示平台
- [ ] 創作者計畫
- [ ] 推薦引擎
- [ ] 商業化功能

### Phase 3 (6個月+)
- [ ] 生態系統建立
- [ ] B2B 解決方案
- [ ] 國際化擴張
- [ ] AR/VR 整合

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發規範
- 遵循 Swift 編碼風格
- 使用 SwiftLint 檢查代碼品質
- 提交前運行測試套件

### 分支策略
- `main` - 穩定版本
- `develop` - 開發分支
- `feature/*` - 功能分支

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 📞 聯繫我們

- **GitHub**: [@dofaromg](https://github.com/dofaromg)
- **專案討論**: GitHub Issues
- **技術交流**: GitHub Discussions

---

**MrliouWord** - 讓3D創作變得簡單而美好 ✨