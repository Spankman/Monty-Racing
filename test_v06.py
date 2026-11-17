import unittest
from krok_adapter import normalize

class FeatureTests(unittest.TestCase):
    def payload(self):
        return {'success':True,'data':[{'venue':'Example','country':'AU','date':'2026-11-14','type':'T','races':[{'number':1,'status':'open','distance':1200,'track_condition':'Good 4','runners':[{'number':1,'name':'A','is_scratched':False,'fixed_win':3.2,'barrier':1,'weight':57.5,'claim_kg':1.5},{'number':2,'name':'B','is_scratched':False,'fixed_win':4.2,'barrier':2}]}]}],'meta':{}}
    def test_derived_features(self):
        s,_=normalize(self.payload(),'2026-11-14')
        r=s['runners'][0]
        self.assertEqual(r['barrier_fraction'],0.5)
        self.assertEqual(r['inside_three'],1)
        self.assertEqual(r['effective_weight'],56)
        self.assertAlmostEqual(r['barrier_x_distance'],0.6)  # barrier / active field size * distance / 1000
    def test_cursor_pagination_refused(self):
        f=self.payload();f['meta']['next_cursor']='another-page'
        with self.assertRaisesRegex(ValueError,'paginated'):
            normalize(f,'2026-11-14')

if __name__=='__main__': unittest.main()
