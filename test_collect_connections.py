import json,tempfile,unittest
from pathlib import Path
import pandas as pd
from collect_connections import collect

class CollectorTests(unittest.TestCase):
    def test_shared_people_fetched_once_per_window_and_cached(self):
        class Fake:
            def __init__(self):self.calls=[]
            def get(self,*args):return {'tier':'pro','remaining':20000}
            def stats(self,kind,name,window):self.calls.append((kind,name,window));return {}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cards=root/'cards';cards.mkdir()
            (cards/'belmont-1.json').write_text(json.dumps({'date':'2026-11-18','raceNumber':1,'runners':[
                {'number':1,'name':'Alpha','jockey':'Full Rider','trainer':'Full Trainer'},
                {'number':2,'name':'Beta','jockey':'Full Rider','trainer':'Full Trainer'}]}))
            inputs=pd.DataFrame([{'meeting':'Belmont','race':1,'number':1,'horse':'Alpha'},
                                 {'meeting':'Belmont','race':1,'number':2,'horse':'Beta'}])
            client=Fake();latest=pd.DataFrame({'market_id':[]})
            first=collect(inputs,cards,latest,root/'out','2026-11-18',client=client)
            second=collect(inputs,cards,latest,root/'out','2026-11-18',client=client)
            self.assertEqual(len(client.calls),4)
            self.assertEqual(first['requested'],4)
            self.assertEqual(second['statuses'],{'cached':4})

if __name__=='__main__':unittest.main()
