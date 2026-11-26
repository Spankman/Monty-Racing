# Monty Racing — Living Development Plan
Owner direction, 25 November 2026. Read before planning Work or Codex sessions. Supplements existing betting and integrity policies; does not override them.

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

## Issue 240 roughie audit update — 26 November 2026

- [x] Hash-verify requests236–239 shared forecast and artifact; document the unpreserved121V6/118V7 scored runner records without inventing exclusions.
- [x] Audit static market offsets, saved calibration temperature, missing-history cancellation and inactive expert blending; no operational90/10 claim.
- [x] Run frozen-model chronological month evaluation and the requested four odds bands, settlement-only place joins, day-bootstrap uncertainty and high-price winner stress tests. Exchange prices are proxies, not named fixed-win validation.
- [x] Stage RUFFIES TO WATCH diagnostics across official/provisional views and compact/mobile tickets; no quota, production threshold, model or approval change.
- [ ] Recover the exact original236provider snapshot/shared inputs and missing per-runner scores for a complete named $10+ exclusion audit.
- [ ] Obtain licensed historical named-bookmaker fixed-win quotes and original fold1/fold2 artifacts/evaluation records before claiming full fixed-win walk-forward acceptance.
- [ ] Independently validate compatible as-of form and lifetime horse identities; original feature groups, Trainer Intent, pedigree, sectionals and hidden-form hypotheses remain research, not active model additions.
- [ ] Require owner-reviewed later prospective improvement before any calibration/weighting/threshold change. Six-day PE trial is untouched; no new live API credits consumed.

Evidence and handover: [issue240audit](operations/audit/RUFFIE_AUDIT_2026-11-26.md). This plan copies the unmerged owner document from draft234; reconcile its additive update with that draft before any eventual merge. No production merge or model activation is authorised.

## Inference evidence engineering — 26 November 2026

Staged workstream `engineering/inference-evidence`, based on #241. Canonical shared governance remains PR #234 (`fb5f8b4481c535f5415b8ad3ed285579885bd48b` reviewed); reconcile this older copied plan before eventual integration.

- [x] Complete private evidence packet, all scored/declaration records, frozen feature/contribution replay and receipt-bound encryption implemented.
- [x] Historical #236–239 archive search: originals not recovered; 121 V6/118 V7 records remain unavailable.
- [x] Research-only diagnostics/consumer and explicit roughie assessment states implemented; no training or weighting activation.
- [ ] Source retention/public-display permission, durable owner key custody and live wrapper verification before production approval.

See [engineering handover](operations/audit/INFERENCE_EVIDENCE_HANDOVER_2026-11-26.md). Work's #242 research remains separate; trial #235 untouched. No provider credits, merge or deployment.
