import unittest
import pandas as pd
from run_verified_v6 import run
from race_day import ROOT
from monty.integrity import ArtifactError, verify_artifacts

class FrozenV6EndToEndTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for day in ('2026-11-19','2026-11-20'):
            for n in (1,2):
                rows.append(dict(date=day,WIN_MARKET_ID=day,SELECTION_ID=str(n),
                    SELECTION_NAME='Horse'+str(n),TRACK='Test',DISTANCE=1200,
                    market_probability=.5,barrier=n,jockey='J Smith',trainer='A Jones',
                    going='soft',class_text='BM58',BEST_AVAIL_BACK_AT_SCHEDULED_OFF=2,
                    y=int(n==1)))
        return pd.DataFrame(rows)
    def test_frozen_v6_research_run(self):
        d=self.fixture()
        try:
            verify_artifacts(ROOT)
        except ArtifactError as exc:
            # The public checkout omits frozen artifacts. Never bypass integrity
            # or manufacture a passing frozen-model score.
            with self.assertRaisesRegex(ArtifactError,'Missing artifact'):
                run(d.iloc[:2],d.iloc[2:].drop(columns=['y']),'2026-11-20')
            return
        out=run(d.iloc[:2],d.iloc[2:].drop(columns=['y']),'2026-11-20')
        self.assertEqual(len(out),2)
        self.assertAlmostEqual(out.v6_probability.sum(),1)
        self.assertFalse(out.betting_authorised.any())
        self.assertTrue(out.status.eq('FROZEN_V6_RESEARCH_ONLY').all())
    def test_unverified_results_prices_cannot_substitute(self):
        d=self.fixture()
        h=d.iloc[:2].drop(columns=['BEST_AVAIL_BACK_AT_SCHEDULED_OFF'])
        h['starting_price']=2
        with self.assertRaisesRegex(ValueError,'scheduled-off'):
            run(h,d.iloc[2:],'2026-11-20')

if __name__=='__main__':unittest.main()
