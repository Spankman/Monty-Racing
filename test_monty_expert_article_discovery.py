import unittest
from monty_expert_article_discovery import discover,SOURCES

class ArticleDiscoveryTests(unittest.TestCase):
 def test_multiple_established_sources_registered(self):
  for name in ('Racenet','Punters','Racing.com','TAB NZ','RacingBase'):
   self.assertIn(name,SOURCES)
 def test_leads_are_not_tips(self):
  html='<a href="/tips/mornington-preview">Mornington tips</a><a href="https://outside.example/tips">External tips</a>'
  result=discover('Test','https://example.org/',fetcher=lambda url:html)
  self.assertEqual(result['status'],'located')
  self.assertEqual(len(result['articles']),1)
  self.assertEqual(result['articles'][0]['status'],'located_unverified')
 def test_reject_http(self):
  with self.assertRaises(ValueError):
   discover('Test','http://example.org/',fetcher=lambda url:'')
if __name__=='__main__':unittest.main()
