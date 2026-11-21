# Monty Expert Consensus — experimental branch

This is an isolated feature prototype, **not a trained Monty V7 Candidate 2 model**. Monty V6 and main remain unchanged.

Input records require race_id, runner_id, expert_id, published_at (timezone-aware ISO-8601), rank, and optional confidence. The prototype deduplicates each expert's latest eligible pre-cutoff selection and returns coverage, top-one/top-three votes, vote shares, weighted shares and confidence. Missing coverage is explicitly null, not zero.

**Known limitations:** currently assumes one runner per expert's latest selection; to ingest full ranked shortlists, group by expert + runner and validate unique ranks before training. Weights must be learned from *prior* races only. Experts may share syndicated content; deduplicate editorial sources. Do not treat a post-race tip as historical evidence. The published_at cutoff must precede the race and the odds snapshot. Verify runner IDs, scratches, publication timestamps, licenses and data availability.

## Evaluation gate

1. Collect timestamped predictions from up to ten distinct experts per race, with legal access and provenance.
2. Freeze pre-race odds, tipster data, and V6 predictions. Audit missing races and coverage.
3. Train baseline Monty-only, consensus-only and Monty+consensus on identical chronological folds, separately for AU and NZ.
4. Compare log loss, Brier score, calibration, strike rate, ROI, confidence intervals and coverage; include market benchmark.
5. Only consider promotion after prospective shadow testing; no model replacement based on retrospective gains alone.

Run unit tests: `python -m unittest discover -s expert_consensus_experiment -p 'test_*.py'` from repo root (or from this directory with `python -m unittest`).

**Status:** feature extraction prototype created; no tipster dataset acquired, model fitted or backtest run.

## New rules (18 Nov 2026)

- Per-race consensus is **valid only with 5–20 independent expert sources**. Below five, vote counts are retained for audit, but normalized consensus/confidence values are null and `expert_requirement_satisfied=false`. Monty-only scoring must remain available.
- More than 20 sources triggers an error: curate independent, predeclared sources, never select experts based on that race's results.
- `feature_priority.py` ranks feature groups from **paired chronological held-out ablation predictions**, reporting per-fold log-loss improvement and consistency. This is not a trained weight optimizer. Feature weights should be fitted with regularization on training folds, not assigned from test-set importance.
- Prioritise sourcing features by measured out-of-sample gain, availability, licensing, freshness and acquisition cost. Recheck interactions and rare-condition features before discarding apparently weak groups.
- No live experts were connected and no new model was trained by this change. Historical tip availability and tipster independence are outstanding.

Run `python -m unittest discover -s expert_consensus_experiment -p 'test_*.py'` at repository root.
