import unittest
from monty_settle_verified_wins import settle

class TestSettlement(unittest.TestCase):
    def setUp(self):
        self.p = dict(race_id="2026-11-21:AU:Test:1", version="V7", meeting="Test",
            race="1", number="4", horse="Example", captured_at="2026-11-21T01:00:00Z",
            scheduled_start="2026-11-21T02:00:00Z", fixed_win_odds="3.50",
            win_probability="0.30")
        self.r = dict(race_id=self.p["race_id"], number="4",
            finish_position="1", result_verified_at="2026-11-21T03:00:00Z")
    def test_win_profit(self):
        x = settle([self.p], [self.r])["V7"]
        self.assertEqual((x["bets"], x["wins"], x["profit"], x["roi_pct"]), (1,1,2.5,250))
    def test_loss(self):
        self.r["finish_position"] = "2"
        self.assertEqual(settle([self.p], [self.r])["V7"]["profit"], -1)
    def test_unverified_not_loss(self):
        self.assertEqual(settle([self.p], []), {})
    def test_early_result_rejected(self):
        self.r["result_verified_at"] = "2026-11-21T01:30:00Z"
        with self.assertRaises(ValueError): settle([self.p], [self.r])
    def test_duplicate_results_rejected(self):
        with self.assertRaises(ValueError): settle([self.p], [self.r,self.r])
if __name__ == "__main__": unittest.main()
