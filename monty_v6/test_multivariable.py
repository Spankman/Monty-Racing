import tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd
import run_multivariable as m
from gear import parse_gear_change

class MultivariableChecks(unittest.TestCase):
    def test_gear_event_is_separate_from_existing_gelding_status(self):
        self.assertTrue(np.isnan(parse_gear_change('Gelding')['first_after_gelding']))
        x=parse_gear_change('Blinkers FIRST TIME, Gelded',True)
        self.assertEqual(x['first_after_gelding'],1);self.assertEqual(x['blinkers_first'],1)
        self.assertEqual(parse_gear_change('Blinkers OFF FIRST TIME',True)['blinkers_first'],0)
        self.assertTrue(np.isnan(parse_gear_change(None)['blinkers_first']))
    def test_ampm_clock_recovery(self):
        self.assertEqual(m.full_clock_seconds('12:43:00 PM'),12*3600+43*60)
        self.assertEqual(m.full_clock_seconds('12:43:00 AM'),43*60)
        self.assertEqual(m.full_clock_seconds('13:01:02.000'),13*3600+62)
    def test_going_does_not_collapse_heavy_into_soft(self):
        self.assertEqual(m.condition('HVY 10'),'heavy');self.assertEqual(m.condition('SOFT6'),'soft');self.assertEqual(m.condition('GOOD4'),'good');self.assertEqual(m.condition('AWT'),'synthetic')
    def test_unknown_connections_are_not_real_people(self):
        self.assertEqual(m.clean_person('NOT NOTIFIED'),'');self.assertEqual(m.clean_person('Damian Lane'),'damianlane')
    def test_overlay_rejects_future_and_unknown_time(self):
        a=pd.DataFrame([dict(date='2025-01-01',track='Test',race=1,horse='A',source_url='https://example.org/source',published_at='2025-01-01T04:01:00Z',scheduled_start_utc='2025-01-01T04:00:00Z')])
        with self.assertRaises(ValueError):m.validate_overlay(a)
        a.published_at='2025-01-01T03:00:00Z';self.assertEqual(len(m.validate_overlay(a)),1)
        a.published_at=''
        with self.assertRaises(ValueError):m.validate_overlay(a)
    def fixture(self):
        rows=[]
        for date,mid in [('2025-01-01','1'),('2025-01-01','2'),('2025-01-02','3')]:
            for i in range(4):
                r=dict(date=date,WIN_MARKET_ID=mid,SELECTION_ID=str(i),name_key=str(i),TRACK='Test',DISTANCE=1200,SELECTION_NAME='Horse '+str(i),y=int(i==0),market_probability=.25,enriched_eligible=True,jockey='rider'+str(i),trainer='trainer',going='heavy',barrier=i+1,class_text='BM58',allocated_weight=58.,claim_kg=2.)
                for c in ['age','is_gelding','first_after_gelding','blinkers_first','blinkers_off','tongue_tie_first','winkers_first']:r[c]=np.nan
                rows.append(r)
        return pd.DataFrame(rows)
    def test_same_day_outcomes_do_not_change_connections_or_form(self):
        a=self.fixture();d,X,n=m.build_features(a);b=a.copy();b.loc[b.date.eq('2025-01-01'),'y']=1-b.loc[b.date.eq('2025-01-01'),'y'];_,Y,_=m.build_features(b)
        np.testing.assert_array_equal(X[:8],Y[:8]);self.assertFalse(np.array_equal(X[8:,n.index('jockey_year_residual')],Y[8:,n.index('jockey_year_residual')]))
    def test_current_weight_and_claim_and_unknown_gelding(self):
        _,X,n=m.build_features(self.fixture());self.assertEqual(X[0,n.index('effective_weight')],56.);self.assertTrue(np.isnan(X[0,n.index('first_after_gelding')]));self.assertTrue(np.isnan(X[0,n.index('is_gelding')]))
    def test_future_result_invariance(self):
        a=self.fixture();_,X,_=m.build_features(a);a.loc[a.date.eq('2025-01-02'),'y']=0;_,Y,_=m.build_features(a);np.testing.assert_array_equal(X,Y)
    def test_unknown_historical_distance_is_not_a_known_band(self):
        self.assertEqual(m.distance_band(np.nan),-1);self.assertEqual(m.distance_band(1200),3)
        a=self.fixture();a.loc[:3,'DISTANCE']=np.nan;a.loc[:3,'enriched_eligible']=False
        _,X,n=m.build_features(a);self.assertTrue(np.isfinite(X[:,n.index('observed_starts_log')]).all())

if __name__=='__main__':unittest.main()
