import unittest
import numpy as np
import pandas as pd
from .core import probability,fit,predict,calibrate,exotics,blend_expert,value_decision
from .evidence import join_evidence,blackbook_matches

class ProbabilityTests(unittest.TestCase):
    def test_extremes_and_group_sums(self):
        p=probability([1000,1001,-1000,-999],['a','a','b','b'])
        np.testing.assert_allclose(p[:2].sum(),1);np.testing.assert_allclose(p[2:].sum(),1)
    def test_train_transform_not_changed_by_test(self):
        X=np.array([[1,np.nan],[2,np.nan],[3,np.nan],[4,np.nan]])
        m=fit(X,np.array([1,0,0,1]),np.ones(4)*.5,['a','a','b','b'],['x','missing'],.1)
        before=str(m);p=predict(m,np.array([[np.nan,np.nan],[1e8,1e8]]),np.array([.5,.5]),['c','c'])
        self.assertEqual(before,str(m));self.assertAlmostEqual(p.sum(),1)
    def test_exotic_identities(self):
        top,q=exotics([.5,.3,.2],3)
        np.testing.assert_allclose(top,[1,1,1]);self.assertAlmostEqual(np.triu(q,1).sum(),1)
        p2,_=exotics([.5,.3,.2],2);self.assertAlmostEqual(p2.sum(),2)
        np.testing.assert_allclose(q,q.T);np.testing.assert_allclose(np.diag(q),0)
    def test_no_bet_and_expert_default(self):
        self.assertEqual(value_decision(.1,2)['decision'],'NO BET')
        np.testing.assert_equal(blend_expert([.6,.4],[.1,.9]),[.6,.4])
        with self.assertRaises(ValueError):blend_expert([.6,.4],[.1,.9],.5)
    def test_calibration_disjoint_function_no_labels_prediction(self):
        t=calibrate(np.array([.7,.3,.8,.2]),[1,0,1,0],['a','a','b','b'])
        self.assertTrue(.5<=t<=2)

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.r=pd.DataFrame([dict(race_id='r',runner_id='h',decision_at='2026-11-18T00:00:00Z',country='AU')])
        self.o=dict(race_id='r',runner_id='h',country='AU',feature='last600_seconds',value=35.2,
            source_url='https://example.test/report',published_at='2026-11-01T00:00:00Z',
            available_at='2026-11-01T00:00:00Z',captured_at='2026-11-17T00:00:00Z',
            event_at='2026-10-31T00:00:00Z',event_kind='prior_race',identity_verified=True)
    def test_prior_evidence(self):
        r,a=join_evidence(self.r,[self.o]);self.assertEqual(r.last600_seconds[0],35.2)
    def test_future_publication_rejected(self):
        r,a=join_evidence(self.r,[dict(self.o,available_at='2026-11-19T00:00:00Z')]);self.assertTrue(np.isnan(r.last600_seconds[0]))
    def test_current_race_results_rejected(self):
        r,a=join_evidence(self.r,[dict(self.o,event_at='2026-11-18T00:00:00Z')]);self.assertTrue(np.isnan(r.last600_seconds[0]))
    def test_duplicate_is_missing(self):
        r,a=join_evidence(self.r,[self.o,dict(self.o,value=34)]);self.assertTrue(np.isnan(r.last600_seconds[0]))
    def test_country_identity_and_weather(self):
        for change in [dict(country='NZ'),dict(identity_verified=False),dict(feature='forecast_rain_mm')]:
            r,a=join_evidence(self.r,[dict(self.o,**change)]);self.assertEqual(a[0]['status'],'REJECTED')
    def test_blackbook_scratchings_and_no_auto_bet(self):
        a=blackbook_matches([dict(horse="Bred ’em All",source_url='https://example.test',race_id='x',date='2026-11-18',scratched=True)])
        self.assertEqual(a[0]['status'],'SCRATCHED');self.assertFalse(a[0]['automatic_bet'])

if __name__=='__main__':unittest.main()
