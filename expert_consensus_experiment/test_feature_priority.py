import unittest
from expert_consensus_experiment.feature_priority import rank_feature_groups
class PriorityTests(unittest.TestCase):
    def test_ablation(self):
        folds=[{"y":[1,0],"baseline":[0.8,0.2],"without":{"form":[0.5,0.5],"noise":[0.9,0.1]}},
               {"y":[0,1],"baseline":[0.2,0.8],"without":{"form":[0.5,0.5],"noise":[0.1,0.9]}}]
        ranked=rank_feature_groups(folds)
        self.assertEqual(ranked[0]["group"],"form")
        self.assertEqual(ranked[0]["priority"],"high")
        self.assertEqual(ranked[1]["priority"],"low")
if __name__=="__main__": unittest.main()
