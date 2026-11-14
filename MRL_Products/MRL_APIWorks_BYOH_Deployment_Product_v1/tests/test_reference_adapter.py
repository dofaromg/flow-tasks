"""MRL-47 local reference adapter tests with synthetic provider responses."""

from __future__ import annotations

import contextlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import socket
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time
import unittest
from unittest.mock import patch

PRODUCT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PRODUCT / "scripts"))

from MRL_capability_routing_v1 import RoutingRejected, replay_receipt, wire_time
from MRL_gate_schema_validator_v1 import SchemaRejected, product_catalog
from MRL_reference_adapter_v1 import (
    VERSION, MRLReferenceAdapter, _bytes_digest, canonical, main, replay_usage,
)
from runtime.MRL_local_model_adapter_v1 import MRLModelGateError


MODEL = "MRL_fixture_model"
PROMPT = "MRL-47 synthetic private input"
OUTPUT = "MRL-47 synthetic local answer"
PROVIDER_ERROR = "MRL-47 synthetic provider secret"


class ProviderFixture:
    """Small protocol fixture for Ollama and llama.cpp on an ephemeral loopback port."""

    def __init__(self, backend="ollama"):
        self.backend = backend
        self.calls = []
        self.available = True
        self.inventory = None
        self.remote_alias = False
        self.metadata_missing = False
        self.redirect = None
        self.status = 200
        self.bad_json = False
        self.bad_content = False
        self.error_envelope = False
        self.usage = (7, 3)
        self.delay = 0
        self.probe_delay = 0
        self.chunk_delay = 0
        self.truncate_response = False
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def respond(self, status, body, headers=None):
                raw = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    truncated = fixture.truncate_response and self.path == fixture.chat_path
                    self.send_header("Content-Length", str(len(raw) + 8 if truncated else len(raw)))
                    for key, value in (headers or {}).items():
                        self.send_header(key, value)
                    self.end_headers()
                    if fixture.chunk_delay and self.path == fixture.chat_path:
                        for index in range(0, len(raw), 10):
                            self.wfile.write(raw[index:index + 10])
                            self.wfile.flush()
                            time.sleep(fixture.chunk_delay)
                    else:
                        self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def do_GET(self):
                fixture.calls.append((self.path, None))
                if fixture.probe_delay:
                    time.sleep(fixture.probe_delay)
                if fixture.inventory is not None:
                    self.respond(200, fixture.inventory)
                    return
                if self.path == "/api/tags" and fixture.backend == "ollama":
                    self.respond(200, {"models": [{"name": MODEL, "model": MODEL}] if fixture.available else []})
                elif self.path == "/v1/models" and fixture.backend == "llamacpp":
                    self.respond(200, {"data": [{"id": MODEL}] if fixture.available else []})
                else:
                    self.respond(404, {"error": "fixture route missing"})

            def do_POST(self):
                size = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(size))
                fixture.calls.append((self.path, payload))
                if self.path == "/api/show" and fixture.backend == "ollama":
                    details = {"details": {"format": "gguf"}, "model_info": {"general.architecture": "fixture"}}
                    if fixture.remote_alias:
                        details["remote_host"] = "https://mrl-egress.invalid"
                    self.respond(200, {} if fixture.metadata_missing else details)
                    return
                if self.path != fixture.chat_path:
                    self.respond(404, {"error": "fixture route missing"})
                    return
                if fixture.delay:
                    time.sleep(fixture.delay)
                if fixture.redirect:
                    status, location = fixture.redirect
                    self.respond(status, {"error": PROVIDER_ERROR}, {"Location": location})
                    return
                if fixture.status != 200:
                    self.respond(fixture.status, {"error": PROVIDER_ERROR})
                    return
                if fixture.bad_json:
                    self.respond(200, b'{"error":broken')
                    return
                content = {"private": PROVIDER_ERROR} if fixture.bad_content else OUTPUT
                counts = fixture.usage
                if fixture.backend == "ollama":
                    response = {"message": {"content": content}}
                    if counts is not None:
                        response.update(prompt_eval_count=counts[0], eval_count=counts[1])
                else:
                    response = {"choices": [{"message": {"content": content}}]}
                    if counts is not None:
                        response["usage"] = {"prompt_tokens": counts[0], "completion_tokens": counts[1]}
                if fixture.error_envelope:
                    response["error"] = PROVIDER_ERROR
                self.respond(200, response)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)

    @property
    def endpoint(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    @property
    def chat_path(self):
        return "/api/chat" if self.backend == "ollama" else "/v1/chat/completions"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    @property
    def generation_calls(self):
        return [payload for path, payload in self.calls if path == self.chat_path]


def reference_documents(fixture, now):
    """Adapt MRL-36 synthetic metadata to one local text model."""
    source = json.loads((PRODUCT / "tests/fixtures/mrl36/decision-input.json").read_text(encoding="utf-8"))
    target = source["candidates"][0]
    target["capabilities"] = ["text"]
    target["workload_classes"] = ["chat"]
    target["model_artifact"]["model_id"] = MODEL
    target["runtime_snapshot"]["backend"] = fixture.backend
    target["health"]["observed_at"] = wire_time(now)
    target["pricing"]["effective_at"] = wire_time(now - timedelta(hours=1))
    target["pricing"]["expires_at"] = wire_time(now + timedelta(hours=1))

    config = {
        "contract_version": VERSION, "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
        "enabled": True,
        "local_model": {"backend": fixture.backend, "endpoint": fixture.endpoint, "model": MODEL,
                        "timeout_seconds": 1},
        "target": target, "policy": source["policy"],
    }
    config["policy"].update(cloud_target_allowlist=[], cloud_classification_allowlist=[],
                            target_weights={target["target_id"]: 5000})
    messages = [{"role": "user", "content": PROMPT}]
    request = source["request"]
    request.update(task="text.generate", workload_class="chat", requested_model=MODEL,
                   required_capabilities=["text"], input_digest=_bytes_digest(canonical(messages)))
    request["data_handling"].update(egress_allowed=False, approved_cloud_targets=[])
    request["budgets"]["max_attempts"] = 1
    return config, {"contract_version": VERSION, "routing_request": request, "messages": messages}


class ReferenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 14, 18, 15, tzinfo=timezone.utc)

    def adapter(self, fixture, *, change=None):
        config, envelope = reference_documents(fixture, self.now)
        if change is not None:
            change(config)
        return MRLReferenceAdapter(config, clock=lambda: self.now), envelope

    def check_success(self, fixture):
        adapter, envelope = self.adapter(fixture)
        self.assertTrue(adapter.health()["ready"])
        self.assertEqual(adapter.models()["models"][0]["model_id"], MODEL)
        self.assertEqual(adapter.capabilities()["capabilities"], ["text"])
        prediction = adapter.decision(envelope)["decision_receipt"]
        self.assertEqual(prediction["outcome"], "shadow_selected")
        self.assertEqual(prediction["attempts"], [])
        self.assertEqual(replay_receipt(prediction), prediction)
        self.assertEqual(fixture.generation_calls, [])

        result = adapter.generate(envelope)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["text"], OUTPUT)
        route = result["decision_receipt"]
        self.assertEqual(route["mode"], "live")
        self.assertEqual(route["outcome"], "routed")
        self.assertEqual(route["execution_location"], "local")
        self.assertEqual(route["attempts"][0]["result"],
                         {"status": "succeeded", "output_digest": _bytes_digest(OUTPUT.encode("utf-8"))})
        self.assertEqual(replay_receipt(route), route)
        self.assertFalse(route["health_fallback"]["used"])
        self.assertEqual(route["replay_input"]["request"]["trace_id"], envelope["routing_request"]["trace_id"])

        usage = result["usage_receipt"]
        self.assertEqual((usage["input_tokens"], usage["output_tokens"]), (7, 3))
        self.assertEqual(usage["usage_state"], "reported")
        self.assertEqual(usage["request_id"], route["request_id"])
        self.assertEqual(usage["route_receipt_id"], route["receipt_id"])
        self.assertEqual(replay_usage(usage, route, expected_digest=usage["receipt_digest"]), usage)
        self.assertNotIn(PROMPT, json.dumps({"route": route, "usage": usage}))
        self.assertNotIn(OUTPUT, json.dumps({"route": route, "usage": usage}))
        self.assertEqual(fixture.generation_calls,
                         [{"model": MODEL, "messages": envelope["messages"], "stream": False}])

    def test_ollama_reference_end_to_end_and_receipts(self):
        with ProviderFixture("ollama") as fixture:
            self.check_success(fixture)

    def test_llamacpp_reference_end_to_end_and_receipts(self):
        with ProviderFixture("llamacpp") as fixture:
            self.check_success(fixture)

    def test_detection_without_metadata_is_fail_closed(self):
        with ProviderFixture() as fixture:
            fixture.metadata_missing = True
            adapter, envelope = self.adapter(fixture)
            self.assertEqual(adapter.models()["error"]["code"], "MODEL_LOCALITY_UNKNOWN")
            self.assertEqual(adapter.generate(envelope)["error"]["code"], "MODEL_LOCALITY_UNKNOWN")
            self.assertEqual(fixture.generation_calls, [])

    def test_operator_disable_uses_no_provider(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture, change=lambda config: config.update(enabled=False))
            self.assertFalse(adapter.capabilities()["enabled"])
            for operation in (adapter.health, adapter.models, lambda: adapter.generate(envelope)):
                self.assertEqual(operation()["error"]["code"], "ADAPTER_DISABLED")
            self.assertEqual(fixture.calls, [])

    def test_missing_model_has_replayable_no_route_without_prompt_dispatch(self):
        with ProviderFixture() as fixture:
            fixture.available = False
            adapter, envelope = self.adapter(fixture)
            self.assertEqual(adapter.models()["models"], [])
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["code"], "MODEL_UNAVAILABLE")
            self.assertEqual(result["error"]["acceptance"], "not_dispatched")
            route = result["decision_receipt"]
            self.assertEqual(route["outcome"], "no_route")
            self.assertEqual(replay_receipt(route), route)
            self.assertEqual(route["attempts"], [])
            self.assertIsNone(result["usage_receipt"])
            self.assertEqual(fixture.generation_calls, [])

    def test_unconfigured_model_never_contacts_backend(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            envelope["routing_request"]["requested_model"] = "MRL_other_model"
            self.assertEqual(adapter.generate(envelope)["error"]["code"], "MODEL_UNAVAILABLE")
            self.assertEqual(fixture.calls, [])

    def test_unsupported_capability_and_revision_do_not_dispatch(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            for key, value in (("required_capabilities", ["vision"]), ("required_runtime_revision", "other")):
                with self.subTest(key=key):
                    request = deepcopy(envelope)
                    request["routing_request"][key] = value
                    result = adapter.generate(request)
                    self.assertEqual(result["error"]["code"], "ROUTE_DECLINED")
                    self.assertEqual(result["decision_receipt"]["attempts"], [])
            self.assertEqual(fixture.generation_calls, [])

    def test_stale_control_plane_health_is_not_refreshed_by_probe(self):
        with ProviderFixture() as fixture:
            stale = wire_time(self.now - timedelta(hours=1))
            def change(config):
                config["target"]["health"]["observed_at"] = stale
            adapter, envelope = self.adapter(fixture, change=change)
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["code"], "ROUTE_DECLINED")
            self.assertIn("HEALTH_STALE", json.dumps(result["decision_receipt"]))
            self.assertEqual(fixture.generation_calls, [])

    def test_unknown_passport_evidence_and_expired_price_do_not_dispatch(self):
        with ProviderFixture() as fixture:
            for field in ("hardware", "pricing"):
                with self.subTest(field=field):
                    def change(config):
                        if field == "hardware":
                            config["target"]["hardware"] = None
                        else:
                            config["target"]["pricing"]["expires_at"] = wire_time(self.now)
                    adapter, envelope = self.adapter(fixture, change=change)
                    result = adapter.generate(envelope)
                    self.assertEqual(result["error"]["code"], "ROUTE_DECLINED")
                    self.assertEqual(result["decision_receipt"]["attempts"], [])
            self.assertEqual(fixture.generation_calls, [])

    def test_egress_intent_is_denied_before_provider_contact(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            for field, value in (("egress_allowed", True), ("approved_cloud_targets", ["cloud-test"])):
                with self.subTest(field=field):
                    request = deepcopy(envelope)
                    request["routing_request"]["data_handling"][field] = value
                    self.assertEqual(adapter.generate(request)["error"]["code"], "EGRESS_DENIED")
            self.assertEqual(fixture.calls, [])

    def test_remote_endpoint_configuration_is_rejected(self):
        with ProviderFixture() as fixture:
            for endpoint in ("https://mrl-egress.invalid", "http://192.0.2.9:9000",
                             "http://mrl-egress.invalid@127.0.0.1", "http://127.0.0.1?target=external",
                             "http://[::1]mrl-egress.invalid", "http://localhost:65536"):
                with self.subTest(endpoint=endpoint):
                    def change(config):
                        config["local_model"]["endpoint"] = endpoint
                    with self.assertRaises(MRLModelGateError) as failure:
                        self.adapter(fixture, change=change)
                    self.assertEqual(failure.exception.code, "EGRESS_DENIED")
            self.assertEqual(fixture.calls, [])

    def test_remote_alias_detected_before_prompt_is_sent(self):
        with ProviderFixture() as fixture:
            fixture.remote_alias = True
            adapter, envelope = self.adapter(fixture)
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["code"], "EGRESS_DENIED")
            self.assertEqual(result["decision_receipt"]["attempts"], [])
            self.assertEqual(fixture.generation_calls, [])
            self.assertNotIn(PROMPT, json.dumps(fixture.calls))

    def test_remote_alias_in_registry_rejected_without_metadata_post(self):
        with ProviderFixture() as fixture:
            fixture.inventory = {"models": [{"name": MODEL, "remote_model": "remote"}]}
            adapter, envelope = self.adapter(fixture)
            self.assertEqual(adapter.generate(envelope)["error"]["code"], "EGRESS_DENIED")
            self.assertEqual(fixture.calls, [("/api/tags", None)])

    def test_known_ollama_cloud_suffix_rejected_at_configuration(self):
        with ProviderFixture() as fixture:
            for suffix in (":cloud", ":70b:cloud", "-cloud"):
                with self.subTest(suffix=suffix):
                    config, _ = reference_documents(fixture, self.now)
                    config["local_model"]["model"] = MODEL + suffix
                    config["target"]["model_artifact"]["model_id"] = MODEL + suffix
                    with self.assertRaises(MRLModelGateError) as failure:
                        MRLReferenceAdapter(config)
                    self.assertEqual(failure.exception.code, "EGRESS_DENIED")
            self.assertEqual(fixture.calls, [])

    def test_proxy_environment_is_ignored(self):
        with ProviderFixture("llamacpp") as fixture, ProviderFixture("llamacpp") as proxy:
            adapter, envelope = self.adapter(fixture)
            variables = {"http_proxy": proxy.endpoint, "https_proxy": proxy.endpoint,
                         "HTTP_PROXY": proxy.endpoint, "HTTPS_PROXY": proxy.endpoint,
                         "no_proxy": "", "NO_PROXY": ""}
            with patch.dict(os.environ, variables):
                self.assertTrue(adapter.generate(envelope)["ok"])
            self.assertEqual(len(fixture.generation_calls), 1)
            self.assertEqual(proxy.calls, [])

    def test_redirects_do_not_forward_messages(self):
        with ProviderFixture("llamacpp") as fixture, ProviderFixture("llamacpp") as second:
            adapter, envelope = self.adapter(fixture)
            for status, location in ((302, second.endpoint + fixture.chat_path),
                                     (307, "http://mrl-egress.invalid" + fixture.chat_path),
                                     (308, second.endpoint + fixture.chat_path)):
                with self.subTest(status=status):
                    fixture.redirect = status, location
                    result = adapter.generate(envelope)
                    self.assertEqual(result["error"]["code"], "BACKEND_REDIRECT_REJECTED")
                    self.assertEqual(result["error"]["acceptance"], "unknown")
                    self.assertIsNone(result["usage_receipt"])
            self.assertEqual(second.calls, [])

    def test_localhost_alias_uses_literal_loopback_resolution(self):
        with ProviderFixture("llamacpp") as fixture:
            def change(config):
                config["local_model"]["endpoint"] = fixture.endpoint.replace("127.0.0.1", "LOCALHOST")
            adapter, envelope = self.adapter(fixture, change=change)
            resolver = socket.getaddrinfo
            names = []
            def track(host, *args, **kwargs):
                names.append(host)
                return resolver(host, *args, **kwargs)
            with patch("socket.getaddrinfo", side_effect=track):
                self.assertTrue(adapter.generate(envelope)["ok"])
            self.assertEqual(names, ["127.0.0.1", "127.0.0.1"])

    def test_literal_ipv6_endpoint_keeps_the_default_http_port(self):
        with ProviderFixture("llamacpp") as fixture:
            def change(config):
                config["local_model"]["endpoint"] = "http://[::1]"

            adapter, envelope = self.adapter(fixture, change=change)
            connect = socket.create_connection
            addresses = []

            def connect_fixture(address, *args):
                addresses.append(address)
                return connect(("127.0.0.1", fixture.server.server_port), *args)

            with patch("socket.create_connection", side_effect=connect_fixture):
                self.assertTrue(adapter.generate(envelope)["ok"])
            self.assertEqual(addresses, [("::1", 80), ("::1", 80)])

            def change_tls(config):
                config["local_model"]["endpoint"] = "https://[::1]"

            tls_adapter, _ = self.adapter(fixture, change=change_tls)
            with patch("socket.create_connection", side_effect=ConnectionRefusedError) as call:
                self.assertEqual(tls_adapter.health()["error"]["code"], "BACKEND_UNAVAILABLE")
            self.assertEqual(call.call_args.args[0], ("::1", 443))

    def test_unavailable_endpoint_reports_normalized_failure(self):
        with contextlib.closing(socket.socket()) as occupied, ProviderFixture("llamacpp") as fixture:
            occupied.bind(("127.0.0.1", 0))
            def change(config):
                config["local_model"]["endpoint"] = f"http://127.0.0.1:{occupied.getsockname()[1]}"
            adapter, envelope = self.adapter(fixture, change=change)
            self.assertEqual(adapter.health()["error"]["code"], "BACKEND_UNAVAILABLE")
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["acceptance"], "not_dispatched")
            self.assertEqual(result["decision_receipt"]["attempts"], [])

    def test_http_errors_are_sanitized_and_unconfirmed(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            for status in (404, 429, 500):
                with self.subTest(status=status):
                    fixture.status = status
                    result = adapter.generate(envelope)
                    self.assertEqual(result["error"]["code"], "BACKEND_HTTP_ERROR")
                    self.assertEqual(result["error"]["acceptance"], "unknown")
                    self.assertEqual(result["decision_receipt"]["attempts"][0]["result"]["status"], "commit_unknown")
                    self.assertEqual(replay_receipt(result["decision_receipt"]), result["decision_receipt"])
                    self.assertNotIn(PROVIDER_ERROR, json.dumps(result))
                    self.assertIsNone(result["usage_receipt"])
            self.assertEqual(len(fixture.generation_calls), 3)

    def test_malformed_provider_responses_do_not_fake_text_or_usage(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            for field in ("bad_json", "bad_content", "error_envelope"):
                with self.subTest(field=field):
                    setattr(fixture, field, True)
                    try:
                        result = adapter.generate(envelope)
                        self.assertEqual(result["error"]["code"], "BACKEND_INVALID_RESPONSE")
                        self.assertIsNone(result["usage_receipt"])
                        self.assertNotIn(PROVIDER_ERROR, json.dumps(result))
                    finally:
                        setattr(fixture, field, False)

    def test_nonstream_socket_timeout_stops_without_retry(self):
        with ProviderFixture("llamacpp") as fixture:
            fixture.delay = 0.2
            def change(config):
                config["local_model"]["timeout_seconds"] = 0.04
            adapter, envelope = self.adapter(fixture, change=change)
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["code"], "BACKEND_TIMEOUT")
            self.assertEqual(result["decision_receipt"]["attempts"][0]["result"]["status"], "commit_unknown")
            self.assertEqual(len(fixture.generation_calls), 1)
            self.assertIsNone(result["usage_receipt"])

    def test_total_deadline_caps_inventory_probe_before_prompt_dispatch(self):
        with ProviderFixture("llamacpp") as fixture:
            fixture.probe_delay = 0.5
            adapter, envelope = self.adapter(fixture)
            envelope["routing_request"]["budgets"]["max_total_latency_ms"] = 150
            started = time.monotonic()
            result = adapter.generate(envelope)
            self.assertLess(time.monotonic() - started, 0.4)
            self.assertEqual(result["error"]["code"], "BACKEND_TIMEOUT")
            self.assertEqual(result["error"]["acceptance"], "not_dispatched")
            self.assertEqual(result["decision_receipt"]["attempts"], [])
            self.assertEqual(fixture.generation_calls, [])

    def test_total_deadline_interrupts_a_trickling_completion(self):
        with ProviderFixture("llamacpp") as fixture:
            fixture.chunk_delay = 0.05
            adapter, envelope = self.adapter(fixture)
            envelope["routing_request"]["budgets"]["max_total_latency_ms"] = 350
            started = time.monotonic()
            result = adapter.generate(envelope)
            self.assertLess(time.monotonic() - started, 0.65)
            self.assertEqual(result["error"]["code"], "BACKEND_TIMEOUT")
            self.assertEqual(result["error"]["acceptance"], "unknown")
            self.assertEqual(result["decision_receipt"]["attempts"][0]["result"]["status"], "commit_unknown")
            self.assertEqual(len(fixture.generation_calls), 1)

    def test_truncated_content_length_rejects_a_complete_json_prefix(self):
        with ProviderFixture("llamacpp") as fixture:
            fixture.truncate_response = True
            adapter, envelope = self.adapter(fixture)
            result = adapter.generate(envelope)
            self.assertEqual(result["error"]["code"], "BACKEND_INVALID_RESPONSE")
            self.assertEqual(result["error"]["acceptance"], "unknown")
            self.assertIsNone(result["usage_receipt"])

    def test_missing_and_invalid_usage_are_not_turned_into_observed_zero(self):
        with ProviderFixture("llamacpp") as fixture:
            adapter, envelope = self.adapter(fixture)
            for counts, expected in ((None, (None, None, "unknown")),
                                     ((0, -3), (0, None, "partial")),
                                     ((True, "5"), (None, None, "unknown"))):
                with self.subTest(counts=counts):
                    fixture.usage = counts
                    result = adapter.generate(envelope)
                    usage = result["usage_receipt"]
                    self.assertEqual((usage["input_tokens"], usage["output_tokens"], usage["usage_state"]), expected)
                    self.assertEqual(replay_usage(usage, result["decision_receipt"]), usage)

    def test_request_payload_digest_unknown_fields_and_invalid_integer_fail_closed(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            for kind in ("changed-prompt", "provider-option", "wrong-version", "float-budget", "surrogate"):
                with self.subTest(kind=kind):
                    request = deepcopy(envelope)
                    if kind == "changed-prompt":
                        request["messages"][0]["content"] += " changed"
                    elif kind == "provider-option":
                        request["endpoint"] = "https://mrl-egress.invalid"
                    elif kind == "wrong-version":
                        request["contract_version"] = "0.1-RC0"
                    elif kind == "float-budget":
                        request["routing_request"]["budgets"]["max_attempts"] = 1.0
                    else:
                        request["messages"][0]["content"] = chr(0xD800)
                    self.assertEqual(adapter.generate(request)["error"]["code"], "INVALID_REQUEST")
            self.assertEqual(fixture.calls, [])

    def test_adapter_result_schema_does_not_accept_control_plane_fields(self):
        result = {"status": "succeeded", "output_digest": _bytes_digest(OUTPUT.encode("utf-8"))}
        product_catalog().validate("routing-adapter-result-rc1-draft", result)
        with self.assertRaises(SchemaRejected):
            product_catalog().validate("routing-adapter-result-rc1-draft", {
                **result, "egress_allowed": True,
            })

    def test_usage_replay_rejects_bad_links_and_tampering(self):
        with ProviderFixture() as fixture:
            adapter, envelope = self.adapter(fixture)
            first = adapter.generate(envelope)
            usage, route = first["usage_receipt"], first["decision_receipt"]
            for modified in ({**usage, "input_tokens": 8}, {**usage, "request_id": "other"}):
                with self.assertRaises(RoutingRejected):
                    replay_usage(modified, route)
            with self.assertRaises(RoutingRejected):
                replay_usage(usage, route, expected_digest="sha256:" + "0" * 64)
            with self.assertRaises(SchemaRejected):
                replay_usage({**usage, "input_tokens": 7.0}, route)

    def test_cli_end_to_end_and_offline_replay(self):
        with ProviderFixture("llamacpp") as fixture, TemporaryDirectory() as directory:
            config, envelope = reference_documents(fixture, datetime.now(timezone.utc))
            root = Path(directory)
            config_path, request_path = root / "config.json", root / "request.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            request_path.write_text(json.dumps(envelope), encoding="utf-8")
            def run(*args):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    code = main(list(args))
                return code, json.loads(output.getvalue())
            code, result = run("generate", "--config", str(config_path), "--request", str(request_path))
            self.assertEqual(code, 0, result)
            decision_path, usage_path = root / "decision.json", root / "usage.json"
            decision_path.write_text(json.dumps(result["decision_receipt"]), encoding="utf-8")
            usage_path.write_text(json.dumps(result["usage_receipt"]), encoding="utf-8")
            previous_calls = list(fixture.calls)
            route = result["decision_receipt"]
            code, replayed = run("replay", "--decision", str(decision_path), "--request", str(request_path),
                                 "--usage", str(usage_path), "--expected-decision-digest",
                                 route["integrity"]["receipt_digest"], "--expected-usage-digest",
                                 result["usage_receipt"]["receipt_digest"])
            self.assertEqual(code, 0)
            self.assertEqual(replayed["request_digest_verified"], route["integrity"]["input_digest"])
            self.assertEqual(replayed["usage_receipt"], result["usage_receipt"])
            envelope["routing_request"]["trace_id"] = "wrong-trace"
            request_path.write_text(json.dumps(envelope), encoding="utf-8")
            code, invalid = run("replay", "--decision", str(decision_path), "--request", str(request_path))
            self.assertEqual(code, 2)
            self.assertEqual(invalid["error"]["code"], "INVALID_REQUEST")
            self.assertEqual(fixture.calls, previous_calls)
            request_path.write_text('{"contract_version": "1", "contract_version": "2"}', encoding="utf-8")
            code, invalid = run("generate", "--config", str(config_path), "--request", str(request_path))
            self.assertEqual(code, 2)
            self.assertEqual(invalid["error"]["code"], "INVALID_REQUEST")


if __name__ == "__main__":
    unittest.main()
