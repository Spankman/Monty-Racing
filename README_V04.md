# Monty V6 Race-Day Engine v0.4

## What's new

* `collect_runners.py`: configurable HTTPS/local JSON race-snapshot collection, immutable raw response, SHA-256 provenance and timestamp; no undocumented TAB endpoint is claimed.
* `import_fields.py`: preserves **actual V6 numeric feature columns** supplied in the source rather than discarding them, while validating identity, prices, scratchings and source-declared active-runner counts.
* `run_day.py`: end-to-end collect -> validate -> original frozen V6 inference -> CSV selections, plus source/audit files.
* `test_v04.py`: feature-retention and incomplete-field regression tests.

## Running

Install dependencies listed in `monty_v6/pyproject.toml` (notably numpy, pandas, scipy, beautifulsoup4). Then:

    python run_day.py race_snapshot.json --date 2026-11-14 --output-dir output

Or use a **permitted HTTPS JSON endpoint** containing a documented `runners` array and a `races` array with `meeting`, `race`, and independently verified `expected_active_runners` for each race. Each runner needs `meeting`, `race`, `number`, `horse`, `odds`, optional `scratched` and optional exact V6 feature names. Date should match the requested date. The source's own race counts are assertions, not an independent TAB cross-check.

## Tests

    python -m unittest test_v04.py test_import_fields.py test_discover_meetings.py -v
    cd monty_v6 && python -m unittest discover -s . -p 'test_*.py'

## Critical limitations

**This is NOT yet a verified automatic TAB.com.au feed.** No live official TAB endpoint has been integrated or tested. The importer cannot independently verify source-declared active-runner counts, race-date status, freshness, or prices. Without an actual authorized source returning the requisite JSON data, it cannot generate genuine race-day predictions. Model scores based largely on imputed features can be low-information and should not be marketed as demonstrated predictive edge. A real TAB feed adapter and independent reconciliation are the next steps. Never confuse synthetic integration tests with actual race-day selections.
