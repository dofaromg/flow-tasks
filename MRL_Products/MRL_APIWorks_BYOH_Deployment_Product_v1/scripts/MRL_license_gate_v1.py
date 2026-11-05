#!/usr/bin/env python3
"""MRL-37 executable rights gate. origin_signature: MrLiouWord.

Manifests describe claims. Only exact decisions in the canonical Owner-reviewed
License Scope Registry authorize them. No SPDX-name or trust-signature inference.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from MRL_artifact_trust_v1 import canonical, file_bytes, load_json

PRODUCT = Path(__file__).resolve().parents[1]
REGISTRY = PRODUCT.parents[1] / 'config/MRL_LICENSE_SCOPE_REGISTRY_v1.json'
SCHEMA = PRODUCT / 'licenses/MRL_license_manifest_schema_v1.json'
RESERVED = {'NOTICE', 'MRL_LICENSE_MANIFEST.json', 'MRL_LICENSE_CONTEXT.json',
            'MRL_LICENSE_RECEIPT.json', 'MRL_LICENSE_REGISTRY_SNAPSHOT.json',
            'MRL_PRODUCT_BUNDLE_MANIFEST.json'}


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate(value, schema, location='$'):
    """Validate the closed JSON Schema subset used by the shipped v1 schema."""
    types = {'object': lambda x: isinstance(x, dict), 'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str), 'boolean': lambda x: type(x) is bool,
             'integer': lambda x: type(x) is int, 'null': lambda x: x is None}
    if 'type' in schema:
        expected = schema['type'] if isinstance(schema['type'], list) else [schema['type']]
        if not any(types[t](value) for t in expected):
            raise ValueError('schema type: ' + location)
    if 'const' in schema and value != schema['const']:
        raise ValueError('schema const: ' + location)
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError('schema enum: ' + location)
    if isinstance(value, dict):
        if set(schema.get('required', [])) - set(value):
            raise ValueError('schema required: ' + location)
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError('schema extra: ' + location)
        for key in value:
            if key in props:
                validate(value[key], props[key], location + '.' + key)
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            raise ValueError('schema empty array: ' + location)
        for item in value:
            validate(item, schema['items'], location + '[]')
    if isinstance(value, str):
        if len(value.strip()) < schema.get('minLength', 0):
            raise ValueError('schema empty string: ' + location)
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            raise ValueError('schema pattern: ' + location)
    if type(value) is int and value < schema.get('minimum', value):
        raise ValueError('schema minimum: ' + location)


def safe_name(name):
    """Reject ambiguous Windows/POSIX paths before filesystem access."""
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('invalid relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('invalid relative path')
    if any(x.rstrip(' .') != x for x in path.parts):
        raise ValueError('ambiguous relative path')
    return name


def read_ref(root, ref):
    safe_name(ref['path'])
    raw = file_bytes(Path(root), ref['path'], 'sha256:' + ref['sha256'])
    if not raw or not raw.strip():
        raise ValueError('empty license/artifact document')
    return raw


def inventory(root):
    """Exact staged payload, including files hidden by a builder's source filters."""
    found = set()
    for path in Path(root).rglob('*'):
        if path.is_symlink():
            raise ValueError('symlink in licensed payload')
        if path.is_file():
            name = path.relative_to(root).as_posix()
            safe_name(name)
            found.add(name)
    return found


def notice_bytes(manifest, evidence_root):
    """Preserve the complete reviewed upstream LICENSE/NOTICE/terms bytes."""
    output = [b'MRL NOTICE v1 | origin_signature: MrLiouWord\n']
    for component in manifest['components']:
        output.append(('\n' + component['id'] + ' | ' + component['kind'] + ' | '
                       + component['license_id'] + ' | ' + component['delivery'] + '\n').encode())
        output.append(('Obligations: ' + json.dumps(component['obligations'], ensure_ascii=False)
                       + '\n').encode())
        if component['delivery'] == 'customer_provided':
            output.append(b'Customer supplies/acquires model; MRL acquisition prohibited.\n')
        for ref in component['documents']:
            output.append(('--- ' + ref['role'] + ' ' + ref['path'] + ' sha256:'
                           + ref['sha256'] + ' ---\n').encode())
            output.extend([read_ref(evidence_root, ref), b'\n'])
    return b''.join(output)


def evaluate(manifest, context, root, evidence_root, registry=None,
             required_files=None, exhaustive=False, customer_files_present=True, required_roles=None):
    """Rehash bytes and exact reviewed decisions. A receipt cannot authorize use."""
    receipt = {'schema': 'MRL_License_Receipt_v1', 'origin_signature': 'MrLiouWord',
               'allowed': False, 'legal_rights_review': 'UNRESOLVED',
               'formal_customer_delivery': 'REQUIRES_OWNER_APPROVAL',
               'decision_points': ['approve', 'reject', 'needs-counsel']}
    try:
        registry = load_json(REGISTRY) if registry is None else registry
        validate(manifest, load_json(SCHEMA))
        validate(context, {'type': 'object', 'additionalProperties': False,
                           'required': ['customer', 'region', 'mrl_annual_revenue_usd',
                                        'customer_annual_revenue_usd', 'customer_model_responsibility'],
                           'properties': {'customer': {'type': 'string', 'minLength': 1},
                                          'region': {'type': 'string', 'minLength': 1},
                                          'mrl_annual_revenue_usd': {'type': ['integer', 'null'], 'minimum': 0},
                                          'customer_annual_revenue_usd': {'type': ['integer', 'null'], 'minimum': 0},
                                          'customer_model_responsibility': {'type': 'boolean'}}})
        if registry['origin_signature'] != 'MrLiouWord' or registry['default_status'] != 'RIGHTS_UNRESOLVED':
            raise ValueError('canonical unresolved policy required')
        for key in ('whole_repository_inference_allowed', 'commercial_permission_inference_allowed',
                    'sublicensing_inference_allowed', 'third_party_delegation_inference_allowed'):
            if registry[key] is not False:
                raise ValueError('inference policy must remain false')
        receipt.update(manifest_sha256=digest(manifest), context_sha256=digest(context),
                       registry_sha256=digest(registry), reviewed_records=[])
        covered, ids, folded = set(), set(), set()
        for component in manifest['components']:
            for ref in component['files']:
                name = safe_name(ref['path'])
                if name.casefold() in folded:
                    raise ValueError('duplicate or case-colliding payload path')
                folded.add(name.casefold())
        today = datetime.now(timezone.utc).date()
        for component in manifest['components']:
            if component['id'] in ids:
                raise ValueError('duplicate component id')
            ids.add(component['id'])
            label = component['license_id'].strip().upper()
            if label in ('UNKNOWN', 'NOASSERTION', 'NONE', 'UNRESOLVED'):
                raise ValueError('unknown license')
            decisions = [r for r in registry.get('artifact_decisions', [])
                         if r.get('component_sha256') == digest(component)
                         and r.get('context_sha256') == digest(context)]
            if len(decisions) != 1:
                raise ValueError('missing or ambiguous Owner rights decision: ' + component['id'])
            decision = decisions[0]
            if (decision.get('decision') != 'approve' or decision.get('issued_by') != 'MrLiouWord'
                    or not decision.get('record_id') or not decision.get('evidence_reference')
                    or not decision.get('rollback') or decision.get('third_party_rights_verified') is not True
                    or not date.fromisoformat(decision['review_date']) <= today <= date.fromisoformat(decision['expires_on'])):
                raise ValueError('rights decision rejected, expired, or needs-counsel')
            actions = {'commercial_use'}
            if component['delivery'] == 'bundled':
                actions.add('redistribute')
            else:
                actions.add('customer_model_use')
            if (decision.get('grantee') != 'MRL' or decision.get('purpose') != 'commercial_customer_delivery'
                    or decision.get('environment') != 'BYOH'
                    or not actions <= set(decision.get('permitted_actions', []))
                    or actions & set(decision.get('prohibited_actions', []))
                    or not date.fromisoformat(decision['starts_on']) <= today):
                raise ValueError('Owner grant scope/action/time mismatch')
            # Custom/LicenseRef terms require an explicit review; names never confer rights.
            if (label.startswith('LICENSEREF-') or label == 'CUSTOM') and decision.get('custom_terms_reviewed') is not True:
                raise ValueError('custom license not reviewed')
            roles = {r['role'] for r in component['documents']}
            if 'license' not in roles or 'notice' not in roles:
                raise ValueError('LICENSE and NOTICE documents required')
            for ref in component['documents']:
                read_ref(evidence_root, ref)
            if component['commercial_use'] is not True:
                raise ValueError('commercial use prohibited')
            for field, target in (('regions', 'region'), ('customers', 'customer')):
                if '*' not in component[field] and context[target] not in component[field]:
                    raise ValueError('region/customer restriction')
            limit, applies = component['annual_revenue_limit_usd'], component['threshold_applies_to']
            if (limit is None) != (applies == 'none'):
                raise ValueError('threshold applicability unresolved')
            if limit is not None:
                for who in ('mrl', 'customer') if applies == 'both' else (applies,):
                    revenue = context[who + '_annual_revenue_usd']
                    if revenue is None or revenue >= limit:
                        raise ValueError('commercial threshold unmet or unknown')
            if component['delivery'] == 'customer_provided':
                if (component['kind'] != 'model_weights' or component['mrl_acquisition'] is not False
                        or context['customer_model_responsibility'] is not True):
                    raise ValueError('customer model responsibility/acquisition restriction')
                for ref in component['files']:
                    safe_name(ref['path'])
                    if exhaustive and (Path(root) / ref['path']).exists():
                        raise ValueError('customer-provided weights must not be bundled')
            elif component['redistribution'] is not True:
                raise ValueError('redistribution prohibited')
            for ref in component['files']:
                name = safe_name(ref['path'])
                if name.casefold() in {n.casefold() for n in RESERVED} or name.casefold().startswith('mrl_license_evidence/'):
                    raise ValueError('reserved license output path')
                if component['delivery'] == 'bundled' or (not exhaustive and customer_files_present):
                    read_ref(root, ref)
                    covered.add(name)
            receipt['reviewed_records'].append(decision['record_id'])
        for role in required_roles or []:
            matches = [c for c in manifest['components']
                       if c['kind'] == role['kind'] and c['id'] == role['id']
                       and c['version'] == role['version']
                       and role['files'] <= {r['path'] for r in c['files']}]
            if len(matches) != 1:
                raise ValueError('workload license identity/kind mismatch')
        if required_files is not None and not set(required_files) <= covered:
            raise ValueError('required artifact license coverage missing')
        if exhaustive and inventory(root) != covered:
            raise ValueError('bundle license coverage mismatch')
        receipt.update(allowed=True, legal_rights_review='MATCHED_OWNER_RECORDS',
                       notice_sha256=hashlib.sha256(notice_bytes(manifest, evidence_root)).hexdigest())
    except (ValueError, TypeError, KeyError, OSError) as error:
        receipt['reason'] = str(error)
    return receipt


def registry_snapshot(registry, receipt):
    """Export only decisions applicable to this delivery, never unrelated grants."""
    selected = set(receipt['reviewed_records'])
    return {'schema': 'MRL_License_Registry_Snapshot_v1', 'origin_signature': 'MrLiouWord',
            'canonical_registry_sha256': digest(registry),
            'artifact_decisions': [r for r in registry.get('artifact_decisions', [])
                                   if r.get('record_id') in selected]}


def package_license(stage, manifest, context, evidence_root):
    """Gate every staged byte, then export reproducible evidence and full NOTICE."""
    registry = load_json(REGISTRY)
    result = evaluate(manifest, context, stage, evidence_root, registry, exhaustive=True)
    if not result['allowed']:
        raise ValueError('license gate DENIED: ' + result.get('reason', 'unknown'))
    output = Path(stage) / 'MRL_LICENSE_EVIDENCE'
    output.mkdir()
    for component in manifest['components']:
        for ref in component['documents']:
            raw = read_ref(evidence_root, ref)
            target = output / ref['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    for name, value in [('MRL_LICENSE_MANIFEST.json', manifest), ('MRL_LICENSE_CONTEXT.json', context),
                        ('MRL_LICENSE_RECEIPT.json', result),
                        ('MRL_LICENSE_REGISTRY_SNAPSHOT.json', registry_snapshot(registry, result))]:
        (Path(stage) / name).write_bytes(canonical(value))
    (Path(stage) / 'NOTICE').write_bytes(notice_bytes(manifest, evidence_root))
    return result


def verify_packaged(stage):
    """Re-evaluate against the current canonical registry, never trust a receipt."""
    stage = Path(stage)
    manifest = load_json(stage / 'MRL_LICENSE_MANIFEST.json')
    context = load_json(stage / 'MRL_LICENSE_CONTEXT.json')
    evidence = stage / 'MRL_LICENSE_EVIDENCE'
    result = evaluate(manifest, context, stage, evidence, customer_files_present=False)
    if not result['allowed']:
        return result
    expected = set(RESERVED) - {'MRL_PRODUCT_BUNDLE_MANIFEST.json'}
    for component in manifest['components']:
        if component['delivery'] == 'bundled':
            expected.update(ref['path'] for ref in component['files'])
        elif any((stage / ref['path']).exists() for ref in component['files']):
            raise ValueError('customer weights present in delivery')
        expected.update('MRL_LICENSE_EVIDENCE/' + ref['path'] for ref in component['documents'])
    actual = inventory(stage) - {'MRL_PRODUCT_BUNDLE_MANIFEST.json'}
    if actual != expected:
        raise ValueError('packaged license coverage mismatch')
    if (stage / 'NOTICE').read_bytes() != notice_bytes(manifest, evidence):
        raise ValueError('NOTICE mismatch')
    if load_json(stage / 'MRL_LICENSE_RECEIPT.json') != result:
        raise ValueError('license receipt mismatch')
    if load_json(stage / 'MRL_LICENSE_REGISTRY_SNAPSHOT.json') != registry_snapshot(load_json(REGISTRY), result):
        raise ValueError('registry snapshot stale')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'context', 'artifact-root', 'evidence-root', 'receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--exhaustive', action='store_true')
    parser.add_argument('--verify-packaged', action='store_true',
                        help='Rehash complete package, NOTICE, evidence and current registry')
    args = parser.parse_args(argv)
    try:
        result = (verify_packaged(args.artifact_root) if args.verify_packaged else
                  evaluate(load_json(args.manifest), load_json(args.context), args.artifact_root,
                           args.evidence_root, exhaustive=args.exhaustive))
    except (ValueError, OSError) as error:
        result = {'allowed': False, 'reason': str(error), 'origin_signature': 'MrLiouWord'}
    with args.receipt.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['allowed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
