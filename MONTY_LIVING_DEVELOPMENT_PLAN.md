# Monty Racing — Living Development Plan
Owner direction, 25 November 2026. Read before planning Work or Codex sessions. Supplements existing betting and integrity policies; does not override them.

## Mandatory development and research protocol — 26 November 2026
- Apply the startup and completion requirements in [AGENTS.md](AGENTS.md) to current and future development. Keep governing documents, prior findings and workstream commits pinned in the shared handover.
- Review applicable research before implementation and reproduce relevant academic baselines wherever practical. Compare modern alternatives against matched academic, frozen-engine and independent market baselines using chronological leakage-free evaluation. Record negative and blocked runs along with successful ones.
- Keep the [research library](MONTY_RESEARCH_LIBRARY.md), this plan and the shared handover current. The [baseline handover](MONTY_BASELINE_HANDOVER_2026-11-26.md) records this protocol update and identifies the missing master handover.

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
