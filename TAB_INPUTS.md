# TAB fixed-win input bridge

Ferg approved current TAB fixed win prices, with the observation/capture time recorded. A bookmaker-supplied quote-update timestamp is no longer mandatory. Tote win, place prices, pool totals and provider predictions are not used for this input path. This preference does not change V6's historical scheduled-off quote requirement.

## What was exercised

The rendered Kyneton R6 page on 17 November 2026 was read through the browser and Show All Form was expanded. Direct observation identified 16 declared runner cards, four SCR fixed-win cells and 12 priced active runners. The condition displayed Good (4), distance 1887m and class BM56. A fixed-price capture was observed at 2026-11-17T03:51:29.274Z. No Krok credits, sign-in or bet-slip actions were used.

The fixed win cells were identified by the observed DOM attribute `data-test-fixed-odds-win-price`; the distinct tote column has `data-test-parimutuel-win-price`. Do not select the first numeric value in runner text, which could instead be a weight or rating. Always inspect the live DOM before using a selector: this is not a stability guarantee for future site versions.

## Capture format and commands

`tab_inputs.py` accepts an explicitly captured JSON object with `source_url`, `meeting`, `captured_at_utc`, `jump_time`, `distance_m`, `track_condition`, `class_text`, `declared_runners`, and all displayed `runners`. Each runner requires `number`, `horse`, `barrier` and `fixed_win_text` (decimal odds or the observed string SCR). Optional metadata includes jockey, trainer, listed_weight, age and form_observation.

Run `python tab_inputs.py /private/path/capture.json --output-dir race_day_output/tab`. It writes an assessment bundle and per-race readiness report. Run `python audit_history_identity.py bundle.json canonical_history.csv.gz --output identity_audit.json` for candidate identity checks.

The structured capture is an assertion about what was observed, not an independently authenticated website export. Race URL/date, finite values, saddlecloth uniqueness, captured count, SCR status and scheduled jump are checked. The page's displayed local jump time must be reconciled with a timezone-qualified schedule; do not invent a UTC time from an unknown display timezone. `declared_runners` is the number of displayed cards captured, not an independently queried server count.

## Deliberately unresolved

Current odds and basic race context provide 14 of 43 active numeric V6 inputs for the captured race. Rendered form rows remain observations until matched to the retained history used by V6; a latest actual start or a trial must not silently replace the latest eligible retained race. Shorthand rider names are not automatically equated to full names. Listed weight is preserved separately until its claim convention is established.

Against the October retained history, four of the 12 names had one candidate ID, six had multiple candidate IDs and two were absent. A unique name match alone is not a verified cross-source horse ID. No identity joins were approved and no predictions were generated.

The adapter is an offline consumer of observed page data, not an unattended browser collector or a TAB API integration. TAB browser access was verified for this race; full-day automated coverage remains unverified. The original frozen V6 artifacts and earlier decision records remain unchanged.
