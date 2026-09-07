#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_TriggerPulse_v1.py — Agent 執行骨架:觸發器脈衝（定時/檔變）
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/triggers/`
（triggers.py + helpers.py + trigger_runner.py）。去重蒸餾決策：
  - SDK 的 on_file_change 依賴外部套件 watchfiles —— 蒸餾時去除該外部依賴，
    改以 stdlib mtime 輪詢實作（母體零外部依賴原則）。
  - 與母體 MRL_PersistentLoop_Daemon_v1 的分工：Daemon 是常駐程序層，
    本模組是 agent session 內的 asyncio 觸發任務群（session 同生共死）。

本次吸收的核心知識（母體原缺）：
1. Trigger = async fn(TriggerContext)；ctx.send() 把訊息推回 agent。
2. every(interval)：首次觸發在第一個 interval 之後（非立即）。
3. TriggerRunner 為 async context manager：進場起任務、離場取消收乾。

依賴：Python stdlib only（asyncio, os, pathlib）。
"""
from __future__ import annotations

import asyncio
import inspect
import os
import pathlib
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

from MRL_AgentHarness_Types_v1 import FileChange, FileChangeKind

__all__ = ["TriggerContext", "trigger", "every", "on_file_change", "TriggerRunner"]


class TriggerContext:
    """每個 trigger 一份的句柄；send() 把訊息推回 agent 連線。"""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def send(self, content: str) -> None:
        await self._connection.send_trigger_notification(content)


# Trigger 即任何吃單一 TriggerContext 參數的 async 函式。
Trigger = Callable[[TriggerContext], Awaitable[None]]


def trigger(func: Trigger) -> Trigger:
    """驗證並標記 trigger：必須 async、恰好一個參數。"""
    if not inspect.iscoroutinefunction(func):
        raise ValueError("trigger 必須是 async 函式")
    if len(inspect.signature(func).parameters) != 1:
        raise ValueError("trigger 必須恰好接受一個參數（TriggerContext）")
    setattr(func, "__is_trigger__", True)
    return func


def every(
    interval_seconds: float,
    callback: Callable[[TriggerContext], Awaitable[None]],
) -> Trigger:
    """固定間隔觸發；首次觸發在第一個 interval 之後。"""
    if interval_seconds <= 0:
        raise ValueError(f"interval_seconds 必須為正，收到 {interval_seconds}")

    async def _trigger(ctx: TriggerContext) -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            await callback(ctx)

    _trigger.__name__ = f"every_{interval_seconds}s"
    return _trigger


def _snapshot(path: pathlib.Path) -> Dict[str, float]:
    """遞迴收集 path 下所有檔案的 mtime（單檔亦可）。"""
    snap: Dict[str, float] = {}
    try:
        if path.is_file():
            snap[str(path)] = path.stat().st_mtime
        elif path.is_dir():
            for root, _dirs, files in os.walk(path):
                for f in files:
                    p = pathlib.Path(root) / f
                    try:
                        snap[str(p)] = p.stat().st_mtime
                    except OSError:
                        continue
    except OSError:
        pass
    return snap


def on_file_change(
    path: "str | pathlib.Path",
    callback: Callable[[TriggerContext, Sequence[FileChange]], Awaitable[None]],
    poll_seconds: float = 0.5,
) -> Trigger:
    """檔案/目錄變更觸發（stdlib mtime 輪詢版；watchfiles 外部依賴已蒸餾去除）。"""
    if poll_seconds <= 0:
        raise ValueError(f"poll_seconds 必須為正，收到 {poll_seconds}")
    watch_path = pathlib.Path(path)

    async def _trigger(ctx: TriggerContext) -> None:
        prev = _snapshot(watch_path)
        while True:
            await asyncio.sleep(poll_seconds)
            cur = _snapshot(watch_path)
            changes: List[FileChange] = []
            for p, mtime in cur.items():
                if p not in prev:
                    changes.append(FileChange(kind=FileChangeKind.ADDED, path=p))
                elif mtime != prev[p]:
                    changes.append(FileChange(kind=FileChangeKind.MODIFIED, path=p))
            for p in prev:
                if p not in cur:
                    changes.append(FileChange(kind=FileChangeKind.DELETED, path=p))
            prev = cur
            if changes:
                await callback(ctx, changes)

    _trigger.__name__ = f"on_file_change_{watch_path.name}"
    return _trigger


class TriggerRunner:
    """async context manager：進場為每個 trigger 起一個 task，離場全數取消收乾。"""

    def __init__(self, triggers: Sequence[Trigger], connection: Any) -> None:
        self._triggers = list(triggers)
        self._connection = connection
        self._tasks: List[asyncio.Task] = []

    async def __aenter__(self) -> "TriggerRunner":
        for trig in self._triggers:
            ctx = TriggerContext(self._connection)
            self._tasks.append(asyncio.create_task(trig(ctx)))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    @property
    def is_running(self) -> bool:
        return any(not t.done() for t in self._tasks)


def _demo() -> None:
    import tempfile

    class _EchoConnection:
        async def send_trigger_notification(self, content: str) -> None:
            print("[trigger→agent]", content)

    async def main() -> None:
        received: List[str] = []

        async def tick(ctx: TriggerContext) -> None:
            received.append("tick")
            await ctx.send(f"心跳 #{len(received)}")

        with tempfile.TemporaryDirectory() as tmp:
            async def on_change(ctx: TriggerContext, changes: Sequence[FileChange]) -> None:
                for c in changes:
                    await ctx.send(f"檔變 {c.kind.value}: {pathlib.Path(c.path).name}")

            async with TriggerRunner(
                triggers=[
                    every(0.2, tick),
                    on_file_change(tmp, on_change, poll_seconds=0.1),
                ],
                connection=_EchoConnection(),
            ) as runner:
                await asyncio.sleep(0.35)
                (pathlib.Path(tmp) / "新檔.txt").write_text("內容")
                await asyncio.sleep(0.35)
                print("運行中:", runner.is_running)
            print("收乾後運行中:", runner.is_running)

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
