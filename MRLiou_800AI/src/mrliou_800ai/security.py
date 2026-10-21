from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Mapping


def configured_token() -> str:
    """Return the configured API token without exposing it in logs."""
    token = os.environ.get("MRL_API_TOKEN", "").strip()
    if token:
        return token

    root = Path(os.environ.get("MRL_HOME", Path.cwd())).resolve()
    token_file = Path(os.environ.get("MRL_TOKEN_FILE", root / "secrets" / "api_token.txt"))
    try:
        return token_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def supplied_token(headers: Mapping[str, str]) -> str:
    direct = str(headers.get("X-MRL-Token", "")).strip()
    if direct:
        return direct

    authorization = str(headers.get("Authorization", "")).strip()
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def is_authorized(headers: Mapping[str, str]) -> bool:
    expected = configured_token()
    if not expected:
        return True
    candidate = supplied_token(headers)
    return bool(candidate) and hmac.compare_digest(candidate, expected)


def authentication_enabled() -> bool:
    return bool(configured_token())
