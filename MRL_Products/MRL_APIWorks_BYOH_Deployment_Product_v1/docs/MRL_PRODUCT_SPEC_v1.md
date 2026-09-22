# MRL APIWorks BYOH 商品規格 v1

## 要解決的問題

客戶希望使用自己的硬體與本機模型，又需要穩定 API、可回放記憶、可驗證證據與來源身分，而不把本機資料預設送往外部模型 API。

## 交付介面

| Method | Route | 驗收結果 |
|---|---|---|
| GET | `/health` | 模型、本機邊界、Memory、Evidence 狀態 |
| POST | `/v1/mother/run` | 推論輸出、Evidence reference、Passport |
| GET | `/v1/memory/recall` | 指定 world/session 的稽核回放 |

## 支援基線

- Windows PowerShell；
- Python 3.10 以上；
- Ollama 或 llama.cpp OpenAI-compatible server；
- Gateway 與模型端點限定 loopback。

## 完成判準

客戶節點必須以真實安裝模型完成 health、inference、兩筆 Memory、Evidence hash chain 與 Passport hash。Stub、外部模型服務或僅 CI 測試都不能取代客戶驗收。

