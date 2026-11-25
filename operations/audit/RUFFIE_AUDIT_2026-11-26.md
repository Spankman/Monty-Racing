# Roughie identification and predictive performance audit

26 November 2026. Owner issue [240](https://github.com/Spankman/Monty-Racing/issues/240).
Development branch `audit/roughies-240`, based on draft231 at
`0df55dccd230b69bba8e0be5f8d8ef9462f5c388`. Draft only: no merge, deployment,
training, model artifact, production weighting, value threshold or betting-rule
change. V6 official; V7 research-only. No new live provider requests or credits.
The separate PuntersEdge six-day trial, its branch, ledger and automation remain
untouched. All examples/results below are historical, not current selections.

## Findings supported by the actual archive

Requests236 RM6,237 RM7,238 RM6PS and239 RM7PS all reference **one** genuine
shared run `45716359662-1-236`, not four fresh independent executions. It ran
production commit `623d46b449e46cfc5fa63b633c3f19b404bba41a`, V7 commit
`efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`, Krok capture
`2026-11-25T22:49:33.466304Z`, expiry22:54:33UTC. The request indices, source
receipt and complete workflow artifact were retrieved and hash-verified.

[Run](https://github.com/Spankman/Monty-Racing/actions/runs/45716359662) ·
[Forecast](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-26/45716359662-1-236/forecast.json) ·
[Receipt](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-26/45716359662-1-236/receipt.json).
Forecast SHA `23a5e11588539e56621b52965808b00ce1433dc37b895242ad900ddde3883875`;
receipt SHA `af2c36b18c461169bf6f01aca75d7435467b27f1fb6cdb3e982619484d2b2409`.

- Provider card29races/four Australian meetings;19accepted,10excluded as restricted
  race types. This is provider coverage, not independently verified TAB coverage.
- V6 genuinely scored19races/168active runners. V7 scored18races/162runners;
  RockhamptonR2 was blocked before V7 inference by inconsistent price provenance.
- Both raw forecast roughie lists contain **zero watches**. Production
  `selection()` computes watches before `forecast.json` is written; projection
  and ticket rendering occur afterward. Therefore zero raw watches were **not
  caused solely by hiding a nonempty shortlist during rendering**.
- For V6, any scored $10+ runner would pass its unchanged minimum-price rule
  ($6) and positive-probability requirement. Zero raw watches proves none passed
  `p*odds>1` in that snapshot. For V7, each scored $10+ runner failed `p>=0.06`,
  positive point EV, or both. Individual identities/reasons are not recoverable
  for missing rows; that is not a licence to invent them.
- Only47V6 and44V7 runner records survived the short-ticket projection.
  **121V6 and118V7 scored runner records are absent.** No preserved runner is
  $10+; maximum preserved price is$7. The artifact contains only public
  forecast/view/ticket files; the shared input CSV/JSON and full scoring outputs
  were not retained. The total number/identity of $10+ runners is unknown.
- All18shared preserved ticket orders match V6/V7. Across the preserved subsets,
  there are zero market-price rank inversions (38V6/35V7 comparable pairs).
  This does **not** establish identical unpreserved full-field rankings.
- Missing independent fields/conditions, compatible form and prospective value
  approval block wagering. They are operational/data failures, not evidence of
  a verified predictive NO BET. Five races also report incomplete named fixed
  prices. Existing classification repairs in the unmerged stack separate these
  outcomes; production still uses its earlier wording.

Complete archive-population accounting:
[RACE_EXCLUSION_COVERAGE.csv](roughies_240_results/RACE_EXCLUSION_COVERAGE.csv).
Every preserved runner was audited privately; missing runner counts are retained
by race/model. A complete named $10+ exclusion audit is **blocked by discarded
original inputs**, not declared complete. Earlier PuntersEdge prices, a new Krok
call, search results or a different timestamp/provider cannot fill this gap.

## What the models actually weight

V6 linear scoring is `softmax(log(p_market) + Z*w)`.
V7 is `softmax((log(p_market) + Z*w) / 1.0620913911959668)`.
The market logit coefficient is1.0 for V6 and0.9415385608897094 for V7;
feature-correction logits receive the same respective scaling. These are
**static log-score coefficients**, not percentages of independent form and
market forecasts. They do not change per race/runner with confidence or data
quality. Missingness indicators and frozen imputation affect scores but do not
constitute adaptive weighting.

The historical90/10 proposal is **90% Monty/10% external experts**, conditional
on prior validation/provenance/coverage. It is not a90%independent-form/10%market
configuration. Operational inference invokes no expert blender: actual
model-vs-expert weights are **100%/0%** in every scored race. Missing experts do
not cancel or penalise independent scoring. No eligible historical complete-field
expert archive exists for a genuine90/10 performance test; no expert predictions
were fabricated. [Per-race weight audit](roughies_240_results/PER_RACE_WEIGHTING.csv).

When missing historical features are imputed to identical values within a race,
their common logit contributions cancel during normalisation. With only market,
field size and distance, V6 consequently reduces to the market. V7 additionally
applies its temperature, flattening the same market ranks. Current barrier/going
inputs can create small contrasts; neither engine is simply replaced by a
shared fallback ranker.

For today's **preserved** runners, the exact within-race nonmarket contrast can
still be recovered as `T*log(p_i/p_j)-log(odds_j/odds_i)` without guessing the full
normaliser. Maximum absolute contrasts are0.0234400V6 and0.0220730V7 (about2.37%
and2.23% multiplicative pair-odds differences). This proves some nonmarket
influence among preserved rows, not profitable information or full-field skill.
Per-feature attribution and actual full-market probabilities need the missing
shared inputs. The archive does not preserve today's actual feature counts.
Earlier authenticated adapter audits observed16/55schema inputs:13/43active
V6 and12/42active V7. They are context, not invented per-runner measurements for236.

## Why few high-priced V7 watches are structurally expected

The6%floor implies fair win odds of at most$16.67. A$40runner at that floor
needs a gross point EV of+140%; a$60runner needs+260%. It restricts the search
but is not proven optimal. Lowering it solely to produce more roughies is
unsupported. The new section exposes policy-excluded numerical diagnostics
without changing that floor or making them approved selections.

Short-price favourites head the main ticket because it ranks estimated win
probability and applies the existing$4 fixed-win progression. Most-likely winner,
market value and a standalone roughie are different decisions. No longshot is
padded into a quinella/trifecta/first-four to make the slip look diverse.

## Market integrity and earlier investigations

Draft225 found concentration of apparent value under abnormal market books.
Draft226 separated model uplift from normalisation and quarantined anomalous
prices. Those controls remain intact. Its authentic25November GeelongR8 and
LauncestonR6 books were95.924159% and72.746422%; a market-only model therefore
created apparent point EV of+4.2490% and+37.4638% before any independent signal.
Those are **different races/date**, not reconstructed26November books.

For the current trimmed archive, only incomplete-book lower bounds can be
calculated. No full book/underround, identical-book vector, offer freshness,
independent field completeness or full market ranking is invented. In new
complete diagnostic records:

`p_model*odds - 1 = (1/book - 1) + (p_model - p_market_normalised)*odds`.

Underround/mixed books, missing/conflicting runners, unknown identities,
withdrawals, stale/future/missing offer clocks and inconsistent timestamps keep
DATA BLOCKED/NO BET. Retrieval time is never substituted for quote observation.
A normalised-market positive edge without positive model uplift is not genuine
model-derived value.

## New chronological historical analysis

The original source pins, original55artifact manifest, frozen feature matrix and
V7 fold3 model were verified. No fit or research-pickle load occurred. Two cohorts:

1. **584races/6004runners**,1–15June2025, original full inputs. This is the actual
   saved V7 fold3 test window but has already been examined in prior research.
2. **5512races/53470runners**,June andAugust–October2026, sparse current-market,
   field-size/distance inputs with frozen imputation, evaluated month by month
   after the model/calibration cutoffs. May/July2026 remain excluded by original
   source-integrity pins. No future labels enter predictors.

These are **scheduled-off exchange-price simulations**, not historical named
bookmaker fixed-win validation or independently settled prospective results.
Only fold3 was available; this is chronological fixed-model evaluation, **not a
new expanding-window refit walk-forward experiment**. Reproducing all original
folds needs the original fold1/fold2 artifacts/evaluation records and compatible
warm-up, or separate approved research reconstruction. No missing fold was
silently trained. The requested genuine fixed-win walk-forward acceptance
therefore remains incomplete.

|Cohort|Market log loss|V6 log loss|V7 log loss|
|---|---:|---:|---:|
|2025 original full inputs|1.908782|1.905764|1.904216|
|2026 sparse inputs|1.779461|1.779461|1.781385|

Full-input loss differences versus market: V6−0.003018, day-block95%CI
[−0.008271,+0.002533]; V7−0.004567,[−0.009597,+0.001292]. Neither establishes
reliable incremental benefit. In later sparse data V6 mean absolute probability
uplift is1.56e−17, mean rank difference0. V7 uplift is0.003730 in probability
units but rank difference0; its loss **worsens** by0.001924,[+0.000686,+0.003069].
Calibration-driven differences must not be called independent form intelligence.

### Requested bands and selection sensitivity

Later2026 **research-only positive uplift plus positive gross EV**, excluding
underrounds. This deliberately reports the no-floor comparison separately from
existing V7 eligibility; it does not activate a lower threshold. V6 has zero
positive-uplift selections in every band under sparse inputs.

|Exchange quote band|V7 runners/wins|Win strike|Place-market strike|5%fee ROI proxy|Day-block95%ROI interval|
|---|---:|---:|---:|---:|---:|
|$10–19.99|8908/608|6.83%|28.26%|−9.59%|−16.15%to−2.98%|
|$20–39.99|8458/321|3.80%|18.40%|−4.87%|−15.41%to+5.74%|
|$40–59.99|3359/61|1.82%|12.53%|−18.23%|−36.72%to+1.68%|
|$60+|9678/82|0.85%|5.28%|−5.67%|−24.72%to+15.14%|

Under the **unchanged V7 6%floor**, only7019$10–19.99runners qualify for this
point-EV simulation:512wins,7.29%win strike,29.78%place-market strike and−9.11%
ROI proxy. None qualify in the three higher bands. This does not justify reducing
the floor: the newly admitted no-floor cohorts are losing or inconclusive.

Place strike uses actual separately joined Betfair PLACE_RESULT labels; missing
labels stay missing. It is the exchange's settled place market, not assumed
fixed top3. No place-bet ROI is invented from absent executable place prices.
All-runner, unchanged-policy and no-floor research cohorts have separate sample
counts and calibration. Raw and assumed5%winnings-fee flat-unit WIN returns are
reported; these are not verified fills, stake limits, bookmaker deductions or
actual exchange net-market commission settlement.

The2025full-input no-floor cohorts have some positive ROI point estimates, but
all displayed day-block intervals cross zero, sample size is only15days, and
large winners matter. V7$40–59.99ROI+26.72% becomes−12.50% if its three largest
winner payouts are removed while keeping stakes. Its$60+largest winner accounts
for35.10%of gross returns. In2026, V7$60+ROI moves from−5.67%to−16.87% under the
same top-three payout stress. This is a fragility scenario, not an alternative
settled strategy.

[Full aggregate results](roughies_240_results/HISTORICAL_RESULTS.json) include
calibration bins, observed/expected probabilities, Brier differences versus
market on matched bands, all sample counts/place-label coverage, monthly paired
log loss, class/going/distance strata,2000day-bootstrap intervals and winner
concentration.2026going is explicitly unknown. Raw exchange race-class labels
are not invented benchmark grades. Do not infer superiority from small strata.

### Alternative weights tested without modifying models

Correction-strength multipliers0,0.5,1and1.5 and V7 temperature1 versus its saved
1.062091 were fixed research-only sensitivities. They do not fit a form-only
model or substitute market probabilities for experts. In sparse later inputs,
changing correction strength changes no meaningful within-race information;
V7temperature1 simply returns the market and removes its observed loss penalty.
In full inputs, some point differences appear, but these previously examined
15days do not justify selecting or activating a new weight. Frozen production
weights, preprocessing, temperature and thresholds remain unchanged.

## Existing feature and research-factor assessment

[FEATURE_RESEARCH_REGISTER.csv](roughies_240_results/FEATURE_RESEARCH_REGISTER.csv)
maps every requested factor to existing inputs and the prior authenticated
missingness-ablation results; it does not repeat55unchanged ablations or claim
causal effects. Findings:

- Recent/full form, track/distance/going residuals and jockey/trainer residuals
  already exist. Their live strength is limited by verified lifetime identity,
  complete earlier race/market history and compatible original definitions.
- Class, trip change, recency and connections overlap trainer-intent hypotheses;
  no trained standalone Trainer Intent Index exists. Observable changes are not
  evidence of inside knowledge.
- Barriers are active. Weight changes, age, gelding and gear inputs are in the
  schema but inactive in both saved candidates; merely supplying them cannot
  create a new frozen-model signal.
- Sectionals/finishing speed, pedigree indices and explicit interference/unlucky
  run evidence are not selected frozen inputs. No new index was invented or
  trained. Original input groups and a chronological comparative test should
  precede any additional feature development.
- Last3/5win rates/residuals overlap recent winners/beaten expectations but do
  not implement a dedicated last-start-winner/beaten-favourite factor.
- One market snapshot is not market movement. Later SP/BSP/closing prices never
  become earlier prediction inputs. Recovered candidate histories cannot bypass
  source availability, identity or same-day leakage checks.

No new feature shows a demonstrated independently validated out-of-sample
roughie benefit in this audit. The Living Development Plan records the gaps
rather than marking feature hypotheses complete.

## Staged reporting improvement

`operations/ruffies.py` adds **RUFFIES TO WATCH** after the existing main-race
assessment, with track/race, saddlecloth/name, fixed price/book, model/version,
model and full normalised-market probabilities, probability uplift, point EV,
normalisation/model-edge decomposition, feature/history quality, reduced
confidence, exact inclusion/exclusion reasons, per-offer observation/expiry,
and **NOT APPROVED / NO BET**. Roughies remain standalone WIN ONLY.

A genuine research candidate with suitable complete source data remains visible
even when independent official approval is unavailable. Anomalous or unverified
books stay diagnostic DATA BLOCKED; positive underround normalisation is never
promoted to predictive value. V7policy-floor exclusions can be inspected as
research diagnostics, not falsely counted as qualifying watches. No quota,
price floor or probability cutoff is relaxed. No candidates produces a precise
none/exclusion explanation. Legacy incomplete archives are labelled incomplete,
not reconstructed. Expired/closed watch selections are suppressed on retrieval.

The same section survives RM6/RM7/RM6PS/RM7PS and bothPS aliases, official
projection, compact delivery and repeated refresh. The archived full forecast
retains all scored rows/exclusions; compact output retains display watches plus
counts/location. Offer clocks bind the exact adapter-selected price, not a model-
wide capture timestamp. Existing white/black/gold HTML, main ticket ordering,
$4progression and plain text remain. Duplicate legacy watch lines are avoided;
no PNG is generated. Existing main NO BET and approval decisions are untouched.

Files/functions changed: `monty_operations.execute/current_result/ticket`,
`operations.ruffies.audit/attach/refresh/text`, `operations.delivery.compact`,
`operations.render.render`; offline `operations.audit.roughies_240` and
`test_ruffies.py`; operationalCI adds the new tests. No frozen source/artifact
or six-day-trial files were changed.

## Verification and practical blockers

Original55V6hashes verified; V6 selected linear model unchanged, V7 fold3 model
SHA `c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324` unchanged.
New synthetic reporting/audit tests cover provenance, incomplete/underround/
mixed/stale/future clocks, policy-floor exclusions, every command/PSalias,
compact/repeated retrieval, explicit none, nonmutation and genuineNO BET.
Existing full operational/runner checks and frozen historical replay are run
before the exact proposed commit'sCI is assessed. Final exact commit andCI URLs
are recorded in the draft PR body; an earlier green job is not substituted.

Smallest missing evidence for complete26November reconstruction:

1. Original Krok JSON whose canonical snapshot hash is
   `54ad2cba0ae8bfd622d93db8e2ea0b4d1d23f6c6b5fb2743cb35713edda855d2`, including
   active/SCR identities and nested quote clocks.
2. The19original `private/0..18/snapshot.json` shared inputs matching each saved
   `shared_model_input_sha256`, or equivalent authenticated original inputs.
   Actual per-engine CSVs (`validated_runners.csv`/`monty_selections.csv` forV6,
   `provisional_input.csv`/`v7_research_scores.csv` forV7) permit exact trace
   checks. Do not replace them with a different provider or recapture.
3. Historical named-bookmaker fixed-win vectors with price vintage and reliable
   official outcomes for true fixed-win validation; original fold1/fold2 trained
   records and warm-up for full multi-fold reproduction. No new API spend is
   authorised in this task.

Priorities: retain full future audit evidence using the already staged stack;
resolve identity/as-of history and independently executable bookmaker access;
complete the separate PEtrial; then predeclare a genuinely later paired
prospective comparison before owner-reviewed weighting/threshold/model changes.
No activation, paid subscription or wagering recommendation is made.

IN MONTY WE TRUST.
