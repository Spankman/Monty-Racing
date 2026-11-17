import json,tempfile,unittest
from pathlib import Path
from collect_runners import collect
from import_fields import convert
from race_day import run
class Integration(unittest.TestCase):
 def test_feature_retention_and_scoring(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);date='2026-11-14'
   model=json.loads((Path(__file__).parent/'monty_v6/results/frozen_model.json').read_text())
   feat=next(x for x in model['input_feature_names'] if x not in ('market_probability','log_market_probability','log_field_size'))
   obj={'date':date,'races':[{'meeting':'TEST','race':'1','expected_active_runners':3}], 'runners':[{'meeting':'TEST','race':'1','number':str(i),'horse':f'Horse {i}','odds':v,feat:float(i)} for i,v in enumerate([2.5,4,7],1)]}
   src=p/'src.json';src.write_text(json.dumps(obj))
   collect(str(src),p/'raw.json',p/'manifest.json',date)
   audit=convert(p/'raw.json',p/'manifest.json',p/'runners.csv',p/'audit.json')
   self.assertTrue(audit['ready'],audit['issues'])
   self.assertIn(feat,(p/'runners.csv').read_text())
   scored=run(p/'runners.csv',p/'pred.csv')
   self.assertEqual(len(scored),3)
 def test_incomplete_race_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);obj={'date':'2026-11-14','races':[{'meeting':'TEST','race':'1','expected_active_runners':3}],'runners':[{'meeting':'TEST','race':'1','number':'1','horse':'Only','odds':2.5}]};src=p/'s.json';src.write_text(json.dumps(obj));collect(str(src),p/'raw.json',p/'m.json','2026-11-14');audit=convert(p/'raw.json',p/'m.json',p/'r.csv',p/'a.json');self.assertFalse(audit['ready']);self.assertFalse((p/'r.csv').exists())
if __name__=='__main__':unittest.main()
