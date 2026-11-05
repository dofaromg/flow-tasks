"""Verify the persisted local-delivery archive and reject post-extraction drift."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

PRODUCT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PRODUCT/'local_console'))
import MRL_build_local_delivery_v1 as builder
from MRL_verify_local_package_v1 import verify


class LocalDeliveryTests(unittest.TestCase):
    def test_full_zip_closure_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);output=root/'MRL_delivery.zip'
            result=builder.build(output,'a'*40)
            self.assertEqual(result['Coverage'],100)
            self.assertEqual(result['expected_file_count'],result['actual_zip_count'])
            with zipfile.ZipFile(output) as z:
                self.assertIn(builder.NAME+'/Start_MRL.cmd',z.namelist())
                self.assertIn(builder.NAME+'/'+builder.CONSOLE+'/index.html',z.namelist())
                z.extractall(root/'unpacked')
            stage=root/'unpacked'/builder.NAME
            self.assertEqual(verify(stage)['delivery_gate'],'DELIVERY_PASS')
            (stage/'Start_MRL.cmd').write_bytes(b'tampered')
            self.assertIn('Start_MRL.cmd',verify(stage)['Mismatch'])
            (stage/'extra.bin').write_bytes(b'extra')
            self.assertIn('extra.bin',verify(stage)['Extra'])
            (stage/'Run_Local_Acceptance.cmd').unlink()
            self.assertIn('Run_Local_Acceptance.cmd',verify(stage)['Missing'])
            with self.assertRaises(FileExistsError):builder.build(output,'a'*40)

    def test_exact_commit_and_manifest_inventory_required(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):builder.build(Path(t)/'bad.zip','main')


if __name__=='__main__':unittest.main()
