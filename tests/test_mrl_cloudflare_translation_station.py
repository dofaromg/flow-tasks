"""Tests for the non-destructive MRL/Cloudflare translation boundary."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mrl_cloudflare_translation_station import (  # noqa: E402
    DEFAULT_MAP,
    TranslationError,
    find_external_node,
    inspect_node,
    load_registry,
    score_delta_vector,
    translate_forward,
    translate_reverse,
    utf8_to_base64_chunked,
    validate_registry,
    verify_encoding_invariant,
)


SHA = "43ff96f75833c4ef2da92afd1f415cd533e848d1"


class TranslationStationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(DEFAULT_MAP)

    def test_registry_has_complete_parameter_and_node_coverage(self) -> None:
        result = validate_registry(self.registry)
        self.assertEqual(result["parameters"], 13)
        self.assertEqual(result["canonical_profiles"], 4)
        self.assertEqual(result["external_nodes"], 4)
        self.assertEqual(result["method_changes"], 3)

    def test_every_current_external_node_is_held(self) -> None:
        for node in self.registry["external_nodes"]:
            result = inspect_node(
                self.registry,
                node["provider_kind"],
                node["external_project"],
            )
            self.assertEqual(result["effective_action"], "HOLD")

    def test_unknown_critical_parameters_never_pass(self) -> None:
        node = find_external_node(self.registry, "workers", "mrl-store")
        score = score_delta_vector(self.registry, node["delta_states"])
        self.assertTrue(score["decision"].startswith("HOLD_"))
        self.assertIn("delta_identity", score["critical_unknown"])
        self.assertLess(score["confidence"], 0.8)

    def test_critical_mismatch_is_a_singularity(self) -> None:
        node = find_external_node(self.registry, "workers", "mrlflow-tasks")
        score = score_delta_vector(self.registry, node["delta_states"])
        self.assertEqual(score["decision"], "HOLD_SINGULARITY")
        self.assertIn("delta_runtime", score["critical_mismatch"])
        self.assertIn("delta_deploy_policy", score["critical_mismatch"])

    def test_similar_store_names_are_not_equated(self) -> None:
        node = find_external_node(self.registry, "workers", "mrl-store")
        self.assertEqual(node["link_state"], "unverified_name_similarity_only")
        self.assertEqual(node["delta_states"]["delta_identity"], "UNKNOWN")
        self.assertIn("MUST NOT", node["identity_guard"])

    def test_forward_hold_preserves_both_identities(self) -> None:
        result = translate_forward(
            self.registry,
            {
                "provider_kind": "workers",
                "external_project": "mrlflow-tasks",
                "source_sha": SHA,
            },
        )
        self.assertEqual(result["action"], "HOLD")
        trace = result["trace_envelope"]
        self.assertEqual(trace["canonical_identity"], "mrlflow-tasks")
        self.assertEqual(trace["external_project"], "mrlflow-tasks")
        self.assertEqual(trace["source_sha"], SHA)

    def test_reverse_translation_is_append_only_and_redacts_secrets(self) -> None:
        event = {
            "provider_kind": "workers",
            "external_project": "flow-tasks",
            "source_sha": SHA,
            "build_id": "build-123",
            "result": "DEPLOYMENT_FAILED",
            "observed_at": "2026-08-11T08:20:49Z",
            "parameter_snapshot": {
                "root": "flowos",
                "GITHUB_TOKEN": "must-not-survive",
                "nested": {"master_key": "must-not-survive"},
            },
        }
        first = translate_reverse(self.registry, event)
        second = translate_reverse(self.registry, event)
        self.assertTrue(first["append_only"])
        self.assertEqual(first["event_id"], second["event_id"])
        self.assertEqual(first["parameter_snapshot"]["GITHUB_TOKEN"], "[REDACTED]")
        self.assertEqual(first["parameter_snapshot"]["nested"]["master_key"], "[REDACTED]")
        self.assertEqual(first["source_sha"], SHA)
        self.assertEqual(first["mapping_version"], self.registry["mapping_version"])

    def test_encoding_formula_is_chunk_invariant_for_unicode_and_large_input(self) -> None:
        value = ("MrLiouWord／粒子轉譯／怎麼過去，就怎麼回來\n" * 5000) + "終"
        result = verify_encoding_invariant(value, [1, 2, 3, 127, 1024, 32768, 65535])
        self.assertTrue(result["passed"])
        expected = utf8_to_base64_chunked(value, 1)
        self.assertEqual(expected, utf8_to_base64_chunked(value, 32768))

    def test_invalid_chunk_size_is_rejected(self) -> None:
        with self.assertRaises(TranslationError):
            utf8_to_base64_chunked("x", 0)

    def test_registry_cannot_turn_unknown_into_match(self) -> None:
        mutated = copy.deepcopy(self.registry)
        mutated["authority"]["unknown_is_match"] = True
        with self.assertRaises(TranslationError):
            validate_registry(mutated)

    def test_verified_synthetic_link_round_trips_without_renaming(self) -> None:
        registry = copy.deepcopy(self.registry)
        node = find_external_node(registry, "workers", "flow-tasks")
        node["link_state"] = "active_verified"
        node["forward_action"] = "TRANSLATE"
        node["delta_states"] = {key: "MATCH" for key in node["delta_states"]}
        forward = translate_forward(
            registry,
            {
                "provider_kind": "workers",
                "external_project": "flow-tasks",
                "source_sha": SHA,
            },
        )
        self.assertEqual(forward["action"], "TRANSLATE")
        self.assertEqual(forward["provider_request"]["external_project"], "flow-tasks")
        self.assertEqual(
            forward["trace_envelope"]["canonical_identity"],
            "flowos-neural-gate",
        )
        reverse = translate_reverse(
            registry,
            {
                "provider_kind": "workers",
                "external_project": "flow-tasks",
                "source_sha": SHA,
                "build_id": "synthetic-build",
                "result": "SUCCESS",
                "observed_at": "2026-08-12T00:00:00Z",
                "delta_vector": node["delta_states"],
            },
        )
        self.assertEqual(reverse["external_project"], "flow-tasks")
        self.assertEqual(reverse["canonical_profile"], "flowos_neural_gate")
        self.assertEqual(reverse["source_sha"], SHA)
        self.assertEqual(reverse["diagnostic_decision"], "PASS")


if __name__ == "__main__":
    unittest.main()
