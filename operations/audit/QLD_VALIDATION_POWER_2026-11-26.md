# Queensland validation power and sample-size assessment

26 November 2026, Brisbane · design sensitivity · no validation outcomes opened.

The [v1 preregistration](https://github.com/Spankman/Monty-Racing/blob/29239357579422148091a3320401d5e0572d774c/operations/audit/MONTY_INDEPENDENT_VALIDATION_2027Q1.md) remains authoritative. Keep 4 January–28 March 2027 inclusive (84 days), fit through 29 November, 1–27 December calibration, the original admission rules, frozen arm selection and day-clustered inference. This memo predeclares an interpretation and design sensitivity. It does not amend the cohort or approve acquisition.

## Planning inputs

The #246 historical calendar pilot showed 15 non-trial meetings over one June week. Using that count, **eight races/meeting is a planning assumption**, giving 120 races/week and about 1,440 census races in 12 weeks. The actual Jan–Mar calendar, total eligible races, admissible days, scratchings, bookmaker coverage and label count are unknown. This one historical week is not a seasonal calendar forecast. At 25%, 50%, 75% and 100% admission the implied counts are 360, 720, 1,080 and 1,440 races. Current actual pilot has zero pre-jump trainable rows. Admission could be zero; never forecast positive coverage from this study. At most 84 potential day clusters, and likely fewer represented.

Pairs are whole races. Never count runners as independent wins. For the primary, use #244's paired Benter-style full blend versus calibrated market 95% day-bootstrap interval [−0.0011961,+0.0017920] on 4,129 retrospective AU races to infer a **historical effective** SD: interval width divided by 2×1.96, multiplied by √4,129 = 0.048983. This folds the historical race/day dependence into the calibration of the planning variance. Do not multiply it again. Transfer to new Queensland fields is uncertain. The stressed sensitivity uses 0.075. There is no held-out training replicate in either variance. Refitting/cohort variability can be larger.

Design at two-sided 5% and 80% power. A normal approximation gives detectable effect `(1.960 + 0.842) × effective SD / sqrt(N)`. Required sample is the squared inverse relation. Approximate test power includes both tails. For secondary strike/calibration/ROI planning use illustrative design effect 1.4 (equivalent to 9 observations per group at ICC .05 with equal sizes). Recompute using actual **earlier-only** grouped dispersion and capture counts, allowing unequal day size and correlated consecutive days. A general design-effect sensitivity is `1 + [(1+CV²)m−1] × ICC`. Power can fall with fewer represented dates, large meetings or serial dependence. In final reporting use the preregistered day bootstrap and disclose a frozen seven-day grouped robustness check if sufficient distinct blocks, without replacing the primary result. Small-cluster results are inconclusive where interval assumptions are unreliable.

## Primary result and adequacy

| Assumed admitted races | Detectable absolute log-loss improvement | Stressed detectable improvement | Power for 0.002 | Power for 0.005 |
| ---: | ---: | ---: | ---: | ---: |
| 360 | 0.00723 | 0.01107 | 12% | 49% |
| 720 | 0.00511 | 0.00783 | 19% | 78% |
| 1,080 | 0.00418 | 0.00639 | 27% | 92% |
| 1,440 | 0.00362 | 0.00554 | 34% | 97% |

At the historical effective spread, 80% power needs about **18,833**, **4,709** or **754** races for improvements of 0.001, 0.002 or 0.005 respectively. Stressed equivalents are 44,150, 11,038 or 1,766. At 60 admitted/week the 0.002 target translates to about 79 weeks under the historical spread, including any usable initial period if an independently specified synthesis is authorised. This is a scale estimate, not a scheduling instruction. At 720 races power for 0.001 is 8.5%.

One primary contrast: **two-stage Benter minus calibrated market on mean race-level log loss**, as already preregistered. Freeze the book, values, coefficients, exact trained data and manifest before the window. Use the identical admitted runner/race set and 10,000 Brisbane-day cluster-bootstrap draws at the registered seed. Negative values favour Benter. The upper 95% limit below zero is evidence of improvement in this cohort. An interval spanning zero is inconclusive. Report 0.001/0.002 planning-effect values and their relation to the interval separately. They do not change the preregistered statistical test, have no status as betting or promotion thresholds, and should be owner-reviewed before powering a separate confirmation. Independent form scores are reported regardless of whether standalone beats market. Win-only economics is a separate follow-up gate. Do not promote on a significant small effect or null result alone.

Readiness and statistical adequacy are separate. The existing readiness gates are unmet at this review. If any already specified input, timing, complete-price, trust, rights or pre-test manifest requirement fails at freeze, record **BLOCKED**. If readiness passes and the race count is low, publish the locked window transparently as a potentially inconclusive initial evaluation. Additional powered evidence belongs to a new untouched prospective window with an analysis and stopping date registered before its first result. Do not extend this window in response to observed estimates, top up until significance, or reuse its outcomes for model selection. Finishing order and all recent roughie subgroups are secondary.

## Secondary design and sample scale

| Endpoint at 720 paired races | Assumptions | Approximate sensitivity |
| --- | --- | --- |
| Summed multiclass race Brier | Illustrative effective SD of paired difference 0.05–0.10, because no paired archive dispersion is published | Detectable improvement 0.0052–0.0104. For 0.005, roughly 785–3,140 paired races. |
| Calibration-in-the-large within one bin | Illustrative nominal probability 10%, one effective observation/race before day design effect 1.4 | Detectable deviation about 3.7 percentage points. Detecting 2 points takes roughly 2,473 comparable bin entries, and 1 point 9,890. Real sparse/empty bins need coverage counts. Group runners into races/days for residuals. |
| Top-pick win strike | Both locked arms compared on the same races. Illustrative total discordant win outcomes 10%, design effect 1.4 | Detectable gain about 3.9 percentage points. For a 2-point gain, roughly 2,748 races. Discordance range 5–20% changes the 720-race MDE to 2.8–5.5 points. Known-place strike requires verified terms and its own denominator and discordance. |
| Paired win-only ROI versus market top picks | Matched equal one-unit exposures, prior-only paired per-race return SD scenarios 0.5, 1, 2 units, design effect 1.4 | Detectable gains about 6.2, 12.4 or 24.7 ROI points. Keep same price availability/time policy across arms, show turnover and return discrepancies. |
| Win-only ROI versus break-even | One selection per race at illustrative effective gross payout 3.0, after any applicable deduction/slippage | At 720 independent selections, exact upper-tail power for +10% margin about 45%. About 2,228 selections for +10% with the planning design effect, and 8,854 for +5%. This is scenario sizing, not a claim of achievable pricing. |

### Roughie take-up and rare returns

The selection rates below arise from the earlier #244 blend's **research exchange** screen counts (348, 617, 448, 2,442 over 4,129 races). Multiple eligible selections can occur in a race. They are deliberately illustrative and may overstate official selections. A funding or model requirement is never inferred from these counts. The high band spans variable odds. Prices in this grid are illustrative *effective* gross payout after costs, not observed offers. First, an independent homogeneous binomial favourable-tail exact calculation tests p0=1/payout vs p1=1.10/payout with upper-tail size ≤2.5% to match a two-sided 95% sign criterion. Dependence and uneven bet times make actual power less reliable. Then invert a normal approximation with separate null/alternative Bernoulli dispersions and design effect 1.4 for planning requirements.

| Decimal band | Example effective payout | Projected selections at 720 | Expected wins at break-even | Independent exact power for +10% | Approximate selections needed at +10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| $10–19.99 | 15 | 61 | 4.07 | 3.3% | 15,804 |
| $20–39.99 | 30 | 108 | 3.60 | 1.8% | 32,773 |
| $40–59.99 | 50 | 78 | 1.56 | 2.9% | 55,399 |
| $60+ | 80 | 426 | 5.33 | 3.6% | 89,338 |

Treat band-level findings as exploratory. At these win counts, empirical resampling may omit payout values it never observed and give misleading certainty. Report group sizes, exposure, wins, break-even conditions, pre-jump clock drift, disallowed/missing selections, ROI, date-block intervals when support exists, and stress zeroing one and three highest winning payouts with all stakes retained. Never report paper simulations as realised returns. Compare spread across meeting/date strata, stable in-window quote changes, stake limits, locked named fixed-win terms, deductions/dead heats, price slippage and selection bias. Compare exchange proxies separately with commission. Treat adverse price assumptions explicitly and record unavailable executable offers without imputation. No wagering in this work.

Prespecify one confirmatory score, with secondary odds, timing and model families labelled descriptive. If later elevating four bands to confirmatory use a sequential/Holm procedure or conservative per-band alpha .0125, specified beforehand, and cluster inference. This raises required sample beyond the unadjusted grid. Disclose admissions versus census by day, race type, field size and operator, reasons for non-admission and small numbers. Do not extrapolate covered-book results to all races or infer the selected sample is representative. Use no test outcome to fit, calibrate, choose thresholds, remove observations or advance the end date.

## Reproduction

Run `node operations/audit/qld_validation_power.cjs` with no data dependencies. The numerical grid is also committed as [JSON](QLD_VALIDATION_POWER_2026-11-26.json). The script checks monotonic MDE/sample-size cases and an exact-binomial null tail bound. It uses fixed inputs from the [historical published aggregate](https://github.com/Spankman/Monty-Racing/blob/29239357579422148091a3320401d5e0572d774c/operations/audit/HISTORICAL_BLOCKS_2026-11-26.json). Verify scenario assumptions using approved training/calibration period records only and prior to any later preregistration. Method references: [clustering and variable cluster sizes](https://academic.oup.com/ije/article/52/5/1648/7172835) and [proper forecasting scores](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).

This is statistical design work before the future cohort. No acquisition, predictions, fit, wagers, deployment or trial changes occurred.

IN MONTY WE TRUST.
