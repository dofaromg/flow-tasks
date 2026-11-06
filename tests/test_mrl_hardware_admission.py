"""Compatibility tests for the single canonical MRL-34 admission gate."""

import unittest

from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import (
    MRL_hardware_admission_v1 as canonical,
)
from utils import mrl_hardware_admission as compatibility


class CanonicalAdmissionTests(unittest.TestCase):
    def test_compatibility_exports_use_the_product_gate(self):
        self.assertIs(compatibility.admit, canonical.evaluate)
        self.assertIs(compatibility.load_matrix, canonical.load_matrix)
        self.assertIs(compatibility.require_admission, canonical.require_admission)
        self.assertEqual(compatibility.DEFAULT_MATRIX, canonical.MATRIX)

    def test_release_matrix_has_separate_unknown_tracks_and_no_acceptance(self):
        matrix = canonical.load_matrix()
        routes = {route["bundle_id"]: route["track"] for route in matrix["routes"]}
        self.assertEqual(matrix["acceptances"], [])
        self.assertEqual(routes["MRL_APIWorks_BYOH_DL580_V100_CUDA12_v1"], "dl580-v100")
        self.assertEqual(routes["MRL_APIWorks_BYOH_Modern_NVIDIA_CUDA13_v1"], "modern-gpu")


if __name__ == "__main__":
    unittest.main()
