"""Offline end-to-end contract test for provisional single-race value output."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from .run_provisional_race import execute


class ProvisionalRaceValueContract(unittest.TestCase):
    def test_selection_artifact_includes_value_without_betting_approval(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            snapshot = root / "snapshot.json"
            snapshot.write_text(json.dumps({"date": "2026-11-21"}))
            out = root / "output"

            def fake_stage(snapshot_path, meeting, race, path, **kwargs):
                pd.DataFrame([
                    {"meeting": meeting, "race": race, "number": "1", "horse": "Favourite", "odds": 2.0},
                    {"meeting": meeting, "race": race, "number": "2", "horse": "Value Horse", "odds": 8.0},
                    {"meeting": meeting, "race": race, "number": "3", "horse": "Third", "odds": 5.0},
                ]).to_csv(path, index=False)

            def fake_predict(model_path, input_path, output_dir, **kwargs):
                pd.DataFrame([
                    {"runner_id": "1", "horse": "Favourite", "fixed_win_odds": 2.0, "v7_win_probability": .45},
                    {"runner_id": "2", "horse": "Value Horse", "fixed_win_odds": 8.0, "v7_win_probability": .20},
                    {"runner_id": "3", "horse": "Third", "fixed_win_odds": 5.0, "v7_win_probability": .10},
                ]).to_csv(Path(output_dir) / "v7_research_scores.csv", index=False)

            with patch("v7.run_provisional_race.stage", side_effect=fake_stage), patch(
                "v7.run_provisional_race.run", side_effect=fake_predict
            ):
                result = execute(snapshot, "Test Track", "6", date="2026-11-21",
                                 country="AU", output_dir=out)
            saved = json.loads((out / "provisional_selection.json").read_text())
            self.assertEqual(saved, result)
            self.assertTrue(result["scored_at_utc"].endswith("Z"))
            self.assertIsNone(result["provider_odds_captured_at_utc"])
            self.assertFalse(result["pre_race_evidence_verified"])
            self.assertEqual(result["ordered"][0]["number"], "1")
            self.assertEqual(result["provisional_value_candidate"]["number"], "2")
            self.assertFalse(result["provisional_value_candidate"]["betting_authorised"])
            self.assertFalse(result["betting_authorised"])
            self.assertEqual(result["fixed_win_price_progression"]["numbers"], ["1", "2"])
            self.assertIn("NO BET", result["win_value_diagnostic"]["betting_decision"])

if __name__ == "__main__":
    unittest.main()
