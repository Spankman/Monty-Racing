# Monty Racing — Living Development Plan
Owner direction, 25 November 2026. Read before planning Work or Codex sessions. Supplements existing betting and integrity policies; does not override them.

## Mandatory development and research protocol — 26 November 2026
- Apply the startup and completion requirements in [AGENTS.md](AGENTS.md) to current and future development. Keep governing documents, prior findings and workstream commits pinned in the shared handover.
- Review applicable research before implementation and reproduce relevant academic baselines wherever practical. Compare modern alternatives against matched academic, frozen-engine and independent market baselines using chronological leakage-free evaluation. Record negative and blocked runs along with successful ones.
- Keep the [research library](MONTY_RESEARCH_LIBRARY.md), this plan and the shared handover current. The [master handover](MONTY_MASTER_HANDOVER.md) is the permanent entry point; the baseline handover preserves earlier review history.

## Permanent resource rules
- Use ordinary ChatGPT for planning and routine reviews; reserve Work credits for substantial integration and independent audits, Codex for targeted code work. Use conventional scripts and GitHub Actions for repeatable processing.
- Batch related tasks, avoid re-auditing unchanged components, cache and share data, checkpoint long jobs, bound retries and stop on genuine blockers. Report measurable progress, costs where observable, and concise handovers. Never guess remaining credits.
- Maximise existing paid Krok entitlement first; reserve operational credits, verify expiry, retention rights and overage settings. No extra spending, renewal or subscription change without owner approval. Store licensed data privately.
- Efficiency never overrides source integrity, freshness, NO BET, frozen artifacts or approval safeguards.

## Development register
- [ ] Stabilise V6 daily/single-race execution, results settlement and Black Book.
- [ ] Complete PuntersEdge acceptance (PR #231); measure credits and verify coverage, freshness, scratchings, results, entitlements and rollback. Free then Hobby if sufficient; retire paid Krok/FormFav only after demonstrated replacement and owner approval.
- [ ] Harvest existing paid Krok history (issue #233): results, timestamped odds, form, sectionals, running positions, gear, pedigree, conditions and connections where available. Verify remaining allowance and rights first; no public raw data.
- [ ] Build shared private historical database with provenance, timestamps, hashes, deduplication, incremental updates and resumable ingestion. AU/NZ separate.
- [ ] Prepare one coordinated historical modelling campaign; notify owner when operational stability, historical depth, retention rights, scripts, storage and credit budget justify one month of PuntersEdge Standard. No purchase without approval; downgrade to Hobby if sufficient afterward.
- [ ] V7 dynamic market/form weighting and calibration; test incremental predictive value beyond market, including expert consensus under existing policy.
- [ ] Dedicated experimental Ruffy Score: odds bands $8–12, $12–20, $20–30, $30+ (non-overlapping boundaries); win/place hit rates, separate research win/place/each-way ROI, losing streaks and drawdown, metro/country, hidden form, class/distance, wet tracks and market moves. Existing official ruffies WIN ONLY rule remains.
- [ ] Track bias: historical and race-day positional/lane bias, speed maps, tempo, rail/weather, sectionals, bias-adjusted form and Black Book candidates; distinguish pace and market expectations from bias, update with uncertainty and detect reversals.
- [ ] Gear changes: audit existing features; model additions/removals/reapplication, combinations and trainer-specific effects, gelding separately.
- [ ] Trainer Intent Index: last-start winners or favourites subsequently gelded, gear changed or distance changed; interactions with class, time between starts, trainer history and market support. Observable decisions, not proof of inside knowledge.
- [ ] Breeding/Pedigree Index: sire/dam/damsire and as-of progeny statistics, distance/surface, maturity, lightly raced/debut runners and interactions with trainer intent and gear. Test declining influence with exposed form.
- [ ] Validate all research with chronological leakage-free comparisons, matched fields, adequate samples, calibration, best-bet and ruffy results separately, exotic accuracy and risk. No promotion until robust prospective improvement and owner approval.

Research modules are non-blocking: include reliable pre-race variables in experimental modelling, omit unavailable inputs rather than delay operations; no arbitrary weights. V6 remains frozen and official, V7 research-only. No fabricated data, after-race backfill or deployment without approval. Keep this register current as new owner-approved ideas arise; mark completion only with evidence.

## Research-first programme
- [ ] Complete source reading and existing-feature/code/licence audit using [research library](MONTY_RESEARCH_LIBRARY.md).
- [ ] Reproduce simple market, conditional logit, Benter combination and Australian PLS benchmarks on common historical data before advanced models.
- [ ] Test incremental feature groups, adjusted speed, hidden form, uncertainty, race-relative rankings and coherent finishing-order probabilities; record negative findings and prospective results.

## Optimise before expanding — owner-approved priority
- [ ] Audit existing features for data quality, redundancy and incremental predictive value; test removal as well as addition.
- [ ] Prioritise existing-feature interpretation, weighting, calibration, market benchmark and race/value selection before new feature acquisition.
- [ ] Gate each proposed feature on repeatable unseen-race improvement, uncertainty, net ROI/risk, data and maintenance costs, and operational reliability. Record rejected features and reasons; do not adopt complexity for marginal or statistically inconclusive gains. Use shared ablation tests and existing benchmark pipeline to conserve credits.

## Delegated feature pruning — owner approval 25 November 2026
ChatGPT, Work and Codex may independently remove or disable redundant, ineffective or unjustifiably costly predictive factors and research features in development candidates without seeking prior owner approval. Use proportionate evidence (existing tests, ablations, redundancy or documented cost/benefit); retain reproducible baseline and rollback, record rationale and uncertainty, and notify owner afterwards in the next handover with affected features, evidence and impact. Do not treat inconclusive evidence as proof of harm. This authority does not permit changing frozen V6 artifacts, saved baselines, betting rules, safety/data-integrity controls, production deployment, model promotion, billing or merging without existing approvals. No separate approval needed for individual research pruning decisions.

## Shared baseline reconciliation — 26 November 2026

- [x] Reviewed the mandatory protocol at PR234 `6b205a5cab7e79a237d9fd1903a203c72d1bf8f1`; retain its startup/completion rules for current and future development.
- [x] Index completed issue240 workstream `cd775dc07a0a716ecb47a6e4db934c5fb451a72a` as `RUFFIES-240-20261126` in the shared Research Library, including null/negative and blocked findings.
- [x] Update the shared baseline handover with governing, production, trial and audit refs.
- [x] Permanent master handover established and reconciled with Work; the dated baseline remains historical evidence.
- [ ] Complete dependent exact academic replications on compatible data; Work #244 recovered the full Australian PLS paper, superseding the former access gap.
- [ ] Require genuinely later prospective improvement and owner approval before model/weight/threshold activation.

PR241 carries an older copied plan plus its additive issue240 section; reconcile it with this newer shared PR234 register before any eventual merge, retaining the substantive audit findings. Both remain unmerged. Keep both test_ruffies and test_pe_trial when eventually integrating their parallel CI additions. The six-day PE trial is untouched. Explicit owner instructions, including the $4 fixed-win progression, supersede older unresolved-cutoff wording. No betting policy change is made here.

## Independent predictive development — 26 November 2026

- [x] P0: Restore and verify the original AU archive, inventory matched context and recheck the pinned place sources, Queensland sectional captures and public PuntersEdge closing lines. Coverage and availability gaps are recorded.
- [ ] P0: Build registration-level, timestamped form and settlement joins, starting with permitted Australian authority data. Source independently complete named-bookmaker snapshots before testing fixed-win value. Keep missing source vintage and unresolved identities explicit.
- [x] P1: Test market, conditional logit, Benter-style combination, maintenance of market-calibration control, completeness-adaptive combination, PLS-inspired control and boosted challenger in four historical folds. Independent history helps standalone form but incremental market benefit is unproven. Exact Australian PLS replication remains open.
- [x] P2: Test a partial prior-start and connection block and four roughie bands. Record insufficient incremental edge and rare-winner sensitivity. No thresholds changed.
- [ ] P2: Isolate trainer-intent contributions on later authority-linked data. Gear/gelding, pedigree, speed/pace and hidden form require verified dated inputs and a separate ablation. Validate named-bookmaker and prospective outcomes on separate cohorts.
- [ ] Obtain genuinely later paired confirmation before considering any promotion or weight change. Existing official approval and all integrity rules apply.

[Draft #242 and evidence](https://github.com/Spankman/Monty-Racing/pull/242), research head `ad47142f9b824d74d05d30cdc467a416ad987229`. Codex data and engineering requirements are in the linked research handover. The six-day PuntersEdge trial remains a separate workstream.

## P0 inference evidence engineering — 26 November 2026

- [x] Staged full private runner/features/contribution evidence with licence gates, encrypted receipt binding and bounded recovery. [Draft #243](https://github.com/Spankman/Monty-Racing/pull/243), engineering head `19f6eede08d71349484fd4594d4c18262d68a3ad`, stacked on #241.
- [x] Historical #236–239 recovery searched existing artifacts, authorised workspace and backup. Original snapshot not recovered; 121 V6/118 V7 omitted runner records remain unavailable. No new provider calls.
- [x] Research-only consumer and diagnostic contracts expose market offsets, calibration, missingness/cancellation and market-normalisation effects without pretending conditional corrections are independent form predictions. Work's #242 remains separate and authoritative for its historical study.
- [x] Local 224 operational, 158 runner and 13 frozen integrity tests passed; all55V6hashes and17,987-runner/1,787-race replay verified. Synthetic-input genuine frozen V6/V7 evidence round-trip verified complete7declarations/12scores,55features and numerical replay <=1.1e-16. Exact-head CI evidence is tracked in #243.
- [ ] Provider-specific private-retention and separate public-display permission, durable owner recovery-key custody, original PE HTTP wrapper wiring and separately approved live acceptance before activation. Public metadata-only delivery when rights absent is explicit, not model NO BET.

[Engineering handover](https://github.com/Spankman/Monty-Racing/blob/19f6eede08d71349484fd4594d4c18262d68a3ad/operations/audit/INFERENCE_EVIDENCE_HANDOVER_2026-11-26.md) and [consumer contract](https://github.com/Spankman/Monty-Racing/blob/19f6eede08d71349484fd4594d4c18262d68a3ad/operations/RESEARCH_INTERFACE.md). No merge/deploy, model/threshold/weight change or interference with trial #235.

### Final engineering acceptance checkpoint — 26 November 2026

Draft #243 final tested head `112703369ad8386df50801627b02b2c656092cf2`: all four CI checks green, 225 operational/158 runner/13 frozen local tests, 25 new contract checks. Native connector artifact download + authenticated private replay verified 24 files/7 declarations/12 scores/both 55-feature matrices, max probability error 1.0061396160665481e-16. [Exact receipt and CI proof](operations/audit/evidence_retention_acceptance_20261126). Synthetic inputs, genuine unchanged frozen engines; zero provider calls, not live acceptance. Historical originals remain missing and licensing/key custody/live PE wrapper approval blockers remain open. Production and trial unchanged.

## Historical evidence and independent validation — 26 November 2026

- [x] Established [MONTY_MASTER_HANDOVER.md](MONTY_MASTER_HANDOVER.md) as the shared startup reference on draft #234.
- [x] Published historical source and feature coverage registers, eight disjoint chronological ablations and the #243 negative check showing the old archive fails verified availability.
- [x] Recovered the full West–Kazakov paper and evaluated a paper-informed eight-component comparison. No market edge demonstrated. Exact PLSGLR replication remains open.
- [x] Registered future Queensland test dates and evaluation rules before outcomes. Test capture and final candidate freeze not yet ready.
- [ ] Secure lawful official identity crosswalks, confirmed publication-time revisions, complete bookmaker vectors and independently settled results. Isolate additional feature blocks after verified acquisition.
- [ ] Freeze candidate manifest or mark 2027 window blocked. No production action without independent evidence and owner approval.

[Draft #244](https://github.com/Spankman/Monty-Racing/pull/244), `29239357579422148091a3320401d5e0572d774c`.

## Engineering readiness integration — 26 November 2026

- [x] Permanent master handover and mandatory startup/update protocol.
- [x] Reconcile #234 shared docs with #241/#243 evidence code; keep #242 research isolated.
- [x] Staged PE original-success-response acquisition wrapper, single-use guard and explicit field/provenance diagnostics; no new live calls.
- [x] Encrypted bounded progress checkpoints, interruption receipt/recovery and cleanup; hard runner-loss limitation explicit.
- [x] Explicit private-delivery blocked outcome preserves genuine inference classification.
- [x] Provider terms review and owner key/private-sink procedures documented.
- [ ] Owner source/cloud-processing confirmation, durable key backup, private sink authentication/access approval and genuinely live/mobile acceptance before deployment.

Current branch `integration/evidence-readiness-20261126` atop #243. [Assessment and rollback](operations/governance/INTEGRATION_READINESS_2026-11-26.md). Exact tests/CI are recorded in the draft PR. Zero provider API credits; trial #235 untouched.

## Final readiness engineering checkpoint — 26 November 2026

Draft [#245](https://github.com/Spankman/Monty-Racing/pull/245), exact tested head `fd901172448f0197b5adb69d8c196660a416f1f6`: allfourCIchecks green;239operational/158runner/13frozenlocaltests;39evidencecontracts. Native connector download+independent private decryption/replay verified base24files and syntheticPE26files,7declarations/12scores each,both55features,allmodelpins,and checkpoint salvage. Maxprobabilitydifference1.0061396160665481e-16. [Receipts/CI/aggregate proof](operations/governance/readiness_acceptance_20261126). Synthetic transport, genuine frozen engines;zero liveproviderAPIcredits,no live/iPhone acceptance. Source/cloudprocessing/private-display scope,keybackup,approvedprivate-deliveryauthentication and separatelyauthorisedlivevalidation remain deployment blockers. [Work input/identity handoff](operations/governance/WORK_INPUT_CONTRACT.md). Production/trial unchanged;no merge/deploy.

## Final operational readiness planning — 26 November 2026

- [x] Review current master/owner rules, #245 dependencies and Work #244 without repeating model experiments or live probes.
- [x] One [owner approval checklist](operations/readiness/OWNER_APPROVAL_CHECKLIST.md), unsent provider drafts, private sink/history conditions, iPhone custody steps, genuine live acceptance matrix, costs and rollback prepared.
- [x] Confirm current #226 head is already an ancestor of tested #245; no duplicate integration required.
- [x] Identify real remaining boundaries: private routing, paired-ticket publication, PNG/approved assets and unverified monitor activity. No new source-code defect demonstrated or speculative runtime change made.
- [ ] Obtain provider/cloud/archival confirmation and owner-approved private access/key backup; then scoped routing/presentation work and separately authorised live/iPhone/schedule acceptance.

[Consolidated report](operations/readiness/FINAL_OPERATIONAL_READINESS.md). No provider API credits, permission/secret changes, trial changes, merge or deployment. Existing #245 exact-head CI/replay evidence reused honestly.

## Historical data acquisition and December preparation — 26 November 2026

- [x] Verify free Racing Queensland historical meeting/race and horse/role endpoints. Publish 23-source and 79-feature coverage register, tested aggregate and bounded parser. Recover 68/97 issuer-scoped identity links across nine races and record 29 unresolved rows.
- [x] Check West–Kazakov appendix/input mismatch and record data and PLSGLR requirements. Do not fit again without compatible new data.
- [ ] Obtain dated declared/changed/final revisions and repeat identity observations, then build verified separate prior-start, trainer and jockey performance histories. Obtain rights before any wider collection.
- [ ] Add documented earlier gear/gelding, pedigree, grade, distance, speed, pace and interference only where source timing and identity pass.
- [ ] Authenticate independently published official outcomes and complete named fixed-win books. Exercise authorised shadow preparation only within existing permissions. Document the candidate freeze and fit-through-29-November/December calibration gates or mark the January–March cohort BLOCKED. No test-cohort tuning.

[Draft #246 at 49d9676](https://github.com/Spankman/Monty-Racing/pull/246). No refit or market-edge claim, paid product recommendation, new live API credits, merge, deployment or trial modification.

## Data quality and independent predictive science — owner alignment, 26 November 2026

Use the [audit disposition register](operations/audit/GROK_AUDIT_RESPONSE_2026-11-26.md) for evidence, responsibilities, dependencies and acceptance. Indicative effort: **45%** data verification, **20%** independent form modelling, **15%** academic replication, **10%** operational reliability/simplification, **10%** validation/statistics. Actual sequencing follows admissible data and readiness.

- [ ] Work P0: prospectively dated authority captures, scoped identities, repeated horse/role histories and independently settled results. Exhaust lawful free/current archives. Count admissible records and exclusion reasons ahead of download totals. Preserve #246 pilot limits.
- [ ] Work P1: odds-free race probabilities, followed by strictly earlier-fitted Benter and calibrated-market comparison. Keep frozen V6/V7 as references. Use new meaningful evidence or registered research gaps before additional builds.
- [ ] Work P1/P2: stage shrinkage, Plackett–Luce, explicit favourite–longshot stability and exact West–Kazakov research as data permits. Preserve all existing research indices and transparent no-quota roughie diagnostics.
- [ ] Codex: improve as-of quality and existing private delivery/one-capture workflow with measured end-to-end acceptance. Reuse evidence and result routing, avoid duplicate queues and preserve guards. Keep [one owner checklist](operations/readiness/OWNER_APPROVAL_CHECKLIST.md). Major redevelopment requires an evidenced blocker.
- [x] Assess preliminary [Queensland sample size and statistical power](operations/audit/QLD_VALIDATION_POWER_2026-11-26.md). Unmet readiness remains open. Record BLOCKED if gates fail and preregister any distinct follow-up before its outcomes. No change to dates, endpoints, safeguards or the separate six-day trial.

### Codex independent arithmetic verification — 26 November2026

[Draft #249](https://github.com/Spankman/Monty-Racing/pull/249), branch `research/audit-alignment-20261126`, supplements Work’s canonical audit register/power study; it does not introduce a competing register, prospective cohort or model variant. Reviewed/reconciled shared6921bf47ed48401175762fff25100e860ff70865. Independent SciPy/NormalDist checks match primary sample counts, with maximum log-loss-power difference5.91e-6 and binomial probability difference4.67e-7 attributable to rounded published output. SD/design/alpha/rare-event sensitivities are hypothetical; actual eligibility/variance/power remain unverified. Six mathematical regressions and byte-identical local reruns passed; exact final-head CI tracked in the draft.

Verified55originalV6hashes and pinnedV7 unchanged;no refit,newprediction,providercredits,spending,credential/permission changes,trial mutation,merge or deployment. Work owns verified-data/science;Codex owns supporting contracts/minimal reliability. The already-authorised data-first scientific sequence and indicative45/20/15/10/10priorities remain in the existing Plan. Existing owner checklist remains the only operational approval list.


## Owner-approved provider investigation — 26 November 2026

- [ ] Work P0: reconcile the existing canonical source register (no duplicate register) with Punting Form, RacingZone, Racing and Sports, Everyrace (Wizard/Superform), Australian Stud Book, Form Focus, Racenet, Punters.com.au, Racing Australia and state authorities. Retain existing Betfair, Krok and PuntersEdge entries. Investigate historical depth, machine-readable/bulk/API access, individual sectionals and positions, weights/claims, gear/gelding, pedigree, regional coverage, identities, publication/revision times, private modelling/backtesting/cloud retention rights, cost and strictly admitted rows. Free lawful sources first; no purchases or additional provider credits. Codex supports existing contracts only. Report verified findings and gaps in the next handover. [Owner instruction](https://github.com/Spankman/Monty-Racing/pull/234#issuecomment-7186406139). No trial or model changes.


## Operational consolidation — owner approval 26 November 2026

Day 1 trial report: 12/12 captures, both frozen engines scored, zero admitted forecasts and zero settlements. [Run 45736491530](https://github.com/Spankman/Monty-Racing/actions/runs/45736491530). Owner priority: make Monty reliable, economical and demonstrate net financial performance; defer discretionary redevelopment.

- [ ] Codex P0: diagnose Rockhampton authority FileNotFoundError from existing evidence; repair existing interfaces on separate staging branch, with regression proof. Support NSW/WA authority integration, field/emergency status and named complete fixed-win book verification; reuse existing contracts.
- [ ] Work P0: identify lawful independent NSW/WA/QLD authority and operator evidence, historical as-of compatibility and verified settlement sources. Compare PE/Krok matched freshness, completeness and actual credit cost using existing trial receipts. Distinguish missing evidence from provider failure.
- [ ] ChatGPT: track verified selections, settlements, win/exotic ROI separately, actual versus paper results, and operating costs; review exact repair evidence and maintain shared handover.

Preserve six-day trial protocol and branch, frozen models, selection rules and verification gates. No extra provider calls, purchases, merge, deployment or permission changes authorised. No forced bets or stake increases to recover costs. Repairs staged only; report blockers and measured acceptance, not assumed profitability.


## Operational consolidation repair handoff — 26 November 2026

Codex draft [#250](https://github.com/Spankman/Monty-Racing/pull/250), tested staging head `d005d711d1237c63ba3a5f72e98fa108336db4e8`, based on #245. [Report/register](https://github.com/Spankman/Monty-Racing/blob/d005d711d1237c63ba3a5f72e98fa108336db4e8/operations/audit/consolidation_20261126/REPORT.md). Day1 RQ failure has two causes: missing pdftotext runtime and missing scratching panel on race-detail HTML. Separate meeting-page acquisition, actionable decoder diagnostic, Rockhampton mapping and batch dedup staged; a trial runtime patch is review-only and not applied. Post-jump free RQ meeting page200 still has no explicit race2 nil-scratching state, correctly blocked. Settlement now preserves repeated results, rejects conflicts/tampering and retains all admission gates. Local244operational/33targeted/13frozen passed;55originalhashes unchanged. Exact-head CI green: [244 operational](https://github.com/Spankman/Monty-Racing/actions/runs/45812143753), [158 runner and6V7](https://github.com/Spankman/Monty-Racing/actions/runs/45812143742), all atd005d711d1237c63ba3a5f72e98fa108336db4e8. Runtime patch applies cleanly to trial8468904 but remains unapplied. Work owns lawful NSW/WA/source-status and independent named-book evidence plus strict as-of history; no duplicate source acquisition programme. Zero paid APIcredits;one free authority HTML investigation. Active trial, production, models, thresholds and existing future preregistrations untouched. No retrospective Day1 admission or profitability claim;merge/deploy/trial patch require owner approval.
