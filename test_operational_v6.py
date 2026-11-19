import unittest
import json
import tempfile
import subprocess
import sys
from unittest.mock import patch
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
    def test_restricted_research_flag_survives_scoring(self):
        data=sample()
        data["research_only_restricted_race"]=True
        out=score_operational(data,ROOT)
        self.assertTrue(out.research_only_restricted_race.all())
        self.assertFalse(out.betting_authorised.any())
    def test_restricted_research_flag_rejects_strings(self):
        data=sample()
        data["research_only_restricted_race"]=["False","False","False"]
        with self.assertRaisesRegex(ValueError,"must be booleans"):
            score_operational(data,ROOT)
    def test_market_edge_is_not_betting_roi(self):
        out=score_operational(sample(),ROOT)
        np.testing.assert_allclose(out.relative_market_edge.to_numpy(),
                                   out.monty_prob.to_numpy()/out.market_prob.to_numpy()-1)
        np.testing.assert_allclose(out.expected_win_roi.to_numpy(),
                                   out.monty_prob.to_numpy()*out.odds.to_numpy()-1)
        self.assertFalse(out.betting_authorised.any())
        self.assertNotIn("edge",out.columns)
    def test_invalid_odds(self):
        data=sample();data.loc[0,"odds"]=0.5
        with self.assertRaises(ValueError):score_operational(data,ROOT)
    def test_reject_single_runner_and_scratched_field(self):
        with self.assertRaisesRegex(ValueError,"at least two active runners"):
            score_operational(sample().iloc[:1],ROOT)
        data=sample()
        data["scratched"]=["yes","true","no"]
        with self.assertRaisesRegex(ValueError,"at least two active runners"):
            score_operational(data,ROOT)
    def test_scratched_missing_odds_excluded_before_active_validation(self):
        data=sample()
        data.loc[2,"scratched"]="yes"
        data.loc[:1,"scratched"]="no"
        data.loc[2,"odds"]=np.nan
        out=score_operational(data,ROOT)
        self.assertEqual(len(out),2)
        self.assertEqual(set(out.horse),{"A","B"})
        self.assertAlmostEqual(out.monty_prob.sum(),1,places=8)
        self.assertFalse(out.betting_authorised.any())
        data.loc[0,"odds"]=np.nan
        with self.assertRaisesRegex(ValueError,"Missing runner or odds"):
            score_operational(data,ROOT)
    def test_duplicate_runner(self):
        data=sample();data.loc[1,"number"]="1"
        with self.assertRaises(ValueError):score_operational(data,ROOT)
    def test_reject_invalid_race_and_saddlecloth_numbers(self):
        for field,value in (("race","0"),("race","R1"),("number","0"),("number","1A")):
            with self.subTest(field=field,value=value):
                data=sample()
                data.loc[0,field]=value
                with self.assertRaisesRegex(ValueError,"positive integers"):
                    score_operational(data,ROOT)
    def test_duplicate_horse_name_is_rejected(self):
        data=sample()
        data.loc[1,"horse"]=" a "
        with self.assertRaisesRegex(ValueError,"Duplicate horse identity"):
            score_operational(data,ROOT)
    def test_multiple_races(self):
        data=sample();other=sample().assign(race="2")
        out=score_operational(pd.concat([data,other],ignore_index=True),ROOT)
        self.assertTrue(np.allclose(out.groupby("race_id").monty_prob.sum(),1))
    def test_snapshot_bridge_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            snapshot=d/"snapshot.json"
            snapshot.write_text(json.dumps({
                "date":"2026-11-21",
                "runners":sample().to_dict(orient="records"),
                "races":[{"meeting":"TEST","race":"1","expected_active_runners":3}]
            }))
            output=d/"scored"
            cmd=[sys.executable,"operational/run_snapshot.py",str(snapshot),
                 "--output-dir",str(output)]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            predictions=pd.read_csv(output/"operational_predictions.csv")
            self.assertEqual(len(predictions),3)
            self.assertFalse(predictions.betting_authorised.any())
            self.assertAlmostEqual(predictions.monty_prob.sum(),1,places=8)
            record=json.loads((output/"prediction_record.json").read_text())
            provenance=json.loads((output/"snapshot_provenance.json").read_text())
            self.assertFalse(record["independent_field_verification_proven"])
            self.assertFalse(provenance["betting_authorised"])
            self.assertEqual(len(provenance["source_snapshot_sha256"]),64)
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)
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
            self.assertFalse(record["manifest_counts_are_source_assertions"])
            self.assertEqual(len(record["input_sha256"]),64)
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)
    def test_matches_frozen_v6_scoring_math_without_private_artifacts(self):
        # Patch only the integrity gate; the original V6 scoring math remains unchanged.
        from monty.scoring import score_features
        import json
        model=json.loads((ROOT/"results"/"frozen_model.json").read_text())
        names=model["input_feature_names"]
        data=sample()
        output=score_operational(data,ROOT)
        X=np.full((len(data),len(names)),np.nan)
        if "log_field_size" in names:
            X[:,names.index("log_field_size")]=np.log(len(data))
        if "log_market_probability" in names:
            X[:,names.index("log_market_probability")]=np.log(output.market_prob.to_numpy())
        with patch("monty.scoring.verify_artifacts",return_value=55):
            original=score_features(X,names,output.market_prob.to_numpy(),
                                    output.race_id.to_numpy(),root=ROOT)
        np.testing.assert_allclose(output.monty_prob.to_numpy(),original,rtol=1e-12,atol=1e-12)
    def test_parity_with_real_feature_values_and_two_races(self):
        from monty.scoring import score_features
        model=json.loads((ROOT/"results"/"frozen_model.json").read_text())
        names=model["input_feature_names"]
        data=pd.concat([sample(),sample().assign(race="2",odds=[3.0,5.0,7.0])],ignore_index=True)
        # Exercise real non-market features and missing-indicator handling.
        nonmarket=[n for n in names if n not in ("log_field_size","log_market_probability")]
        self.assertTrue(nonmarket)
        for n in nonmarket[:3]:
            data[n]=[0.2,np.nan,1.3,0.5,0.9,np.nan]
        output=score_operational(data,ROOT)
        X=np.full((len(data),len(names)),np.nan)
        for j,n in enumerate(names):
            if n in data:
                X[:,j]=pd.to_numeric(data[n],errors="coerce").to_numpy(float)
        if "log_field_size" in names:
            X[:,names.index("log_field_size")]=np.log(3)
        if "log_market_probability" in names:
            X[:,names.index("log_market_probability")]=np.log(output.market_prob.to_numpy())
        with patch("monty.scoring.verify_artifacts",return_value=55):
            original=score_features(X,names,output.market_prob.to_numpy(),
                                    output.race_id.to_numpy(),root=ROOT)
        np.testing.assert_allclose(output.monty_prob.to_numpy(),original,rtol=1e-12,atol=1e-12)
    def test_missing_features_are_disclosed(self):
        out=score_operational(sample(),ROOT)
        self.assertTrue((out.feature_coverage<1).all())

if __name__=="__main__":unittest.main()
