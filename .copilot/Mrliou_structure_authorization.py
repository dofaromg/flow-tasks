#!/usr/bin/env python3
"""MRL structure-index authorization. origin_signature: MrLiouWord.

The checked-out registry is the authority; CLI flags/environment cannot select
another registry. This enforces cooperating entry points, not a hostile host.
"""

import argparse
import getpass
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'config/MRL_AUTHORIZATION_REGISTRY_v1.json'
REPOSITORY = 'dofaromg/flow-tasks'
WORKFLOW = REPOSITORY + '/.github/workflows/structure-indexer.yml@refs/heads/main'
ARTIFACTS = ('.copilot/structure-scan.json', '.copilot/structure-index.json',
             '.copilot/structure.fltnz', 'STRUCTURE.md')
ACTIONS = {'structure.scan', 'structure.generate', 'structure.upload'}
REQUIRED = {'record_id', 'grantee', 'scope', 'actions', 'issued_by', 'issued_at',
            'expires_at', 'evidence_reference', 'rollback'}
FALSE_POLICIES = (
    'implicit_authorization_allowed', 'repository_access_is_authorization',
    'collaborator_role_is_authorization', 'bot_or_agent_execution_is_authorization',
    'prior_contribution_is_authorization', 'technical_capability_is_authorization',
    'silence_is_authorization', 'restoration_is_authorization',
    'operating_grant_transfers_authorship', 'operating_grant_transfers_founder_status',
    'operating_grant_transfers_commercial_rights',
)


class AuthorizationDenied(PermissionError):
    """A fixed reason code, never source paths or registry contents."""


def deny(reason):
    raise AuthorizationDenied(reason)


def exact_path(path, relative):
    """Reject path escapes and symlinks, including symlinked parent directories."""
    path = Path(os.path.abspath(path))
    expected = ROOT / relative
    if path != expected:
        deny('PATH_SCOPE_MISMATCH')
    for item in (path, *path.parents):
        if item == ROOT:
            break
        if item.is_symlink():
            deny('SYMLINK_DENIED')
    return path


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            deny('DUPLICATE_REGISTRY_KEY')
        result[key] = value
    return result


def _timestamp(value):
    if not isinstance(value, str):
        deny('INVALID_GRANT_TIME')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        deny('INVALID_GRANT_TIME')
    return result


def _context():
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        event = os.environ.get('GITHUB_EVENT_NAME', '')
        actor = os.environ.get('GITHUB_ACTOR', '')
        trigger = os.environ.get('GITHUB_TRIGGERING_ACTOR', '')
        if (os.environ.get('GITHUB_REPOSITORY') != REPOSITORY
                or os.environ.get('GITHUB_REF') != 'refs/heads/main'
                or os.environ.get('GITHUB_WORKFLOW_REF') != WORKFLOW
                or event not in {'push', 'schedule', 'workflow_dispatch', 'issue_comment'}
                or not actor or not trigger):
            deny('UNTRUSTED_EXECUTION_CONTEXT')
        return 'github-actions', {'actor': actor, 'triggering_actor': trigger}, event, \
            'refs/heads/main', 'github-actions-artifact:' + REPOSITORY
    # Local identity is an operating-system context, not a cryptographic signature.
    actor = 'local:' + getpass.getuser()
    return 'local', {'actor': actor, 'triggering_actor': actor}, 'local', 'local', 'local-checkout'


def authorize(actions, depth=8):
    """Require one active exact-scope grant for the complete requested operation."""
    try:
        if not set(actions) or not set(actions) <= ACTIONS or type(depth) is not int or not 1 <= depth <= 8:
            deny('INVALID_REQUEST')
        exact_path(REGISTRY, 'config/MRL_AUTHORIZATION_REGISTRY_v1.json')
        raw = REGISTRY.read_bytes()
        registry = json.loads(raw, object_pairs_hook=_unique,
                              parse_constant=lambda _: deny('INVALID_JSON_CONSTANT'))
        model = registry['authorization_model']
        if (registry.get('schema_version') != '1.0.0'
                or registry.get('origin_signature') != 'MrLiouWord'
                or registry.get('root_authority') != 'Mr.liou'
                or model.get('default_decision') != 'DENY'
                or model.get('explicit_grant_required') is not True
                or model.get('delegation_requires_explicit_scope') is not True
                or any(model.get(key) is not False for key in FALSE_POLICIES)
                or set(registry['required_fields']) != REQUIRED):
            deny('INVALID_REGISTRY_POLICY')
        grants = registry['active_grants']
        if not isinstance(grants, list):
            deny('INVALID_GRANT_LIST')
        if not grants:
            deny('NO_RECORDED_GRANT')
        environment, grantee, event, ref, destination = _context()
        if environment == 'local' and 'structure.upload' in actions:
            deny('LOCAL_UPLOAD_DENIED')
        now = datetime.now(timezone.utc)
        matches = []
        ids = set()
        for grant in grants:
            # Unknown fields are denied rather than silently ignoring restrictions.
            if (not isinstance(grant, dict) or set(grant) != REQUIRED | {
                    'status', 'prohibited_actions', 'purpose', 'environment'}):
                deny('INVALID_GRANT_SCHEMA')
            scope = grant['scope']
            if not isinstance(scope, dict) or set(scope) != {
                    'repository', 'assets', 'max_depth', 'destination', 'events', 'ref'}:
                deny('INVALID_GRANT_SCOPE')
            for field in ('record_id', 'evidence_reference', 'rollback'):
                if not isinstance(grant[field], str) or not grant[field].strip():
                    deny('INCOMPLETE_GRANT')
            if grant['record_id'] in ids:
                deny('DUPLICATE_GRANT_ID')
            ids.add(grant['record_id'])
            allowed = grant['actions']
            prohibited = grant['prohibited_actions']
            if (not isinstance(allowed, list) or not allowed or not set(allowed) <= ACTIONS
                    or not isinstance(prohibited, list) or not set(prohibited) <= ACTIONS
                    or type(scope['max_depth']) is not int or not 1 <= scope['max_depth'] <= 8
                    or not isinstance(scope['events'], list)
                    or not scope['events'] or not set(scope['events']) <= {
                        'push', 'schedule', 'workflow_dispatch', 'issue_comment', 'local'}):
                deny('INVALID_GRANT_CONSTRAINTS')
            starts, expires = _timestamp(grant['issued_at']), _timestamp(grant['expires_at'])
            if starts >= expires:
                deny('INVALID_GRANT_TIME')
            if (grant['status'] == 'active' and grant['issued_by'] == 'MrLiouWord'
                    and grant['grantee'] == grantee and grant['environment'] == environment
                    and grant['purpose'] == 'structure-index' and starts <= now < expires
                    and scope['repository'] == REPOSITORY and scope['assets'] == ['.']
                    and scope['destination'] == destination and scope['ref'] == ref
                    and event in scope['events'] and depth <= scope['max_depth']
                    and set(actions) <= set(allowed) and not set(actions) & set(prohibited)):
                matches.append(grant['record_id'])
        if len(matches) != 1:
            deny('NO_UNIQUE_MATCHING_GRANT')
        return {'decision': 'ALLOW', 'registry_sha256': hashlib.sha256(raw).hexdigest(),
                'origin_signature': 'MrLiouWord'}
    except AuthorizationDenied:
        raise
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        deny('REGISTRY_UNREADABLE_OR_INVALID')


def main():
    """Evaluate workflow preflight/upload without reading source/index contents."""
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['preflight', 'upload'])
    parser.add_argument('--depth', type=int, default=8)
    args = parser.parse_args()
    try:
        result = authorize(ACTIONS if args.phase == 'preflight' else {'structure.upload'}, args.depth)
        if args.phase == 'upload':
            for relative in ARTIFACTS:
                path = exact_path(ROOT / relative, relative)
                if not path.is_file() or path.stat().st_size == 0:
                    deny('MISSING_GENERATED_ARTIFACT')
        print(json.dumps(result, sort_keys=True))
    except AuthorizationDenied as error:
        print(json.dumps({'decision': 'DENY', 'reason': str(error),
                          'origin_signature': 'MrLiouWord'}, sort_keys=True))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
