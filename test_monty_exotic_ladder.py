import unittest
from monty_exotic_ladder import exotic_ladder as ladder, dividend_progression
def horse(n,odds,kind='BEST BET',qualified=True):
 return {'number':n,'odds':odds,'selection_type':kind,'qualified':qualified}
class LadderTests(unittest.TestCase):
 def test_full_ladder(self):
  r=ladder(horse(1,2),[horse(2,3),horse(3,3.5),horse(4,7)],short_price_limit=4,verified=True,stake_per_combination=1)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN','QUINELLA','BOXED TRIFECTA','BOXED FIRST FOUR'])
  self.assertEqual(r['options'][-1]['total_stake'],24)
 def test_roughie_win_only(self):
  r=ladder(horse(9,20,'RUFFY'),[horse(2,2)],short_price_limit=4,verified=True)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN'])
 def test_no_research_exotics(self):
  self.assertEqual(ladder(horse(1,2),[horse(2,2)],short_price_limit=4)['options'],[])
 def test_second_long_stops_at_quinella(self):
  r=ladder(horse(1,2),[horse(2,8),horse(3,2)],short_price_limit=4,verified=True)
  self.assertEqual(len(r['options']),2)
 def test_unqualified_not_padded(self):
  r=ladder(horse(1,2),[horse(2,2,qualified=False)],short_price_limit=4,verified=True)
  self.assertEqual(len(r['options']),1)
 def test_missing_threshold_fails(self):
  with self.assertRaises(ValueError):ladder(horse(1,2),[],short_price_limit=None,verified=True)
class DividendProgressionTests(unittest.TestCase):
 def test_escalates_on_actual_dividend_not_horse_win_odds(self):
  r=dividend_progression(horse(1,2),[horse(2,15),horse(3,20),horse(4,25)],
      quotes={'QUINELLA':5,'BOXED TRIFECTA':15,'BOXED FIRST FOUR':120},
      verified=True,min_return=100,stake_per_combination=1)
  self.assertEqual([o['bet_type'] for o in r['options']],
      ['WIN','QUINELLA','BOXED TRIFECTA','BOXED FIRST FOUR'])
  self.assertEqual(r['options'][-1]['total_stake'],24)
 def test_under_four_checks_quinella_even_if_win_return_exceeds_floor(self):
  r=dividend_progression(horse(1,3.5),[horse(2,6)],
      quotes={'QUINELLA':12},verified=True,min_return=2,stake_per_combination=1)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN','QUINELLA'])
 def test_exactly_four_does_not_force_quinella(self):
  r=dividend_progression(horse(1,4),[horse(2,6)],
      quotes={'QUINELLA':12},verified=True,min_return=2,stake_per_combination=1)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN'])
 def test_missing_dividend_stops_without_guessing(self):
  r=dividend_progression(horse(1,2),[horse(2,3),horse(3,4)],
      quotes={},verified=True,min_return=100,stake_per_combination=1)
  self.assertEqual(len(r['options']),1)
  self.assertIn('dividend unavailable',r['status'])
 def test_research_never_authorised(self):
  r=dividend_progression(horse(1,2),[],quotes={},min_return=100,stake_per_combination=1)
  self.assertEqual(r['options'],[])
 def test_no_threshold_no_bet(self):
  r=dividend_progression(horse(1,2),[],quotes={},verified=True,stake_per_combination=1)
  self.assertEqual(r['options'],[])
 def test_single_and_daily_use_identical_progression(self):
  from monty_single_race_policy import assess_single_race_progression
  from race_day import assess_daily_best_bet_progression
  kwargs=dict(quotes={'QUINELLA':110},verified=True,min_return=100,stake_per_combination=1)
  a=assess_single_race_progression(horse(1,2),[horse(2,5)],**kwargs)
  b=assess_daily_best_bet_progression(horse(1,2),[horse(2,5)],**kwargs)
  self.assertEqual(a,b)
  self.assertEqual(a['options'][-1]['bet_type'],'QUINELLA')
if __name__=='__main__':unittest.main()
