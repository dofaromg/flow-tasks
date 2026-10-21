"""
Terminal — Formal closed-loop system
origin_signature: MrLiouWord

⊢ TERMINAL ≡ ⟨Σ, Φo, Φa, Φr⟩
C = { closed, no_return, no_goal, no_semantic }
∄ halt, ∄ return, ∄ external_write

Φo: Ω → Σ  (observe: world → state)
Φa: Σ → Σ  (advance: state → state)
Φr: Σ → Ω  (reify:   state → world)

LAW-0: All values must carry origin_signature="MrLiouWord"
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Tuple, TypeVar

Omega = TypeVar("Omega")  # World type
Sigma = TypeVar("Sigma")  # State type

ORIGIN_SIGNATURE = "MrLiouWord"


class InvariantError(Exception):
    """Raised when Ω-closure or Σ-closure is violated."""
    pass


@dataclass
class Step:
    """Result of a single terminal step."""
    t: int
    world: Any
    state: Any
    world_next: Any
    state_next: Any


class Terminal:
    """
    Generic Terminal system: ⟨Σ, Φo, Φa, Φr⟩

    Matches the spec's Python/Java/PHP/TypeScript/Rust/Go implementations.
    All operations enforce closure invariants (LAW-0).
    """

    def __init__(
        self,
        Phi_o: Callable,       # Ω → Σ
        Phi_a: Callable,       # Σ → Σ
        Phi_r: Callable,       # Σ → Ω
        in_omega: Optional[Callable] = None,  # Ω predicate
        in_sigma: Optional[Callable] = None,  # Σ predicate
    ):
        self.Phi_o = Phi_o
        self.Phi_a = Phi_a
        self.Phi_r = Phi_r
        self.in_omega = in_omega
        self.in_sigma = in_sigma
        self.step_count = 0
        self.origin_signature = ORIGIN_SIGNATURE

    def check_omega(self, w) -> None:
        """Verify Ω-closure."""
        if self.in_omega and not self.in_omega(w):
            raise InvariantError("Ω-closure violated")

    def check_sigma(self, s) -> None:
        """Verify Σ-closure."""
        if self.in_sigma and not self.in_sigma(s):
            raise InvariantError("Σ-closure violated")

    def observe(self, w):
        """Φo: Ω → Σ — observe world, produce state."""
        self.check_omega(w)
        s = self.Phi_o(w)
        self.check_sigma(s)
        return s

    def advance(self, s):
        """Φa: Σ → Σ — advance state."""
        self.check_sigma(s)
        s2 = self.Phi_a(s)
        self.check_sigma(s2)
        return s2

    def reify(self, s):
        """Φr: Σ → Ω — reify state back to world."""
        self.check_sigma(s)
        w = self.Phi_r(s)
        self.check_omega(w)
        return w

    def step(self, w_t) -> Tuple:
        """
        Full cycle: observe → advance → reify → observe.
        Returns (w_next, s_next).
        """
        s_t = self.observe(w_t)
        s_a = self.advance(s_t)
        w_next = self.reify(s_a)
        s_next = self.observe(w_next)
        self.step_count += 1
        return (w_next, s_next)

    def step_detailed(self, w_t) -> Step:
        """Full cycle with detailed result."""
        s_t = self.observe(w_t)
        s_a = self.advance(s_t)
        w_next = self.reify(s_a)
        s_next = self.observe(w_next)
        self.step_count += 1
        return Step(
            t=self.step_count,
            world=w_t, state=s_t,
            world_next=w_next, state_next=s_next,
        )

    def run(self, w0, max_steps: Optional[int] = None) -> Iterator[Tuple[int, Any, Any]]:
        """
        Infinite generator: yields (t, world, state) at each tick.
        Matches the spec's run() across all 6 languages.
        """
        self.check_omega(w0)
        t = 0
        w = w0
        s = self.observe(w)

        while max_steps is None or t < max_steps:
            yield (t, w, s)
            w, s = self.step(w)
            t += 1

    def run_n(self, w0, n: int) -> List[Tuple[int, Any, Any]]:
        """Run for exactly n steps, return list of (t, world, state)."""
        return list(self.run(w0, max_steps=n))


def make_law0_terminal(
    transform_w_to_s: Callable,
    advance_s: Callable,
    reify_s_to_w: Callable,
) -> Terminal:
    """
    Create a Terminal with LAW-0 signature enforcement.
    All world/state dicts must have origin_signature="MrLiouWord".
    """
    def phi_o(w):
        s = transform_w_to_s(w)
        if isinstance(s, dict):
            s["origin_signature"] = ORIGIN_SIGNATURE
        return s

    def phi_a(s):
        s2 = advance_s(s)
        if isinstance(s2, dict):
            s2["origin_signature"] = ORIGIN_SIGNATURE
        return s2

    def phi_r(s):
        w = reify_s_to_w(s)
        if isinstance(w, dict):
            w["origin_signature"] = ORIGIN_SIGNATURE
        return w

    def in_omega(w):
        if isinstance(w, dict):
            return w.get("origin_signature") == ORIGIN_SIGNATURE
        return True

    def in_sigma(s):
        if isinstance(s, dict):
            return s.get("origin_signature") == ORIGIN_SIGNATURE
        return True

    return Terminal(phi_o, phi_a, phi_r, in_omega, in_sigma)
