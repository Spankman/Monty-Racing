"""Regression checks for fail-closed research runner identity auditing."""
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from research_daily_audit import assess

class ResearchDailyIdentityTests(unittest.TestCase):
    def check_rows(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scores=root/"scores.csv"
            pd.DataFrame(rows).to_csv(scores,index=False)
            model=root/"model.json"
            source=root/"source.json"
            model.write_text(json.dumps({"date":"2026-11-19","runners":len(rows),"races":1}))
            source.write_text(json.dumps({"runners_accepted":len(rows),"races_accepted":1}))
            return assess(scores,model,source)

    def rows(self):
        return [
            {"meeting":"TEST","race":1,"number":1,"horse":"Alpha","odds":3,
             "market_prob":0.5,"research_prob":0.5,"edge":0.5,
             "feature_coverage":0.5,"status":"UNAPPROVED RESEARCH — NO BET"},
            {"meeting":"TEST","race":1,"number":2,"horse":"Beta","odds":3,
             "market_prob":0.5,"research_prob":0.5,"edge":0.5,
             "feature_coverage":0.5,"status":"UNAPPROVED RESEARCH — NO BET"}]

    def test_distinct_runners_accepted(self):
        self.assertEqual(self.check_rows(self.rows())["approved_bets"],0)

    def test_duplicate_saddlecloth_rejected(self):
        rows=self.rows()
        rows[1]["number"]=1
        with self.assertRaisesRegex(ValueError,"Duplicate saddlecloth"):
            self.check_rows(rows)

    def test_duplicate_horse_rejected(self):
        rows=self.rows()
        rows[1]["horse"]="Alpha"
        with self.assertRaisesRegex(ValueError,"Duplicate horse"):
            self.check_rows(rows)

    def test_missing_identity_rejected(self):
        rows=self.rows()
        rows[1]["horse"]=None
        with self.assertRaisesRegex(ValueError,"Missing runner identity"):
            self.check_rows(rows)

if __name__=="__main__":
    unittest.main()
