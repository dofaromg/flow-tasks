#!/usr/bin/env python3
"""Build and run module-a locally; retain evidence without pushing any image."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "origin_signature": "MrLiouWord",
        "build": "NOT_RUN", "container_start": "NOT_RUN", "http": "NOT_RUN",
        "deployment": "NOT_PERFORMED", "commands": [], "http_checks": [],
    }
    container = None
    image = "mrl-module-a-smoke:" + uuid.uuid4().hex
    exit_code = 1

    def run(command, timeout=120, check=True):
        result = subprocess.run(command, cwd=root, text=True, capture_output=True,
                                timeout=timeout, check=False)
        record = {"command": command, "exit_code": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
        report["commands"].append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
        if check and result.returncode:
            raise RuntimeError("Command failed: " + " ".join(command))
        return result

    def request(base, method, path, body=None, expected=200):
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(base + path, method=method,
                                     data=body.encode() if body is not None else None,
                                     headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read().decode()
            report["http_checks"].append({"method": method, "path": path,
                                          "request_body": body, "status": response.status,
                                          "response_body": raw})
            if response.status != expected:
                raise AssertionError(f"{method} {path}: {response.status} != {expected}")
            return json.loads(raw)

    try:
        report["source_commit"] = run(["git", "rev-parse", "HEAD"]).stdout.strip()
        report["working_tree"] = run(["git", "status", "--short"]).stdout
        sources = ["apps/module-a/Dockerfile", "apps/module-a/app.py",
                   "apps/module-a/core.py", "apps/module-a/requirements.txt"]
        sources += [str(path.relative_to(root)) for path in sorted(
            (root / "apps/common").glob("*.py"))]
        report["source_sha256"] = {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in sources
        }
        if shutil.which("docker") is None:
            report["build"] = "UNVERIFIED"
            report["reason"] = "Docker CLI is not installed; no Docker build or container ran."
            exit_code = 2
        else:
            run(["docker", "version"])
            report["build"] = "FAIL"
            run(["docker", "build", "--progress=plain", "-t", image,
                 "-f", "apps/module-a/Dockerfile", "apps"], timeout=900)
            report["build"] = "PASS"
            run(["docker", "image", "inspect", image])
            report["container_start"] = "FAIL"
            container = run(["docker", "run", "--detach", "--publish", "127.0.0.1::8080",
                             "--env", "ENVIRONMENT=container-smoke", image]).stdout.strip()
            port = run(["docker", "port", container, "8080/tcp"]).stdout.strip().split(":")[-1]
            base = "http://127.0.0.1:" + port
            deadline = time.monotonic() + 40
            while True:
                try:
                    if request(base, "GET", "/health") != {"status": "healthy"}:
                        raise AssertionError("Unexpected health response")
                    break
                except (OSError, urllib.error.URLError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.5)
            report["container_start"] = "PASS"

            # Inspect imports, versions, source bytes and route registration inside
            # the image, with no source bind mount and no injected PYTHONPATH.
            inspection = run(["docker", "exec", container, "python", "-c", """
import app, common.flask_utils, hashlib, importlib.metadata, json
from pathlib import Path
rules = list(app.app.url_map.iter_rules())
for path in ('/health', '/info', '/compute'):
    matching = [r for r in rules if r.rule == path]
    assert len(matching) == 1, path
    assert sum(r.endpoint == matching[0].endpoint for r in rules) == 1, path
assert not app.app.debug
files = ['module-a/app.py', 'module-a/core.py', 'module-a/requirements.txt',
         'common/__init__.py', 'common/flask_utils.py']
print(json.dumps({'routes': [(r.rule, r.endpoint) for r in rules],
 'flask_version': importlib.metadata.version('Flask'),
 'gunicorn_version': importlib.metadata.version('gunicorn'),
 'common_module': common.flask_utils.__file__,
 'sha256': {'apps/' + p: hashlib.sha256((Path('/app') / p).read_bytes()).hexdigest()
            for p in files}}))
"""])
            installed = json.loads(inspection.stdout)
            for path, digest in installed["sha256"].items():
                if report["source_sha256"][path] != digest:
                    raise AssertionError("Image source mismatch: " + path)
            report["image_imports_and_routes"] = installed
            report["http"] = "FAIL"
            info = request(base, "GET", "/info")
            assert info == {"service": "module-a", "version": "2.0.0",
                            "environment": "container-smoke",
                            "origin_signature": "MrLiouWord",
                            "capabilities": ["compute_particle", "tokenize", "simhash64",
                                             "particle_score"]}, info
            for text, count in (("MRL MRL 世界", 3), ("", 0)):
                computed = request(base, "POST", "/compute", json.dumps({"text": text}))
                assert computed["ok"] is True
                assert computed["result"]["token_count"] == count
                assert computed["result"]["sha256"] == hashlib.sha256(text.encode()).hexdigest()
                assert computed["result"]["origin_signature"] == "MrLiouWord"
            for body in ('{}', '{"text":null}', '{"text":123}', '{"text":[]}',
                         'null', '[]', '["private-input"]', '"private-input"',
                         '42', 'true', '{"text":', ''):
                rejected = request(base, "POST", "/compute", body, expected=400)
                assert rejected == {"ok": False, "error": "invalid_input"}, rejected
            report["http"] = "PASS"
            exit_code = 0
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if container:
            for command in (["docker", "logs", container],
                            ["docker", "inspect", container],
                            ["docker", "rm", "--force", container]):
                try:
                    run(command, check=False)
                except Exception as error:
                    report.setdefault("cleanup_errors", []).append(str(error))
        if report["build"] == "PASS":
            try:
                run(["docker", "image", "rm", image], check=False)
            except Exception as error:
                report.setdefault("cleanup_errors", []).append(str(error))
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["exit_code"] = exit_code
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print(json.dumps({key: report[key] for key in
                          ("build", "container_start", "http", "deployment", "exit_code")}),
              flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
