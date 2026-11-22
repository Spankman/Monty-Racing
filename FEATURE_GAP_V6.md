# V6 feature-data gap audit — 2026-11-22

**Status:** Research and implementation planning only. Frozen V6 artifacts must not be modified. No betting authorization.

Latest verified GitHub readiness: run 44978660883, 48 races accepted, no predictions generated.

The frozen model has **55** input feature names. The current `krok_adapter.py` can provide or derive **up to 18**, conditional on runner data, prices, and track condition being present and valid. This is *not* measured runner-level completeness.

## Potentially supported by existing live intake (18)

- Market-derived (2): `log_market_probability`, `log_field_size`. Calculated downstream from complete active fields.
- Distance/barrier (6): `distance_km`, `barrier`, `barrier_fraction`, `inside_three`, `outside_barrier`, `barrier_x_distance`. Depend on source values.
- Weight (3): `allocated_weight`, `claim_kg`, `effective_weight`. May be missing; absence must not become zero.
- Going (6): `going_good`, `going_soft`, `going_heavy`, `going_firm`, `going_synthetic`, `going_unknown`. Unknown is not evidence of known suitability.
- Age (1): `age`.

## Unsupported by current live intake (37)

`observed_starts_log`, `observed_win_rate`, `observed_market_residual`, `year_starts_log`, `year_win_rate`, `year_market_residual`, `last3_win_rate`, `last5_win_rate`, `last3_market_residual`, `last5_market_residual`, `track_win_residual`, `distance_win_residual`, `track_distance_residual`, `going_win_residual`, `jockey_year_residual`, `jockey_90d_residual`, `trainer_year_residual`, `trainer_90d_residual`, `jockey_trainer_residual`, `horse_jockey_residual`, `days_since_run_log`, `resuming_60d`, `quick_backup_7d`, `distance_change_km`, `up_200m`, `down_200m`, `benchmark_class`, `benchmark_class_change`, `jockey_changed`, `trainer_changed`, `weight_change`, `is_gelding`, `first_after_gelding`, `blinkers_first`, `blinkers_off`, `tongue_tie_first`, `winkers_first`.

## Next engineering tasks

1. Persist a per-feature count from the existing `intake_only.capture()` coverage report into a **sanitized** GitHub status summary. Do not publish horse names, raw provider response, secrets or private archive.
2. Identify licensed/verified pre-race historical result and runner sources with timestamped as-of availability. Never reconstruct prior knowledge using post-race information.
3. Implement history joins using stable runner, jockey, trainer and race identities, with strict as-of cutoffs and explicit missingness.
4. Independently verify TAB fields, scratchings and fixed odds. Research-only scoring may run on verified complete features, but no betting labels until validated.
5. Test AU and NZ separately; freeze prospective predictions and odds before races.

**Integrity:** No invented features, no filling missing historical fields with zeros, no relaxation of completeness checks, and no modifications to frozen V6 model files.
