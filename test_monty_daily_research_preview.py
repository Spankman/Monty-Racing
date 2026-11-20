import tempfile, unittest
from pathlib import Path
import pandas as pd
from monty_daily_research_preview import preview

class TestPreview(unittest.TestCase):
    def test_preview_is_unapproved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"scores.csv"
            pd.DataFrame([
                dict(meeting="Pakenham",race="8",number="2",horse="A",odds=2.2,research_prob=.7,status="UNAPPROVED RESEARCH — NO BET"),
                dict(meeting="Pakenham",race="8",number="10",horse="B",odds=5.5,research_prob=.3,status="UNAPPROVED RESEARCH — NO BET")
            ]).to_csv(p,index=False)
            out=preview(p)
            self.assertEqual(out.iloc[0].research_ladder,"QUINELLA BOXED")
            self.assertEqual(out.iloc[0].runner_numbers,"2-10")
            self.assertIn("NO BET",out.iloc[0].status)
    def test_rejects_approved_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"s.csv"
            pd.DataFrame([dict(meeting="A",race=1,number=1,horse="A",odds=3,research_prob=1,status="BET")]).to_csv(p,index=False)
            with self.assertRaises(ValueError):preview(p)
