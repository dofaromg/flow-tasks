#!/usr/bin/env python3
"""Bidirectional MRL/Cloudflare boundary translation without side rewriting.

The station preserves both namespaces, represents unknown evidence explicitly,
and refuses promotion when an identity, deployment policy, binding contract, or
other critical boundary parameter is unresolved.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "config" / "MRL_CLOUDFLARE_TRANSLATION_MAP_v1.json"
ALLOWED_STATES = {"MATCH", "MISMATCH", "UNKNOWN"}
ALLOWED_LINK_STATES = {
    "active_verified",
    "historical_shadow_unverified",
    "historical_failure_scope_unverified",
    "shell_not_promoted",
    "unverified_name_similarity_only",
}
NO_DEPLOY_POLICIES = {
    "gke_gitops",
    "requires_explicit_deployment",
    "local_backfill_no_deploy",
}
SENSITIVE_KEY = re.compile(
    r"(?:token|secret|password|credential|private[_-]?key|api[_-]?key|master[_-]?key)",
    re.IGNORECASE,
)


class TranslationError(RuntimeError):
    """Raised when the translation contract is invalid or unsafe."""


def load_registry(path: Path = DEFAULT_MAP) -> dict[str, Any]:
    """Load and validate the translation registry."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TranslationError(f"missing translation map: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TranslationError(f"invalid translation map JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise TranslationError("translation map root must be an object")
    validate_registry(value)
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TranslationError(message)


def _parameter_index(registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    parameters = registry.get("inconsistency_parameters")
    _require(isinstance(parameters, list) and parameters, "inconsistency parameters missing")
    result: dict[str, dict[str, Any]] = {}
    for item in parameters:
        _require(isinstance(item, dict), "inconsistency parameter must be an object")
        parameter_id = item.get("id")
        _require(isinstance(parameter_id, str) and parameter_id, "parameter id missing")
        _require(parameter_id not in result, f"duplicate parameter: {parameter_id}")
        _require(
            isinstance(item.get("weight"), int) and item["weight"] > 0,
            f"invalid weight: {parameter_id}",
        )
        _require(isinstance(item.get("critical"), bool), f"critical flag missing: {parameter_id}")
        result[parameter_id] = item
    return result


def validate_registry(registry: Mapping[str, Any]) -> dict[str, int]:
    """Validate schema, identity boundaries, vectors, formulas, and history."""

    _require(registry.get("schema_version") == "1.0.0", "unsupported schema version")
    _require(registry.get("origin_signature") == "MrLiouWord", "origin signature mismatch")
    _require(bool(registry.get("mapping_version")), "mapping version missing")
    authority = registry.get("authority")
    _require(isinstance(authority, dict), "authority contract missing")
    _require(authority.get("canonical_root") == "MRL", "canonical root mismatch")
    _require(authority.get("external_provider") == "Cloudflare", "provider mismatch")
    false_flags = (
        "destructive_side_rewrite_allowed",
        "implicit_name_equivalence_allowed",
        "unknown_is_match",
        "history_rewrite_allowed",
    )
    _require(all(authority.get(flag) is False for flag in false_flags), "boundary safety weakened")

    tri_state = registry.get("tri_state")
    _require(
        tri_state == {"MATCH": 0, "MISMATCH": 1, "UNKNOWN": None},
        "tri-state contract changed",
    )
    parameters = _parameter_index(registry)

    thresholds = registry.get("thresholds")
    _require(isinstance(thresholds, dict), "thresholds missing")
    minimum_confidence = thresholds.get("minimum_confidence")
    singularity_score = thresholds.get("singularity_score")
    _require(
        isinstance(minimum_confidence, (int, float)) and 0 < minimum_confidence <= 1,
        "minimum confidence invalid",
    )
    _require(
        isinstance(singularity_score, (int, float)) and 0 < singularity_score <= 1,
        "singularity score invalid",
    )

    formulas = registry.get("formulas")
    _require(isinstance(formulas, dict), "translation formulas missing")
    formula_floor = {
        "known_weight",
        "mismatch_weight",
        "total_weight",
        "singularity_score",
        "confidence",
        "forward",
        "reverse",
        "round_trip",
        "encoding",
    }
    _require(formula_floor.issubset(formulas), "translation formula coverage incomplete")

    profiles = registry.get("canonical_profiles")
    _require(isinstance(profiles, list) and profiles, "canonical profiles missing")
    profile_index: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        _require(isinstance(profile, dict), "canonical profile must be an object")
        profile_id = profile.get("id")
        _require(isinstance(profile_id, str) and profile_id, "canonical profile id missing")
        _require(profile_id not in profile_index, f"duplicate canonical profile: {profile_id}")
        _require(bool(profile.get("canonical_identity")), f"canonical identity missing: {profile_id}")
        _require(bool(profile.get("deploy_policy")), f"deploy policy missing: {profile_id}")
        profile_index[profile_id] = profile

    nodes = registry.get("external_nodes")
    _require(isinstance(nodes, list) and nodes, "external nodes missing")
    node_keys: set[tuple[str, str]] = set()
    node_ids: set[str] = set()
    for node in nodes:
        _require(isinstance(node, dict), "external node must be an object")
        node_id = node.get("node_id")
        key = (node.get("provider_kind"), node.get("external_project"))
        _require(all(isinstance(part, str) and part for part in key), "external node key missing")
        _require(isinstance(node_id, str) and node_id, "external node id missing")
        _require(key not in node_keys, f"duplicate external node key: {key}")
        _require(node_id not in node_ids, f"duplicate external node id: {node_id}")
        node_keys.add(key)
        node_ids.add(node_id)
        candidate = node.get("candidate_profile")
        _require(candidate in profile_index, f"unknown candidate profile: {candidate}")
        _require(node.get("link_state") in ALLOWED_LINK_STATES, f"invalid link state: {node_id}")
        _require(node.get("forward_action") in {"HOLD", "TRANSLATE"}, f"invalid action: {node_id}")
        if node.get("link_state") != "active_verified":
            _require(node.get("forward_action") == "HOLD", f"unverified node can deploy: {node_id}")
        if profile_index[candidate].get("deploy_policy") in NO_DEPLOY_POLICIES:
            _require(node.get("forward_action") == "HOLD", f"no-deploy profile can deploy: {node_id}")
        vector = node.get("delta_states")
        _require(isinstance(vector, dict), f"delta vector missing: {node_id}")
        _require(set(vector) == set(parameters), f"delta coverage mismatch: {node_id}")
        _require(set(vector.values()).issubset(ALLOWED_STATES), f"invalid delta state: {node_id}")
        source_sha = node.get("observed_source_sha")
        _require(
            isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None,
            f"invalid source SHA: {node_id}",
        )

    method_history = registry.get("method_change_history")
    _require(isinstance(method_history, list) and len(method_history) >= 3, "method history incomplete")
    times = [entry.get("observed_at") for entry in method_history if isinstance(entry, dict)]
    _require(len(times) == len(method_history) and times == sorted(times), "method history not ordered")
    _require(
        all(entry.get("method") == "utf8ToBase64" for entry in method_history),
        "method history identity changed",
    )

    required_return = {
        "event_id",
        "map_id",
        "mapping_version",
        "origin_signature",
        "canonical_profile",
        "provider",
        "provider_kind",
        "external_project",
        "source_sha",
        "build_id",
        "parameter_snapshot",
        "delta_vector",
        "singularity_score",
        "confidence",
        "result",
        "observed_at",
    }
    _require(
        required_return.issubset(registry.get("return_evidence_fields", [])),
        "return evidence fields incomplete",
    )
    _require(len(registry.get("invariants", [])) >= 7, "round-trip invariants incomplete")
    return {
        "parameters": len(parameters),
        "canonical_profiles": len(profile_index),
        "external_nodes": len(nodes),
        "method_changes": len(method_history),
    }


def score_delta_vector(
    registry: Mapping[str, Any], vector: Mapping[str, str]
) -> dict[str, Any]:
    """Apply weighted three-state singularity and confidence formulas."""

    parameters = _parameter_index(registry)
    _require(set(vector) == set(parameters), "delta vector does not cover all parameters")
    _require(set(vector.values()).issubset(ALLOWED_STATES), "delta vector contains invalid state")
    total_weight = sum(item["weight"] for item in parameters.values())
    known_weight = sum(
        parameters[key]["weight"] for key, state in vector.items() if state != "UNKNOWN"
    )
    mismatch_weight = sum(
        parameters[key]["weight"] for key, state in vector.items() if state == "MISMATCH"
    )
    confidence = known_weight / total_weight
    singularity = mismatch_weight / known_weight if known_weight else None
    critical_unknown = sorted(
        key
        for key, state in vector.items()
        if state == "UNKNOWN" and parameters[key]["critical"]
    )
    critical_mismatch = sorted(
        key
        for key, state in vector.items()
        if state == "MISMATCH" and parameters[key]["critical"]
    )
    thresholds = registry["thresholds"]
    if critical_mismatch:
        decision = thresholds["critical_mismatch_action"]
    elif critical_unknown or confidence < thresholds["minimum_confidence"]:
        decision = thresholds["critical_unknown_action"]
    elif singularity is not None and singularity >= thresholds["singularity_score"]:
        decision = "HOLD_SINGULARITY"
    elif mismatch_weight:
        decision = "TRANSLATE_REQUIRED"
    else:
        decision = "PASS"
    return {
        "total_weight": total_weight,
        "known_weight": known_weight,
        "mismatch_weight": mismatch_weight,
        "confidence": round(confidence, 6),
        "singularity_score": None if singularity is None else round(singularity, 6),
        "critical_unknown": critical_unknown,
        "critical_mismatch": critical_mismatch,
        "decision": decision,
    }


def find_external_node(
    registry: Mapping[str, Any], provider_kind: str, external_project: str
) -> dict[str, Any]:
    """Resolve an external node without inferring identity from similar names."""

    matches = [
        node
        for node in registry["external_nodes"]
        if node["provider_kind"] == provider_kind
        and node["external_project"] == external_project
    ]
    if len(matches) != 1:
        raise TranslationError(
            f"external node is not uniquely registered: {provider_kind}/{external_project}"
        )
    return matches[0]


def _profile(registry: Mapping[str, Any], profile_id: str) -> dict[str, Any]:
    return next(profile for profile in registry["canonical_profiles"] if profile["id"] == profile_id)


def inspect_node(
    registry: Mapping[str, Any], provider_kind: str, external_project: str
) -> dict[str, Any]:
    """Return the current boundary vector and non-mutating decision."""

    node = find_external_node(registry, provider_kind, external_project)
    profile = _profile(registry, node["candidate_profile"])
    score = score_delta_vector(registry, node["delta_states"])
    return {
        "node_id": node["node_id"],
        "provider_kind": provider_kind,
        "external_project": external_project,
        "canonical_profile": profile["id"],
        "canonical_identity": profile["canonical_identity"],
        "link_state": node["link_state"],
        "configured_forward_action": node["forward_action"],
        "effective_action": "HOLD"
        if node["forward_action"] == "HOLD" or score["decision"].startswith("HOLD")
        else "TRANSLATE",
        "delta_vector": dict(node["delta_states"]),
        "score": score,
    }


def sanitize_snapshot(value: Any) -> Any:
    """Remove secret values while retaining parameter names for evidence."""

    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if SENSITIVE_KEY.search(str(key)) else sanitize_snapshot(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_snapshot(item) for item in value]
    return value


def translate_forward(registry: Mapping[str, Any], intent: Mapping[str, Any]) -> dict[str, Any]:
    """Translate an MRL intent or return a structured HOLD without side effects."""

    provider_kind = intent.get("provider_kind")
    external_project = intent.get("external_project")
    source_sha = intent.get("source_sha")
    _require(isinstance(provider_kind, str), "provider_kind missing")
    _require(isinstance(external_project, str), "external_project missing")
    _require(
        isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None,
        "source_sha must be a full lowercase SHA",
    )
    node = find_external_node(registry, provider_kind, external_project)
    profile = _profile(registry, node["candidate_profile"])
    score = score_delta_vector(registry, node["delta_states"])
    hold_reasons: list[str] = []
    if node["link_state"] != "active_verified":
        hold_reasons.append(f"identity_link={node['link_state']}")
    if node["forward_action"] != "TRANSLATE":
        hold_reasons.append(f"forward_action={node['forward_action']}")
    if profile["deploy_policy"] in NO_DEPLOY_POLICIES:
        hold_reasons.append(f"deploy_policy={profile['deploy_policy']}")
    if score["decision"] not in {"PASS", "TRANSLATE_REQUIRED"}:
        hold_reasons.append(f"diagnostic={score['decision']}")
    envelope = {
        "map_id": registry["map_id"],
        "mapping_version": registry["mapping_version"],
        "origin_signature": registry["origin_signature"],
        "canonical_profile": profile["id"],
        "canonical_identity": profile["canonical_identity"],
        "provider": "Cloudflare",
        "provider_kind": provider_kind,
        "external_project": external_project,
        "source_sha": source_sha,
        "parameter_snapshot": sanitize_snapshot(intent.get("parameter_snapshot", {})),
        "delta_vector": dict(node["delta_states"]),
        "score": score,
    }
    if hold_reasons:
        return {"action": "HOLD", "reasons": hold_reasons, "trace_envelope": envelope}
    return {
        "action": "TRANSLATE",
        "provider_request": {
            "provider_kind": provider_kind,
            "external_project": external_project,
            "source_root": profile["source_root"],
            "entrypoint": profile["entrypoint"],
            "build_method": profile["build_method"],
            "required_bindings": profile["binding_contract"],
            "source_sha": source_sha,
        },
        "trace_envelope": envelope,
    }


def _event_id(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "mrl-cf-" + hashlib.sha256(encoded).hexdigest()


def translate_reverse(registry: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a provider callback into append-only MRL evidence."""

    provider_kind = event.get("provider_kind")
    external_project = event.get("external_project")
    source_sha = event.get("source_sha")
    _require(isinstance(provider_kind, str), "provider_kind missing")
    _require(isinstance(external_project, str), "external_project missing")
    _require(
        isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None,
        "source_sha must be a full lowercase SHA",
    )
    node = find_external_node(registry, provider_kind, external_project)
    profile = _profile(registry, node["candidate_profile"])
    vector = event.get("delta_vector", node["delta_states"])
    _require(isinstance(vector, dict), "delta_vector must be an object")
    score = score_delta_vector(registry, vector)
    core = {
        "map_id": registry["map_id"],
        "mapping_version": registry["mapping_version"],
        "origin_signature": registry["origin_signature"],
        "canonical_profile": profile["id"],
        "provider": "Cloudflare",
        "provider_kind": provider_kind,
        "external_project": external_project,
        "source_sha": source_sha,
        "build_id": event.get("build_id"),
        "parameter_snapshot": sanitize_snapshot(event.get("parameter_snapshot", {})),
        "delta_vector": dict(vector),
        "singularity_score": score["singularity_score"],
        "confidence": score["confidence"],
        "result": event.get("result", "UNKNOWN"),
        "observed_at": event.get("observed_at"),
    }
    return {
        "event_id": _event_id(core),
        **core,
        "append_only": True,
        "diagnostic_decision": score["decision"],
        "critical_unknown": score["critical_unknown"],
        "critical_mismatch": score["critical_mismatch"],
        "source_comment": event.get("source_comment", node.get("mutable_comment")),
    }


def utf8_to_base64_chunked(value: str, chunk_size: int = 0x8000) -> str:
    """Implement the encoding formula while making chunk size semantically irrelevant."""

    if chunk_size <= 0:
        raise TranslationError("chunk_size must be greater than zero")
    data = value.encode("utf-8")
    rebuilt = b"".join(data[index : index + chunk_size] for index in range(0, len(data), chunk_size))
    return base64.b64encode(rebuilt).decode("ascii")


def verify_encoding_invariant(value: str, chunk_sizes: list[int] | None = None) -> dict[str, Any]:
    """Verify that every chunk form preserves the same bytes and digest."""

    sizes = chunk_sizes or [1, 2, 3, 127, 1024, 0x8000]
    outputs = {size: utf8_to_base64_chunked(value, size) for size in sizes}
    unique = set(outputs.values())
    encoded = value.encode("utf-8")
    expected = base64.b64encode(encoded).decode("ascii")
    passed = len(unique) == 1 and next(iter(unique), expected) == expected
    return {
        "passed": passed,
        "chunk_sizes": sizes,
        "utf8_sha256": hashlib.sha256(encoded).hexdigest(),
        "base64_sha256": hashlib.sha256(expected.encode("ascii")).hexdigest(),
    }


def _read_event(path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TranslationError(f"cannot read event: {exc}") from exc
    if not isinstance(value, dict):
        raise TranslationError("event root must be an object")
    return value


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--provider-kind", required=True, choices=("pages", "workers"))
    inspect_parser.add_argument("--project", required=True)
    forward_parser = subparsers.add_parser("forward")
    forward_parser.add_argument("--event", required=True)
    reverse_parser = subparsers.add_parser("reverse")
    reverse_parser.add_argument("--event", required=True)
    encoding_parser = subparsers.add_parser("verify-encoding")
    encoding_parser.add_argument("--text", required=True)
    args = parser.parse_args()
    registry = load_registry(args.map)
    if args.command == "validate":
        _print({"status": "DELIVERY_PASS", "coverage": "100%", **validate_registry(registry)})
    elif args.command == "inspect":
        _print(inspect_node(registry, args.provider_kind, args.project))
    elif args.command == "forward":
        _print(translate_forward(registry, _read_event(args.event)))
    elif args.command == "reverse":
        _print(translate_reverse(registry, _read_event(args.event)))
    elif args.command == "verify-encoding":
        result = verify_encoding_invariant(args.text)
        _print(result)
        if not result["passed"]:
            raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except TranslationError as exc:
        print(f"MRL_CLOUDFLARE_TRANSLATION_FAIL: {exc}")
        raise SystemExit(1) from exc
