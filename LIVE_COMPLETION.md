# Live Monty completion status — 17 November 2026

## Verified baseline

The frozen V6 coefficients and preprocessing remain unchanged. All 55 original artifact hashes pass. Historical replay matches 17,987 runners in 1,787 races, with maximum absolute probability difference 1.6653345369377348e-16. The wrapper has 33 passing tests and the model has 13.

Krok meetings connectivity passed in GitHub Actions. The 1:10 pm Queensland snapshot supplied 13 of 43 active feature inputs; reduced-data model results remain research-only. Existing NO BET records and manual expert selections are distinct and must not be relabelled.

## Simplest data route to investigate

Use Krok's existing authenticated `field-form` endpoint rather than a new scraper or MCP deployment. The provider documents race-level runner histories, form splits and per-book quote capture timestamps, with at most ten recent runs per runner. See https://krokodds.com.au/api-docs/racing/form . `probe_form.py` audits actual availability without returning runner records or scoring.

That endpoint's career win percentages are not equivalent to V6 features. V6 derives shrunk residual performance against the normalized probabilities of entire prior race fields, with stable horse identities, prior-day cutoffs, connection histories over 90/365 days and track/distance histories. Ten recent starts cannot establish all those histories. Provider ratings must never replace V6 coefficients or probabilities.

## Remaining implementation dependency

Obtain compatible historical whole-field outcomes and market prices, stable IDs and as-of connections/conditions; update the private history store through the previous local date; validate identity joins and feature parity against the unchanged builder. Then establish current quote ages and field/scratching reconciliation, and run prospective shadow evaluation before approving betting labels. The program currently reports BLOCKED rather than declaring these requirements satisfied.

## Operational commands

Restore the private original archive with `restore_archive.py`. Set the existing API key privately. Run `python intake_only.py --date YYYY-MM-DD` to capture and audit, or `python assess_day.py assessment_bundle.json` to recheck a capture. `race_day.py` remains a research scorer whose actionable category is blocked. No scheduled betting or automatic wagering is configured.

## Live field-form probe

On 17 November at 1:24 pm Queensland, four Kyneton race requests returned form data and seven further AU race requests returned HTTP errors. The four responses contained 380 history rows, of which 209 had finishing positions and 254 had BSP values. Rows were not independently reconciled or transformed into V6 features. Quote capture timestamps were present, so they are available for a future freshness-aware adapter. HTTP status codes were not retained by this first probe, so the reason for the seven failures is unconfirmed. The workflow succeeding means the audit completed, not that every API request succeeded.

Evidence: https://github.com/Spankman/Monty-Racing/actions/runs/44009909818 . The temporary probe launcher was removed after this run. No research ratings were used, no model scoring occurred, and the key stayed in GitHub secrets.

## Historical bridge and free source follow-up

The canonical pre-race builder now reproduces all 62,255 archived feature rows exactly. A final-date run reproduced 367 runners with current outcomes absent. The original manifest-backed feature builder remains unchanged; the prediction adapter copies its formulas and suppresses current-day outcome updates.

The historical market feature specifically uses BEST_AVAIL_BACK_AT_SCHEDULED_OFF. BSP and fixed-odds SP are not equivalent and are rejected as substitutes. The new official Betfair CSV importer exactly reproduces the corrected original April source loader (13,842 runners). A downloaded October 2026 file supplied 14,055 retained runners across 1,475 races, without using Krok credits; missing connection/going metadata remains explicit.

The bounded follow-up provider diagnostic returned 200 for Scone R7 field-form, 16 November results and 17 November 2025 results. The response reported free-tier credit allowance remaining 11, reset 2026-12-01; no large Krok backfill was attempted. The earlier seven HTTP failures' status was not recorded, so their exact reason remains unconfirmed. The new client records status and stops on 401/402/403/429 without blind retries.

Official free sources investigated: Betfair Automation Hub data/dataListing (historical prices/results and IDs), Racing Australia FreeFields (AU field/form/result pages), LOVERACING.NZ RaceInfo (NZ fields/results). No verified free one-for-one API replacement covering all required real-time odds, full form history and metadata was established. TAB says new Studio API applications are closed. Betfair offers delayed developer API data; it must not be presented as current executable odds.

## Direct TAB input follow-up

TAB's public race page loaded successfully in the browser, including expanded runner form. Added an offline fixed-win observation adapter and capture-time-only policy as approved by Ferg. It never falls back to tote odds when a fixed win cell is missing. TAB_INPUTS.md and validation/tab_fixed_win_capture_2026-11-17.json record the concrete test and its remaining limits. A 12-runner October identity candidate audit found four unique candidates, six ambiguous sets and two absent names; none were promoted to verified joins. Raw runner captures remain ignored/private.
