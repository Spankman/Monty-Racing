# Monty 6.0 — multivariable form research

10 November 2026 · Peter Ferguson · In Monty We Trust

## What changed

Monty now has a working feature engine with **55 definitions: 44 observed in the development data and 11 unavailable pending verified inputs**. The engine models earlier observed horse form, condition suitability, distance and track history, jockey/trainer combinations and changes, draw, fitness and comparable benchmark-class changes. Linear market-offset and nonlinear histogram boosting candidates were trained and compared.

This is a substantive research implementation, not a claim that all requested variables have already been learned or that accuracy has improved. Available-data manual Full Monty tips remain a separate analysis method.

## Factors and actual status

| Factor | Implemented treatment | Status |
|---|---|---|
| Recent form | Last 3/5 observed wins and results relative to prior market expectations | Tested |
| Longer-term form | All observed and trailing-year starts, win rates and market residuals | Tested; incomplete observed history |
| Going | Good/soft/heavy/firm/synthetic plus prior horse performance on that category | Tested; reconstructed meeting ratings, not certified per-race pre-off snapshots |
| Distance | Current trip, prior distance band and track-distance form, rise/drop since last observed run | Tested |
| Jockey | 90/365-day performance relative to market, change of rider, horse/jockey combination | Tested on available 2025 connection history |
| Trainer | 90/365-day performance and trainer change | Tested on available 2025 connection history |
| Jockey/trainer | Historical combination performance with shrinkage | Tested |
| Barrier | Draw, draw relative to retained field size, inside/outside and distance interaction | Tested |
| Track | Horse's earlier course and course/distance performance | Tested |
| Fitness | Days since observed run, 60-day resumption and seven-day backup | Tested; missing starts limit interpretation |
| Class | Benchmark value/change only where comparable labels exist | Tested; other classes remain unknown |
| Weights/claims | Allocated/effective weight and change since last observed run | Implemented input support; NO training values recovered |
| Gear | First blinkers, blinkers off, first tongue tie/winkers | Implemented parser/input support; NO training values recovered |
| Gelding | Existing gelding status separately from explicit first-after-gelding event | Implemented input support; NO training values recovered |
| Age, pace, sectionals | Age supported in overlay; pace/sectionals need reliable additional sources | Not trained |

Unknown does not mean zero. No fixed bonus was invented for gelding, blinkers or dropping in weight. Missing flags are explicit, and a field with no training observations is inactive. The gear parser distinguishes the published change “Gelded” from an existing description “Gelding”.

## Data enrichment

Downloaded the public Mostafa Nasser TAB-derived CSV compilation: **287,840 rows**, January–15 June 2025. It contains multiple codes/international records and repeated/conflicting entries; it was not treated as an Australian thoroughbred training set by itself.

Static metadata are joined to the existing Betfair thoroughbred outcomes using exact normalised date, venue, race number and horse name, with distance agreement. After static duplicate handling and whole-field matching, **62,255 runner rows across 6,422 races** are available for this experiment. Labels come from Betfair, not the incomplete finishing-position column in the supplementary file. No fuzzy identity guessing was used.

One useful recovery: April 2025 Betfair timestamps are in 12-hour AM/PM notation. The earlier parser conservatively excluded them. The new parser recovers **1,447 eligible April races**. Original V5 results were preserved. The additional recovered April rows are used here for validation and earlier-history updates, not to rewrite old reported picks.

Earlier outcome history is drawn from retained 2020–2024 races. Jockey/trainer/condition-specific history exists only where supplementary fields were matched, largely from January 2025. A missing observed history must not be described as an unraced horse or a complete career record.

## Frozen model comparison

| Block | Period | Races |
|---|---|---:|
| Training | January–March 2025 | 3,439 |
| Validation | April 2025 | 1,196 |
| Development diagnostic | May–15 June 2025 | 1,787 |

**All these dates were exposed to earlier development.** This is a chronological feature-development diagnostic, not a genuinely fresh holdout or prospective proof. September–October 2026 was not scored again. Model design was set before fitting. Failed pre-fit runs exposed source-format issues, which were repaired before any model evaluation. No hyperparameters were tuned against diagnostic results.

Compared: market baseline; three linear market-offset L2 penalties (0.01, 0.1, 1.0); and one fixed histogram boosting classifier blended 10%/25% with market probabilities. Imputation/scaling fit training data only. All same-day outcomes are withheld until the next local date; result-publication times are unavailable, so next-day availability remains an assumption. Current outcomes, in-play prices and whole-race preplay extrema are not predictors.

Validation selected the **linear offset model with L2 = 1.0**. Validation log loss: 1.737825 versus market 1.738214. Boosting did not improve validation log loss and was not selected.

## Diagnostic result

| Metric | Market favourite / benchmark | Selected multivariable candidate |
|---|---:|---:|
| Winners | 624 / 1,787 | 622 / 1,787 |
| Win strike rate | 34.92% | 34.81% |
| Race log loss, lower is better | 1.815969 | 1.816407 |
| Multiclass Brier, lower is better | 0.781575 | 0.781712 |
| Winner among four highest probabilities | 77.17% | 76.83% |
| Quote-return proxy, illustrative 5% commission | -4.92% | -4.69% |

Selected-minus-market log-loss difference: +0.000438. Paired calendar-day bootstrap 95% interval: -0.002151 to +0.002742, crossing zero. No reliable accuracy gain is demonstrated. The candidate's tiny return-proxy advantage does not establish a value edge; both proxies lost money in this block. No actual bets were placed.

Top-four coverage describes the eventual winner's model rank, not four finishing-place predictions. Proxy returns assume fills at displayed scheduled-start exchange quotes and illustrative 5% commission on winning profit; liquidity, latency, full scratch history and reduction factors are absent. This is a conditional settled-runner sample, not a morning-tip backtest.

## Material limitations

The supplementary static fields come from historical result records, not archived publication snapshots. Going can be a final meeting condition and riders may include late replacements. These fields are useful for research but do not prove what was known at an earlier cutoff. Complete weights/claims/gear, per-race going timestamps, full finishing positions/margins, ratings, pace and sectionals remain data gaps. Model complexity cannot repair missing or mistimed inputs.

Official Racing Australia historical pages returned unavailable records for tested meetings; Racing Queensland, Racing NSW and Breednet direct requests were blocked in this environment. Existing public search snippets were not converted into invented bulk data. PuntersEdge advertises richer acceptances and bulk datasets, but the bulk endpoint requires paid tiers; no account or purchase was made.

## Safeguards and deliverables

Nine tests pass: 12/24-hour time parsing, going categories, unknown connection handling, future/unknown overlay-time rejection, same-day connections/form isolation, future-result invariance, effective weight with known claim, explicit gelding/gear-event distinction, and safe unknown historical distance handling. Delivered diagnostic probabilities sum to one for each race with exactly one label winner.

The pack includes source static data, recovered April source, joined development runners, feature matrix/coverage, fitted coefficients and scaler, saved boosting research model, validation results, diagnostic predictions/metrics, registry, tests, logs and reproduction instructions. It requires the previously delivered V5 cleaned source table alongside it for full rebuilding; the README gives the exact relative path. Pickles and model files are generated research artifacts, not a live deployment.

## Next step

Prioritise timestamped weight, claim, gear/first-after-gelding, per-race going, pace and sectional data. Use those when verified rather than assigning subjective synthetic training values. Freeze prospective predictions on genuinely future races with source timestamps and prices before making an improvement claim. Nothing was automatically connected to the nightly review or a betting account.

## Sources

Mostafa Nasser, horse-racing-ml-pipeline: https://github.com/xx36Mostafa/horse-racing-ml-pipeline

Betfair Australia Automation Hub: https://betfair-datascientists.github.io/data/dataListing/

Racing Queensland open data: https://www.racingqueensland.com.au/about/reports-and-data/open-data

Racing Australia gear/acceptance pages: https://www.racingaustralia.horse/

PuntersEdge bulk endpoint documentation: https://puntersedge.online/endpoints
