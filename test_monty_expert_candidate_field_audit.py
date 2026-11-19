import json
import tempfile
import unittest
from pathlib import Path
from monty_expert_candidate_field_audit import audit

class FieldAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "scores.csv"
        self.path.write_text("meeting,race,number,horse\nAlbury,3,12,Cool Idol\nDoomben,7,2,Chandler\n")
    def tearDown(self):
        self.tmp.cleanup()
    def candidate(self, race, number, horse):
        return {"articles":[{"candidates":[{"race":race,"number":number,"horse_text":horse,
            "status":"CANDIDATE_ONLY_NOT_VERIFIED"}]}]}
    def test_exact_match_stays_unverified(self):
        x=audit(self.candidate("3","12","Cool Idol"),self.path)
        self.assertEqual(x["field_matches"],1)
        self.assertEqual(x["verified_tip_count"],0)
        self.assertEqual(x["candidates"][0]["status"],"UNVERIFIED_NO_BET")
        self.assertEqual(x["candidates"][0]["meeting_candidate"],"Albury")
    def test_wrong_horse_rejected(self):
        self.assertEqual(audit(self.candidate("3","12","Wrong Horse"),self.path)["field_matches"],0)
    def test_missing_race_rejected(self):
        self.assertEqual(audit(self.candidate(None,"12","Cool Idol"),self.path)["field_matches"],0)
    def test_ambiguous_meetings_rejected(self):
        with self.path.open("a") as f: f.write("Mackay,3,12,Cool Idol\n")
        self.assertEqual(audit(self.candidate("3","12","Cool Idol"),self.path)["field_matches"],0)

if __name__=="__main__": unittest.main()
