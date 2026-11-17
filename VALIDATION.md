# Repair validation — 17 November 2026

Validation was run locally on the staged branch implementation before publication.

- Complete-archive wrapper/intake/operations suite: 26 passed.
- Original model suite: 13 passed.
- Clean staged checkout, excluding historical data: all 21 configured CI tests passed.
- Historical replay: 17,987 runners, 1,787 races; maximum probability difference 1.6653345369377348e-16.
- All 55 original artifact hashes match after restoring the saved archive; frozen model, preprocessing and manifest are unchanged.
- Credential-pattern and dataset-exclusion checks passed on staged files. This is a bounded check, not a security certification.
- No model fitting or research-pickle loading was performed.
- Real Krok connectivity passed on GitHub Actions run 44007843608 after merge, using the repository secret: 12 accepted races, 119 accepted runners, price source labelled TAB by Krok. No model was loaded and no predictions were generated. Independent TAB verification and complete AU/NZ coverage remain unverified. The local environment still does not possess the secret.
- Both initial GitHub offline code-check runs passed (push run 44007427082 and pull-request run 44007453673).
- The temporary live-check launcher was removed after success; the reusable manual workflow remains. The count-only provider report and run URL are in validation/krok_connection_2026-11-17.json.

The 21 clean-checkout tests are a subset of the full validation, not additional independent tests. The historical archive remains required for complete integrity verification and model scoring. No claims of profitability or new predictive improvement are made.

Four hashed original Python files retain their original trailing blank lines; they were not reformatted to satisfy Git's blank-at-EOF warning.
