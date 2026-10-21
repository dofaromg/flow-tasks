#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_HookLattice_v1.py — Agent 執行骨架:Hook 三型格與生命週期分發器
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/hooks/hooks.py` 與
`hooks/hook_runner.py`。母體原本沒有的關鍵結構（本次吸收的核心知識）：

1. Hook 三型格：
     InspectHook   — 只讀、不阻斷（觀測）
     DecideHook    — 只讀、可阻斷（裁決，回 HookResult）
     TransformHook — 可改寫、阻斷（轉換，回新資料）
2. 作用域上下文鏈：SessionContext → TurnContext → OperationContext，
   get_state 沿父鏈回溯、set_state 只寫本層（子層遮蔽不污染父層）。
3. 生命週期分發：session start/end、pre/post turn、pre/post tool call、
   tool error（Transform 復原鏈）。

依賴：Python stdlib only（abc, asyncio, inspect）。
"""
from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from MRL_AgentHarness_Types_v1 import HookResult, ToolCall, ToolResult

__all__ = [
    "HookContext",
    "SessionContext",
    "TurnContext",
    "OperationContext",
    "InspectHook",
    "DecideHook",
    "TransformHook",
    "OnSessionStartHook",
    "OnSessionEndHook",
    "PreTurnHook",
    "PostTurnHook",
    "PreToolCallDecideHook",
    "PostToolCallHook",
    "OnToolErrorHook",
    "HookRunner",
    "pre_turn",
    "post_turn",
    "pre_tool_call_decide",
    "post_tool_call",
    "on_tool_error",
    "on_session_start",
    "on_session_end",
]


# ─── 作用域上下文鏈 ──────────────────────────────────────────────────────────
class HookContext:
    """hook 共享狀態容器；讀沿父鏈回溯，寫只落本層。"""

    def __init__(self, parent: Optional["HookContext"] = None) -> None:
        self.parent = parent
        self._store: Dict[str, Any] = {}

    def get_state(self, key: str, default: Any = None) -> Any:
        if key in self._store:
            return self._store[key]
        if self.parent is not None:
            return self.parent.get_state(key, default)
        return default

    def set_state(self, key: str, value: Any) -> None:
        self._store[key] = value


class SessionContext(HookContext):
    """整個 session 存續的上下文（鏈根）。"""

    def __init__(self) -> None:
        super().__init__(parent=None)


class TurnContext(HookContext):
    """單一回合存續的上下文。"""

    def __init__(self, session_context: SessionContext) -> None:
        super().__init__(parent=session_context)


class OperationContext(HookContext):
    """單一操作（如一次工具呼叫）存續的上下文。"""

    def __init__(self, turn_context: TurnContext) -> None:
        super().__init__(parent=turn_context)


# ─── Hook 三型格 ─────────────────────────────────────────────────────────────
class InspectHook:
    """只讀、不阻斷。子類覆寫 run()。"""

    async def run(self, context: HookContext, data: Any) -> None:
        raise NotImplementedError


class DecideHook:
    """只讀、可阻斷。run() 回傳 HookResult。"""

    async def run(self, context: HookContext, data: Any) -> HookResult:
        raise NotImplementedError


class TransformHook:
    """可改寫。run() 回傳轉換後資料（None = 未處理，交給下一個）。"""

    async def run(self, context: HookContext, data: Any) -> Any:
        raise NotImplementedError


# ─── 生命週期具體介面 ────────────────────────────────────────────────────────
class OnSessionStartHook(InspectHook):
    """session 啟動時觸發。"""


class OnSessionEndHook(InspectHook):
    """session 結束時觸發。"""


class PreTurnHook(DecideHook):
    """回合開始前裁決；data 為使用者輸入。"""


class PostTurnHook(InspectHook):
    """回合結束後觀測；data 為模型回應文字。"""


class PreToolCallDecideHook(DecideHook):
    """工具呼叫前裁決；data 為 ToolCall。"""


class PostToolCallHook(InspectHook):
    """工具呼叫後觀測；data 為 ToolResult。"""


class OnToolErrorHook(TransformHook):
    """工具失敗時轉換錯誤表示；回 None 表示未處理。"""


# ─── 裝飾器工廠 ──────────────────────────────────────────────────────────────
def _make_hook_decorator(hook_cls: type, *, pass_data: bool = True):
    """把 async 函式包成對應 Hook 子類實例（沿用 SDK decorator 精髓）。"""

    def decorator(func: Callable[..., Awaitable[Any]]):
        if not inspect.iscoroutinefunction(func):
            raise ValueError("hook 裝飾器只接受 async 函式")

        class _FunctionHook(hook_cls):  # type: ignore[misc, valid-type]
            def __init__(self, f):
                self.f = f
                self.__name__ = getattr(f, "__name__", "hook")

            async def run(self, context: HookContext, data: Any) -> Any:
                return await (self.f(data) if pass_data else self.f())

            async def __call__(self, *args, **kwargs):
                return await self.f(*args, **kwargs)

        return _FunctionHook(func)

    return decorator


pre_turn = _make_hook_decorator(PreTurnHook)
post_turn = _make_hook_decorator(PostTurnHook)
pre_tool_call_decide = _make_hook_decorator(PreToolCallDecideHook)
post_tool_call = _make_hook_decorator(PostToolCallHook)
on_tool_error = _make_hook_decorator(OnToolErrorHook)
on_session_start = _make_hook_decorator(OnSessionStartHook, pass_data=False)
on_session_end = _make_hook_decorator(OnSessionEndHook, pass_data=False)


# ─── HookRunner ──────────────────────────────────────────────────────────────
_HOOK_TYPE_REGISTRY: List[Tuple[type, str]] = [
    (OnSessionStartHook, "_on_session_start"),
    (OnSessionEndHook, "_on_session_end"),
    (PreTurnHook, "_pre_turn"),
    (PostTurnHook, "_post_turn"),
    (PreToolCallDecideHook, "_pre_tool_call_decide"),
    (PostToolCallHook, "_post_tool_call"),
    (OnToolErrorHook, "_on_tool_error"),
]


class HookRunner:
    """依型別歸簿註冊 hook，並在各生命週期點分發。"""

    def __init__(self) -> None:
        self._on_session_start: List[OnSessionStartHook] = []
        self._on_session_end: List[OnSessionEndHook] = []
        self._pre_turn: List[PreTurnHook] = []
        self._post_turn: List[PostTurnHook] = []
        self._pre_tool_call_decide: List[PreToolCallDecideHook] = []
        self._post_tool_call: List[PostToolCallHook] = []
        self._on_tool_error: List[OnToolErrorHook] = []
        self.session_context = SessionContext()

    def register_hook(self, hook: Any) -> None:
        for hook_type, attr in _HOOK_TYPE_REGISTRY:
            if isinstance(hook, hook_type):
                getattr(self, attr).append(hook)
                return
        raise ValueError(f"未知 hook 型別: {type(hook)}")

    @property
    def pre_tool_call_decide_hooks(self) -> Tuple[PreToolCallDecideHook, ...]:
        return tuple(self._pre_tool_call_decide)

    # session
    async def dispatch_session_start(self) -> None:
        for h in self._on_session_start:
            await h.run(context=self.session_context, data=None)

    async def dispatch_session_end(self) -> None:
        for h in self._on_session_end:
            await h.run(context=self.session_context, data=None)

    # turn
    async def dispatch_pre_turn(self, prompt: Any) -> Tuple[HookResult, TurnContext]:
        turn_context = TurnContext(self.session_context)
        for h in self._pre_turn:
            res = await h.run(context=turn_context, data=prompt or "")
            if not res.allow:
                return res, turn_context
        return HookResult(allow=True), turn_context

    async def dispatch_post_turn(self, turn_context: TurnContext, response: str) -> None:
        for h in self._post_turn:
            await h.run(context=turn_context, data=response)

    # tool
    async def dispatch_pre_tool_call(
        self, turn_context: TurnContext, tool_call: ToolCall
    ) -> Tuple[HookResult, ToolCall, OperationContext]:
        op_context = OperationContext(turn_context)
        for h in self._pre_tool_call_decide:
            res = await h.run(context=op_context, data=tool_call)
            if not res.allow:
                return res, tool_call, op_context
        return HookResult(allow=True), tool_call, op_context

    async def dispatch_post_tool_call(
        self, op_context: OperationContext, result: ToolResult
    ) -> None:
        for h in self._post_tool_call:
            await h.run(context=op_context, data=result)

    async def dispatch_on_tool_error(
        self, op_context: OperationContext, error: Exception
    ) -> Tuple[HookResult, Any]:
        """Transform 復原鏈：第一個回非 None 的 hook 勝出；hook 自身炸掉則 fail-closed。"""
        for h in self._on_tool_error:
            try:
                res = await h.run(context=op_context, data=error)
                if res is not None:
                    return HookResult(allow=True), res
            except Exception as e:  # noqa: BLE001 — 復原鏈本身失敗必須關閉而非上拋
                return HookResult(allow=False, message=f"錯誤復原失敗: {e}"), None
        return HookResult(allow=False), None


def _demo() -> None:
    import asyncio

    async def main() -> None:
        runner = HookRunner()
        seen: List[str] = []

        @pre_turn
        async def block_empty(prompt: str) -> HookResult:
            seen.append(f"pre_turn:{prompt!r}")
            return HookResult(allow=bool(prompt), message="空輸入阻斷")

        @post_turn
        async def log_response(text: str) -> None:
            seen.append(f"post_turn:{text!r}")

        runner.register_hook(block_empty)
        runner.register_hook(log_response)

        ok, turn_ctx = await runner.dispatch_pre_turn("你好")
        turn_ctx.set_state("k", "turn 值")
        await runner.dispatch_post_turn(turn_ctx, "母體回應")
        blocked, _ = await runner.dispatch_pre_turn("")
        print("允許:", ok.allow, "| 阻斷:", not blocked.allow, blocked.message)
        print("上下文鏈回溯:", OperationContext(turn_ctx).get_state("k"))
        print("事件序:", seen)

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
