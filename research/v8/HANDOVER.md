# V8 — owner-authorised engineering handover
28 November 2026. Isolated branch from main. No production activation.
Grok supplied the Python skeleton; ChatGPT condensed comments/formatting and disabled fake market-as-V6 scoring with NotImplementedError. This is not a working engine.

## Responsibilities
Grok: independent read-only design/code review using accessible public material; identify simplifications and gaps, never invent private interfaces or request secrets.
Codex: inspect actual repository interfaces and integrate verified existing components; implement and test the following gaps.
Work: independently verify live data, scoring provenance, coverage, latency, delivery and acceptance. Record evidence and limitations.
Coordinate via #260 and PR #262; preserve PR #235 six-day trial and frozen V6/V7 artifacts. Do not merge or activate without owner approval.

## Gap register
| Function | Required completion |
|---|---|
| capture_snapshot | Reuse actual PuntersEdge client, verify coverage AU/NZ, full fields, odds, scratchings, barriers, required features, track conditions, provider timestamps; bounded timeout; no silent Krok fallback |
| Snapshot | Hash canonical immutable data and provenance; preserve real provider capture time; verify freshness (5 minutes, freeze 1 minute pre-jump) |
| validate_snapshot | Per-race validation for daily; exact meeting/date/country/race identity for single; reject incomplete/duplicate fields, missing/nonfinite odds, unknown scratching status, stale data; structured failure reasons |
| score_with_v6 | Reuse verified frozen V6 scoring entrypoint and feature schema, verify artifact manifest; no placeholder probabilities, no retraining; preserve normalised market and genuine model outputs |
| apply_betting_gates | Existing daily best bets and roughies only, strict qualification, NO BET allowed; explicit single race relaxed thresholds and genuine ranked selections whenever valid scoring possible, automatic maiden/2YO/hurdle override; label low confidence; existing $4 win-odds progression and boxed exotics, roughies standalone |
| write_result | Unique request IDs, atomic immutable receipts, verified hashes, private archive delivery and read-back, no restricted data in public comments; distinguish SCORED, NO BET, DATA_BLOCKED |
| handle_daily | Brisbane date, process valid races independently, report excluded races and coverage; do not hardcode final NO BET |
| handle_single_race | Exact race only, Brisbane request date and correct NZ mapping; do not hardcode NO BET; return rankings if scoreable |
| handle_status | Read-only latest request status/receipt, never trigger another run |
| main | Strict command validation, multiword track names, date handling, reject malformed commands; RM6/RM6 track race/C; optional RM6PS clearly labelled |
| workflow | Isolated test command routing, no production issue triggers, bounded execution, terminal responses on exceptions; reuse existing secure archive mechanism |
| ticket | Preserve approved black/white/gold ticket and deterministic exact PNG export |

## Acceptance
Repeated prospective live tests across AU metro/provincial/country and NZ, turf/dirt, scratchings, stale/invalid snapshots, outages, closed markets vs officially abandoned races. No fabricated picks, silent skips or stale results. A DATA_BLOCKED is error handling, not scoring success. Proposed targets: acknowledgement 10s, single race 60s, daily 180s, terminal response 99%, scoring 95% where independently adequate data exists; measure rather than claim. Verify hashes and private read-back, frozen V6 parity, automated tests, rollback. Keep prospective ledger vs market/favourites with win and exotic ROI separate. V7 and all Living Development Plan research remain separate, non-blocking. No expert collection or V7 scoring in V8 hot path. No secrets or restricted provider data in public files. No production changes until explicit owner approval.
