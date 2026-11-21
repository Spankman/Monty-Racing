import unittest
from v7.canonical_bridge import to_v7_fields

ROWS = [{"meeting":"Pukekohe","race":"6","number":str(i),"horse":"Horse "+str(i),"odds":float(i+2)} for i in range(1,5)]

class CanonicalBridgeTests(unittest.TestCase):
    def test_requires_independent_attestation(self):
        with self.assertRaises(ValueError):
            to_v7_fields(ROWS,date="2026-11-21",country="NZ",source_url="https://example.org")
    def test_valid_checked_field(self):
        out=to_v7_fields(ROWS,date="2026-11-21",country="NZ",source_url="https://example.org",field_verified=True)
        self.assertEqual(len(out),4)
        self.assertTrue(out.field_verified.all())
        self.assertEqual(out.race_id.iloc[0],"NZ|PUKEKOHE|6")
    def test_nonfinite_odds_rejected(self):
        for invalid in (float("inf"), float("nan")):
            rows=[dict(r) for r in ROWS]
            rows[0]["odds"]=invalid
            with self.assertRaises(ValueError):
                to_v7_fields(rows,date="2026-11-21",country="NZ",source_url="https://example.org",field_verified=True)
    def test_malformed_date_rejected(self):
        with self.assertRaises(ValueError):
            to_v7_fields(ROWS,date="tomorrow",country="NZ",source_url="https://example.org",field_verified=True)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            to_v7_fields(ROWS+[ROWS[0]],date="2026-11-21",country="NZ",source_url="https://example.org",field_verified=True)

if __name__=="__main__":
    unittest.main()
