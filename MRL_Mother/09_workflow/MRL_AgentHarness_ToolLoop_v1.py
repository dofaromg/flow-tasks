#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_ToolLoop_v1.py — Agent 執行骨架:並行工具批次執行器
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/tools/tool_runner.py`
與 `tools/tool_context.py`。與母體既有 tool_registry.py 的分工（去重定位）：
  - tool_registry.py — schema 宣告 + 輸入驗證 + MerkleChain 記錄（註冊簿）
  - 本模組           — 執行語意：並行批次、錯誤隔離、上下文注入（執行器）
  兩者以 from_tool_registry() 橋接，不重複造註冊簿。

本次吸收的核心知識（母體原缺）：
1. 批次並行執行 + 錯誤隔離：asyncio.gather 全包 try/except，
   單一工具炸掉回 ToolResult(error=...)，不得連坐取消同批其他工具。
2. sync 工具丟 asyncio.to_thread，不阻塞事件迴圈。
3. ToolContext 注入：註冊時以型別註解偵測一次並快取；
   產生對外 schema 時剝除注入參數（模型永遠看不到內部參數）。

依賴：Python stdlib only（asyncio, functools, inspect, typing）。
"""
from __future__ import annotations

import asyncio
import functools
import inspect
import typing
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import _try_import
from MRL_AgentHarness_Types_v1 import PythonTool, ToolCall, ToolResult

__all__ = ["ToolContext", "ToolWithSchema", "ToolLoopRunner", "from_tool_registry"]


class ToolContext:
    """注入給工具的會話能力句柄（工具藉此回望母體會話）。"""

    def __init__(self, conversation: Any = None) -> None:
        self.conversation = conversation


class ToolWithSchema:
    """帶顯式 JSON-Schema 的工具包裝（interop tool_registry 宣告式風格）。"""

    def __init__(self, fn: Callable[..., Any], input_schema: Dict[str, Any]) -> None:
        self.fn = fn
        self.input_schema = input_schema
        self.__name__ = fn.__name__
        self.__doc__ = fn.__doc__

    def __call__(self, **kwargs: Any) -> Any:
        return self.fn(**kwargs)


def _find_context_param(fn: Callable[..., Any]) -> Optional[str]:
    """回傳 ToolContext 型別參數名（含 Optional[ToolContext]）；無則 None。"""
    target = fn
    while isinstance(target, ToolWithSchema):
        target = target.fn
    try:
        hints = typing.get_type_hints(target)
    except (TypeError, NameError, AttributeError):
        return None
    for name, ann in hints.items():
        if name == "return":
            continue
        if ann is ToolContext:
            return name
        if typing.get_origin(ann) is typing.Union and ToolContext in typing.get_args(ann):
            return name
    return None


def _make_public_callable(fn: Callable[..., Any], context_param: str) -> Callable[..., Any]:
    """回傳剝除注入參數簽名的代理 callable（schema 生成用）。"""
    if isinstance(fn, ToolWithSchema):
        return ToolWithSchema(_make_public_callable(fn.fn, context_param), fn.input_schema)
    sig = inspect.signature(fn)
    public_sig = sig.replace(
        parameters=[p for n, p in sig.parameters.items() if n != context_param]
    )

    @functools.wraps(fn)
    def _proxy(**kwargs):
        return fn(**kwargs)

    setattr(_proxy, "__signature__", public_sig)
    return _proxy


def _is_async(obj: Any) -> bool:
    if isinstance(obj, ToolWithSchema):
        return _is_async(obj.fn)
    return inspect.iscoroutinefunction(obj) or (
        hasattr(obj, "__call__") and inspect.iscoroutinefunction(obj.__call__)
    )


class ToolLoopRunner:
    """具名工具的註冊與並行執行器（sync/async 皆可）。"""

    def __init__(self, tools: Optional[List[PythonTool]] = None) -> None:
        self._tools: Dict[str, PythonTool] = {}
        self._context: Optional[ToolContext] = None
        self._context_params: Dict[str, str] = {}  # 註冊時快取，免每次呼叫做內省
        for tool in tools or []:
            self.register(tool)

    def set_context(self, ctx: ToolContext) -> None:
        self._context = ctx

    def register(self, tool: PythonTool, name: Optional[str] = None) -> None:
        tool_name = name or tool.__name__
        if tool_name in self._tools:
            raise ValueError(f"工具 '{tool_name}' 已註冊")
        self._tools[tool_name] = tool
        ctx_param = _find_context_param(tool)
        if ctx_param is not None:
            self._context_params[tool_name] = ctx_param

    def unregister(self, name: str) -> None:
        if name not in self._tools:
            raise KeyError(f"工具 '{name}' 未註冊")
        del self._tools[name]
        self._context_params.pop(name, None)

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_public_callable(self, tool_name: str) -> Callable[..., Any]:
        """對外 schema 用 callable：內部注入參數已從簽名剝除。"""
        if tool_name not in self._tools:
            raise KeyError(f"工具 '{tool_name}' 未註冊")
        tool = self._tools[tool_name]
        ctx_param = self._context_params.get(tool_name)
        return tool if ctx_param is None else _make_public_callable(tool, ctx_param)

    async def _execute_fn(self, fn: Callable[..., Any], **kwargs: Any) -> Any:
        if not _is_async(fn):
            result = await asyncio.to_thread(fn, **kwargs)
        else:
            result = fn(**kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _inject_context(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        ctx_param = self._context_params.get(tool_name)
        if ctx_param is not None and self._context is not None and ctx_param not in kwargs:
            return {**kwargs, ctx_param: self._context}
        return kwargs

    async def execute(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name not in self._tools:
            raise KeyError(f"工具 '{tool_name}' 未註冊")
        kwargs = self._inject_context(tool_name, kwargs)
        return await self._execute_fn(self._tools[tool_name], **kwargs)

    async def process_tool_calls(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """並行執行一批工具呼叫；錯誤隔離、順序保持、絕不連坐。"""

        async def _execute_one(tc: ToolCall) -> ToolResult:
            # 全身 try/except：任何洩漏都會讓 gather 取消同批兄弟任務
            try:
                if tc.name not in self._tools:
                    return ToolResult(name=tc.name, error=f"未知工具: '{tc.name}'")
                result = await self._execute_fn(
                    self._tools[tc.name], **self._inject_context(tc.name, tc.args)
                )
                return ToolResult(name=tc.name, result=result)
            except Exception as e:  # noqa: BLE001
                return ToolResult(name=tc.name, error=str(e), exception=e)

        return list(await asyncio.gather(*[_execute_one(tc) for tc in tool_calls]))


def from_tool_registry(registry: Any = None) -> ToolLoopRunner:
    """橋接母體 tool_registry.ToolRegistry：吸收其已註冊工具為本執行器工具。

    registry 為 None 時嘗試動態匯入 tool_registry 並建新註冊簿；
    匯入失敗回傳空 runner（沙盒安全降級）。
    """
    if registry is None:
        registry_cls = _try_import("tool_registry", "ToolRegistry")
        if registry_cls is None:
            return ToolLoopRunner()
        registry = registry_cls()
    runner = ToolLoopRunner()
    tools = getattr(registry, "_tools", {})
    for name, entry in dict(tools).items():
        fn = getattr(entry, "fn", None) or getattr(entry, "func", None) or (
            entry if callable(entry) else None
        )
        if fn is not None:
            runner.register(fn, name=name)
    return runner


def _demo() -> None:
    async def main() -> None:
        runner = ToolLoopRunner()

        def add(a: int, b: int) -> int:
            return a + b

        async def fail() -> None:
            raise RuntimeError("演示失敗隔離")

        async def whoami(ctx: ToolContext) -> str:
            return f"ctx={type(ctx).__name__}"

        runner.register(add)
        runner.register(fail)
        runner.register(whoami)
        runner.set_context(ToolContext(conversation="母體會話"))

        results = await runner.process_tool_calls([
            ToolCall(name="add", args={"a": 2, "b": 3}),
            ToolCall(name="fail"),
            ToolCall(name="whoami"),
            ToolCall(name="ghost"),
        ])
        for r in results:
            print(f"{r.name:8s} ok={r.ok!s:5s} result={r.result!r} error={r.error!r}")
        pub = runner.get_public_callable("whoami")
        print("對外簽名(注入參數已剝除):", inspect.signature(pub))

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
