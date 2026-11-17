import unittest,tempfile,json,csv
from pathlib import Path
from import_fields import convert
class TestIntake(unittest.TestCase):
 def test_good_and_scratch(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d)
   (d/'r.json').write_text(json.dumps([{'track':'Test','race_number':1,'saddlecloth':1,'horse_name':'Alpha','win_odds':2.5},{'track':'Test','race_number':1,'saddlecloth':2,'horse_name':'Beta','win_odds':4},{'track':'Test','race_number':1,'saddlecloth':3,'horse_name':'Gamma','status':'SCRATCHED'}]))
   (d/'m.json').write_text(json.dumps({'source':'user-supplied TAB snapshot','captured_at':'2026-11-14T08:00:00+10:00','races':[{'meeting':'Test','race':1,'expected_active_runners':2}]}))
   x=convert(d/'r.json',d/'m.json',d/'out.csv',d/'audit.json');self.assertTrue(x['ready']);self.assertEqual(len(list(csv.DictReader((d/'out.csv').read_text().splitlines()))),2)
   m=json.loads((d/'m.json').read_text());m['races'][0]['expected_active_runners']=3;(d/'m.json').write_text(json.dumps(m))
   x=convert(d/'r.json',d/'m.json',d/'out.csv',d/'audit.json');self.assertFalse(x['ready']);self.assertFalse((d/'out.csv').exists())
if __name__=='__main__':unittest.main()
