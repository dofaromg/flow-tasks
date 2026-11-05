#!/usr/bin/env python3
"""MRL local acceptance console. origin_signature: MrLiouWord."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import ipaddress
import json
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import threading
import urllib.parse
import uuid
import webbrowser
import zipfile

PRODUCT = Path(__file__).resolve().parents[1]
REPO = PRODUCT.parents[1]
sys.path.insert(0, str(PRODUCT/'scripts'))
import MRL_artifact_trust_v1 as trust
import MRL_capture_node_evidence_v1 as node

VERSION = 'MRL_Runtime_Trust_Local_v1.1.0'


def now():
    return datetime.now(timezone.utc).isoformat()


def confined(root: Path, value: str, directory=False) -> Path:
    """Operator inputs may read only within the explicit evidence workspace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError('請填寫檔案或目錄路徑')
    raw = Path(value)
    candidate = raw if raw.is_absolute() else root/raw
    # Reject symlink/junction traversals before resolving the path.
    current = candidate
    while current != current.parent:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError('不接受符號連結或 junction')
        current = current.parent
    result = candidate.resolve(strict=True)
    if result != root and root not in result.parents:
        raise ValueError('路徑超出啟動時指定的 evidence-root')
    if directory and not result.is_dir():
        raise ValueError('需要目錄')
    if not directory and not result.is_file():
        raise ValueError('需要一般檔案')
    return result


class ConsoleState:
    """Single operator queue; append-only receipts and public evidence exports."""
    def __init__(self, evidence_root: Path, state_dir: Path):
        evidence_root.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        self.root = evidence_root.resolve()
        self.state_dir = state_dir.resolve()
        if self.state_dir == PRODUCT or PRODUCT in self.state_dir.parents:
            raise ValueError('state-dir 必須在來源套件外部')
        self.token = secrets.token_urlsafe(32)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.lock = threading.Lock()
        self.jobs = {}

    def health(self):
        try:
            version = subprocess.check_output([trust.openssl_command(), 'version'],
                                              timeout=10, text=True).strip()
        except (ValueError, OSError, subprocess.SubprocessError) as error:
            version = 'UNAVAILABLE: ' + str(error)
        policy = trust.load_json(trust.POLICY)
        return {'origin_signature': trust.ORIGIN, 'console_version': VERSION,
                'host': platform.node(), 'os': platform.platform(), 'python': platform.python_version(),
                'openssl': version, 'evidence_root': str(self.root), 'state_dir': str(self.state_dir),
                'production_keys': len(policy['keys']), 'production_artifacts': len(policy['artifacts']),
                'policy_digest': trust.digest(policy), 'time_utc': now(),
                'formal_delivery_admission': 'REQUIRES_COMPOSED_GATE', 'dl580_acceptance': 'NOT_YET_TESTED'}

    def submit(self, action, inputs):
        if action not in ('demo', 'selftest', 'verify', 'replay', 'compose', 'node'):
            raise ValueError('未知操作')
        if not isinstance(inputs, dict):
            raise ValueError('輸入必須是 JSON object')
        with self.lock:
            if any(j['status'] in ('queued', 'running') for j in self.jobs.values()):
                raise RuntimeError('前一工作尚未完成')
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = {'id': job_id, 'action': action, 'status': 'queued', 'created_at': now()}
        self.executor.submit(self.run, job_id, action, inputs)
        return self.jobs[job_id].copy()

    def run(self, job_id, action, inputs):
        with self.lock:
            self.jobs[job_id]['status'] = 'running'
        result = {'origin_signature': trust.ORIGIN, 'console_version': VERSION,
                  'job_id': job_id, 'action': action, 'recorded_at': now(),
                  'engineering': 'SEPARATE', 'supply_chain_isolation': 'UNVERIFIED',
                  'formal_delivery_admission': 'NOT_GRANTED', 'dl580_acceptance': 'UNVERIFIED'}
        try:
            if action == 'selftest':
                process = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s',
                                          str(PRODUCT/'tests'), '-v'], cwd=REPO,
                                         capture_output=True, text=True, errors='replace', timeout=180)
                result.update(engineering='PASS' if process.returncode == 0 else 'FAIL',
                              exit_code=process.returncode, log=(process.stdout+process.stderr)[-200000:])
            elif action == 'demo':
                # Fixture key lives only in its TemporaryDirectory and is never exported.
                sys.path.insert(0, str(PRODUCT/'tests'))
                from test_artifact_trust import ArtifactTrustTests
                fixture = ArtifactTrustTests()
                fixture.setUp()
                try:
                    demo = self.state_dir/('demo-'+job_id)
                    receipt = trust.export_evidence(fixture.m, fixture.p, fixture.root, demo)
                    replay = trust.replay(receipt, fixture.m, fixture.p, demo)
                    drift_root = fixture.root/'runtime.whl'
                    drift_root.write_bytes(b'MRL_SYNTHETIC_TAMPER_TEST')
                    denied = trust.evaluate(fixture.m, fixture.p, fixture.root)
                    result.update(engineering='PASS' if replay['replay_matches'] and not denied['release_allowed'] else 'FAIL',
                                  test_only=True, demo_path=str(demo),
                                  verification=receipt, replay=replay, digest_drift=denied)
                finally:
                    fixture.doCleanups()
            elif action in ('verify', 'replay', 'compose'):
                artifact_root = confined(self.root, inputs['artifact_root'], True)
                policy = trust.load_json(trust.POLICY)
                if action == 'compose':
                    read = lambda key: trust.load_json(confined(self.root, inputs[key]))
                    outcome = trust.evaluate_delivery(read('host'), read('workload'), artifact_root,
                                                      read('artifact_paths'), read('runtime_manifests'), policy)
                    result.update(decision=outcome,
                                  formal_delivery_admission=outcome['formal_delivery_admission'])
                else:
                    manifest = trust.load_json(confined(self.root, inputs['manifest']))
                    purpose = inputs.get('purpose', 'release')
                    if purpose not in ('release', 'canary'):
                        raise ValueError('目的只能是 release 或 canary')
                    if action == 'replay':
                        previous = trust.load_json(confined(self.root, inputs['receipt']))
                        outcome = trust.replay(previous, manifest, policy, artifact_root)
                    else:
                        outcome = trust.evaluate(manifest, policy, artifact_root, purpose)
                    result.update(decision=outcome)
                    if outcome['status'] in ('trust_verified', 'isolated_canary'):
                        trust.export_evidence(manifest, policy, artifact_root,
                                              self.state_dir/('evidence-'+job_id), outcome['purpose'])
            elif action == 'node':
                # Existing canonical node collector owns gateway loop validation.
                data_dir = confined(self.root, inputs['runtime_data'], True)
                prior = confined(self.root, inputs['node_receipt']) if inputs.get('node_receipt') else None
                captured = node.capture(inputs.get('gateway', 'http://127.0.0.1:7811'), data_dir, prior)
                captured['receipt_hash'] = node.digest(captured)
                result.update(node_evidence=captured,
                              dl580_acceptance='LIVE_LOOP_RECORDED_REQUIRES_MODEL_RESTART_REVIEW')
            result['operation_status'] = 'completed'
        except Exception as error:
            result.update(operation_status='failed', error=f'{type(error).__name__}: {error}')
        result['receipt_hash'] = trust.digest(result)
        path = self.state_dir/(job_id+'.json')
        with path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        if trust.load_json(path) != result:
            raise ValueError('收據讀回不一致')
        with self.lock:
            self.jobs[job_id].update(status=result['operation_status'], result=result)

    def history(self):
        rows = []
        for path in sorted(self.state_dir.glob('*.json'), reverse=True):
            try:
                r = trust.load_json(path)
                if r.get('job_id') == path.stem:
                    rows.append({'id': path.stem, 'action': r['action'], 'status': r['operation_status'],
                                 'recorded_at': r['recorded_at'], 'receipt_hash': r['receipt_hash']})
            except (ValueError, KeyError, OSError):
                continue
        return sorted(rows, key=lambda r: r['recorded_at'], reverse=True)

    def receipt(self, job_id):
        if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
            raise ValueError('無效工作識別碼')
        path = self.state_dir/(job_id+'.json')
        result = trust.load_json(path)
        if result.get('receipt_hash') != trust.digest({k:v for k,v in result.items() if k != 'receipt_hash'}):
            raise ValueError('收據雜湊不符')
        return result

    def export(self, job_id):
        result = self.receipt(job_id)
        files = {'MRL_LOCAL_RECEIPT.json': trust.canonical(result)}
        # Only a completed explicit export directory may be downloaded.
        for prefix in ('demo-', 'evidence-'):
            root = self.state_dir/(prefix+job_id)
            if root.exists():
                manifest = trust.load_json(root/'MRL_TRUST_MANIFEST.json')
                policy = trust.load_json(root/'MRL_TRUST_POLICY.json')
                previous = trust.load_json(root/'MRL_TRUST_RECEIPT.json')
                checked = trust.replay(previous, manifest, policy, root)
                if not checked['replay_matches']:
                    raise ValueError('匯出證據已變更')
                # Recreate the explicit reference allowlist; never recurse through unrelated files.
                refs = [manifest[k]['path'] for k in ('artifact','sbom','provenance')]
                record = next(r for r in policy['artifacts'] if r['identity'] == previous['identity'])
                if record.get('stage') == 'release_approved':
                    refs.append(record['mrl32_clearance']['path'])
                refs += ['MRL_TRUST_MANIFEST.json','MRL_TRUST_POLICY.json','MRL_TRUST_RECEIPT.json']
                for rel in refs:
                    path = confined(root, rel)
                    files['evidence/'+rel] = path.read_bytes()
        inventory = [{'path':n,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in files.items()]
        files['MRL_EXPORT_MANIFEST.json'] = trust.canonical({'origin_signature':trust.ORIGIN,
                                                          'test_only':result.get('test_only',False),'files':inventory})
        output = io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
            for name,raw in files.items():
                z.writestr(name,raw)
        with zipfile.ZipFile(io.BytesIO(output.getvalue())) as z:
            if set(z.namelist()) != set(files) or any(z.read(n) != b for n,b in files.items()):
                raise ValueError('ZIP 讀回失敗')
        return output.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = 'MRL-Local/1.1'

    def log_message(self, *args):
        pass

    def send(self, code, raw, content_type='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(raw)

    def obj(self, code, value):
        self.send(code, trust.canonical(value))

    def permitted(self):
        expected = self.server.server_address
        host = self.headers.get('Host','')
        if host not in (f'127.0.0.1:{expected[1]}', f'localhost:{expected[1]}'):
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{expected[1]}',f'http://localhost:{expected[1]}'):
            return False
        provided = self.headers.get('Authorization','')
        return secrets.compare_digest(provided, 'Bearer '+self.server.state.token)

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == '/':
            # Static UI holds no capability; API requests require this launch session token.
            self.send(200, (PRODUCT/'local_console/index.html').read_bytes(), 'text/html; charset=utf-8')
            return
        if not self.permitted():
            self.obj(403, {'error':'請使用啟動程式顯示的本機網址登入此操作台'})
            return
        state = self.server.state
        try:
            if path == '/api/health':
                self.obj(200,state.health())
            elif path == '/api/history':
                self.obj(200,state.history())
            elif path.startswith('/api/jobs/'):
                job_id = path.split('/')[-1]
                with state.lock:
                    result = state.jobs.get(job_id)
                    if result is None:
                        result = {'id':job_id,'status':'completed','result':state.receipt(job_id)}
                    self.obj(200,result)
            elif path.startswith('/api/export/'):
                raw = state.export(path.split('/')[-1])
                self.send(200,raw,'application/zip')
            else:
                self.obj(404,{'error':'找不到此入口'})
        except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
            self.obj(400,{'error':str(error)})

    def do_POST(self):
        if not self.permitted():
            self.obj(403,{'error':'本機工作階段未授權'})
            return
        if self.path != '/api/jobs':
            self.obj(404,{'error':'找不到此入口'})
            return
        try:
            length = int(self.headers.get('Content-Length','0'))
            if length < 1 or length > 1024*1024:
                raise ValueError('請求大小無效')
            if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                raise ValueError('需要 JSON')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body,dict):
                raise ValueError('需要 JSON object')
            job = self.server.state.submit(body['action'],body.get('inputs',{}))
            self.obj(202,job)
        except RuntimeError as error:
            self.obj(409,{'error':str(error)})
        except (ValueError,KeyError,TypeError) as error:
            self.obj(400,{'error':str(error)})


def create_server(root, state_dir, port=8766):
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.state = ConsoleState(Path(root),Path(state_dir))
    return server


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--evidence-root',type=Path,default=REPO/'MRL_local_data/incoming')
    parser.add_argument('--state-dir',type=Path,default=REPO/'MRL_local_data/receipts')
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args(argv)
    server=create_server(args.evidence_root,args.state_dir,args.port)
    url=f'http://127.0.0.1:{server.server_port}/#token={server.state.token}'
    print(f'{VERSION}\n{url}\nevidence-root: {server.state.root}\nreceipts: {server.state.state_dir}',flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.state.executor.shutdown(wait=True)


if __name__ == '__main__':
    main()
