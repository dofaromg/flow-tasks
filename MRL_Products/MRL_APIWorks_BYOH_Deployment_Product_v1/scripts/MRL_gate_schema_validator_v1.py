#!/usr/bin/env python3
"""Offline MRL BYOH Draft 2020-12 conformance. origin_signature: MrLiouWord."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012

from MRL_artifact_trust_v1 import canonical, load_json

DRAFT = 'https://json-schema.org/draft/2020-12/schema'
BASE_URI = 'https://mrl.invalid/byoh/'
PRODUCT = Path(__file__).resolve().parents[1]
LICENSE_PROFILE = 'licenses/MRL_license_manifest_validation_v1.schema.json'
LICENSE_SOURCE = 'licenses/MRL_license_manifest_schema_v1.json'
SCHEMA_FILES = {
    'artifact-trust': 'trust/MRL_artifact_trust_manifest_schema_v1.json',
    'billing-receipt': 'schemas/billing-receipt.schema.json',
    'byoh-manifest': 'schemas/compatibility-manifest.schema.json',
    'byoh-bundle-manifest': 'schemas/MRL_product_bundle_manifest_schema_v1.json',
    'decision-request': 'schemas/rc0/decision-contract.schema.json',
    'decision-response': 'schemas/rc0/decision-response.schema.json',
    'deployment-passport': 'schemas/rc0/deployment-passport.schema.json',
    'license-manifest': LICENSE_PROFILE,
    'reference-adapter-config-rc1-draft': 'schemas/rc1-draft/reference-adapter-config.schema.json',
    'reference-adapter-request-rc1-draft': 'schemas/rc1-draft/reference-adapter-request.schema.json',
    'reference-adapter-usage-rc1-draft': 'schemas/rc1-draft/reference-adapter-usage.schema.json',
    'route-receipt': 'schemas/rc0/route-receipt.schema.json',
    'route-receipt-rc1-draft': 'schemas/rc1-draft/route-receipt.schema.json',
    'routing-adapter-result-rc1-draft': 'schemas/rc1-draft/routing-adapter-result.schema.json',
    'routing-decision-input-rc1-draft': 'schemas/rc1-draft/routing-decision-input.schema.json',
    'security-privacy-baseline': 'schemas/security-privacy-baseline.schema.json',
}
FORMAT_CHECKER = Draft202012Validator.FORMAT_CHECKER


class SchemaRejected(ValueError):
    """A conformance error with an instance location and stable keyword."""

    def __init__(self, keyword, path='', detail=''):
        self.keyword = keyword
        self.path = path
        super().__init__(f'schema {keyword} at {path or "/"}' +
                         (f': {detail}' if detail else ''))


def pointer(parts):
    """Return an RFC 6901 JSON Pointer."""
    return ''.join('/' + str(part).replace('~', '~0').replace('/', '~1') for part in parts)


def schema_nodes(resource, base):
    """Walk Draft 2020-12 subschemas with their effective base URIs."""
    if resource.id() is not None:
        base = urljoin(base, resource.id())
    yield resource, base
    for child in resource.subresources():
        yield from schema_nodes(child, base)


class SchemaCatalog:
    """Compile the checked-in schema set without filesystem or HTTP retrieval."""

    def __init__(self, root=PRODUCT):
        if 'date-time' not in FORMAT_CHECKER.checkers:
            raise SchemaRejected('format-checker-unavailable', detail='install requirements.mrl45.lock')
        identifiers = set()
        anchors = set()
        resources = []
        nodes = []
        self.ids = {}
        self.uris = {}
        for name, relative_path in (*SCHEMA_FILES.items(), ('license-source', LICENSE_SOURCE)):
            document = load_json(root / relative_path)
            if document.get('$schema') != DRAFT or not isinstance(document.get('$id'), str) or not document['$id']:
                raise SchemaRejected('catalog-identity', detail=relative_path)
            try:
                Draft202012Validator.check_schema(document)
            except SchemaError as error:
                raise SchemaRejected('invalid-schema', pointer(error.absolute_path), relative_path) from error
            retrieval_uri = urljoin(BASE_URI, relative_path)
            resource = Resource.from_contents(document, default_specification=DRAFT202012)
            resources.append((retrieval_uri, resource))
            self.ids[name] = document['$id']
            self.uris[name] = urljoin(retrieval_uri, document['$id'])
            for node, uri in schema_nodes(resource, retrieval_uri):
                if node.id() is not None:
                    if uri in identifiers or not urlsplit(uri).scheme or urlsplit(uri).fragment:
                        raise SchemaRejected('catalog-id', detail=uri)
                    identifiers.add(uri)
                for anchor in node.anchors():
                    key = (uri, anchor.name)
                    if key in anchors:
                        raise SchemaRejected('duplicate-anchor', detail=f'{uri}#{anchor.name}')
                    anchors.add(key)
                nodes.append((node.contents, uri))

        self.registry = Registry().with_resources(resources).crawl()
        for document, uri in nodes:
            if not isinstance(document, dict):
                continue
            if document.get('$schema', DRAFT) != DRAFT:
                raise SchemaRejected('catalog-dialect', detail=uri)
            if 'format' in document and document['format'] not in FORMAT_CHECKER.checkers:
                raise SchemaRejected('unknown-format', detail=document['format'])
            for keyword in ('$ref', '$dynamicRef'):
                if keyword in document:
                    self._check_ref(uri, document[keyword])

    def _check_ref(self, base, reference):
        try:
            target = self.registry.resolver(base).lookup(reference)
        except Unresolvable as error:
            raise SchemaRejected('unresolved-ref', detail=f'{base} → {reference}') from error
        if not isinstance(target.contents, (bool, dict)):
            raise SchemaRejected('ref-target-not-schema', detail=f'{base} → {reference}')

    def _validate(self, uri, instance):
        # Reuse the gate's strict JSON representation before Draft validation.
        try:
            canonical(instance)
        except (ValueError, TypeError) as error:
            raise SchemaRejected('invalid-json-value') from error
        validator = Draft202012Validator(
            {'$schema': DRAFT, '$ref': uri},
            registry=self.registry, format_checker=FORMAT_CHECKER,
        )
        error = next(validator.iter_errors(instance), None)
        if error is not None:
            detail = ''
            if error.validator == 'required':
                detail = 'missing ' + ', '.join(k for k in error.validator_value if k not in error.instance)
            elif error.validator in ('type', 'format'):
                detail = 'expected ' + str(error.validator_value)
            raise SchemaRejected(error.validator, pointer(error.absolute_path), detail)

    def validate(self, name, instance):
        """Validate an explicitly selected product contract."""
        if name not in SCHEMA_FILES:
            raise SchemaRejected('unknown-schema')
        self._validate(self.uris[name], instance)
        if name == 'license-manifest':
            for index, component in enumerate(instance['components']):
                require_wire_integer(component['annual_revenue_limit_usd'],
                                     ('components', index, 'annual_revenue_limit_usd'))

    def validate_license_inputs(self, manifest, context):
        """Use the catalog for both existing License Gate input documents."""
        self.validate('license-manifest', manifest)
        self._validate(self.uris['license-manifest'] + '#/$defs/context', context)
        for key in ('mrl_annual_revenue_usd', 'customer_annual_revenue_usd'):
            require_wire_integer(context[key], (key,))


def require_wire_integer(value, path):
    """Preserve PR #708's exact integer representation for rights records."""
    if value is not None and type(value) is not int:
        raise SchemaRejected('type', pointer(path), 'expected JSON integer without a decimal')


@lru_cache(maxsize=1)
def product_catalog():
    """Reuse the fixed product catalog within one process."""
    return SchemaCatalog()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check', help='check schema IDs, metaschemas and offline references')
    validate = commands.add_parser('validate', help='validate one JSON document')
    validate.add_argument('schema', choices=SCHEMA_FILES)
    validate.add_argument('instance', type=Path)
    args = parser.parse_args(argv)
    try:
        catalog = product_catalog()
        if args.command == 'check':
            output = {'status': 'SCHEMA_CATALOG_VALID', 'schema_ids': catalog.ids}
        else:
            catalog.validate(args.schema, load_json(args.instance))
            output = {'status': 'SCHEMA_VALID', 'schema_id': catalog.ids[args.schema]}
        code = 0
    except SchemaRejected as error:
        output = {'status': 'SCHEMA_REJECTED', 'keyword': error.keyword,
                  'instance_path': error.path, 'reason': str(error)}
        code = 2
    except (SchemaError, ValueError, TypeError, OSError, RecursionError) as error:
        output = {'status': 'SCHEMA_REJECTED', 'reason': str(error)}
        code = 2
    print(json.dumps(output, ensure_ascii=True, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
