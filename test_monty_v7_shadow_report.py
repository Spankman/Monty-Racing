import csv
import tempfile
import unittest
from pathlib import Path
from monty_v7_shadow_report import render

FIELDS = ["meeting","race","number","horse","odds","v7_shadow_prob","v7_status"]
STATUS = "UNAPPROVED V7 SHADOW — NO BET"

class ReportTests(unittest.TestCase):
    def make(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "v7.csv"
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def rows(self):
        return [
            dict(meeting="Ascot",race="1",number="2",horse="Runner B",odds="4.5",v7_shadow_prob="0.4",v7_status=STATUS),
            dict(meeting="Ascot",race="1",number="1",horse="Runner A",odds="2.1",v7_shadow_prob="0.6",v7_status=STATUS),
        ]

    def test_actual_rank_order_and_no_bet(self):
        report = render(self.make(self.rows()))
        self.assertLess(report.index("#1 Runner A"), report.index("#2 Runner B"))
        self.assertIn("NO BET", report)
        self.assertIn("60.0%", report)

    def test_rejects_duplicate(self):
        rows = self.rows()
        with self.assertRaises(ValueError):
            render(self.make(rows + [rows[0]]))

    def test_rejects_invalid_probability_total(self):
        rows = self.rows()
        rows[0]["v7_shadow_prob"] = "0.2"
        with self.assertRaises(ValueError):
            render(self.make(rows))

    def test_rejects_approved_bet_claim(self):
        rows = self.rows()
        rows[0]["v7_status"] = "BET"
        with self.assertRaises(ValueError):
            render(self.make(rows))

    def test_rejects_missing_odds(self):
        rows = self.rows()
        rows[0]["odds"] = ""
        with self.assertRaises(ValueError):
            render(self.make(rows))

if __name__ == "__main__":
    unittest.main()
