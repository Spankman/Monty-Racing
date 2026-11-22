from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from v6_daily import publish, sha


class V6DailyTest(unittest.TestCase):
    def test_coverage_rank_and_receipt_for_pre_off_named_field(self):
        date = "2026-11-22"
        now = datetime(2026, 11, 22, 1, tzinfo=timezone.utc)
        jump = (now + timedelta(minutes=10)).isoformat()
        rows = [dict(meeting="Test", race="1", number=str(n), horse=f"Horse {n}", odds=price,
                     _price_source="TAB") for n, price in [(2, 4.0), (1, 5.0)]]
        snapshot = dict(date=date, runners=rows, races=[dict(meeting="Test", race="1")])
        payload = {"data": [dict(venue="Test", country="AU", type="T", date=date, races=[
            dict(number=1, status="open", jump_time=jump, runners=[dict(number=3, is_scratched=True)])
        ])]}
        assessment = dict(races=[dict(meeting="Test", race="1",
                                      reasons=["independent_fields_and_scratchings_unverified"])])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"provider_response.json").write_text(json.dumps(payload))
            (root/"assessment_bundle.json").write_text(json.dumps(
                dict(captured_at_utc=now.isoformat(), snapshot=snapshot, audit={})))
            def score(_source, _date, output):
                (Path(output)/"monty_selections.csv").write_text(
                    "meeting,race,number,horse,odds,monty_prob\nTest,1,1,Horse 1,5,0.3\n"
                    "Test,1,2,Horse 2,4,0.7\n")
            with patch("v6_daily.run", side_effect=score):
                card = publish(date, root, assessment, root/"daily", commit="test",
                               fixtures=dict(date=date, source="fixture", meetings={"TEST": 2}),
                               clock=lambda: now)
            self.assertEqual(card["counts"], {"PROVISIONAL": 1, "SKIPPED": 1})
            self.assertEqual(card["no_bet"], 2)
            self.assertEqual(card["races"][0]["provider_scratched"], ["3"])
            receipt = json.loads((root/"daily/receipt.json").read_text())
            forecast = json.loads((root/"daily/forecast.json").read_text())
            self.assertEqual(receipt["forecast_sha256"], sha(root/"daily/forecast.json"))
            self.assertEqual([row["number"] for row in forecast["rows"]], ["2", "1"])
            self.assertTrue(all(not row["bet_authorised"] for row in forecast["rows"]))
            self.assertIn("#2 Horse 2 $4.00", (root/"daily/report.md").read_text())
