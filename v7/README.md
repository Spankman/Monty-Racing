# Monty V7 development handover

V7 is an experimental branch. V6, its original 55-file artifact contract,
historical selections and results remain unchanged. No production entry point
has been switched. This candidate has not earned replacement approval.

## Delivered

- Race-conditional ridge model with a market log-probability offset.
- Expanding chronological fits, separate earlier model-selection and temperature
  calibration windows; training-only medians/scalers and missing indicators.
- Original full warm-up reconstruction checked against all 62,255 × 55 saved
  features, with immutable-file verification before and after evaluation.
- Frozen V6 and normalized-market comparisons on identical eligible May–June
  races; April excluded from frozen-V6 comparison because V6 selected on April.
- Win log loss, race Brier, runner calibration bins/ECE, strike rate, one-unit
  payout-proxy ROI and daily aggregate drawdown. NO BET remains explicit.
- Harville/Plackett-Luce top-two/top-three and unordered quinella estimates.
  These are structural estimates, **not calibrated or validated place prices**.
- Optional full-field expert probability blending, default weight zero, capped
  at 25%. No expert data history exists here, so no fitted or activated weight.
- Strict evidence interface for source-verified sectionals, pace, interference,
  prior bias, forecast weather and connection statistics. Unknown inputs stay
  missing; current-race outcomes and post-decision publication are rejected.
- Confirmed blackbook names (Revelare, Argerich, Bred 'em All, Calamari Ring),
  candidate matching and next-start review output. Existing scheduled Monty
  Blackbook Watch remains in place; this branch creates no duplicate task and
  does not claim a newly deployed notification service.

## Actual protocol, fixed before this candidate's results

| Fold | Fit through | Penalty selection | Temperature calibration | Evaluation |
| --- | --- | --- | --- | --- |
| 1 | 28 Feb 2025 | 1–15 Mar | 16–31 Mar | April |
| 2 | 31 Mar 2025 | 1–15 Apr | 16–30 Apr | May |
| 3 | 30 Apr 2025 | 1–15 May | 16–31 May | 1–15 June |

Candidate penalties: 0.01, 0.1, 1.0. Calibration temperatures bounded 0.5–2.
No refit after calibration. Historic outcomes can update pre-race histories only
on later local dates; original history builder defers all same-day updates.
Rolling test-month histories may use already-observed prior-day test outcomes,
as a genuine sequential deployment would, without refitting model parameters.

The value simulation bets **only the highest-probability horse in each race**
when its net expected return is at least +5%, using 5% winnings commission and
one-unit stakes. Top-pick ROI (bet every race) and filtered-value ROI are separate.
No meeting quotas. This is a predeclared research strategy, not an optimized live
betting rule. Drawdown is measured after daily net settlement, not intraday.

## Reproduce

From repository root, with the private original archive restored outside the
repository and current V6 source on this branch:

```bash
python -m pip install -r v7/requirements.txt
python -m unittest v7.test_v7 -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m v7.evaluate \
  --v6-root /absolute/path/to/unchanged/monty_v6 \
  --history-package /absolute/path/to/original-package \
  --output /absolute/path/to/new-v7-output
```

`--history-package` contains original `monty_v5/results/cleaned_eligible_runners.csv.gz`,
`monty_v5/run_research.py`, its registry, plus `monty_v6/sources/github_racing_data.csv`
and `monty_v6/sources/april_recovery/ANZ_Thoroughbreds_2025_04.csv`.
`--v6-root` contains the full original 55-entry artifact manifest and results.
Do not regenerate manifests, repair missing values inside the archived files,
or rerun the V6 training pipeline to satisfy a missing-file check.

The evaluation writes three independent model JSON files, private per-runner
predictions and an aggregate audit with input digests/runtime/protocol/results.
It never deserializes the research pickle or changes an original artifact.
No credentials needed for the offline benchmark.

Research inference (separate CLI, never replaces `race_day.py`):

```bash
python -m v7.predict --model /path/fold_3_model.json \
  --features /path/verified_full_fields.csv --output /path/new-output
```

Input required: race_id, runner_id, horse, date, country, fixed_win_odds,
source_url, field_verified=True. Optional columns have exact trained feature
names. Scratchings must already be removed and the complete field verified.
Missing optional features use saved training defaults. Do not use a model on
races on/before its calibration end date. NZ receives an explicit unvalidated
country warning. Outputs always identify experimental V7 status; deployment
remains NO BET until separately validated and approved. This does not change
Ferg's permission to receive provisional V6 selections with missing features.

## Limits and promotion decision

These 2025 dates/features have been exposed in previous research. Walk-forward
parameter fitting and calibration are chronological, but this is **retrospective
research**, not a fresh prospective trial. Historical TAB-derived static metadata
has no verified publication snapshots; final going/connection availability can
therefore differ from decision-time information. Do not call the whole dataset
certified leakage-free just because the parameter splits are chronological.

Place finishes/payouts, quinella dividends, timestamped expert opinions,
sectionals, pace, interference, bias and forecast-vintage history are absent from
this benchmark. They were not fabricated or silently replaced by proxies. NZ
and other jurisdictions lack a validated training cohort. See SOURCES.md for
verified paths and blockers, and RESULTS.md for the actual candidate outcome.

Next work: collect licensed/publicly available point-in-time samples with full
race identities, test source adapters and numeric semantics, add verified place
labels, train separate place calibration, and freeze a prospective prediction
ledger. Evaluate extra features in separately registered ablations against both
V6 and the market. Do not tune on this test report and claim the same dates are
fresh holdout. Require explicit Ferg approval before any V6 replacement.
