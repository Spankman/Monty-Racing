# FormFav vs Krok — measured source-coverage protocol

This is an **audit procedure**, not evidence of a completed live comparison.

1. Capture FormFav and Krok for the same date with authenticated provider access, retaining acquisition timestamps and API quota limits. Do not commit credentials or raw licensed race cards.
2. Normalize each source to the same Monty runner-input schema **without guessing equivalence**. The existing Krok adapter produces a normalized snapshot. FormFav's existing `merge_card` enriches an existing saved field and does not independently produce an equivalent snapshot; therefore it must not be passed off as a standalone source benchmark.
3. Run `research_source_feature_coverage.py monty_v6/results/frozen_model.json --source krok=... --source formfav=... --output source_feature_coverage.json` only after both normalized files exist.
4. Reconcile same-date meeting/race/saddlecloth/horse identities before interpreting comparative coverage. Do not equate unmatched runner sets or different capture times.
5. Measure missingness by feature and runner, separately for AU and NZ. Track quote origin, quote time, off-time and scratching freshness independently of numeric coverage.
6. Preserve original V6 feature semantics. FormFav aggregated jockey/trainer percentages are **not** replacements for V6 market-adjusted residuals; FormFav official starting prices are **not** scheduled-off market quotes.
7. Compare predictive impact only using frozen chronological out-of-sample data and an identical market-only benchmark. A larger feature count alone is not an edge.

Current evidence: repository documentation reports a FormFav Pro capture of 35 AU races / 416 active runners on 17 November for 18 November and 13–21 of 43 model features observed, but no same-time comparable Krok coverage report. Historical Krok availability samples include missing sectionals and history fields. **No new live provider call or predictive uplift is claimed here.**

Security: source audit outputs must not contain keys, raw proprietary records, or private account data. V6 remains frozen; V7 is research-only.
