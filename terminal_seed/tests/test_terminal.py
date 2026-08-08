"""Tests for Terminal — core closed-loop system. origin_signature: MrLiouWord"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from terminal_seed.terminal import (
    Terminal, InvariantError, Step, ORIGIN_SIGNATURE, make_law0_terminal,
)


# ── Helpers ──

def _simple_terminal():
    """Terminal over numeric world/state: w*2 → s+1 → s/2."""
    return Terminal(
        Phi_o=lambda w: w * 2,
        Phi_a=lambda s: s + 1,
        Phi_r=lambda s: s / 2,
    )


def _dict_terminal():
    """Terminal over dict world/state with LAW-0."""
    return make_law0_terminal(
        transform_w_to_s=lambda w: {"v": w.get("v", 0) + 1, "tick": w.get("tick", 0)},
        advance_s=lambda s: {"v": s["v"] * 2, "tick": s["tick"] + 1},
        reify_s_to_w=lambda s: {"v": s["v"], "tick": s["tick"]},
    )


# ── Terminal basics ──

def test_origin_signature():
    assert ORIGIN_SIGNATURE == "MrLiouWord"


def test_observe():
    t = _simple_terminal()
    assert t.observe(5) == 10


def test_advance():
    t = _simple_terminal()
    assert t.advance(10) == 11


def test_reify():
    t = _simple_terminal()
    assert t.reify(10) == 5.0


def test_step():
    t = _simple_terminal()
    w_next, s_next = t.step(5)
    # observe(5)=10, advance(10)=11, reify(11)=5.5, observe(5.5)=11.0
    assert w_next == 5.5
    assert s_next == 11.0
    assert t.step_count == 1


def test_step_detailed():
    t = _simple_terminal()
    result = t.step_detailed(5)
    assert isinstance(result, Step)
    assert result.t == 1
    assert result.world == 5
    assert result.state == 10
    assert result.world_next == 5.5
    assert result.state_next == 11.0


def test_run_finite():
    t = _simple_terminal()
    results = t.run_n(1.0, 5)
    assert len(results) == 5
    assert results[0][0] == 0  # first tick
    assert results[4][0] == 4  # last tick


def test_run_generator():
    t = _simple_terminal()
    gen = t.run(1.0, max_steps=3)
    ticks = list(gen)
    assert len(ticks) == 3
    for i, (tick, w, s) in enumerate(ticks):
        assert tick == i


def test_step_count_increments():
    t = _simple_terminal()
    t.step(1.0)
    t.step(2.0)
    t.step(3.0)
    assert t.step_count == 3


# ── Invariant checks ──

def test_omega_closure_violation():
    t = Terminal(
        Phi_o=lambda w: w,
        Phi_a=lambda s: s,
        Phi_r=lambda s: s,
        in_omega=lambda w: w > 0,
    )
    with pytest.raises(InvariantError, match="Ω-closure"):
        t.observe(-1)


def test_sigma_closure_violation():
    t = Terminal(
        Phi_o=lambda w: -1,  # produces invalid state
        Phi_a=lambda s: s,
        Phi_r=lambda s: s,
        in_sigma=lambda s: s > 0,
    )
    with pytest.raises(InvariantError, match="Σ-closure"):
        t.observe(5)


def test_no_predicates_no_error():
    t = Terminal(
        Phi_o=lambda w: w,
        Phi_a=lambda s: s,
        Phi_r=lambda s: s,
    )
    # No predicates → no invariant checks → no error
    assert t.observe(-999) == -999


# ── LAW-0 terminal ──

def test_law0_terminal_signature_injection():
    t = _dict_terminal()
    w0 = {"v": 1, "tick": 0, "origin_signature": "MrLiouWord"}
    results = t.run_n(w0, 3)
    assert len(results) == 3
    for _, w, s in results:
        assert w.get("origin_signature") == "MrLiouWord"
        assert s.get("origin_signature") == "MrLiouWord"


def test_law0_terminal_rejects_bad_signature():
    t = _dict_terminal()
    w_bad = {"v": 1, "tick": 0, "origin_signature": "WRONG"}
    with pytest.raises(InvariantError, match="Ω-closure"):
        t.observe(w_bad)


def test_law0_terminal_values_evolve():
    t = _dict_terminal()
    w0 = {"v": 1, "tick": 0, "origin_signature": "MrLiouWord"}
    results = t.run_n(w0, 4)
    # Values should change across ticks
    values = [s.get("v") for _, _, s in results]
    assert len(set(values)) > 1  # not all the same
