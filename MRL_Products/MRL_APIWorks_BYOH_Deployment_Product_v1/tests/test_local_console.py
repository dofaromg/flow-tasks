"""HTTP console integration; fixtures never grant production trust."""
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile

PRODUCT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PRODUCT/'local_console'))
import MRL_local_console_v1 as console


class LocalConsoleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.server=console.create_server(self.root/'incoming',self.root/'receipts',0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
        self.url=f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown();self.server.server_close();self.server.state.executor.shutdown(wait=True)
        self.thread.join(3)

    def request(self,path,body=None,token=True,extra=None):
        headers={'Authorization':'Bearer '+self.server.state.token} if token else {}
        if extra:headers.update(extra)
        raw=json.dumps(body).encode() if body is not None else None
        if raw:headers['Content-Type']='application/json'
        return urllib.request.urlopen(urllib.request.Request(self.url+path,data=raw,headers=headers),timeout=15)

    def run_job(self,action,inputs=None):
        with self.request('/api/jobs',{'action':action,'inputs':inputs or {}}) as r:
            self.assertEqual(r.status,202);job=json.load(r)
        end=time.monotonic()+20
        while time.monotonic()<end:
            with self.request('/api/jobs/'+job['id']) as r:current=json.load(r)
            if current['status'] in ('completed','failed'):return current
            time.sleep(.02)
        self.fail('job timed out')

    def test_local_html_and_auth_boundary(self):
        with self.request('/',token=False) as r:
            self.assertIn('本地驗收操作台',r.read().decode())
            self.assertEqual(r.headers['X-Frame-Options'],'DENY')
        for headers in ({},{'Origin':'https://untrusted.example'},{'Host':'untrusted.example'}):
            with self.assertRaises(urllib.error.HTTPError) as err:
                self.request('/api/health',token=bool(headers),extra=headers)
            self.assertEqual(err.exception.code,403)
        with self.request('/api/health') as r:
            health=json.load(r);self.assertEqual(health['production_keys'],0)
            self.assertEqual(health['production_artifacts'],0)

    def test_complete_demo_and_zip_are_real_and_replayable(self):
        job=self.run_job('demo');result=job['result']
        self.assertEqual(result['engineering'],'PASS',result)
        self.assertTrue(result['test_only']);self.assertTrue(result['replay']['replay_matches'])
        self.assertFalse(result['digest_drift']['release_allowed'])
        self.assertEqual(result['formal_delivery_admission'],'NOT_GRANTED')
        with self.request('/api/export/'+job['id']) as r:archive=zipfile.ZipFile(io.BytesIO(r.read()))
        self.assertEqual(len(archive.namelist()),9)
        self.assertFalse(any(n.endswith('.pem') for n in archive.namelist()))
        export=self.root/'unpacked';archive.extractall(export)
        policy=console.trust.load_json(export/'evidence/MRL_TRUST_POLICY.json')
        manifest=console.trust.load_json(export/'evidence/MRL_TRUST_MANIFEST.json')
        prior=console.trust.load_json(export/'evidence/MRL_TRUST_RECEIPT.json')
        self.assertTrue(console.trust.replay(prior,manifest,policy,export/'evidence')['replay_matches'])
        (Path(result['demo_path'])/'unrelated-secret.pem').write_text('NOT_FOR_EXPORT')
        raw=self.server.state.export(job['id'])
        self.assertNotIn('unrelated-secret.pem',zipfile.ZipFile(io.BytesIO(raw)).namelist())

    def test_manual_verification_ignores_demo_policy(self):
        job=self.run_job('demo');demo=Path(job['result']['demo_path'])
        import shutil
        shutil.copytree(demo,self.server.state.root/'runtime')
        checked=self.run_job('verify',{'manifest':'runtime/MRL_TRUST_MANIFEST.json','artifact_root':'runtime'})
        self.assertEqual(checked['result']['decision']['status'],'denied')
        self.assertFalse(checked['result']['decision']['release_allowed'])

    def test_path_escape_and_invalid_request_fail_closed(self):
        job=self.run_job('verify',{'manifest':'../missing.json','artifact_root':'.'})
        self.assertEqual(job['status'],'failed')
        self.assertEqual(job['result']['formal_delivery_admission'],'NOT_GRANTED')
        for body in ({'action':'run-shell','inputs':{}},[],{'action':'verify','inputs':[]}):
            with self.assertRaises(urllib.error.HTTPError) as err:self.request('/api/jobs',body)
            self.assertEqual(err.exception.code,400)

    def test_append_only_receipts_and_restart_history(self):
        job=self.run_job('demo')
        original=(self.server.state.state_dir/(job['id']+'.json')).read_bytes()
        with self.request('/api/history') as r:self.assertEqual(json.load(r)[0]['id'],job['id'])
        replacement=console.ConsoleState(self.server.state.root,self.server.state.state_dir)
        self.addCleanup(lambda:replacement.executor.shutdown(wait=True))
        self.assertNotEqual(replacement.token,self.server.state.token)
        self.assertEqual(replacement.history()[0]['id'],job['id'])
        self.assertEqual(replacement.receipt(job['id'])['receipt_hash'],job['result']['receipt_hash'])
        self.assertEqual((self.server.state.state_dir/(job['id']+'.json')).read_bytes(),original)

    def test_receipt_tamper_blocks_export(self):
        job=self.run_job('demo');path=self.server.state.state_dir/(job['id']+'.json')
        r=json.loads(path.read_text());r['engineering']='FORGED';path.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.server.state.export(job['id'])

    def test_symlink_outside_workspace_denies(self):
        outside=self.root/'outside';outside.mkdir();target=self.server.state.root/'linked'
        try:target.symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError):console.confined(self.server.state.root,'linked',True)

    def test_existing_gateway_capture_and_restart_replay(self):
        from test_node_evidence import NodeEvidenceTests
        fixture=NodeEvidenceTests();fixture.setUp();self.addCleanup(fixture.tearDown)
        state=console.ConsoleState(fixture.root,self.root/'node-receipts')
        self.addCleanup(lambda:state.executor.shutdown(wait=True))
        def capture(inputs):
            job=state.submit('node',inputs);end=time.monotonic()+20
            while time.monotonic()<end:
                with state.lock:current=state.jobs[job['id']].copy()
                if current['status'] in ('completed','failed'):return current['result']
                time.sleep(.02)
            self.fail('node timeout')
        first=capture({'gateway':fixture.url,'runtime_data':str(fixture.data_dir)})
        self.assertEqual(first['node_evidence']['status'],'LIVE_LOOP_EVIDENCE_PASS',first)
        prior=fixture.root/'node-prior.json';prior.write_text(json.dumps(first['node_evidence']))
        port=fixture.gateway.server_port;fixture.stop_gateway();fixture.start_gateway(port)
        second=capture({'gateway':fixture.url,'runtime_data':str(fixture.data_dir),'node_receipt':str(prior)})
        self.assertEqual(second['node_evidence']['status'],'PERSISTED_REPLAY_EVIDENCE_PASS',second)
        self.assertEqual(second['formal_delivery_admission'],'NOT_GRANTED')
        self.assertFalse(second['node_evidence']['restart_observed'])


if __name__=='__main__':unittest.main()
