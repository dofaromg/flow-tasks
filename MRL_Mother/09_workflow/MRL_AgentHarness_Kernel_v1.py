#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_Kernel_v1.py — Agent 執行骨架:會話核心（生命週期 + 對話迴圈）
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/agent.py`、
`conversation/conversation.py`、`connections/connection.py`。
SDK 原版依賴閉源編譯 runtime 二進位（僅 PyPI wheel 提供，repo 不可跑）——
蒸餾時以可插拔 ModelGateway 取代該二進位，母體因此得到「可實際運行」版本：
  - EchoGateway   — 沙盒確定性閘道（無真模型；驗證迴圈/政策/工具鏈用）
  - OllamaGateway — 實機閘道【待起動】：需實機 OLLAMA_HOST 驗收後方可標 PASS

與母體既有模組分工（去重定位）：
  - agent_planner.py（ReAct 迴圈）／ MRL_multi_agent.py（多代理）不重疊：
    本核心是「單 agent session 的生命週期容器」，把 HookLattice、PolicyGate、
    ToolLoop、TriggerPulse 四件蒸餾物接線成一個可運行整體。
  - 會話持久化沿用 conversation.py / conversation_manager.py，本核心只管
    in-session 歷史與用量累計。

本次吸收的核心知識（母體原缺）：
1. 安全不變量：有工具而無政策、亦無裁決 hook ⇒ 拒絕啟動（開機即擋，
   對齊 rl_00 deny-by-default）。
2. async context manager 生命週期：進場接線（hooks→政策→工具→觸發器），
   離場逆序收乾；啟動半途失敗必須清理已開資源再上拋。
3. 對話迴圈：pre_turn 裁決 → 閘道生成 → 工具呼叫經政策閘 → 並行執行 →
   結果回填歷史 → 迭代至無工具呼叫 → post_turn 觀測。

依賴：Python stdlib only（asyncio, json, os, urllib）。
CLI：python3 09_workflow/MRL_AgentHarness_Kernel_v1.py "TOOL:add a=2 b=3"
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

from MRL_utils import ORIGIN_SIGNATURE
from MRL_AgentHarness_Types_v1 import (
    HookResult,
    Step,
    StepType,
    ToolCall,
    ToolResult,
    UsageMetadata,
)
from MRL_AgentHarness_HookLattice_v1 import HookRunner
from MRL_AgentHarness_PolicyGate_v1 import Policy, enforce
from MRL_AgentHarness_ToolLoop_v1 import ToolContext, ToolLoopRunner
from MRL_AgentHarness_TriggerPulse_v1 import Trigger, TriggerRunner

__all__ = [
    "GatewayReply",
    "ModelGateway",
    "EchoGateway",
    "OllamaGateway",
    "AgentConfig",
    "ChatResponse",
    "Conversation",
    "Agent",
]


# ─── 模型閘道 ────────────────────────────────────────────────────────────────
@dataclasses.dataclass
class GatewayReply:
    """閘道單次生成結果：text 與 tool_calls 至少一者有值。"""

    text: str = ""
    tool_calls: List[ToolCall] = dataclasses.field(default_factory=list)
    usage: UsageMetadata = dataclasses.field(default_factory=UsageMetadata)


class ModelGateway:
    """可插拔模型閘道介面（取代 SDK 閉源 runtime 二進位的蒸餾點）。"""

    async def generate(
        self, history: Sequence[Step], tool_names: Sequence[str]
    ) -> GatewayReply:
        raise NotImplementedError


# 工具名允許 '/'（命名空間工具，如 mcp_srv/read），對齊 PolicyGate 前綴政策
_TOOL_DIRECTIVE = re.compile(r"TOOL:([\w/]+)((?:\s+\w+=\S+)*)")


class EchoGateway(ModelGateway):
    """沙盒確定性閘道 — 非真實 AI 模型。

    語意：最後一則 user 步含 `TOOL:name k=v ...` 指令 ⇒ 發出對應工具呼叫
    （每回合一次）；已有工具結果 ⇒ 覆述結果；否則回聲輸入。
    用途：沙盒驗證「迴圈/政策/工具/hook」接線正確性。
    """

    async def generate(
        self, history: Sequence[Step], tool_names: Sequence[str]
    ) -> GatewayReply:
        usage = UsageMetadata(prompt_tokens=sum(len(str(s.content)) for s in history))
        # 只看本回合片段（最後一則 USER 之後），避免跨回合污染
        last_user_idx = next(
            (i for i in range(len(history) - 1, -1, -1) if history[i].type == StepType.USER),
            -1,
        )
        last_user = history[last_user_idx] if last_user_idx >= 0 else None
        turn_segment = history[last_user_idx + 1 :] if last_user_idx >= 0 else []
        tool_results = [s for s in turn_segment if s.type == StepType.TOOL_RESULT]
        already_called = any(s.type == StepType.TOOL_CALL for s in turn_segment)

        if last_user is not None and not already_called:
            m = _TOOL_DIRECTIVE.search(str(last_user.content))
            if m:
                name = m.group(1)
                args: Dict[str, Any] = {}
                for pair in m.group(2).split():
                    k, v = pair.split("=", 1)
                    try:
                        args[k] = json.loads(v)
                    except (ValueError, json.JSONDecodeError):
                        args[k] = v
                usage.total_tokens = usage.prompt_tokens + usage.response_tokens
                return GatewayReply(tool_calls=[ToolCall(name=name, args=args)], usage=usage)

        if tool_results:
            summary = "; ".join(
                f"{r['name']}→{r.get('result') if r.get('error') is None else '錯誤:' + str(r.get('error'))}"
                for r in (s.content for s in tool_results)
            )
            text = f"[echo/沙盒] 工具結果: {summary}"
        else:
            text = f"[echo/沙盒] {last_user.content if last_user else ''}"
        usage.response_tokens = len(text)
        usage.total_tokens = usage.prompt_tokens + usage.response_tokens
        return GatewayReply(text=text, usage=usage)


class OllamaGateway(ModelGateway):
    """實機 Ollama 閘道【待起動】。

    當下狀態：程式碼已就位、沙盒未驗（沙盒無 OLLAMA_HOST）。
    依 CLAUDE.md 約定：在實機 OLLAMA_HOST 驗收通過前，不得稱「已跑通」。
    """

    def __init__(self, model: str = "llama3", host: Optional[str] = None) -> None:
        self.model = model
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")

    async def generate(
        self, history: Sequence[Step], tool_names: Sequence[str]
    ) -> GatewayReply:
        role_map = {
            StepType.USER: "user",
            StepType.MODEL: "assistant",
            StepType.TOOL_RESULT: "tool",
            StepType.TOOL_CALL: "assistant",
        }
        messages = [
            {"role": role_map[s.type], "content": str(s.content)} for s in history
        ]
        payload = json.dumps(
            {"model": self.model, "messages": messages, "stream": False}
        ).encode("utf-8")

        def _call() -> Dict[str, Any]:
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))

        data = await asyncio.to_thread(_call)
        text = data.get("message", {}).get("content", "")
        usage = UsageMetadata(
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            response_tokens=int(data.get("eval_count", 0)),
        )
        usage.total_tokens = usage.prompt_tokens + usage.response_tokens
        return GatewayReply(text=text, usage=usage)


# ─── 設定與回應 ──────────────────────────────────────────────────────────────
@dataclasses.dataclass
class AgentConfig:
    """宣告式 agent 設定（蒸餾自 SDK AgentConfig，去 pydantic 化）。"""

    gateway: ModelGateway = dataclasses.field(default_factory=EchoGateway)
    tools: List[Any] = dataclasses.field(default_factory=list)
    policies: List[Any] = dataclasses.field(default_factory=list)  # Policy 或 List[Policy]
    hooks: List[Any] = dataclasses.field(default_factory=list)
    triggers: List[Trigger] = dataclasses.field(default_factory=list)
    max_tool_rounds: int = 8
    max_history: int = 200


@dataclasses.dataclass
class ChatResponse:
    """單回合最終回應。"""

    text: str
    blocked: bool = False
    block_reason: str = ""
    usage: UsageMetadata = dataclasses.field(default_factory=UsageMetadata)


class Conversation:
    """in-session 對話狀態：歷史、回合數、用量累計（持久化沿用母體既有模組）。"""

    def __init__(self, max_history: int = 200) -> None:
        self._history: List[Step] = []
        self._turn_count = 0
        self._total_usage = UsageMetadata()
        self._max_history = max_history

    @property
    def history(self) -> List[Step]:
        return list(self._history)

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def total_usage(self) -> UsageMetadata:
        return self._total_usage

    @property
    def last_response(self) -> str:
        for s in reversed(self._history):
            if s.type == StepType.MODEL:
                return str(s.content)
        return ""

    def clear_history(self) -> None:
        self._history.clear()

    def append(self, step: Step) -> None:
        self._history.append(step)
        if len(self._history) > self._max_history:
            del self._history[: len(self._history) - self._max_history]

    def bump_turn(self, usage: UsageMetadata) -> None:
        self._turn_count += 1
        self._total_usage.add(usage)


class _TriggerConnection:
    """觸發器通知落點：進佇列，由 next_trigger_notification() 取用。"""

    def __init__(self) -> None:
        self.queue: "asyncio.Queue[str]" = asyncio.Queue()

    async def send_trigger_notification(self, content: str) -> None:
        await self.queue.put(content)


# ─── Agent 核心 ──────────────────────────────────────────────────────────────
class Agent:
    """單 agent session 生命週期容器（async context manager）。

    接線順序（進場）：HookRunner ← hooks ← 政策閘 → ToolLoopRunner →
    Conversation → TriggerRunner；離場逆序收乾。
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._hook_runner: Optional[HookRunner] = None
        self._tool_runner: Optional[ToolLoopRunner] = None
        self._conversation: Optional[Conversation] = None
        self._trigger_runner: Optional[TriggerRunner] = None
        self._trigger_connection = _TriggerConnection()
        self.origin_signature = ORIGIN_SIGNATURE

    async def __aenter__(self) -> "Agent":
        try:
            self._hook_runner = HookRunner()
            for hook in self._config.hooks:
                self._hook_runner.register_hook(hook)

            # 安全不變量（rl_00 deny-by-default）：有工具而無政策亦無裁決 hook ⇒ 拒啟
            has_decide_hook = bool(self._hook_runner.pre_tool_call_decide_hooks)
            if self._config.tools and not self._config.policies and not has_decide_hook:
                raise ValueError(
                    "已啟用工具但未設安全政策。"
                    "加 policies=[allow_all()] 全放行，"
                    "或 policies=[deny_all(), allow('工具名')] 選擇性放行。"
                )
            if self._config.policies:
                self._hook_runner.register_hook(enforce(self._config.policies))

            self._tool_runner = ToolLoopRunner(tools=list(self._config.tools))
            self._conversation = Conversation(max_history=self._config.max_history)
            self._tool_runner.set_context(ToolContext(self._conversation))

            if self._config.triggers:
                self._trigger_runner = TriggerRunner(
                    triggers=self._config.triggers,
                    connection=self._trigger_connection,
                )
                await self._trigger_runner.__aenter__()

            await self._hook_runner.dispatch_session_start()
            return self
        except Exception:
            await self._cleanup()
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._hook_runner is not None:
            await self._hook_runner.dispatch_session_end()
        await self._cleanup()

    async def _cleanup(self) -> None:
        if self._trigger_runner is not None:
            await self._trigger_runner.__aexit__(None, None, None)
            self._trigger_runner = None
        # session 關閉後全數歸零：is_started 回 False，conversation 取用即拋錯
        self._hook_runner = None
        self._tool_runner = None
        self._conversation = None

    @property
    def is_started(self) -> bool:
        return self._conversation is not None

    @property
    def conversation(self) -> Conversation:
        if self._conversation is None:
            raise RuntimeError("session 未啟動；請用 `async with Agent(...)`。")
        return self._conversation

    async def next_trigger_notification(self, timeout: float = 5.0) -> str:
        """等待下一則觸發器通知（測試/驅動迴圈用）。"""
        return await asyncio.wait_for(self._trigger_connection.queue.get(), timeout)

    async def _run_tool_calls(self, turn_ctx, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """每個呼叫先過政策閘；放行者並行執行；被拒者回結構化錯誤。"""
        assert self._hook_runner is not None and self._tool_runner is not None
        approved: List[ToolCall] = []
        results_by_index: Dict[int, ToolResult] = {}
        op_contexts = {}
        for i, tc in enumerate(tool_calls):
            verdict, tc, op_ctx = await self._hook_runner.dispatch_pre_tool_call(
                turn_ctx, tc
            )
            op_contexts[i] = op_ctx
            if verdict.allow:
                approved.append(tc)
                results_by_index[i] = None  # type: ignore[assignment] # 佔位，稍後回填
            else:
                results_by_index[i] = ToolResult(
                    name=tc.name, error=verdict.message or "遭政策閘拒絕"
                )

        executed = await self._tool_runner.process_tool_calls(approved)
        it = iter(executed)
        for i in sorted(results_by_index):
            if results_by_index[i] is None:
                results_by_index[i] = next(it)

        final: List[ToolResult] = []
        for i in sorted(results_by_index):
            res = results_by_index[i]
            if res.exception is not None:
                verdict, recovered = await self._hook_runner.dispatch_on_tool_error(
                    op_contexts[i], res.exception
                )
                if verdict.allow:
                    res = ToolResult(name=res.name, error=str(recovered))
            await self._hook_runner.dispatch_post_tool_call(op_contexts[i], res)
            final.append(res)
        return final

    async def chat(self, prompt: str) -> ChatResponse:
        """單回合：pre_turn → (生成 ⇄ 政策閘工具迴圈)* → post_turn。"""
        if self._hook_runner is None or self._conversation is None:
            raise RuntimeError("session 未啟動；請用 `async with Agent(...)`。")

        verdict, turn_ctx = await self._hook_runner.dispatch_pre_turn(prompt)
        if not verdict.allow:
            return ChatResponse(text="", blocked=True, block_reason=verdict.message)

        conv = self._conversation
        conv.append(Step(type=StepType.USER, content=prompt))
        turn_usage = UsageMetadata()
        text = ""

        for _round in range(self._config.max_tool_rounds):
            reply = await self._config.gateway.generate(
                conv.history, self._tool_runner.tool_names if self._tool_runner else []
            )
            turn_usage.add(reply.usage)
            if not reply.tool_calls:
                text = reply.text
                break
            conv.append(
                Step(
                    type=StepType.TOOL_CALL,
                    content=[{"name": tc.name, "args": tc.args} for tc in reply.tool_calls],
                )
            )
            results = await self._run_tool_calls(turn_ctx, reply.tool_calls)
            for r in results:
                conv.append(
                    Step(
                        type=StepType.TOOL_RESULT,
                        content={"name": r.name, "result": r.result, "error": r.error},
                    )
                )
        else:
            text = f"[kernel] 已達工具迴圈上限 {self._config.max_tool_rounds}，回合終止"

        conv.append(Step(type=StepType.MODEL, content=text))
        conv.bump_turn(turn_usage)
        await self._hook_runner.dispatch_post_turn(turn_ctx, text)
        return ChatResponse(text=text, usage=turn_usage)


def _demo() -> None:
    import sys

    from MRL_AgentHarness_PolicyGate_v1 import allow, deny_all

    prompt = sys.argv[1] if len(sys.argv) > 1 else "TOOL:add a=2 b=3"

    def add(a: int, b: int) -> int:
        return a + b

    def rm_rf(path: str) -> str:
        return f"絕不應執行到這裡: {path}"

    async def main() -> None:
        config = AgentConfig(
            gateway=EchoGateway(),
            tools=[add, rm_rf],
            policies=[deny_all(), allow("add")],
        )
        async with Agent(config) as agent:
            resp = await agent.chat(prompt)
            print("回應:", resp.text)
            blocked = await agent.chat("TOOL:rm_rf path=/")
            print("危險工具:", blocked.text)
            print(
                "回合數:", agent.conversation.turn_count,
                "| 累計 tokens(字元估):", agent.conversation.total_usage.total_tokens,
            )

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
