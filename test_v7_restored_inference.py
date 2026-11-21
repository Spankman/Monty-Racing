"""Offline smoke checks for restored V7 Candidate 1 inference; no live bets."""
import json
import unittest
from pathlib import Path
import numpy as np
from v7.core import predict

MODEL = Path(__file__).parent / "v7" / "artifacts" / "fold_3_model.json"

class RestoredV7InferenceTests(unittest.TestCase):
    def test_saved_model_runs_with_missing_optional_features(self):
        model = json.loads(MODEL.read_text())
        self.assertEqual(len(model["names"]), len(model["medians"]))
        races = np.array(["NZ|TEST|6"] * 4)
        market = np.array([.4, .3, .2, .1])
        features = np.full((4, len(model["names"])), np.nan)
        if "log_market_probability" in model["names"]:
            features[:, model["names"].index("log_market_probability")] = np.log(market)
        if "log_field_size" in model["names"]:
            features[:, model["names"].index("log_field_size")] = np.log(4)
        result = predict(model, features, market, races)
        self.assertTrue(np.isfinite(result).all())
        self.assertTrue((result > 0).all())
        self.assertAlmostEqual(float(result.sum()), 1.0, places=10)

    def test_rejects_incomplete_market(self):
        model = json.loads(MODEL.read_text())
        features = np.full((3, len(model["names"])), np.nan)
        with self.assertRaises(ValueError):
            predict(model, features, [.5, .3, .1], ["race"] * 3)

if __name__ == "__main__":
    unittest.main()
