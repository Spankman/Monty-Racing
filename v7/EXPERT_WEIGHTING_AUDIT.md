# V7 expert weighting audit · 24 November 2026

| Path | Intended or configured weighting | Verified behaviour |
| --- | --- | --- |
| Owner specification, 19 November | 90% independent Monty and 10% expert after provenance and coverage gates. Test 0%, 5%, 10%, 15% and 20% with chronological evidence. Zero when evidence is insufficient. | The old shadow blender enforces a 20% ceiling. The spec conditions adjustments on out-of-sample evidence. |
| Live RM7 and RM7PS on main | Pinned independent V7 scorer | 100% V7 model and 0% external tips. The live entry point has no expert scoring or adjustment call. |
| Daily research shadow on main | A separate frozen-linear research scorer. Fixed 10% default when the optional expert CSV and ≥60% feature coverage pass. | Four successful logs show 0 expert-weighted race instances out of 10, 9, 55 and 55. Discovery and field audits do not supply the raw CSV consumed by the blend. |
| Expert performance utility and guard | Descriptive hit rate and simulated WIN ROI. Manual research review. | The evaluator does not update a live or shadow weight. The weight gate returns zero even when eligible for manual review. No scheduled settled expert ledger was identified. |
| Separate prototypes | Feature vote aggregation and an agreement/coverage heuristic | The [ECI feature branch](https://github.com/Spankman/Monty-Racing/tree/096d1a009dc6ae25c95f45fc79ac258ecccd3e00) and [experiment #9](https://github.com/Spankman/Monty-Racing/pull/9) are unmerged. The latter's heuristic is independent of settled performance and its argument validation permits up to 30%. Expert-cache [#18](https://github.com/Spankman/Monty-Racing/pull/18) and discovery schedule [#60](https://github.com/Spankman/Monty-Racing/pull/60) were merged. |

The 129 observed shadow race instances may include overlapping races across executions. The inspected logs were [45101700293](https://github.com/Spankman/Monty-Racing/actions/runs/45101700293), [45009629302](https://github.com/Spankman/Monty-Racing/actions/runs/45009629302), [44656031530](https://github.com/Spankman/Monty-Racing/actions/runs/44656031530) and [44634366312](https://github.com/Spankman/Monty-Racing/actions/runs/44634366312). The [owner directive](https://github.com/Spankman/Monty-Racing/blob/47f7fb4570b5eccd4b93c96d629e052d20fc0e8f/EXPERT_CONSENSUS_ADAPTIVE_WEIGHTING.md) documents the research intent.

## Historical comparison

The Sandown staging CSVs in the unmerged experiment leave publication timestamps blank and flag the timezone as unverified. Original pages establish that picks were published, including the [Gately article](https://thegreattipoff.com/news/david-gately-horse-racing-tips-for-sandown-181126) and the [GoBet article](https://www.gobet.com.au/horse-racing-tips/sandown-november-18-2026/). The inspected archive did not establish pre-race capture of the relevant article versions, sufficient independent coverage, matching frozen predictions, prices and official settlements. The separate 24 November barrier/price study supplies no matched tipster evidence.

The candidate replay verified three archived forecast hashes against the original receipts for [Ararat R3](https://github.com/Spankman/Monty-Racing/issues/162), [Ararat R5](https://github.com/Spankman/Monty-Racing/issues/180) and [Tamworth R6](https://github.com/Spankman/Monty-Racing/issues/182). Each retained **100% independent V7 and 0% expert weight**. The replay supplied no independently verified common-market settlements and no matched expert inputs. The observed candidate distribution is 0% expert on 3 of 3 archived forecasts.

| Requested arm | Eligible settled races | Strike rate, P&L, ROI, calibration and drawdown |
| --- | ---: | --- |
| Frozen V6, unchanged V7, V7 at 100/0 | 0 each | Unavailable on the matched expert sample |
| V7 fixed 95/5, 90/10, 85/15 and 80/20 | 0 each | Unavailable |
| Dynamic V7 | 0 | Unavailable |

Class and odds slices, selection volume on the matched set, and expert contribution are unestimable. Current weighting recommendation is **100/0**. Reassess 90/10 when prospective capture supplies enough usable data and paired results support it.

## Research candidate and ledger

- Cards use the original frozen V6 and pinned V7 model hashes, one complete shared field snapshot, an available-at-cutoff model forecast, and posts captured and verified before the forecast. The candidate uses the experimental 5–20 independent editorial groups and the previous 60% model feature coverage gate. A group votes once. Duplicate author/document claims and conflicting votes reduce the eligible pool.
- Votes are shrunk toward the verified market using earlier settled evidence. The calibration minimum is 100 races over at least 20 Brisbane dates. A second minimum of 100 earlier settled, out-of-sample comparisons over at least 20 dates governs dynamic weighting. The review uses up to 300 recent observations. Increases require a positive paired log-loss margin against Monty-only, the market and the current weight, with simulated profit no worse in those comparisons. The 10% research starting point needs supportive paired loss and profit. The ceiling is 20%. Normal reviews occur at most weekly, with five-point increases. Missing evidence can immediately zero the weight.
- The report compares one simulated unit on each arm's top WIN selection at the common verified captured fixed prices. Official dividends are preserved as evidence and never used as replacement fixed prices. Incompatible active fields, dead heats and void races are excluded across arms. Log loss and Brier cover the whole field. Calibration, strike rate, ROI and drawdown use the documented matched population. The ledger preserves model-only, expert-only and combined picks, odds, weights, reason, settlements, and individual performance.

Run the module with **python -m v7.expert_weighting**. Use the global **--ledger** option to select a research-only directory.

- **freeze verified-card.json** writes one verified pre-race decision using the actual decision time. **settle verified-result.json** adds the official known outcome, and records ledger-entry time separately from official settlement.
- **review --days 1 --as-of ISO_TIMESTAMP** and **review --days 7 --as-of ISO_TIMESTAMP** produce nightly and weekly summary payloads. Automated ingestion was not activated. A verified source and settlement stream for existing review consumers was not identified, and main was left outside the branch change.
- **replay verified-archive.json --as-of ISO_TIMESTAMP** accepts an object with cards and results arrays. It replays the archived decision times in order and accepts only settlements known before each prediction. Replay outputs must stay outside the prospective ledger.

The card contains race_id, classification, cutoff_at, scheduled_start, runners (number to name), odds (number to decimal fixed price), odds_source, odds_captured_at, odds_verified, v7_feature_coverage, shared_model_input_sha256, model_captured_at, model_artifacts, models and optional tips. Model maps use v6 and v7 keys. Their artifact records contain model_sha256, forecast_sha256 and forecast_url. Each tip includes author_id, independence_group, source_url, independence_evidence, evidence_sha256, number, horse, provenance_verified, published_at, captured_at and verified_at. Verify original evidence, timestamps, receipts, prices and editorial dependence before setting flags. Keep licensed raw evidence outside Git.

Each result contains race_id, status (official_single_winner), official_verified, race_off_at, settled_at, source_url, active_runners, winner and available verified dividends. Replay uses recorded_at when available, otherwise requires settled_at to represent the documented availability time. Forecast and result files are written once and independently hashed. The candidate verifies the supplied evidence contract without authenticating external websites.
