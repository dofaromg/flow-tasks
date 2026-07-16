"""
Tests for agent_planner — AgentPlanner ReAct loop.
"""
import pytest

from tool_registry import ToolRegistry
from agent_planner import AgentPlanner, FINISH_ACTION, ORIGIN_SIGNATURE


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_registry():
    reg = ToolRegistry()

    @reg.register(description="Add two numbers.", parameters={"a": float, "b": float})
    def add(a: float, b: float) -> float:
        return a + b

    @reg.register(description="Echo a message.", parameters={"message": str})
    def echo(message: str) -> str:
        return message

    return reg


def _static_plan(steps):
    """Return a think_fn that executes a fixed list of decisions."""
    idx = {"v": 0}

    def think(_state):
        i = idx["v"]
        idx["v"] += 1
        return steps[min(i, len(steps) - 1)]

    return think


# ─── AgentPlanner ─────────────────────────────────────────────────────────────

class TestAgentPlanner:
    def test_immediate_finish(self):
        reg = _make_registry()
        think = _static_plan([
            {"action": FINISH_ACTION, "args": {"answer": "done"}}
        ])
        planner = AgentPlanner(reg, think_fn=think, max_steps=5)
        result = planner.run("trivial goal")
        assert result["finished"] is True
        assert result["answer"] == "done"

    def test_one_tool_call_then_finish(self):
        reg = _make_registry()
        think = _static_plan([
            {"thought": "Add numbers.", "action": "add", "args": {"a": 3.0, "b": 4.0}},
            {"thought": "Done.", "action": FINISH_ACTION, "args": {"answer": 7.0}},
        ])
        planner = AgentPlanner(reg, think_fn=think, max_steps=10)
        result = planner.run("What is 3 + 4?")
        assert result["finished"] is True
        assert result["answer"] == 7.0

    def test_result_keys(self):
        reg = _make_registry()
        think = _static_plan([
            {"action": FINISH_ACTION, "args": {"answer": "x"}}
        ])
        planner = AgentPlanner(reg, think_fn=think)
        result = planner.run("goal")
        for key in ("goal", "answer", "steps", "total_steps", "finished",
                    "started_at_ms", "ended_at_ms", "origin_signature"):
            assert key in result

    def test_origin_signature(self):
        reg = _make_registry()
        think = _static_plan([{"action": FINISH_ACTION, "args": {"answer": None}}])
        planner = AgentPlanner(reg, think_fn=think)
        result = planner.run("g")
        assert result["origin_signature"] == ORIGIN_SIGNATURE

    def test_goal_preserved(self):
        reg = _make_registry()
        think = _static_plan([{"action": FINISH_ACTION, "args": {"answer": None}}])
        planner = AgentPlanner(reg, think_fn=think)
        result = planner.run("my specific goal")
        assert result["goal"] == "my specific goal"

    def test_step_limit_respected(self):
        reg = _make_registry()
        # think_fn never issues FINISH — forces step-limit cut-off
        def think(_state):
            return {"action": "echo", "args": {"message": "loop"}}

        planner = AgentPlanner(reg, think_fn=think, max_steps=3)
        result = planner.run("loop forever")
        assert result["finished"] is False

    def test_steps_recorded(self):
        reg = _make_registry()
        think = _static_plan([
            {"action": "echo", "args": {"message": "hi"}},
            {"action": FINISH_ACTION, "args": {"answer": "done"}},
        ])
        planner = AgentPlanner(reg, think_fn=think, max_steps=10)
        result = planner.run("goal")
        # Each iteration produces think + act + observe steps (3 per tool call)
        # plus think + finish for the last step → total ≥ 4
        assert result["total_steps"] >= 4

    def test_step_types_present(self):
        reg = _make_registry()
        think = _static_plan([
            {"action": "echo", "args": {"message": "hi"}},
            {"action": FINISH_ACTION, "args": {"answer": "done"}},
        ])
        planner = AgentPlanner(reg, think_fn=think, max_steps=10)
        result = planner.run("goal")
        step_types = {s["type"] for s in result["steps"]}
        assert "think" in step_types
        assert "act" in step_types
        assert "observe" in step_types
        assert "finish" in step_types

    def test_observations_in_state(self):
        """think_fn receives observations from previous steps."""
        observations_seen = []

        reg = _make_registry()

        def think(state):
            observations_seen.append(list(state["observations"]))
            step = state["step"]
            if step == 0:
                return {"action": "add", "args": {"a": 1.0, "b": 2.0}}
            return {"action": FINISH_ACTION, "args": {"answer": "done"}}

        planner = AgentPlanner(reg, think_fn=think, max_steps=5)
        planner.run("goal")
        # Second call should see the observation from the add call
        assert len(observations_seen) >= 2
        assert len(observations_seen[1]) == 1
        assert observations_seen[1][0]["tool"] == "add"

    def test_unknown_tool_error_in_observation(self):
        reg = _make_registry()
        think = _static_plan([
            {"action": "nonexistent_tool", "args": {}},
            {"action": FINISH_ACTION, "args": {"answer": "done"}},
        ])
        planner = AgentPlanner(reg, think_fn=think, max_steps=5)
        result = planner.run("goal")
        obs = [s for s in result["steps"] if s["type"] == "observe"]
        # Observation for the failed tool call should capture the error
        assert obs[0]["tool_result"]["ok"] is False

    def test_initial_context_passed_to_state(self):
        captured_state = {}

        reg = _make_registry()

        def think(state):
            captured_state.update(state)
            return {"action": FINISH_ACTION, "args": {"answer": None}}

        planner = AgentPlanner(reg, think_fn=think)
        planner.run("goal", initial_context={"key": "value"})
        assert captured_state["context"]["key"] == "value"

    def test_answer_none_when_not_finished(self):
        reg = _make_registry()

        def think(_state):
            return {"action": "echo", "args": {"message": "loop"}}

        planner = AgentPlanner(reg, think_fn=think, max_steps=2)
        result = planner.run("loop")
        assert result["answer"] is None
        assert result["finished"] is False
