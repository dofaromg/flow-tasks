#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AgentHarness_PolicyGate_v1.py — Agent 執行骨架:工具呼叫政策閘（9 級優先序）
origin_signature: MrLiouWord
layer: L3 LAW
group: Y=0 RootGate

吸收來源（母體吸收記錄）
----------------------
蒸餾自 MRL-antigravity-sdk-python `google/antigravity/hooks/policy.py`（904 行）。
與母體既有 MRL_guardrail.py 的分工（去重定位，不重疊）：
  - MRL_guardrail   — 律法不變量層（rootlaw / AUP 全域裁決）
  - 本政策閘        — 工具呼叫粒度的 allow/deny/ask 規則引擎

本次吸收的核心知識（母體原缺）：
1. 9 級優先序桶（數字小者先評估）：
     具名 DENY(0) > 具名 ASK(1) > 具名 ALLOW(2)
   > 前綴 DENY(3) > 前綴 ASK(4) > 前綴 ALLOW(5)
   > 全域 DENY(6) > 全域 ASK(7) > 全域 ALLOW(8)
   ⟹ [deny_all(), allow("view_file")] 自然得到 deny-by-default 姿態。
2. Fail-Closed：政策 predicate 評估中拋例外 ⇒ 一律 DENY（不得開放）。
3. workspace_only：symlink 解析 + 大小寫摺疊 + 結構化包含比對的路徑圈地。
4. 裁決語彙與 MRL_guardrail 對齊：ASK_USER ≈ REQUIRE_HUMAN。

依賴：Python stdlib only（dataclasses, inspect, pathlib）。
"""
from __future__ import annotations

import dataclasses
import inspect
import pathlib
import sys
from typing import Any, Awaitable, Callable, List, Optional, Sequence, Union

from MRL_AgentHarness_Types_v1 import Decision, HookResult, ToolCall
from MRL_AgentHarness_HookLattice_v1 import HookContext, PreToolCallDecideHook

__all__ = [
    "Decision",
    "Policy",
    "allow",
    "deny",
    "ask_user",
    "allow_all",
    "deny_all",
    "workspace_only",
    "enforce",
    "PolicyGateHook",
]

_WILDCARD = "*"

Predicate = Callable[..., Any]
AskUserHandler = Callable[[ToolCall], Union[bool, Awaitable[bool]]]


@dataclasses.dataclass(frozen=True)
class Policy:
    """單條工具政策規則。

    Attributes:
        tool: 目標工具名；"*" 全域；"prefix/*" 前綴（如 MCP server 圈）。
        decision: 命中時的裁決。
        when: 可選 predicate（吃 ToolCall 或 args dict）；None 表示恆命中。
        ask_user: ASK_USER 裁決的詢問處理器（enforce 時強制檢查存在）。
        name: 人讀標籤（記錄與 deny 原因用）。
    """

    tool: str
    decision: Decision
    when: Optional[Predicate] = None
    ask_user: Optional[AskUserHandler] = None
    name: str = ""


# ─── 建構器 ──────────────────────────────────────────────────────────────────
def allow(tool: str, *, when: Optional[Predicate] = None, name: str = "") -> Policy:
    """建立 APPROVE 政策。"""
    return Policy(tool=tool, decision=Decision.APPROVE, when=when, name=name)


def deny(tool: str, *, when: Optional[Predicate] = None, name: str = "") -> Policy:
    """建立 DENY 政策。"""
    return Policy(tool=tool, decision=Decision.DENY, when=when, name=name)


def ask_user(
    tool: str,
    *,
    handler: AskUserHandler,
    when: Optional[Predicate] = None,
    name: str = "",
) -> Policy:
    """建立 ASK_USER 政策（REQUIRE_HUMAN 對齊）。"""
    return Policy(
        tool=tool, decision=Decision.ASK_USER, when=when, ask_user=handler, name=name
    )


def allow_all() -> Policy:
    """全開政策（顯式知情選擇，非預設）。"""
    return allow(_WILDCARD, name="allow_all")


def deny_all() -> Policy:
    """全關政策；配合具名 allow() 形成 deny-by-default（對齊 rl_00）。"""
    return deny(_WILDCARD, name="deny_all")


# ─── workspace 圈地 ──────────────────────────────────────────────────────────
PathOrStr = Union[str, "pathlib.Path"]


def _secure_normalize_path(path: PathOrStr) -> pathlib.Path:
    """對稱正規化：解析 symlink；失敗上拋 OSError 由呼叫端 fail-closed。"""
    return pathlib.Path(path).resolve()


def _is_case_insensitive_fs() -> bool:
    return sys.platform in ("win32", "darwin")


def _is_path_in_workspace(target_path: PathOrStr, workspace_path: PathOrStr) -> bool:
    """target 是否落在 workspace 內（結構化逐段比對，防尾斜線切片漏洞）。"""
    try:
        t = _secure_normalize_path(target_path)
        w = _secure_normalize_path(workspace_path)
    except OSError:
        return False  # fail-closed
    if _is_case_insensitive_fs():
        t_parts = [p.casefold() for p in t.parts]
        w_parts = [p.casefold() for p in w.parts]
    else:
        t_parts, w_parts = list(t.parts), list(w.parts)
    if len(t_parts) < len(w_parts):
        return False
    return t_parts[: len(w_parts)] == w_parts


# canonical_path 未填時的路徑引數後備鍵（SDK 原版由 runtime 二進位填 canonical_path；
# 蒸餾版無該二進位，故必須從 args 偵測，否則圈地形同虛設）
_PATH_ARG_KEYS = ("canonical_path", "path", "file_path", "filepath", "file", "target_path", "dir")


def _candidate_path(tc: ToolCall) -> str:
    """取圈地檢查用路徑：優先 canonical_path，其次常見路徑引數鍵。"""
    if tc.canonical_path:
        return tc.canonical_path
    for key in _PATH_ARG_KEYS:
        v = tc.args.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


def workspace_only(
    workspaces: Sequence[PathOrStr],
    file_tools: Sequence[str] = ("read_file", "write_file", "create_file", "list_dir"),
) -> List[Policy]:
    """把檔案類工具圈禁在指定 workspace 目錄內；其他工具不受影響。

    路徑來源：ToolCall.canonical_path，未填時後備偵測常見路徑引數鍵
    （path / file_path / file / target_path / dir）。
    限制（誠實標註）：工具若用非常見引數名傳路徑，仍會繞過本圈地——
    該類工具請自行填 canonical_path 或加專屬 deny 政策。
    """

    def _outside_workspace(tc: ToolCall) -> bool:
        path = _candidate_path(tc)
        if not path:
            return False  # 無路徑引數的邊界情況（如 list_dir 用 cwd）放行
        return not any(_is_path_in_workspace(path, ws) for ws in workspaces)

    return [deny(t, when=_outside_workspace, name="workspace_only") for t in file_tools]


# ─── 9 級優先序桶 ────────────────────────────────────────────────────────────
_LEVELS = {
    ("specific", Decision.DENY): 0,
    ("specific", Decision.ASK_USER): 1,
    ("specific", Decision.APPROVE): 2,
    ("prefix", Decision.DENY): 3,
    ("prefix", Decision.ASK_USER): 4,
    ("prefix", Decision.APPROVE): 5,
    ("global", Decision.DENY): 6,
    ("global", Decision.ASK_USER): 7,
    ("global", Decision.APPROVE): 8,
}
_NUM_LEVELS = 9


def _scope(tool: str) -> str:
    if tool == _WILDCARD:
        return "global"
    if tool.endswith("/*"):
        return "prefix"
    return "specific"


def _bucket_index(p: Policy) -> int:
    return _LEVELS[(_scope(p.tool), p.decision)]


def _matches_target(policy_tool: str, call_target: str) -> bool:
    if policy_tool == _WILDCARD:
        return True
    if policy_tool.endswith("/*"):
        prefix = policy_tool[:-2]
        return "/" in call_target and call_target.split("/", 1)[0] == prefix
    return policy_tool == call_target


async def _evaluate_predicate(policy: Policy, tool_call: ToolCall) -> bool:
    """predicate 為 None 恆真；接受吃 ToolCall 或 args dict 兩種簽名；例外上拋。"""
    if policy.when is None:
        return True
    sig = inspect.signature(policy.when)
    params = list(sig.parameters.values())
    if params:
        ann = params[0].annotation
        if ann is ToolCall or ann == "ToolCall":
            raw = policy.when(tool_call)
        else:
            raw = policy.when(tool_call.args)
    else:
        raw = policy.when()
    return bool(await raw if inspect.isawaitable(raw) else raw)


async def _execute_ask_user(policy: Policy, tool_call: ToolCall) -> bool:
    assert policy.ask_user is not None  # enforce() 時已驗證
    result = policy.ask_user(tool_call)
    if inspect.isawaitable(result):
        result = await result
    return bool(result)


# ─── 政策閘 hook ─────────────────────────────────────────────────────────────
class PolicyGateHook(PreToolCallDecideHook):
    """依優先序桶逐一評估；首個命中即定案；評估炸掉一律 fail-closed。"""

    def __init__(self, buckets: Sequence[Sequence[Policy]]) -> None:
        self._buckets = buckets

    async def _evaluate_policy(
        self, p: Policy, tool_call: ToolCall
    ) -> Optional[HookResult]:
        if not _matches_target(p.tool, tool_call.name):
            return None
        try:
            if not await _evaluate_predicate(p, tool_call):
                return None
            return await self._apply(p, tool_call)
        except Exception as e:  # noqa: BLE001 — LAW: 評估失敗必須關閉
            return HookResult(
                allow=False,
                message=f"政策 '{p.name or p.tool}' 評估失敗，fail-closed: {e!r}",
            )

    async def _apply(self, p: Policy, tool_call: ToolCall) -> HookResult:
        label = p.name or p.tool
        if p.decision == Decision.DENY:
            return HookResult(allow=False, message=f"政策 '{label}' 拒絕")
        if p.decision == Decision.APPROVE:
            return HookResult(allow=True)
        # ASK_USER（REQUIRE_HUMAN）
        approved = await _execute_ask_user(p, tool_call)
        if approved:
            return HookResult(allow=True)
        return HookResult(
            allow=False, message=f"人工否決工具 '{tool_call.name}'（政策 '{label}'）"
        )

    async def run(self, context: HookContext, data: ToolCall) -> HookResult:
        try:
            for bucket in self._buckets:
                for p in bucket:
                    result = await self._evaluate_policy(p, data)
                    if result is not None:
                        return result
        except Exception as e:  # noqa: BLE001
            return HookResult(allow=False, message=f"政策閘內部錯誤，fail-closed: {e!r}")
        return HookResult(allow=True)  # 無政策命中 — 預設開放（由 enforce 呼叫端決定姿態）


def _flatten(policies: Sequence[Union[Policy, Sequence[Policy]]]) -> List[Policy]:
    flat: List[Policy] = []
    for p in policies:
        if isinstance(p, Policy):
            flat.append(p)
        else:
            flat.extend(p)
    return flat


def enforce(policies: Sequence[Union[Policy, Sequence[Policy]]]) -> PolicyGateHook:
    """把政策集編譯成 PreToolCallDecideHook（建構時即分桶排序）。

    Raises:
        ValueError: ASK_USER 政策缺 handler。
    """
    flat = _flatten(policies)
    for p in flat:
        if p.decision == Decision.ASK_USER and p.ask_user is None:
            raise ValueError(f"ASK_USER 政策 '{p.name or p.tool}' 缺 handler")
    buckets: List[List[Policy]] = [[] for _ in range(_NUM_LEVELS)]
    for p in flat:
        buckets[_bucket_index(p)].append(p)
    return PolicyGateHook(buckets)


def _demo() -> None:
    import asyncio

    async def main() -> None:
        gate = enforce([
            deny_all(),
            allow("view_file"),
            ask_user("run_command", handler=lambda tc: False, name="人工確認"),
        ])
        ctx = HookContext()
        for name in ("view_file", "write_file", "run_command"):
            res = await gate.run(ctx, ToolCall(name=name))
            print(f"{name:12s} → {'ALLOW' if res.allow else 'DENY '} {res.message}")

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
