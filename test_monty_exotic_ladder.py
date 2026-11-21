import unittest
from monty_exotic_ladder import exotic_ladder as ladder, research_display_ladder
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
 def test_report_display_stages(self):
  for odds,expected in [
   ([2,3,3,8],'F4 BOX'),([2,3,5,2],'TRI BOX'),
   ([2,4,2,2],'Q'),([4,2,2,2],'WIN')]:
   kind,picks=research_display_ladder([{'number':i+1,'odds':p} for i,p in enumerate(odds)])
   self.assertEqual(kind,expected)
   self.assertEqual(len(picks),{'WIN':1,'Q':2,'TRI BOX':3,'F4 BOX':4}[expected])
 def test_exactly_four_is_not_short(self):
  r=ladder(horse(1,4),[horse(2,2)],short_price_limit=4,verified=True)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN'])
 def test_second_at_four_stops_before_trifecta(self):
  r=ladder(horse(1,2),[horse(2,4),horse(3,2)],short_price_limit=4,verified=True)
  self.assertEqual([o['bet_type'] for o in r['options']],['WIN','QUINELLA'])
 def test_missing_threshold_fails(self):
  with self.assertRaises(ValueError):ladder(horse(1,2),[],short_price_limit=None,verified=True)
if __name__=='__main__':unittest.main()
