"""Exercise the workflow CLIs against an offline Krok card and scored flags."""
import json
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import runpy
import sys
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd
from v7.predict import run

DATE = "2030-01-02"
NUMBERS = ("09", "2", "7", "1")
CASES = (
    ((4, 5, 6, 7), {}, "BB", 1),
    ((2, 4, 5, 6), {}, "Q (boxed)", 2),
    ((2, 3, 4, 5), {}, "T (boxed)", 3),
    ((2, 3, 3.5, 5), {}, "FF (boxed)", 4),
    ((2, 3, 3.5, 5), {"evidence_verified": None}, "NO BET", 1),
    ((2, 3, 3.5, 5), {"evidence_verified": False}, "NO BET", 1),
    ((2, 3, 3.5, 5), {"roughie": True}, "NO BET", 1),
    ((2, 3, 3.5, 5), None, "NO BET", 1),
)


def provider_card():
    return dict(success=True, data=[dict(
        venue="Example", date=DATE, type="T", country="AU",
        races=[dict(number=i, status="open", name="Benchmark 65", runners=[
            dict(number=n, name=f"Runner {n}", fixed_win=odds, is_scratched=False)
            for n, odds in zip(NUMBERS, case[0])
        ]) for i, case in enumerate(CASES, 1)],
    )])


def offline_scores(model, inputs, output, *, provisional):
    run(model, inputs, output, provisional=provisional)
    path = output / "v7_research_scores.csv"
    data = pd.read_csv(path, dtype={"runner_id": str})
    flags = CASES[int(data["race"].iloc[0]) - 1][1]
    if flags is not None:
        # Deterministic hypothetical engine rankings, independent of price order.
        data["v7_win_probability"] = data.runner_id.map(dict(zip(NUMBERS, (.4, .3, .2, .1))))
        data["evidence_verified"] = [True] * 4
        data["roughie"] = [False] * 4
        for flag, value in flags.items():
            data[flag] = data[flag].astype(object)
            data.loc[data.runner_id == "2", flag] = value
    data.iloc[::-1].to_csv(path, index=False)


def cli(module, *args):
    with patch.object(sys, "argv", [module, *map(str, args)]), redirect_stdout(StringIO()):
        runpy.run_module(module, run_name="__main__")


class ProvisionalWorkflowTests(unittest.TestCase):
    def test_daily_and_single_race_commands(self):
        with (TemporaryDirectory(dir=os.environ.get("MONTY_OFFLINE_OUTPUT")) as temp,
            patch.dict(os.environ, {"KROK_API_KEY": "offline"}),
            patch("krok_adapter.fetch", return_value=provider_card()),
            patch("v7.run_provisional_race.run", side_effect=offline_scores),
        ):
            root = Path(temp)
            fixture = root / "fixtures.json"
            fixture.write_text(json.dumps(dict(date=DATE, meetings={"Example": len(CASES)})))
            daily = root / "daily"
            cli("v7.run_live_daily", "--date", DATE, "--verified-fixtures", fixture,
                "--output-dir", daily)
            card = json.loads((daily / "selections.json").read_text())
            report = (daily / "selections.md").read_text()
            self.assertEqual(card["copy_text"], report)
            self.assertFalse(card["failures"])
            self.assertEqual(len(card["results"]), len(CASES))
            for race, (_, flags, label, count) in enumerate(CASES, 1):
                with self.subTest(race=race):
                    single = root / f"single-{race}"
                    cli("v7.run_live_single_race", "--meeting", "Example", "--race", race,
                        "--date", DATE, "--country", "AU", "--output-dir", single)
                    subprocess.run([sys.executable, "-m", "v7.provisional_output",
                                    "--output-dir", str(single)], check=True)
                    result = json.loads((single / "selection.json").read_text())
                    visible = (single / "selection.md").read_text()
                    self.assertEqual(result["copy_text"], visible)
                    self.assertIn(visible.split("**Example**\n\n")[1].strip(), report)
                    self.assertIn(f"{label} assessment · NO BET", visible)
                    self.assertFalse(result["betting_authorised"])
                    self.assertFalse(card["results"][race - 1]["betting_authorised"])
                    self.assertEqual(result["ordered"], card["results"][race - 1]["ordered"])
                    picks = [line.split("#")[1].split()[0] for line in visible.splitlines()
                             if line.startswith("- ")]
                    self.assertEqual(picks, list(NUMBERS[:count]))
                    self.assertEqual(result["fixed_win_price_progression"]["numbers"], picks)
                    if race in (5, 6, 8):
                        self.assertFalse(result["ordered"][1]["evidence_verified"])
                    if race == 7:
                        self.assertTrue(result["ordered"][1]["roughie"])
            if os.environ.get("MONTY_OFFLINE_OUTPUT"):
                for path in root.glob("*/select*.md"):
                    (root.parent / f"{path.parent.name}.md").write_bytes(path.read_bytes())
