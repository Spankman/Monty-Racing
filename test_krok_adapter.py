import unittest
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from krok_adapter import normalize
class KrokAdapterTests(unittest.TestCase):
 def fixture(self):
  return {'success':True,'data':[{'venue':'Sample','country':'AU','date':'2026-11-14','type':'T','races':[{'number':1,'status':'open','distance':1200,'runner_count':3,'track_condition':'Soft 6','runners':[{'number':1,'name':'A','is_scratched':False,'fixed_win':3.5,'barrier':1},{'number':2,'name':'B','is_scratched':False,'fixed_win':4.5},{'number':3,'name':'C','is_scratched':True}]}]}],'meta':{'has_more':False}}
 def test_complete(self):
  s,a=normalize(self.fixture(),'2026-11-14');self.assertEqual(len(s['runners']),2);self.assertEqual(s['runners'][0]['distance_km'],1.2);self.assertEqual(s['runners'][0]['going_soft'],1)
 def test_missing_price_skips(self):
  f=self.fixture();del f['data'][0]['races'][0]['runners'][1]['fixed_win']
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_incomplete_race_diagnostics_keep_complete_races(self):
  f=self.fixture()
  incomplete=dict(f['data'][0]['races'][0])
  incomplete['number']=2
  incomplete['runners']=[dict(r) for r in incomplete['runners']]
  incomplete['runners'][0].pop('fixed_win')
  incomplete['runners'][1].pop('name')
  incomplete['runners'][1].pop('number')
  f['data'][0]['races'].append(incomplete)
  s,a=normalize(f,'2026-11-14')
  self.assertEqual(a['races_accepted'],1)
  self.assertEqual(a['runners_accepted'],2)
  self.assertEqual(len(a['incomplete_race_diagnostics']),1)
  diagnostic=a['incomplete_race_diagnostics'][0]
  self.assertEqual(diagnostic['meeting'],'Sample')
  self.assertEqual(diagnostic['race'],'2')
  self.assertEqual(diagnostic['missing_price'],1)
  self.assertEqual(diagnostic['missing_number'],1)
  self.assertEqual(diagnostic['missing_name'],1)
  self.assertFalse(diagnostic['class_label_present'])
  self.assertNotIn('runners',diagnostic)
  summary=a['incomplete_race_summary']
  self.assertEqual(summary['races'],1)
  self.assertEqual(summary['races_missing_price'],1)
  self.assertEqual(summary['races_missing_number'],1)
  self.assertEqual(summary['races_missing_name'],1)
  self.assertEqual(summary['missing_price_runner_slots'],1)
  self.assertEqual(summary['missing_number_runner_slots'],1)
  self.assertEqual(summary['missing_name_runner_slots'],1)
  self.assertEqual(diagnostic['price_status'],'partial_fixed_win_prices')
  self.assertEqual(summary['races_partial_fixed_win_prices'],1)
  self.assertEqual(summary['races_no_fixed_win_prices'],0)
  self.assertEqual(summary['races_prices_present_identity_incomplete'],0)
 def test_no_fixed_odds_available_is_separate_diagnostic(self):
  f=self.fixture()
  extra=dict(f['data'][0]['races'][0])
  extra['number']=2
  extra['runners']=[dict(r) for r in extra['runners']]
  for runner in extra['runners']:runner.pop('fixed_win',None)
  f['data'][0]['races'].append(extra)
  _,audit=normalize(f,'2026-11-14')
  self.assertEqual(audit['incomplete_race_summary']['races_no_fixed_win_prices'],1)
  self.assertEqual(audit['incomplete_race_diagnostics'][0]['price_status'],'no_fixed_win_prices')
  self.assertEqual(audit['races_accepted'],1)

 def test_prohibited_race_not_misreported_as_incomplete(self):
  f=self.fixture()
  prohibited=dict(f['data'][0]['races'][0])
  prohibited['number']=2
  prohibited['name']='Maiden Plate'
  prohibited['runners']=[dict(r) for r in prohibited['runners']]
  prohibited['runners'][0].pop('fixed_win')
  f['data'][0]['races'].append(prohibited)
  _,a=normalize(f,'2026-11-14')
  self.assertEqual(a['incomplete_race_diagnostics'],[])
  self.assertEqual(sum('prohibited race type' in x for x in a['skipped']),1)
 def test_full_page_without_end_marker_rejected(self):
  f=self.fixture();f['data']=[dict(f['data'][0],venue='Sample'+str(i)) for i in range(50)]
  f['meta']={}
  with self.assertRaisesRegex(ValueError,'50-meeting page limit'):
   normalize(f,'2026-11-14')
 def test_full_page_with_explicit_end_marker_allowed(self):
  f=self.fixture();f['data']=[dict(f['data'][0],venue='Sample'+str(i)) for i in range(50)]
  s,a=normalize(f,'2026-11-14')
  self.assertEqual(a['races_accepted'],50)
 def test_malformed_pagination_metadata_rejected(self):
  f=self.fixture();f['meta']=['not','metadata']
  with self.assertRaisesRegex(ValueError,'pagination metadata'):
   normalize(f,'2026-11-14')
 def test_malformed_meeting_record_rejected(self):
  f=self.fixture();f['data'].append(None)
  with self.assertRaisesRegex(ValueError,'meeting record'):
   normalize(f,'2026-11-14')
 def test_paginated_rejected(self):
  f=self.fixture();f['meta']['has_more']=True
  with self.assertRaises(ValueError):normalize(f,'2026-11-14')
 def test_prohibited_race_is_excluded(self):
  f=self.fixture();f['data'][0]['races'].append({'number':2,'name':'Two Year Old Maiden','status':'open','runners':f['data'][0]['races'][0]['runners']})
  s,a=normalize(f,'2026-11-14');self.assertEqual(len(s['races']),1);self.assertTrue(any('prohibited race type' in x for x in a['skipped']))
 def test_opt_in_flat_maiden_and_juvenile_are_research_only(self):
  f=self.fixture()
  f['data'][0]['races'][0]['name']='Two Year Old Maiden'
  s,a=normalize(f,'2026-11-14',include_restricted_flat_research=True)
  self.assertEqual(a['restricted_flat_research_races'],1)
  self.assertEqual(a['races_accepted'],1)
  self.assertTrue(s['races'][0]['research_only_restricted_race'])
  self.assertFalse(s['races'][0]['betting_authorised'])
  self.assertTrue(all(r['research_only_restricted_race'] and not r['betting_authorised'] for r in s['runners']))
 def test_jumps_still_excluded_in_research_mode(self):
  f=self.fixture()
  f['data'][0]['races'][0]['name']='Novice Hurdle'
  with self.assertRaisesRegex(ValueError,'No complete'):
   normalize(f,'2026-11-14',include_restricted_flat_research=True)
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
 def test_fixture_cli_to_provisional_predictions(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   fixture=root/'krok_fixture.json'
   fixture.write_text(json.dumps(self.fixture()))
   output=root/'out'
   result=subprocess.run([sys.executable,'krok_adapter.py','--date','2026-11-14',
     '--fixture',str(fixture),'--output-dir',str(output),'--provisional-operational'],
     capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   record=json.loads((output/'provisional_scored'/'prediction_record.json').read_text())
   provenance=json.loads((output/'provisional_scored'/'snapshot_provenance.json').read_text())
   self.assertEqual(record['runner_count'],2)
   self.assertEqual(record['race_count'],1)
   self.assertFalse(record['betting_authorised'])
   self.assertFalse(provenance['independent_field_verification_proven'])
   self.assertTrue((output/'provisional_scored'/'operational_predictions.csv').exists())
   rerun=subprocess.run([sys.executable,'krok_adapter.py','--date','2026-11-14',
     '--fixture',str(fixture),'--output-dir',str(output),'--provisional-operational'],
     capture_output=True,text=True)
   self.assertNotEqual(rerun.returncode,0)
if __name__=='__main__':unittest.main()
