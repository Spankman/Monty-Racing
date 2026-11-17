import csv, tempfile, unittest
from pathlib import Path
from backend_bridge import prepare
class BridgeTests(unittest.TestCase):
 def test_preview_and_freeze_guard(self):
  snapshot={'date':'2026-11-14','runners':[{'meeting':'Testville','race':'1','number':'2','horse':'Example','odds':4.0}]}
  audit={'race_count':1,'runner_count':1,'source_sha256':'abc','tab_verified':False}
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'scored.csv'
   with f.open('w',newline='') as h:
    w=csv.DictWriter(h,fieldnames=['meeting','race','number','monty_prob','odds','edge','category']);w.writeheader();w.writerow({'meeting':'Testville','race':'1','number':'2','monty_prob':0.3,'odds':4,'edge':0.2,'category':'BEST BET'})
   rows=prepare(snapshot,str(f),audit)
   self.assertEqual(len(rows['runners']),1)
   self.assertEqual(len(rows['monty_predictions']),0)
   with self.assertRaises(ValueError):prepare(snapshot,str(f),audit,freeze=True)
   audit['tab_verified']=True
   self.assertEqual(len(prepare(snapshot,str(f),audit,freeze=True)['monty_predictions']),1)
if __name__=='__main__':unittest.main()
