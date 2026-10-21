# MRL_AgentHarness 吸收報告 v1 — sdk-python 去重蒸餾

origin_signature: MrLiouWord
吸收日期: 2026-07-05
來源: dofaromg/MRL-antigravity-sdk-python（Google Antigravity SDK for Python 鏡像）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

---

## 一、去重蒸餾判定表

外部 SDK 逐部位比對母體既有能力，**已有者不重複吸收**，只吸收母體缺層：

| SDK 部位 | 母體既有對應（不重複吸收） | 判定 |
|---|---|---|
| `conversation/`（會話持久化） | `09_workflow/conversation.py`、`conversation_manager.py` | 重複 — 跳過 |
| 工具 schema 註冊/驗證 | `09_workflow/tool_registry.py` | 重複 — 跳過 |
| 任務路由 | `09_workflow/MRL_Tool_Router_v1.py` | 重複 — 跳過 |
| 多代理協作 | `09_workflow/MRL_multi_agent.py` | 重複 — 跳過 |
| ReAct 迴圈 | `09_workflow/agent_planner.py` | 重複 — 跳過 |
| 律法不變量裁決 | `09_workflow/MRL_guardrail.py`（rootlaw/AUP 層） | 分工互補 — 跳過 |
| `hooks/hooks.py` + `hook_runner.py` | 無 | **吸收** |
| `hooks/policy.py`（9 級優先序政策閘） | 無 | **吸收** |
| `tools/tool_runner.py`（並行批次+錯誤隔離+上下文注入） | 無 | **吸收** |
| `triggers/`（定時/檔變觸發器） | 無（Daemon 是程序層，非 session 層） | **吸收** |
| `agent.py`（session 生命週期容器+安全不變量） | 無 | **吸收** |
| pydantic / watchfiles / otel 外部依賴 | 母體零外部依賴原則 | **蒸餾去除** |
| 閉源 runtime 二進位（PyPI wheel 限定） | 不可吸收之黑箱 | **以 ModelGateway 可插拔介面取代** |

## 二、母體系統名稱產物（重新命名建構）

| 母體產物 | 蒸餾自 | 層位 |
|---|---|---|
| `09_workflow/MRL_AgentHarness_Types_v1.py` | `types.py`（1180 行 → 核心型別） | L7 LOOP / Y=3 |
| `09_workflow/MRL_AgentHarness_HookLattice_v1.py` | `hooks/hooks.py` + `hook_runner.py` | L7 LOOP / Y=3 |
| `09_workflow/MRL_AgentHarness_PolicyGate_v1.py` | `hooks/policy.py`（904 行） | L3 LAW / Y=0 |
| `09_workflow/MRL_AgentHarness_ToolLoop_v1.py` | `tools/tool_runner.py` + `tool_context.py` | L7 LOOP / Y=3 |
| `09_workflow/MRL_AgentHarness_TriggerPulse_v1.py` | `triggers/*`（watchfiles 依賴已去除，改 stdlib 輪詢） | L7 LOOP / Y=3 |
| `09_workflow/MRL_AgentHarness_Kernel_v1.py` | `agent.py` + `conversation.py` + `connection.py` | L7 LOOP / Y=3 |
| `tests/test_MRL_agentharness_v1.py` | 驗收測試（pytest 相容 + 獨立執行器） | — |

吸收的核心知識（母體原缺）：

1. **Hook 三型格**：Inspect（只讀不阻斷）/ Decide（可阻斷）/ Transform（可改寫），
   配 Session→Turn→Operation 作用域上下文鏈（讀沿父鏈、寫落本層）。
2. **9 級政策優先序桶**：具名 DENY > 具名 ASK > 具名 ALLOW > 前綴三級 > 全域三級；
   `[deny_all(), allow("x")]` 自然構成 deny-by-default（對齊 rl_00）。
3. **Fail-Closed 律**:政策 predicate 評估拋例外 ⇒ 一律 DENY。
4. **工具批次錯誤隔離**：並行執行、單工具失敗不連坐、順序保持。
5. **啟動期安全不變量**:有工具而無政策亦無裁決 hook ⇒ 拒絕啟動。
6. **workspace 圈地**：symlink 解析 + 大小寫摺疊 + 結構化逐段比對（防尾綴切片旁路）。

## 三、當下狀態（依 CLAUDE.md 狀態回報約定）

- 六模組 CLI demo：**PASS（沙盒，2026-07-05）** — `python3 09_workflow/MRL_AgentHarness_Kernel_v1.py`
- 驗收測試 21 項：**PASS（沙盒，2026-07-05）** — `python3 tests/test_MRL_agentharness_v1.py`
- EchoGateway 端到端（含政策閘攔截）：**PASS（沙盒 runtime 路徑，非真實 AI 模型）**
- `OllamaGateway`：**待起動 / 待實機** — 程式碼就位，需實機 `OLLAMA_HOST` 驗收後方可標 PASS
- pytest 路徑：**待驗證** — 沙盒無 pytest 套件，僅獨立執行器驗過；CI/實機 pytest 待跑

## 四、啟用方式

```python
from MRL_AgentHarness_Kernel_v1 import Agent, AgentConfig, EchoGateway
from MRL_AgentHarness_PolicyGate_v1 import deny_all, allow

def add(a: int, b: int) -> int:
    return a + b

config = AgentConfig(
    gateway=EchoGateway(),            # 實機換 OllamaGateway(model=..., host=OLLAMA_HOST)
    tools=[add],
    policies=[deny_all(), allow("add")],
)
async with Agent(config) as agent:
    resp = await agent.chat("TOOL:add a=2 b=3")
```
