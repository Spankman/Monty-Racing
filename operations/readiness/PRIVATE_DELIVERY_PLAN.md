# Minimal private delivery plan

26 November 2026. Proposed, not configured. Keep public source/Actions compute and the existing issue-based command interface; add one owner-private **derived-results** repository only after approval. No custom server, MCP service, private plugin or new paid platform.

## Recommended flow

1. Ordinary iPhone ChatGPT checks the matching latest request. Fresh matching results are reused; pending requests are followed. Otherwise it creates one owner-authored issue in the existing public repository. C performs only reads.
2. Existing Actions acquires one fresh shared snapshot and runs unchanged V6/V7. Raw provider/feature evidence stays encrypted under approved source policies; it is never copied into readable ticket files or public issue comments.
3. A narrowly scoped publisher sends only permitted derived forecast/ticket/receipt records to proposed private repo `Spankman/Monty-Racing-Private-Results`. Suggested paths preserve current conventions: `requests/N.json`, `daily/DATE/latest.json`, `runs/DATE/RUN/forecast.json`, per-model text/HTML and receipt files. Use immutable run paths and atomic index updates; conflict retries must not rescore or refetch. Never overwrite a completed forecast.
4. Public source repo receives acknowledgement, queue/execution/delivery status, capture/expiry and hashes only. It links the private record without leaking runners/odds in public comments, previews, artifacts or logs. Public and private forecasts need separate hashes/receipts: do not relabel a metadata envelope as the full forecast.
5. ChatGPT reads the exact private index and linked forecast/receipt through its authorised GitHub connector, checks run/scope/hash/freshness/jump, then displays two separately copyable tickets on a both-model request. Private publication failure means PRIVATE_DELIVERY_BLOCKED with preserved model execution—not NO BET, a manual assessment, stale fallback or duplicate run.

## Minimum authentication

- Existing source GITHUB_TOKEN handles source issues/public metadata; leave its routing intact.
- A distinct short-lived fine-grained credential has only Contents read/write on the single private sink, plus mandatory metadata read. It needs no source-repository administration, billing, organisation access or private-sink Actions permission. Install only after owner approval in GitHub’s secret UI. Use it only in the private-publish step; never replace the worker’s queue credential globally.
- Existing ChatGPT GitHub connector must be explicitly granted read access to that private repo. A token in Actions does not grant ChatGPT access. Demonstrate a harmless private sentinel read in a **fresh ordinary iPhone conversation** before real provider-data delivery; a workspace `gh` read is insufficient.
- No account/repo permission, secret, token or repository created in this task. Account permissions/secret creation cannot be assumed from current connector reads. The earlier secret-creation403 was not retried.

This is the smallest proposed route, but private publication routing is **not implemented by PR245**: `operations.transport.REPO` still targets the source repo, and the worker’s public directory/comment paths must be split before deployment. One reviewed routing/publish change after approval is required; no new model development. Do not merge245 expecting private delivery already to work.

## Retention / deletion and the Git-history condition

Raw provider inputs/features: existing policy cap1–7days, encrypted evidence upload and consumer expiry/deletion. Preserve permitted hash-only receipts. This policy does not authorise publicly accessible ciphertext when the provider disallows it.

Private derived forecasts/tickets: immutable historical records are useful for settlement. Use Git **only if the provider confirms personal archival rights covering quoted historical prices and Git history/backups**, as requested in the letters. Keep public receipts free of restricted detail. Five-minute validity still governs live display, regardless of archival retention permission.

Deleting a file in a later commit does not erase history, forks, clones or backups. Therefore do not promise hard7/30day plaintext deletion in a Git repository. If provider permission instead requires expiring price-bearing slips, this recommended Git-content design is blocked. Submit a revised private-artifact-only design with automatic expiry and separately reviewed authentication/cost; do not silently add it or claim ordinary Git deletion suffices. This conditional choice avoids building an unnecessary second system before provider clarification.

Owner/authorised consumers must delete recovered raw plaintext by deadline, revoke departing access, expire compromised credentials and test permission failure. Existing historical source archives are not deleted by this plan. Key rotation cannot revoke already-held ciphertext/private-key copies.

## Why not move all execution privately now?

Moving the existing five-minute schedule into a private repo would create up to288queue-start opportunities/day (8,640 per30days), before daily/issue work, and may exceed included private Actions minutes. It also needs provider/archive secret reconfiguration and queue routing changes. Keeping existing public standard-runner compute avoids that unnecessary migration/cost. Exact current GitHub plan/storage allowance is unverified; check it before activation and set spending prevention. No paid overage is authorised.
