# Monty Racing — agent instructions

Applies to all repository development sessions, including Codex, ChatGPT Work and other agents. Owner instructions and existing safety policies take precedence.

## Mandatory startup
1. Before starting or resuming any development, read the latest versions of this file, README.md, MONTY_BETTING_POLICY.md, SELECTION_RULES.md, MONTY_LIVING_DEVELOPMENT_PLAN.md, MONTY_RESEARCH_LIBRARY.md, operations/README.md, [MONTY_MASTER_HANDOVER.md](MONTY_MASTER_HANDOVER.md), the active workstream handover and any applicable owner-approved rules.
2. Check open issues and draft PRs, their latest comments, dependencies and exact tested commits. Review PR #234 for the owner-approved development register until integrated. Record each governing document's date or version and GitHub ref and full commit SHA, including the exact workstream base. Identify unavailable documents and research explicitly, record the access limitation and its scope, and leave any work that depends on them pending.
3. Reconcile conflicting or superseded instructions against explicit owner decisions. Identify blockers and the highest-priority authorised task; do not expand scope without approval.
4. Reuse existing evidence and datasets. Avoid repeated audits of unchanged commits; use scripts for repetitive work, checkpoint long tasks and bound retries. Report observable resource consumption and never guess credit balances.

## Non-negotiable safeguards
V6 remains frozen and official; V7 is research-only. Preserve betting policy, freshness gates, NO BET, provenance and pre-race forecast integrity. Never invent data or predictions. Keep licensed raw data and secrets private. No merge, deployment, subscription purchase, billing change or model promotion without owner approval. Reading a work order does not itself authorise unrelated changes.

## End of session
Update the living development register with evidence-backed status and leave a concise dated handover in the relevant issue/PR or linked document. Include exact branch/commit, completed work, tests and limitations, blockers, observable credits/costs, next actionable step and required owner approvals. Link evidence rather than duplicate it. Do not mark unverified work complete.

GitHub is the shared source of truth, not an automatic messaging service. Agents must explicitly inspect current repository state at startup; do not assume another agent has read a new issue or branch.

## Research before development
Review relevant academic methods and previous Monty experiments before implementation. Review the existing code and reuse verified methods and legally reusable code. For modelling work, reproduce the applicable published baselines wherever practical and document any approximation or unavailable material. Test whether modern data, statistical methods or machine learning add measurable value beyond those baselines and an independent market benchmark on the same eligible races and decision times. Use chronological, leakage-free, reproducible testing. Record successful, null, negative and blocked experiments in MONTY_RESEARCH_LIBRARY.md or link a durable experiment record there. Update the Living Development Plan and shared handover with exact evidence references at completion so ChatGPT, Codex and Work can resume from the same baseline.

## Optimise before expanding — owner rule
Prioritise data quality, interpretation of existing features, redundancy removal, weighting, calibration, value and race selection before adding features. Require incremental independent information, repeatable out-of-sample benefit, justified acquisition/maintenance/compute costs and no reliability regression. Assess net ROI, calibration, uncertainty and risk, not strike rate alone. Prefer the simpler model when evidence does not justify complexity; reject or defer marginal features. Preserve frozen V6 and existing approval safeguards.

## Delegated feature pruning — owner approval 25 November 2026
ChatGPT, Work and Codex may independently remove or disable redundant, ineffective or unjustifiably costly predictive factors and research features in development candidates without seeking prior owner approval. Use proportionate evidence (existing tests, ablations, redundancy or documented cost/benefit); retain reproducible baseline and rollback, record rationale and uncertainty, and notify owner afterwards in the next handover with affected features, evidence and impact. Do not treat inconclusive evidence as proof of harm. This authority does not permit changing frozen V6 artifacts, saved baselines, betting rules, safety/data-integrity controls, production deployment, model promotion, billing or merging without existing approvals. No separate approval needed for individual research pruning decisions.
