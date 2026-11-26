# Monty historical recovery and independent predictive development

26 November 2026 Brisbane · `AU-HISTORICAL-BLOCKS-20261126` · research only.

## Decision and governing references

Prioritise authority-linked, publication-time trainer/jockey and prior-start histories. The expanded form candidate and the paper-informed PLS challenger did not establish incremental predictive value above calibrated market. Retain the tested candidate and ablations as evidence. No basis to promote either, increase roughie volume or activate new weights.

Reviewed AGENTS.md, 25–26 November Living Development Plan and Research Library, Betting Policy (18 November), Selection Rules (17 November), owner extensions and operational guidance at [PR #234, 14c1d1b](https://github.com/Spankman/Monty-Racing/tree/14c1d1b7b443b607e0a35e2abff87db40d7f8a74). Reviewed [issue #240](https://github.com/Spankman/Monty-Racing/issues/240), #241 at `cd775dc07a0a716ecb47a6e4db934c5fb451a72a`, #242 research handover at `ad47142f9b824d74d05d30cdc467a416ad987229`, and #243 engineering handover, Work Page and research interface at `112703369ad8386df50801627b02b2c656092cf2`. Reviewed the original historical audit, previous limited identity results and negative calibration and roughie experiments. This branch extends #242. #243 stays on its separate branch and is used at its pinned head for the input-name contract and negative availability check. Its encrypted evidence recovery was verified on synthetic source inputs with genuine unchanged engines. No live permission or fresh real packet is implied. The master entry point is being established in #234 and supersedes the interim index for startup.

## P0 — recovery and data coverage

[Source coverage register](HISTORICAL_SOURCE_COVERAGE_2026-11-26.csv) · [Feature coverage register](HISTORICAL_FEATURE_COVERAGE_2026-11-26.csv). The feature register combines the existing 55-field mapping with measured finite-value/archive race counts, new research fields and missing authority evidence. Counts are properties of the reference set, not of all Australian race fields or the admissible future cohort. Source rows separately preserve period, retrieval scope, rights, cost and unknown denominators. Empty source counts mean unmeasured, not zero.

- Reopened the original private archive, restored 28 files and verified all 55 V6 hashes. The enriched reference window is 1 January–15 June 2025, 62,255 runner rows and 6,422 races. Archive race IDs and horse proxy links are stable only within their observed contexts. Previous result labels came from the exchange and current archived context does not have auditable publication vintages.
- Betfair archive evidence covers 16 verified monthly files (22,499 races, 216,366 runners). May/July 2026 remain quarantined. Scheduled-off exchange prices and May/June 2025 pinned settlement-only place labels support retrospective evaluation. They cannot furnish named fixed-win quotes or official finishing positions.
- Racing Queensland's prior permitted sectional sample is 26 races/342 rows. Of these, 263 have section measurements. The aggregate sample contains 1,713 measured and 509 missing segment entries. Racing Australia documents Horse Code and ASB ID. No authorised national ID mapping or prior-start census has been recovered.
- Cross-checked the public authority profile Superhero (RQ-scoped ID 403447) against the Doomben 17 June 2026 R8 authority form-book record. Both identify the runner as 13th of 14, barrier 9 in the 1,350 m BM65. The profile reports 58.5 kg alongside a 2 kg claim while the meeting form book prints 60.5 kg. Preserve source semantics separately. The profile update and form header do not prove the pre-jump vintage of those fields. The RQ sectional PDF also covers the previous source lead, Doomben R8 on 27 May. This is corroboration of an event and a state-scoped profile. It does not identify a national registration or prove that sources are independent of the same authority feed. Neither sample was added to the training set.
- PuntersEdge's attributed public September release contains 1,283 AU thoroughbred races / 55,420 offer rows across books. Prior TAB sample coverage was 436/1,276 provider-union-complete vectors, with only 20 same-integer-offset vectors. Completeness by provider union and reported times cannot prove official field status or true pre-decision quotes. Public sample rights are CC BY 4.0. Paid/private endpoint rights and retention are separate. FormFav and Krok remain documented authorised-archive leads only with no fresh calls. Source and economic comparisons are in the register; no licence is inferred from accessibility.
- State authorities, Australian Stud Book/pedigree sources, sectionals and stewards material provide a viable next sampling path. Racing Queensland's public reports can supply tagged interference and track information after the earlier start. They cannot enter a feature at or before their verified first publication. Gear changes require a dated pre-jump revision and separate post-race settlement. No additional subscription or provider credits were used.

[Authority profile](https://www.racingqueensland.com.au/racing/profiles/thoroughbred-horse/superhero-403447) · [17 June authority form book](https://www.racingqueensland.com.au/RacingFile.ashx?path=%2FThoroughbredMeetingFiles%2Fbok_DOOM_20260617.pdf) · [27 May authority sectionals](https://www.racingqueensland.com.au/RacingFile.ashx?path=%2FSectional%2F20260527_Doomben_T.pdf) · [Racing Australia identifier definitions](https://www.racingaustralia.horse/StableAssist/UserGuide.aspx) · [PuntersEdge open export](https://puntersedge.online/datasets) · [Betfair source definitions](https://betfair-datascientists.github.io/modelling/dataSources/)

## Identity and publication-time acceptance

1. Store issuer, namespace, immutable entity ID and revision. Scope each race by local date, jurisdiction, official meeting and race ID, mapped venue, race number, distance and scheduled start/revision. Require one official runner with saddlecloth and canonical horse ID and match provider entry IDs on that event. Review ambiguities against foal year, sex, country/pedigree and dated connections. A display name can corroborate a matched race, never create a join. State/market identity scope must be explicit. Do not silently unify trainers/jockeys by text.
2. Keep event, publisher/observation time, archive first-seen time, ingestion time and source digest together in an immutable private provenance record, with licence ID and retrieval context. Use provable source publication or a receipted first-seen observation with timezone. A later retrieval or an event date does not establish the earlier availability needed for fitting.
3. Join the most recent legitimate revision strictly before cutoff. Label corrections and missingness and quarantine conflicts, timestamp shifts, incomplete field/price vectors and ambiguous quote semantics. For prior starts, exclude the whole current local race date, even if a race finished earlier. Use role histories by verified official IDs, maintaining jurisdiction/dates and duplicates. Apply derivations only from earlier evidence. Hold settlement and publication of official results outside prediction storage until fit/settlement eligibility is verified.
4. Use #243 per-race receipt validation and prospective contract for admitted data. Preserve presence masks, time semantics, raw quote binding and as-of evidence beside model snapshots. The legacy reference rows correctly fail #243's provenance gate. They are evaluated only as explicitly unverified-vintage retrospective diagnostics. Actual data gate checks additionally need inclusion/exclusion reasons, stale/change revision counts, full declared/active counts, source-lineage conflicts, odds semantics and source/feature missingness by race and time window. No change to engineering transport is needed here.

## P1 — ablations and comparative performance

Refit drop-one feature blocks on all four #242 chronological folds, keeping fit, calibration and test separated. Added earlier-date trip (±200 m) and same coarse going form. All blocks are disjoint. Within-block substitutions and other correlated features remain, so ablations are conditional, not causal effects. The effect below is loss after removal minus loss before removal. Positive suggests the fitted full candidate used that information. Intervals are pointwise Brisbane/date-cluster resamples and should not be read as multiplicity-adjusted discoveries.

| Removed block | Standalone loss change | 95% interval | Market blend loss change |
|---|---:|---:|---:|
| Prior-start form | +0.000503 | −0.002360 to +0.003463 | −0.000369 |
| Trainer history/change | +0.036265 | +0.026395 to +0.045554 | +0.000319 |
| Jockey history/change | +0.023704 | +0.017914 to +0.029663 | −0.000048 |
| Distance suitability/change | −0.000831 | −0.003091 to +0.001222 | −0.000250 |
| Class context/change | −0.000074 | −0.000883 to +0.000655 | −0.000019 |
| Going suitability | −0.001781 | −0.003049 to −0.000553 | +0.000098 |
| Barrier and barrier × trip | +0.002342 | +0.000521 to +0.004248 | +0.000139 |
| Partial trainer intent | −0.006081 | −0.012187 to −0.000932 | +0.000316 |

No blend drop-one interval excludes zero. Current-weight, sectional, pedigree, gelding/gear and hidden-form blocks could not be tested on compatible verified records. The broader model should not replace #242's simpler candidate. Adding trip and going context did not improve pooled standalone loss versus that branch's 2.158321 point estimate. Avoid increasing complexity or adopting ablation-driven pruning from this already exposed sample.

| Arm | Pooled March–June, 4,129 races | June common subset, 584 races |
|---|---:|---:|
| Raw market | 1.761018 | 1.908782 |
| Calibrated market | 1.760747 | 1.905301 |
| Expanded independent fundamental | 2.161253 | 2.210909 |
| Frozen V6 | — | 1.905764 |
| Frozen V7 | — | 1.904216 |
| Expanded Benter-style blend | 1.761060 | 1.905318 |
| Expanded completeness-adaptive | 1.760882 | 1.904796 |
| 8-component PLS logistic blend adaptation | 1.761048 | 1.905245 |

The PLS blend difference is +0.000301 against pooled calibrated market (95% interval −0.000915 to +0.001497); expanded Benter +0.000313 (−0.001196 to +0.001792). June was previously examined and cannot be used as an untouched final cohort. The [aggregate results](HISTORICAL_BLOCKS_2026-11-26.json) contain Brier, place/win diagnostics, calibration, class/going splits, all four odds bands and high-price outlier sensitivity. Place labels only exist for the verified May and June exchange source files. Pooled blend race Brier was 0.766906 versus 0.766689 calibrated market. The corresponding top-pick place strike on known place labels was 66.84% versus 67.06% and exchange quote-proxy ROI −2.95% versus −2.19%. Every pooled extended blend roughie-band ROI interval crossed zero. There are no new named fixed-win or prospective results. No roughie threshold or quota was changed.

## Academic replication progress

Recovered the [published full West–Kazakov paper](https://www.ubplj.org/index.php/jpm/article/download/2093/1839/7190), DOI 10.5750/jpm.v18i1.2093. The paper describes logistic-link PLSGLR with missing data, 22 candidate inputs, a chronological pre-/post-July 2020 split, 9,060 races in each side, fit-side winner resampling and an eight-component validation plateau. It compares Australian starting-price and profitability diagnostics. Do not infer executable pre-cutoff fixed-win prices or that the reported profitability will transfer to Monty.

The new adaptation uses eight fit-only standard PLS components, a logistic outcome model, race normalization and later-window market calibration. It does not implement the paper's missing-data PLSGLR algorithm, original resampling scheme, original data, full feature set, quote semantics or staking comparison. Exact replication remains open. Use the publication's method and appendix with authorised matching data before claiming that. Retain #242's earlier reproduced Benter, conditional logit and Harville methods, not their original datasets/results. The earlier boosting benchmark, favourite–longshot controls, regularisation and literature are indexed in the Research Library. Speed, pace, drafting and hidden form remain acquisition-led. Do not infer pace and interference from finishing place.

## Later cohort and engineering handover

[Preregistered protocol](MONTY_INDEPENDENT_VALIDATION_2027Q1.md) fixes 4 January–28 March 2027 Brisbane, the seven matched arms, the primary comparison and data/analysis gates before test outcomes. Capture and fit manifest remain pending. Rights, custody, bookmaker field evidence and verified training/calibration inputs are prerequisites. No new workflow, capture or race is assumed. If requirements are unmet by the freeze, record the window BLOCKED without retrospective backfill.

Codex priorities: obtain lawful registration/event crosswalk and publication-time authority revisions first. Separate trainer and jockey tracks and keep field availability counts by block. Then collect matching complete named fixed-win books and official settlement, privately. Add sectional and incident data after a narrowly verified joint coverage pilot. Acquire gear/gelding and pedigree after source identity and time are proven. Keep all source requirements visible through the shared master handover and GitHub. Do not repeat the failed #243 historical archive search without a new lead.

## Reproduce

Restore the pinned original checkpoint as in #242. Use the pinned V7 checkout and exact #243 checkout, plus the private pinned May/June 2025 Betfair exports. Run from repo root:

```sh
PYTHONPATH=.:monty_v6 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -q test_historical_blocks test_fundamental_study test_ruffies
PYTHONPATH=.:monty_v6 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m operations.audit.historical_blocks --v7 PINNED_V7 --engineering PINNED_243 --months PRIVATE_MONTHS --output PRIVATE_OUTPUT.json
```

All 24 targeted local checks passed, including two new ablation contract checks. Published aggregate SHA-256: `7f2fa34f06027ca7cc6d02f28d1929f50aafdfc05e02f66e75b9171bd303f386`. No raw records published. No merge, deployment, purchases, live API usage, trial intervention, bets, change to $4 progression/NO BET/freshness or promotion. V6 remains official and frozen. V7 remains research-only.

IN MONTY WE TRUST.
