#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

from memory_archive_seed import MemoryArchiveSeed


class TestMemoryArchiveSeed(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.archive = MemoryArchiveSeed(storage_path=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_restore_and_compress_seed(self):
        particle_data = {"message": "你好，世界", "count": 1}

        created = self.archive.create_seed(
            particle_data=particle_data,
            metadata={"source": "unit-test"},
            seed_name="demo_seed",
        )
        restored = self.archive.restore_seed("demo_seed")
        compressed = self.archive.compress_seed("demo_seed")

        self.assertTrue(os.path.exists(created["seed_file"]))
        self.assertEqual(restored["particle_data"], particle_data)
        self.assertEqual(restored["metadata"]["source"], "unit-test")
        self.assertEqual(
            compressed,
            "MEMORY_SEED(demo_seed) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))",
        )

    def test_merge_export_and_import_seed(self):
        self.archive.create_seed({"id": 1}, seed_name="seed_a")
        self.archive.create_seed([{"id": 2}], seed_name="seed_b")

        merged = self.archive.merge_seeds(["seed_a", "seed_b"], merged_name="merged_seed")
        merged_seed = self.archive.restore_seed("merged_seed")
        exported_path = self.archive.export_seed("merged_seed")

        imported_archive_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, imported_archive_dir)
        imported_archive = MemoryArchiveSeed(storage_path=imported_archive_dir)
        imported = imported_archive.import_seed(exported_path)

        self.assertEqual(merged["seed_name"], "merged_seed")
        self.assertEqual(len(merged_seed["particle_data"]["particles"]), 2)
        self.assertTrue(os.path.exists(exported_path))
        self.assertEqual(imported["seed_name"], "merged_seed")


if __name__ == "__main__":
    unittest.main()
