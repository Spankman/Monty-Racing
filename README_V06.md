# Monty v0.6 — additional deterministic features and pagination safeguards

Builds on v0.5 without retraining the frozen Monty V6 model.

- Calculates `barrier_fraction`, `inside_three`, `outside_barrier`, `barrier_x_distance`, and `effective_weight` from source data when available.
- Rejects Krok responses advertising `next_cursor`, `next_page`, or `next` as well as `has_more`/`truncated`; never silently calls a partial national feed complete.
- Adds offline regression tests for the derived features and cursor pagination.
- Does **not** solve the Python runtime DNS restriction or verify the actual Krok API key. No real 14 November race-day runners were scored.
- Existing feed adapter has not been validated against a live Krok response; its field assumptions may require correction. Price source is not independently TAB verified. Do not treat synthetic selections as betting tips.

Run tests: `python -m unittest test_krok_adapter test_v04 test_import_fields test_discover_meetings test_v06 -q`.
