# Repair validation — 17 November 2026

Validation was run locally on the staged branch implementation before publication.

- Complete-archive wrapper/intake/operations suite: 26 passed.
- Original model suite: 13 passed.
- Clean staged checkout, excluding historical data: all 21 configured CI tests passed.
- Historical replay: 17,987 runners, 1,787 races; maximum probability difference 1.6653345369377348e-16.
- All 55 original artifact hashes match after restoring the saved archive; frozen model, preprocessing and manifest are unchanged.
- Credential-pattern and dataset-exclusion checks passed on staged files. This is a bounded check, not a security certification.
- No model fitting or research-pickle loading was performed.
- Real Krok connectivity was not tested locally: KROK_API_KEY was absent. GitHub Actions results must be checked separately after publication.

The 21 clean-checkout tests are a subset of the full validation, not additional independent tests. The historical archive remains required for complete integrity verification and model scoring. No claims of profitability or new predictive improvement are made.

Four hashed original Python files retain their original trailing blank lines; they were not reformatted to satisfy Git's blank-at-EOF warning.
