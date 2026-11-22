# Operational integration acceptance evidence

Staging branch: integration/chatgpt-operations, based on the unmerged
fix/v6-daily-acceptance baseline. No production merge performed.

## Genuine live evidence (23 November 2026 Brisbane card)

### Shared daily capture, genuine V6 and V7

Workflow: https://github.com/Spankman/Monty-Racing/actions/runs/45079542429
Code commit: 0dd59b135d41ea14c9f45c6975c920d3de65f7bb
Result run ID: 45079542429-1-daily
Status: COMPLETED_NO_BET (workflow completed successfully).
Capture: 2026-11-22T22:46:36.899732+00:00 = 08:46:36 AEST, 23 November.

- Provider observed 3 Australian meetings / 15 races; no reliable NZ card found.
- 11 races accepted after four prohibited-class exclusions.
- Both models genuinely scored 5 races. Other common fields were blocked,
  chiefly because the whole field lacked named TAB fixed-win quotes or timing.
- Both received byte-identical timestamped per-race JSON, including all available
  normalized source features. No price-only projection was used in this run.
- Independent TAB field/conditions verification: zero. Official decision NO BET.
- V7 remains research-only. No wagers, fitting or research-pickle loading.

Connector-read result interface, ref `monty-operations-results`:
`daily/2026-11-23/latest.json` ->
`runs/2026-11-23/45079542429-1-daily/forecast.json`
and `receipt.json` in the same directory.

SHA-256 of exact connector-retrieved forecast bytes, recomputed locally:
`0d82caf3a2ed1565dc85c2df866f7a465e688e1681d8e7d0678d7ae59faafcd5`.
It matches the receipt. Official V6 and provisional V7 views were separately
retrieved through github_fetch_file. These are real live outputs, not CI fixtures.

### ChatGPT issue request and retrieval

The ChatGPT connector created owner request #100:
https://github.com/Spankman/Monty-Racing/issues/100
Title: Monty command: RM7PS; date 2026-11-23.

Workflow: https://github.com/Spankman/Monty-Racing/actions/runs/45079564800
Retrieved via connector: requests/100.json, ref monty-operations-results.
Status: COMPLETED_NO_BET; result run ID 45079564800-1-100.
Forecast SHA-256: b2fd584f52b043fbdf7b27e2c1380c0b468791b15cf635a0ff55be49c20df74e.

IMPORTANT: this is a demonstrated connector request -> staging worker ->
connector retrieval chain, but the worker was manually dispatched from the
Codex workspace. It does not prove automatic ordinary-chat triggering yet.

### Genuine single-race inference

Connector-created request #102: Monty command: RM7 Ballina 1, date 2026-11-23,
country AU. https://github.com/Spankman/Monty-Racing/issues/102
Workflow: https://github.com/Spankman/Monty-Racing/actions/runs/45079740604
Retrieved connector index: requests/102.json; forecast and receipt under
runs/2026-11-23/45079740604-1-102/.

Both versions genuinely scored exactly ONE race, Ballina R1. They remain
NO BET, with separately ordered probabilities. Shared model-input SHA-256:
f3ba664a68ae3e9914262ac37eef92b430a3d1963c8dcec6bbf76dac133d2464.
Forecast SHA-256: b34979b7b35c1f82ee0c7af26dc8b688054d73ed5d2cec62f2eed6b0bd4c3071.
No daily-card fallback or other-model substitution occurred.

### Genuine blocked request

Connector-created #101: RM6 Ballina 3, 2026-11-23 AU.
Workflow: https://github.com/Spankman/Monty-Racing/actions/runs/45079714321
Connector-retrieved index requests/101.json reports PARTIAL_OR_BLOCKED,
not successful inference. Both versions refused unqualified common inputs.
Forecast SHA-256: f3a05830322b70ea182265e895c57bf23bebc8da7f23ef664eb11a995fb046f4.

### Frozen artifacts

V6 unchanged model SHA-256:
f44e31f74ed017f915963950b17f144fbf6c994854403a39ba197fe5923d3fb7.
V7 unchanged model SHA-256:
c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324.
V7 code pinned to efc51abb1595ef1eb8417e2d4e0d591f6d3c9378.
All 55 original V6 manifest entries independently rechecked locally, zero drift.
The live runner validates the original complete manifest before inference.

## Offline/simulated evidence (not live inference)

29 focused tests pass locally: command/schema/transport contracts, existing
adapter parity, fixed-win progression, V6 daily receipts and ledger validation.
14 are new operational tests; inference in those tests is MOCKED. They cover
same snapshot bytes, stale/future/post-jump rejection, altered identity/price
rejection, missing country, missing named price, per-model failure with no
fallback, immutable outputs, owner-only strict-JSON queue, blocked raw publication,
failure receipts and escaped copyable/right-aligned ticket output.

Initial integration CI passed:
https://github.com/Spankman/Monty-Racing/actions/runs/45079542301
Subsequent final-revision CI is linked from the draft PR; check that exact head
rather than treating this older successful run as proof of a later commit.

An actual local invocation without KROK_API_KEY produced a FAILED receipt with
zero selections. No live provider request was claimed for that local test.
Stale snapshot tests advance the test clock and are SIMULATED, not a fresh live
feed test. Real failed/old-date request evidence is recorded separately if run.

## What is NOT demonstrated / remaining blockers

1. Unattended connector-only triggering: issue events and cron load from the
   default branch. The new workflow is unmerged; manual branch dispatch is still
   needed in staging. The initial attempt to dispatch an unregistered new workflow
   returned HTTP 404; a branch-only push trigger registered staging safely.
2. Hard 08:10 punctuality: Actions cron is best-effort. Exact-time guarantees need
   an authenticated external scheduler/watchdog; none was provisioned.
3. Complete independent AU/NZ verification and an approved betting-ready decision
   path: unavailable; NO BET remains correct. NZ coverage/validation not claimed.
4. New request issue-event handling and five-minute queue fallback are implemented
   and tested offline, but require default-branch activation to demonstrate the
   full ordinary-conversation service. Passing CI alone is not completion.

Minimum next action is review/approval of production activation, including the
existing V6 acceptance baseline and new workflow/code. Existing repository
secrets already enabled live staging; no new API key in chat, MCPBackend service,
external server or manual file transfer is required for the queued design.
