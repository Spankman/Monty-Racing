# Monty V6 Race-Day Engine v0.3 — Meeting Discovery

This release adds `discover_meetings.py`, a conservative TABtouch meeting-market schedule collector. It supports `--fetch` when run on a computer with internet access, or `--html` for a saved HTML page. It filters known non-thoroughbred and non-AU/NZ venues, marks uncertain venues for manual review, and emits a JSON audit. **It does not collect runners, scratchings or odds**, and cannot yet automatically run V6 for today's fields. TAB.com.au remains the preferred authority for final verification.

## Run

```
python discover_meetings.py --date 2026-11-14 --fetch --output meetings.json
# or
python discover_meetings.py --date 2026-11-14 --html tabtouch_saved.html --output meetings.json
python -m unittest test_discover_meetings.py test_import_fields.py -v
```

The website can change layout, block automated requests, or omit races; treat results as provisional. Never infer active runner counts from market counts. The existing `import_fields.py` still requires a separately verified active-runner manifest; `race_day.py` scores only complete verified priced fields. There is no silent fallback to tipster guesses or fake prices. The frozen V6 model is included unchanged.

## Current limitations

* No direct live network access in this execution environment; the `--fetch` mode was not integration-tested against the live website.
* No automated TAB.com.au race-field/odds ingestion yet; no national 14 Nov 2026 model selections generated.
* Venue classification is conservative, not exhaustive. `review_required` means unknown code or venue, not automatically a thoroughbred TAB meeting.
