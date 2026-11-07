"""Controlled model loading and cache provenance regression tests; no GPU claims."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

REPO = Path(__file__).resolve().parents[1]
PRODUCT = REPO / 'MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1'
sys.path.insert(0, str(PRODUCT / 'tests'))
from test_hardware_admission import fixture, write_artifacts, tested_matrix
from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import MRL_hardware_admission_v1 as gate


class AdmittedModelCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        host, workload = fixture()
        paths = write_artifacts(self.root/'artifacts', workload)
        host['loaded_runner'] = copy.deepcopy(workload['runner'])
        host['loaded_runtime'] = copy.deepcopy(workload['runtime_binary'])
        self.matrix = self.root/'matrix.json'
        tested_matrix(host, workload, self.matrix)
        matrix_patch = patch.object(gate, 'MATRIX', self.matrix)
        matrix_patch.start()
        self.addCleanup(matrix_patch.stop)
        with patch.dict(sys.modules, {'torch': MagicMock(), 'yaml': MagicMock()}):
            spec = importlib.util.spec_from_file_location('mrl_cache_test', REPO/'utils/model_cache.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.cache = module.ModelCache(config_path=str(self.root/'no-config'))
        self.inputs = dict(host=host, workload=workload, artifact_root=self.root/'artifacts', artifact_paths=paths)
        self.name = workload['model']['id']

    def loader(self, streams):
        return {name: stream.read() for name, stream in streams.items()}

    def test_controlled_load_and_matching_cache_hit(self):
        result = self.cache.load_admitted_model(self.name, self.loader, **self.inputs)
        self.assertEqual(result['weights-00001.bin'], b'test-shard-1')
        self.assertIs(self.cache.get_admitted_model(self.name, **self.inputs), result)

    def test_legacy_registration_cannot_forge_provenance(self):
        self.cache.register_model(self.name, object(), {'digest': self.inputs['workload']['model']['digest']}, 0)
        with self.assertRaisesRegex(gate.AdmissionError, 'provenance'):
            self.cache.get_admitted_model(self.name, **self.inputs)

    def test_replaced_source_during_load_is_not_cached(self):
        def replace(streams):
            path = self.root/'artifacts/model/weights-00001.bin'
            path.unlink()
            path.write_bytes(b'other model')
            self.assertEqual(streams['weights-00001.bin'].read(), b'test-shard-1')
            return object()
        with self.assertRaises(ValueError):
            self.cache.load_admitted_model(self.name, replace, **self.inputs)
        self.assertFalse(self.cache.has_model(self.name))

    def test_cache_substitution_cannot_retain_provenance(self):
        self.cache.load_admitted_model(self.name, self.loader, **self.inputs)
        self.cache.models[self.name] = object()
        with self.assertRaises(gate.AdmissionError):
            self.cache.get_admitted_model(self.name, **self.inputs)

    def test_unknown_configuration_does_not_call_loader(self):
        self.inputs['workload']['quantization'] = 'int8'
        loader = MagicMock()
        with self.assertRaises(gate.AdmissionError):
            self.cache.load_admitted_model(self.name, loader, **self.inputs)
        loader.assert_not_called()

    def test_unbound_model_name_and_none_loader_are_refused(self):
        with self.assertRaises(gate.AdmissionError):
            self.cache.load_admitted_model('wrong model', self.loader, **self.inputs)
        with self.assertRaises(gate.AdmissionError):
            self.cache.load_admitted_model(self.name, lambda streams: None, **self.inputs)


if __name__ == '__main__':
    unittest.main()
