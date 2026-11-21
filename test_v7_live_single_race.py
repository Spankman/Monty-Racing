"""Offline integration test for the live Krok-to-V7 entry point."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from v7.run_live_single_race import live

class LiveSingleRaceTest(unittest.TestCase):
    def test_live_fetch_normalize_and_v7(self):
        snapshot={"date":"2026-11-21","races":[{"meeting":"Gosford","race":"1",
                    "expected_active_runners":4,"betting_authorised":False}],
                  "runners":[{"meeting":"Gosford","race":"1","number":str(i),
                    "horse":"Horse "+str(i),"odds":float(i+2),
                    "_price_source":"TAB","betting_authorised":False,
                    "research_only_restricted_race":True,
                    "race_classification_unknown":False} for i in range(1,5)]}
        audit={"races_accepted":1,"runners_accepted":4}
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"KROK_API_KEY":"test-key"}),patch("v7.run_live_single_race.fetch",return_value={"fixture":True}) as fetch,patch("v7.run_live_single_race.normalize",return_value=(snapshot,audit)) as normalize:
            result=live("Gosford","1",date="2026-11-21",country="AU",
                        output_dir=Path(tmp)/"result",allow_restricted=True)
            fetch.assert_called_once_with("2026-11-21","test-key")
            self.assertTrue(normalize.call_args.kwargs["include_restricted_flat_research"])
            self.assertEqual(len(result["ordered"]),4)
            self.assertEqual(result["status"],"PROVISIONAL_V7_PROVIDER_UNVERIFIED")
            self.assertFalse(result["betting_authorised"])
    def test_missing_key(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"KROK_API_KEY":""}):
            with self.assertRaisesRegex(ValueError,"KROK_API_KEY missing"):
                live("Gosford","1",date="2026-11-21",country="AU",output_dir=Path(tmp)/"out")

if __name__=="__main__":
    unittest.main()
