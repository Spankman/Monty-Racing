# Monty V6 race-day bridge (prototype)

Uses the original frozen V6 model and verifies its artifact manifest before scoring. Never retrains on race-day outcomes.

Run: `python race_day.py complete_fields.csv --complete-fields --output selections.csv`

Required columns: meeting,race,number,horse,odds. Optional: scratched, and any original V6 input feature name (see input_template.csv). Each race MUST contain all non-scratched runners and contemporaneous decimal odds; never use partial fields or fabricated odds. The flag is a user assertion, not an automated verification.

Model imputes missing optional features using historical medians; market probability and field size are computed from current odds. Output gives market-normalized probability, Monty probability, fair odds, edge and provisional best-bet/ruffy/no-bet labels. These labels are mechanical and NOT validated profitable betting recommendations. Current implementation has no automatic TAB importer, no bookmaker commission, no scratchings freshness verification, no odds timestamp verification and no calibrated confidence filter. No live race-day predictions have been made.

Tests: Original V6 suite 13/13 passed. Smoke-test scoring on four synthetic runners succeeded; synthetic data are not included as tips.
