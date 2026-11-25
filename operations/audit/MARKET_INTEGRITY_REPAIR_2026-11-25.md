# Market integrity repair — copyable handover

**Draft only. No deployment, production merge, retraining or betting-rule change.**

Branch: `fix/market-integrity`, stacked on Work's draft #225 at
`5b2ee240c9a3a4e1cb3cfe0a4cc4d1f25d39e007`, which contains draft #213 at
`4a3068c07b3608174a8e647381c38abc6af045b5`. Both reviewed heads were fetched,
and their reports and prior repairs are retained. The review reproduced the two
incident books and compared every saved watch's uplift with #225's runner CSV.
It does not claim to have independently repeated every historical ROI arm in
the roughie audit. No historical research policy is activated.

## Confirmed problem

The archived 25 November production forecast contains underround price vectors.
For full-field decimal prices `o`, book `S = sum(1/o)`. Normalized market
probability is `(1/o)/S`, so its same-price edge is `1/S - 1` for every runner.
Positive numerical edge can therefore arise without any positive model uplift.
It does not establish a simultaneous executable offer, independent predictive
value or a qualified wager.

| Archived race | Recovered active prices | Book % | Signed overround pp | Market-only numerical edge |
| --- | ---: | ---: | ---: | ---: |
| Geelong R8 | 10/10 | 95.9241594571 | -4.0758405429 | +4.2490239852% |
| Launceston R6 | 9/9 | 72.7464215966 | -27.2535784034 | +37.4638061986% |

These full vectors reconcile to the archive's internal active counts, not an
independently verified authority field. Per-offer timestamps and affirmative
simultaneous availability were not preserved. The race-level TAB attribution
does not prove a coherent executable book, but there is also no affirmative
evidence proving that these particular books mixed bookmakers. Neither stale
quotes nor missing external runners can be conclusively diagnosed retrospectively.

## Repairs

- `operations/market_integrity.py`: calculates full book percentage, signed
  overround, positive underround and observed lower bound for incomplete books.
  No normalization is supplied for incomplete/conflicting vectors.
- Flags missing/invalid prices, missing/duplicate/conflicting active identities,
  declared-count inconsistencies, unknown scratchings, unknown/mixed bookmakers,
  absent/invalid/stale/future quote times, quote-after-capture anomalies and
  inconsistent timestamps. Different update times can be legitimate; they remain
  unverified rather than being called proof of bad data. The existing 300-second
  boundary applies; no invented synchronization tolerance or book-percentage cap.
- Extracts times only from the exact already-selected quote. It does not borrow
  another offer's time, a runner's unrelated update time, a better-win time for
  fixed-win odds, or capture time. Missing times remain unknown. The public
  `quoted_at` field is no longer populated with capture time; `quote_capture_at`
  records acquisition separately. Old immutable forecasts are never rewritten.
- Separates each saved model probability from normalized market probability,
  probability uplift and edge contribution. Exact decomposition:
  `raw edge = market-only normalization edge + (model p - market p) * odds`.
  A positive model contribution is explicitly **not validated predictive value**.
- Attaches full-field market-only distributions to both model views where the
  whole price vector exists. Missing archived V7 probabilities stay missing.
- Quarantines anomalous/unverified books from actionable value. No bare provider
  flag or caller boolean releases quarantine or authorizes betting. Independent
  same-race field/scratching and executable named-bookmaker quote evidence, plus
  the existing outstanding approval evaluator, remain necessary. No permanent
  underround exclusion or roughie quota is introduced.
- Preserves every original roughie watch with NO BET, market warnings and
  arithmetic attribution. Preserves model rankings and the $4 progression;
  single-race value candidates remain diagnostic, never authorized wagers.
- `monty_operations.py`: adds market evidence after real inference, without
  changing shared model input bytes. Rechecks ages during retrieval. Legacy
  archives receive derived annotations on copies. Malformed fields retain their
  pre-existing DATA BLOCKED outcome, rather than becoming technical failures.
- `operations/render.py` / `operations/delivery.py`: retain warnings and
  decomposition in white/black/gold HTML, mobile copyable text and compact views.
  Existing ordering, bold best runner, right-aligned prices, standalone watches,
  slogans and presentation are preserved. No image generation or new acronym.
- `operations/prospective.py`: new immutable records retain the market audit.
  Research comparison admission is separate from betting authorization.

## Authentic incident evidence

Original run: `45551033605-1-221`, used by requests #221–224.
[Original workflow](https://github.com/Spankman/Monty-Racing/actions/runs/45551033605).
Both original forecast and receipt were retrieved and independently SHA-256
verified before exact two-race extraction into
`testdata/market_integrity_2026-11-25.json`.

Forecast SHA-256:
`3dd8547fdaab7dafa70e45907e6f8c52a8e7d7114753e7f3a36dc89580abc8fe`

Receipt SHA-256:
`925f4bc02ac1049980907dc432a29d5cca9eb16300339b8c0369d81c788d4e30`

The replay is evaluated at the original capture plus 30 seconds, solely to test
historical display behaviour. **It is not new inference, current odds, live
acceptance or a current selection slip.** No new provider calls or workflows
were dispatched, no production requests were created, and no results were invented.

| Archived command replay | Watches retained across both incident races | Classification / approval |
| --- | ---: | --- |
| RM6 | 14 V6 | Diagnostic PROVISIONAL / DATA BLOCKED, NO BET |
| RM6PS | 14 V6 | PROVISIONAL / DATA BLOCKED, NO BET |
| RM7 | 7 V7 | RESEARCH ONLY / DATA BLOCKED, NO BET |
| RM7PS | 7 V7 | Provisional research view / DATA BLOCKED, NO BET |

At $10 or longer, counts remain Geelong V6 5 / V7 0 and Launceston V6 7 / V7 2.
No model threshold or runner quota changed. All views preserve warnings in text,
HTML and compact delivery; expiry suppresses watches. C and the existing issue
queue are unchanged and do not submit inference through this repair.

Machine-readable arithmetic and command replay evidence:
[MARKET_INTEGRITY_REPLAY_2026-11-25.json](MARKET_INTEGRITY_REPLAY_2026-11-25.json).

## Validation and limits

Local suites: 151 operational contracts (including eight new market tests),
155 existing runner checks, and 13 frozen V6 checks passed. The suites overlap;
these counts must not be summed as distinct tests. New tests cover exact incident
books, comparison to Work's saved uplifts, additive decomposition, incomplete
vectors, mixed operators, selected-offer timestamp binding, stale/future/missing
quote times, all four command projections, repeated rendering, compact warning
retention and expiration. CI includes `test_market_integrity`; final exact head
and workflow conclusions are recorded in the draft PR and handover.

All 55 original V6 artifact hashes verify. Historical replay: 17,987 runners /
1,787 races, maximum probability difference 1.6653345369377348e-16; no refit.
Frozen V6/V7 files, coefficients, preprocessing and original records are unchanged.

Remaining blockers: absent incident raw quotes/times and independently matched
authority fields prevent retrospective executable-price validation. Existing
Actions-side bookmaker access, compatible historical features, horse identity
resolution and the missing production approval evaluator remain outside this
targeted repair. No new live end-to-end inference acceptance is claimed.

Recommendation: review and retain the stacked draft. Obtain contemporaneous
authority and direct named-bookmaker evidence, verify a complete pre-race book,
and freeze paired model/market forecasts before settlement. Do not activate
quotas, new probability floors, new uplift thresholds or expert blending without
out-of-sample evidence and owner approval. Keep V6 official and V7 research-only.
No production change is recommended merely because CI is green.

Rollback now requires no production action: leave the drafts unmerged. Any future
approved deployment should revert only these wrapper changes through review,
preserving immutable result refs and model manifests.

IN MONTY WE TRUST.
