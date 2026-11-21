"""Regression tests for the snapshot execution wrapper (no live racing data)."""
import json
import tempfile
import unittest
from pathlib import Path
from integrations.run_snapshot import execute

class SnapshotTests(unittest.TestCase):
    def test_missing_snapshot_is_not_executed(self):
        with tempfile.TemporaryDirectory() as folder:
            s=execute("2026-11-18","",folder)
            self.assertFalse(s["model_executed"])
            self.assertEqual(s["status"],"DISCOVERY_ONLY_NO_RUNNER_SNAPSHOT")
            self.assertTrue((Path(folder)/"run_status.json").is_file())
            self.assertFalse((Path(folder)/"predictions.json").exists())
    def test_nonexistent_snapshot_is_not_executed(self):
        with tempfile.TemporaryDirectory() as folder:
            s=execute("2026-11-18","does-not-exist.json",folder)
            self.assertEqual(s["status"],"SNAPSHOT_NOT_FOUND")
    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                execute("2026-11-18","../private.json",folder)
    def test_invalid_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                execute("2026-02-30","",folder)

if __name__=="__main__":
    unittest.main()
