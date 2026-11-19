import unittest
from monty_expert_candidate_extract import extract

class CandidateExtractTests(unittest.TestCase):
 def test_explicit_tip(self):
  x=extract('<p>Best Bet: Race 7 #2 Chandler</p>','https://example.org/article')
  self.assertEqual(len(x),1)
  self.assertEqual((x[0]['race'],x[0]['number'],x[0]['horse_text']),('7','2','Chandler'))
  self.assertEqual(x[0]['status'],'CANDIDATE_ONLY_NOT_VERIFIED')
 def test_prose_not_a_tip(self):
  x=extract('<p>Chandler may improve in race seven but there are plenty of chances.</p>','https://example.org/article')
  self.assertEqual(x,[])
 def test_nav_ignored(self):
  x=extract('<nav><p>Best Bet: Race 7 #2 Chandler</p></nav>','https://example.org/article')
  self.assertEqual(x,[])
if __name__=='__main__':unittest.main()
