"""Compare observable race-day features with the unchanged training builder."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'monty_v6'))
from krok_adapter import normalize
from monty.features import build_features
from monty.normalization import condition

class AdapterParity(unittest.TestCase):
    def compare(self, going, distance=1200, barriers=(1,2,3,4)):
        from test_multivariable import MultivariableChecks
        d=MultivariableChecks().fixture().iloc[:4].copy()
        d['going']=condition(going);d['DISTANCE']=distance;d['barrier']=list(barriers)
        runners=[dict(number=i+1,name=r.SELECTION_NAME,is_scratched=False,
                      fixed_win=4.,barrier=r.barrier) for i,r in enumerate(d.itertuples())]
        payload={'success':True,'data':[dict(venue='Test',country='AU',type='T',date='2025-01-01',
          races=[dict(number=1,status='open',distance_m=distance,track_condition=going,runners=runners)])]}
        snapshot,_=normalize(payload,'2025-01-01')
        _,X,names=build_features(d)
        for i,row in enumerate(snapshot['runners']):
            for name in ['barrier_fraction','inside_three','outside_barrier','barrier_x_distance']:
                np.testing.assert_allclose(row.get(name,np.nan),X[i,names.index(name)],rtol=1e-12,atol=1e-12,err_msg=name)
            for g in ('good','soft','heavy','firm','synthetic','unknown'):
                name='going_'+g
                self.assertEqual(row[name],X[i,names.index(name)],name)
    def test_outside_threshold(self): self.compare('Soft 6')
    def test_distance_arithmetic(self): self.compare('Good4',distance=1357)
    def test_missing_going(self):
        for g in (None,'','unknown'):
            with self.subTest(g=g):self.compare(g)
    def test_going_aliases(self):
        for g in ('HVY10','AWT','FAST','SYNTHETIC','FIRM2','Heavy 9'):
            with self.subTest(g=g):self.compare(g)
    def test_missing_barrier(self): self.compare('Good 4',barriers=(0,2,3,4))

if __name__=='__main__':unittest.main()
