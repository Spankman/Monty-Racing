import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
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
 def test_missing_or_redirected_robots_prevents_page_fetch(self):
  for status in (302, 404, 503):
   with self.subTest(status=status), patch('urllib.request.build_opener') as create:
    opener = create.return_value
    opener.open.side_effect = HTTPError('https://example.org/robots.txt', status, 'error', {}, None)
    result = discover('Test', 'https://example.org/tips')
    self.assertEqual(result['status'], 'unavailable')
    self.assertEqual(opener.open.call_count, 1)
    self.assertEqual(create.call_args.args[0].__class__.__name__, 'NoRedirects')

 def test_unsuitable_robots_response_is_not_permission(self):
  for content_type, body in [('text/html', b'<html>challenge</html>'), ('text/plain', b'x'*100001)]:
   with self.subTest(content_type=content_type), patch('urllib.request.build_opener') as create:
    response = MagicMock(headers={'Content-Type': content_type})
    response.read.return_value = body
    create.return_value.open.return_value.__enter__.return_value = response
    self.assertEqual(discover('Test', 'https://example.org/tips')['status'], 'unavailable')
    self.assertEqual(create.return_value.open.call_count, 1)
if __name__=='__main__':unittest.main()
