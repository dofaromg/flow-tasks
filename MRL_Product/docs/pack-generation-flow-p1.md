# MRL Pack Generation 流程
> origin_signature: MrLiouWord  
> phase: 第十五包

---

## 完整生成路徑

```
使用者提交問題（category = product）
  ↓
POST /api/analyze
  → Core_Generator.analyze()
     → PromptBuilder.buildSystemPrompt('product')
     → AI 模型（product 偏重 prompt）
     → ResultNormalizer.normalizeResult(raw, 'product')
     → TemplateSelector.selectTemplate('product')
        → 'MRL_Delivery_Template_Product_v1'
     → Composer.composeAnalyzeResponse(...)
  ← response: { analysis_id, template_id, result, ... }

使用者付款解鎖 full_result
  → full_result 顯示（delivery-renderer.js）
  → product full 底部出現「生成 ProductPack」按鈕

使用者點擊「生成 ProductPack」（選 mode）
  ↓
POST /api/pack/generate { analysis_id, mode }
  → routes/pack.js
  → Packs.generateFromAnalysis({ analysisId, mode })
     → PackBuilder.buildPackFromAnalysis()
        → DB 取回 analysis（full_result）
        → ResultNormalizer.normalizeResult(rawResult, 'product')
        → buildProductPack({ normalizedResult, mode, ... })
           → _deriveTitle() — 從 core_judgment 推導標題
           → _buildPages(mode) — 依 mode 生成頁面清單
           → _buildDeployment() — DL580 部署草案
           → _buildPricingModel(mode) — 收費模式草案
        → packToJson(pack)
     → PackExporter.savePack(pack)
        → storage/packs/{pack_id}.json
  ← response: { pack_id, title, mode, summary, pack }

前端 renderPackResult(data)
  → 顯示 Pack summary + 頁面清單 + 執行順序 + 使用者流程
  → 下載 JSON 按鈕（GET /api/pack/{pack_id}/download）
```

---

## Core_Generator vs Pack_Generator 的接法

```
Core_Generator
  職責：analyze → normalize → template_id → compose response
  輸出：payload（給 ControlPanel 顯示）

Pack_Generator
  職責：從已完成的 analysis 建立 Pack Spec
  輸入：analysis_id（DB 已有 full_result）
  輸出：ProductPack JSON（存 storage/packs/）
```

**兩者不重疊**：Core_Generator 在 analyze 時跑，Pack_Generator 在使用者主動觸發時跑。

---

## Pack 資料在哪裡

```
生成後：storage/packs/{pack_id}.json
API 讀取：GET /api/pack/{pack_id}
下載：GET /api/pack/{pack_id}/download
列出（admin）：GET /api/pack?key={admin_key}
```

---

*origin_signature: MrLiouWord*
