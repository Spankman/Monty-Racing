# Monty-Racing — M-Train Racing Algorithm

**In Monty We Trust.**

This branch imports the saved V6 source and frozen linear model, repairs race-day feature calculations, and adds direct Krok connectivity checks. Offline historical replay is reproducible with the original private archive. Live model predictions and a betting edge have not been established.

## What works

- Race-day barrier and going features match the unchanged training builder.
- A frozen linear model, ordered feature contract and original 55-entry artifact manifest are included. No retraining or research-pickle loading is required for replay.
- `check_krok.py` tests direct Krok API connectivity, validates input shape and saves a count-only connection report. It never loads the model or generates selections.
- GitHub Actions has offline checks and a manually triggered Krok connection check. Neither schedules bets nor connects MCPBackend.

## Install and check

```sh
python -m pip install -r requirements-runner.txt
python -m unittest test_krok_adapter test_adapter_parity test_v06 test_backend_bridge test_discover_meetings test_v04.Integration.test_incomplete_race_rejected test_operations
```

These code checks use synthetic fixtures. They do not establish live API success.

## Restore the private historical archive

Historical datasets, source HTML and research results are intentionally excluded from this public repository. Their redistribution permissions are not established. The original manifest and inference integrity gate are unchanged: scoring fails if any required artifact is absent or altered.

Download your saved `Monty_Repaired_Checkpoint_2026-11-17.zip` or `Monty_v6_Multivariable_Code_Data_and_Results.zip` privately, then run:

```sh
python restore_archive.py /absolute/path/to/archive.zip
python -m unittest discover -s . -p 'test_*.py'
cd monty_v6
python -m unittest discover -s . -p 'test_*.py'
python verify_project.py
```

Restoration validates every missing file against the existing manifest before writing, preserves matching existing files, and rejects mismatches. It does not regenerate the manifest. The restored files remain ignored by Git.

The selected model's consistency with the saved archive has been verified, not independent authorship or profitability. V7 and boosting research remain separate from the operational baseline. Full experiment reconstruction still needs the separately identified V5 inputs.

## Test Krok privately

Set `KROK_API_KEY` in your runner's environment, or use the existing GitHub Actions repository secret. Never put it in source files or chat.

```sh
python check_krok.py --date YYYY-MM-DD
```

The manual workflow is `Monty manual Krok connection check`. After the workflow exists on the default branch, open Actions, choose that workflow, select Run workflow, choose a branch and enter the Queensland racing date. It sends the secret only to the provider request step and uploads a count-only report. This workflow has not yet been run on GitHub.

Data source: [Krok Odds](https://krokodds.com.au). A capture timestamp is not a verified quote-update timestamp. Coverage of every AU/NZ meeting and independent TAB verification are not established. Historical-form features must still be sourced as of the decision time before treating model output as suitable for live selections.

`intake_only.py` additionally captures input and feature coverage after restoring the full archive; it does not score. Existing `race_day.py` is a prototype research scorer, not a verified live tipping service.

## Validation recorded before publication

With the full archive restored locally: 55 original artifact hashes matched; 13 model tests and 20 wrapper/intake tests passed. Replay reproduced 17,987 runner probabilities across 1,787 races with maximum difference 1.6653345369377348e-16. The fitted model, preprocessing, manifest and original records were unchanged. Current branch validation is recorded in `VALIDATION.md`.

Never fabricate runners, scratchings, conditions, odds, predictions, results or returns. Prioritise TAB.com.au and cross-check conflicting sources. Freeze genuine pre-race picks with timestamps; separate probability from value and permit NO BET. Expert tips and personal blackbook bets are not independent model predictions.
