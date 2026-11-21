import tempfile
import unittest
from pathlib import Path
import pandas as pd
from v7.run_single_race import execute

class SingleRaceV7EntryTests(unittest.TestCase):
    def test_refuses_unverified_fields(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"runners.csv"
            pd.DataFrame([{"meeting":"Pukekohe","race":"6","number":"1","horse":"Test","odds":3.0}]).to_csv(src,index=False)
            with self.assertRaisesRegex(ValueError,"independent"):
                execute(src,date="2026-11-21",country="NZ",source_url="https://example.org",
                        model_path="v7/artifacts/fold_3_model.json",
                        output_dir=Path(d)/"output")
    def test_rejects_multiple_races(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"runners.csv"
            pd.DataFrame([{"meeting":"Pukekohe","race":str(i),"number":"1","horse":"Test","odds":3.0} for i in (6,7)]).to_csv(src,index=False)
            with self.assertRaisesRegex(ValueError,"exactly one race"):
                execute(src,date="2026-11-21",country="NZ",source_url="https://example.org",
                        model_path="v7/artifacts/fold_3_model.json",
                        output_dir=Path(d)/"output",independently_verified=True)
if __name__=="__main__":
    unittest.main()
