import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from monty_expert_cache import validate, key, stamp

BASE={"date":"2026-11-20","track":"Kilcoy","race":4,"runner":"Example Horse","expert":"Example Expert","source_url":"https://example.org/tip","published_at":"2026-11-20T08:00:00+10:00","off_at":"2026-11-20T14:00:00+10:00"}
class CacheTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(BASE)["race"],4)
    def test_post_off_rejected(self):
        x={**BASE,"published_at":"2026-11-20T14:01:00+10:00"}
        with self.assertRaises(ValueError): validate(x)
    def test_naive_timestamp_rejected(self):
        x={**BASE,"published_at":"2026-11-20T08:00:00"}
        with self.assertRaises(ValueError): validate(x)
    def test_source_required(self):
        x={**BASE,"source_url":"http://example.org"}
        with self.assertRaises(ValueError): validate(x)
    def test_dedupe(self):
        self.assertEqual(key(BASE),key({**BASE,"track":"KILCOY"}))
if __name__=="__main__":unittest.main()
