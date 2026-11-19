import unittest
import json
import tempfile
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from operational.v6_operational_scorer import score_operational

ROOT=Path("monty_v6")
def sample():
    return pd.DataFrame({"meeting":["TEST"]*3,"race":["1"]*3,
                         "number":["1","2","3"],"horse":["A","B","C"],
                         "odds":[2.5,4.0,8.0]})
class OperationalV6Tests(unittest.TestCase):
    def test_probabilities_and_no_bet(self):
        out=score_operational(sample(),ROOT)
        self.assertAlmostEqual(out.monty_prob.sum(),1,places=8)
        self.assertTrue((out.monty_prob>0).all())
        self.assertFalse(out.betting_authorised.any())
        self.assertTrue(out.status.str.startswith("PROVISIONAL").all())
    def test_invalid_odds(self):
        data=sample();data.loc[0,"odds"]=0.5
        with self.assertRaises(ValueError):score_operational(data,ROOT)
    def test_duplicate_runner(self):
        data=sample();data.loc[1,"number"]="1"
        with self.assertRaises(ValueError):score_operational(data,ROOT)
    def test_multiple_races(self):
        data=sample();other=sample().assign(race="2")
        out=score_operational(pd.concat([data,other],ignore_index=True),ROOT)
        self.assertTrue(np.allclose(out.groupby("race_id").monty_prob.sum(),1))
    def test_cli_manifest_rejects_incomplete_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            source=d/"runners.csv"
            sample().to_csv(source,index=False)
            manifest=d/"races.json"
            manifest.write_text(json.dumps({"races":[{"meeting":"TEST","race":"1","expected_active_runners":4}]}))
            result=subprocess.run([sys.executable,"operational/run_operational.py",str(source),
                "--output-dir",str(d/"out"),"--race-manifest",str(manifest)],
                capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("Incomplete or unexpected",result.stderr)
            self.assertFalse((d/"out"/"prediction_record.json").exists())
    def test_cli_writes_create_only_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            source=d/"runners.csv"
            sample().to_csv(source,index=False)
            cmd=[sys.executable,"operational/run_operational.py",str(source),"--output-dir",str(d/"out")]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            record=json.loads((d/"out"/"prediction_record.json").read_text())
            self.assertFalse(record["betting_authorised"])
            self.assertFalse(record["pre_off_proven"])
            self.assertEqual(len(record["input_sha256"]),64)
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)
    def test_missing_features_are_disclosed(self):
        out=score_operational(sample(),ROOT)
        self.assertTrue((out.feature_coverage<1).all())

if __name__=="__main__":unittest.main()
