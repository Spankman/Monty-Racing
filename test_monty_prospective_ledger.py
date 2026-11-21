import unittest
from monty_prospective_ledger import validate

class TestLedger(unittest.TestCase):
    def setUp(self):
        self.row = dict(race_id="2026-11-21:AU:Cranbourne:6", version="V7",
            meeting="Cranbourne", race="6", number="11", horse="Example",
            captured_at="2026-11-21T02:00:00+00:00",
            scheduled_start="2026-11-21T03:00:00+00:00",
            fixed_win_odds="2.50", win_probability="0.35")
    def test_valid(self):
        self.assertEqual(validate([self.row]), 1)
    def test_after_start_rejected(self):
        self.row["captured_at"] = "2026-11-21T04:00:00+00:00"
        with self.assertRaises(ValueError): validate([self.row])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError): validate([self.row, self.row])
    def test_missing_timezone_rejected(self):
        self.row["captured_at"] = "2026-11-21T02:00:00"
        with self.assertRaises(ValueError): validate([self.row])
    def test_invalid_odds_rejected(self):
        self.row["fixed_win_odds"] = "1"
        with self.assertRaises(ValueError): validate([self.row])
if __name__ == "__main__":
    unittest.main()
