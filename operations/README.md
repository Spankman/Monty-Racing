# ChatGPT operational interface — GitHub Actions

Production PR #104 is active. The small reliability repair remains on a separate
unmerged branch; see `CHATGPT.md` for the ordinary-chat operating instructions.
PR #123 was closed: dedicated hosting, custom services and private plugins are
not being pursued. This branch changes transport/orchestration only. Frozen V6 and the V7 fold-3
candidate remain unchanged. This does not authorise wagers or V7 deployment.

## Architecture and audited alternatives

- Demonstrated: the ChatGPT GitHub connector can create issues, read files at
  an explicit branch, inspect workflow jobs/logs, and download artifacts.
- No connector workflow-dispatch method is exposed. `gh workflow run` works
  in the Codex execution workspace, but that is NOT proof ordinary ChatGPT can
  dispatch without that workspace.
- The activated `monty-operations.yml` handles owner command issues and runs
  both frozen engines from one timestamped capture. Live issue-event execution
  has been demonstrated. Scheduled catch-up remains separately unproved.
- Simplest supported route: connector creates a structured owner request issue;
  an Actions issue handler plus scheduled queue fallback runs the command with
  existing repository secrets. Connector reads a small immutable result index
  and derived forecasts on `monty-operations-results`. No new API server,
  MCPBackend, PAT in chat, or manual artifact transfer is required.

## Activation boundary

Production PR #104 is already activated. The reliability repair's issue-event
queue handling and aliases load from GitHub's default branch only after an
approved merge. Branch push tests run real frozen inference in isolation and
publish to `monty-simple-staging-results`; they do not activate the new default-
branch issue handler. Do not merge without owner approval.

The existing KROK_API_KEY, V6_ARCHIVE_URL and V6_ARCHIVE_TOKEN remain in Actions
secrets. No new credentials, hosting, subscription or manual user dispatch is
required for normal commands. Results remain on a separate branch, never main.
Existing schedules and results-review workflows are preserved. Morning/queue
cron success must be separately observed before claiming unattended recovery.

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
| RM6 | Return the current V6 official view, refreshing the daily capture if stale or unavailable |
| RM7 | Return the current V7 shadow selections, refreshing the daily capture if stale or unavailable. Official decision stays NO BET |
| RM6PS / RMV6PS | Return fresh V6 provisional ordered assessments; reuse a valid matching capture |
| RM7PS / RMV7PS | Return fresh V7 provisional research assessments; reuse a valid matching capture |
| RM6 Ballina 3 | Fresh capture; both models assess only Ballina R3; show V6 |
| RM7 Te Rapa 4 | Fresh capture; both models assess only requested race; show V7 |
| C | Read the latest relevant request, its status, capture times and receipt |

Every run computes BOTH versions so their comparison uses the same timestamped
source and byte-identical per-race JSON, including available source features.
Restricted-class analysis is allowed only for a specifically requested single
race, as in the existing owner rule. All official outputs remain NO BET under
current model/evidence gates; requesting provisional output does not change them.
Single-race commands default to provisional assessment with explicit NO BET.

### Connector retrieval and freshness

For a new daily RM6/RM7 command, check
`daily/YYYY-MM-DD/latest.json` for the Brisbane date on
`monty-operations-results`. Read the linked forecast and receipt on that same
ref. Compare the actual retrieval time against `captured_at`, `valid_until`,
the five-minute cap, and each race's scheduled jump. A usable live forecast
can be displayed. Otherwise create one fresh command issue using the format
above. For any selection command, reuse the newest matching pending or still-fresh
request first, including across model/provisional views of the same scope.
Otherwise create a fresh request. Never fall back past a newer failed/expired
request to older selections.

After creating issue N, retain its number in the conversation and fetch
`requests/N.json` on `monty-operations-results`. Until an index appears,
report QUEUED with the issue number. The worker writes QUEUED and RUNNING
indices with the request ID, run ID and workflow URL. Read this same index
while it is pending and use only its linked forecast and receipt when it
completes. Never switch back to the daily index while following an issue.
If the terminal attempt failed or its output expired, report that outcome.
If status publication was unavailable and the linked workflow has ended,
re-read the index once to account for a concurrent terminal write. If it
still shows RUNNING, report that the workflow ended without publishing a
terminal status.

For C, use the request number from the current conversation when available.
Otherwise find the latest owner-authored Monty command for the relevant
Brisbane date and scope, including pending requests. Use the daily index
only when there is no matching issue. Report request ID and status, run ID
and workflow status where available, semantic outcome, captured_at,
capture_age_seconds, valid_until and receipt. Leave unavailable fields
explicitly blank. C uses connector reads only.

The index gives `forecast_path`, `receipt_path`, run_id, date, status and
SHA-256. Stored previews alongside those paths are `v6-official.json`,
`v6-provisional.json`, `v7-shadow.json`, `v7-official.json` and
`v7-provisional.json`, with plain-text and HTML equivalents. RM7 displays
the shadow view and retains V7 research-only and official NO BET labels.
Use the immutable forecast to re-evaluate freshness before displaying
a view or ticket. Archived HTML/text tickets carry historical quote labels.
For earlier runs without a shadow file, use the V7 provisional view after
rechecking freshness. A fresh card can still contain races that have jumped;
omit their runner selections and identify them as closed.

`python -m operations.client` is an executable reference for this contract.
It uses an authenticated GitHub CLI. For example, to follow an existing
request without submitting another, run
`python -m operations.client RM7 --request-id N`. Use
`python -m operations.client C --request-id N` to read its status. The
ordinary ChatGPT client uses the equivalent connector operations.

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
The worker records timeouts and launch failures as FAILED with a sanitized
receipt. If publishing the forecast fails, the worker records terminal
FAILED with the workflow URL and no forecast or receipt pointer, if GitHub
accepts the status write. During broader publication outages, the workflow
fails and logs a sanitized status marker. Completed request indices and
forecast files are immutable.

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
queue fallback catches up a missed daily slot after 08:10 if no daily attempt
was published, and processes connector-created requests, with global concurrency,
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


## Single-race fallback hierarchy

RM6/RM7 track race now select the highest valid tier automatically: existing
OFFICIAL requirements, genuine frozen-model PROVISIONAL rankings, or an explicit
independent FORM ASSESSMENT handoff to ChatGPT. The latter is not a completed
model forecast: ChatGPT must research the exact race, cite actual sources and
then provide the independent assessment without asking for an extra command.

Both frozen models require whole-field market probabilities. Never invent odds,
uniform priors, incomplete-field normalization or replacement weights. Complete
provider quotes may support provisional inference without independent TAB
attribution. Missing prices/identities/scratchings and V7's original minimum-
field/consistent-provenance restrictions remain genuine model limitations; they
trigger public form research rather than a falsely labelled Monty prediction.
Technical failures stay visible. Official NO BET and full-day rules are unchanged.

Only selected factual evidence is included in the handoff: known runner identity,
observed quote/source, scratching flags and available basic race facts. No raw
provider envelope, credentials, private historical form records or fake ranked
predictions are published. Independent sources must be accessed with tools that
actually exist; missing research access must be disclosed.

The unchanged $4 ladder applies only when its required actual prices are present.
Without them, independent form rankings can show ODDS UNAVAILABLE and a deferred
bet type. Distinguish most-likely winner from value; value cannot be fabricated
when price/comparison evidence is absent. See CHATGPT.md for automatic handling.

This branch's live push test uses the existing workflow and existing secrets for
RM6 Ballina 7, isolated on monty-single-staging-results. It does not activate the
new single-race behaviour on production without an approved merge.


## Workflow stage timings

The Actions worker emits structured `MONTY_TIMING` lines in the job log. Queue
discovery covers issue listing and candidate index lookups. An issue-triggered
worker performs one owner-validated issue lookup and publishes the triggering
request before scanning and draining older entries. Scheduled queue and daily
catch-up remain available. Current request index
reads and QUEUED/RUNNING writes have separate spans. Within the runner, frozen
verification and the actual provider fetch are logged separately. Fetch time
includes any provider pagination, retries and retry waits. Runner total includes
both spans plus startup, scoring and rendering. Result publication is timed
separately. Additive totals must not double-count the two nested runner spans.

Durations use a monotonic clock. Each mark contains only fixed stage/outcome
labels, a run ID and elapsed seconds. It is workflow diagnostic metadata and
does not enter forecasts, receipts or tickets. An `ok` timed span only means
the operation returned without raising. Check the existing semantic forecast
status to determine whether either model scored.
