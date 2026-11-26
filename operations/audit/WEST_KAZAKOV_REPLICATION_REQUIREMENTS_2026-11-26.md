# West–Kazakov exact replication readiness

26 November 2026 · [Publisher full paper](https://www.ubplj.org/index.php/jpm/article/download/2093/1839/7190) · DOI 10.5750/jpm.v18i1.2093.

The paper reports 22 explanatory inputs in the data section, while the appendix lists 26 bullets. The selected subset, exact source-vintage semantics and original matrices/code were not recovered. No public original dataset was located through publisher and archive searches. An author or rights-holder data/method request is prepared as a next acquisition option. None was sent.

| Appendix ordinal | Concept, paraphrased | Replication requirement |
| --- | --- | --- |
| 1 | Prior career start count | Complete authority-linked race census before target date, no trials unless defined by study |
| 2–4 | Recency of each of the previous three starts | Verified identity, dates and race termination for each prior start |
| 5–6 | Career win and place frequencies | Complete past starts/results and original place definition |
| 7 | Log of the previous start's SP | Exact SP source/definition and pre-feature availability; exchange scheduled-off best back is a different quantity |
| 8, 12, 18 | Course wins, class wins and exposure to today's class | Canonical venues, dated class ontology and earlier results |
| 9–11 | Changes in grade rating, weight and trip | Define grade scale, declared/carried meaning, claims, and exact run distances |
| 13, 25 | Closing-speed history and final-200 m pace history | Author-defined segment and aggregation over prior runs. Sample sectionals only; no verified cohort join |
| 14, 17, 19–20 | Average, first-up and recent peak runner ratings | Requires original numerical rating formula or permitted historic ratings with availability; no substitute from finish rank |
| 15–16 | Rolling jockey win share and change of rider rating | RQ-scoped pilot IDs establish a lead only; national or covered census and result timelines missing |
| 21–22 | Expected in-race position and wide-draw correction | Original geometry/position prediction, distance/barrier mapping, as-of track data |
| 23–24 | Quick return and young horse competing in unrestricted ages | Verified prior date, foal date and published race eligibility |
| 26 | Morning market price | Actual start-of-racing-day source/time, distinct from settlement/SP. Despite article language around fundamentally estimated strengths this is a market feature. Leave it out of an explicitly independent Monty arm. |

Separate stages from the published experiment: its Jan 2019–Dec 2021 metropolitan/provincial restriction and July 2020 split, fit-side winner resampling, missing-data logistic PLSGLR, variable and component selection, odds/source terms and difference in decision rules between comparators all require reproduction. The raw data, paper-specific rating definitions, exact selected inputs, missing-data fit details and execution prices remain unresolved. Country samples, refreshed books or Monty's exchange-quote proxy cannot silently replace them. Any future paper-inspired benchmark should use chronological held-out races, comparable staking rules for attribution, and calibrate probabilities independently after any class-prior resampling.

PR #244's eight-component adaptation remains the tested result. No refit or new academic return claim in this acquisition pilot. Retain the Benter-style log combination and calibrated market as comparators. Compare modern methods only after new verified rows materially increase coverage.

[CRAN plsRglm](https://cran.r-project.org/web/packages/plsRglm/index.html) is a free candidate implementation for missing-data logistic PLS. It was identified from its documentation and was neither executed nor identified as the authors' code. Match algorithm, resampling, component selection and calibration before claiming replication.
