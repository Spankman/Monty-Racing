# Live Krok verification — operational runbook

Status (2026-11-21): **NOT VERIFIED** after diagnostic changes. Historical manual run 44847348535 failed with `BLOCKED: Date or provider input did not pass validation` (exit 2). The old message hid the actual validation reason. Offline diagnostics regression tests subsequently passed (run 44848255657). This does **not** prove live provider connectivity.

## Trigger
1. In GitHub Actions, select **Monty manual Krok connection check** (`.github/workflows/monty-manual-intake.yml`).
2. Select branch `grok-independent-repairs` so the improved diagnostic code is used.
3. Click **Run workflow**. Leave date blank for the current Queensland date or provide a valid `YYYY-MM-DD` date.
4. Inspect the **Check live provider connection without predictions** step. Record the run ID and final conclusion.

This GitHub connector currently provides workflow reads and reruns but no fresh workflow-dispatch action. Do not represent an offline CI run or old rerun as a new live check.

## Pass criteria
- Workflow completes successfully.
- `connection_report.json` is uploaded and includes `live_request_succeeded: true`, positive accepted races/runners, captured UTC time, and price sources.
- Independently note `tab_verified: false`, `model_loaded: false`, and `predictions_generated: false`. These flags do not change just because connectivity works.
- Record skipped/incomplete/ambiguous races separately; connection success does not prove full AU/NZ TAB coverage.

## Failure triage
- `missing_api_key`: confirm GitHub Actions secret exists, without revealing its value.
- `invalid_date_or_feed_date`: inspect supplied date and provider's date fields.
- `incomplete_pagination`: inspect safe Krok page audit (counts and metadata keys only).
- `duplicate_race_identity`: preserve conflicting records for audit; never choose arbitrary prices.
- `no_eligible_complete_fields`: distinguish an empty/off-hours card from malformed/partial race data.
- `provider_input_validation`: inspect the validator and add a specific safe error category/test.
- HTTP status (401/403/429/etc.): diagnose access/rate limits without printing tokens or response bodies.

Do not bypass provider checks to claim model predictions. No bet should be issued from a connection-only report.
