"""Offline tests for provisional prediction audit (no provider or secret)."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from operational.verify_provisional_output import verify


class ProvisionalAuditTests(unittest.TestCase):
    def make_output(self, directory):
        root = Path(directory)
        record = {
            "status": "PROVISIONAL_OPERATIONAL_V6",
            "betting_authorised": False,
            "pre_off_proven": False,
            "independent_field_verification_proven": False,
            "artifact_integrity_verified": False,
            "runner_count": 2,
            "race_count": 1,
        }
        provenance = {"betting_authorised": False, "independent_field_verification_proven": False}
        rows = [
            {"race_id": "TEST|1", "number": "1", "horse": "Alpha", "odds": "2.5", "monty_prob": "0.6", "market_prob": "0.5", "betting_authorised": "False"},
            {"race_id": "TEST|1", "number": "2", "horse": "Beta", "odds": "3.0", "monty_prob": "0.4", "market_prob": "0.5", "betting_authorised": "False"},
        ]
        self.write(root, record, provenance, rows)
        return record, provenance, rows

    @staticmethod
    def write(root, record, provenance, rows):
        (root / "prediction_record.json").write_text(json.dumps(record))
        (root / "snapshot_provenance.json").write_text(json.dumps(provenance))
        with (root / "operational_predictions.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_valid_provisional_output(self):
        with tempfile.TemporaryDirectory() as temp:
            self.make_output(temp)
            self.assertEqual(verify(temp)["runners"], 2)

    def test_rejects_authorised_betting_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            record, provenance, rows = self.make_output(temp)
            rows[0]["betting_authorised"] = "True"
            self.write(Path(temp), record, provenance, rows)
            with self.assertRaisesRegex(ValueError, "betting-authorised"):
                verify(temp)

    def test_rejects_incorrect_probability_sum(self):
        with tempfile.TemporaryDirectory() as temp:
            record, provenance, rows = self.make_output(temp)
            rows[0]["monty_prob"] = "0.7"
            self.write(Path(temp), record, provenance, rows)
            with self.assertRaisesRegex(ValueError, "Probabilities"):
                verify(temp)

    def test_rejects_duplicate_saddlecloth(self):
        with tempfile.TemporaryDirectory() as temp:
            record, provenance, rows = self.make_output(temp)
            rows[1]["number"] = "1"
            self.write(Path(temp), record, provenance, rows)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                verify(temp)

    def test_rejects_claimed_independent_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            record, provenance, rows = self.make_output(temp)
            provenance["independent_field_verification_proven"] = True
            self.write(Path(temp), record, provenance, rows)
            with self.assertRaisesRegex(ValueError, "independent verification"):
                verify(temp)

    def test_rejects_nonfinite_probability(self):
        with tempfile.TemporaryDirectory() as temp:
            record, provenance, rows = self.make_output(temp)
            rows[0]["monty_prob"] = "nan"
            self.write(Path(temp), record, provenance, rows)
            with self.assertRaisesRegex(ValueError, "Invalid odds"):
                verify(temp)


if __name__ == "__main__":
    unittest.main()
