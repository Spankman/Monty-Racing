# Prospective statistical power assessment — planning only

26 November2026; exact source protocol #244 `29239357579422148091a3320401d5e0572d774c`, version1. **No formal cohort, endpoint, cutoff or protocol file changed. No target outcomes opened, model fitted or forecast generated.** Reproducible outputs: `python -m operations.audit_alignment.power OUTPUT.json`; all inputs are disclosed scenarios, not estimated prospective results.

## Decision

The4January–28March2027 window is84calendar days. Verified future eligible race/selection counts, full-book availability, paired loss/Brier variance and day/meeting dependence are unknown. A defensible **achieved-power or calendar-sufficiency claim is therefore unavailable**. Current strict training/calibration/rights/candidate gates remain unmet: readiness is BLOCKED until satisfied before their existing deadlines. Nothing in this assessment waives them.

The window could inform moderate predictive differences if enough matched races are admitted, but cannot be presumed sufficient for tiny incremental market gains or rare-longshot profitability. Under stated scenarios below, detecting a0.001paired log-loss improvement needs tens of thousands of races, while500longshot bets provide very low power for10%ROI even under optimistic assumptions. Recommend treating the fixed window as a limited independently verified validation cohort and, if precision is inadequate, preregistering an additional later cohort before its outcomes. Do not extend/redefine the existing cohort retrospectively, pool populations without declaring heterogeneity or tune against its results.

## Primary paired endpoint

Existing primary remains mean race log-loss difference **Benter blend minus calibrated market**, negative better, with10000whole-Brisbane-day bootstrap draws/seed20261126 and a95%interval. A confidence interval spanning zero remains inconclusive, not evidence of equivalence. Secondary arms remain secondary. The independent fundamental need not beat market standalone; test whether its contribution improves the combined model on the same eligible races.

Normal planning approximation:

`n = ceil[D * (z(1-alpha/2) + z(power))² * paired_SD² / effect²]`.

D is an explicit clustering/design-factor scenario, not an estimated correction; runners are never independent sample units. Desired effects below are **illustrative research planning magnitudes, not newly approved betting thresholds or protocol success criteria**. Real day-block/participant serial dependence and unequal day sizes require a pilot-based cluster simulation, not plugging in an invented D.

At pairedSD0.05,design1.5,alpha0.05,two-sided80%power:

| Absolute log-loss improvement | Required admitted races |
| --- | ---: |
| 0.001 | 29,434 |
| 0.002 | 7,359 |
| 0.005 | 1,178 |

At the same assumptions,500/1000/1500races have minimum detectable differences0.00767/0.00543/0.00443. At the more favourable SD0.02, counts fall by a factor0.16; at0.10they increase fourfold. Machine-readable grid includes80/90%power,SD0.02/0.05/0.10,design1/1.5/3and alpha0.05 versus0.05/6. These are sensitivities, not assurance those sample counts will exist in Queensland.

The already-examined #244 historical4129-race interval[-0.001196,+0.001792] implies a rough normal-equivalent effectiveSD≈0.049. This is only an order-of-magnitude diagnostic: its exploratory old population, fitted models, source-vintage gaps and clustered bootstrap make it **not** independently verified variance for the target cohort. Do not double-apply a design factor to that historical effectiveSD and claim an empirical calculation.

## Other endpoints and rare-event precision

- **Race Brier:** use paired summed multiclass race score differences and their own verified earlier pilotSD, not runner-level Bernoulli counts or the log-lossSD. The same grid/formula supplies sensitivities, but no Brier sample-size claim is made without that variance.
- **Win strike:** paired top-pick comparison depends on discordant races. At20%discordance,2percentage-point improvement anddesign1.5, the normal planning requirement is5,875races (see exact grid); choices and selections must be frozen and measured on the same races. Do not use independent two-proportion arithmetic on overlapping winners.
- **Calibration:** fixed original bins remain. Ideal independent Wilson95%half-width at500observations is≈4.37percentage points in the worst-case0.5bin; sparse longshot bins have few wins and clustered effective samples. Marginal bin intervals are not a complete powered calibration test. For a confirmatory slope/intercept or calibration-error endpoint, freeze its estimator, null and material alternative and simulate using earlier data; otherwise report descriptive bin intervals and counts only.
- **Win-only ROI:** code provides exact-binomial upper-tail power for ideal equal-price independently filled bets, testing zeroROI with alpha0.05. At500bets and true10%ROI, power is17.6%at$10,12.1%at$20,10.1%at$40,8.1%at$60and5.3%at$100. This optimistic diagnostic does not assume real prices, fills or bookmaker access.
- **Approximate ROI sample requirements:** equal-price normal approximation allowing different null/alternative variances at80%power needs5,728/$10,12,116/$20,24,893/$40,37,670/$60and63,225/$100bets for10%ROI before extra dependence; exact outputs are authoritative. These counts are independent bets, not registered races. Real mixed odds, deductions, liability constraints, non-fills and shared-race/day selection can worsen precision; a normal approximation alone is unreliable in rare tails.
- **Roughie bands:** maintain[10,20),[20,40),[40,60),[60,infinity) and within-band probability calibration, strike, uplift, prices, ROI and sample denominators. Never fill bands by lowering floors. Freeze net-return definitions and stress removing one/three largest winning payouts with stakes unchanged. Bayesian/bootstrapped tail estimates must disclose assumptions and still require enough observed winners. Pooled rare winners cannot establish every stratum profitable.

## Dependence, multiplicity and analysis safeguards

Whole-race paired comparisons; block whole days/meetings and inspect repeated horse/role serial dependence across days. Record day/race/runner/selection counts, unequal cluster sizes and non-admission reasons. All compared models use the exact same admitted fields/cutoff/operator evidence. Missing and excluded races remain in the denominator ledger; do not select a favourable complete subset after seeing outcomes.

Retain one primary test as registered. Proposed secondary SAP should define comparison families before the pre-test manifest: for example Holm control for five non-primary model-vs-market log-loss comparisons, with other metrics/strata exploratory unless separately preregistered. Codealpha/6is a conservative planning scenario, **not an adopted protocol amendment**. Do not use a favourable secondary ROI cell to rescue a failed primary or retrospectively change the endpoint. Report uncertainty/multiplicity even for null results.

Economic analysis requires real timestamped named-bookmaker fixed-win quotes, independent field/settlement, actual deductions/commissions where applicable, and declared execution/non-fill assumptions. No quote-proxy result becomes proven profitability. No exoticROI/payout assumptions determine progression. Settlement labels stay out of features, candidate choice and admission decisions.

## Required next inputs / extension decision

Work supplies: authorised official-calendar denominator, forecast admission fractions by block/state/meeting, earlier-only paired loss/Brier and return records, complete bookmaker observation/offer evidence and uncertainty in discordance/day dependence. Codex supplies frozen reproducible cohort/evidence reader and the planning script; no new market calls authorised. Estimate variance/cluster scenarios on strictly earlier compatible data, before opening January outcomes, and run cluster/rare-event design simulations with documented uncertainty. If such evidence is unavailable, keep power BLOCKED rather than inventing expected races or profit rates.

Before the existing freeze, register any detailed SAP choices/material-effect targets and whether the cohort can support them. If insufficient, retain its fixed analysis and preregister a later confirmation cohort with justified target sample/time cap, independent stopping rule and costs/rights approvals. No repeated peeking, outcome-driven extension, selective settlement or model tuning. Owner approval remains necessary for live acquisition, purchases, activation and promotion; the owner’s scientific-priority direction is already authorised.
