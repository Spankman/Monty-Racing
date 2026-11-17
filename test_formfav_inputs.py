import unittest
import pandas as pd
import race_day
from formfav_inputs import merge_card,reconcile_tab

class FormFavInputTests(unittest.TestCase):
    def setUp(self):
        self.frame=pd.DataFrame([dict(number=i,horse=n,barrier=i,odds=5,distance_km=1.2)
            for i,n in [(1,'Alpha'),(2,'Beta'),(3,'Gamma'),(4,'Delta')]])
        self.card={'distance':'1200m','raceClass':'BM68','condition':'Heavy 8','runners':[
            dict(number=i,name=n,barrier=i,weight=58,scratched=i==4)
            for i,n in [(1,'Alpha'),(2,'Beta'),(3,'Gamma'),(4,'Delta')]]}

    def test_scratching_recalculates_field_features(self):
        d=merge_card(self.frame,self.card)
        self.assertEqual(len(d),3)
        self.assertEqual(d.iloc[-1].barrier_fraction,1)
        self.assertEqual(d.going_heavy.sum(),3)
        self.assertEqual(d.claim_kg.sum(),0)

    def test_no_partial_odds_fields(self):
        with self.assertRaises(ValueError):merge_card(self.frame.iloc[:2],self.card)

    def test_no_saddlecloth_only_identity_join(self):
        self.card['runners'][0]['name']='Other Horse'
        with self.assertRaises(ValueError):merge_card(self.frame,self.card)

    def test_duplicate_source_runner_rejected(self):
        self.card['runners'].append(self.card['runners'][0])
        with self.assertRaises(ValueError):merge_card(self.frame,self.card)

    def observation(self):
        return {'url':'https://www.tab.com.au/racing/2026-11-18/BELMONT/BEL/R/1',
            'main_text':'Soft (5)','runners':[dict(id='runner-number-'+str(i),
            name=n+' ('+str(i)+')\nJ jockey T trainer',fixed_win='SCR' if i==2 else '5.00')
            for i,n in [(1,'Alpha'),(2,'Beta'),(3,'Gamma'),(4,'Delta')]]}

    def test_tab_authority_requires_full_identity_and_preserves_source(self):
        self.card.update(track='Belmont',date='2026-11-18',raceNumber=1)
        updated,quotes,audit=reconcile_tab(self.card,self.observation())
        self.assertTrue(updated['runners'][1]['scratched'])
        self.assertFalse(self.card['runners'][1]['scratched'])
        self.assertEqual(len(audit),2)
        self.assertEqual(updated['condition'],'Soft 5')

    def test_tab_override_rejects_other_race(self):
        self.card.update(track='Belmont',date='2026-11-18',raceNumber=2)
        with self.assertRaises(ValueError):reconcile_tab(self.card,self.observation())

    def test_tab_override_rejects_missing_runner(self):
        self.card.update(track='Belmont',date='2026-11-18',raceNumber=1)
        observation=self.observation();observation['runners'].pop()
        with self.assertRaises(ValueError):reconcile_tab(self.card,observation)

    def test_tab_override_rejects_changed_horse_at_same_number(self):
        self.card.update(track='Belmont',date='2026-11-18',raceNumber=1)
        observation=self.observation();observation['runners'][0]['name']='Wrong Horse (1)'
        with self.assertRaises(ValueError):reconcile_tab(self.card,observation)

if __name__=='__main__':unittest.main()
