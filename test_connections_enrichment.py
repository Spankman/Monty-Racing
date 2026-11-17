import datetime,json,tempfile,unittest
from pathlib import Path
import race_day
from connections_enrichment import supplement,stats_file

class SupplementalStatsTests(unittest.TestCase):
    binding={'meeting':'Belmont','race':1,'number':1,'horse':'Alpha','jockey':'Damian Lane'}
    def record(self,cache,**changes):
        data={'jockeyName':'Damian Lane','isAmbiguous':False,
              'recentStats':{'windowDays':90,'totalStarts':100,'totalWins':20,'overallWinRate':.2}}
        data.update(changes)
        stats_file(cache,'jockey','Damian Lane',90).write_text(json.dumps({'captured_at_utc':'2026-11-17T09:00:00Z','data':data}))
    def test_absent_stats_remain_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            result=supplement(self.binding,d)
            self.assertEqual(result['support_jockey_90d_status'],'unavailable')
            self.assertNotIn('support_jockey_90d_win_rate',result)
    def test_aggregate_never_becomes_model_residual(self):
        with tempfile.TemporaryDirectory() as d:
            self.record(d);result=supplement(self.binding,d)
            self.assertEqual(result['support_jockey_90d_win_rate'],.2)
            self.assertNotIn('jockey_90d_residual',result)
    def test_ambiguous_person_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            self.record(d,isAmbiguous=True);result=supplement(self.binding,d)
            self.assertEqual(result['support_jockey_90d_status'],'identity_unverified')
    def test_wrong_window_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            self.record(d,recentStats={'windowDays':365,'totalStarts':100});result=supplement(self.binding,d)
            self.assertEqual(result['support_jockey_90d_status'],'window_unverified')

if __name__=='__main__':unittest.main()
