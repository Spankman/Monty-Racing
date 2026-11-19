import tempfile,unittest
from pathlib import Path
import pandas as pd
from monty_expert_independence import audit

class IndependenceTests(unittest.TestCase):
 def test_same_author_two_sites_one_opinion(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'tips.csv'
   pd.DataFrame([
    dict(meeting='Mornington',race='7',number='2',source='Bets.com.au',author='Adam Cusworth'),
    dict(meeting='Mornington',race='7',number='2',source='Blackbook',author='Adam Cusworth'),
    dict(meeting='Mornington',race='7',number='2',source='Just Horse Racing',author='Adam Page')
   ]).to_csv(p,index=False)
   x=audit(p)['races'][0]
   self.assertEqual(x['published_sources'],3)
   self.assertEqual(x['provisional_independent_opinions'],2)
 def test_unknown_identical_picks_grouped(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'tips.csv'
   pd.DataFrame([
    dict(meeting='M',race='1',number='2',source='Site A',author=''),
    dict(meeting='M',race='1',number='2',source='Site B',author='')
   ]).to_csv(p,index=False)
   self.assertEqual(audit(p)['races'][0]['provisional_independent_opinions'],1)
if __name__=='__main__':unittest.main()
