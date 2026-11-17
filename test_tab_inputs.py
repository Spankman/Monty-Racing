import copy
import datetime as dt
import unittest
from unittest.mock import patch
from tab_inputs import normalize
from assess_day import assess

class TabInputTests(unittest.TestCase):
    def capture(self):
        return dict(source_url='https://www.tab.com.au/racing/2026-11-17/TEST/TST/R/1',
            meeting='Test',captured_at_utc='2026-11-17T03:00:00Z',jump_time='2026-11-17T04:00:00Z',
            distance_m=1200,track_condition='Good (4)',class_text='BM56',declared_runners=3,
            runners=[dict(number='1',horse='One',barrier=1,fixed_win_text='2.00',tote_win=99),
                     dict(number='2',horse='Two',barrier=3,fixed_win_text='4.00',tote_win=1.1),
                     dict(number='3',horse='Three',barrier=4,fixed_win_text='SCR')])
    def test_fixed_win_only_and_scratchings(self):
        b=normalize(self.capture());rows=b['snapshot']['runners']
        self.assertEqual([r['odds'] for r in rows],[2,4])
        self.assertEqual(b['audit']['scratched_numbers'],['3'])
        self.assertEqual(rows[1]['barrier_fraction'],1.5)
        self.assertEqual(rows[1]['barrier_x_distance'],3/2*1200/1000)
        self.assertEqual(rows[0]['going_good'],1)
        self.assertNotIn('allocated_weight',rows[0])
    def test_no_tote_fallback_when_fixed_price_missing(self):
        c=self.capture();c['runners'][0]['fixed_win_text']=''
        with self.assertRaisesRegex(ValueError,'fixed win'):normalize(c)
    def test_declared_count_must_reconcile(self):
        c=self.capture();c['runners'].pop()
        with self.assertRaisesRegex(ValueError,'count'):normalize(c)
    def test_duplicate_saddlecloth_rejected(self):
        c=self.capture();c['runners'][1]['number']='1'
        with self.assertRaisesRegex(ValueError,'saddlecloth'):normalize(c)
    def test_elapsed_race_rejected(self):
        c=self.capture();c['jump_time']='2026-11-17T02:00:00Z'
        with self.assertRaisesRegex(ValueError,'already due'):normalize(c)
    def test_foreign_source_rejected(self):
        c=self.capture();c['source_url']=c['source_url'].replace('www.tab.com.au','other.example')
        with self.assertRaisesRegex(ValueError,'TAB'):normalize(c)
    def test_capture_only_removes_only_provider_timestamp_block(self):
        b=normalize(self.capture())
        now=dt.datetime(2026,11,17,3,1,tzinfo=dt.timezone.utc)
        with patch('assess_day.verify_artifacts',return_value=55):r=assess(b,now=now)['races'][0]
        self.assertNotIn('provider_quote_update_time_unverified',r['reasons'])
        self.assertIn('active_form_features_incomplete',r['reasons'])
        self.assertEqual(r['decision'],'BLOCKED')
        self.assertTrue(r['warnings'])
    def test_name_only_candidates_are_never_verified_joins(self):
        import pandas as pd
        from audit_history_identity import audit
        history=pd.DataFrame({'SELECTION_ID':['10','20'],'SELECTION_NAME':['One','One']})
        result=audit(normalize(self.capture()),history)
        self.assertEqual(result['verified_joins'],0)
        self.assertEqual(result['runners'][0]['status'],'ambiguous')
        self.assertEqual(result['runners'][1]['status'],'absent')

    def test_capture_only_still_rejects_stale_snapshot(self):
        b=normalize(self.capture())
        with patch('assess_day.verify_artifacts',return_value=55):
            r=assess(b,now=dt.datetime(2026,11,17,3,20,tzinfo=dt.timezone.utc))['races'][0]
        self.assertIn('snapshot_not_fresh',r['reasons'])

if __name__=='__main__':unittest.main()
