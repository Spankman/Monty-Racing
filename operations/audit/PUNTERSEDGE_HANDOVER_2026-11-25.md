# PuntersEdge staged integration — copyable handover

**Draft PR #231; no merge, deployment, automatic provider switch, billing change,
model refit, new threshold, V7 promotion or wager.** Branch
`integration/puntersedge-staging`, based on #230 at
`5c96fe36e9714cd1fcd27fb8d345a95b00c94472`, retaining the preceding draft stack.
Production remains unchanged. Final exact-head CI references are in the PR.

## Authentication, entitlement and licence

The configured `PUNTERSEDGE_API_KEY` authenticated successfully in Actions.
`/v1/usage` reports **Free, 1,500 credits/month**; live headers report **30 requests
per minute**. The observed reset is 1 December 2026 UTC. No key, account email,
billing URL, raw provider response or betslip link is exported. Free is personal
use; raw payloads and inference inputs stay private. Reports contain aggregate
measurements and hashes, not redistributable odds feeds.

The public schema registers **98 paths / 112 operations**. The endpoint register,
published cost table and plan-feature matrix are retained under
`operations/audit/puntersedge_evidence/`. They distinguish documentation from
authenticated tests: **nine distinct GET endpoints returned 200 on this Free
credential** across the probes: usage, next-to-go, events, acceptances, form,
markets, track-conditions, changes and results. No claim that every documented
route was authenticated. Account, key, billing and mutation routes were excluded.

Documented Free includes live racing odds, events, recent results and form;
events have a 24-hour forward horizon and price history has a recent window.
Older price archives, historical sports odds, exports, live streams and commercial
display/redistribution have separate restrictions. Do not infer entitlement from
schema presence. **Published markets-view restrictions conflict with an observed
Free HTTP 200**: it is described as Plus/legacy Standard, yet the first probe was
served for two credits. That route is not relied on or re-requested. Clarify
the discrepancy with the provider before depending on it; no other restricted
routes were explored. No upgrade or signup was attempted.

Sources: [schema](https://api.puntersedge.online/openapi.json),
[pricing](https://puntersedge.online/api/pricing),
[licence](https://puntersedge.online/terms),
[freshness semantics](https://puntersedge.online/developers/freshness).

## Actual Australian data and historical form

The sampled rolling card contained **35 confirmed AU thoroughbred races across
six venues**, with zero unresolved countries. Its venues included next-day cards:
Albany, Geraldton, Hawkesbury, Launceston, Mornington and Rockhampton. This is a
24-hour priced horizon, **not 35 races on 25 November or verified national TAB
coverage**. Events also returned 35 records. Requests retain unresolved-country
records for disclosure; the scoring adapter refuses to guess their country.

The Launceston acceptance response contained eight races / 75 declared runners,
nine withdrawals and three emergencies across the meeting. Launceston R6's live
and acceptance vectors matched by saddlecloth, normalized name and scratching
status: ten declarations, nine active, one scratching, no target-race emergency.
These are two views served by one provider, not independent verification. The
authority-derived acceptance snapshot was approximately two hours old.

Field-form returned ten runners with history and **99 past-run rows**. It reports
Racing Australia/TABtouch-derived form coverage from 28 May 2025. Provider horse
references are folded-name identifiers and RA runner references identify entries,
not a national lifetime horse identity. No name-only historical crosswalk is
accepted. The 55-row mapping records available fields, candidate context and
remaining original-definition gaps. Historical win/market residuals, original
scheduled-off full-field probabilities, complete chronological windows and
registered identities remain unverified. Form summaries, SP, closing odds and
provider ratings are not inserted as replacement features. Frozen imputation is
preserved; no historical feature activation or refit.

Results sampling returned **35 races: 31 final / four interim**, with **355 runner
rows** and five unavailable/null runner lists. The null lists exposed a bug in the
first reporting probe, now fixed and regression-tested; the original evidence is
retained with its TypeError. A successful results response is not a full finishing
order or independently verified official settlement. No forecast was settled. The final sample advanced to 33 final / two interim
results, still 35 races / 355 runner rows / five unavailable runner lists.

## Matched market and clock comparison

Target: **Launceston R6, 25 November 2026, scheduled 09:57 UTC**. Same date, AU
country, thoroughbred code, venue, race number and jump time were required before
matching number, horse name and bookmaker. Requests overlapped within each
window; upstream observations could not be forced to identical instants.

The second live run sampled 70 matched runner/book offers in each window, with
61 agreeing prices. At 08:05:24 UTC, PuntersEdge's matched poll times were
3.43–235.17 seconds old (70/70 within five minutes); Krok's were
1,004.57–4,897.40 seconds old (0/70). At 08:06:44 UTC PuntersEdge had 63/70
within five minutes, while Krok still had none. The paired age ranges did not
overlap: no identical upstream observation-time comparison was established.
The final validation additionally normalizes PointsBet's AU alias and UTC clock
formats; do not silently compare differently named bookmaker identities. At 08:12:37
UTC it matched 81 offers, 72 equal prices, with 72/81 PuntersEdge observations
within 300s versus 0/81 Krok. At 08:13:51 it matched 72 offers, all 72 prices
equal, with 63/72 fresh PuntersEdge observations versus 0/72 Krok. Matched
coverage changed, so the two windows are not a fixed 81-offer panel. No exact
observation instants matched. TAB and Sportsbet remained complete and fresh.

`age_basis=poll` was present on all 99 PuntersEdge offers in that target race.
Across a window exceeding the documented Free 65-second board cache, **72 offers
kept identical prices while their poll timestamps advanced**. That supports
observation-clock semantics rather than price-change semantics. It does not prove
an operator accepted a wager or establish independent upstream collection.
`push_receipt` and unknown time bases remain timestamp-unverified in the adapter;
no upstream sender delay is guessed. The `/markets.observed_at` clock is documented
as newest price change and is never substituted for per-offer poll time.

Reported integer ages differed from the end-of-window absolute calculation by up
to 3.54 / 8.15 seconds in the second run, which includes request/processing time.
The guard uses the absolute quote timestamp at decision/retrieval, not a frozen
age counter. **Monty's 300-second limit remains unchanged**, including on provider
`card` tiers that permit much older prices. Other-book freshness varied; no blanket
claim that the entire provider panel was fresh is made.

TAB and Sportsbet each supplied all nine active target runners. Independently
recomputed book totals were **129.928001%** and **128.722616%**, respectively.
Both are overround; no normalization-created underround value was manufactured.
Both remained quarantined because independent field/operator evidence and the
existing approval prerequisites were incomplete.

## Direct evidence and collection independence

TAB was checked first using the exact race-page link: HTTP 500. Sportsbet's exact
race link returned HTTP 403. Neither produced a verified contemporaneous direct
price vector. No CAPTCHA, TLS, redirect or access restriction was bypassed.
The comparison cannot claim an independently executable book.

PuntersEdge documents its own polls and the measured cadence differs from Krok's
served board. Nevertheless, price agreement, different timestamps, API brands and
collector claims cannot exclude shared upstream data or Krok materialization lag.
**Independence from Krok remains unestablished.** RA-derived fields/forms from both
providers also do not provide independent authority collection merely by being
served twice. A permitted direct same-book sample and provider-confirmed
collector/upstream lineage are still required for corroboration.

## Implemented adapter and genuine frozen-engine test

`puntersedge_adapter.Client` supports only bounded GET data routes, API-key headers,
no redirects, limited transient retries, timeouts, per-request metering and a
staging credit budget. It refuses C, billing/key operations and other unsupported
routes. Raw responses are not logged. Requested race counts determine a
conservative credit reservation; actual headers remain the measurement.

`canonical_race` stages **one explicit named fixed-WIN book** into the existing
snapshot/feature builder. It rejects unresolved country, wrong date/code,
duplicate identities, conflicting scratchings, missing book prices and explicit
closed/in-play status. No cross-book stitching, tipster substitution, exotic-price
input or new model feature definition. Only `poll`-based absolute timestamps bind
to the selected offer. Optional acceptance reconciliation does not grant
independent verification or betting permission.

The second genuine live run at
`759999de9766ab1361b54391b85e06bc4e117afe` executed **both frozen engines** on the
same PuntersEdge TAB field. V6: SCORED / PROVISIONAL. V7: SCORED / RESEARCH ONLY.
Both betting decisions: DATA BLOCKED. This demonstrates staged input compatibility,
not production approval, automatic failover or ordinary ChatGPT activation.

[Second live workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45573196626).
Forecast SHA-256:
`55553f7866aed49b45f0bffd42fb5959cc17b987ea0122c07214d198e4c2a821`
Receipt SHA-256:
`0978488109dce4b56c4269ab24fabc4070dcdfcb6324b6d8a318184fc60e2176`
Aggregate ZIP SHA-256, independently checked:
`bcbbf53aff1bd43d050598e9ae84c5f8e572d0952adcf2c7cb9d0734c3c0699e`.
Raw inference records were not published under the personal-use data licence;
their hashes are runtime receipts, not a claim of independent forecast-byte replay.

Invocation for a secure staging caller: construct `Client()` from the existing
environment secret, request `/v1/racing/next-to-go` with `categories=horse`,
`country=AU`, `include_unresolved=true`, venue and a bounded `num_races`; select the
exact race ID/date/jump; call `canonical_race(..., day=..., book='tab')`; pass that
private payload to the existing runner. Never expose source payloads or credentials.
No production RM/C command routing was changed. Primary/fallback suitability is a
conditional recommendation for provisional research, **not an activated switch**.

## Consumption and monthly scenarios

First probe: 25 billed credits reported. Second probe: **23 billed credits**;
`credits_used` rose **25 → 48**, exactly matching second-run nonzero cost headers.
The usage endpoint is documented free but omits a cost header; per-request header
summaries retain that unknown rather than inventing it. The usage-period counter
reconciles the measured charged requests. Remaining allowance after the second
run: 1,452 credits. The final run added **19 credits**, matching its header sum
and counter **48 → 67**, leaving **1,433**. All three runs together reported
**67 charged PuntersEdge credits**, consistent with the initial zero counter.
The six Krok comparisons reported four known credits and two missing costs;
their total remains unknown. Krok calls are metered separately and missing Krok cost headers
are not silently counted as zero.

Measured charges: `num_races=200` next-to-go 4 per call (even for one selected
venue), events 1, acceptances 2, field-form 3, markets 2 on the initial granted
request, conditions 1, changes 2, results 2. Usage has no measured nonzero charge.
Final adapter requests use `num_races=20` for a targeted meeting instead of 200;
the final live run confirmed **two credits** for each targeted 20-race request. Documentation prices 21–60 at three. Do not fan out one
form request per horse where one field-form request serves the race.

| Assumed personal usage over 31 days | Estimated credits |
| --- | ---: |
| One 200-race bulk capture/day | 124 |
| Bulk plus ten fresh 20-race single-meeting calls/day, at 2 each | 744 |
| Same pattern with the tested 200-race request shape at 4 each | 1,364 |
| Add daily field-form and results to that 1,364-credit pattern | 1,519: exceeds Free |
| One two-credit poll every minute for ten hours/day | 37,200: exceeds Free |

These are explicitly assumed workloads, not a month-long trial. Fresh reuse can
reduce requests; missing/expired data must never be reused to fit an allowance.
Current Free API price is **A$0**; no purchase or plan change occurred. Bounded
personal on-demand usage can fit 1,500 credits; continuous monitoring cannot.
Successful coverage/freshness still needs a multi-day sample, including near jump.

## Tests, limitations and recommendation

The regression suite includes transport secrecy, forbidden routes, budget bounds,
retry limits, exact single-book mapping, original feature arithmetic, poll versus
push/price-change times, expiry, closure/in-play checks, field conflicts, null
results and cross-provider UTC/book aliases. Local results: **182 operational contracts, 158 runner checks and 13 frozen
V6 tests passed** (overlapping suites; do not sum). Exact final CI is recorded
in the draft PR. All 55 original V6 hashes and the 17,987-runner /
1,787-race historical replay remain intact, max difference
1.6653345369377348e-16, no refit. V7 remains pinned and research-only.

Recommend PuntersEdge as the **leading staged candidate for provisional single-
race inputs** and a possible later primary/fallback source. Do not activate an
automatic switch or authorize bets yet. Still outstanding: independently permitted
direct prices, collector lineage, fresh primary authority checks, full original
historical feature compatibility, broader daily/near-jump reliability, and complete
official settlement. The Free markets-view documentation mismatch needs clarification.

Keep all PRs draft and unmerged. Existing betting rules, five-minute freshness,
market quarantine, Smart Betting Tickets and official/research roles remain.

IN MONTY WE TRUST.

## Final live validation receipt

[Run 45574218049](https://github.com/Spankman/Monty-Racing/actions/runs/45574218049),
runtime head `85dc10b1dc9b42049e2a83da65322bc708f31c20`. Both engines again
SCORED on one explicit TAB book, V6 PROVISIONAL / V7 RESEARCH ONLY, both betting
DATA BLOCKED. This final phase exercised the alias/UTC fixes, explicit closure
rejection and lower-cost targeted request shape. No source failover was activated.

Forecast SHA-256:
`05c3cd765b079d5feb96113f3d4d843c8e925752edd6e132fc08e59f79b4b287`
Receipt SHA-256:
`9acc04453cdc3da18ca7eb39f52a4073fff9faf7cb6bc792c3474d2d0f6e77bd`
Aggregate artifact 15003810515 ZIP SHA-256, independently checked:
`9e477e7444b646741b866168a6b5805a8309c761ba006fc05f7b7459718c9555`.

See `VALIDATED_LIVE_PROBE.json`, retaining the earlier `INITIAL_LIVE_PROBE.json`
and second-run `FINAL_LIVE_PROBE.json` unchanged. No raw quotes were published.
