import unittest
import pandas as pd
import race_day
from betfair_metadata import match_metadata,jockey_change

class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.rows=pd.DataFrame([dict(WIN_MARKET_ID='123',SELECTION_ID='1',SELECTION_NAME='Alpha',date='2026-10-01',TRACK='Gatton')])
        self.payload={'raceEventId':'1.123','day':'01-10-2026','venueName':'Gatton','runners':[
            {'selectionId':'1','runnerName':'Alpha','jockeyName':'Les Tilley'},
            {'selectionId':'2','runnerName':'Extra'}]}
    def test_extra_metadata_cannot_expand_retained_field(self):
        rows,extras=match_metadata(self.rows,self.payload)
        self.assertEqual(set(rows),{'1'});self.assertEqual(extras,['2'])
    def test_wrong_market_rejected(self):
        self.payload['raceEventId']='1.456'
        with self.assertRaises(ValueError):match_metadata(self.rows,self.payload)
    def test_wrong_name_rejected(self):
        self.payload['runners'][0]['runnerName']='Different'
        with self.assertRaises(ValueError):match_metadata(self.rows,self.payload)
    def test_wrong_date_rejected(self):
        self.payload['day']='02-10-2026'
        with self.assertRaises(ValueError):match_metadata(self.rows,self.payload)
    def test_jockey_change_requires_current_tab_booking(self):
        self.assertEqual(jockey_change('Damian Lane','Damian Lane','ALPHA (1)\nJD LaneTTrainer'),0)
        self.assertEqual(jockey_change('Les Tilley','Damian Lane','ALPHA (1)\nJD LaneTTrainer'),1)
        self.assertIsNone(jockey_change('Les Tilley','Damian Lane','ALPHA (1)\nJL CurrieTTrainer'))
    def test_abbreviation_not_assumed_a_new_person(self):
        self.assertIsNone(jockey_change('D Lane','Damian Lane','ALPHA (1)\nJD LaneTTrainer'))

if __name__=='__main__':unittest.main()
