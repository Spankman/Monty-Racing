"""Regression checks for V7 fusion. Run: python -m unittest discover -s expert_consensus_experiment -p 'test_fusion_train.py'"""
import unittest
from expert_consensus_experiment.fusion_train import predict, walk_forward, _group

def race(day, race_id, winner=1, expert=False):
    return [
        {"race_date": day, "race_id": race_id, "number": str(i),
         "v6_probability": 0.5, "won": int(i == winner),
         "expert_requirement_satisfied": expert,
         "expert_top1_share": float(i == 1), "expert_top3_share": 1.0,
         "expert_coverage": 5}
        for i in (1, 2)]

class FusionTest(unittest.TestCase):
    def test_missing_expert_is_exact_baseline(self):
        field = race("2026-01-01", "A", expert=False)
        self.assertEqual(predict(field, [10, 20, 30]), predict(field, [0, 0, 0]))
    def test_normalization(self):
        self.assertAlmostEqual(sum(predict(race("2026-01-01", "A", expert=True), [1, 0, 0])), 1)
    def test_duplicate_runner_rejected(self):
        field = race("2026-01-01", "A")
        field[1]["number"] = "1"
        with self.assertRaises(ValueError):
            _group(field)
    def test_insufficient_history(self):
        rows = race("2026-01-01", "A") + race("2026-01-02", "B")
        self.assertEqual(walk_forward(rows, min_train_races=100)["status"], "INSUFFICIENT_HISTORICAL_DATA")
    def test_chronology(self):
        rows = race("2026-01-01", "A", expert=True) + race("2026-01-02", "B", expert=True)
        result = walk_forward(rows, min_train_races=1)
        self.assertEqual(result["folds"], 1)
        self.assertEqual(result["details"][0]["test_date"], "2026-01-02")
        self.assertEqual(result["details"][0]["train_races"], 1)
    def test_no_lookahead_same_day(self):
        rows = race("2026-01-01", "A") + race("2026-01-02", "B") + race("2026-01-02", "C")
        result = walk_forward(rows, min_train_races=1)
        self.assertEqual(result["details"][0]["train_races"], 1)
        self.assertEqual(result["details"][0]["test_races"], 2)

if __name__ == "__main__":
    unittest.main()
