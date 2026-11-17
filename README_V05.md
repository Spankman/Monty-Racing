# Monty V6 v0.5 — documented live-feed adapter

Adds `krok_adapter.py`, a connector for the documented Krok Odds `GET /api/v1/racing/meetings` endpoint. It takes a user-supplied API key from environment variable `KROK_API_KEY`; never hard-code or share keys.

## Run with live data (requires your own key and network access)

```bash
export KROK_API_KEY='YOUR_PRIVATE_KEY'
python krok_adapter.py --date 2026-11-14 --output-dir output_live
```

Or test offline:

```bash
python krok_adapter.py --date 2026-11-14 --fixture krok_synthetic_fixture.json --output-dir output_test
python -m unittest test_krok_adapter test_v04 test_import_fields test_discover_meetings
```

Output: `output_live/scored/monty_selections.csv`, plus original source, normalized snapshot and audit.

**Warnings:** No live API call was successfully executed in the build environment. The feed requires a key. The adapter rejects paginated feeds, incomplete race fields, unpriced runners and unknown scratchings. It uses TAB prices when explicitly available, otherwise fixed prices with source labels; no independent TAB verification has been implemented. The source's active runner count is derived from its own runner array, NOT independently checked. Do not claim complete national coverage until the provider confirms its entire meeting list was returned. Only simple directly observable V6 features are mapped; historical residuals remain missing and use the model's imputation. No real V6 picks have been produced by this build. Test fixtures are fictional and not betting advice. Review terms before commercial use.

API docs: https://krokodds.com.au/api-docs/racing
