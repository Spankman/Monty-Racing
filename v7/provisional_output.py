"""Render research-only workflow artifacts from the engine's original ranking."""
import argparse
import json
from pathlib import Path

from monty_daily_price_ladder import format_daily


def shortlist(result):
    return dict(
        meeting=result["meeting"], race=result["race"], qualified=True,
        classification="Class unverified",
        ranked=[
            dict(number=runner["number"], horse=runner["horse"],
                 odds=runner["fixed_win_odds"], probability=runner["v7_win_probability"],
                 evidence_verified=runner.get("evidence_verified") is True,
                 roughie=runner.get("roughie") is True)
            for runner in result["ordered"]
        ],
    )


def write_single_race(output):
    original = output / "v7" / "provisional_selection.json"
    result = json.loads(original.read_text(encoding="utf-8"))
    result["copy_text"] = (
        "# Monty V7 provisional research — NO BET\n\n"
        + format_daily([shortlist(result)]) + "\n"
    )
    (output / "selection.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "selection.md").write_text(result["copy_text"], encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    write_single_race(parser.parse_args().output_dir)
