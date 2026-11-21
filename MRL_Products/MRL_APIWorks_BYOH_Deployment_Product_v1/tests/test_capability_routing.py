"""MRL-36 local/cloud stub conformance and deterministic RC1 draft replay."""

from copy import deepcopy
from dataclasses import fields, FrozenInstanceError
from datetime import timedelta
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
FIXTURES = Path(__file__).resolve().parent / 'fixtures/mrl36'
sys.path.insert(0, str(SCRIPTS))

import MRL_capability_routing_v1 as routing
from MRL_gate_schema_validator_v1 import product_catalog, SchemaRejected


class RecordingStub:
    """An in-memory adapter with a fixed response and an invocation log."""

    def __init__(self, response: dict):
        self.response = response
        self.calls = []

    def __call__(self, invocation: routing.Invocation) -> dict:
        self.calls.append(invocation)
        return self.response


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = routing.load_json(FIXTURES / 'scenarios.json')
        cls.payload = cls.scenarios['synthetic_payload_utf8'].encode('utf-8')
        cls.at = routing.timestamp(cls.scenarios['evaluated_at'])

    def setUp(self):
        self.snapshot = deepcopy(self.scenarios['input'])
        self.ok = routing.load_json(FIXTURES / 'adapter-success.json')
        self.health = {'status': routing.PRE_ACCEPTANCE_HEALTH, 'output_digest': None}
        self.local = self.snapshot['candidates'][0]
        self.cloud = self.snapshot['candidates'][1]
        self.policy = self.snapshot['policy']
        self.egress = self.snapshot['request']['data_handling']
        self.budgets = self.snapshot['request']['budgets']

    def set_path(self, path, value):
        document = self.snapshot
        for key in path[:-1]:
            document = document[key]
        document[path[-1]] = deepcopy(value)

    def route(self, local=None, cloud=None, *, time_offsets=(0, 10, 20),
              snapshot=None, adapters=None, payload=None):
        snapshot = self.snapshot if snapshot is None else snapshot
        local = RecordingStub(self.ok) if local is None else local
        cloud = RecordingStub(self.ok) if cloud is None else cloud
        if adapters is None:
            adapters = {
                'local-primary': routing.RegisteredAdapter('local', local),
                'cloud-approved': routing.RegisteredAdapter('cloud', cloud),
            }
        controller = routing.StubRouter(snapshot['policy'], adapters)
        times = iter(self.at + timedelta(milliseconds=ms) for ms in time_offsets)
        receipt = controller.route_live(
            snapshot, self.payload if payload is None else payload, clock=lambda: next(times),
        )
        calls = local.calls if isinstance(local, RecordingStub) else []
        cloud_calls = cloud.calls if isinstance(cloud, RecordingStub) else []
        return receipt, calls, cloud_calls

    def check_scenario(self, case):
        for change in case.get('changes', []):
            self.set_path(change['path'], change['value'])
        for new_target in case.get('additional_candidates', []):
            self.snapshot['candidates'].append(deepcopy(new_target))
        if case['mode'] == 'shadow':
            receipt = routing.evaluate_shadow(self.snapshot, self.at)
            calls = []
        else:
            local = RecordingStub(case.get('local_response', self.ok))
            cloud = RecordingStub(case.get('cloud_response', self.ok))
            receipt, local_calls, cloud_calls = self.route(
                local, cloud, time_offsets=case.get('time_offsets_ms', (0, 10, 20)),
            )
            calls = [call.target_id for call in (*local_calls, *cloud_calls)]
            self.assertEqual([attempt['target_id'] for attempt in receipt['attempts']], calls)
        self.assertEqual(calls, case['expected_calls'])
        for key, value in case['expected'].items():
            self.assertEqual(receipt[key], value, key)
        for target_id, reason in case.get('last_round_checks', {}).items():
            self.assertIn(reason, receipt['decision_rounds'][-1]['candidate_checks'][target_id])
        frozen = routing.load_json(FIXTURES / 'receipts' / case['receipt'])
        self.assertEqual(receipt, frozen)
        self.assertEqual(routing.replay_receipt(frozen), frozen)

    def test_registered_shadow_never_calls_adapters_or_changes_live(self):
        before, before_local, before_cloud = self.route()
        shadow = deepcopy(self.snapshot)
        shadow['candidates'] = [deepcopy(self.cloud)]
        with patch.object(routing.StubRouter, 'route_live', side_effect=AssertionError('shadow dispatched')):
            result = routing.evaluate_shadow(shadow, self.at)
        after, after_local, after_cloud = self.route()
        self.assertEqual(result['resolved_target'], 'cloud-approved')
        self.assertIsNone(result['execution_location'])
        self.assertEqual(result['attempts'], [])
        self.assertEqual(before, after)
        self.assertEqual(before_local, after_local)
        self.assertEqual(before_cloud, after_cloud)
        self.assertEqual(before_local[0].payload, self.payload)
        self.assertIsInstance(before_local[0].timeout_ms, int)

    def test_adapter_receives_one_target_and_immutable_input(self):
        observed = []

        def adapter(invocation):
            self.assertEqual({field.name for field in fields(invocation)}, {
                'request_id', 'task', 'target_id', 'requested_model',
                'resolved_model_version', 'runtime_version', 'timeout_ms', 'payload',
            })
            with self.assertRaises(FrozenInstanceError):
                invocation.target_id = 'cloud-approved'
            observed.append(invocation.target_id)
            return self.ok

        receipt, _, cloud_calls = self.route(local=adapter)
        self.assertEqual(receipt['outcome'], 'routed')
        self.assertEqual(observed, ['local-primary'])
        self.assertEqual(cloud_calls, [])

    def test_adapter_attempt_to_write_policy_or_choose_target_stops_dispatch(self):
        for field, value in (
            ('policy', self.policy), ('next_target', 'cloud-approved'),
            ('approved_cloud_targets', ['cloud-approved']), ('egress_allowed', True),
            ('route_probabilities', {'cloud-approved': 10000}),
        ):
            with self.subTest(field=field):
                response = {**self.health, field: value}
                receipt, local, cloud = self.route(local=RecordingStub(response))
                self.assertEqual(len(local), 1)
                self.assertEqual(cloud, [])
                self.assertEqual(receipt['outcome'], 'execution_failed')
                self.assertEqual(receipt['attempts'][0]['result']['status'], 'invalid_adapter_result')
                self.assertEqual(routing.replay_receipt(receipt), receipt)
        clean, _, cloud = self.route()
        self.assertEqual(clean['resolved_target'], 'local-primary')
        self.assertFalse(cloud)

    def test_untrusted_local_label_cannot_rebind_cloud_stub(self):
        self.cloud['execution_location'] = 'local'
        self.egress['egress_allowed'] = False
        calls = RecordingStub(self.ok)
        with self.assertRaisesRegex(routing.RoutingRejected, 'execution location'):
            self.route(cloud=calls)
        self.assertFalse(calls.calls)

    def test_adapter_result_does_not_accept_object_hooks(self):
        class AdapterObject(dict):
            def __deepcopy__(self, memo):
                raise AssertionError('adapter object hook ran')

        receipt, local, cloud = self.route(local=RecordingStub(AdapterObject(self.health)))
        self.assertEqual(receipt['attempts'][0]['result']['status'], 'invalid_adapter_result')
        self.assertEqual(len(local), 1)
        self.assertFalse(cloud)

    def test_live_policy_dispatch_rejects_a_different_policy_snapshot(self):
        stub = RecordingStub(self.ok)
        controller = routing.StubRouter(
            self.policy, {'local-primary': routing.RegisteredAdapter('local', stub)},
        )
        self.policy['abstain_below_bps'] = 9999
        with self.assertRaisesRegex(routing.RoutingRejected, 'control-plane policy'):
            controller.route_live(self.snapshot, self.payload, clock=lambda: self.at)
        self.assertFalse(stub.calls)

    def test_payload_digest_mismatch_stops_dispatch(self):
        stub = RecordingStub(self.ok)
        with self.assertRaisesRegex(routing.RoutingRejected, 'payload digest'):
            self.route(local=stub, payload=b'other synthetic bytes')
        self.assertFalse(stub.calls)

    def test_no_fallback_when_adapter_commitment_unknown_or_terminal(self):
        for status in ('failed', 'commit_unknown'):
            with self.subTest(status=status):
                receipt, local, cloud = self.route(
                    local=RecordingStub({'status': status, 'output_digest': None}),
                )
                self.assertEqual(receipt['outcome'], 'execution_failed')
                self.assertEqual(receipt['attempts'][0]['result']['status'], status)
                self.assertEqual(len(local), 1)
                self.assertFalse(cloud)
                self.assertEqual(len(receipt['decision_rounds']), 1)

    def test_adapter_error_is_terminal_and_sanitized(self):
        def unavailable(invocation):
            raise RuntimeError('private test message')

        receipt, _, cloud = self.route(local=unavailable)
        self.assertEqual(receipt['attempts'][0]['result']['status'], 'adapter_error')
        self.assertFalse(cloud)
        self.assertNotIn('private test message', json.dumps(receipt))

    def test_missing_adapter_does_not_trigger_fallback(self):
        cloud = RecordingStub(self.ok)
        receipt, _, calls = self.route(
            cloud=cloud, adapters={'cloud-approved': routing.RegisteredAdapter('cloud', cloud)},
        )
        self.assertFalse(calls)
        self.assertEqual(receipt['outcome'], 'execution_failed')
        self.assertEqual(receipt['attempts'][0]['result']['status'], 'adapter_unavailable')

    def test_fallback_to_another_local_target_with_egress_denied(self):
        backup = deepcopy(self.local)
        backup['target_id'] = 'local-backup'
        self.snapshot['candidates'].append(backup)
        self.policy['target_weights']['local-backup'] = 100
        self.egress['egress_allowed'] = False
        primary = RecordingStub(self.health)
        secondary = RecordingStub(self.ok)
        cloud = RecordingStub(self.ok)
        adapters = {
            'local-primary': routing.RegisteredAdapter('local', primary),
            'local-backup': routing.RegisteredAdapter('local', secondary),
            'cloud-approved': routing.RegisteredAdapter('cloud', cloud),
        }
        receipt, _, _ = self.route(local=primary, cloud=cloud, adapters=adapters)
        self.assertEqual(receipt['resolved_target'], 'local-backup')
        self.assertEqual(receipt['execution_location'], 'local')
        self.assertEqual([row['target_id'] for row in receipt['attempts']], ['local-primary', 'local-backup'])
        self.assertEqual(len(secondary.calls), 1)
        self.assertFalse(cloud.calls)

    def test_fallback_budget_counts_elapsed_time_and_prior_price(self):
        for constraint, amount, reason in (
            ('max_total_latency_ms', 800, 'LATENCY_BUDGET_EXCEEDED'),
            ('max_total_cost_micros', 250, 'COST_BUDGET_EXCEEDED'),
        ):
            with self.subTest(constraint=constraint):
                budgets = deepcopy(self.budgets)
                self.budgets[constraint] = amount
                receipt, _, cloud = self.route(local=RecordingStub(self.health), time_offsets=(0, 100))
                self.assertFalse(cloud)
                checks = receipt['decision_rounds'][-1]['candidate_checks']
                self.assertIn(reason, checks['cloud-approved'])
                self.budgets.update(budgets)

    def test_attempt_limit_exhaustion_does_not_report_empty_candidates(self):
        self.budgets['max_attempts'] = 1
        receipt, local, cloud = self.route(local=RecordingStub(self.health))
        self.assertEqual(receipt['outcome'], 'execution_failed')
        self.assertEqual(receipt['route_reason'], ['ATTEMPT_LIMIT_REACHED'])
        self.assertEqual(receipt['health_fallback']['health_rejected_targets'], ['local-primary'])
        self.assertEqual(len(local), 1)
        self.assertFalse(cloud)
        self.assertEqual(routing.replay_receipt(receipt), receipt)

    def test_fallback_abstention_does_not_dispatch_the_cloud(self):
        self.policy['abstain_below_bps'] = 6000
        self.policy['target_weights']['cloud-approved'] = 2000
        self.policy['target_weights']['cloud-second'] = 2000
        self.policy['cloud_target_allowlist'].append('cloud-second')
        self.egress['approved_cloud_targets'].append('cloud-second')
        other = deepcopy(self.cloud)
        other['target_id'] = 'cloud-second'
        self.snapshot['candidates'].append(other)
        receipt, _, cloud = self.route(local=RecordingStub(self.health))
        self.assertFalse(cloud)
        self.assertEqual(receipt['outcome'], 'abstained')
        self.assertEqual(receipt['route_probabilities'], {
            'cloud-approved': 5000, 'cloud-second': 5000, 'local-primary': 0,
        })

    def test_policy_probabilities_use_integer_rounding_and_stable_ties(self):
        self.policy['target_weights'] = {'local-primary': 1, 'local-a': 1, 'local-b': 1}
        self.policy['abstain_below_bps'] = 3000
        self.snapshot['candidates'] = [
            {**deepcopy(self.local), 'target_id': name} for name in ('local-primary', 'local-b', 'local-a')
        ]
        shadow = routing.evaluate_shadow(self.snapshot, self.at)
        self.assertEqual(shadow['route_probabilities'], {'local-a': 3334, 'local-b': 3333, 'local-primary': 3333})
        self.assertEqual(shadow['resolved_target'], 'local-a')
        self.snapshot['candidates'].reverse()
        reverse = routing.evaluate_shadow(self.snapshot, self.at)
        self.assertEqual(reverse['route_probabilities'], shadow['route_probabilities'])
        self.assertEqual(reverse['resolved_target'], shadow['resolved_target'])

    def test_duplicate_target_and_invalid_ttft_boundaries_are_rejected(self):
        duplicate = deepcopy(self.local)
        duplicate['estimated_ttft_ms'] += 1
        self.snapshot['candidates'].append(duplicate)
        with self.assertRaisesRegex(routing.RoutingRejected, 'duplicate target_id'):
            self.route()
        self.snapshot['candidates'].pop()
        classes = self.policy['ttft_classes']
        classes['interactive_max_ms'] = classes['standard_max_ms']
        with self.assertRaisesRegex(routing.RoutingRejected, 'boundaries'):
            self.route()

    def test_invalid_clocks_and_non_integer_wire_values_fail_closed(self):
        with self.assertRaisesRegex(routing.RoutingRejected, 'clock moved backward'):
            self.route(local=RecordingStub(self.health), time_offsets=(0, -1))
        with self.assertRaisesRegex(routing.RoutingRejected, 'timezone-aware'):
            routing.evaluate_shadow(self.snapshot, self.at.replace(tzinfo=None))
        self.policy['abstain_below_bps'] = 100.0
        with self.assertRaisesRegex(SchemaRejected, 'expected JSON integer'):
            self.route()

    def test_hardware_model_runtime_workload_and_capability_filter(self):
        self.egress['egress_allowed'] = False
        for field, value, expected in (
            ('hardware', None, 'HARDWARE_UNKNOWN'),
            ('hardware', {**self.local['hardware'], 'runtime_abi': 'cuda-13'}, 'HARDWARE_MISMATCH'),
            ('hardware', {**self.local['hardware'], 'vram_mib_per_accelerator': 4096}, 'HARDWARE_MISMATCH'),
            ('model_artifact', {**self.local['model_artifact'], 'model_id': 'unrequested'}, 'MODEL_MISMATCH'),
            ('model_artifact', {**self.local['model_artifact'], 'revision': 'other'}, 'MODEL_REVISION_MISMATCH'),
            ('runtime_snapshot', {**self.local['runtime_snapshot'], 'version': 'other'}, 'RUNTIME_REVISION_MISMATCH'),
            ('workload_classes', ['audio'], 'WORKLOAD_MISMATCH'),
            ('capabilities', [], 'CAPABILITY_MISMATCH'),
        ):
            with self.subTest(reason=expected, field=field):
                previous = self.local[field]
                self.local[field] = value
                receipt, local, cloud = self.route()
                self.assertFalse(local)
                self.assertFalse(cloud)
                self.assertEqual(receipt['outcome'], 'no_route')
                self.assertIn(expected, receipt['decision_rounds'][0]['candidate_checks']['local-primary'])
                self.local[field] = previous

    def test_price_and_health_unknown_or_stale_never_dispatch(self):
        self.egress['egress_allowed'] = False
        self.local['estimated_latency_ms'] = 600
        for field, value, expected in (
            ('pricing', None, 'PRICE_UNKNOWN'),
            ('pricing', {**self.local['pricing'], 'currency': 'USD'}, 'PRICE_CURRENCY_MISMATCH'),
            ('pricing', {**self.local['pricing'], 'expires_at': self.local['pricing']['effective_at']},
             'PRICE_INVALID_WINDOW'),
            ('pricing', {**self.local['pricing'], 'effective_at': '2026-11-14T04:00:01Z'},
             'PRICE_NOT_YET_EFFECTIVE'),
            ('health', {**self.local['health'], 'observed_at': '2026-11-14T04:00:01Z'}, 'HEALTH_STALE'),
            ('health', {**self.local['health'], 'score_bps': 10}, 'HEALTH_TOO_LOW'),
            ('estimated_ttft_ms', None, 'LATENCY_UNKNOWN'),
            ('estimated_ttft_ms', 510, 'TTFT_BUDGET_EXCEEDED'),
        ):
            with self.subTest(reason=expected):
                previous = self.local[field]
                self.local[field] = value
                receipt, local, cloud = self.route()
                self.assertFalse(local or cloud)
                self.assertIn(expected, receipt['decision_rounds'][0]['candidate_checks']['local-primary'])
                self.local[field] = previous

    def test_ttft_classes_at_exact_boundaries(self):
        self.local['estimated_latency_ms'] = 700
        for metric, expected in ((150, 'interactive'), (151, 'standard'),
                                 (350, 'standard'), (351, 'batch')):
            with self.subTest(metric=metric):
                self.local['estimated_ttft_ms'] = metric
                receipt, _, cloud = self.route()
                self.assertEqual(receipt['ttft_class'], expected)
                self.assertFalse(cloud)

    def test_cloud_requires_both_allowlists_and_matching_data_class(self):
        for owner_targets, request_targets, classification in (
            ([], ['cloud-approved'], 'internal'),
            (['cloud-approved'], [], 'internal'),
            (['cloud-approved'], ['cloud-approved'], 'restricted'),
        ):
            with self.subTest(classification=classification, allowlist=owner_targets):
                self.policy['cloud_target_allowlist'] = owner_targets
                self.egress.update(approved_cloud_targets=request_targets, classification=classification)
                receipt, _, cloud = self.route(local=RecordingStub(self.health))
                self.assertFalse(cloud)
                self.assertEqual(receipt['outcome'], 'no_route')
                self.assertIn('EGRESS_DENIED', receipt['decision_rounds'][-1]['candidate_checks']['cloud-approved'])

    def test_tamper_even_with_recomputed_hash_does_not_replay(self):
        receipt, _, _ = self.route(local=RecordingStub(self.health))
        altered = deepcopy(receipt)
        altered['route_probabilities']['cloud-approved'] = 9000
        with self.assertRaisesRegex(routing.RoutingRejected, 'digest mismatch'):
            routing.replay_receipt(altered)
        altered['integrity']['receipt_digest'] = routing.replay_hash(altered)
        with self.assertRaisesRegex(routing.RoutingRejected, 'does not reproduce'):
            routing.replay_receipt(altered)

    def test_independent_expected_digest_binds_replay_to_the_received_receipt(self):
        first, _, _ = self.route()
        self.policy['policy_version'] = 'fixture-other-policy'
        different, _, _ = self.route()
        expected = first['integrity']['receipt_digest']
        self.assertEqual(routing.replay_receipt(first, expected_digest=expected), first)
        self.assertEqual(routing.replay_receipt(different), different)
        with self.assertRaisesRegex(routing.RoutingRejected, 'expected digest'):
            routing.replay_receipt(different, expected_digest=expected)

    def test_replay_rechecks_egress_against_recorded_attempts(self):
        receipt, _, _ = self.route(local=RecordingStub(self.health))
        receipt['replay_input']['request']['data_handling']['egress_allowed'] = False
        receipt['integrity']['replay_input_digest'] = routing.digest(receipt['replay_input'])
        receipt['integrity']['receipt_digest'] = routing.replay_hash(receipt)
        with self.assertRaisesRegex(routing.RoutingRejected, 'unused replay observations'):
            routing.replay_receipt(receipt)

    def test_replay_rejects_wrong_attempt_identity_and_extra_round(self):
        receipt, _, _ = self.route()
        receipt['attempts'][0]['target_id'] = 'cloud-approved'
        receipt['integrity']['receipt_digest'] = routing.replay_hash(receipt)
        with self.assertRaisesRegex(routing.RoutingRejected, 'dispatch observation'):
            routing.replay_receipt(receipt)
        receipt, _, _ = self.route()
        receipt['decision_rounds'].append(deepcopy(receipt['decision_rounds'][0]))
        receipt['integrity']['receipt_digest'] = routing.replay_hash(receipt)
        with self.assertRaisesRegex(routing.RoutingRejected, 'unused replay observations'):
            routing.replay_receipt(receipt)

    def test_genesis_and_adjacent_chain_link(self):
        parent = routing.load_json(FIXTURES / 'receipts/live-local.json')
        child = routing.load_json(FIXTURES / 'receipts/live-ledger-child.json')
        routing.verify_chain_link(parent, None)
        routing.verify_chain_link(child, parent)
        with self.assertRaisesRegex(routing.RoutingRejected, 'missing previous receipt'):
            routing.verify_chain_link(child, None)
        other = routing.load_json(FIXTURES / 'receipts/live-cloud.json')
        with self.assertRaisesRegex(routing.RoutingRejected, 'previous receipt link mismatch'):
            routing.verify_chain_link(child, other)

    def test_legacy_and_additive_receipts_select_their_own_schema(self):
        v0 = routing.load_json(FIXTURES.parent / 'mrl45/route-receipt.json')
        v1 = routing.load_json(FIXTURES / 'receipts/live-local.json')
        catalog = product_catalog()
        catalog.validate('route-receipt', v0)
        catalog.validate(routing.RECEIPT_SCHEMA, v1)
        with self.assertRaises(SchemaRejected):
            catalog.validate('route-receipt', v1)
        with self.assertRaises(SchemaRejected):
            catalog.validate(routing.RECEIPT_SCHEMA, v0)

    def test_shadow_receipt_schema_rejects_dispatch(self):
        receipt = routing.load_json(FIXTURES / 'receipts/shadow-selected.json')
        receipt['attempts'] = routing.load_json(FIXTURES / 'receipts/live-local.json')['attempts']
        with self.assertRaises(SchemaRejected):
            product_catalog().validate(routing.RECEIPT_SCHEMA, receipt)

    def test_replay_cli_chain_and_strict_input(self):
        cli = SCRIPTS / 'MRL_capability_routing_v1.py'
        child = routing.load_json(FIXTURES / 'receipts/live-ledger-child.json')
        bootstrap = (
            'import pathlib, runpy, sys\n'
            'def deny_network(event, args):\n'
            '    if event.startswith("socket."):\n'
            '        raise AssertionError("route replay tried to use the network")\n'
            'sys.addaudithook(deny_network)\n'
            'script = sys.argv.pop(1)\n'
            'sys.path.insert(0, str(pathlib.Path(script).parent))\n'
            'runpy.run_path(script, run_name="__main__")\n'
        )
        result = subprocess.run([
            sys.executable, '-c', bootstrap, str(cli), str(FIXTURES / 'receipts/live-ledger-child.json'),
            '--previous', str(FIXTURES / 'receipts/live-local.json'),
            '--expected-digest', child['integrity']['receipt_digest'],
        ], capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output['status'], 'ROUTE_REPLAY_MATCH')
        self.assertTrue(output['chain_link_checked'])
        self.assertTrue(output['expected_digest_checked'])
        with tempfile.TemporaryDirectory() as temp:
            malformed = Path(temp) / 'fixture.json'
            malformed.write_text('{"mode":"shadow","mode":"live"}', encoding='utf-8')
            rejected = subprocess.run([sys.executable, str(cli), str(malformed)], capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(json.loads(rejected.stdout)['status'], 'ROUTE_REPLAY_REJECTED')


def scenario_test(case):
    def run():
        fixture = RoutingTests()
        fixture.setUpClass()
        fixture.setUp()
        fixture.check_scenario(case)
    return unittest.FunctionTestCase(run, description=f"MRL36 {case['id']}")


def load_tests(loader, tests, pattern):
    for case in routing.load_json(FIXTURES / 'scenarios.json')['cases']:
        tests.addTest(scenario_test(case))
    return tests
