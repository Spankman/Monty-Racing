import datetime as dt
import unittest
from unittest.mock import patch
from assess_day import assess

class ReadinessTests(unittest.TestCase):
    def bundle(self):
        return {'captured_at_utc':'2026-11-17T03:00:00Z',
                'snapshot':{'date':'2026-11-17','runners':[{'meeting':'Test','race':'1','age':4}]},
                'races':[{'meeting':'Test','race':'1','jump_time':'2026-11-17T04:00:00Z'}], 'audit':{}}
    def check(self,b):
        with patch('assess_day.verify_artifacts',return_value=55), patch('assess_day.validate_model_contract',return_value=['age','prior_form','log_field_size']):
            return assess(b,dt.datetime(2026,11,17,3,1,tzinfo=dt.timezone.utc))['races'][0]
    def test_missing_form_never_becomes_betting_label(self):
        r=self.check(self.bundle())
        self.assertEqual(r['decision'],'BLOCKED')
        self.assertEqual(r['missing_features'],['prior_form'])
        self.assertEqual(r['fully_observed_active_features'],2)
    def test_elapsed_race_rejected_despite_open_status(self):
        b=self.bundle();b['races'][0]['jump_time']='2026-11-17T02:00:00Z'
        self.assertIn('race_already_due',self.check(b)['reasons'])
    def test_stale_capture_rejected(self):
        b=self.bundle();b['captured_at_utc']='2026-11-17T02:00:00Z'
        self.assertIn('snapshot_not_fresh',self.check(b)['reasons'])
    def test_missing_jump_and_nonfinite_feature_rejected(self):
        b=self.bundle();b['races']=[];b['snapshot']['runners'][0]['age']=float('nan')
        r=self.check(b)
        self.assertIn('jump_time_unverified',r['reasons']);self.assertIn('age',r['missing_features'])
    def test_future_capture_rejected(self):
        b=self.bundle();b['captured_at_utc']='2026-11-17T03:05:00Z'
        self.assertIn('snapshot_not_fresh',self.check(b)['reasons'])
    def test_positive_research_edge_cannot_emit_actionable_pick(self):
        import tempfile
        from pathlib import Path
        import numpy as np
        from race_day import run
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'runners.csv';target=Path(tmp)/'scores.csv'
            source.write_text('meeting,race,number,horse,odds\nTest,1,1,One,4\nTest,1,2,Two,4\n')
            with patch('race_day.score_features',return_value=np.array([0.5,0.5])):
                result=run(source,target)
            self.assertTrue((result['edge']>0).all())
            self.assertTrue((result['research_category']=='BEST BET').all())
            self.assertTrue((result['category']=='BLOCKED — RESEARCH ONLY').all())

    def test_timezone_required(self):
        b=self.bundle();b['captured_at_utc']='2026-11-17T03:00:00'
        with self.assertRaisesRegex(ValueError,'timezone'):self.check(b)

if __name__=='__main__':unittest.main()
