import unittest
from expert_consensus_experiment.source_audit import audit_tips

def tip(origin, source="https://example.com/tips", runner="a", rank=1):
    return dict(race_id="r", runner_id=runner, expert_id=origin,
                analyst_origin_id=origin, source_url=source,
                published_at="2026-11-18T08:00:00+10:00", rank=rank)

class AuditTests(unittest.TestCase):
    def test_independent_minimum(self):
        rows=[tip("e"+str(i)) for i in range(5)]
        _, report=audit_tips(rows,"2026-11-18T09:00:00+10:00")
        self.assertTrue(report["races"]["r"]["feature_available"])
    def test_syndication_not_double_counted(self):
        rows=[tip("same","https://a.example/tips"),tip("same","https://b.example/tips")]
        _, report=audit_tips(rows,"2026-11-18T09:00:00+10:00")
        self.assertEqual(report["races"]["r"]["independent_experts"],1)
    def test_future_tip_rejected(self):
        row=tip("e")
        row["published_at"]="2026-11-18T10:00:00+10:00"
        eligible, report=audit_tips([row],"2026-11-18T09:00:00+10:00")
        self.assertEqual(eligible,[])
        self.assertEqual(len(report["rejected"]),1)
    def test_conflict_rejected(self):
        rows=[tip("e",runner="a"),tip("e",runner="b")]
        eligible, report=audit_tips(rows,"2026-11-18T09:00:00+10:00")
        self.assertEqual(eligible,[])
        self.assertTrue(report["rejected"])
if __name__=="__main__": unittest.main()
