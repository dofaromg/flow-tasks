#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_MRL_agentharness_v1.py — MRL_AgentHarness_* 蒸餾模組驗收測試
origin_signature: MrLiouWord

pytest 相容；沙盒無 pytest 時可獨立執行：
    python3 tests/test_MRL_agentharness_v1.py
"""
from __future__ import annotations

import asyncio
import pathlib
import sys
import tempfile

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in [_REPO_ROOT, _REPO_ROOT / "09_workflow"]:
    if str(_sub) not in sys.path:
        sys.path.insert(0, str(_sub))

from MRL_AgentHarness_Types_v1 import (  # noqa: E402
    Decision,
    FileChangeKind,
    HookResult,
    ToolCall,
    ToolResult,
)
from MRL_AgentHarness_HookLattice_v1 import (  # noqa: E402
    HookContext,
    HookRunner,
    OperationContext,
    SessionContext,
    TurnContext,
    post_tool_call,
    pre_tool_call_decide,
    pre_turn,
)
from MRL_AgentHarness_PolicyGate_v1 import (  # noqa: E402
    allow,
    allow_all,
    ask_user,
    deny,
    deny_all,
    enforce,
    workspace_only,
)
from MRL_AgentHarness_ToolLoop_v1 import (  # noqa: E402
    ToolContext,
    ToolLoopRunner,
)
from MRL_AgentHarness_TriggerPulse_v1 import (  # noqa: E402
    TriggerRunner,
    every,
    on_file_change,
)
from MRL_AgentHarness_Kernel_v1 import (  # noqa: E402
    Agent,
    AgentConfig,
    EchoGateway,
)


def _run(coro):
    return asyncio.run(coro)


# ─── HookLattice ─────────────────────────────────────────────────────────────
def test_context_chain_lookup_and_shadowing():
    session = SessionContext()
    session.set_state("k", "session")
    turn = TurnContext(session)
    op = OperationContext(turn)
    assert op.get_state("k") == "session"       # 沿父鏈回溯
    turn.set_state("k", "turn")
    assert op.get_state("k") == "turn"          # 子層遮蔽
    assert session.get_state("k") == "session"  # 寫不污染父層
    assert op.get_state("無此鍵", "預設") == "預設"


def test_hook_runner_pre_turn_blocks():
    async def main():
        runner = HookRunner()

        @pre_turn
        async def block_empty(prompt: str) -> HookResult:
            return HookResult(allow=bool(prompt), message="空輸入")

        runner.register_hook(block_empty)
        ok, _ = await runner.dispatch_pre_turn("hi")
        blocked, _ = await runner.dispatch_pre_turn("")
        assert ok.allow and not blocked.allow

    _run(main())


def test_hook_runner_rejects_unknown_type():
    runner = HookRunner()
    try:
        runner.register_hook(object())
        assert False, "應拋 ValueError"
    except ValueError:
        pass


# ─── PolicyGate ──────────────────────────────────────────────────────────────
def test_policy_deny_by_default_with_specific_allow():
    async def main():
        gate = enforce([deny_all(), allow("view_file")])
        ctx = HookContext()
        assert (await gate.run(ctx, ToolCall(name="view_file"))).allow
        assert not (await gate.run(ctx, ToolCall(name="write_file"))).allow

    _run(main())


def test_policy_specific_deny_beats_global_allow():
    async def main():
        gate = enforce([allow_all(), deny("rm_rf")])
        ctx = HookContext()
        assert not (await gate.run(ctx, ToolCall(name="rm_rf"))).allow
        assert (await gate.run(ctx, ToolCall(name="anything"))).allow

    _run(main())


def test_policy_prefix_wildcard_bucket():
    async def main():
        gate = enforce([deny_all(), allow("mcp_srv/*")])
        ctx = HookContext()
        assert (await gate.run(ctx, ToolCall(name="mcp_srv/read"))).allow
        assert not (await gate.run(ctx, ToolCall(name="other/read"))).allow

    _run(main())


def test_policy_ask_user_approve_and_reject():
    async def main():
        answers = {"回應": True}

        async def handler(tc: ToolCall) -> bool:
            return answers["回應"]

        gate = enforce([ask_user("run_command", handler=handler)])
        ctx = HookContext()
        assert (await gate.run(ctx, ToolCall(name="run_command"))).allow
        answers["回應"] = False
        res = await gate.run(ctx, ToolCall(name="run_command"))
        assert not res.allow and "人工否決" in res.message

    _run(main())


def test_policy_ask_user_requires_handler():
    from MRL_AgentHarness_PolicyGate_v1 import Policy

    try:
        enforce([Policy(tool="x", decision=Decision.ASK_USER)])
        assert False, "缺 handler 應拋 ValueError"
    except ValueError:
        pass


def test_policy_predicate_exception_fails_closed():
    async def main():
        def boom(args):
            raise RuntimeError("predicate 爆炸")

        gate = enforce([allow("t", when=boom)])
        res = await gate.run(HookContext(), ToolCall(name="t"))
        assert not res.allow and "fail-closed" in res.message

    _run(main())


def test_policy_when_predicate_on_args():
    async def main():
        gate = enforce([deny_all(), allow("calc", when=lambda args: args.get("a", 0) > 0)])
        ctx = HookContext()
        assert (await gate.run(ctx, ToolCall(name="calc", args={"a": 1}))).allow
        assert not (await gate.run(ctx, ToolCall(name="calc", args={"a": -1}))).allow

    _run(main())


def test_workspace_only_containment():
    async def main():
        with tempfile.TemporaryDirectory() as ws:
            gate = enforce([allow_all(), workspace_only([ws])])
            ctx = HookContext()
            inside = ToolCall(name="write_file", canonical_path=str(pathlib.Path(ws) / "a.txt"))
            outside = ToolCall(name="write_file", canonical_path="/etc/passwd")
            sibling = ToolCall(name="write_file", canonical_path=ws + "_旁路/x")
            assert (await gate.run(ctx, inside)).allow
            assert not (await gate.run(ctx, outside)).allow
            assert not (await gate.run(ctx, sibling)).allow  # 防尾綴切片旁路
            # 非檔案工具不受圈地影響
            assert (await gate.run(ctx, ToolCall(name="calc"))).allow
            # canonical_path 未填時，後備偵測常見路徑引數鍵（圈地不得形同虛設）
            via_args_out = ToolCall(name="write_file", args={"path": "/etc/passwd"})
            via_args_in = ToolCall(name="write_file", args={"path": str(pathlib.Path(ws) / "b.txt")})
            assert not (await gate.run(ctx, via_args_out)).allow
            assert (await gate.run(ctx, via_args_in)).allow

    _run(main())


# ─── ToolLoop ────────────────────────────────────────────────────────────────
def test_toolloop_batch_error_isolation_and_order():
    async def main():
        runner = ToolLoopRunner()

        def add(a: int, b: int) -> int:
            return a + b

        async def boom() -> None:
            raise RuntimeError("炸")

        runner.register(add)
        runner.register(boom)
        results = await runner.process_tool_calls([
            ToolCall(name="boom"),
            ToolCall(name="add", args={"a": 1, "b": 2}),
            ToolCall(name="ghost"),
        ])
        assert [r.name for r in results] == ["boom", "add", "ghost"]  # 順序保持
        assert not results[0].ok and results[0].error == "炸"
        assert results[1].ok and results[1].result == 3  # 兄弟不連坐
        assert not results[2].ok and "未知工具" in results[2].error

    _run(main())


def test_toolloop_context_injection_and_public_signature():
    async def main():
        import inspect

        runner = ToolLoopRunner()

        def probe(x: int, ctx: ToolContext) -> str:
            return f"{x}:{type(ctx).__name__}"

        runner.register(probe)
        runner.set_context(ToolContext(conversation="母體"))
        out = await runner.execute("probe", x=7)
        assert out == "7:ToolContext"
        sig = inspect.signature(runner.get_public_callable("probe"))
        assert "ctx" not in sig.parameters  # 模型看不到注入參數

    _run(main())


def test_toolloop_duplicate_registration_rejected():
    runner = ToolLoopRunner()

    def t() -> None:
        pass

    runner.register(t)
    try:
        runner.register(t)
        assert False, "重複註冊應拋 ValueError"
    except ValueError:
        pass


# ─── TriggerPulse ────────────────────────────────────────────────────────────
def test_trigger_every_and_file_change():
    async def main():
        received = []

        class _Conn:
            async def send_trigger_notification(self, content: str) -> None:
                received.append(content)

        with tempfile.TemporaryDirectory() as tmp:
            async def tick(ctx):
                await ctx.send("tick")

            async def changed(ctx, changes):
                for c in changes:
                    await ctx.send(f"{c.kind.value}")

            async with TriggerRunner(
                triggers=[every(0.05, tick), on_file_change(tmp, changed, poll_seconds=0.05)],
                connection=_Conn(),
            ) as runner:
                await asyncio.sleep(0.12)
                (pathlib.Path(tmp) / "f.txt").write_text("x")
                await asyncio.sleep(0.15)
                assert runner.is_running
            assert not runner.is_running
        assert "tick" in received
        assert FileChangeKind.ADDED.value in received

    _run(main())


def test_trigger_every_rejects_nonpositive():
    try:
        every(0, lambda ctx: None)  # type: ignore[arg-type]
        assert False
    except ValueError:
        pass


def test_trigger_on_file_change_rejects_nonpositive_poll():
    async def _noop(ctx, changes):
        pass

    try:
        on_file_change("/tmp", _noop, poll_seconds=0)
        assert False
    except ValueError:
        pass


# ─── Kernel 端到端 ───────────────────────────────────────────────────────────
def test_kernel_refuses_tools_without_policy():
    async def main():
        def t() -> None:
            pass

        try:
            async with Agent(AgentConfig(tools=[t])):
                pass
            assert False, "無政策應拒絕啟動"
        except ValueError as e:
            assert "安全政策" in str(e)

    _run(main())


def test_kernel_end_to_end_tool_call_via_policy_gate():
    async def main():
        events = []

        def add(a: int, b: int) -> int:
            return a + b

        def rm_rf(path: str) -> str:
            raise AssertionError("被拒工具絕不可執行")

        @post_tool_call
        async def observe(result: ToolResult) -> None:
            events.append((result.name, result.ok))

        config = AgentConfig(
            gateway=EchoGateway(),
            tools=[add, rm_rf],
            policies=[deny_all(), allow("add")],
            hooks=[observe],
        )
        async with Agent(config) as agent:
            ok = await agent.chat("TOOL:add a=2 b=3")
            assert "add→5" in ok.text
            denied = await agent.chat("TOOL:rm_rf path=/")
            assert "deny_all" in denied.text and "rm_rf" in denied.text
            assert agent.conversation.turn_count == 2
            assert agent.conversation.total_usage.total_tokens > 0
        assert ("add", True) in events
        assert ("rm_rf", False) in events

    _run(main())


def test_kernel_pre_turn_block_short_circuits():
    async def main():
        @pre_turn
        async def block_all(prompt: str) -> HookResult:
            return HookResult(allow=False, message="全阻斷")

        async with Agent(AgentConfig(hooks=[block_all])) as agent:
            resp = await agent.chat("hi")
            assert resp.blocked and resp.block_reason == "全阻斷"
            assert agent.conversation.turn_count == 0  # 被阻斷不計回合

    _run(main())


def test_kernel_decide_hook_satisfies_safety_invariant():
    async def main():
        @pre_tool_call_decide
        async def custom_gate(tc: ToolCall) -> HookResult:
            return HookResult(allow=tc.name != "危險")

        def t() -> str:
            return "ok"

        # 無 policies 但有裁決 hook ⇒ 允許啟動
        async with Agent(AgentConfig(tools=[t], hooks=[custom_gate])) as agent:
            resp = await agent.chat("TOOL:t")
            assert "t→ok" in resp.text

    _run(main())


def test_kernel_session_closed_after_exit():
    async def main():
        async with Agent(AgentConfig()) as agent:
            await agent.chat("hi")
            assert agent.is_started
        assert not agent.is_started  # 離場後 session 歸零
        try:
            _ = agent.conversation
            assert False, "關閉後取 conversation 應拋 RuntimeError"
        except RuntimeError:
            pass

    _run(main())


def test_kernel_tool_usage_accounted_in_tool_rounds():
    async def main():
        def add(a: int, b: int) -> int:
            return a + b

        from MRL_AgentHarness_PolicyGate_v1 import allow_all

        async with Agent(AgentConfig(tools=[add], policies=[allow_all()])) as agent:
            resp = await agent.chat("TOOL:add a=1 b=1")
            # 工具呼叫輪 + 總結輪的 prompt 用量都要入帳
            assert resp.usage.total_tokens >= resp.usage.prompt_tokens > 0

    _run(main())


def test_kernel_trigger_notification_reaches_agent():
    async def main():
        async def beat(ctx):
            await ctx.send("觸發訊息")

        async with Agent(AgentConfig(triggers=[every(0.05, beat)])) as agent:
            msg = await agent.next_trigger_notification(timeout=2.0)
            assert msg == "觸發訊息"

    _run(main())


# ─── 獨立執行器（沙盒無 pytest 時） ──────────────────────────────────────────
if __name__ == "__main__":
    import traceback

    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed / {len(tests)} total")
    sys.exit(1 if failed else 0)
