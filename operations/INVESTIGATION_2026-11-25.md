# RM6 / RM7 investigation — 25 November 2026 Brisbane

Draft repair PR [#210](https://github.com/Spankman/Monty-Racing/pull/210), branch
`fix/prediction-approval-diagnostics`, based on production
`623d46b449e46cfc5fa63b633c3f19b404bba41a`. No production merge or V7 promotion.

## Findings from the actual original requests

| Request | Actual saved result | Races scored by each engine | Capture UTC, 24 November |
| --- | --- | ---: | --- |
| [206 RM6](https://github.com/Spankman/Monty-Racing/issues/206) | PARTIAL_OR_BLOCKED | 27 | 22:32:21.845828 |
| [207 RM7](https://github.com/Spankman/Monty-Racing/issues/207) | PARTIAL_OR_BLOCKED | 27 | 22:34:06.559952 |
| [208 RM6PS](https://github.com/Spankman/Monty-Racing/issues/208) | COMPLETED_NO_BET (legacy label) | 28 | 22:35:57.396231 |
| [209 RM7PS](https://github.com/Spankman/Monty-Racing/issues/209) | COMPLETED_NO_BET (legacy label) | 28 | 22:37:46.361583 |

All four original forecast and receipt hashes were independently verified. Their
contents were not rewritten. Every capture has a five-minute expiry; these are
historical investigation evidence, not current selection slips.

1. **Approval was never actually evaluated.** `selection()` always set official
   NO BET, `execute()` always appended missing field/history/value evidence,
   and `current_result()` always deleted official-view rankings. `assess_day`
   and `race_day` explicitly describe their outputs as unapproved research.
   This is an unfinished evidence/approval integration, not proof that either
   model found no value. The original runner cannot produce QUALIFIED bets,
   even if its numerical probabilities have been successfully calculated.
2. **Historical model inputs are missing from the operational data path.**
   The adapter maps contemporaneous market/field/barrier/distance/going/weight
   observations, but does not join the compatible historical feature builder.
   In the live branch capture, every scored runner had 16 of 55 observed input
   features; the others used saved imputation. In particular, historical horse,
   track/distance/going and jockey/trainer residuals were missing. Form strings,
   strike rates and BSP cannot silently replace V6's exact retained-history
   residuals and scheduled-off full-field probabilities.
3. **Both predictive engines genuinely run.** V6 uses `run_day` → `race_day`
   → frozen `monty.scoring.score_features`, selected `linear_1.0`. V7 runs in
   a separate interpreter and pinned checkout, through
   `v7.run_provisional_race` → `v7.predict` → `v7.core.predict`. No common
   tipster/fallback scorer or overwritten output path was found. Both receive
   the same per-race input bytes, with independent output directories.
4. **Similar rankings are strongly market driven.** Both frozen algorithms
   start from normalized inverse fixed-win odds, then apply their own ridge
   form corrections. V7 also applies frozen temperature 1.0620913911959668.
   In #209 their top runner agreed in 28/28 races, but probabilities differed;
   Wyong R5's displayed second runner was V6 #5 versus V7 #2. In a later shared
   live capture their top runner agreed in 27/28 races. Similarity is therefore
   not identical inference or an expert-tip substitution.
5. **A real operational failure was obscured.** Geelong R8 failed with generic
   `inference_failed_ValueError` in both #206 and #207, then succeeded in #208
   and #209. The original exception cause/private input was not retained in
   those public receipts, so its precise past cause cannot honestly be recovered.
   New allowlisted error codes distinguish identity/price mismatch, invalid
   probabilities, changed shared input, expiry during inference and component
   reconciliation errors. No speculative relaxation of exact price/identity
   checks was made. The later live branch executions did not reproduce this error.

## Dynamic weighting

The original `EXPERT_CONSENSUS_ADAPTIVE_WEIGHTING.md` specifies **90% model /
10% expert as a conditional research baseline**, not an always-active production
blend. `monty_v7_shadow_blend.blend` defaults to .10, bounds research expert weight
to 0–.20 and requires provenance, independent named authors and >=60% model
feature coverage. Missing experts leave model scores unchanged.

`monty_expert_weight_gate.gate` requires chronological holdout, sufficient settled
history (default 100 races), identical comparison odds/races and provenance, and
still only flags manual review; it does not activate a new weight. No genuinely
automatic performance-driven weighting is connected to `monty_operations.invoke`.
The actual operational runs therefore use **100% frozen model / 0% experts**.
This includes the market offset built into each model; it does not mean
market-independent probabilities. No weighting was changed in this repair.
Live expert blending/dynamic adjustment cannot be accepted as demonstrated.

## Repairs and before/after behaviour

- `operations/assessment.py`: separate successful V6 PROVISIONAL and V7 RESEARCH
  ONLY predictions from DATA BLOCKED betting approval, DATA BLOCKED inference
  inputs and EXECUTION FAILED technical errors. Successful inference now ends
  `COMPLETED_ASSESSMENTS`, rather than mislabelling missing verification as a
  genuine predictive NO BET. Legacy reason keys are retained for compatibility.
- `monty_operations.current_result`, `projection`, `ticket` and
  `operations/render.py`: RM6 standard view retains clearly separated diagnostic
  model assessments while its approved selection list stays empty. RM7 displays
  genuine research rankings. PS commands display explicit provisional limitations.
  All four single-race variants retain the existing automatic hierarchy and
  explicit PS intent. Ranking, value and probability diagnostics persist in the
  immutable forecast; expired or post-jump rankings remain suppressed at retrieval.
- `monty_operations.selection`: retains full-field rankings, fair win odds,
  normalized market probabilities and `probability * fixed_win_odds - 1` numerical
  edges. Positive arithmetic edge is not treated as a validated betting opportunity.
- `operations/model_audit.py`: independently reconciles actual staged CSV inputs,
  frozen imputation/scaling, market offset, form correction and V7 temperature
  against every engine-reported probability. It never fits a model, supplies
  replacement predictions or loads a research pickle. Reconciliation fails closed.
- `krok_adapter.named_bookmaker`: recognizes documented named fixed-bookmaker
  attribution for the **exact already selected price**. It does not change the
  adapter's price-selection priority or infer a fixed-win operator from a
  differently priced best-win quote. Exchanges and mismatched prices remain
  unaccepted. Generic `_price_source` remains intact for the pinned V7 contract.
- Removed the duplicated *shared* V7 minimum-three-runner gate from V6 full-day
  scoring. V6 retains its own valid minimum and V7 keeps its separate minimum.
- Aggregate source availability, observed/imputed features, provider condition/
  surface observations and effective zero expert weight are now disclosed.
- Existing issue ingress, terminal issue delivery, read-only C, progression,
  best/ruffy thresholds, blackbook/settlement code and frozen artifacts are preserved.
  No approved logo/legend asset or active blackbook monitor is invented; the
  existing white/black/gold renderer and copyable text remain in use.

There is **still no validated production approval evaluator**. No repair here
manufactures QUALIFIED selections or declares a genuine fully verified NO BET
when essential evidence is missing. The legacy `recommended_bet_type='NO BET'`
is a no-wager instruction, not the new semantic explanation of a data failure.

## Provider and validation limitations

The current Krok pagination adapter already follows explicit cursors/pages,
checks declared totals and duplicate identities, bounds acquisition/retries and
rejects incomplete final feeds. The observed live AU/NZ card was obtained on one
page; pagination was not the cause of the original missing approval.

Named bookmaker quotes are provider assertions, not independent field or
scratching verification. Historical feature compatibility and quote-update ages
are not established by having a form string or a new API fetch timestamp. The
existing five-minute capture window and pre-jump gates remain unchanged.

Public access probes returned HTTP 200 for the dated TAB page, TABtouch Geelong R8
and Racing Queensland Ipswich form page. The published TABtouch material exposes
historical form and RQ identifies the dated TAB meeting/going. These are useful
corroboration leads, not a complete automated current field/scratchings/condition
attestation. No blanket verification flag was granted from page access or search
snippets. No unofficial TAB endpoint, paywall bypass or new paid source was added.

Sources: [Krok documented racing API](https://krokodds.com.au/api-docs/racing),
[TABtouch dated Geelong R8](https://www.tabtouch.com.au/racing/2026-11-25/mr/8),
[RQ dated Ipswich form](https://www.racingqueensland.com.au/racing/form-analysis/thoroughbred/ipsw/20261125).

## Validation and acceptance scope

See [machine-readable evidence](INVESTIGATION_2026-11-25_EVIDENCE.json) for exact
runs, capture/expiry times, request IDs, forecast and receipt hashes. Live branch
validation uses the existing Actions workflow and existing secrets, one shared
provider capture for the command matrix, and derived artifacts only. It creates
no production issue, publishes no production results and places no wagers.

Final live-tested inference commit: `57af341a8a68afa402e80a5ad2248ba0e159525f`.
[Live run 45508147641](https://github.com/Spankman/Monty-Racing/actions/runs/45508147641),
[derived artifact 14974930827](https://github.com/Spankman/Monty-Racing/actions/runs/45508147641/artifacts/14974930827).
Capture: **25 November 09:14:12.641678 Brisbane**, expiry 09:19:12.641678.
All ten forecast hashes and all ten receipt hashes were independently checked;
all ten executions share one provider snapshot hash. The final handover commit
adds documentation and per-runner bookmaker display; it does not change inference.

| Genuine branch request | Each engine scored | Processing seconds |
| --- | ---: | ---: |
| RM6, AU | 28 races | 25.813 |
| RM7, AU | 28 races | 25.556 |
| RM6PS, AU | 28 races | 25.243 |
| RM7PS, AU | 28 races | 24.926 |
| RM6 Albany 3 | 1 race | 1.016 |
| RM7 Albany 3 | 1 race | 1.023 |
| RM6PS Albany 3 | 1 race | 1.048 |
| RM7PS Albany 3 | 1 race | 1.039 |
| RM6, explicit NZ scope | 3 races | 2.832 |
| RM7, explicit NZ scope | 3 races | 2.680 |

These are actual shared-capture model execution/forecast timings, excluding
GitHub startup/provider capture and ordinary ChatGPT/iPhone delivery. All ten
ended COMPLETED_ASSESSMENTS. All V6 predictions were PROVISIONAL, all V7
predictions RESEARCH ONLY, and betting approval remained DATA BLOCKED.
No qualified bet or fully verified negative value decision was manufactured.

Scored AU coverage: Albany 5, Geelong 4, Ipswich 4, Launceston 6, Strathalbyn 5,
Wyong 4 races (261 runners). Explicit NZ coverage: Te Aroha R9–R11. The original
requests and ordinary default issue requests are AU-scoped; the separate NZ
probe does not silently change that default. The source listed 55 AU/NZ races;
24 were excluded by existing full-day class rules (including Te Aroha R1–R8).
Independent national TAB meeting completeness is still unverified. Raw source
inventory includes 32 outside-AU/NZ meetings, which are not scored.

In the final scored AU card all 261 chosen prices had explicit named TAB
attribution, so the old named-price gap was absent. This remains Krok-attributed
pricing, not independent TAB field verification. Only 23 of the 55 observed
AU/NZ source races carried a condition observation. Unknowns were not fabricated.

The documented field-form endpoint also succeeded using a provider-supplied
supported identifier, with the date/meeting/full declared horse identities
matching the selected race. It supplied eight recent-form blocks and aggregate
observations including 32 BSP, 29 finish-position, 35 distance and 12 weight
fields. It supplied **no original scheduled-off full-field probability records
or original-market/horse identity crosswalk**. Thus form is available, but
compatible historical residuals cannot be reconstructed from this response.
The probe did not inject those observations or outcomes into either engine.

Each live probability reconciled against frozen scoring components within
1.6653345369377348e-16. For an actual Albany R3 runner in the earlier same-day
capture, market probability was .3236383066, V6 form correction -.1212358544
and output .3202716767; V7 correction -.4860154315, temperature 1.0620913912
and output .3063523749. Each is race-normalized across the full field;
these historical diagnostics are not current betting selections.

Local checks: 111 operational/adapter/ledger tests; 152 offline CI code tests;
13 frozen V6 tests. The first broad local run had four import errors because
BeautifulSoup was missing in the workspace. Installing the already pinned
`beautifulsoup4==4.14.3` into an ignored local test directory resolved them; no
new project dependency was added. Original replay: 55 manifest entries verified,
17,987 runners / 1,787 races; maximum difference 1.6653345369377348e-16, no refit.

Actual production C read of #209 used four GETs, zero writes, returned EXPIRED
and no current ticket. It did not queue inference. Branch command delivery and
failure/expiry behaviour have automated contracts; production issue delivery of
this **unmerged** repair and fresh ordinary ChatGPT/iPhone acceptance remain
post-approval checks. A green workflow alone is not inference acceptance.

Remaining prerequisites: a permitted independently reconciled current field/
scratchings/conditions path, exact as-of historical data plus identity crosswalk
for original feature definitions, and reviewed prospective V6 betting-approval
criteria/evidence. Do not weaken those requirements or activate expert blending
merely to obtain selections. Owner review/merge approval is required; V7 remains
research-only. No new subscription or hosting is proposed.
