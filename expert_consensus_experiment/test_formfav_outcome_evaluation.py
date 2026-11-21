import unittest
import pandas as pd
from expert_consensus_experiment.formfav_outcome_evaluation import evaluate

class FormFavOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.p=pd.DataFrame([
            dict(meeting="X",race="1",number="1",horse="Alpha",control_prob=.6,monty_prob=.4),
            dict(meeting="X",race="1",number="2",horse="Beta",control_prob=.4,monty_prob=.6)])
        self.o=pd.DataFrame([
            dict(meeting="X",race="1",number="1",horse="Alpha",finish_position=2,source_url="https://example.org/results"),
            dict(meeting="X",race="1",number="2",horse="Beta",finish_position=1,source_url="https://example.org/results")])
    def test_improvement(self):
        s,_=evaluate(self.p,self.o)
        self.assertLess(s["delta_log_loss"],0)
        self.assertEqual(s["enriched_top_wins"],1)
    def test_missing_runner(self):
        with self.assertRaises(ValueError):evaluate(self.p,self.o.iloc[:1])
    def test_duplicate_winner(self):
        o=self.o.copy();o.loc[0,"finish_position"]=1
        with self.assertRaises(ValueError):evaluate(self.p,o)
    def test_invalid_source(self):
        o=self.o.copy();o.loc[0,"source_url"]=""
        with self.assertRaises(ValueError):evaluate(self.p,o)
    def test_identity_mismatch(self):
        o=self.o.copy();o.loc[0,"horse"]="Wrong"
        with self.assertRaises(ValueError):evaluate(self.p,o)
if __name__=="__main__":unittest.main()
