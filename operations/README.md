# ChatGPT operational interface (staging)

This branch adds transport/orchestration only. Frozen V6 and the V7 fold-3
candidate remain unchanged. This does not authorise wagers or V7 deployment.

## Architecture and audited alternatives

- Demonstrated: the ChatGPT GitHub connector can create issues, read files at
  an explicit branch, inspect workflow jobs/logs, and download artifacts.
- No connector workflow-dispatch method is exposed. `gh workflow run` works
  in the Codex execution workspace, but that is NOT proof ordinary ChatGPT can
  dispatch without that workspace.
- Existing default-branch issue handling supports only V7 single races. Existing
  polling exists because integration-created issues may not fire issue events.
  Existing daily jobs fetch separately; V6 readiness/daily and V7 shadow jobs
  do not provide one shared source snapshot contract.
- Simplest supported route: connector creates a structured owner request issue;
  an Actions issue handler plus scheduled queue fallback runs the command with
  existing repository secrets. Connector reads a small immutable result index
  and derived forecasts on `monty-operations-results`. No new API server,
  MCPBackend, PAT in chat, or manual artifact transfer is required.
- Secure callable API/custom MCP is an alternative only if its authenticated
  action/tool is actually installed and granted access. None has been
  demonstrated here. A GitHub App using short-lived installation tokens and
  scoped Actions/contents permissions would avoid long-lived client keys, but
  adds hosting/authentication and is unnecessary for the queued route.

## Activation boundary

New issue triggers and schedules load from GitHub's DEFAULT branch. They do not
activate simply because this integration branch passes CI. Do not merge without
owner approval. Manual branch workflow dispatch can test staging; it cannot prove
unattended default-branch activation. The existing issue workflows remain intact.
The issue title prefix `Monty command: ` avoids invoking legacy handlers.

Minimum production action after review: approve activation of the new workflow
and its code on the default branch, with Actions contents-write and issues-read
permissions and the existing KROK_API_KEY, V6_ARCHIVE_URL and V6_ARCHIVE_TOKEN.
Results publish on a separate branch, never as forecast commits on main.
Existing scheduled jobs are not disabled here; consolidate redundant production
schedules only in that reviewed activation change to avoid duplicate API usage.

## Exact ChatGPT invocation

For a fresh execution, call `github_create_issue` with:

```
repository_full_name: Spankman/Monty-Racing
title: Monty command: RM6PS
body: {"date":"2026-11-23"}
```

The body is strict JSON with only optional `date` (YYYY-MM-DD Brisbane) and
`country` (AU/NZ). If omitted, the creation date is the target date; old requests
are not silently moved to today's card. Only requests authored by Spankman are
accepted. A request never supplies credentials, code, paths or model choices.
The workflow uses subprocess argument lists, not shell interpolation of commands.

| User command | Result |
| --- | --- |
| RM6 | Fresh dual capture/inference; return V6 official NO BET/qualified view |
| RM7 | Fresh dual capture/inference; return V7 research official NO BET view |
| RM6PS | Fresh dual run; return V6 provisional ordered assessments |
| RM7PS | Fresh dual run; return genuine V7 provisional research assessments |
| RM6 Ballina 3 | Fresh capture; both models assess only Ballina R3; show V6 |
| RM7 Te Rapa 4 | Fresh capture; both models assess only requested race; show V7 |
| C | Read status/index/receipt; do not dispatch or reuse old odds as fresh |

Every run computes BOTH versions so their comparison uses the same timestamped
source and byte-identical per-race JSON, including available source features.
Restricted-class analysis is allowed only for a specifically requested single
race, as in the existing owner rule. All official outputs remain NO BET under
current model/evidence gates; requesting provisional output does not change them.
Single-race commands default to provisional assessment with explicit NO BET.

After creating issue N, use `github_fetch_file` with:

```
repository_full_name: Spankman/Monty-Racing
ref: monty-operations-results
path: requests/N.json
```

If not found: PENDING, not failed and not successful. Check workflow jobs or
retry after the queue interval. Do not invent a receipt. The index gives
`forecast_path`, `receipt_path`, run_id, date, status and SHA-256. Retrieve these
with the SAME explicit ref. For daily results use `daily/YYYY-MM-DD/latest.json`.
Forecast views alongside those paths are `v6-official.json`,
`v6-provisional.json`, `v7-official.json`, `v7-provisional.json`; plain-text
and HTML ticket equivalents use `.txt`/`.html`. No manual download is required.

C example: "Run 123-1-456 completed; V6 scored 8, V7 scored 8; both official
NO BET. Prices captured at 08:10 AEST, now STALE; use RM6PS/RM7PS for fresh output."
Numbers in this example are illustrative, not execution evidence.

Receipts store the SHA-256 of the exact forecast.json bytes. There is no
self-referential hash inside that file. Verify bytes in a compute-capable client;
if ChatGPT only reads connector text, say hash is supplied but not recomputed.
Each model's commit and model hash are pinned/recorded; V7 is pinned to
`efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`, model hash
`c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324`.

## Freshness, failures and safety

Check captured_at, valid_until, scheduled_start AND latest status at retrieval.
Five-minute freshness is the existing V6 acceptance window, not a new value
threshold. A stale historic forecast stays immutable but must be labelled STALE
and NO BET when retrieved; a before-jump capture does not stay fresh all day.
Failed attempts publish FAILED with no substitute selections; per-model failures
remain separate, and are never replaced with another model or tipsters.
Publication errors fail the workflow; the absence of a new completed request
index is not permission to show a previous success as that request's result.

The runner is not an independent TAB verifier. Coverage includes observed AU/NZ
meetings and provider skips, with `complete_au_nz_coverage_verified=false`.
Unknown country, ambiguous identities, due/missing jump time, unnamed/mixed price
sources and common fields below three runners are blocked. No assertion of NZ
model validation is made. Unknown inputs use only saved imputation.

Only derived forecast selections, requested scratching metadata, completeness
flags, safety reasons and receipts are public. Raw feeds, full feature matrices,
private historical archives, credentials and arbitrary exception strings stay
out of publication. Private intermediate files are ephemeral. Original manifest
checks run before V6 scoring. No fitting, pickle loading or exotic-dividend
pricing is added. Existing $4 fixed-WIN price ladder is reused; roughies stay
standalone WIN assessments. All actionable decisions remain NO BET.

The HTML ticket uses white/black/gold, track grouping, bold leading runner,
right-aligned fixed-win odds, only progression runners, explicit provisional/
NO BET labels, copyable plain text and IN MONTY WE TRUST. It does not expand
Monty as an acronym. Plain text remains fully usable through connector reads.

## Scheduling and reliability limits

`10 22 * * *` is 08:10 Brisbane the following calendar day. GitHub cron is
best-effort and can be delayed/dropped; it is not a hard 08:10 SLA. A five-minute
queue fallback processes connector-created requests, with global concurrency,
immutable per-request completion records and no duplicate processing on retries.
Requests that failed are immutable completed attempts; request a new issue to retry.
For a guaranteed 08:10 trigger, an authenticated external scheduler and alerting
is an additional infrastructure requirement. Do not claim it is provisioned.

## Acceptance evidence

Simulated unit tests: `python -m unittest test_monty_operations -v`.
They mock model inference and do NOT establish live execution. Live evidence,
connector retrieval and CI references are recorded separately in ACCEPTANCE.md.
A live run that fails provider pagination or verification is a genuine failed
attempt, not a passing end-to-end inference test. Do not equate passing CI with
an operationally activated ordinary-ChatGPT service.
