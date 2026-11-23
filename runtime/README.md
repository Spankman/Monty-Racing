# Permanent Monty service candidate — NOT operationally accepted

This is a separate serving branch based on production commit
`a5a6e0f2ac7fab040251b7c1ba70f694274c1a17`. It does not change the frozen
V6/V7 engines, model artifacts, preprocessing, manifest, betting thresholds,
$4 ladder, existing renderer, or production schedules. Do not merge or activate
this candidate before the client and hosting gates below are demonstrated.

## What exists

A Linux Python HTTP/MCP service wraps `monty_operations.execute` directly.
It does not dispatch GitHub workflows, invoke tipsters, retrain, or load a
research pickle. Each execution scores both existing engines on one captured
provider card. A single-race scope is separate from a daily scope; it cannot
silently return the daily card or another track.

- Authenticated REST: `POST /v1/commands`, `GET /v1/status/{request_id}`.
- Stateless MCP: `POST /mcp`; tools `monty_execute` and `monty_status`.
- SQLite WAL persists requests, job status and receipt locations. A process lock
  enforces one worker owner. A crash records interrupted jobs as FAILED on
  restart, rather than silently repeating provider calls.
- One inference worker, at most 16 queued/running scopes. Concurrent equivalent
  requests coalesce. Each caller still gets its own request ID.
- Valid model/view requests reuse a completed capture immediately. A shared
  in-memory provider cache lasts at most five minutes; requested stale scopes
  trigger acquisition and inference again. The original jump-time checks remain.
  There is no speculative/background provider polling in this candidate.
- Provider calls use the fixed original Krok meetings endpoint, pagination/count
  validation, bounded attempts, socket timeouts, a 20-second acquisition budget,
  Retry-After cooldown and no redirect/credential forwarding. Authentication
  errors and incomplete cards fail closed. This is not a hard real-time deadline:
  socket reads and the original per-race subprocess timeout may exceed targets.
- Every completed forecast and original engine receipt is retained under the
  private state volume. C rechecks forecast hash/run identity and freshness.
  Expired selections are withheld. A new request creates a new run without
  overwriting old evidence. Receipt hashes are returned independently.
- JSON includes model outcome, capture age, expiry, receipt, plain-text ticket and
  the existing white/black/gold HTML ticket. It never generates an image.

## Commands and PS meaning

| Command | Existing engine/view |
| --- | --- |
| RM6 | V6 official; preserve all official NO BET gates |
| RM7 | V7 shadow, RESEARCH ONLY |
| RM6PS / RMV6PS | V6 provisional ordered assessments |
| RM7PS / RMV7PS | V7 provisional research assessments |
| RM6 Ballina R5 | V6 single-race provisional assessment |
| RM7 Ballina R5 | V7 single-race provisional research assessment |
| C | Read status/results only; never fetch data or start inference |

PS was verified against `operations/README.md`, `monty_operations.command` and
`SELECTION_RULES.md`: it means provisional assessment with explicit missing-data
and NO BET disclosures. It is not a different predictive model or approval to bet.
The aliases are normalized at the new service boundary only. Unlike the old
issue transport's always-new PS request, this service reuses still-valid results
as requested by the user. Model/view semantics and freshness limits are unchanged.

Example REST body: `{"command":"RM7PS","date":"2026-11-23","country":"AU","wait_seconds":10}`.
Use today's Brisbane date, or omit date. Omit country for AU/NZ coverage; AU/NZ
filters cannot create meetings absent from the provider. Live historical-date
requests are rejected before any provider call.

C body: `{"command":"C","request_id":"<returned 32-character request ID>"}`.
Without an ID, C reads the latest request. `Idempotency-Key` is supported for
safe retry of the same command. Reusing it after expiry returns that expired
request; a genuinely new operation must use a new key. C never refreshes it.

Response states include QUEUED, RUNNING, FAILED, COMPLETED, EXPIRED and NOT_FOUND.
The independent `semantic_outcome` and `model_outcome` must also be checked:
COMPLETED transport alone does not establish successful scoring, complete coverage
or a qualifying bet. NO BET must not be presented as an infrastructure failure.

## Client compatibility investigation — gate still open

Official OpenAI documentation checked on 23 November 2026:

- [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt):
  Sites-hosted plugins can be created on any plan. Mobile plugin availability
  depends on capability. This does not itself prove this user's iPhone tool calls.
- [Hosting a plugin with Sites](https://help.openai.com/en/articles/20001547-hosting-a-plugin-with-chatgpt-sites):
  publishing an MCP-capable Site provisions its private plugin. Plugin Creator is
  optional, not a prerequisite. The native Sites skill confirms this workflow.
- [Custom MCP connections](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt):
  direct developer-mode connections are not a demonstrated Plus/iPhone solution.
- [Creating/editing GPTs](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts):
  do not promise a new personal custom GPT/Action as the current solution.

Conditional simplest architecture: ChatGPT private Sites plugin -> authenticated
Sites gateway -> a single warm Linux Python container with private persistent
storage -> direct Krok API. GitHub holds code/tests and can deploy to the chosen
host; it is not the request executor. A Sites Worker cannot run the existing
NumPy/pandas/scikit-learn Python engines in its JavaScript/128 MB environment.
The bearer-only backend MCP endpoint is not claimed to be a standalone ChatGPT
OAuth installation. Native Sites identity and an owner-private audience must
protect the gateway; its backend token must remain a server secret.

No Site has been created or published. Sites native tools and skill references
are available, but the prescribed `site-workflow.mjs`/`project-setup.mjs` helpers
are absent from the execution filesystem; executor skill listing is empty and
cloud access to the helper resource failed. Do not bypass the prescribed
source/package workflow or claim a plugin connection exists. A supported Sites
publishing environment/helper bundle is needed for the read-only connection
probe. After publication, install/connect the auto-created Monty plugin under
Plugins -> Personal -> Created by you if not connected automatically. Then test
its tool from a fresh ordinary ChatGPT conversation on the actual iPhone.

No architecture is committed as production-ready before that probe. No host,
paid subscription, public data endpoint, credential transfer or new charges have
been introduced.

## Backend provisioning — minimum requirements, not user chat secrets

One existing always-on Linux Python/container host with HTTPS and durable private
storage is needed. None has been identified yet. No free tier is asserted to
provide guaranteed 24/7 availability. If a paid host is needed, obtain explicit
cost approval before creating it.

The host secret store must receive `KROK_API_KEY`, `MONTY_EXECUTE_TOKEN` and,
optionally, a different `MONTY_READ_TOKEN` (at least 32 random characters each).
The provider key is absent locally; GitHub Actions secrets cannot be read back
and must not be requested in chat. A future authorised deployment job can
provision the existing secret securely to a selected host. Never embed secrets
in source, images, arguments, public logs or client JavaScript.

Preserve all 55 original V6 manifest entries. Restore the existing originals
privately, using the unchanged manifest. Supply the untracked historical files
as read-only mounts or secure startup restoration; do not overlay original old
source over the repaired package. The container includes public code/model JSON
only and intentionally cannot pass full inference integrity until the private
original files are supplied. A failed missing-file check is not waived.

Build from a pushed, clean branch commit:

```
docker build --build-arg MONTY_SOURCE_COMMIT="$(git rev-parse HEAD)" -f runtime/Dockerfile -t monty-runtime:review .
```

Source provenance is checked against that exact public Git commit. V7 is checked
out at the original `efc51abb1595ef1eb8417e2d4e0d591f6d3c9378` commit. Run one
non-root replica, private state directory mode 0700, behind HTTPS. Do not expose
its unencrypted HTTP listener to the public Internet. Network/rate-limit rules,
volume backups, supervised restart, secret rotation, deployment/rollback and
external monitoring must be configured on the selected host before acceptance.
The app does not store or authorize wagers. Do not share the private Site.

The existing 08:10 Brisbane Actions schedule remains unchanged. Two active
workflows currently declare that morning time (`monty-operations.yml` and the
legacy `monty-auto-morning.yml`), so migration needs one designated schedule
owner and deduplication before enabling a replacement. This candidate does not
start a competing daily scheduler. No unattended schedule success has yet been
observed for the operations workflow.

## Acceptance required before saying operational

Run authenticated LIVE RM6, RM7, both PS commands/aliases and each model's
single-race request from ordinary ChatGPT. Retrieve two independent slips and
receipts for a paired request from the same capture. Confirm C issues zero
provider/inference calls, cache reuse, five-minute expiry/replacement, duplicate
coalescing, provider retry/rate limits and failed request disclosure. Repeat from
a fresh ChatGPT conversation and actual iPhone. Measure command-to-retrieval,
including client/tool latency. Demonstrate unattended morning execution and
restart/queue recovery. Distinguish controlled failure tests from live provider
failures. All gates remain open where evidence is missing.

Independent TAB field/conditions attestation, historical form completeness and
NZ meeting coverage remain data blockers. Current production outputs are NO BET;
this service must not weaken those gates. The existing horse-head M logo and
approved betting legend assets were not found in the repository; they remain a
presentation gap rather than an invitation to invent replacement branding.

See [evidence](EVIDENCE.md) for measured existing production runs and local tests.
