"""Offline end-to-end V7 inference on synthetic fields only.

Synthetic names and odds are fixtures, NEVER racing selections.
"""
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from v7.run_single_race import execute

MODEL=Path(__file__).parent/"v7"/"artifacts"/"fold_3_model.json"

class V7SyntheticEndToEnd(unittest.TestCase):
    def test_real_v7_model_scores_complete_synthetic_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"synthetic.csv"
            pd.DataFrame([
                {"meeting":"SYNTHETIC","race":"99","number":str(i),
                 "horse":"SYNTHETIC TEST "+str(i),"odds":o}
                for i,o in enumerate((2.5,4.0,6.0,10.0),1)
            ]).to_csv(src,index=False)
            output=execute(src,date="2026-11-21",country="AU",
                source_url="https://example.org/synthetic-fixture",
                model_path=MODEL,output_dir=root/"out",
                independently_verified=True)
            scored=pd.read_csv(output)
            self.assertEqual(len(scored),4)
            self.assertAlmostEqual(float(scored.v7_win_probability.sum()),1,places=9)
            self.assertTrue(scored.deployment_decision.str.startswith("NO BET").all())
            self.assertTrue(scored.status.eq("EXPERIMENTAL_V7_NOT_APPROVED_REPLACEMENT").all())
            self.assertTrue((root/"out"/"quinella_estimates.csv").exists())

if __name__=="__main__":
    unittest.main()
