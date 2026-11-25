# Monty independent predictive research

26 November 2026, Brisbane · `FUNDAMENTALS-AU-20261126` · Research only

## Decision

The historical form block adds genuine signal relative to the weaker form-only model, but the signal does not demonstrate incremental skill beyond the market. Keep the market-only calibration control in every future comparison. Prioritise independently sourced form and runner identity before further complexity. No recommendations to activate new weights, change roughie thresholds or promote a model.

## Preflight

Reviewed the [governing documents](https://github.com/Spankman/Monty-Racing/tree/4bf8ddf01ff221081f5abce526fd6e84f55b70ab) at PR #234 `4bf8ddf01ff221081f5abce526fd6e84f55b70ab`: AGENTS.md, Living Development Plan and Research Library (25–26 November), shared baseline handover (26 November), Betting Policy, Selection Rules and operating guidance, including no extra live credits, owner-approved $4 progression and research safeguards. A separately designated current master handover remains unavailable. The 26 November baseline handover supplies an interim index.

Reviewed [issue #240](https://github.com/Spankman/Monty-Racing/issues/240) and the [26 November audit handover](https://github.com/Spankman/Monty-Racing/blob/cd775dc07a0a716ecb47a6e4db934c5fb451a72a/operations/audit/RUFFIE_AUDIT_2026-11-26.md) at draft #241 `cd775dc07a0a716ecb47a6e4db934c5fb451a72a`, the code base for this research. Reviewed the preceding historical recovery and ablation evidence. The audit already measured the 5,512 later sparse races: market 1.779461, V6 1.779461, V7 1.781385. Those are archived fixed-engine results. This study addresses a different question by training independent probabilities on richer dated history, so its pooled 2025 loss values are not comparable with those later sparse figures.

Production ref inspected: `623d46b449e46cfc5fa63b633c3f19b404bba41a`. Six-day trial snapshot reviewed for boundaries: #235 `84689048a374f2af824da77057623d20809f6baa`. No trial branch, evidence or automation changed. Zero live provider calls or credits, purchases or subscriptions. Frozen V6 official, pinned V7 research-only. No activation, deployment, billing, betting rules, thresholds, freshness or reporting changes.

## P0 — Data recovery and coverage

| Source | Recovered or verified evidence | Decision and gap |
| --- | --- | --- |
| Original private checkpoint and joined AU archive | Restored 28 files against existing pins. All 55 V6 artifact hashes verified. 62,255 runners and 6,422 races, Jan–15 June 2025. Non-null: barrier 62,255, jockey 62,253, trainer 61,728, class text 61,421, going text 62,255. | Archive is a retrospective enriched subset. Source publication vintage and national horse/jockey/trainer registration crosswalk remain unverified. Benchmark-class change is present in only 5.30% of inputs. No observed weight, age, gelding or blinkers-first fields in this checkpoint subset. Preserve unknowns. |
| Betfair historic monthly archive | Prior audited 16 pinned months, 22,499 retained AU races. This run checked hashes of May and June 2025 settlement-only place files. 17,864 runner rows eligible for two/three-place conditional diagnostics. | Scheduled-off best back is an exchange price proxy. May and July 2026 stay quarantined as in #241. Official final scratchings and a separate settlement feed are still required for prospective validation. Keep raw data private. |
| Racing Queensland | Locally rehashed all three previously acquired official sectional files against the existing validated receipts. 26 races, 342 runner rows, 1,713 populated segment measures, 509 missing segment entries, 79 runner rows without measurements. | Free public access was previously verified for these files. This establishes sparse availability, and no cohort join or rights to redistribute raw files. Use the authority's stewards and sectional indexes to build dated event-level links with official registration and original publication timestamps. |
| PuntersEdge | Rehashed the saved September 2026 closing-line export against the published audit. 55,420 AU thoroughbred rows, 1,283 races. Example: TAB has 436 provider-union-complete vectors and 20 with the same integer capture offset. Prior Launceston form capture returned 99 past runs. | Attributed public sample is CC BY 4.0. Provider-union coverage and coarse offsets do not establish independent field completeness, verified quote vintage or executable prices. No same-cohort fixed-win joins in this study. Private API records require their own terms. No credits consumed. |
| Racing Australia and state authorities | Prior authority declarations/results and Queensland historical examples provide join leads. The source audit records access restrictions on national and NSW pages and incomplete VIC, SA, WA and TAS retrieval. | Prefer official registration, declared changes, settled results, gear and reports. Use permitted public files or an authorised feed. No name-only joins, inferred gear, or cross-state equivalence claims. |
| Krok and FormFav | Prior Krok meetings and field-form served genuine responses. Earlier FormFav access and current public documentation are documented by the existing data audits. | No new account access or calls. Actual remaining entitlement, retention rights, usable full historical timestamped books and subscriber-only prices remain unknown. Reuse authorised private archives first. No cost or renewal assumptions. |
| Pedigree and hidden form | Breednet and authority links are candidates. Racing Queensland has published sectional and stewards-report indexes. | No evidenced pedigree histories, incident labels or reliable lane/cover series in the test cohort. No guessed interference or performance from finish rank. No raw republishing. |

P0 implementation interface for Codex: private race and runner keys tied to authority registration and dated race entries, source URL and checksum, source observation/published time and ingestion time, source licence, definition/version and research outcome timestamp. Preserve observed draw, weight/claim, class, distance, going, gear change operation and prior runs independently of current fixed-win snapshots. Add stewards event type and timestamp, source text pointer, reliability label, section start/length/time and missing reason. Final scratchings and official standings belong on a separate settlement record. Verify same upstream provenance before claiming independent corroboration. Fail unresolved joins closed. Do not mutate the trial or overwrite older audited evidence.

[Betfair data definitions](https://betfair-datascientists.github.io/modelling/dataSources/) · [Authority open data](https://www.racingqueensland.com.au/about/reports-and-data/open-data) · [Sectionals](https://www.racingqueensland.com.au/racing/replays) · [Stewards reports](https://www.racingqueensland.com.au/racing/race-day-stewards-reports) · [PuntersEdge archive and licence](https://puntersedge.online/datasets) · [Source and cost inventory](AU_FREE_SOURCE_REGISTER_2026-11-25.csv)

## Academic methods and replication status

| Source | Implementation and limitations |
| --- | --- |
| [Bolton & Chapman, 1986](https://doi.org/10.1287/mnsc.32.8.1040), [paper](https://www.fsb.miamioh.edu/lij14/411_read_horse.pdf) | Implemented the race-conditional multinomial likelihood with shared runner coefficients. Added predeclared L2 shrinkage. Independent model uses an Australian feature set and day-aware fitting. Method reproduction, not a replication of the original dataset or reported returns. |
| [Benter, 1994](https://gwern.net/doc/statistics/decision/1994-benter.pdf) | Trained a separate fundamental model, then fitted race-normalized exp(a·log p_form + b·log p_market) on later previously unscored calibration races. The logits used in code differ from the log probabilities by race constants that cancel. Reproduces the two-stage functional method with mild L2 shrinkage and different datasets and windows. Completeness-interacted form weight and boosted ensemble are Monty extensions. No historical expert weight reused. |
| [West & Kazakov, 2024](https://www.ubplj.org/index.php/jpm/article/view/2093) | Publisher confirms PLS classification study. PDF wrapper located and download was unavailable in this session. Four-component PLS regression plus race logit is explicitly PLS-inspired. Paper-specific preprocessing, odds inclusion, variable filtering and staking results were not reproduced. |
| [Smith & Vaughan Williams, 2010](https://doi.org/10.1016/j.ijforecast.2009.12.014), [Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a.html), [Clarke et al., 2017](https://doi.org/10.11648/j.ajss.20170506.12) | Measured calibration across odds bands and fitted a temperature/power on market-only scores. Distinguish calibration from adding form. Historical exchange normalization differs from choosing a de-vigging method for a named bookmaker. No paired fixed-win Shin or power-margin test run. |
| [Harville, 1973](https://doi.org/10.1080/01621459.1973.10482425) | Implemented sequential conditional finishing probabilities for top-two/top-three marginals. Archived settlement determines which place-count diagnostic to evaluate; this is a conditional historical diagnostic and cannot supply advance market terms. Full orders and exotic ROI not validated. |
| [Friedman, 2001](https://doi.org/10.1214/aos/1013203451), [Lessmann et al., 2010](https://doi.org/10.1016/j.ijforecast.2009.12.013), [Silverman & Suchard, 2013](https://doi.org/10.5750/jpm.v7i1.595) | Tested a histogram-gradient-boosting challenger and a later fitted market ensemble. Used regularised conditional logit as the parametric baseline. This comparison does not reproduce the historical gradient boosting, racing random forest or profit-regularized implementations. |
| [Rosenbloom, 2003](https://doi.org/10.1016/S0305-0483(03)00053-7), [Spence et al., 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3391435/) | Adjusted speed and pacing/drafting justify acquisition tests. Publisher abstract for speed and open methods for pacing were checked. No matched historical figure or timing cohort with suitable publication evidence here. No speed, drafting or pace replication claim. |

## P1 — Chronological results

Four expanding fit windows, each followed by a separate calibration window and then disjoint March, April, May and 1–15 June 2025 evaluation blocks. Imputation, scaling, supervised projection and candidate fitting were fit-period only. Each blend and market control used only the intervening calibration period. Prior-form labels update after the entire local day. The base independent form design excludes current and prior market price variables and market residuals. The extended variant uses the previous start's observed exchange favourite and previous outcomes after the relevant racing day. Those inputs do not incorporate the target race's price or outcome. Horse identity uses the archive proxy; context publication vintage is unverified. The June matched V6/V7 reference was previously exposed. No matching 2026 enriched independent assessment, untouched confirmation or prospective settlement is claimed.

Lower log loss and Brier are better. Win strike and ROI refer to the highest-probability runner per race. ROI is an exchange scheduled-off quote proxy with assumed 5% commission on each winning return.

| Arm | Pooled log loss · 4,129 races | Race Brier | Top win strike | Top quote-proxy ROI | June log loss · 584 races |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raw market | 1.761018 | 0.766630 | 36.38% | −2.19% | 1.908782 |
| Calibrated market | 1.760747 | 0.766689 | 36.38% | −2.19% | 1.905301 |
| Fundamental conditional logit | 2.242017 | 0.888453 | 13.47% | −5.68% | 2.305763 |
| Fundamental with prior-start/connection block | 2.158321 | 0.869745 | 20.37% | −3.30% | 2.210666 |
| Benter-style combined | 1.762064 | 0.767258 | 36.38% | −2.41% | 1.909504 |
| Completeness-adaptive Benter-style | 1.762099 | 0.767289 | 36.35% | −2.47% | 1.909523 |
| Prior-start/connection blend | 1.760875 | 0.766772 | 36.18% | −2.91% | 1.905314 |
| PLS-inspired fundamental | 2.240342 | 0.888755 | 13.34% | −6.08% | 2.308488 |
| Boosted fundamental | 2.247732 | 0.891342 | 13.15% | −4.69% | 2.298906 |
| Boosted plus market | 1.762266 | 0.767515 | 36.18% | −2.95% | 1.905465 |
| Frozen V6 | — | — | — | — | 1.905764 |
| Frozen V7 | — | — | — | — | 1.904216 |

The prior-start/connection blend's loss difference vs raw market is −0.000143 (day-bootstrap 95% interval −0.001558 to +0.001241), and +0.000128 (−0.000930 to +0.001177) vs calibrated market. Relative to calibrated market the base Benter, adaptive and boosted combinations each worsened pooled loss with pointwise day-bootstrap intervals above zero. Fitted form coefficients shift across folds, including reversal in April. Completeness is an availability signal only and the tested interaction does not justify activating adaptive weights. Pooled place strike on top picks with known place labels was 67.06% market, 66.89% extended blend and 47.53% extended fundamental. Conditional Harville runner-place Brier was 0.16619 market vs 0.16624 extended blend. Class and going strata, calibration bins, fold and paired results are in the aggregate JSON. Intervals are exploratory, pointwise and conditional on trained fits. They do not adjust for repeated method comparisons.

## P2 — Extended findings and priorities

- Trainer Intent: the five prior-event interaction features plus four role-history features improved the odds-free comparison, but cannot isolate trainer intent. Last-start winner and beaten-favourite coverage was 15.39% and 15.16%, respectively. Class change 5.30%, jockey history 97.30% and trainer history 93.53%. Run a preregistered block ablation on later authority-linked history to separate contributions. Gear, gelding, reapplication and current price-movement hypotheses remain open.
- Pedigree and hidden form: no fit. Secure sire/dam/damsire registration links and rolling progeny counts, and pair with dated authority sectionals and stewards events. Test going/distance, debut and exposed-form groups with shrinkage after obtaining cohort-level coverage.
- Roughie Score: explored positive model uplift and positive fee-adjusted point EV on books at or above 100%. No production gate changes. For the extended blend:

| Exchange quote band | Attempts / wins | Net ROI proxy | Day-bootstrap 95% | ROI zeroing three largest payouts |
| --- | ---: | ---: | ---: | ---: |
| $10–19.99 | 218 / 25 | +55.28% | −0.11% to +114.14% | +30.80% |
| $20–39.99 | 536 / 24 | +19.86% | −28.81% to +69.74% | −0.02% |
| $40–59.99 | 410 / 13 | +46.60% | −15.92% to +118.79% | +8.33% |
| $60+ | 2,398 / 15 | +11.75% | −52.72% to +106.92% | −37.78% |

All four intervals include zero. The market-only recalibration comparator also produces apparent longshot returns in this proxy. Concentrated payouts, price availability, multiple arm/band comparisons and unknown fills preclude an independent roughie edge claim. No place-price ROI or exotic ROI is estimated. Keep named fixed-win historical simulation and independently verified prospective settlements as separate future cohorts.

## Reproduction and handover

Use Python 3.12 and the recorded aggregate software versions. Restore the original private checkpoint with `restore_archive.py`, have the pinned May/June 2025 Betfair CSVs available privately, and check out V7 at `efc51abb1595ef1eb8417e2d4e0d591f6d3c9378` (model digest checked). For reproducibility:

```sh
PYTHONPATH=monty_v6 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -q test_fundamental_study
PYTHONPATH=monty_v6 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m operations.audit.fundamental_study --months PRIVATE_MONTHS --v7 PINNED_V7 --output PRIVATE_OUTPUT.json
```

Four new checks cover race normalization, training-only preprocessing, place mass and current-price/current-label/same-day invariance. [Aggregate results and archive hashes](FUNDAMENTAL_STUDY_RESULTS_2026-11-26.json). An independent rerun of the local command produced byte-identical JSON. The 22 combined local tests passed (four new and 18 inherited roughie tests). The published JSON uses sorted keys and compact separators and has SHA-256 `197d242d0e87e24168dd348f9f2983eb63a2d44defb6ec7dff2da28b49234393`. Raw licensed records are not committed.

Next: Codex to retain complete pre-inference observations through the documented #241 interface and build authority crosswalk and cutoff-aware research joins. Reuse existing acquisition evidence and immutable monthly pins. Research to preregister a later paired comparison with market calibration, recovered form and form-block ablations before further hyperparameter or feature search. Review authorised fixed-win archive access and alternate identifiers without spending credits on this workstream. Once qualified, freeze forecasts against the independent market baseline and settle against official results in a separate prospective cohort. Keep trial, frozen engines and betting thresholds as currently governed.

IN MONTY WE TRUST.
