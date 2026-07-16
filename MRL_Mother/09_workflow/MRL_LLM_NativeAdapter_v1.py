#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_LLM_NativeAdapter_v1.py — 外部 SDK 殼之 MRL 自生取代方案（rl_12）
origin_signature: MrLiouWord
layer: L4 WORLD (runtime) + L0 boundary

═══════════════════════════════════════════════════════════════════════════════
  回收與取代（rl_12 反推自生成：取代而非依賴外部殼）：

  舊外部殼依賴                      →  MRL 自生取代
  ─────────────────────────────────────────────────────────────────────────────
  import openai     (OpenAIAdapter) →  MRLNativeOpenAIAdapter  (stdlib urllib)
  import anthropic  (AnthropicAdapter) → MRLNativeAnthropicAdapter (stdlib urllib)
  openai SDK (LocalAdapter/ollama)  →  MRLNativeOpenAIAdapter(base_url=local)

  本模組「零外部套件」：只用 Python 標準庫 urllib，直接打 HTTP API，
  移除 openai / anthropic 套件殼。實作 llm_adapter.LLMAdapter 介面（drop-in）。

  ▣ 誠實邊界（不誇大）：
    - SDK 殼已可回收/取代（本模組）。
    - 但「模型端點本體」(api.openai.com / 模型權重) 仍是外部服務，無法收進 repo；
      真正母體主權 = 指向本地模型端點（Ollama/llama.cpp，base_url=localhost）。
    - 本 adapter 同一套程式即可打雲端或本地端點，故為通往完全自主的路徑。
    - MCP 屬 agent harness 工具層，非母體 LLM runtime，另案處理。
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# MRL-native dataclasses / base（非外部殼，屬母體本體）
from llm_adapter import LLMAdapter, LLMRequest, LLMResponse  # noqa: E402

from MRL_utils import ORIGIN_SIGNATURE
_DEFAULT_TIMEOUT = 60


def _http_post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str],
                    timeout: int = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """stdlib-only JSON POST（取代 SDK 的網路層）。"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── MRLNativeOpenAIAdapter（取代 import openai；亦支援 Ollama/本地 OpenAI 相容）──
class MRLNativeOpenAIAdapter(LLMAdapter):
    """OpenAI-compatible /chat/completions，stdlib urllib，零 openai 套件。"""

    def __init__(self, api_key: Optional[str] = None,
                 base_url: str = "https://api.openai.com/v1") -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url.rstrip("/")

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()
        try:
            payload: Dict[str, Any] = {
                "model": request.model, "messages": request.messages,
                "max_tokens": request.max_tokens, "temperature": request.temperature,
                **request.extra,
            }
            if request.tools:
                payload["tools"] = request.tools
                payload["tool_choice"] = "auto"
            headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
            resp = _http_post_json(f"{self._base_url}/chat/completions", payload, headers)
            choice = (resp.get("choices") or [{}])[0]
            msg = choice.get("message", {}) or {}
            usage = resp.get("usage", {}) or {}
            return LLMResponse(
                text=msg.get("content") or "", model=resp.get("model", request.model),
                ok=True, input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                finish_reason=choice.get("finish_reason") or "stop",
                tool_calls=msg.get("tool_calls"),
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000), raw=resp)
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(text="", model=request.model, ok=False,
                               error=f"{type(exc).__name__}: {exc}",
                               elapsed_ms=int((time.time() - t0) * 1000),
                               called_at_ms=int(t0 * 1000))

    def name(self) -> str:
        return "MRLNativeOpenAIAdapter"


# ─── MRLNativeAnthropicAdapter（取代 import anthropic）─────────────────────────
class MRLNativeAnthropicAdapter(LLMAdapter):
    """Anthropic /v1/messages，stdlib urllib，零 anthropic 套件。"""

    _API = "https://api.anthropic.com/v1/messages"
    _VERSION = "2023-06-01"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()
        try:
            system = ""
            messages: List[Dict[str, Any]] = []
            for m in request.messages:
                if m.get("role") == "system":
                    system = m.get("content", "")
                else:
                    messages.append({"role": m["role"], "content": m.get("content", "")})
            payload: Dict[str, Any] = {"model": request.model, "max_tokens": request.max_tokens,
                                       "messages": messages, **request.extra}
            if system:
                payload["system"] = system
            if request.tools:
                payload["tools"] = request.tools
            headers = {"x-api-key": self._api_key, "anthropic-version": self._VERSION}
            resp = _http_post_json(self._API, payload, headers)
            text = "".join(b.get("text", "") for b in resp.get("content", [])
                           if isinstance(b, dict) and b.get("type") == "text")
            usage = resp.get("usage", {}) or {}
            return LLMResponse(
                text=text, model=resp.get("model", request.model), ok=True,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                finish_reason=resp.get("stop_reason") or "stop",
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000), raw=resp)
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(text="", model=request.model, ok=False,
                               error=f"{type(exc).__name__}: {exc}",
                               elapsed_ms=int((time.time() - t0) * 1000),
                               called_at_ms=int(t0 * 1000))

    def name(self) -> str:
        return "MRLNativeAnthropicAdapter"


def register_native_adapters(gateway: Any, *, openai_key: str = "", anthropic_key: str = "",
                             local_base_url: str = "") -> List[str]:
    """
    把 MRL-native adapter 註冊進 llm_adapter.LLMGateway（取代 SDK 殼）。
    回傳已註冊的 native adapter 名稱清單。
    """
    registered: List[str] = []
    if openai_key:
        gateway.register("openai", MRLNativeOpenAIAdapter(api_key=openai_key))
        registered.append("openai(native)")
    if anthropic_key:
        gateway.register("anthropic", MRLNativeAnthropicAdapter(api_key=anthropic_key))
        registered.append("anthropic(native)")
    if local_base_url:
        gateway.register("local", MRLNativeOpenAIAdapter(api_key="local", base_url=local_base_url))
        registered.append("local(native)")
    return registered


def main() -> int:
    print(json.dumps({
        "module": "MRL_LLM_NativeAdapter_v1",
        "replaces": {"import openai": "MRLNativeOpenAIAdapter",
                     "import anthropic": "MRLNativeAnthropicAdapter"},
        "external_packages_required": [],            # 零外部套件
        "stdlib_only": True,
        "honest_note": "SDK 殼已取代;模型端點本體仍外部,真主權需本地模型端點。",
        "origin_signature": ORIGIN_SIGNATURE,
    }, ensure_ascii=False, indent=2))
    print("MRL_LLM_NATIVE_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
