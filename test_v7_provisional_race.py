"""Smoke test: real V7 inference from a provider-shaped single race."""
import json
import tempfile
import unittest
from pathlib import Path
from v7.run_provisional_race import execute

class ProvisionalV7Test(unittest.TestCase):
    def test_actual_v7_scores_provisional_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            runners=[{"meeting":"Gosford","race":"1","number":str(i),
                      "horse":"Horse "+str(i),"odds":float(i+2),
                      "_price_source":"TAB","betting_authorised":False,
                      "research_only_restricted_race":True,
                      "race_classification_unknown":False}
                     for i in range(1,5)]
            snapshot={"date":"2026-11-21","races":[{"meeting":"Gosford","race":"1",
                                "expected_active_runners":4,
                                "betting_authorised":False}],
                      "runners":runners}
            src=root/"snapshot.json"
            src.write_text(json.dumps(snapshot))
            with self.assertRaises(ValueError):
                execute(src,"Gosford","1",date="2026-11-21",country="AU",
                        output_dir=root/"blocked")
            result=execute(src,"Gosford","1",date="2026-11-21",country="AU",
                           allow_restricted=True,output_dir=root/"scored")
            self.assertEqual(result["status"],"PROVISIONAL_V7_PROVIDER_UNVERIFIED")
            self.assertFalse(result["betting_authorised"])
            self.assertEqual(len(result["ordered"]),4)
            self.assertAlmostEqual(sum(x["v7_win_probability"] for x in result["ordered"]),1,places=6)
            self.assertTrue((root/"scored"/"v7_research_scores.csv").exists())
            ranked=result["ordered"]
            self.assertEqual(result["win_value_diagnostic"]["betting_decision"],"NO BET — provisional probabilities not prospectively validated")
            for horse in ranked:
                self.assertAlmostEqual(horse["model_expected_win_roi"],horse["v7_win_probability"]*horse["fixed_win_odds"]-1)
                self.assertAlmostEqual(horse["market_implied_probability"],1/horse["fixed_win_odds"])
            expected=[x["number"] for x in ranked[:4]]
            self.assertEqual(result["fixed_win_price_progression"]["numbers"],expected[:len(result["fixed_win_price_progression"]["numbers"])])
            self.assertIn(result["fixed_win_price_progression"]["type"],("WIN","QUINELLA","BOXED_TRIFECTA","BOXED_FIRST_FOUR"))

if __name__=="__main__":
    unittest.main()
