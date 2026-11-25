# Australian live provider reliability · 25 November 2026

**Decision:** Retain Krok for discovery and provisional inputs while testing replacements. The existing paid credential did not demonstrate reliable fresh fixed-WIN prices. Neither a downgrade nor a switch to another feed is supported. Production approval stays DATA BLOCKED.

## Same race and same bookmaker

Draft #229's 411 selected offers had zero verified fresh prices. The 340 safely timestamped prices (82.7%) were 385–4,832 seconds old. The other 71 were timestamp-unbound. A new read-only probe matched Launceston R6 TAB prices to the same nine provider-declared active runners. Routes were requested in parallel within each window. Race, saddlecloth and horse name had to match. This is a comparison within Krok without independent field or executable-price attestation.

| Route | Matched / fresh at 17:18:55 Brisbane | Matched / fresh at 17:20:15 Brisbane | Age at second check |
| --- | ---: | ---: | ---: |
| Meetings query | 9 / 0 | 9 / 0 | 2,188.6 s |
| Dated meetings alias | 9 / 0 | 9 / 0 | 2,188.6 s |
| TAB-filtered flucs | 9 / 0 | 9 / 0 | 494.4 s |
| Race-filtered odds history | 0 / 0 | 9 / 0 | 494.4 s |

All eight HTTP responses were 200. Flucs was 1,694.149 seconds newer than the board for all nine runners, with the same prices. Both board routes and flucs retained identical timestamps across the 79.780-second comparison interval. Odds history had no usable matched TAB vector in the first window, then matched flucs in the second. No endpoint passed the unchanged five-minute limit. Two samples do not establish long-run cadence, especially near jump.

The test identifies a lag in the served board relative to Krok's capture mirror. Krok documents flucs and odds history as views of a shared mirror. Neither independently verifies the other. Paid rate-limit headers were present. The cache floor alone does not account for the observed ages. The evidence cannot separate board caching/materialization, collector lag or bookmaker-side delays. Ask Krok for the board generation time, cache status, and upstream collection logs for the exact market. Treat quote observation, bookmaker update and response times separately.

[Workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45567127513) · [Archive](https://github.com/Spankman/Monty-Racing/actions/runs/45567127513/artifacts/14999999448) · [Same-race evidence](live_reliability_evidence/krok_same_race.json) · [Krok endpoints](https://krokodds.com.au/api-docs/racing)

## Cost and alternatives

| Source | Evidence | Decision |
| --- | --- | --- |
| Krok paid API | Board discovery works; quote age failed. Marketing and terms list A$49 and A$79.99/month respectively. Actual invoice unverified. | Retain for discovery pending replacement trial. No evidence an upgrade solves this. |
| Krok Free | A$0, 50 credits/month and 300-second documented cache floor. Separate Free credential absent. One one-page daily card costs 30–31 credits, two daily 60–62. | Trial separately; no downgrade justified on this evidence. |
| Krok mirror | Four measured five-credit calls. Four board costs unknown. One daily board plus one daily mirror request is about 180–186 credits/month. | Diagnostics only. No fresh fallback shown. |
| FormFav | No configured credential. Premium documents per-book capturedAt and stale, and distinct price movement times. Website amounts Free $0, Pro $10, Premium $50 monthly; invoice currency unverified. | Standard RM has no paid FormFav dependency. Prefer Free for optional form after checking personal paid uses. Do not upgrade on freshness claims. |
| PuntersEdge | No configured live credential. Prior open sample verifies retrospective prices, with incomplete and anomalous books. Free API advertised and paid plans from A$9/month. | First low-cost alternative to test against the same direct named bookmaker. No verified live replacement yet. |
| Direct operator | Public TABtouch page corroborates race context. No direct TAB vector at the probe times. Earlier VicBet/LetsBet reachable with no matched executable snapshot. | Preferred independent fixed-WIN evidence once permitted and verified. |

Use Racing Queensland for Queensland field, going and official results. An authorised direct single-book source remains the preferred price reference. Trial an authorised independent collector against it on the same AU field and price type. Preselect races across multiple days, including near jump. Report complete matched books, missing quotes, quote age distributions, same-price timestamp updates, failure rate, credits and licensing. No credential, billing or plan changes were made.

[Krok terms](https://krokodds.com.au/terms) · [Krok marketing](https://krokodds.com.au/api-access) · [FormFav price docs](https://formfav.com/docs/endpoints/prices) · [PuntersEdge open sample](https://github.com/Puntersedge-api/puntersedge-datasets)

## Racing Queensland declarations

Recaptured the exact Ipswich PDF from #229. Its SHA-256 is ea02ee81db1e8be5162d52a3bdf44b34b35ebc7c37f0798a6a2da840ea61f4ba. R7 HTML differed from the failed capture hash, and the original HTML was not published. Both old and new parsers accepted all seven races on the later captures. The original ValueError remains unreproduced.

Fixed a separate reproduced weakness: the old text search could select a later Scratchings label outside the race panel. The new parser selects race-local rows, requires explicit withdrawal or Nil evidence, and rejects duplicate, malformed and wrong-race entries. Failure stages distinguish PDF-link extraction, retrieval and declaration parsing. All seven published race declarations replayed, with 101 declarations and 29 withdrawals. R3, R5 and R7 reserves remained unresolved. The captures were post-jump and no pre-jump verification is implied.

[Replay and source hashes](live_reliability_evidence/rq_ipswich_replay.json)

Keep drafts #229 and #230 unmerged. No model, scoring, fresh-price threshold, release safeguard or betting rules changed. No deployment or wagering.
