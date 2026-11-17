import datetime as dt
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch
import urllib.error
import numpy as np
import pandas as pd
from history_bridge import build
from history_features import build_features as prediction_builder
from monty.features import build_features as original_builder
from krok_client import get,ProviderError

class HistoryBridgeTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for day in ['2026-11-15','2026-11-16']:
            for n in [1,2]:
                rows.append(dict(date=day,WIN_MARKET_ID=day,SELECTION_ID=str(n),SELECTION_NAME='Horse'+str(n),
                    TRACK='Test',DISTANCE=1200,market_probability=.5,barrier=n,jockey='J Smith',trainer='A Jones',
                    going='soft',class_text='BM58',BEST_AVAIL_BACK_AT_SCHEDULED_OFF=2,y=int(n==1)))
        return pd.DataFrame(rows)
    def test_exact_builder_parity_and_unknown_outcome(self):
        from history_bridge import prepare
        d=self.fixture();d['enriched_eligible']=True;d['name_key']=d.SELECTION_NAME.str.lower()
        from history_bridge import OPTIONAL
        for c in OPTIONAL:d[c]=np.nan
        _,expected,names=original_builder(d)
        h=d[d.date.eq('2026-11-15')];c=d[d.date.eq('2026-11-16')].drop(columns='y')
        rows,actual,got_names=build(h,c,'2026-11-16')
        self.assertEqual(names,got_names)
        np.testing.assert_allclose(actual,expected[2:],atol=0,rtol=0,equal_nan=True)
        self.assertTrue(rows.y.isna().all())
    def test_current_results_never_change_features(self):
        d=self.fixture();h=d.iloc[:2];c=d.iloc[2:].copy()
        a=build(h,c,'2026-11-16')[1];c['y']=1-c.y
        np.testing.assert_array_equal(a,build(h,c,'2026-11-16')[1])
    def test_future_history_rejected(self):
        d=self.fixture()
        with self.assertRaisesRegex(ValueError,'same-day'):build(d,d.iloc[2:],'2026-11-16')
    def test_incomplete_market_rejected(self):
        d=self.fixture()
        with self.assertRaisesRegex(ValueError,'unnormalized'):build(d.iloc[:1],d.iloc[2:],'2026-11-16')
    def test_equal_name_different_id_never_inherits_history(self):
        d=self.fixture();c=d.iloc[2:].copy();c.loc[c.index[0],'SELECTION_ID']='99'
        rows,X,names=build(d.iloc[:2],c,'2026-11-16')
        index=rows.index[rows.SELECTION_ID.eq('99')][0]
        self.assertEqual(X[index,names.index('observed_starts_log')],0)
    def test_bsp_is_not_accepted_as_historical_price_proxy(self):
        d=self.fixture();h=d.iloc[:2].drop(columns='BEST_AVAIL_BACK_AT_SCHEDULED_OFF');h['WIN_BSP']=2
        with self.assertRaisesRegex(ValueError,'BSP/SP'):build(h,d.iloc[2:],'2026-11-16')
    def test_inconsistent_quote_probability_rejected(self):
        d=self.fixture();h=d.iloc[:2].copy();h.loc[h.index[0],'BEST_AVAIL_BACK_AT_SCHEDULED_OFF']=3
        with self.assertRaisesRegex(ValueError,'disagree'):build(h,d.iloc[2:],'2026-11-16')

    def test_native_import_rejects_entire_race_with_missing_quote(self):
        from betfair_history import convert,COLUMNS
        rows=[]
        for n in range(1,5):
            r={key:'' for key in COLUMNS}
            r.update(LOCAL_MEETING_DATE='2026-10-01',SCHEDULED_RACE_TIME='12:00:00',ACTUAL_OFF_TIME='12:01:00',
                TRACK='Test',STATE_CODE='QLD',RACE_NO='1',WIN_MARKET_ID='1',RACING_TYPE='Thoroughbred',
                DISTANCE='1200',RACE_TYPE='BM58',SELECTION_ID=str(n),TAB_NUMBER=str(n),SELECTION_NAME='Horse'+str(n),
                WIN_RESULT='WINNER' if n==1 else 'LOSER',WIN_BSP='4',BEST_AVAIL_BACK_AT_SCHEDULED_OFF='4')
            rows.append(r)
        source=pd.DataFrame(rows);result,audit=convert(source)
        self.assertEqual(len(result),4);self.assertAlmostEqual(result.market_probability.sum(),1)
        source.loc[0,'BEST_AVAIL_BACK_AT_SCHEDULED_OFF']=''
        result,audit=convert(source);self.assertTrue(result.empty)
        self.assertEqual(audit['exclusions']['invalid_any_runner_quote'],1)

    def test_http_status_preserved_without_body_or_key(self):
        error=urllib.error.HTTPError('https://example',429,'secret-body',{'Retry-After':'60'},None)
        with patch('krok_client.urllib.request.urlopen',side_effect=error) as request:
            with self.assertRaises(ProviderError) as result:get('/api/v1/racing/field-form',{},'private-key')
            self.assertEqual(result.exception.status,429);self.assertEqual(result.exception.retry_after,'60')
            self.assertNotIn('private-key',str(result.exception));request.assert_called_once()

if __name__=='__main__':unittest.main()
