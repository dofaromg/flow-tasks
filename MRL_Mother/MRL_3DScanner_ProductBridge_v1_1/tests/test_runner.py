import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RUNNER = Path(__file__).resolve().parents[1] / 'backend/MRL_3D_Reconstruction_Server/python/mrl3d_job_runner.py'
spec = importlib.util.spec_from_file_location('runner', RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class RunnerTests(unittest.TestCase):
    def test_colmap_missing_is_independent_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            scan=Path(tmp)/'scan';scan.mkdir();(scan/'photo.jpg').write_bytes(b'test')
            out=Path(tmp)/'out'
            with patch('sys.argv',['runner','--scan-dir',str(scan),'--output-dir',str(out)]), patch.object(runner,'mrl3d_command',return_value=['mrl3d']), patch.object(runner,'which',return_value=None):
                self.assertEqual(runner.main(),3)
            report=json.loads((out/'MRL_JOB_REPORT.json').read_text())
            self.assertEqual(report['status'],'failed');self.assertTrue(report['reason'].startswith('COLMAP_NOT_FOUND'))
            self.assertTrue((scan/'photo.jpg').exists())

    def test_adapter_mismatch_cannot_be_success(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'run',return_value=(0,'{"meta":{"adapter":"synthetic"}}','')):
            self.assertEqual(runner.run_mrl3d(['mrl3d'],Path('config'),tmp,'images','colmap','ok','fail',{}),10)
            self.assertEqual(json.loads(Path(tmp,'MRL_JOB_REPORT.json').read_text())['status'],'failed')

    def test_zero_exit_and_matching_adapter_without_outputs_fails(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'run',return_value=(0,'{"meta":{"adapter":"colmap"}}','')):
            self.assertEqual(runner.run_mrl3d(['mrl3d'],Path('config'),tmp,'images','colmap','ok','fail',{}),11)
            self.assertEqual(json.loads(Path(tmp,'MRL_JOB_REPORT.json').read_text())['status'],'failed')

if __name__ == '__main__': unittest.main()
