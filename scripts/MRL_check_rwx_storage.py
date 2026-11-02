"""Reject RWX claims that rely on a cluster default. origin_signature: MrLiouWord.

Read-only: accepts rendered YAML or kubectl JSON, including Lists and claim
templates. An explicit empty string disables dynamic provisioning and is kept.
"""

import argparse
from pathlib import Path
import sys

import yaml


def check_documents(documents):
    """Return claim inventory and policy violations without changing resources."""
    claims, errors = [], []

    def claim(value, location):
        if not isinstance(value, dict) or not isinstance(value.get("spec"), dict):
            errors.append(f"{location}: invalid PVC spec")
            return
        spec = value["spec"]
        modes = spec.get("accessModes", [])
        if not isinstance(modes, list):
            errors.append(f"{location}: accessModes must be a list")
            return
        storage = spec.get("storageClassName")
        name = value.get("metadata", {}).get("name", "<unnamed>")
        claims.append((location, name, modes, storage))
        if "ReadWriteMany" in modes and not isinstance(storage, str):
            errors.append(
                f"{location} ({name}): RWX requires explicit storageClassName; "
                'choose an approved provider or "" for static binding'
            )

    def walk(value, location):
        if isinstance(value, dict):
            if value.get("kind") == "PersistentVolumeClaim":
                claim(value, location)
            for key, child in value.items():
                if key == "volumeClaimTemplates":
                    if not isinstance(child, list):
                        errors.append(f"{location}.{key}: expected list")
                    else:
                        for index, template in enumerate(child):
                            claim(template, f"{location}.{key}[{index}]")
                else:
                    walk(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{location}[{index}]")

    for index, document in enumerate(documents):
        if document is not None and not isinstance(document, dict):
            errors.append(f"document[{index}]: expected Kubernetes object")
        else:
            walk(document, f"document[{index}]")
    return claims, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="Rendered YAML / kubectl JSON file")
    args = parser.parse_args()
    try:
        with Path(args.manifest).open(encoding="utf-8-sig") as source:
            claims, errors = check_documents(list(yaml.safe_load_all(source)))
    except (OSError, yaml.YAMLError) as exc:
        print(f"MRL_STORAGE_CHECK_ERROR: {exc}", file=sys.stderr)
        return 2
    for location, name, modes, storage in claims:
        print(f"{location}: {name} modes={modes!r} storageClassName={storage!r}")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"MRL_STORAGE_POLICY_{'FAIL' if errors else 'PASS'} claims={len(claims)}")
    print("Scope: supplied manifests only; live cluster, VPC-SC and billing unverified.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
