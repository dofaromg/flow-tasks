#!/usr/bin/env python3
"""MRL-36 backend-neutral routing and offline replay. origin_signature: MrLiouWord."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from MRL_gate_schema_validator_v1 import (
    SchemaRejected, load_json, product_catalog, require_wire_integer,
)
from MRL_hardware_admission_v1 import digest

VERSION = '0.1-RC1-DRAFT'
INPUT_SCHEMA = 'routing-decision-input-rc1-draft'
ADAPTER_SCHEMA = 'routing-adapter-result-rc1-draft'
RECEIPT_SCHEMA = 'route-receipt-rc1-draft'
IDENTITY = {'origin_signature': 'MrLiouWord', 'canonical_authority': 'Mr.liou'}
BASIS_POINTS = 10_000
PRE_ACCEPTANCE_HEALTH = 'health_rejected_before_acceptance'


class RoutingRejected(ValueError):
    """The snapshot or receipt does not conform to the versioned routing rules."""


@dataclass(frozen=True)
class Invocation:
    """One approved target invocation supplied to its registered adapter."""

    request_id: str
    task: str
    target_id: str
    requested_model: str
    resolved_model_version: str
    runtime_version: str
    timeout_ms: int
    payload: bytes


Adapter = Callable[[Invocation], dict]
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class RegisteredAdapter:
    """A control-plane binding of a stub to a registered execution location."""

    execution_location: str
    invoke: Adapter


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def wire_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RoutingRejected('routing clock must be timezone-aware')
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def add_reason(reasons: list[str], condition: bool, reason: str) -> None:
    if condition:
        reasons.append(reason)


def validate_snapshot(snapshot: dict) -> dict[str, dict]:
    product_catalog().validate(INPUT_SCHEMA, snapshot)
    targets = {row['target_id']: row for row in snapshot['candidates']}
    if len(targets) != len(snapshot['candidates']):
        raise RoutingRejected('duplicate target_id in routing snapshot')
    classes = snapshot['policy']['ttft_classes']
    if classes['interactive_max_ms'] >= classes['standard_max_ms']:
        raise RoutingRejected('TTFT class boundaries must strictly increase')

    def check_integers(value: object, path: tuple = ()) -> None:
        if type(value) is float:
            require_wire_integer(value, path)
        elif isinstance(value, dict):
            for key, child in value.items():
                check_integers(child, (*path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_integers(child, (*path, index))

    check_integers(snapshot)
    return targets


def egress_permitted(target: dict, request: dict, policy: dict) -> bool:
    if target['execution_location'] == 'local':
        return True
    rule = request['data_handling']
    target_id = target['target_id']
    return (
        rule['egress_allowed']
        and rule['classification'] in policy['cloud_classification_allowlist']
        and target_id in rule['approved_cloud_targets']
        and target_id in policy['cloud_target_allowlist']
    )


def hardware_reasons(target: dict, request: dict) -> list[str]:
    actual = target['hardware']
    wanted = request['hardware_requirements']
    if actual is None:
        return ['HARDWARE_UNKNOWN']
    families = wanted['accelerator_families']
    abi = wanted['runtime_abi']
    matches = (
        (not families or actual['accelerator_family'] in families)
        and actual['accelerator_count'] >= wanted['min_accelerators']
        and actual['vram_mib_per_accelerator'] >= wanted['min_vram_mib_per_accelerator']
        and (actual['accelerator_count'] > 0 or wanted['min_vram_mib_per_accelerator'] == 0)
        and (abi is None or abi == actual['runtime_abi'])
    )
    return [] if matches else ['HARDWARE_MISMATCH']


def health_reasons(target: dict, budgets: dict, at: datetime) -> list[str]:
    health = target['health']
    if (health['state'] not in ('healthy', 'degraded')
            or health['observed_at'] is None or health['score_bps'] is None):
        return ['HEALTH_UNAVAILABLE']
    observed = timestamp(health['observed_at'])
    reasons = []
    add_reason(reasons, health['score_bps'] < budgets['min_health_bps'], 'HEALTH_TOO_LOW')
    add_reason(
        reasons, not timedelta(0) <= at - observed <= timedelta(milliseconds=budgets['max_health_age_ms']),
        'HEALTH_STALE',
    )
    return reasons


def price_reasons(target: dict, budgets: dict, at: datetime, reserved: int) -> list[str]:
    price = target['pricing']
    if price is None:
        return ['PRICE_UNKNOWN']
    effective = timestamp(price['effective_at'])
    expires = timestamp(price['expires_at'])
    reasons = []
    add_reason(reasons, price['currency'] != budgets['currency'], 'PRICE_CURRENCY_MISMATCH')
    if expires <= effective:
        reasons.append('PRICE_INVALID_WINDOW')
    elif at < effective:
        reasons.append('PRICE_NOT_YET_EFFECTIVE')
    elif at >= expires:
        reasons.append('PRICE_EXPIRED')
    add_reason(reasons, reserved + price['estimated_cost_micros'] > budgets['max_total_cost_micros'],
               'COST_BUDGET_EXCEEDED')
    return reasons


def candidate_reasons(target: dict, snapshot: dict, at: datetime, elapsed: timedelta,
                      attempted: set[str], reserved: int) -> list[str]:
    request, policy = snapshot['request'], snapshot['policy']
    target_id = target['target_id']
    budgets = request['budgets']
    if target_id in attempted:
        return ['ALREADY_ATTEMPTED']
    reasons = []
    add_reason(reasons, target_id not in policy['target_weights'], 'TARGET_NOT_IN_POLICY')
    add_reason(reasons, not egress_permitted(target, request, policy), 'EGRESS_DENIED')
    model = target['model_artifact']
    add_reason(reasons, request['requested_model'] != model['model_id'], 'MODEL_MISMATCH')
    wanted_model = request['required_model_revision']
    add_reason(reasons, wanted_model is not None and wanted_model != model['revision'],
               'MODEL_REVISION_MISMATCH')
    wanted_runtime = request['required_runtime_revision']
    add_reason(reasons, wanted_runtime is not None and wanted_runtime != target['runtime_snapshot']['version'],
               'RUNTIME_REVISION_MISMATCH')
    add_reason(reasons, request['workload_class'] not in target['workload_classes'], 'WORKLOAD_MISMATCH')
    add_reason(reasons, not set(request['required_capabilities']).issubset(target['capabilities']),
               'CAPABILITY_MISMATCH')
    reasons.extend(hardware_reasons(target, request))
    reasons.extend(health_reasons(target, budgets, at))
    reasons.extend(price_reasons(target, budgets, at, reserved))
    ttft, latency = target['estimated_ttft_ms'], target['estimated_latency_ms']
    if ttft is None or latency is None or ttft > latency:
        reasons.append('LATENCY_UNKNOWN')
    else:
        add_reason(reasons, ttft > budgets['max_ttft_ms'], 'TTFT_BUDGET_EXCEEDED')
        add_reason(reasons, elapsed + timedelta(milliseconds=latency) >
                   timedelta(milliseconds=budgets['max_total_latency_ms']), 'LATENCY_BUDGET_EXCEEDED')
    return reasons


def normalized_weights(weights: dict[str, int]) -> dict[str, int]:
    total = sum(weights.values())
    if not total:
        return {}
    quotients = {key: divmod(BASIS_POINTS * weight, total) for key, weight in weights.items()}
    probabilities = {key: value[0] for key, value in quotients.items()}
    missing = BASIS_POINTS - sum(probabilities.values())
    for key in sorted(weights, key=lambda key: (-quotients[key][1], key))[:missing]:
        probabilities[key] += 1
    return probabilities


def select_round(snapshot: dict, targets: dict[str, dict], when: str,
                 elapsed: timedelta, attempted: set[str], reserved: int) -> dict:
    at = timestamp(when)
    checks = {
        key: candidate_reasons(targets[key], snapshot, at, elapsed, attempted, reserved)
        for key in sorted(targets)
    }
    eligible = [key for key, reasons in checks.items() if not reasons]
    local = [key for key in eligible if targets[key]['execution_location'] == 'local']
    pool = local or eligible
    policy = snapshot['policy']
    probabilities = dict.fromkeys(checks, 0)
    probabilities.update(normalized_weights({key: policy['target_weights'][key] for key in pool}))

    chosen = min(pool, key=lambda key: (-policy['target_weights'][key], key), default=None)
    if chosen is None:
        outcome = 'no_route'
    elif probabilities[chosen] < policy['abstain_below_bps']:
        chosen, outcome = None, 'abstained'
    else:
        outcome = 'selected'
    return {
        'evaluated_at': when, 'outcome': outcome, 'selected_target': chosen,
        'route_probabilities': probabilities, 'candidate_checks': checks,
    }


def preflight_health_skips(initial: dict, targets: dict[str, dict], weights: dict) -> list[str]:
    chosen = initial['selected_target']
    if chosen is None:
        return []
    picked = targets[chosen]
    health_checks = {'HEALTH_UNAVAILABLE', 'HEALTH_TOO_LOW', 'HEALTH_STALE'}
    picked_rank = (picked['execution_location'] != 'local', -weights[chosen], chosen)
    return [
        key for key, reasons in initial['candidate_checks'].items()
        if reasons and set(reasons).issubset(health_checks)
        and (targets[key]['execution_location'] != 'local', -weights[key], key) < picked_rank
    ]


def ttft_class(target: dict, policy: dict) -> str:
    metric = target['estimated_ttft_ms']
    classes = policy['ttft_classes']
    if metric <= classes['interactive_max_ms']:
        return 'interactive'
    if metric <= classes['standard_max_ms']:
        return 'standard'
    return 'batch'


def replay_hash(receipt: dict) -> str:
    """Compute the RC1 draft receipt digest while omitting its own digest field."""
    integrity = {key: value for key, value in receipt['integrity'].items() if key != 'receipt_digest'}
    return digest({**receipt, 'integrity': integrity})


def build_receipt(snapshot: dict, targets: dict[str, dict], mode: str,
                  rounds: list[dict], attempts: list[dict], outcome: str,
                  reason: str, target: dict | None) -> dict:
    request, policy = snapshot['request'], snapshot['policy']
    health_rejected = [
        item['target_id'] for item in attempts if item['result']['status'] == PRE_ACCEPTANCE_HEALTH
    ]
    skipped = preflight_health_skips(rounds[0], targets, policy['target_weights'])
    used = len(attempts) > 1 or (bool(attempts) and bool(skipped))
    reasons = [reason]
    if health_rejected and len(rounds) > 1:
        reasons.append('HEALTH_FALLBACK_RETRY')

    versioned_input_digest = digest(snapshot)
    input_key = {
        'version': VERSION, 'mode': mode, 'snapshot': versioned_input_digest,
        'created_at': rounds[0]['evaluated_at'],
    }
    receipt = {
        'receipt_version': VERSION, **IDENTITY,
        'receipt_id': 'mrl36-' + digest(input_key).split(':', 1)[1],
        'request_id': request['request_id'], 'trace_id': request['trace_id'],
        'sequence': snapshot['sequence'], 'created_at': rounds[0]['evaluated_at'],
        'mode': mode, 'outcome': outcome,
        'policy_id': policy['policy_id'], 'policy_version': policy['policy_version'],
        'decision_model': policy['decision_model'], 'requested_model': request['requested_model'],
        'resolved_target': target['target_id'] if target else None,
        'resolved_model_version': target['model_artifact']['revision'] if target else None,
        'execution_location': target['execution_location'] if outcome == 'routed' else None,
        'route_probabilities': rounds[-1]['route_probabilities'], 'route_reason': reasons,
        'health_fallback': {
            'used': used, 'preflight_skipped_targets': skipped, 'health_rejected_targets': health_rejected,
        },
        'ttft_class': ttft_class(target, policy) if target else None,
        'pricing': target['pricing'] if target else None,
        'replay_input': snapshot, 'decision_rounds': rounds, 'attempts': attempts,
        'integrity': {
            'input_digest': request['input_digest'],
            'output_digest': attempts[-1]['result']['output_digest'] if outcome == 'routed' else None,
            'replay_input_digest': versioned_input_digest,
            'previous_receipt_digest': snapshot['previous_receipt_digest'],
        },
    }
    receipt['integrity']['receipt_digest'] = replay_hash(receipt)
    return receipt


def run_decisions(snapshot: dict, targets: dict[str, dict], mode: str, clock: Callable[[], str],
                  invoke: Callable[[dict, int], dict] | None = None) -> dict:
    attempts, rounds = [], []
    attempted = set()
    request = snapshot['request']
    limit = request['budgets']['max_attempts']
    total_ms = request['budgets']['max_total_latency_ms']
    reserved = 0
    first = previous = None
    terminal = None

    for _ in range(limit):
        when = clock()
        now = timestamp(when)
        if previous is not None and now < previous:
            raise RoutingRejected('routing clock moved backward')
        first = first or now
        previous = now
        elapsed = now - first
        decision = select_round(snapshot, targets, when, elapsed, attempted, reserved)
        rounds.append(decision)
        selected = decision['selected_target']
        if selected is None:
            terminal = (
                (None, 'abstained', 'BELOW_CONFIDENCE_THRESHOLD')
                if decision['outcome'] == 'abstained' else (None, 'no_route', 'NO_ELIGIBLE_TARGET')
            )
            break
        target = targets[selected]
        if mode == 'shadow':
            terminal = (target, 'shadow_selected', 'SHADOW_ONLY')
            break

        timeout_ms = (timedelta(milliseconds=total_ms) - elapsed) // timedelta(milliseconds=1)
        assert invoke is not None
        result = invoke(target, timeout_ms)
        attempts.append({
            'target_id': selected, 'execution_location': target['execution_location'], 'result': result,
        })
        status = result['status']
        if status == 'succeeded':
            terminal = (target, 'routed', 'POLICY_SELECTED')
            break
        if status != PRE_ACCEPTANCE_HEALTH:
            terminal = (None, 'execution_failed', 'ADAPTER_FAILED')
            break
        attempted.add(selected)
        reserved += target['pricing']['estimated_cost_micros']

    target, outcome, reason = terminal or (None, 'execution_failed', 'ATTEMPT_LIMIT_REACHED')
    receipt = build_receipt(snapshot, targets, mode, rounds, attempts, outcome, reason, target)
    product_catalog().validate(RECEIPT_SCHEMA, receipt)
    return receipt


class StubRouter:
    """Dispatch only to registered local/cloud stubs under one control-plane policy."""

    def __init__(self, policy: dict, adapters: Mapping[str, RegisteredAdapter]):
        self._policy_digest = digest(policy)
        self._adapters = dict(adapters)

    def route_live(self, snapshot: dict, payload: bytes, *, clock: Clock = utc_now) -> dict:
        """Route immutable synthetic bytes using a trusted decision-input snapshot."""
        snapshot = deepcopy(snapshot)
        targets = validate_snapshot(snapshot)
        if self._policy_digest != digest(snapshot['policy']):
            raise RoutingRejected('snapshot does not match the control-plane policy')
        if type(payload) is not bytes:
            raise RoutingRejected('payload must be immutable bytes')
        expected = 'sha256:' + hashlib.sha256(payload).hexdigest()
        request = snapshot['request']
        if request['input_digest'] != expected:
            raise RoutingRejected('payload digest does not match the request')
        for target_id in targets.keys() & self._adapters.keys():
            if targets[target_id]['execution_location'] != self._adapters[target_id].execution_location:
                raise RoutingRejected('candidate execution location does not match adapter registration')

        def invoke(target: dict, timeout_ms: int) -> dict:
            adapter = self._adapters.get(target['target_id'])
            if adapter is None:
                return {'status': 'adapter_unavailable', 'output_digest': None}
            if adapter.execution_location == 'cloud' and not egress_permitted(target, request, snapshot['policy']):
                raise RoutingRejected('cloud dispatch denied by the control-plane policy')
            call = Invocation(
                request_id=request['request_id'], task=request['task'], target_id=target['target_id'],
                requested_model=request['requested_model'],
                resolved_model_version=target['model_artifact']['revision'],
                runtime_version=target['runtime_snapshot']['version'], timeout_ms=timeout_ms,
                payload=payload,
            )
            try:
                result = adapter.invoke(call)
            except Exception:
                return {'status': 'adapter_error', 'output_digest': None}
            if (type(result) is not dict
                    or any(type(key) is not str for key in result)
                    or set(result) != {'status', 'output_digest'}
                    or any(type(value) not in (str, type(None)) for value in result.values())):
                return {'status': 'invalid_adapter_result', 'output_digest': None}
            result = result.copy()
            try:
                product_catalog().validate(ADAPTER_SCHEMA, result)
            except (SchemaRejected, TypeError, RecursionError):
                return {'status': 'invalid_adapter_result', 'output_digest': None}
            return result

        return run_decisions(snapshot, targets, 'live', lambda: wire_time(clock()), invoke)


def evaluate_shadow(snapshot: dict, evaluated_at: datetime) -> dict:
    """Calculate an alternative decision using metadata only."""
    when = wire_time(evaluated_at)
    snapshot = deepcopy(snapshot)
    return run_decisions(snapshot, validate_snapshot(snapshot), 'shadow', lambda: when)


def replay_receipt(receipt: dict, *, expected_digest: str | None = None) -> dict:
    """Verify the stored input and reproduce the complete receipt without adapters."""
    product_catalog().validate(RECEIPT_SCHEMA, receipt)
    fields = receipt['integrity']
    if fields['receipt_digest'] != replay_hash(receipt):
        raise RoutingRejected('receipt digest mismatch')
    if expected_digest is not None and fields['receipt_digest'] != expected_digest:
        raise RoutingRejected('receipt does not match the expected digest')
    if fields['replay_input_digest'] != digest(receipt['replay_input']):
        raise RoutingRejected('replay input digest mismatch')
    times = iter(row['evaluated_at'] for row in receipt['decision_rounds'])
    attempts = iter(receipt['attempts'])

    def next_clock() -> str:
        try:
            return next(times)
        except StopIteration as error:
            raise RoutingRejected('missing decision round') from error

    def next_attempt(target: dict, _timeout_ms: int) -> dict:
        try:
            record = next(attempts)
        except StopIteration as error:
            raise RoutingRejected('missing dispatch observation') from error
        if (record['target_id'], record['execution_location']) != (target['target_id'], target['execution_location']):
            raise RoutingRejected('dispatch observation does not match the selected target')
        return record['result']

    snapshot = receipt['replay_input']
    regenerated = run_decisions(snapshot, validate_snapshot(snapshot), receipt['mode'], next_clock, next_attempt)
    if next(times, None) is not None or next(attempts, None) is not None:
        raise RoutingRejected('unused replay observations')
    if regenerated['integrity']['receipt_digest'] != fields['receipt_digest']:
        raise RoutingRejected('receipt does not reproduce the routing decision')
    return regenerated


def verify_chain_link(receipt: dict, previous_receipt: dict | None,
                      *, expected_digest: str | None = None) -> None:
    """Verify one adjacent receipt pair or an explicitly supplied genesis."""
    replay_receipt(receipt, expected_digest=expected_digest)
    if previous_receipt is None:
        if receipt['sequence'] != 0:
            raise RoutingRejected('missing previous receipt')
        return
    replay_receipt(previous_receipt)
    if (receipt['trace_id'] != previous_receipt['trace_id']
            or receipt['mode'] != previous_receipt['mode']
            or receipt['sequence'] != previous_receipt['sequence'] + 1
            or timestamp(receipt['created_at']) < timestamp(previous_receipt['created_at'])
            or receipt['integrity']['previous_receipt_digest'] != previous_receipt['integrity']['receipt_digest']):
        raise RoutingRejected('previous receipt link mismatch')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path, help='saved MRL-36 RC1 draft receipt')
    parser.add_argument('--previous', type=Path, help='verify the supplied previous receipt link')
    parser.add_argument('--expected-digest', help='expected sha256: digest from an independent evidence source')
    args = parser.parse_args(argv)
    try:
        receipt = load_json(args.receipt)
        if args.previous:
            verify_chain_link(receipt, load_json(args.previous), expected_digest=args.expected_digest)
        else:
            replay_receipt(receipt, expected_digest=args.expected_digest)
        output = {
            'status': 'ROUTE_REPLAY_MATCH', 'receipt_id': receipt['receipt_id'],
            'outcome': receipt['outcome'], 'route_reason': receipt['route_reason'],
            'receipt_digest': receipt['integrity']['receipt_digest'],
            'chain_link_checked': bool(args.previous),
            'expected_digest_checked': args.expected_digest is not None,
        }
        code = 0
    except (ValueError, OSError, TypeError, RecursionError) as error:
        output = {'status': 'ROUTE_REPLAY_REJECTED', 'reason': str(error)}
        code = 2
    print(json.dumps(output, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
