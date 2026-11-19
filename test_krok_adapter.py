import unittest
from krok_adapter import normalize
class KrokAdapterTests(unittest.TestCase):
 def fixture(self):
  return {'success':True,'data':[{'venue':'Sample','country':'AU','date':'2026-11-14','type':'T','races':[{'number':1,'status':'open','distance':1200,'runner_count':3,'track_condition':'Soft 6','runners':[{'number':1,'name':'A','is_scratched':False,'fixed_win':3.5,'barrier':1},{'number':2,'name':'B','is_scratched':False,'fixed_win':4.5},{'number':3,'name':'C','is_scratched':True}]}]}],'meta':{'has_more':False}}
 def test_complete(self):
  s,a=normalize(self.fixture(),'2026-11-14');self.assertEqual(len(s['runners']),2);self.assertEqual(s['runners'][0]['distance_km'],1.2);self.assertEqual(s['runners'][0]['going_soft'],1)
 def test_missing_price_skips(self):
  f=self.fixture();del f['data'][0]['races'][0]['runners'][1]['fixed_win']
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_paginated_rejected(self):
  f=self.fixture();f['meta']['has_more']=True
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_prohibited_race_is_excluded(self):
  f=self.fixture();f['data'][0]['races'].append({'number':2,'name':'Two Year Old Maiden','status':'open','runners':f['data'][0]['races'][0]['runners']})
  s,a=normalize(f,'2026-11-14');self.assertEqual(len(s['races']),1);self.assertTrue(any('prohibited race type' in x for x in a['skipped']))
 def test_uncertain_scratching_rejected(self):
  f=self.fixture();f['data'][0]['races'][0]['runners'][1].pop('is_scratched')
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_duplicate_race_key_rejected(self):
  f=self.fixture()
  f['data'][0]['races'].append(dict(f['data'][0]['races'][0]))
  with self.assertRaisesRegex(ValueError,'Duplicate meeting/race'):
   normalize(f,'2026-11-14')
 def test_duplicate_race_key_across_meetings_rejected(self):
  f=self.fixture()
  f['data'].append(dict(f['data'][0]))
  with self.assertRaisesRegex(ValueError,'Duplicate meeting/race'):
   normalize(f,'2026-11-14')
 def test_in_play_and_unknown_statuses_rejected(self):
  for status in ('running','jumped','interim',None,'final'):
   f=self.fixture();f['data'][0]['races'][0]['status']=status
   with self.subTest(status=status),self.assertRaises(ValueError):
    normalize(f,'2026-11-14')
 def test_prohibited_class_variants_rejected(self):
  for label in ('MDN PLATE','Novice Chase','Jumps Flat Race','Juvenile Stakes','2-Y-O Handicap'):
   f=self.fixture();f['data'][0]['races'][0]['name']=label
   with self.subTest(label=label),self.assertRaises(ValueError):
    normalize(f,'2026-11-14')
 def test_all_two_year_old_runners_rejected(self):
  f=self.fixture()
  for r in f['data'][0]['races'][0]['runners']:r['age']=2
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_mixed_price_sources_rejected(self):
  f=self.fixture()
  f['data'][0]['races'][0]['runners'][0]['odds']=[{'bookmaker':'TAB','win':3.5}]
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_wrong_date_rejected(self):
  with self.assertRaises(ValueError):normalize(self.fixture(),'2026-11-15')
if __name__=='__main__':unittest.main()
