# MRL_Terminal — 終端系統立體種子（母體原生重寫，可獨立執行）
# origin_signature: MrLiouWord
# layer: MRL_Runtime / 立體種子核 (上中下三層打通)
"""終端系統立體種子核：TERMINAL ≡ ⟨Σ, Φo, Φa, Φr⟩。

母體原生重寫（非外部複製）：以結構+邏輯把「終端立體種子」實作為一支
stdlib-only、可獨立執行的母體核。三層打通：

    上層 Ω (World)  --Φo observe-->  中層 Σ (State)
    中層 Σ          --Φa advance-->  中層 Σ
    中層 Σ          --Φr reify   -->  下層→上層 Ω' (顯化回世界)

閉包律 C = { closed, no_return, no_goal, no_semantic }：
  - 系統不 halt、不 return 外部、不 external_write —— 純封閉可逆迴圈。
LAW-0 簽名律：Ω 與 Σ 皆須帶 origin_signature == "MrLiouWord"，否則閉包破壞。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Generator, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"


class InvariantError(Exception):
    """閉包/簽名不變量被破壞。"""


class MRL_Terminal:
    """⟨Σ, Φo, Φa, Φr⟩ 立體種子。

    Φo: Ω → Σ  觀察（上→中）
    Φa: Σ → Σ  推進（中）
    Φr: Σ → Ω  顯化（中→下→上）
    inOmega / inSigma：閉包檢查（預設套 LAW-0 簽名律）。
    """

    def __init__(
        self,
        phi_o: Callable[[Any], Any],
        phi_a: Callable[[Any], Any],
        phi_r: Callable[[Any], Any],
        in_omega: Optional[Callable[[Any], bool]] = None,
        in_sigma: Optional[Callable[[Any], bool]] = None,
    ) -> None:
        self.phi_o = phi_o
        self.phi_a = phi_a
        self.phi_r = phi_r
        self.in_omega = in_omega if in_omega is not None else self._law0
        self.in_sigma = in_sigma if in_sigma is not None else self._law0
        self.origin_signature = ORIGIN_SIGNATURE

    # LAW-0 預設閉包：物件需帶 origin_signature == MrLiouWord
    @staticmethod
    def _law0(x: Any) -> bool:
        if isinstance(x, dict):
            return x.get("origin_signature") == ORIGIN_SIGNATURE
        return getattr(x, "origin_signature", None) == ORIGIN_SIGNATURE

    def _check_omega(self, w: Any) -> None:
        if self.in_omega and not self.in_omega(w):
            raise InvariantError("Ω-closure violated (LAW-0)")

    def _check_sigma(self, s: Any) -> None:
        if self.in_sigma and not self.in_sigma(s):
            raise InvariantError("Σ-closure violated (LAW-0)")

    # 上→中
    def observe(self, w: Any) -> Any:
        self._check_omega(w)
        s = self.phi_o(w)
        self._check_sigma(s)
        return s

    # 中→中
    def advance(self, s: Any) -> Any:
        self._check_sigma(s)
        s2 = self.phi_a(s)
        self._check_sigma(s2)
        return s2

    # 中→下→上
    def reify(self, s: Any) -> Any:
        self._check_sigma(s)
        w = self.phi_r(s)
        self._check_omega(w)
        return w

    def step(self, w_t: Any) -> Tuple[Any, Any]:
        s_t = self.observe(w_t)
        s_a = self.advance(s_t)
        w_next = self.reify(s_a)
        s_next = self.observe(w_next)
        return (w_next, s_next)

    def run(self, w0: Any, max_steps: Optional[int] = None) -> Generator[Tuple[int, Any, Any], None, None]:
        """封閉迴圈：no_goal / no_return —— 預設無限；max_steps 僅為沙盒觀測用。"""
        self._check_omega(w0)
        t = 0
        w = w0
        s = self.observe(w)
        while True:
            yield (t, w, s)
            if max_steps is not None and t + 1 >= max_steps:
                return
            w, s = self.step(w)
            t += 1


# ── 沙盒自我驗收 ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sig = {"origin_signature": ORIGIN_SIGNATURE}

    # 上(世界)：counter 世界；中(狀態)：觀測快照；可逆顯化回世界。
    def phi_o(w: Dict[str, Any]) -> Dict[str, Any]:
        return {"observed": w["n"], **sig}

    def phi_a(s: Dict[str, Any]) -> Dict[str, Any]:
        return {"observed": s["observed"] + 1, **sig}

    def phi_r(s: Dict[str, Any]) -> Dict[str, Any]:
        return {"n": s["observed"], **sig}

    term = MRL_Terminal(phi_o, phi_a, phi_r)
    checks = []

    # 1. 三層迴圈 observe/advance/reify
    s0 = term.observe({"n": 0, **sig})
    s1 = term.advance(s0)
    w1 = term.reify(s1)
    checks.append(("observe/advance/reify", w1["n"] == 1))

    # 2. step 一步 = 上中下打通一圈
    w_next, s_next = term.step({"n": 5, **sig})
    checks.append(("step 打通一圈", w_next["n"] == 6 and s_next["observed"] == 6))

    # 3. run 封閉迴圈（沙盒取 5 步觀測）
    seq = list(term.run({"n": 0, **sig}, max_steps=5))
    checks.append(("run 封閉迴圈 5 步", [r[1]["n"] for r in seq] == [0, 1, 2, 3, 4]))

    # 4. LAW-0 閉包：無簽名世界必須被拒
    try:
        term.observe({"n": 0})
        checks.append(("LAW-0 拒絕無簽名", False))
    except InvariantError:
        checks.append(("LAW-0 拒絕無簽名", True))

    # 5. 全程 origin_signature 保存
    checks.append(("簽名保存", all(r[1]["origin_signature"] == ORIGIN_SIGNATURE for r in seq)))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"MRL_Terminal sandbox: {passed}/{len(checks)} "
          f"{'MRL_TERMINAL_ACCEPTANCE_PASS' if passed == len(checks) else 'FAIL'}")
