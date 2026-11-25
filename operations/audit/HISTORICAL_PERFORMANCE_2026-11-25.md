# Historical recovery and predictive performance

25 November 2026. Reviewed integration base `3c3f1ebe0cc57e2277b9b9e2078903429b66ea32`.

## Decision

Keep [PR #213](https://github.com/Spankman/Monty-Racing/pull/213) draft. The original V6 archive is restored and the replay is independently verified. Historical performance still provides insufficient evidence of an advantage over the betting market. Keep V6 as the official engine, V7 research-only, experts at zero, and production approval blocked. The research code changes neither frozen engine, production thresholds, operational commands, ticket rendering nor the five-minute rule.

## Recovery and coverage

- The existing GitHub connection could read the owner’s private checkpoint. The repository’s original restore procedure restored 28 files after their manifest hashes matched. All **55** hashes subsequently verified. The replay covered **17,987 runners across 1,787 races**, with maximum probability difference **1.6653345369377348e-16** and no fitting. Restored files remained ignored and private. The separate original V5 cleaned warm-up table was absent from the checkpoint inventory.
- Redownloaded the published Betfair monthly files. **16 of 18** matched the pins, representing 22,499 retained AU races and 216,366 runners. November’s published route returned 404. May and July 2026 failed current-publisher hashes. Retrieved both `docs` and `src` copies from all visible publisher commits touching those two paths. May’s accessible revision `ec677b9` still differed. July revisions `5bca238` and `04b4634` both differed. The pinned originals are still missing. Neither month enters this analysis or any historical feature calculation. [Publisher repository](https://github.com/betfair-datascientists/betfair-datascientists.github.io)
- Reread and rehashed the saved staging and production evidence. The live-scored sample still has **16/55** supplied values on each of 260 V6 and 178 V7 runner observations and **0%** complete active inputs. V6 uses 43 numeric inputs, 13 observed and 30 imputed. V7 uses 42 numeric inputs, 12 observed and 30 imputed. V7 uses market probability as an offset even though it is inactive as an extra correction column. Going indicators can encode unknown going, which is different from a verified condition.
- The recovered original June 2025 archive has **6,004 runners**, median **40/55** finite values, and **492 (8.19%)** complete active inputs in each frozen engine. Zero runners have all 55 fields. Coverage in the current live runner did not change. The per-feature register combines original transformations, sources, window and leakage controls with each engine’s activity and observed counts. [Original definitions and source register](Monty_V6_55_Feature_Register.csv) · [Frozen feature builder](../../monty_v6/monty/features.py)

All 30 missing active values occur in both engines. They comprise observed and trailing-year starts, win rates and market residuals, last-three and last-five win rates and residuals, track/distance/track-distance/going residuals, horse-jockey and jockey-trainer interactions, jockey/trainer 90-day and annual residuals, run recency and distance movement, benchmark class and benchmark change, and jockey/trainer changes. The inactive V6 inputs are allocated weight, claim, effective weight, weight change, unknown-going indicator, age, gelding, first after gelding, blinkers first/off, tongue-tie first and winkers first. V7 has the same inactive list plus the separate market correction input. Live supplies allocated weight, unknown-going indicator and age among the inactive V6 inputs. Counts of fields and actual evidence of usable data are evaluated separately.

A Racing Queensland historical result page for Ipswich R7 on 30 October was reachable after its robots check and has dated official race information. It linked to Racing Australia field and result pages and did not expose a registered horse identifier in the inspected links. The capture was post-race. It does not establish historical publication vintage, a live registration crosswalk or prior quote inclusion. Accepted new cross-source horse links **0**. Race number, venue, date, trip, saddlecloth and name are candidate join keys. Require a stable authority registration ID and corroborating source identifiers; reject conflicts and defer same-local-day outcomes exactly as the original feature builder does. [Historical authority page](https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/ipsw/20261030/race/7)

## Predictive performance

Two datasets answer different questions. The original June 1–15, 2025 archive is the actual V7 fold 3 test period and was previously exposed to research. It can test the contribution of the genuinely recovered feature matrix. The 2026 sample uses three observed pre-off columns and frozen imputation. It can test sparse deployment proxies chronologically after model fitting. Neither is untouched prospective evidence. The later sample has June and August–October only. Going and verified pre-race race type cannot be inferred from the exchange data. The study publishes raw source class strata, with unknown going explicitly identified, and condition strata from the original archive.

| Dataset / arm | Races | Log loss | Race Brier | Top strike | Top-pick exchange ROI proxy |
| --- | ---: | ---: | ---: | ---: | ---: |
| June 2025 market / minimal V6 | 584 | 1.908782 | 0.810598 | 32.36% | −6.35% |
| June 2025 V6 with original inputs | 584 | 1.905764 | 0.809833 | 32.02% | −6.48% |
| June 2025 minimal V7 | 584 | 1.904979 | 0.809275 | 32.36% | −6.35% |
| June 2025 V7 with original inputs | 584 | 1.904216 | 0.809116 | 31.85% | −7.88% |
| 2026 market / minimal V6 | 5,512 | 1.779461 | 0.772913 | 35.07% | −1.78% |
| 2026 minimal V7 | 5,512 | 1.781385 | 0.773561 | 35.07% | −1.78% |

In June 2025, original minus minimal log loss was **−0.003018** for V6 (day-block 95% CI −0.008271 to +0.002533) and **−0.000764** for V7 (−0.005455 to +0.004314). Neither reliably improved ranking, strike or simulated top-pick returns. In the later sample V7 log loss was **+0.001924** above the market (+0.000686 to +0.003069), with the same mean winner rank of 2.948 as the market and sparse V6. The frozen models remained unchanged. A rich-input 2026 comparison awaits compatible feature coverage.

## Roughie threshold

The earlier report’s staging watches were confirmed. New simulations apply the frozen models, exclude underrounds from policy eligibility, and compare a 6% probability floor, 3%, no floor, a commission/price-haircut hurdle and a chronological uncertainty hurdle. Estimate a lower observed/expected ratio by odds band on earlier dates (July 2025–April 2026) using a day-block bootstrap. Require at least 100 candidates and 30 prior dates. The haircut reduces gross winnings by 2% before an assumed 5% commission. The band-level bound is a sensitivity test and supplies no per-horse confidence guarantee. Evaluate all approaches on June and August–October 2026 without picking the best-looking rule after seeing results.

| V7 price | Point EV + 6% floor | Point EV + 3% floor | Point EV without floor |
| --- | ---: | ---: | ---: |
| Below $4 | 0 | 0 | 0 |
| $4–$5.99 | 139 / −23.72% | 139 / −23.72% | 139 / −23.72% |
| $6–$9.99 | 2,014 / −8.00% | 2,014 / −8.00% | 2,014 / −8.00% |
| $10–$19.99 | 7,019 / −9.11% | 8,908 / −9.59% | 8,908 / −9.59% |
| $20–$39.99 | 0 | 7,675 / −3.96% | 8,458 / −4.87% |
| $40+ | 0 | 0 | 13,037 / −8.91% |

Cells show runners and exchange proxy ROI. The $10 band no-floor interval was −16.15% to −2.98%. The $20 band no-floor interval was −15.41% to +5.74%. Exchange commission plus price haircut alone admitted 307 candidates in the $10 band with −38.98% quoted-price proxy ROI. The earlier-band uncertainty bound eliminated all candidates across every arm. The 6% cutoff restricts the search but these data do not establish that it is optimal. Lowering it is unsupported. These results use scheduled-off best-back and flat per-selection stakes, with no verified fills, offered stake sizes, book settlement, or exchange net-market commission accounting. No exotics were simulated without verified dividends and costs.

The restored archive also permits a full-input roughie comparison. On the 15 previously exposed June 2025 days, full-input V7 selected 326 positive-after-commission $10–$19.99 runners with +41.55% proxy ROI and 554 in the $20–$39.99 band with +35.23%. Minimal V7 already showed +89.11% in the first band on 154 runners. Full-input V6's $10-band result was +14.06% on 133 runners, with a day-block interval from −45.68% to +93.04%. Full-input V6 and V7 $40-plus results were negative. These exploratory stratified results use different selected sets, no adjustment for multiple comparisons and a brief, previously examined period. The sparse later data show that the shorter-band positive proxies did not persist. An incremental longshot benefit from recovered history remains undemonstrated.

## Independent acquisition, subscriptions and prospective evidence

A separate scoped, read-only Actions source probe completed at **05:09:37 UTC**. Racing Queensland’s Ipswich R7 page was permitted and returned 200. It supplied Soft 5 and scheduled jump 06:33 UTC. TAB and Sportsbet stopped at unavailable robots policies. This corroborates an unattended access barrier while leaving the earlier race-page 500/403 results as separate observations. No issue or results-branch publication, production job, wager or prospective freeze was triggered by the probe. A complete independently verified Australian race still requires permitted named fixed-win access, final emergencies/scratchings reconciliation and compatible as-of identity/history. [Actions run](https://github.com/Spankman/Monty-Racing/actions/runs/45551557613)

- **Betfair** free monthly data is useful for the original scheduled-off market component and retrospective labels. It does not supply the complete contextual feature set or establish executable named fixed-win odds. Preserve the source pins and keep unsupported months out of history. [Data documentation](https://betfair-datascientists.github.io/modelling/dataSources/)
- **Racing Australia and state authorities** are sources for official registration, declared fields, track, connections and results. Racing Queensland Open Data describes a limited calendar/contact API and published race datasets. It offers a practical primary-source route for the first AU jurisdiction. Field and result snapshots must be obtained with published, usable as-of timestamps. [Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data) · [Racing Australia](https://racingaustralia.horse/)
- **Krok** documents field-form and runner-form, 50 free monthly credits and 14-day racing odds history on Free. API terms list A$79.99/month for the paid API tier. The potential saving applies only if existing usage fits the free allowance and required endpoints. No billing record or successful volume trial was available. Krok named prices require independent verification. Served BSP, SP and fixed-win histories do not substitute for original full-field scheduled-off best-back. [Racing form endpoints](https://krokodds.com.au/api-docs/racing/form) · [Krok plan terms](https://krokodds.com.au/terms)
- **FormFav** offers form and named live prices, with Pro results availability. Its authority SP and bookmaker last-fixed-win fields differ from the original exchange input. It is optional for the current runner. Test licensed source lineage and quote timestamp on a same-race sample before using it as an independent operator feed or paying for archive access. [FormFav tiers](https://formfav.com/docs/subscription-tiers) · [Prices](https://formfav.com/docs/endpoints/prices)

Prospective admission and official settlement remain **zero**. The current approval evaluator remains shadow-only and production decisions without the required evidence are DATA BLOCKED. The research uncertainty hurdle cannot authorise a bet and does not prove a genuine production NO BET. Expert effects remain unestimated. No eligible settled expert cohort exists for testing conditional 90/10 against 100/0 on matched historical and market inputs. Fee changes, threshold changes and expert activation remain owner decisions.

## Task register and acceptance sequence

| Status | Work |
| --- | --- |
| Done | Restored and verified the original checkpoint, replayed stored V6 probabilities and resolved five prior local missing-artifact failures. |
| Done | Rehashed historical monthly downloads, checked available upstream revisions and retained quarantine. |
| Done | Reproduced original-feature and sparse scoring, chronological threshold sensitivity, full odds-band and condition/class diagnostics. |
| Done | Ran read-only Actions source probe, with official authority data available and independent fixed-win unavailable. |
| Open | Recover May/July pins and the original V5 warm-up. Resolve authority registration and timestamped race participation before creating a current rich-input join. |
| Open | Acquire licensed or documented permitted independent bookmaker quote access. Match authority declarations, final emergencies, scratches, going, jump, identity and compatible history inside Actions. |
| Open | Predeclare cohort entry, odds/fee assumptions and day-clustered metrics. Freeze common V6/V7/market inputs, quotes, qualification and rejection reasons before jump. Settle with separately hashed official results. Keep nonadmitted cases in the coverage denominator. Record assessed yield and P&L separately by model and bet type. Use verified dividends and stake costs for each exotic permutation. |
| Open | Validate calibrated executable win-price approval on the common prospective cohort. Evaluate experts on identically priced settled forecasts with clustered source lineage. |
| Open | After owner authorisation, run ordinary issues, schedules, repeated requests, boundary expiry and jump, fresh-conversation C/hash retrieval and iPhone acceptance. Keep the previous production SHA and immutable result refs for rollback. |

Reproduction: restore the original manifest-backed V6 artifacts with authorised access, use the pinned V7 checkout and retain the published monthly filenames as YYYY_MM.csv. From the repository root run `python -m operations.audit.price_policy_study MONTHS PINNED_V7_CHECKOUT NEW_OUTPUT_JSON`. Private inputs remain local. The output includes per-band EV, calibration, clustered intervals and replay coverage. The separate Actions probe branch is evidence only.

## Copyable ChatGPT handover

```text
Monty Racing, draft PR #213. Keep unmerged and do not deploy.
V6 official; V7 research-only; 100% model / 0% experts. No wagers.
55 V6 hashes verified. Exact restored replay: 17,987 runners, 1,787 races.
Live coverage still 16/55. May and July Betfair remain excluded by hash.
No demonstrated market advantage. No threshold changes: lowering V7's 6% floor added many losing or statistically inconclusive longshot candidates.
Read-only Actions reached Racing Queensland. Direct independent pre-off bookmaker verification remains blocked. No admitted prospective races or settled results.
Next: reconcile one AU race with primary field and final status, named quote and authorised as-of history. Freeze V6, V7 and market forecasts before jump, then settle on a separate official hash. Extend to a predeclared cohort before approving bets.
RM6, RM7, RM6PS, RM7PS and single-race variants are unchanged. Bare meeting/race uses V6. C reads the original request only. Check the receipt and forecast hashes, compact manifest if applicable, five-minute freshness and scheduled jump.
```
