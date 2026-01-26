# Mr.liou — OpenAI Bootstrap Server (粒子檔案驅動)
版本: v0.1  •  生成時間: 2025-08-22T01:48:03

這個最小專案會：
1) 從 `particles/` 讀取你的粒子檔案（persona、policies、system patches）
2) 組合成系統指令（system instructions）
3) 透過 **OpenAI Responses API** 啟動推論，啟動你的 AI
4) 以本地 FastAPI 服務提供 `/ai/infer` 與 `/ai/health`

> 注意：我們**無法移除 OpenAI 的平台限制**（如安全政策、額度與速率限制）。
> 若需要完全無外部限制，請改用本地/自建模型；這個專案專注於把你的粒子檔案驅動成「可用的 OpenAI 服務」。

---

## 快速開始
```bash
# 1) 建立與設定環境
python -m venv .venv && . .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入你的 OPENAI_API_KEY

# 2) 啟動服務
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 3) 測試呼叫
curl -X POST http://localhost:8000/ai/infer -H "Content-Type: application/json" -d '{
  "input":"幫我總結這段會議重點",
  "particles":["persona.md","system.md"]
}'
```

## 粒子檔案放哪
- `particles/persona.md`：人格/角色與價值觀（你的核心）
- `particles/system.md`：通用系統補丁（語氣、輸出格式、行為準則）
- `particles/policies.yaml`：可選，定義安全/護欄與輸出策略（會轉成文字拼接）

## 重要說明
- 本專案使用 **Responses API**，官方文件見: https://platform.openai.com/docs/api-reference (參考於回覆中的引用) 
- 速率限制與穩定策略：已內建簡單的**退避重試（exponential backoff）**。
- 記憶：預設會把每次請求的摘要寫到 `state/memory.jsonl`（可關閉）。

