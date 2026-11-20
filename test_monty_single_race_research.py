import csv
import tempfile
import unittest
from pathlib import Path
from monty_single_race_research import select

class TestSingleRace(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"scores.csv"
        with self.path.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["meeting","race","number","horse","research_prob","edge","odds","status"])
            w.writeheader()
            for n,horse,p in [(5,"Alpha",0.4),(2,"Beta",0.6)]:
                w.writerow(dict(meeting="Kilcoy",race="4",number=n,horse=horse,research_prob=p,edge=0,odds=3.5,status="UNAPPROVED RESEARCH — NO BET"))
    def tearDown(self):self.tmp.cleanup()
    def test_rank_and_status(self):
        out=select(self.path,"kilcoy",4)
        self.assertEqual(out["runners"][0]["number"],"2")
        self.assertIn("NO BET",out["status"])
    def test_missing_race_rejected(self):
        with self.assertRaises(ValueError):select(self.path,"Kilcoy",9)
    def test_unapproved_only(self):
        s=self.path.read_text().replace("UNAPPROVED RESEARCH — NO BET","BET")
        self.path.write_text(s)
        with self.assertRaises(ValueError):select(self.path,"Kilcoy",4)
if __name__=="__main__":unittest.main()
