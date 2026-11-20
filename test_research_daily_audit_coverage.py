"""Regression tests for daily coverage transparency and fail-closed reporting."""
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from research_daily_audit import assess

class DailyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.scores=root/"scores.csv"
        self.model=root/"model.json"
        self.source=root/"source.json"
        pd.DataFrame([
            dict(meeting="Pakenham",race="1",number="1",horse="A",odds=2.5,market_prob=.5,research_prob=.6,edge=.5,feature_coverage=.8,status="UNAPPROVED RESEARCH — NO BET"),
            dict(meeting="Pakenham",race="1",number="2",horse="B",odds=3.5,market_prob=.5,research_prob=.4,edge=.4,feature_coverage=.7,status="UNAPPROVED RESEARCH — NO BET"),
        ]).to_csv(self.scores,index=False)
        self.model.write_text(json.dumps(dict(date="2026-11-20",runners=2,races=1)))
        self.source.write_text(json.dumps(dict(runners_accepted=2,races_accepted=1,meetings=2,skipped=["Other R1: missing runners"])))
    def test_reports_feed_gaps_without_claiming_complete_coverage(self):
        out=assess(self.scores,self.model,self.source)
        self.assertEqual(out["feed_meetings_seen"],2)
        self.assertEqual(out["meetings_without_accepted_races"],1)
        self.assertEqual(out["accepted_meeting_names"],["Pakenham"])
        self.assertEqual(out["skipped_race_count"],1)
        self.assertFalse(out["complete_AU_NZ_coverage_verified"])
        self.assertFalse(out["independent_TAB_verified"])
        self.assertEqual(out["approved_bets"],0)
    def test_rejects_impossible_feed_meeting_count(self):
        data=json.loads(self.source.read_text())
        data["meetings"]=0
        self.source.write_text(json.dumps(data))
        with self.assertRaises(ValueError):assess(self.scores,self.model,self.source)
    def test_rejects_bad_skipped_audit(self):
        data=json.loads(self.source.read_text())
        data["skipped"]=[123]
        self.source.write_text(json.dumps(data))
        with self.assertRaises(ValueError):assess(self.scores,self.model,self.source)

if __name__=="__main__":
    unittest.main()
