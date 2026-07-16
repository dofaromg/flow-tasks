"""test_MRL_mother_gateway_adapter.py (origin: MrLiouWord)

接母體已上線真模型 gateway 的 adapter。
- 離線安全:單元測 flatten / 建構不需網路。
- live e2e:探測端點可達才跑(不可達自動 skip,不破離線 CI)。
"""
import os, sys, json, urllib.request
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_MotherGateway_Adapter_v1 import (
    MRLNativeMotherGatewayAdapter, _flatten, _DEFAULT_URL, _DEFAULT_MODEL_ID,
)
from llm_adapter import LLMRequest


_ENDPOINT = os.environ.get("MRL_MOTHER_GATEWAY_URL", _DEFAULT_URL)


def _reachable() -> bool:
    try:
        req = urllib.request.Request(
            _ENDPOINT, data=json.dumps({"message": "ping", "model": _DEFAULT_MODEL_ID}).encode(),
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "MRL-Mother/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


# ── 離線安全單元測 ──
def test_flatten_single_message():
    assert _flatten([{"role": "user", "content": "hi"}]) == "hi"


def test_flatten_multi_turn_labels_roles():
    out = _flatten([
        {"role": "system", "content": "S"},
        {"role": "user", "content": "U"},
        {"role": "assistant", "content": "A"},
    ])
    assert "[系統] S" in out and "[使用者] U" in out and "[助理] A" in out


def test_adapter_defaults_and_origin():
    a = MRLNativeMotherGatewayAdapter()
    assert a._url == _DEFAULT_URL
    assert a._remote_model == _DEFAULT_MODEL_ID
    assert a.origin_signature == "MrLiouWord"
    assert a.name() == "MRLNativeMotherGatewayAdapter"


# ── live e2e（明確 opt-in 才跑，避免在收集階段打網路拖慢/卡住離線 CI）──
# 設 MRL_LIVE_E2E=1 才嘗試；reachability 檢查移到函式內，離線時 collection 不打網路。
@pytest.mark.skipif(os.environ.get("MRL_LIVE_E2E") != "1",
                    reason="live e2e 需 opt-in：設 MRL_LIVE_E2E=1 才跑")
def test_live_real_generation():
    if not _reachable():
        pytest.skip("母體 gateway 端點不可達（離線/沙盒）")
    a = MRLNativeMotherGatewayAdapter()
    resp = a.complete(LLMRequest(
        model="mrl-mother",
        messages=[{"role": "user", "content": "用一句話證明你是真模型"}]))
    assert resp.ok is True
    assert isinstance(resp.text, str) and len(resp.text) > 0
    assert resp.model  # 回報實際模型 id
