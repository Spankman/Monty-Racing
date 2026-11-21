"""Tests for persistent expert-source discovery."""
import unittest
from expert_consensus_experiment.source_discovery import load_registry, discovery_queue

class SourceDiscoveryTests(unittest.TestCase):
    def test_registry_has_multiple_sources(self):
        registry = load_registry()
        self.assertGreaterEqual(len(registry["sources"]), 14)
    def test_all_urls_https(self):
        for source in discovery_queue(load_registry()):
            self.assertTrue(source["url"].startswith("https://"))
    def test_priority_then_id(self):
        queue = discovery_queue(load_registry())
        self.assertEqual(queue, sorted(queue, key=lambda s: (s["priority"], s["source_id"])))
    def test_never_claims_fetched(self):
        self.assertTrue(all(s["collection_state"] == "NOT_FETCHED" for s in discovery_queue(load_registry())))
    def test_section_filter(self):
        queue = discovery_queue(load_registry(), include_homepage_only=False)
        self.assertTrue(all(s["verification_status"] != "homepage_only" for s in queue))
    def test_rejects_duplicate_ids(self):
        registry = load_registry()
        registry["sources"].append(dict(registry["sources"][0]))
        # Reuse validation by writing a temporary registry file.
        import tempfile, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sources.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)

if __name__ == "__main__":
    unittest.main()
