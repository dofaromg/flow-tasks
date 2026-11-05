#!/usr/bin/env python3
"""Compose MRL hardware and Runtime trust gates. origin_signature: MrLiouWord."""
import argparse
import json
from pathlib import Path

from MRL_artifact_trust_v1 import POLICY, evaluate_delivery, load_json


def main(argv=None):
    """Use the release-reviewed policy shipped beside the verifier, never artifact keys."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('host', 'workload', 'artifact-paths', 'runtime-manifests', 'artifact-root', 'receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        # runtime-manifests contains full signed documents for runner and runtime.
        result = evaluate_delivery(load_json(args.host), load_json(args.workload), args.artifact_root,
                                   load_json(args.artifact_paths), load_json(args.runtime_manifests),
                                   load_json(POLICY))
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {'origin_signature': 'MrLiouWord', 'allowed': False,
                  'formal_delivery_admission': 'DENIED', 'reason': str(error)}
    with args.receipt.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['allowed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
