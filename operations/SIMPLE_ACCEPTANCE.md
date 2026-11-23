# Simple Actions/ChatGPT acceptance — 23 November 2026

The hosted-service proposal PR #123 is CLOSED, unmerged, with its branch/reports
preserved. No hosting, private plugin, custom MCP, new credential or subscription
is required. Production remains PR #104 merge
`a5a6e0f2ac7fab040251b7c1ba70f694274c1a17` until this repair is approved.

## Genuine connector-created production requests

Every request below was created by native ChatGPT `github_create_issue`, then
executed automatically by an Actions **issues** event. No workspace workflow
dispatch or manual user dispatch was used. Exact linked forecasts and receipts
were retrieved using native `github_fetch_file`, then their exact UTF-8 forecast
SHA-256 values were independently recomputed and matched to index/receipt.
Full IDs, timestamps, hashes and workflow URLs: [machine-readable evidence](SIMPLE_LIVE_EVIDENCE.json).

| Request | Command | Semantic outcome | V6/V7 scored races | Creation -> publication |
| --- | --- | --- | --- | --- |
| 124 | RM6 | COMPLETED_NO_BET | 4 / 4 | 65 s |
| 125 | RM7 | COMPLETED_NO_BET | 4 / 4 | 66 s |
| 126 | RM6PS | COMPLETED_NO_BET | 4 / 4 | 61 s |
| 127 | RM7PS | COMPLETED_NO_BET | 4 / 4 | 66 s |
| 128 | RM6 Ballina 5 | PARTIAL_OR_BLOCKED | 0 / 0 | 65 s |
| 129 | RM7 Ballina 5 | PARTIAL_OR_BLOCKED | 0 / 0 | 59 s |
| 130 | RM6 Barcaldine 2 | PARTIAL_OR_BLOCKED | 0 / 0 | 57 s |
| 131 | RM7 Barcaldine 2 | PARTIAL_OR_BLOCKED | 0 / 0 | 65 s |
| 132 | RM6, fresh replacement | COMPLETED_NO_BET | 1 / 1 | 63 s |
| 133 | RM6 Barcaldine 3; RM7 same-scope retrieval | COMPLETED_NO_BET | 1 / 1 | 67 s |

Publication latency is the result commit time minus issue creation time, NOT
full iPhone response latency. Native connector retrieval occurred while the
successful captures were fresh/pre-jump. By the time a future reader opens this
report, these are historical evidence, not current selections. Do not render
expired runners as current betting tickets.

Each successful execution genuinely ran BOTH frozen models on one capture.
Request 133's separate V6 provisional and V7 shadow views were retrieved; the
models have distinct probability outputs, not a copied/fallback prediction.
RM7 Barcaldine 3 then reused that same valid execution without another issue.

Blocked attempts were NOT counted as successful model inference. Both versions
refused the entire-field named fixed-win-price gate. The later full-day request
132 had only Barcaldine R3 scorable; coverage did not remain at four races. A new
single-race test selected that currently scorable race; neither frozen model nor
price validation was changed to make it succeed.

## Read-only C, repeated commands, aliases and stale replacement

- Native connector checks observed QUEUED (missing index) and RUNNING for the
  outstanding issue, followed that same ID to completion and retrieved its
  receipt. No C issue or workflow was created.
- Live read-only reference-client test on the unmerged repair:
  C for 133 returned the V6 single-race provisional ticket, capture age and
  expiry. RM7 Barcaldine 3 returned the genuine V7 counterpart from 133.
- RM6, RM7, RM6PS, RMV6PS, RM7PS and RMV7PS each reused full-day request 132
  while still within its original five-minute window. The last check was at
  capture age 294.34 seconds, before its 300-second expiry. All returned their
  correct model/view. GitHub access was guarded to GET only; any write or
  duplicate enqueue would fail the test. All responses were real GitHub data,
  not fixture forecasts. [Exact read-only evidence](SIMPLE_READONLY_EVIDENCE.json).
- Capture 124 at 03:04:52.518636 UTC expired at 03:09:52.518636 UTC. The newest
  earlier full-day capture 127 expired at 03:14:36.500860 UTC. The assistant
  created fresh request 132 through the connector at 03:18:27 UTC and retrieved
  its NEW 03:19:08.792502 UTC capture, valid until 03:24:08.792502 UTC. This was
  actual live stale replacement, not a simulated clock or expired forecast.
- Automatic enqueue logic, concurrent burst draining and shared-batch reuse in
  the NEW worker are regression-tested offline. Default-branch execution of
  that changed worker still requires an approved merge. Do not conflate the
  proven existing production issue transport with activation of this repair.

## Genuine repaired-branch staging

Workflow: https://github.com/Spankman/Monty-Racing/actions/runs/45105292235
Event: push. This is a branch test, not an ordinary-chat issue event.
Runtime commit: `53f02cda9538e47f30b41a515749f07706db5f41`.
Command supplied to worker: RMV6PS, normalized to RM6PS.
Results ref: `monty-simple-staging-results` (production results untouched).

Both models SCORED one race from capture 03:20:07.266783 UTC, with explicit
NO BET. The forecast, receipt, all views and daily index appeared in ONE commit
containing 18 files; no partial terminal publication occurred. Publication took
46 seconds from workflow creation. Native connector read the index, exact
forecast/receipt and separate V6 provisional/V7 shadow views before expiry.
No manual workflow dispatch, hosting, retraining or model fallback was used.
[Exact staging proof](SIMPLE_STAGING_EVIDENCE.json).

Forecast SHA-256:
`8c17d8716fa30e2d9b1308bda8c7c226ebde06c684cb18b954ba27a8c64ffbad`

Receipt-file SHA-256:
`06dacd40c62f879976be670baf4cd38c415975bc449462141933f575cd53c758`

Later changes to this branch add tests/documentation/evidence only; the runtime
source above is the exact live-tested executable source. CI checks the PR head.

## Offline and frozen integrity

```
python -m unittest test_simple_operations test_monty_operations test_adapter_parity test_krok_adapter test_readiness test_v06 test_v6_daily test_monty_daily_price_ladder test_monty_prospective_ledger test_operations monty_v6.test_integrity monty_v6.test_multivariable -q
Ran 93 tests in 0.832s — OK
```

All 55 original V6 manifest entries verified. Historical replay: 17,987 runners,
1,787 races; maximum probability difference `1.6653345369377348e-16`; refitted=false.
Only existing manifest-matching originals were restored into ignored local
paths for these tests. Original manifest, frozen weights and historical records
remain unchanged. No research pickle was loaded.

- V6 model: `f44e31f74ed017f915963950b17f144fbf6c994854403a39ba197fe5923d3fb7`
- V6 manifest: `99485842dc4d120f9c6f930889d42a6a317cfe9b6db2c6b5799a3e1063948c20`
- V7 model: `c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324`
- V7 code: `efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`

## Limits and activation requirement

- No merge/production activation of this repair without approval.
- Native ChatGPT issue creation and retrieval are demonstrated in this
  conversation. The physical iPhone/fresh-conversation UX was not directly
  operated; use [ordinary-chat instructions](CHATGPT.md) with connected GitHub.
- Repeated live requests span about 18 minutes, not an unattended full-day soak.
- Operations schedule query still showed zero event=schedule runs. Cron fallback
  is configured but unproved; issue-event runs succeeded independently of it.
- Independent TAB field/scratching/going attestation remains zero. Provider
  historical form completeness and prospective value verification remain gaps.
  All official selections remain NO BET. Do not weaken those evidence gates.
- Only AU observed; three provider meetings / 15 provider races. Full national
  coverage and NZ completeness are not verified. Show omissions and only
  source-supported partial assessments, never imply the entire TAB card.
- Existing $4 progression, model rules, renderer, immutable records and results/
  settlement code were preserved. Approved horse-head logo/legend assets and an
  active automated blackbook monitor were not identifiable in this repository;
  do not claim their presence or activity. No new monitoring was fabricated.
- GitHub/Actions/provider outages can still delay or fail a request. Report actual
  pending/failed/expired/data-blocked outcomes. A green job is never enough.
