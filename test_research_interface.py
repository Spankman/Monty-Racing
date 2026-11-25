"""Math/schema fixtures only, not trained academic benchmarks or live forecasts."""
import tempfile,unittest
from pathlib import Path
import numpy as np
from operations.research_interface import *
class Research(unittest.TestCase):
    def setUp(self):self.p=ModelProvenance('2025-01-01','2025-02-01',True,'a'*64)
    def test_market_and_benter_identity(self):
        m=market_baseline([2,3,6],['r']*3);f=np.array([.4,.3,.3])
        np.testing.assert_allclose(benter_combination(f,m,['r']*3,form_coefficient=0,market_coefficient=1,provenance=self.p,test_start='2025-03-01'),m)
        np.testing.assert_allclose(benter_combination(f,m,['r']*3,form_coefficient=1,market_coefficient=0,provenance=self.p,test_start='2025-03-01'),f)
    def test_conditional_correction_is_not_independent_form(self):
        p=ModelProvenance('2025-01-01','2025-02-01',False,'a'*64)
        with self.assertRaises(ValueError):benter_combination([.5,.5],[.5,.5],['r','r'],form_coefficient=1,market_coefficient=1,provenance=p,test_start='2025-03-01')
    def test_future_training_production_and_target_columns_rejected(self):
        with self.assertRaises(ValueError):self.p.validate('2025-01-01')
        with self.assertRaises(ValueError):independent_form_columns(['barrier','WIN_BSP'])
        with self.assertRaises(ValueError):ModelProvenance('2025-01-01','2025-02-01',True,'a'*64,False).validate('2025-03-01')
    def test_adaptive_race_coherence(self):
        with self.assertRaises(ValueError):adaptive_combination([.4,.6],[.5,.5],['r','r'],weights=[.2,.3],provenance=self.p,test_start='2025-03-01')
        p=adaptive_combination([.4,.6],[.5,.5],['r','r'],weights=[.2,.2],provenance=self.p,test_start='2025-03-01');self.assertAlmostEqual(p.sum(),1)
    def test_ablation_does_not_mutate_original_and_calibration_normalises(self):
        x=np.array([[1.,2.],[3.,4.]]);y=ablate(x,['a','b'],['a']);self.assertTrue(np.isnan(y[:,0]).all());self.assertTrue(np.isfinite(x).all())
        np.testing.assert_allclose(calibrate([.7,.3],['r','r'],1,self.p,'2025-03-01'),[.7,.3])
    def test_walk_forward_no_overlap_or_unavailable_labels(self):
        rows=[dict(race_id='a',date='2025-01-01',result_verified=True,result_available_date='2025-01-02'),dict(race_id='b',date='2025-02-01',result_verified=True,result_available_date='2025-02-02'),dict(race_id='c',date='2025-03-01')]
        for row in rows:
            row['features_verified_asof']=True;row['feature_available_at']=row['date']+'T00:00:00Z';row['scheduled_start']=row['date']+'T01:00:00Z'
        folds=[dict(train_end='2025-01-31',calibration_start='2025-02-01',calibration_end='2025-02-28',test_start='2025-03-01',test_end='2025-03-31')]
        out=walk_forward(rows,folds)[0];self.assertEqual([out[k] for k in ['train','calibration','test']],[[0],[1],[2]])
        rows[0]['result_available_date']='2025-02-15'
        with self.assertRaises(ValueError):walk_forward(rows,folds)
    def test_experiment_record_append_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'run.json';r=dict(experiment_id='test',code_commit='a'*40,input_sha256='a'*64,status='NULL',protocol='synthetic contract',results_sha256='b'*64,limitations=['not a real experiment'])
            record_experiment(p,r)
            with self.assertRaises(FileExistsError):record_experiment(p,r)
if __name__=='__main__':unittest.main()
