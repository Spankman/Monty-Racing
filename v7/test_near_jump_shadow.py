from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from v7.near_jump_shadow import attempt
from v7.shadow import record_results
from v7.test_reconcile import DATE, inputs


class NearJumpShadowTests(unittest.TestCase):
    def test_freeze_and_record_late_scratching_separately(self):
        now = datetime.fromisoformat(DATE + "T02:58:00+00:00")
        with TemporaryDirectory() as temp:
            root = Path(temp)
            sources = inputs()
            captures = {}
            quote_time = DATE + "T02:56:00Z"
            for kind, src in zip(("krok", "fixtures", "quotes"), sources):
                src.update(published_at=quote_time, captured_at=quote_time)
                data = json.dumps(src).encode()
                raw = root / f"{kind}.json"
                raw.write_bytes(data)
                digest = hashlib.sha256(data).hexdigest()
                receipt = raw.with_suffix(".receipt.json")
                receipt.write_text(json.dumps(dict(raw_file=raw.name, raw_sha256=digest,
                                                    normalized_file=raw.name,
                                                    normalized_sha256=digest)))
                captures[kind] = receipt
            rows = [dict(race_id="tab", runner_id=f"t{i}", country="NZ", odds=odds,
                         source_url=sources[2]["source_url"],
                         odds_captured_at_utc=quote_time, scheduled_start_utc=DATE + "T03:00:00Z",
                         v6_probability=p, v7_probability=p, candidate2_probability=p,
                         market_probability=(1 / odds) / sum(1 / o for o in (2.5, 3.5, 5.0)))
                    for i, (odds, p) in enumerate(zip((2.5, 3.5, 5.0), (.5, .3, .2)), 1)]
            scored = root / "scored.json"
            scored.write_text(json.dumps(dict(rows=rows, models={})))
            params = dict(date=DATE, country="NZ", race_id="tab", scored=scored, **captures)
            for name, time in (("early", "02:55:00"), ("late", "02:59:01")):
                audit = attempt(**params, output=root / name,
                                now=datetime.fromisoformat(f"{DATE}T{time}+00:00"))
                self.assertIn("before " + ("decision" if name == "early" else "scheduled jump"), audit["reason"])
                self.assertFalse((root / name / "forecast.json").exists())
            missing = attempt(**dict(params, quotes=root / "missing"), output=root / "missing-data", now=now)
            self.assertEqual(missing["status"], "SKIPPED — NO BET")
            self.assertTrue((root / "missing-data" / "attempt.json").exists())
            result = attempt(**params, output=root / "verified", now=now)
            self.assertEqual(result["status"], "FROZEN — NO BET")
            forecast = root / "verified" / "forecast.json"
            original = forecast.read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), result["receipt"]["sha256"])
            self.assertEqual(json.loads(original)["fresh_evidence"]["cutoff_utc"],
                             DATE + "T02:59:00+00:00")
            settlement = record_results(
                forecast, [dict(race_id="tab", verified=True, source_url="https://example.test/result",
                                available_at=DATE + "T03:10:00Z", status="FINAL",
                                winner_runner_id="t2", scratched_runner_ids=["t1"])],
                root / "result.json", datetime(2030, 1, 3, tzinfo=timezone.utc),
                expected_sha256=result["receipt"]["sha256"])
            self.assertEqual(settlement["dispositions"]["tab"]["status"], "CHANGED_FIELD")
            self.assertFalse(settlement["probability_comparison"]["by_country"])
            self.assertEqual(original, forecast.read_bytes())
