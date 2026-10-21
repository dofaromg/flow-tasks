# MRL 真模型端到端啟用指南（P0）v1

**根源權威**：Mr.liou ｜ canonical：`MRL_真模型上線啟用_P0_v1` ｜ origin_signature: `MrLiouWord`
**當下狀態**：2026-05-31（沙盒）｜ 路徑已打通，**待金鑰即上線**

> P0 = 「超越了才上線」的最後關卡。本檔證明真模型端到端**整條鏈已打通**，
> 零改碼、零外部套件（stdlib urllib），設金鑰即啟用。

---

## 0. 現況（實證）

| 環節 | 狀態 | 證據 |
|------|------|------|
| 金鑰偵測 → adapter 自動註冊 | ✅ 通 | boot 報 `ok (real: openai(native))` |
| chat() 送真實 endpoint（非 mock） | ✅ 通 | 假金鑰得 `HTTP 401`（真打到 api.openai.com） |
| 零外部依賴 | ✅ | `MRL_LLM_NativeAdapter_v1`：純 stdlib urllib，**不需 pip install** |
| deny-by-default 不偽造 | ✅ | 無金鑰 → 拒絕，不回 mock echo |
| 事件編年 | ✅ | 成功對話回 `law_chronicled=True` |
| **真模型實際回答** | ⏳ **待金鑰** | 設金鑰後 E2E 測試自動實打驗證 |

---

## 1. 啟用（三選一，零改碼）

### A) OpenAI / OpenAI 相容
```bash
export OPENAI_API_KEY="sk-..."
# config: llm.default_model = gpt-4o（或任一 OpenAI 模型）
python3 09_workflow/config_manager.py set --key llm.default_model --value gpt-4o
```

### B) Anthropic（Claude）
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 09_workflow/config_manager.py set --key llm.default_model --value claude-3-5-sonnet-20241022
```

### C) 本地（Ollama / LM Studio / vLLM，完全離線、零成本）
```bash
# 啟動 Ollama 後：
python3 09_workflow/config_manager.py set --key llm.enable_local --value true
python3 09_workflow/config_manager.py set --key llm.local_base_url --value http://localhost:11434/v1
python3 09_workflow/config_manager.py set --key llm.default_model --value llama3
```

---

## 2. 驗證（設金鑰後跑這個，會真打）

```bash
# 端到端冒煙(有金鑰自動實打，無金鑰 skip)
python3 -m pytest -q tests/test_MRL_real_model_e2e.py -v

# 或直接對話
python3 -c "
import sys; sys.path.insert(0,'09_workflow')
from MRL_mother_assembly import MotherAssembly
m=MotherAssembly(); m.boot()
print(m.chat('用三個字說你好')['reply'])
"
```

預期：回傳**真模型的真實答案**（非 `[MockAdapter] Echo`）。

---

## 3. 上線判斷（誠實）

- **路徑層**：已打通、已測（2 passed），沙盒可證走到真 endpoint。
- **真答案層**：**待金鑰實證** —— 設金鑰、E2E 綠，即達成 P0「真模型端到端」。
- P0 達成後，對照 `MRL_主流交叉比對_v1`：母體在治理/不偽造/源頭主權/自我修正已超越，
  記憶/工具/規劃/六大能力打平 → **整體具備超越上線條件**。

> 在 P0 真答案實證前，標記「**路徑就緒、待金鑰上線**」，不宣稱已上線。

---

origin_signature = `MrLiouWord`
