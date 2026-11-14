#!/usr/bin/env python3
"""MRL-47 reference adapter over the existing local Runtime. origin_signature: MrLiouWord."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from time import monotonic
from typing import Any

from MRL_artifact_trust_v1 import canonical, load_json
from MRL_capability_routing_v1 import (
    Clock,
    IDENTITY,
    Invocation,
    RegisteredAdapter,
    RoutingRejected,
    StubRouter,
    VERSION,
    evaluate_shadow,
    replay_receipt,
    timestamp,
    utc_now,
    validate_snapshot,
    wire_time,
)
from MRL_gate_schema_validator_v1 import SchemaRejected, product_catalog, require_wire_integer
from MRL_hardware_admission_v1 import digest

RUNTIME_ROOT = (
    Path(__file__).resolve().parents[3] / "MRL_Mother" / "MRL_MotherModel"
    / "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
)
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime import RUNTIME_ID
from runtime.MRL_local_model_adapter_v1 import MRLLocalModelAdapter, MRLModelGateError

ADAPTER_ID = "MRL_Reference_Adapter_v1"
ENGINEERING_BASE = "ccb13c3cedea9388d06cf9cbacdbb136d6a074ab"
CONFIG_SCHEMA = "reference-adapter-config-rc1-draft"
REQUEST_SCHEMA = "reference-adapter-request-rc1-draft"
USAGE_SCHEMA = "reference-adapter-usage-rc1-draft"
MAX_REQUEST_BYTES = 1024 * 1024
OPERATIONS = ("health", "capabilities", "models", "decision", "generate")
ERRORS = {
    "ADAPTER_DISABLED": ("The reference adapter is disabled.", "not_dispatched"),
    "INVALID_CONFIGURATION": ("The local adapter configuration was rejected.", "not_dispatched"),
    "INVALID_REQUEST": ("The versioned request was rejected.", "not_dispatched"),
    "EGRESS_DENIED": ("The local-only policy rejected the target or egress request.", "not_dispatched"),
    "MODEL_LOCALITY_UNKNOWN": ("The local model configuration could not be verified.", "not_dispatched"),
    "MODEL_UNAVAILABLE": ("The requested model is unavailable on this local adapter.", "not_dispatched"),
    "BACKEND_UNAVAILABLE": ("The local model endpoint did not complete the operation.", "unknown"),
    "BACKEND_HTTP_ERROR": ("The local model endpoint returned an HTTP error.", "unknown"),
    "BACKEND_REDIRECT_REJECTED": ("The local model endpoint returned a redirect.", "unknown"),
    "BACKEND_TIMEOUT": ("The local operation reached its deadline.", "unknown"),
    "BACKEND_INVALID_RESPONSE": ("The local model endpoint returned an invalid response.", "unknown"),
    "ROUTE_DECLINED": ("The router found no eligible target within the request policy.", "not_dispatched"),
}
USAGE_STATES = ("unknown", "partial", "reported")


class AdapterRejection(ValueError):
    """A rejection owned by the reference adapter control plane."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(ERRORS[code][0])


def _error(code: str, *, generation_attempted: bool = False) -> dict:
    message, delivery = ERRORS[code]
    return {
        "ok": False, "contract_version": VERSION, "adapter_id": ADAPTER_ID,
        "error": {
            "code": code, "message": message,
            "acceptance": delivery if generation_attempted else "not_dispatched",
        },
    }


def _bytes_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _request_payload(envelope: dict) -> tuple[dict, bytes]:
    envelope = deepcopy(envelope)
    try:
        product_catalog().validate(REQUEST_SCHEMA, envelope)
    except SchemaRejected as error:
        if error.path in {
            "/routing_request/data_handling/egress_allowed",
            "/routing_request/data_handling/approved_cloud_targets",
        } and error.keyword in {"const", "maxItems"}:
            raise AdapterRejection("EGRESS_DENIED") from None
        raise
    request = envelope["routing_request"]
    messages = envelope["messages"]
    if any(not message["content"].strip() for message in messages):
        raise AdapterRejection("INVALID_REQUEST")
    payload = canonical(messages)
    if len(payload) > MAX_REQUEST_BYTES or _bytes_digest(payload) != request["input_digest"]:
        raise AdapterRejection("INVALID_REQUEST")
    return request, payload


def _validate_usage(receipt: dict) -> None:
    product_catalog().validate(USAGE_SCHEMA, receipt)
    for name in ("input_tokens", "output_tokens"):
        require_wire_integer(receipt[name], (name,))


def _usage_receipt(route: dict, counts: dict, completed_at: str) -> dict:
    integrity = route["integrity"]
    target = next(target for target in route["replay_input"]["candidates"]
                  if target["target_id"] == route["resolved_target"])
    receipt = {
        "receipt_version": VERSION, **IDENTITY, "created_at": completed_at,
        "request_id": route["request_id"], "route_receipt_id": route["receipt_id"],
        "route_receipt_digest": integrity["receipt_digest"],
        "input_digest": integrity["input_digest"], "output_digest": integrity["output_digest"],
        "adapter_id": ADAPTER_ID, "parent_runtime_id": RUNTIME_ID,
        "engineering_base_commit": ENGINEERING_BASE,
        "execution_location": route["execution_location"],
        "requested_model": route["requested_model"],
        "resolved_model_version": route["resolved_model_version"],
        "runtime_version": target["runtime_snapshot"]["version"],
        **counts, "usage_state": USAGE_STATES[sum(count is not None for count in counts.values())],
    }
    receipt["receipt_id"] = "MRL_47_usage_" + digest(receipt).split(":", 1)[1]
    receipt["receipt_digest"] = digest(receipt)
    _validate_usage(receipt)
    return receipt


def replay_usage(receipt: dict, decision: dict, *, expected_digest: str | None = None) -> dict:
    """Rebuild the engineering receipt from its counts and a reproducible routing decision."""
    _validate_usage(receipt)
    decision = replay_receipt(decision)
    if (decision["outcome"] != "routed" or decision["execution_location"] != "local"
            or timestamp(receipt["created_at"]) < timestamp(decision["created_at"])):
        raise RoutingRejected("usage requires a completed local route")
    counts = {name: receipt[name] for name in ("input_tokens", "output_tokens")}
    reproduced = _usage_receipt(decision, counts, receipt["created_at"])
    if reproduced != receipt or (expected_digest is not None and receipt["receipt_digest"] != expected_digest):
        raise RoutingRejected("usage receipt does not match its routing and digest evidence")
    return reproduced


class MRLReferenceAdapter:
    """Backend-neutral text entry point with a single operator-configured local adapter."""

    def __init__(self, config: dict, *, clock: Clock = utc_now):
        config = deepcopy(config)
        product_catalog().validate(CONFIG_SCHEMA, config)
        self._policy = config["policy"]
        self._target = config["target"]
        self._enabled = config["enabled"]
        self._clock = clock
        self._runtime = MRLLocalModelAdapter(**config["local_model"])
        target = self._target
        if (target["model_artifact"]["model_id"] != self._runtime.model
                or target["runtime_snapshot"]["backend"] != self._runtime.backend
                or target["target_id"] not in self._policy["target_weights"]):
            raise AdapterRejection("INVALID_CONFIGURATION")

    def _require_enabled(self) -> None:
        if not self._enabled:
            raise AdapterRejection("ADAPTER_DISABLED")

    def health(self) -> dict:
        """Probe the configured model using metadata requests only."""
        try:
            self._require_enabled()
            self._runtime.require_local_model()
        except (AdapterRejection, MRLModelGateError) as error:
            return {**_error(error.code), "ready": False}
        return {
            "ok": True, "ready": True, "contract_version": VERSION, "adapter_id": ADAPTER_ID,
            "execution_location": "local", "model_id": self._runtime.model,
        }

    def capabilities(self) -> dict:
        """Describe the versioned interface without calling the backend."""
        return {
            "ok": True, "contract_version": VERSION, "adapter_id": ADAPTER_ID,
            "enabled": self._enabled, "execution_location": "local", "egress_allowed": False,
            "operations": list(OPERATIONS), "workload_classes": ["chat"], "capabilities": ["text"],
            "parent_runtime_id": RUNTIME_ID, "engineering_base_commit": ENGINEERING_BASE,
            **IDENTITY,
        }

    def models(self) -> dict:
        """Expose only the operator-configured and locally probed model."""
        status = self.health()
        if not status["ok"]:
            return {**status, "models": []}
        return {
            "ok": True, "contract_version": VERSION, "adapter_id": ADAPTER_ID,
            "models": [{
                "model_id": self._runtime.model, "available": True,
                "model_revision": self._target["model_artifact"]["revision"],
                "runtime_revision": self._target["runtime_snapshot"]["version"],
                "revision_source": "operator_snapshot",
            }],
        }

    def _prepare(self, envelope: dict) -> tuple[dict, bytes]:
        self._require_enabled()
        request, payload = _request_payload(envelope)
        snapshot = {
            "contract_version": VERSION, **IDENTITY, "sequence": 0,
            "previous_receipt_digest": None, "request": request,
            "policy": self._policy, "candidates": [deepcopy(self._target)],
        }
        validate_snapshot(snapshot)
        return snapshot, payload

    def _probe(self, snapshot: dict, deadline: float) -> tuple[str | None, datetime]:
        requested_model = snapshot["request"]["requested_model"]
        if requested_model != self._runtime.model:
            return "MODEL_UNAVAILABLE", self._clock()
        try:
            self._runtime.require_local_model(deadline=deadline)
        except MRLModelGateError as error:
            return error.code, self._clock()
        return None, self._clock()

    def _route(self, envelope: dict, *, generate: bool) -> dict:
        started = monotonic()
        try:
            snapshot, payload = self._prepare(envelope)
        except (SchemaRejected, RoutingRejected, UnicodeError, RecursionError):
            return _error("INVALID_REQUEST")
        except AdapterRejection as error:
            return _error(error.code)

        budget = snapshot["request"]["budgets"]["max_total_latency_ms"]
        deadline = started + budget / 1000
        failure, observed_at = self._probe(snapshot, deadline)
        if failure is None and monotonic() >= deadline:
            failure = "BACKEND_TIMEOUT"
        candidate = snapshot["candidates"][0]
        if failure:
            candidate["health"] = {
                "state": "unavailable", "observed_at": wire_time(observed_at), "score_bps": None,
            }
        # A successful probe does not refresh the separate control-plane health score or its age.

        inference: dict[str, Any] = {}
        generation_attempted = False
        completed_at = observed_at

        def invoke(call: Invocation) -> dict:
            nonlocal failure, generation_attempted, completed_at
            now = monotonic()
            if now >= deadline or call.timeout_ms <= 0:
                failure = "BACKEND_TIMEOUT"
                return {"status": "failed", "output_digest": None}
            dispatch_deadline = min(deadline, now + call.timeout_ms / 1000)
            messages = json.loads(call.payload)
            if monotonic() >= dispatch_deadline:
                failure = "BACKEND_TIMEOUT"
                return {"status": "failed", "output_digest": None}
            generation_attempted = True
            try:
                result = self._runtime.complete(
                    messages, report_missing_usage=True, deadline=dispatch_deadline,
                )
                output_digest = _bytes_digest(result["text"].encode("utf-8"))
            except MRLModelGateError as error:
                failure = error.code
                return {"status": "commit_unknown", "output_digest": None}
            except UnicodeError:
                failure = "BACKEND_INVALID_RESPONSE"
                return {"status": "commit_unknown", "output_digest": None}
            completed_at = max(observed_at, self._clock())
            inference.update(result)
            return {"status": "succeeded", "output_digest": output_digest}

        if generate:
            router = StubRouter(self._policy, {
                candidate["target_id"]: RegisteredAdapter("local", invoke),
            })
            decision = router.route_live(snapshot, payload, clock=lambda: observed_at)
        else:
            decision = evaluate_shadow(snapshot, evaluated_at=observed_at)
        if decision["outcome"] not in {"routed", "shadow_selected"}:
            return {
                **_error(failure or "ROUTE_DECLINED", generation_attempted=generation_attempted),
                "decision_receipt": decision, "usage_receipt": None,
            }
        result = {
            "ok": True, "contract_version": VERSION, "adapter_id": ADAPTER_ID,
            "decision_receipt": decision,
        }
        if generate:
            result["text"] = inference["text"]
            result["usage_receipt"] = _usage_receipt(decision, inference["usage"], wire_time(completed_at))
        return result

    def decision(self, envelope: dict) -> dict:
        """Evaluate a routing decision and return its receipt without model generation."""
        return self._route(envelope, generate=False)

    def generate(self, envelope: dict) -> dict:
        """Run one eligible local text generation and return correlated receipts."""
        return self._route(envelope, generate=True)


def _load_request(path: Path) -> dict:
    if path.stat().st_size > MAX_REQUEST_BYTES:
        raise AdapterRejection("INVALID_REQUEST")
    return load_json(path)


def main(argv: list[str] | None = None) -> int:
    """Expose the local interface without introducing a second HTTP gateway."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for operation in OPERATIONS:
        command = commands.add_parser(operation)
        command.add_argument("--config", type=Path, required=True)
        if operation in {"decision", "generate"}:
            command.add_argument("--request", type=Path, required=True)
    replay = commands.add_parser("replay")
    replay.add_argument("--decision", type=Path, required=True)
    replay.add_argument("--request", type=Path)
    replay.add_argument("--usage", type=Path)
    replay.add_argument("--expected-decision-digest")
    replay.add_argument("--expected-usage-digest")
    args = parser.parse_args(argv)
    if args.command == "replay":
        try:
            decision = replay_receipt(load_json(args.decision), expected_digest=args.expected_decision_digest)
            result = {"ok": True, "decision_receipt": decision}
            if args.request:
                request, _ = _request_payload(_load_request(args.request))
                if request != decision["replay_input"]["request"]:
                    raise RoutingRejected("request metadata does not match the replay input")
                result["request_digest_verified"] = decision["integrity"]["input_digest"]
            if args.usage:
                result["usage_receipt"] = replay_usage(
                    load_json(args.usage), decision, expected_digest=args.expected_usage_digest,
                )
        except (ValueError, OSError, RecursionError):
            result = _error("INVALID_REQUEST")
    else:
        try:
            adapter = MRLReferenceAdapter(load_json(args.config))
        except (ValueError, MRLModelGateError, OSError, RecursionError) as error:
            code = error.code if isinstance(error, (MRLModelGateError, AdapterRejection)) else "INVALID_CONFIGURATION"
            result = _error(code)
        else:
            action = getattr(adapter, args.command)
            try:
                if args.command in {"decision", "generate"}:
                    result = action(_load_request(args.request))
                else:
                    result = action()
            except (ValueError, OSError, RecursionError):
                result = _error("INVALID_REQUEST")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
