# Single-race fallback evidence

Runtime tested live: `d100f06ae7b37b0eba276e2ca752d6e39c4bfd9a`.
Production base: PR #134 merge `4a26075fed02e89cbdd75738175c1dcff1bd9b86`.
This change remains on a separate branch until approved. No production merge.

## Genuine live staging

https://github.com/Spankman/Monty-Racing/actions/runs/45110799775

The existing Actions workflow ran RM6 Ballina 7 on push, using the existing
securely configured Krok/archival secrets. No manual dispatch, hosting, custom
MCP, retraining or new subscription. Results are isolated on
`monty-single-staging-results`.

Capture: 2026-11-23T04:16:34.897356+00:00.
Valid until: 2026-11-23T04:21:34.897356+00:00.
Both frozen models genuinely SCORED the same six-active-runner field, with
PROVISIONAL rankings and different model probabilities. Price provenance was
`fixed_win` for every active runner, with no named TAB attribution. The former
single-race gate would have blocked that provenance. Official NO BET remains
unchanged. Both models' existing $4 ladder returned TRIFECTA BOXED as a
provisional assessment, never a wager approval. Neither identified a supported
value candidate; none was fabricated.

The native ChatGPT connector retrieved the index, exact forecast/receipt, and
separate V6/V7 provisional views while fresh and before the recorded jump.
Exact retrieved forecast and receipt SHA-256 values were independently checked
against the unchanged published index. No independent TAB field verification
is claimed. These are historical test records, not current betting slips.

Forecast SHA-256:
`c5daac32a5ce4e40273fe403fafd49ff973ab7f29e4be937b9c77382ccb1055e`

Receipt-file SHA-256:
`032e47612bf5f6286cbd39cbf53a46045dbfa3c85fd24981c9a684d3c3dad491`

[Machine-readable evidence](SINGLE_FALLBACK_LIVE_EVIDENCE.json).

## Offline tests — explicitly not live acceptance

108 relevant tests passed, including 15 new fallback contracts. They cover:
complete unattributed quotes; partial/no prices without imputation; known field
retention; uncertain scratchings; conflicting identity; V6 two-runner scoring
without bypassing V7's minimum; V7 consistent-provenance enforcement; per-model
failure without substitution; timing research handoff; closed/stale suppression;
most-likely versus value; unknown-price rendering; and unchanged integrity gates.
Existing full-day, input-feature parity, $4 progression, ledger, adapter, scoring
and historical replay checks pass. The earlier regression test that required
single and full-day quote gates to be identical now explicitly checks their
user-requested separation, while preserving identical valid input features.

A separate smoke test ran the real V6 and pinned V7 engines on synthetic inputs,
with `source_mode=SIMULATED FIXTURE`. Both scored using their original frozen
preprocessing. Those synthetic probabilities are NOT live forecasts or form
assessments and are not presented as selections.

55 original V6 manifest hashes verified. Historical replay: 17,987 runners,
1,787 races, maximum probability difference `1.6653345369377348e-16`, refitted=false.
Frozen JSON artifacts, coefficients, preprocessing, original historical records
and the original manifest were not changed; no research pickle was loaded.

## What FORM ASSESSMENT means

A missing market price cannot be silently replaced: both frozen models require
whole-field market probabilities. The workflow publishes a factual, explicitly
non-model research handoff instead of inventing probabilities or dropping the
unpriced horse. ChatGPT then independently researches the exact race with tools
actually available, cites current sources and provides supported rankings,
best/value separation and unknown-price labels without an extra command.

A handoff is not itself a completed independent assessment. The live staging
race did not need this tier; missing-price handoffs were verified with controlled
offline inputs. No live public-form research outcome is claimed here. If no
reliable comparative information is accessible, ChatGPT must disclose that and
withhold unsupported selections. Technical failures stay FAILED; independent
research never conceals them or becomes a purported Monty prediction.

No frozen input contract is bypassed. V7 still needs three active runners and
consistent quote provenance. Where V6 can score and V7 cannot, V7 receives its
own independent-form handoff, not V6 probabilities. Full-day gates, official
betting requirements, freshness/post-jump checks and the $4 progression are
preserved. Only single-race ranking availability changes.
