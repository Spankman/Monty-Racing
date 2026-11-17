# Monty current entry point — 17 November 2026

Canonical code: https://github.com/Spankman/Monty-Racing/tree/main . Read this file and LIVE_COMPLETION.md from main before using any older ZIP or chat summary. Source archives are historical snapshots, not the latest operational code.

## Verified

- Original frozen V6 linear model and preprocessing preserved; 55-entry artifact manifest unchanged.
- Historical replay: 17,987 runners, 1,787 races, maximum probability difference 1.6653345369377348e-16.
- Prediction-time history builder uses the original formulas and never updates history with unknown current-day results. Exact full-archive feature parity: 62,255 rows × 55 features. A 367-runner final-date replay matches exactly without supplying current outcomes.
- Official free Betfair ANZ CSV importer uses scheduled-off best-back quotes, not BSP. It reproduces the corrected original April loader's 13,842 runner identities and probabilities exactly.
- October 2026 free-source import: 14,055 retained runners, 1,475 races. Raw third-party data stays private/ignored; import audit is published.
- Krok's race-form and historical-date endpoints returned HTTP 200 in a bounded diagnostic. Its response reported free tier, 11 remaining credits and reset 2026-12-01. This is a reported credit allowance, distinct from any request-rate limit.

## Still blocked

No fully informed live betting service has been established. Recent scheduled-off history, as-of connections/conditions, source identity reconciliation and fresh independently checked fields/quotes remain incomplete. Betfair's public listing currently reaches October 2026; it does not supply current form metadata. V6's retained historical universe is AU thoroughbreds, not a validated NZ model. Do not substitute provider predictions or career win percentages for the original features.

## Continue from here

1. Restore the unchanged private archive using restore_archive.py. Its saved copy is named Monty_Repaired_Checkpoint_2026-11-17.zip; treat its data/model as the original baseline and use current GitHub code.
2. Import official Betfair raw history with betfair_history.py, then add independently matched static metadata and recent compatible data without altering archived records.
3. Build pre-race feature rows with history_bridge.py, using exact market/horse identities and prior local dates only.
4. Use intake_only.py and assess_day.py for input/readiness diagnostics. race_day.py remains research-only. Current betting labels are blocked.
5. Preserve original pre-race NO BET records. Manual expert tips are separate and must never be relabelled Monty predictions.

For racing output, Ferg wants a short list of best bets and roughies with race, saddlecloth, name and timestamped odds; verify wet-track suitability and scratchings, cover AU/NZ meetings when available, and allow NO BET. Never invent scores or claim another chat's code ran in this session.
