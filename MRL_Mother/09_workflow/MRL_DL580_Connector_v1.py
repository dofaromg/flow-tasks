#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_DL580_Connector_v1.py — 連 DL580 伺服器 API 連接器
origin_signature: MrLiouWord
layer: L6 GATEWAY / DL580 BRIDGE

實連定位(沙盒實測):DL580 對外 API 活著 = https://dl580.mrliouword.com
(Express 後端,非空殼;/api/stripe/config 回真 JSON)。對話端點 /api/chat/stream
需授權(回 401 Unauthorized)。本連接器把母體接上此端點,支援:
  - 端點可配置:env MRL_DL580_API(預設 https://dl580.mrliouword.com)
  - 授權可配置:env MRL_DL580_TOKEN(Bearer)或 MRL_DL580_COOKIE(session cookie)
純 stdlib urllib、零外部套件。授權給了即真生成;沒給則誠實回 401(不偽造)。

CLI:python3 09_workflow/MRL_DL580_Connector_v1.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
_DEFAULT_API = "https://dl580.mrliouword.com"
_STREAM_PATH = "/api/chat/stream"


class MRL_DL580Connector:
    """連 DL580 伺服器對話 API(/api/chat/stream),授權可配置。"""

    def __init__(self, api_base: Optional[str] = None,
                 token: Optional[str] = None,
                 cookie: Optional[str] = None,
                 timeout: int = 60) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.api_base = (api_base or os.environ.get("MRL_DL580_API", "") or _DEFAULT_API).rstrip("/")
        self.token = token or os.environ.get("MRL_DL580_TOKEN", "")
        self.cookie = cookie or os.environ.get("MRL_DL580_COOKIE", "")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json",
             "User-Agent": "MRL-Mother/1.0 (origin_signature=MrLiouWord)",
             "Accept": "text/event-stream, application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if self.cookie:
            h["Cookie"] = self.cookie
        return h

    def chat(self, message: str, *, messages: Optional[List[Dict[str, Any]]] = None,
             model: str = "") -> Dict[str, Any]:
        msgs = messages or [{"role": "user", "content": message}]
        payload: Dict[str, Any] = {"messages": msgs}
        if model:
            payload["model"] = model
        url = self.api_base + _STREAM_PATH
        data = json.dumps(payload).encode("utf-8")
        t0 = time.time()
        req = urllib.request.Request(url, data=data, method="POST", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8", "replace")
            text = self._parse_stream(raw)
            return {"ok": True, "reply": text, "endpoint": url,
                    "elapsed_ms": int((time.time() - t0) * 1000),
                    "origin_signature": ORIGIN_SIGNATURE}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            return {"ok": False, "http": e.code, "endpoint": url, "body": body,
                    "authorized": e.code != 401,
                    "hint": "設 MRL_DL580_TOKEN 或 MRL_DL580_COOKIE 授權" if e.code == 401 else "",
                    "origin_signature": ORIGIN_SIGNATURE}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                    "endpoint": url, "origin_signature": ORIGIN_SIGNATURE}

    @staticmethod
    def _parse_stream(raw: str) -> str:
        """解 SSE(data: ...)或純 JSON,抽出文字。"""
        out: List[str] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            if line in ("[DONE]", ""):
                continue
            try:
                obj = json.loads(line)
            except Exception:
                out.append(line)
                continue
            piece = (obj.get("response") or obj.get("reply") or obj.get("content")
                     or obj.get("delta", {}).get("content") if isinstance(obj.get("delta"), dict) else None)
            if not piece and obj.get("choices"):
                ch = obj["choices"][0]
                piece = (ch.get("delta", {}) or {}).get("content") or (ch.get("message", {}) or {}).get("content")
            if piece:
                out.append(piece)
        return "".join(out) if out else raw[:500]

    def health(self) -> Dict[str, Any]:
        """確認 DL580 後端是否活著(打 /api/stripe/config 這個免授權真 API)。"""
        url = self.api_base + "/api/stripe/config"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MRL-Mother/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                alive = r.status == 200 and "json" in r.headers.get("content-type", "")
            return {"alive": alive, "endpoint": self.api_base, "origin_signature": ORIGIN_SIGNATURE}
        except Exception as exc:  # noqa: BLE001
            return {"alive": False, "endpoint": self.api_base, "error": str(exc)}


def main() -> int:
    c = MRL_DL580Connector()
    print(f"DL580 API: {c.api_base}")
    print("後端存活:", json.dumps(c.health(), ensure_ascii=False))
    r = c.chat("用一句話自我介紹,證明你是 DL580 上的真模型")
    print("對話結果:", json.dumps(r, ensure_ascii=False))
    if not r["ok"] and r.get("http") == 401:
        print("→ 連線通到真端點,卡在授權:設 MRL_DL580_TOKEN(Bearer)或 MRL_DL580_COOKIE 即真生成。")
    print("MRL_DL580_CONNECTOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
