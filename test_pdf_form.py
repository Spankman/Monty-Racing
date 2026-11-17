import unittest
import numpy as np
import pandas as pd
import race_day  # establishes the original model package import path
from pdf_form import parse_text,match_start,last_start_features

TEXT='''Wednesday 18th November 2026
 Race 1 Example BENCHMARK 64 Handicap 1200m
 Horse Jockey Trainer Career
1. Example Horse     A Rider     A Trainer    2:1-1-0     1 58
 Speedmap:
                                                               Trainer A Trainer & B
                  1 EXAMPLE HORSE                              Trainer
              Jockey A Rider 58kg
 Career 2:1-1-0
 1 of 4 BLMT Thu 1Oct26 1000m BM64    Good4 A Rider    58.0 1 3.00 Example Horse 58kg 1.0L
 2 of 4 BLMT Fri 2Oct26 800m J/O 4    Good4 A Rider    n/a Test n/a
 1 of 4 BLMT Sat 3Oct26 800m MDN-     Soft A Rider     n/a Test n/a
'''

class PdfHistoryTests(unittest.TestCase):
    def test_trials_and_incomplete_rows_not_counted_as_race_form(self):
        races,runners,starts,quarantine=parse_text(TEXT,'Belmont','2026-11-18')
        self.assertEqual(len(runners),1)
        self.assertEqual(len(starts),1)
        self.assertEqual(starts[0]['date'],'2026-10-01')
        self.assertEqual(len(quarantine),1)

    def test_date_mismatch_rejected(self):
        with self.assertRaises(ValueError):parse_text(TEXT,'Belmont','2026-11-19')

    def test_unread_nonstandard_latest_start_is_quarantined(self):
        sample=TEXT+' PU BLMT Thu 5Nov26 1200m BM64 Good4 A Rider 58.0 1 3.00 Winner\n'
        self.assertTrue(any('PU BLMT' in x['raw_row'] for x in parse_text(sample,'Belmont','2026-11-18')[3]))

    def test_future_outcome_rejected(self):
        with self.assertRaises(ValueError):
            parse_text(TEXT.replace('1Oct26','18Nov26'),'Belmont','2026-11-18')

    def test_name_match_cannot_override_field_or_outcome(self):
        start=parse_text(TEXT,'Belmont','2026-11-18')[2][0]
        h=pd.DataFrame([dict(date='2026-10-01',TRACK='Belmont',DISTANCE=1000,
            SELECTION_NAME=n,WIN_MARKET_ID='one',y=int(i==0),BEST_AVAIL_BACK_AT_SCHEDULED_OFF=4)
            for i,n in enumerate(['Example Horse','B','C','D'])])
        self.assertEqual(match_start(start,h)[1],'matched_retained_market')
        self.assertEqual(match_start(start,h.iloc[:3])[1],'historical_field_size_disagrees')
        h.loc[0,'y']=0
        self.assertEqual(match_start(start,h)[1],'historical_outcome_disagrees')

    def test_original_last_start_formulas(self):
        s=dict(date='2026-11-11',distance_m=1000,class_text='BM64')
        f=last_start_features(s,1200,68,'2026-11-18')
        self.assertAlmostEqual(f['days_since_run_log'],np.log1p(7))
        self.assertEqual(f['quick_backup_7d'],1)
        self.assertEqual(f['up_200m'],1)
        self.assertEqual(f['benchmark_class_change'],4)

if __name__=='__main__':unittest.main()
