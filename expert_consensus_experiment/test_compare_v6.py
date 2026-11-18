import unittest
from expert_consensus_experiment.compare_v6 import compare

def row(number, probability):
    return dict(meeting="Sandown", race="2", number=number, horse="Horse "+number,
                monty_prob=probability, feature_coverage=0.4)

def tip(i, runner):
    return dict(race_id="SANDOWN|2", runner_id=runner, expert_id="e"+str(i),
                analyst_origin_id="e"+str(i), source_url="https://example.org/tip",
                published_at="2026-11-18T08:00:00+10:00", rank=1)

class CompareTests(unittest.TestCase):
    def test_five_experts_joined_without_fake_fusion(self):
        rows, audit=compare([row("1",0.7),row("2",0.3)],
                            [tip(i,"2") for i in range(5)],
                            "2026-11-18T09:00:00+10:00")
        self.assertEqual(rows[0]["v6_probability"],0.7)
        self.assertEqual(rows[1]["expert_top1_share"],1.0)
        self.assertEqual(rows[0]["status"],"RESEARCH_ONLY_UNTRAINED_FUSION")
        self.assertNotIn("combined_probability",rows[0])
    def test_insufficient_experts(self):
        rows, _=compare([row("1",0.7)], [tip(i,"1") for i in range(4)],
                        "2026-11-18T09:00:00+10:00")
        self.assertFalse(rows[0]["expert_requirement_satisfied"])
        self.assertIsNone(rows[0]["expert_top1_share"])

if __name__=="__main__": unittest.main()
