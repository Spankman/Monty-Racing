import datetime
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from monty_expert_article_capture import capture_article, process_leads, NoRedirects
from urllib.request import Request

NOW = datetime.datetime(2026,11,19,3,0,tzinfo=datetime.timezone.utc)
def clock(): return NOW
def fetch(url): return "<p>Best Bet: Race 7 #2 Chandler</p>"

class ArticleCaptureTests(unittest.TestCase):
    def test_capture_stays_unverified(self):
        result = capture_article("https://example.org/tips/",
            "https://example.org/tips/race7", fetcher=fetch,
            robots_allowed=lambda url: True, clock=clock)
        self.assertEqual(result["status"], "captured_unverified")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["status"], "CANDIDATE_ONLY_NOT_VERIFIED")
        self.assertEqual(result["candidates"][0]["captured_at"], NOW.isoformat())
    def test_cross_host_and_http_rejected_before_fetch(self):
        for url in ("http://example.org/tips/a", "https://other.org/tips/a", "https://example.org:bad/tips/a"):
            result = capture_article("https://example.org/tips/", url,
                fetcher=lambda u: self.fail("Should not fetch"),
                robots_allowed=lambda u: self.fail("Should not check robots"))
            self.assertEqual(result["status"], "rejected")
    def test_robots_denial_fails_closed(self):
        result = capture_article("https://example.org/tips/", "https://example.org/tips/a",
            fetcher=lambda u: self.fail("Should not fetch"), robots_allowed=lambda u: False)
        self.assertEqual(result["status"], "rejected")
    def test_large_page_unavailable(self):
        result = capture_article("https://example.org/tips/", "https://example.org/tips/a",
            fetcher=lambda u: "x"*400000, robots_allowed=lambda u: True)
        self.assertEqual(result["status"], "unavailable")
    def test_redirects_never_followed(self):
        self.assertIsNone(NoRedirects().redirect_request(
            Request("https://example.org/tips/a"), None, 302, "Found", {},
            "https://other.org/private"))
    def test_robots_redirect_cannot_trigger_article_fetch(self):
        with patch('urllib.request.build_opener') as create:
            opener = create.return_value
            opener.open.side_effect = HTTPError('https://example.org/robots.txt', 302, 'redirect', {}, None)
            result = capture_article('https://example.org/tips/', 'https://example.org/tips/a',
                                     fetcher=lambda url: self.fail('Article fetch after robots redirect'))
            self.assertEqual(result['status'], 'rejected')
            self.assertEqual(opener.open.call_count, 1)
            self.assertIsInstance(create.call_args.args[0], NoRedirects)

    def test_source_credentials_rejected(self):
        result = capture_article("https://user:pass@example.org/tips/",
            "https://example.org/tips/a",
            fetcher=lambda u: self.fail("Should not fetch"),
            robots_allowed=lambda u: self.fail("Should not check robots"))
        self.assertEqual(result["status"], "rejected")
    def test_processing_never_verifies(self):
        data={"sources":[{"source":"Just Horse Racing","articles":[{"url":"https://www.justhorseracing.com.au/tips/example"}]}]}
        result=process_leads(data,fetcher=fetch,robots_allowed=lambda u: True,clock=clock)
        self.assertEqual(result["verified_tip_count"],0)
        self.assertEqual(result["status"],"RESEARCH_ONLY_NO_BET")
        self.assertEqual(len(result["articles"]),1)

if __name__=="__main__": unittest.main()
