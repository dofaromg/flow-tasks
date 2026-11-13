"""Build and read back the expected standalone deployment ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
MANIFEST = "DELIVERY_MANIFEST.json"


def descriptor(data):
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def verify(path):
    expected = json.loads((ROOT / "Expected_Delivery.json").read_bytes())
    files = set(expected["expected_files"])
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        try:
            manifest = json.loads(archive.read(MANIFEST))
            if not isinstance(manifest.get("files"), dict):
                manifest = {"files": {}}
        except (KeyError, ValueError, AttributeError):
            manifest = {"files": {}}
        payload = set(manifest["files"])
        missing = sorted(files - set(names))
        extra = sorted(set(names) - files)
        mismatch = sorted(name for name in files & set(names)
                          if not archive.getinfo(name).file_size or (
                              name != MANIFEST and
                              descriptor(archive.read(name)) != manifest["files"].get(name)))
        if (len(names) != len(set(names)) or payload | {MANIFEST} != files or
                "Expected_Delivery.json" not in names or
                archive.read("Expected_Delivery.json") != (ROOT / "Expected_Delivery.json").read_bytes() or
                manifest.get("package_map") != {"payload": sorted(files - {MANIFEST}),
                                            "manifest": MANIFEST} or
                manifest.get("dependency_tree") != expected["expected_dependencies"]):
            mismatch.append("package manifest")
        orphan = sorted({name for parent, children in expected["expected_dependencies"].items()
                         for name in [parent, *children] if name not in files})
        coverage = round(100 * (len(files) - len(missing)) / len(files), 2)
        status = "DELIVERY_FAIL" if missing or extra or mismatch or orphan else "DELIVERY_PASS"
        return {"status": status,
                "expected": len(files), "zip_count": len(names), "coverage": coverage,
                "missing": missing, "extra": extra, "mismatch": mismatch,
                "renamed": [], "orphan": orphan, "zip": descriptor(path.read_bytes())}


def build(path):
    expected = json.loads((ROOT / "Expected_Delivery.json").read_bytes())
    files = expected["expected_files"]
    upstream = expected["upstream_git_blobs"]
    payload = {}
    for name in files:
        if name == MANIFEST:
            continue
        source = ROOT / name
        if name in upstream and not source.is_file():
            source = ROOT.parent / name
        data = source.read_bytes()
        if name in upstream:
            # Windows checkouts may normalize line endings; only accept an
            # exact match to the pinned Git blob after reversing that change.
            def git_blob(content):
                return hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
            if git_blob(data) != upstream[name]:
                data = data.replace(b"\r\n", b"\n")
            if git_blob(data) != upstream[name]:
                raise ValueError(f"Upstream blob changed: {name}")
        payload[name] = data
    if any(not data for data in payload.values()):
        raise ValueError("Empty deployment file")
    manifest = {
        "schema": "MRL_Deployment_Manifest/v1",
        "files": {name: descriptor(data) for name, data in sorted(payload.items())},
        "dependency_tree": expected["expected_dependencies"],
        "package_map": {"payload": sorted(payload), "manifest": MANIFEST},
        "origin_signature": expected["origin_signature"],
        "canonical_authority": expected["canonical_authority"],
        "upstream_commit": expected["upstream_commit"],
    }
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in {**payload, MANIFEST: data}.items():
            archive.writestr(name, content)
    return verify(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["build", "verify"])
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()
    result = build(args.zip) if args.mode == "build" else verify(args.zip)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "DELIVERY_PASS" else 1)
