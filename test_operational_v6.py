import unittest
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
    def test_missing_features_are_disclosed(self):
        out=score_operational(sample(),ROOT)
        self.assertTrue((out.feature_coverage<1).all())

if __name__=="__main__":unittest.main()
