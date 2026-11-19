import json
import tempfile
import unittest
from pathlib import Path
from research_prediction_mode_record import record_prediction

class PredictionModeRecordTests(unittest.TestCase):
 def test_separate_create_only_records(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp)
   kw=dict(meeting='Mackay',race=9,selections=[{'number':3,'horse':'Example'}],
           source='FORM_ASSESSMENT',recorded_at_utc='2026-11-19T07:00:00Z')
   daily=record_prediction(base/'daily.json',mode='FULL_DAY',**kw)
   original=(base/'daily.json').read_bytes()
   single=record_prediction(base/'single.json',mode='SINGLE_RACE',parent_daily_id=daily['record_sha256'],**kw)
   self.assertEqual(original,(base/'daily.json').read_bytes())
   self.assertNotEqual(single['mode'],daily['mode'])
   self.assertEqual(single['parent_daily_id'],daily['record_sha256'])
   self.assertFalse(single['betting_authorised'])
   self.assertEqual(json.loads(original)['mode'],'FULL_DAY')
   with self.assertRaises(FileExistsError):
    record_prediction(base/'daily.json',mode='FULL_DAY',**kw)
 def test_invalid_inputs(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):
    record_prediction(Path(tmp)/'bad.json',mode='OTHER',meeting='A',race=1,
                      selections=[{'number':1,'horse':'X'}],source='V7',
                      recorded_at_utc='2026-11-19T07:00:00Z')
 def test_bad_timestamp_and_duplicate_selection(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=dict(mode='SINGLE_RACE',meeting='Mackay',race=9,source='V7',
             selections=[{'number':3,'horse':'Example'}])
   for bad in ('not-a-dateZ','2026-13-19T07:00:00Z','2026-11-19T07:00:00+10:00'):
    with self.subTest(bad=bad),self.assertRaises(ValueError):
     record_prediction(Path(tmp)/'bad.json',recorded_at_utc=bad,**base)
   with self.assertRaises(ValueError):
    record_prediction(Path(tmp)/'duplicate.json',recorded_at_utc='2026-11-19T07:00:00Z',
      **dict(base,selections=[{'number':3,'horse':'Example'},{'number':3,'horse':'EXAMPLE'}]))
if __name__=='__main__':unittest.main()
