# Monty V6 race-day bridge (prototype)

Uses the original frozen V6 model and verifies its artifact manifest before scoring. Never retrains on race-day outcomes.

Run: `python race_day.py complete_fields.csv --complete-fields --output selections.csv`

Required columns: meeting,race,number,horse,odds. Optional: scratched, and any original V6 input feature name (see input_template.csv). Each race MUST contain all non-scratched runners and contemporaneous decimal odds; never use partial fields or fabricated odds. The flag is a user assertion, not an automated verification.

Model imputes missing optional features using historical medians; market probability and field size are computed from current odds. Output gives market-normalized probability, Monty probability, fair odds, edge and provisional best-bet/ruffy/no-bet labels. These labels are mechanical and NOT validated profitable betting recommendations. Current implementation has no automatic TAB importer, no bookmaker commission, no scratchings freshness verification, no odds timestamp verification and no calibrated confidence filter. No live race-day predictions have been made.

Tests: Original V6 suite 13/13 passed. Smoke-test scoring on four synthetic runners succeeded; synthetic data are not included as tips.

## Current operational assessment

Run `python intake_only.py --date YYYY-MM-DD` with the private original archive restored and `KROK_API_KEY` set. This saves an assessment bundle and readiness report alongside the provider snapshot. It does not generate betting selections. Alternatively, run `python assess_day.py /path/to/assessment_bundle.json` to reassess a saved capture. Exit status 2 means blocked; the JSON report explains each race's missing inputs.

Readiness checks require the current Queensland date, a capture no more than five minutes old, a future timezone-qualified jump time, and all active numeric features. The five-minute window is an operational cutoff, not an empirically validated betting threshold. Current provider quote-update times and independent field verification are not established, so this implementation deliberately cannot report live betting readiness. Coverage is presence of finite values, not proof that feature definitions or as-of provenance are correct. Complete coverage alone does not validate profitability.

`race_day.py` now keeps mechanical edge labels in `research_category`; the actionable `category` is always `BLOCKED — RESEARCH ONLY`. This prevents legacy callers from mistaking incomplete-data scores for approved live bets. Research probabilities remain available for diagnosis.

Remaining completion dependency: an available, permitted historical-form feed with timestamped pre-race records, consistent horse identities, the original feature definitions, current scratchings and quote-update timestamps. Add and validate that data path before prospective shadow testing; keep the frozen V6 baseline unchanged.
