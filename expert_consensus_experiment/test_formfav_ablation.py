import unittest
import pandas as pd
from expert_consensus_experiment.formfav_ablation import validate_pairs,sensitivity

class AblationTests(unittest.TestCase):
    def setUp(self):
        self.df=pd.DataFrame([
            {"meeting":"A","race":"1","number":"1","horse":"One","odds":2.5,"jockey_changed":1.0},
            {"meeting":"A","race":"1","number":"2","horse":"Two","odds":3.5,"jockey_changed":float("nan")}])
    def test_odds_change_is_rejected(self):
        altered=self.df.copy();altered.loc[0,"odds"]=2.6
        with self.assertRaises(ValueError):validate_pairs(self.df,altered)
    def test_missing_runner_is_rejected(self):
        with self.assertRaises(ValueError):validate_pairs(self.df,self.df.iloc[:1])
    def test_invalid_probability_mass_rejected(self):\n        def scorer(path,out):\n            frame=pd.read_csv(path,dtype={"meeting":str,"race":str,"number":str})\n            frame["monty_prob"]=[0.6,0.3]\n            return frame\n        with self.assertRaises(ValueError):sensitivity(self.df,scorer)\n    def test_changed_scored_odds_rejected(self):\n        def scorer(path,out):\n            frame=pd.read_csv(path,dtype={"meeting":str,"race":str,"number":str})\n            if frame.jockey_changed.notna().any():frame.loc[0,"odds"]=99\n            frame["monty_prob"]=[0.6,0.4]\n            return frame\n        with self.assertRaises(ValueError):sensitivity(self.df,scorer)\n    def test_identical_fields_pass(self):
        validate_pairs(self.df,self.df.copy())
    def test_paired_score_and_rank_change(self):
        def scorer(path,out):
            frame=pd.read_csv(path,dtype={"meeting":str,"race":str,"number":str})
            frame["monty_prob"]=[0.6,0.4] if frame.jockey_changed.isna().all() else [0.3,0.7]
            return frame
        report=sensitivity(self.df,scorer)
        self.assertEqual(report["runner_count"],2)
        self.assertEqual(report["enriched_feature_rows"],1)
        self.assertEqual(len(report["top_rank_changes"]),1)
        self.assertIsNone(report["accuracy_improvement"])
if __name__=="__main__":unittest.main()
