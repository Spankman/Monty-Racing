import unittest
from monty_exotic_ladder import exotic_ladder as ladder
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
 def test_exactly_four_is_not_short(self):
  r=ladder(horse(1,4),[horse(2,2)],short_price_limit=4,verified=True)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN'])
 def test_second_at_four_stops_before_trifecta(self):
  r=ladder(horse(1,2),[horse(2,4),horse(3,2)],short_price_limit=4,verified=True)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN','QUINELLA'])
 def test_missing_threshold_fails(self):
  with self.assertRaises(ValueError):ladder(horse(1,2),[],short_price_limit=None,verified=True)
if __name__=='__main__':unittest.main()
