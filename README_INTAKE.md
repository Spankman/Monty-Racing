# Monty V6 — race-day intake v0.2

This step adds a **local CSV/JSON intake and audit layer**, not a live TAB API connection. It accepts snapshots that have been obtained legitimately and verifies their structure against an **independently confirmed** expected active-runner count for each race. Do not assume that a file with all listed rows is a complete TAB field. Do not use the example manifest for real betting.

1. Prepare `snapshot.csv` or `snapshot.json` with runner records and a `manifest.json` containing `source`, timezone-aware `captured_at`, and `races` with `meeting`, `race`, `expected_active_runners`.
2. Run `python import_fields.py snapshot.csv manifest.json --output normalized_fields.csv --audit intake_audit.json`.
3. Inspect `intake_audit.json`. If `ready` is false, the CSV is not created.
4. Run `python race_day.py normalized_fields.csv --complete-fields --output selections.csv` **only after independently checking TAB race status, scratchings, and that the prices and counts match the snapshot**.

Supported aliases include `track/venue`, `race_number`, `saddlecloth`, `horse_name`, `win_odds`, and `is_scratched/status`. Scratched runners are excluded; missing odds for active runners are rejected. Missing optional V6 features are handled by the frozen model's historical imputation.

**Limitations:** No network fetch, automatic meeting discovery, live TAB authentication, odds freshness guarantee, full-form feature mapping, or verified profit edge. `--complete-fields` is still a manual assertion. Input price snapshots and selection output should be saved with timestamps to preserve a pre-race audit trail.
