"""Regression tests for Krok meeting pagination; no live credentials required."""
import json
import unittest
from unittest.mock import patch
from krok_adapter import fetch


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return self.payload


def meeting(venue):
    return {"date": "2026-11-22", "country": "AU", "venue": venue, "type": "T", "races": []}


class PaginationTests(unittest.TestCase):
    def run_pages(self, pages):
        urls = []
        def opener(req, timeout):
            urls.append(req.full_url)
            if not pages:
                raise AssertionError("Unexpected additional request")
            return FakeResponse(pages.pop(0))
        with patch("krok_adapter.urllib.request.urlopen", side_effect=opener):
            result = fetch("2026-11-22", "TEST_KEY_NOT_REAL")
        return result, urls

    def test_cursor_pagination_aggregates_all_meetings(self):
        pages = [
            {"success": True, "data": [meeting("A")], "meta": {"total": 2, "has_more": True, "truncated": True, "next_cursor": "abc"}},
            {"success": True, "data": [meeting("B")], "meta": {"total": 2, "has_more": False, "truncated": False}},
        ]
        result, urls = self.run_pages(pages)
        self.assertEqual([m["venue"] for m in result["data"]], ["A", "B"])
        self.assertEqual(result["meta"]["pages_fetched"], 2)
        self.assertIn("cursor=abc", urls[1])

    def test_repeated_cursor_fails_closed(self):
        pages = [
            {"success": True, "data": [meeting("A")], "meta": {"total": 3, "has_more": True, "next_cursor": "abc"}},
            {"success": True, "data": [meeting("B")], "meta": {"total": 3, "has_more": True, "next_cursor": "abc"}},
        ]
        with self.assertRaisesRegex(ValueError, "Repeated meeting pagination pointer"):
            self.run_pages(pages)

    def test_missing_continuation_fails_closed(self):
        pages = [{"success": True, "data": [meeting("A")], "meta": {"total": 2, "has_more": True, "truncated": True}}]
        with self.assertRaises(ValueError):
            self.run_pages(pages)

    def test_count_mismatch_fails_closed(self):
        pages = [{"success": True, "data": [meeting("A")], "meta": {"total": 2, "has_more": False}}]
        with self.assertRaisesRegex(ValueError, "Meeting count mismatch"):
            self.run_pages(pages)

    def test_duplicate_meeting_fails_closed(self):
        pages = [
            {"success": True, "data": [meeting("A")], "meta": {"total": 2, "has_more": True, "next_cursor": "abc"}},
            {"success": True, "data": [meeting("A")], "meta": {"total": 2, "has_more": False}},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate meeting"):
            self.run_pages(pages)


if __name__ == "__main__":
    unittest.main()
