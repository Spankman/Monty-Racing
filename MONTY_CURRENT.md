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

## PDF and FormFav integration — 18 November card

See PDF_FORM.md and FORMFAV.md. PDF history extraction matched 375 historical
starts and recovered latest-start fitness/distance features for 103 runners
before subsequent scratchings. The original formulas and artifacts remain
unchanged; cumulative horse and connections histories remain incomplete.

FormFav API access and the user's Pro tier were verified. Source cards cover
43 AU/NZ races. No FormFav model predictions are used as Monty outputs.
A separate rendered TAB refresh captured all 35 Australian races at
18:24–18:29 Queensland on 17 November: 416 active runners, 34 scratched,
22 stale FormFav scratching flags reconciled. Frozen V6 was rerun with
13–21/43 active features available. This remains research only, with no
fully informed betting recommendation claimed. Keys and raw data stay private.

## TAB fixed-price preference and input path

Ferg approved capture-time-only current odds and fixed win prices only. Bookmaker-supplied update timestamps are not mandatory for that path; historical scheduled-off prices remain required. The TAB browser test and input adapter are documented in TAB_INPUTS.md. Kyneton R6 capture: 16 cards, four scratched, 12 active fixed-win quotes, Good 4. The corresponding readiness audit has 14/43 active inputs observed. Identity reconciliation and historical form remain unresolved; no model picks were generated.
