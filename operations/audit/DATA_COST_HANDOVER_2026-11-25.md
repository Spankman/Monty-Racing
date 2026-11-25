# Data integration and cost optimisation — handover

Draft branch `integration/data-cost-controls`, stacked on #228 at
`bb76198a0eeed5d4c6e1d221fe1bbf1787d3ce93`, retaining preceding draft repairs,
market safeguards and reports. No merge, deployment, subscription/billing change,
model refit, threshold change, expert blend or V7 promotion.

## Implemented and tested

- Exact selected-offer binding for nested `odds[].captured_at` / `capturedAt`.
  The first valid TAB offer remains the adapter's selected price; another
  bookmaker, later duplicate offer, runner update or best-win timestamp cannot
  supply its time. Fixed-win fallback uses explicit field-bound time or a unique
  exact price/book match. Ambiguous matches stay unknown.
- Capture times are labelled provider observations, distinct from bookmaker
  updates and independent execution proof. Explicit timezone required; no UTC
  invented for naive strings. Different observation/update semantics are not
  treated as duplicate fields. Existing age and market quarantine rules remain.
- Per-attempt endpoint/command credit meter, including retries/errors. Missing
  cost headers mean UNKNOWN, not zero. Partial known costs are not presented as
  a complete total; account balance changes are not attributed to Monty.
- Documented dated-card alias support and country/venue filters, retaining strict
  pagination/completeness checks. Routine tests avoid five-credit per-race form
  enrichment and unrelated provider predictions/tips.
- Thread-coalesced in-process `CaptureBatch`: one acquisition can serve command
  views or repeated single races only when original capture AND selected offer
  ages remain below 300 seconds. Missing/expired offer times force acquisition;
  C is rejected by the acquisition interface. No persistent/shared raw live HTTP
  cache was introduced for `no-store` responses, and no freshness window extended.
  This batching is staged and tested, not deployed into the production queue.
- Append-only private `HistoryStore`: content-addressed source revisions,
  integrity checks, deduplicated data blobs, immutable observations and optional
  conditional headers only when a source permits them. Frozen directories are
  rejected. Source-specific network adapters retain permission/host controls.
- Primary RQ acquisition for the initial Ipswich cohort, sharing one PDF across
  requested races within a batch. Authority facts cannot verify bookmaker odds.
  The new live attempt fetched HTML/PDF successfully but declaration parsing
  rejected the documents; it did not grant verification.
- Source-lineage contract requires evidence of separate collectors AND upstreams.
  Distinct API brands, matching prices or two endpoints from Krok are insufficient.
  Caller evidence must still be authenticated; the helper is not source proof.

## Genuine live measurement

[Run 45565320852](https://github.com/Spankman/Monty-Racing/actions/runs/45565320852),
runtime commit `14f35c8aeda8dafffaa20b581f2c00c40f9d79c7`, PR-open staging event.
No production request or manually dispatched workflow. Existing Actions secrets
only; no local credentials. Job success is not market verification success.

Both `/api/v1/racing/meetings?date=...&country=AU` and
`/api/v1/racing/meetings/2026-11-25?country=AU` returned **six meetings, 44 races,
411 active runners, one page**, with matching race identities/active counts.
Venues: Albany, Geelong, Ipswich, Launceston, Strathalbyn and Wyong. This is Krok
coverage, not an independent national TAB completeness claim. NZ was outside
this AU pilot. The dated route is a documented alias, not another collector or
a proven cheaper endpoint. No undocumented `/racing/card` endpoint was guessed.

There were **11,209 nested captured_at fields** across active-runner offers.
**340/411 selected prices** had a safely bound timestamp; none failed ISO parsing.
All 340 were stale at retrieval: **385.174–4,831.508 seconds old**. The other 71
selected prices remained timestamp-unbound. This validates extraction and reveals
a freshness failure; it does not validate bookmaker clocks or executable offers.
No safeguards were relaxed to turn these captures into qualified selections.

| Actual request | Time, seconds | Reported credit cost |
| --- | ---: | --- |
| Meetings, initial shared AU acquisition | 2.755 | 1 |
| Dated-card alias comparison | 1.781 | UNKNOWN: cost header absent |
| RM6 acquisition refresh | 1.771 | UNKNOWN: cost header absent |
| RM7 acquisition refresh | 3.932 | UNKNOWN: cost header absent |

**One known credit; three unmeasured attempts; total UNKNOWN.** Published pricing
would estimate four credits if each request were charged one, but that is not a
measured debit. Only the initial response supplied credit/rate headers, indicating
50,000 monthly credits and 500 requests/minute, consistent with paid API access.
The three subsequent responses cannot be claimed free merely because their cost
headers were absent. This metering limitation needs provider clarification or a
per-request usage export before exact total consumption can be established.

Real command-acquisition trial: RM6 and RM7 each refreshed because reuse failed
freshness. RM6PS, RM7PS and three repeated single-race acquisitions stopped at
the explicit trial network budget. They were NOT completed inference commands,
provider failures, or model NO BET results. No live cache saving was demonstrated.
Offline tests separately demonstrate reuse of genuinely fresh synthetic offers.

The dedicated Free credential, FormFav credential and PuntersEdge credential were
all absent from the staging environment. Therefore no authenticated Free-plan
comparison or FormFav/PuntersEdge live integration was completed. Existing paid
access to Free-labelled routes does not prove a Free account's reliability.

## Live-race pilot and receipts

Both frozen models genuinely scored **Strathalbyn R6** before its scheduled
07:10 UTC jump, using one shared capture at **07:05:12.945861 UTC**. V6 outcome:
PROVISIONAL; V7: RESEARCH ONLY. Market warnings: independent field unverified and
stale prices. Betting remained DATA BLOCKED / NO BET; no cohort admission or
settlement. This is an attempted AU pilot, **not independently verified success**.

No Queensland pre-jump cohort remained available after Ipswich's last jump.
RQ Ipswich R7 HTML and field PDF each returned HTTP 200; declaration parsing
returned ValueError. Do not label that source pair a verified field, resolved
emergency or current pre-race attestation. Original bytes were not published.

Artifact 15000270778 ZIP SHA-256:
`35fa7f0748ff370ff1787aa67eeadeadc93d8456f3c6b21452c93ea963717d82`

Forecast SHA-256:
`ae0cf6338a5099d5f4a79b653e84b5c3c5000eec22a27a6267aacf49d6a02f33`

Receipt SHA-256:
`cb0a1db2e69d7d0c074402c070b0d807c6b1ee553b8174ed03b809875a0a48ba`

ZIP, forecast and receipt bytes were independently rehashed. Derived evidence:
[DATA_COST_LIVE_EVIDENCE_2026-11-25.json](DATA_COST_LIVE_EVIDENCE_2026-11-25.json).

## Historical recovery and optional free sources

Rechecked and indexed the 16 existing hash-pinned Betfair months into the private
append-only store: **22,499 races / 216,366 runners**. Repeat ingestion produced
no duplicate data blobs and made zero network calls. May/July 2026 remain excluded
under their original pins. This is verified reuse/indexing, not newly recovered
starts or a completed historical feature reconstruction. Zero new live features
entered scoring. Prior RQ horse/profile crosswalk research is retained, not
silently converted into a registered Krok identity or complete residual window.
[History index evidence](DATA_COST_HISTORY_INDEX_2026-11-25.json).

FormFav's documented Free form is a useful optional contextual source, while
live odds and results have different entitlements. Existing bounded client/probe
paths are retained; no credential means no authenticated coverage assertion.
PuntersEdge's documented Free allowance is 1,500 monthly credits for newer keys;
the existing pinned CC BY 4.0 sample audit remains historical evidence, not live
price independence. No signup, verification email, new subscription or billing
endpoint was invoked. Provider-generated selections remain outside both engines.

## Cost estimates — conditional, not invoices

Krok Free publishes 50 credits/month, five requests/minute and a 300-second
server-cache floor. Free-labelled endpoints still consume credits. At one credit
per one-page capture:

| Usage scenario | 31-day estimate | Free allowance |
| --- | ---: | --- |
| One shared capture/day | 31 credits | 19 remain, freshness unproven |
| Two fresh captures/day | 62 | Exceeds 50 |
| Daily capture + 10 post-expiry single requests/day | 341 | Exceeds 50 |
| Eight racing days/month, five captures each | 40 | Conditional fit |
| Daily card + five-credit form enrichment/day | 186 | Exceeds 50 |

Multiply by actual pages and billable retries; request timing, not command name,
determines reuse. Never retain expired prices to fit a quota. C makes no provider
acquisition and does not refresh data. These are arithmetic estimates, not a
month-long Free trial. Real fresh-cache savings were zero in this stale sample.

Potential external-data spend: **A$0/month** only if entitled Free sources meet
actual usage, licence and freshness needs. Existing paid Krok cost is not verified
from an invoice: marketing lists A$49, terms list A$79.99, and terms defer to the
current API Access price. Budget estimates must not be treated as current billing.
No change to the existing plan is recommended from this sample. No paid FormFav
or PuntersEdge purchase is proposed. Public authority data has no measured API
credit charge here, but publication/reuse conditions still apply.

## Tests, blockers and next steps

169 operational tests, 155 runner checks and 13 frozen V6 tests passed locally
(overlapping suites; do not sum). Historical replay remains 17,987 runners /
1,787 races, max difference 1.6653345369377348e-16, all 55 hashes verified,
`refitted=false`. Exact final head/CI links are recorded in draft PR #229.

1. Obtain a permitted fresh price source or provider explanation of observed
   offer ages. Both endpoints returned stale selected quotes; refreshing alone
   did not fix that. Keep quarantine and the five-minute rule.
2. Resolve missing per-response credit headers; total debit remains unknown.
3. Diagnose the newly rejected RQ declaration format with private source bytes,
   resolve final emergencies and complete a pre-jump Queensland cohort.
4. Establish genuinely independent operator lineage and compatible as-of history.
5. To test actual Free accounts, an owner-configured Free credential in Actions
   is required. Use secrets, never chat. Optional FormFav/PuntersEdge keys likewise
   require owner-controlled setup; do not downgrade or purchase on this evidence.
6. Run a prospective multi-session Free trial once fresh entitled data exists.
   Freshness failures and budget stops must remain separate from model NO BET.

Keep every PR draft and unmerged. V6 official; V7 research-only. Existing Smart
Betting Tickets, $4 progression, roughie rules and market quarantine are preserved.
No full operational or independently verified pilot acceptance is claimed.

IN MONTY WE TRUST.
