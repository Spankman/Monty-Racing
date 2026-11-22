import copy
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from historical_asof import utc_instant
from v7.reconcile import capture, reconcile
from v7.predict import run
import pandas as pd

DATE = "2030-01-02"
DECISION = DATE + "T02:00:00Z"


def inputs():
    runners = [
        dict(runner_id=f"t{i}", krok_runner_id=f"k{i}", number=str(i),
             horse=f"Example {i}", scratched=i == 4)
        for i in range(1, 5)
    ]
    tab = dict(country="NZ", race_id="tab", krok_race_id="krok", meeting="Example",
               number="1", scheduled_start=DATE + "T03:00:00Z", status="SCHEDULED",
               tier="country", classification="Benchmark 65", class_verified=True,
               going="Soft 5", runners=runners)
    krok = dict(tab, race_id="krok", runners=[
        dict(r, runner_id=r["krok_runner_id"]) for r in runners
    ])
    quotes = dict(country="NZ", race_id="tab", runners=[
        dict(runner_id="t1", fixed_win_odds=2.5), dict(runner_id="t2", fixed_win_odds=3.5),
        dict(runner_id="t3", fixed_win_odds=5.0)
    ])
    return tuple(dict(provider=name, source_url="https://www.tab.co.nz/racing" if name == "TAB"
                      else "https://example.test/" + name,
                      date=DATE, published_at=DATE + "T00:00:00Z",
                      captured_at=DATE + "T01:00:00Z", raw_sha256="a" * 64,
                      normalized_sha256="b" * 64, races=[race])
                 for name, race in zip(("Krok", "TAB", "ExampleBook"), (krok, tab, quotes)))


class ReconciliationTests(unittest.TestCase):
    def run_card(self, sources):
        return reconcile(*sources, date=DATE, decision_at=DECISION)

    def test_preserves_fixed_win_and_crosswalk(self):
        card = self.run_card(inputs())
        self.assertEqual(card["audit"][0]["status"], "VERIFIED")
        result, = card["verified"]
        self.assertEqual(result["country"], "NZ")
        self.assertEqual(result["runners"][0]["fixed_win_odds"], 2.5)
        self.assertEqual(result["scratched_runners"][0]["krok_runner_id"], "k4")
        self.assertEqual(card["sources"]["fixed_win"]["provider"], "ExampleBook")

    def test_disagreement_cannot_enter_verified_fields(self):
        for key, value in (("country", None), ("going", "Good 4"), ("status", "RESULTED")):
            with self.subTest(key=key):
                source = copy.deepcopy(inputs())
                source[0]["races"][0][key] = value
                card = self.run_card(source)
                self.assertFalse(card["verified"])
                self.assertEqual(card["audit"][0]["status"], "PROVISIONAL")
        source = inputs()
        source[0]["races"][0]["runners"][3]["scratched"] = False
        self.assertIn("scratching", self.run_card(source)["audit"][0]["reason"])

    def test_restricted_and_missing_logged(self):
        source = inputs()
        fixture = source[1]["races"][0]
        source[1]["races"].append(dict(fixture, number="2", race_id="missing", krok_race_id="absent"))
        fixture["classification"] = "2-Year-Old Maiden"
        self.assertEqual([r["status"] for r in self.run_card(source)["audit"]],
                         ["EXCLUDED", "MISSING"])

    def test_fixture_must_match_official_publisher_host_and_country(self):
        for provider, url in (
            ("Generic feed", "https://www.tab.co.nz/racing"),
            ("TAB", "https://example.test/racing"),
            ("TAB", "https://tab.co.nz.example.test/racing"),
            ("TAB", "https://tab.co.nz@example.test/racing"),
            ("TAB", "http://tab.co.nz/racing"),
            ("TAB", "https://tab.com.au/racing"),
        ):
            with self.subTest(provider=provider, url=url):
                source = inputs()
                source[1].update(provider=provider, source_url=url)
                card = self.run_card(source)
                self.assertEqual(card["verified"], [])
                self.assertEqual(card["audit"][0]["status"], "PROVISIONAL")
                self.assertIn("approved independent TAB", card["audit"][0]["reason"])

    def test_two_runner_race_does_not_stop_inference_for_verified_card(self):
        source = inputs()
        for capture_data in source:
            race = capture_data["races"][0]
            short = copy.deepcopy(race)
            short["race_id"] += "-short"
            short["number"] = "2"
            if "krok_race_id" in short:
                short["krok_race_id"] += "-short"
            if capture_data["provider"] == "ExampleBook":
                short["runners"].pop()
            else:
                short["runners"][2]["scratched"] = True
            capture_data["races"].append(short)
        card = self.run_card(source)
        self.assertEqual([entry["status"] for entry in card["audit"]], ["VERIFIED", "PROVISIONAL"])
        self.assertEqual(card["audit"][1]["reason"], "Need at least 3 active runners")
        model = Path(__file__).parent / "candidate2_artifacts" / "fold_3_candidate2.json"
        with TemporaryDirectory() as folder:
            output = Path(folder)
            path = output / "card.json"
            path.write_text(json.dumps(card))
            run(model, path, output)
            scored = pd.read_csv(output / "v7_research_scores.csv")
            self.assertEqual(scored["race_id"].tolist(), ["tab"] * 3)
            self.assertTrue(scored["deployment_decision"].str.startswith("NO BET").all())
            card["sources"]["fixtures"]["source_url"] = "https://example.test/racing"
            path.write_text(json.dumps(card))
            with self.assertRaisesRegex(ValueError, "approved independent TAB"):
                run(model, path, output)

    def test_capture_hash_and_cutoff(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            raw, normalized = b"archived provider response", json.dumps(inputs()[0]).encode()
            (root / "raw").write_bytes(raw)
            (root / "data").write_bytes(normalized)
            receipt = root / "receipt.json"
            receipt.write_text(json.dumps(dict(
                raw_file="raw", raw_sha256=hashlib.sha256(raw).hexdigest(),
                normalized_file="data", normalized_sha256=hashlib.sha256(normalized).hexdigest())))
            self.assertEqual(capture(receipt, utc_instant(DECISION))["provider"], "Krok")
            with self.assertRaisesRegex(ValueError, "available"):
                capture(receipt, utc_instant(DATE + "T00:30:00Z"))
            (root / "raw").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "digest"):
                capture(receipt, utc_instant(DECISION))
