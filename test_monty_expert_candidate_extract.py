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
 def test_betting_prose_not_misread_as_separator(self):
  html='<p>Best betting tips</p><p>Value betting guide</p><p>Roughie of the day</p>'
  self.assertEqual(extract(html,'https://example.org/tips'),[])
 def test_nav_ignored(self):
  x=extract('<nav><p>Best Bet: Race 7 #2 Chandler</p></nav>','https://example.org/article')
  self.assertEqual(x,[])
 def test_multiple_explicit_tips_and_provenance(self):
  html='<article><p>Best Bet: Race 7 #2 Chandler</p><p>Roughie: Race 8 #11 Long Shot</p></article>'
  x=extract(html,'https://example.org/tips','Analyst One','2026-11-19T03:00:00+00:00')
  self.assertEqual(len(x),2)
  self.assertEqual([(v['race'],v['number']) for v in x],[('7','2'),('8','11')])
  self.assertTrue(all(v['author']=='Analyst One' and v['status']=='CANDIDATE_ONLY_NOT_VERIFIED' for v in x))
 def test_script_style_and_long_prose_ignored(self):
  html='<script>Best Bet: Race 7 #2 Chandler</script><style>Race 8: #4 Winner</style><p>'+('A'*150)+'</p>'
  self.assertEqual(extract(html,'https://example.org/tips'),[])
 def test_race_label_without_horse_rejected(self):
  self.assertEqual(extract('<p>Best Bet: Race 7 #2</p>','https://example.org/tips'),[])
if __name__=='__main__':unittest.main()
