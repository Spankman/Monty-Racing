# Owner-private ticket delivery — existing GitHub infrastructure

27 November2026. Canonical recovery: issue260 / PR262. No new hosting, plugin, MCP service, paid subscription, repository visibility/access change or API key is introduced.

## Demonstrated capability and exact missing authentication

Existing destination: `Spankman/Monty-Private-Archive`, private branch `monty-operational-private-results`. The archive/default branch is unchanged. Owner-only collaborator review returned1collaborator, Spankman. The native ChatGPT GitHub connector read an actual non-sensitive receipt from that branch, so private connector access is demonstrated in this conversation. Probe commit `f918cce04da4b11be3127934205c74c1b0f0a723`; file SHA-256 `8ec85c287ff1c3043246cf950a472a3687c63dac0a5ddf58c576bcf1b5712471`. This is a transport probe, not a live selection or an iPhone test.

Hosted [probe45924499300](https://github.com/Spankman/Monty-Racing/actions/runs/45924499300), source `fb5a0eba0eba9e2763526427df4f57960a7af9da`, used the existing archive credential. Semantic result: **PRIVATE_TRANSPORT_BLOCKED, HTTP404** before target access was confirmed. A green reporting job does not mean the write passed. Secret-list access also returned403; secret creation was previously denied403. No secret or permission write/retry was attempted. Workspace/connector access is distinct from hosted Actions authentication.

**Minimum owner action:** create a fine-grained GitHub token restricted to the existing private repository, Contents read/write and Metadata read; store it as `MONTY_PRIVATE_RESULTS_TOKEN` in Spankman/Monty-Racing → Settings → Secrets and variables → Actions. Use GitHub's UI; never send the token in chat. No administration, billing, workflow or organisation permission is requested. Preserve `V6_ARCHIVE_TOKEN`; do not replace the working model-restore secret. Choose an expiry/rotation date and renew through the same UI before expiry. A missing/expired token must give a delivery failure, not model NO BET.

No repeated approval for PuntersEdge provider choice is needed. The writer credential and final production activation remain separate from that already-approved choice.

## Licence scope: resolve personal tickets separately from raw retention

Reviewed [PuntersEdge terms](https://puntersedge.online/terms), last updated25Nov2026, SHA-256 `0933f504bd267d2e4309dc0a6eb36ef1c84614143b66927aebd499ac5618a2c9`, unchanged on27Nov. Section3.4 expressly covers AI-assisted API use;8.1 permits own betting decisions, own models/research/backtesting and dashboards the owner looks at;8.4 permits previously obtained data to continue under the original permitted purpose and distinguishes own derived works from feed redistribution.

This narrow route serves only the owner in an authenticated private repository/conversation. It does not publish prices to other people, offer a feed/export/API to customers, assume grandfathered/commercial rights, or grant public display. The private bundle contains derived forecasts and attributed prices, not original HTTP responses, historical datasets, original/transformed feature matrices or contribution traces. Recursive stripping is tested. Full raw research retention and its recovery-key/processor questions remain separate; their unanswered scope need not silently turn a personal derived ticket into predictive NO BET.

Earlier blanket “private delivery/licensing unclear” notes are superseded **only for this documented personal derived-ticket scope**. Public derived-price display remains disabled. The repository must stay private and owner-only; adding other consumers needs a fresh licence/access review. Git history is not guaranteed deletion or independently enforced WORM. Do not promise that deleting a path erases earlier commits. No raw feed archival policy is enabled by this integration.

## Staged implementation

`operations.private_delivery` builds existing V6 official/provisional, V7 shadow/provisional and deduplicated combined assessment text/HTML. It retains no raw feature matrices or provider responses; prices are explicitly retained inside the owner-private derived outputs. Each immutable run path has a receipt binding exact file SHA-256 values, provider snapshot hash, model pins, capture/expiry and licence reference. An atomic Git tree/ref update publishes all files and the private latest index together. Conflicting reruns are rejected; identical retries preserve the original rendered snapshots.

`operations.evidence.store.public_result` invokes that publisher only when the dedicated private credential is configured, the source is live PuntersEdge and the destination is private. Public outputs remain metadata-only and include the private receipt pointer/hash on success. Failed private publication preserves model execution and returns an explicit private delivery blocker. Existing raw-retention gates remain intact.

The public issue terminal comment contains no runner prices. `C` returns request/model state, capture age, original offer age, per-race valid-until and receipt location; it never submits an issue, invokes inference or acquires provider data. Reuse remains tied to provider/model/scope/freshness. Failed V7 may not be replaced by V6. A missing requested race may not be replaced by other fresh races. Private race deadlines include original poll+300seconds, capture+300seconds and the existing pre-jump freeze. A recent HTTP acquisition does not reset an offer clock.

Combined **assessments** remain explicitly provisional/research, deduplicating matching runners while preserving one model's exotic legs and source labels. They are not the qualified daily betting ticket. The qualified ticket cannot manufacture bets while the independent authority/operator/history/value gates remain unmet. No thresholds or model weights change.

## Ordinary ChatGPT invocation after activation

Commands remain RM6, RM7, RM6PS/RMV6PS, RM7PS/RMV7PS, their meeting/race variants, shorthand meeting/race and read-only C. Existing public issue ingress remains the command queue; no second private request queue is introduced.

1. Submit the existing command issue through the native connector; retain its exact request ID.
2. Read its public terminal index/receipt. Pending stays pending; failed, data blocked, NO BET and delivery failure stay distinct.
3. If `PRIVATE_RESULTS_AVAILABLE`, follow `private_delivery.repository`, its commit/ref and exact receipt path using the native GitHub connector. Verify the referenced forecast/view hashes where computation is available; do not claim a cryptographic check that was not performed.
4. Read only the requested private view/forecast. Recheck Brisbane date, requested model/track/race, original poll timestamps, each expiry and jump before displaying. Filter expired races from structured forecasts; a stored text/HTML view is a timestamped snapshot, not a live freshness certificate. C reads the outstanding request and does not start a replacement; a fresh RM command may request one through the existing client.
If a reliable current clock or hash computation is unavailable in a new conversation, report freshness or integrity as UNVERIFIED; do not pretend the check passed. Actual ordinary iPhone access still requires acceptance.

5. Preserve the existing white/black/gold mobile layout, model ordering, saddlecloth/name/bookmaker win prices, legend, $4 progression and research/provisional labels. Generate no image unless requested.

## Acceptance remaining

After the owner configures the writer credential: prove hosted private write, submit actual command requests, verify terminal private receipts and retrieve fresh slips through the native connector. Then obtain final activation approval and run the owner's ordinary iPhone acceptance. Existing projection tests and the harmless connector marker are not substitutes. Provider freshness/identity gaps and official qualification evidence remain separate blockers; do not advertise the service as fully operational now.

### Ready-to-run authentication gate

The final live workflow now tests the dedicated writer **before** any provider acquisition. Missing authentication or denied private write produces a failing acceptance step and a hash-bound preflight artifact; it consumes zero provider credits. Provider/data CI is separate from this live authentication gate. After the owner configures the secret, the assistant can push `operations/recovery/private-live-control.json` on the same staging branch to run the existing bounded workflow; no workflow dispatch or manual user artifact transfer is needed. The separate diagnostic control is `operations/recovery/private-transport-probe.json`. Neither path is a new production request queue. Current ordinary command issues still require final production activation; no staged projection is claimed as that acceptance.
