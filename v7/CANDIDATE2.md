# Candidate 2 — evidence-led development and handover

17 November 2026. Experimental; V6 and Candidate 1 preserved. No deployment.

## Why Candidate 1 lost

Reproduced the original common-period 139 bets exactly: 39 wins, 20.5325 units
lost, -14.7716% scheduled-off quote-proxy ROI after assumed 5% winnings
commission. The model expected 50.49 wins (36.32% average chance), but the
observed strike was 28.06%. It forecast +17.35 units, a 37.88-unit shortfall from
its own expectation. That shortfall includes stochastic outcome variation and
possible mispricing; it is not a causal allocation to model bias alone.

| Odds | Bets | Wins | Model expected wins | Profit units | ROI |
| --- | ---: | ---: | ---: | ---: | ---: |
| Below $3 | 44 | 18 | 22.74 | -4.2925 | -9.76% |
| $3 to below $5 | 67 | 19 | 21.84 | +0.7350 | +1.10% |
| $5 to below $10 | 28 | 2 | 5.91 | -16.9750 | -60.63% |
| $10 or greater | 0 | 0 | 0 | 0 | — |

| Condition | Bets | Wins | Expected wins | Profit units |
| --- | ---: | ---: | ---: | ---: |
| Good | 54 | 17 | 19.04 | -1.7740 |
| Soft | 60 | 20 | 22.16 | +2.0090 |
| Heavy | 18 | 1 | 5.90 | -15.3280 |
| Synthetic | 7 | 1 | 3.38 | -5.4395 |

Six heavy-track bets also fall in $5–$10; they lost six units. Do not add losses
across overlapping breakdown dimensions. Track condition is reconstructed
historical metadata, not a verified decision-time snapshot.

108 bets were market favourites (including ties), losing 12.63 units; 31 were
market ranks 2–3, losing 7.9025 units. **None was a rank-4-or-lower outsider**.
These were not a longshot-heavy portfolio. Probability bands: below20% 10 bets,
-4.06 units; 20–40% 90 bets, -11.9785; 40–60% 31 bets, -1.0425; 60%+ eight bets,
-3.4515. Probability bands are not calibrated confidence guarantees.

Class breakdown: Maiden29 bets/-9.194 units; BM<=64 38/-5.7985; BM>=65
35/-12.0565; class-restricted17/+3.30; Group/Listed6/+5.93; other14/-2.7135.
Raw-class, track and fold detail is in candidate2_artifacts/loss_breakdown.csv.
Small retrospective subgroups cannot justify automatic exclusion rules.

Most losses were in May: 114 bets, -18.5305 units; June had25/-2.002. Even before
Candidate 1's temperature adjustment, these same139 selections expected49.07
wins. Calibration increased that to50.49, so temperature sharpening worsened
the overstatement slightly but does not explain it alone.

### Probability errors versus threshold

The 1,648 passed race leaders were close in aggregate: 35.60% predicted versus
35.32% observed. The selected139 showed an observed-minus-predicted difference
of -8.26 percentage points; day-bootstrap95% interval [-15.00,-1.01] points.
Their ROI interval is broad, approximately [-37.06%,+9.72%]. This is evidence of
**conditional probability overstatement in the selected subset**, with sampling
uncertainty; aggregate all-field calibration can hide this failure.

Post-hoc threshold sensitivity: 0% edge549 bets/-1.84%ROI; 2.5%285/-5.75%;
5%139/-14.77%; 7.5%82/-4.11%; 10%51/+21.60%; 15%29/+30.35%.
These nested subsets are NOT independent experiments. Selecting10% after seeing
this table would overfit. No threshold was changed. The problem involves both
probability accuracy in the filtered subset and sensitivity to the filter;
this data cannot establish a unique causal split or a new profitable cutoff.

## Independent calibration check

All17,987 held-out common-period runners, using their original frozen test
predictions; calibration outcomes were not reused to fit these predictions.
Dates are still already-exposed retrospective research, not prospective data.

| Requested vicinity | Fixed probability interval | Runners | Mean predicted | Actual win rate |
| --- | --- | ---: | ---: | ---: |
| 10% | 5%–<15% | 5,822 | 9.02% | 9.12% |
| 20% | 15%–<25% | 2,248 | 19.26% | 18.68% |
| 40% | 35%–<45% | 427 | 39.06% | 37.94% |

Their observed-minus-predicted day-bootstrap95% intervals all include zero.
This does not prove exact calibration. Within selected bets, the20% vicinity
contains only28 runners: mean20.80%, actual7.14%. The40% vicinity has33:
mean38.48%, actual39.39%. No selected bet is in the10% vicinity. Full bins,
Wilson intervals and clustered uncertainty are saved. All-runner average
probability equals overall win rate mechanically because every race sums to
one; that aggregate is NOT a calibration test.

## Simpler Candidate 2 and identical-period comparison

No new form weights or features were fitted. Candidate2 shrinks the existing
Candidate1 probabilities toward normalized market probabilities. It selects
form weight0,0.5 or1 using only that fold's earlier calibration dates. April
selects0.5, May1, June0 (pure market). Candidate1's calibration predictions are
replayed exactly; fold data/coefficients and original artifacts are unchanged.
This three-choice selection reuses the earlier calibration window rather than
introducing another clean validation dataset; test chronology is protected,
but research-level overfitting remains possible. No thresholds were retuned.

| Method | Same1,787 races: win log loss ↓ | Top-pick strike | Filtered bets | Quote-proxy ROI |
| --- | ---: | ---: | ---: | ---: |
| Candidate2 | 1.818081 | 34.92% | 124 | -15.30% |
| Candidate1 | 1.816589 | 34.75% | 139 | -14.77% |
| FrozenV6 | 1.816407 | 34.81% | 68 | +17.43% |
| Market | 1.815969 | 34.92% | 32 | +13.74% |

**Candidate2 does not improve this benchmark.** Different bet counts reflect
each method's own same-threshold selection, not identical selected portfolios;
probability metrics use identical fields. April excluded from frozenV6 because
it selected on April. Allthree-fold Candidate2/Candidate1/market results, Brier,
calibration, drawdown and full settings are in candidate2_artifacts/comparison.json.

### V6 profitability is not established

V6's68 filtered bets have approximate day-bootstrap95% ROI interval
**[-22.90%,+59.32%]**. Betting every V6 race leader returned -4.69%, with interval
[-10.27%,+0.59%]. V6 being better than a failed V7 candidate is not evidence that
V6 makes money. Quotes are retrospective scheduled-off prices, not verified
executable fills; liquidity, slippage and stake impact remain absent.

## Fold adequacy and countries

April:1,196 races/85 tracks (674good,390soft,107heavy,25synthetic).
May:1,203/86 (602good,366soft,189heavy,46synthetic).
June1–15:584/65 (149good,315soft,71heavy,49synthetic).
There is condition and geographic variation, but these are adjacent months in
one2025 season, with shared tracks (62 between April/May, 51 between May/June, 48 between April/June) and expanding overlapping
training histories. They are not three independent market regimes or sufficient
year-round evidence. Full state/track inventories are in the audit.

AU is evaluated only on its retained AU cohort. **NZ is NOT VALIDATED**, not
scored as an assumed transfer success. No matched NZ historical cohort with
point-in-time form and compatible quotes is available for a separate backtest.
An official NZ sectional sample has been inspected, not used to invent a cohort.

## New source pilot and remaining gaps

- BRC official Eagle Farm report (14Feb2026) exposes each horse's last600m,
  speed, stride, rail-distance and timing. Official page reviewed; direct PDF
  retrieval403. The URL is under a June2026 upload directory for a February
  event: event date cannot be assumed publication date.
- Auckland Racing official3Nov2026 race page exposes comparable NZ sectionals
  and position splits. Direct HTML retrieval403. Three numeric observations
  were manually checked per country (six total), quarantined in the private
  package, with unknown original availability and unresolved ID crosswalks.
  **None entered training or historical performance claims.**
- RQ4June2025 stewards report confirms track upgrade afterRace2, showing why
  final meeting going can leak into earlier-race features. Report discovered
  and read, not used as a pre-race interference flag for that same race.
- Existing FormFav connection caches remain separate. No new licensed TPD
  access, speed-map history, bias series, interference tags or weather forecast
  availability history has been established. Worldwide sources are researched,
  not assumed applicable to AU/NZ or silently combined across jurisdictions.

Source URLs: https://www.brc.com.au/eagle-farm-and-doomben-sectional-data/ ;
https://www.brc.com.au/wp-content/uploads/2026/06/20260214_Eagle_Farm_T.pdf ;
https://www.aucklandracing.co.nz/race-results/yourride-1100-2/ ;
https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/doom/20250604/stewards-report .
Earlier broader provider/weather/market research remains in SOURCES.md.

## Prospective shadow started

A real immutable pre-race snapshot froze416 AU runners/35 races for18Nov2026
at2026-11-17T13:38:01Z (23:38Queensland). Earliest listed start03:55Z18Nov.
V6, Candidate1, Candidate2 and market probabilities plus every available fixed
win quote, capture timestamp, model hashes and source hashes are saved privately.
The public receipt commits its SHA256. Quotes are the existing17Nov18:24–18:29
Queensland TAB capture, **not newly refreshed**. Field changes after that snapshot
remain a risk. This early, sparse-input comparison is distinct from a fresh
near-start trial; no live betting recommendation or real bet is claimed.

`shadow.freeze` uses exclusive creation, rejects already-started races/future
quote capture and validates full-field probabilities. `record_results` writes a
separate result record referencing the unchanged forecast hash, requires verified
source/timing and rejects unsupported outcomes. Original scratched picks must
be voided, never reranked after the result. Results are not yet available; no
prospective performance or automatic polling is claimed. Blackbook matching,
evidence checks, trained missing defaults and NO BET remain unchanged.

## Reproduce and continue

```bash
python -m v7.diagnose --predictions /path/candidate1/walk_forward_predictions.csv.gz \
  --metadata /path/original/results/joined_development_runners.csv.gz \
  --features /path/original/results/development_features.csv.gz --output /path/new-diagnostic
python -m v7.candidate2 --v6-root /path/original/monty_v6 \
  --candidate1-dir /path/candidate1-output --output /path/new-candidate2
python -m unittest v7.test_v7 v7.test_diagnostics -v
```

Do not replace a pre-existing shadow file to refresh prices. Make a separately
identified snapshot and preregister which snapshot governs evaluation before
results. Do not postselect snapshots by their profit. Preserve early snapshots.

Recommendation: continue **evidence acquisition and prospective validation**,
not added model complexity or deployment. Candidate2's shrinkage rule is not
an improvement and should not replace V6. Acquire usable earlier-available
sectional/pace/rail/interference and forecast data, complete a separate NZ
cohort, test ablations on a preregistered new period and collect outcomes against
frozen forecasts. No protected files or historical results were changed.
