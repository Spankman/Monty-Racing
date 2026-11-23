# Monty serving audit — 23 November 2026

Production base: `a5a6e0f2ac7fab040251b7c1ba70f694274c1a17`, merged PR #104.
Candidate branch: `integration/permanent-runtime`. Production unchanged.

## Genuine existing live inference, retrieved through ChatGPT's connector

These are prior production Actions runs, not tests of the new HTTP service or
proof of fresh-conversation/iPhone access. Full forecast and receipt bytes were
retrieved using the native GitHub connector on `monty-operations-results`.
Independent SHA-256 recomputation matched each unchanged index and receipt.
All are now expired; no current selection slips are issued from them.

| Request | Command | Capture UTC | Forecast generated UTC | Public result commit UTC | Request -> publication |
| --- | --- | --- | --- | --- | --- |
| [120](https://github.com/Spankman/Monty-Racing/issues/120) | RM7 | 00:14:19.982110 | 00:14:23.845453 | 00:14:48 | 66 s |
| [121](https://github.com/Spankman/Monty-Racing/issues/121) | RM6 | 00:26:15.612570 | 00:26:19.644750 | 00:26:40 | 63 s |
| [122](https://github.com/Spankman/Monty-Racing/issues/122) | RM6PS | 00:29:36.419886 | 00:29:40.467321 | 00:29:59 | 83 s |

All times are 2026-11-23; add ten hours for Brisbane. Request creation timestamps
were 00:13:42, 00:25:37 and 00:28:36 UTC, respectively. Publication is the result
branch commit's committer timestamp, not the job's green completion time or a
measurement of mobile receipt latency. None met the full-day 60-second target
on this measure. Capture-to-generation was approximately 3.86, 4.03 and 4.05 s;
this is not full request latency or proof of the single-race 15-second target.

Each receipt says LIVE, V6 SCORED four races, V7 SCORED four races,
`COMPLETED_NO_BET`, zero qualifying forecasts and unchanged artifacts.
Both models used the same capture within each execution. Coverage: 3 provider
meetings, 15 provider races, 11 accepted races, 4 scored by both; independently
verified 0; only AU observed; full AU/NZ coverage not verified. Official NO BET
remains justified. No current TAB verification is inferred from bookmaker names.

- 120: [workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45087520763),
  [receipt](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-23/45087520763-1-120/receipt.json).
  Forecast SHA-256 `972ad6d54e1fdc72f639020ce3421394d3e33ed3c1cddee48192ac2019a80051`.
  Receipt-file SHA-256 `d54b2456d989eec98c7028e2641bd3987564482af7eefdc99f8244082e0d248a`.
- 121: [workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45088709509),
  [receipt](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-23/45088709509-1-121/receipt.json).
  Forecast SHA-256 `c65e7a942f0f2126f7bf8ffadaa561d20dbb7e77d58883a63ec0cc7822a94f30`.
  Receipt-file SHA-256 `8047d2081eec4d51ae9e761e7764c11a30b72899437f8522f1ecbd853262b457`.
- 122: [workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45089023300),
  [receipt](https://github.com/Spankman/Monty-Racing/blob/monty-operations-results/runs/2026-11-23/45089023300-1-122/receipt.json).
  Forecast SHA-256 `4613151db7e8cadb288dc28667645c8371a247cb379955781fda505b63a59c9b`.
  Receipt-file SHA-256 `2ec7cb78aef7204397b29f0c0fdcd221bca880259618420489086972a8c4f563`.

Operations workflow schedule query returned `total_count: 0` on 23 November UTC.
Both morning/queue crons exist, but unattended execution is not demonstrated.
The requested 24 November 08:10 Brisbane morning is still in the future at this
audit and cannot be claimed as completed.

## Offline evidence — not live acceptance

```
python -m unittest test_runtime test_monty_operations test_adapter_parity test_v06 test_v6_daily test_monty_daily_price_ladder test_monty_prospective_ledger test_operations monty_v6.test_integrity monty_v6.test_multivariable -q
Ran 87 tests in 4.881s — OK
```

28 are new simulated serving/provider/HTTP/MCP security tests. They emit protocol
NO BET stubs with no predictions and do not replace actual frozen inference.
The rest cover original adapters, contracts, scoring safeguards and replay.

```
PYTHONPATH=monty_v6 python -m monty.integrity
PASS: 55 artifact hashes

PYTHONPATH=monty_v6 python monty_v6/verify_project.py
artifact_hashes: 55
replayed_runners: 17987
replayed_races: 1787
maximum_probability_difference: 1.6653345369377348e-16
refitted: false
```

Only manifest-matching missing originals were copied from the existing local
archive extraction into ignored paths for these tests. No model, manifest,
preprocessing, original historical record or research pickle was changed.

Local credential check: actual environment has no KROK_API_KEY. New service
request `628d110b56b1430cb6204aac07f5e1a0`, job
`c0c0156685bf464bb10b7626fc090376`, recorded FAILED /
PROVIDER_CREDENTIALS_MISSING in ignored private SQLite state. No provider
request, inference, forecast capture or live inference receipt was produced.
GitHub Actions' secret is not assumed to exist here and was not requested.

## Frozen hashes

- V6 model: `f44e31f74ed017f915963950b17f144fbf6c994854403a39ba197fe5923d3fb7`
- V6 manifest: `99485842dc4d120f9c6f930889d42a6a317cfe9b6db2c6b5799a3e1063948c20`
- V7 model: `c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324`
- V7 source commit: `efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`

## Still unproved

New backend live execution, TLS deployment, private Sites plugin publication,
Plus/iPhone tool invocation, fresh-conversation retrieval, live latency targets,
automatic provider recovery against a genuine transient outage, operational
monitoring, automatic daily scheduling and unattended restart/catch-up.
No paid hosting or deployment was started. No wagers were placed.
