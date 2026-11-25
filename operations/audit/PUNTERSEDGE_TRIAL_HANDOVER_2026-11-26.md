# PuntersEdge live acceptance — 26 November 2026, Brisbane

**Status: staged trial established; six-day acceptance NOT complete.**
Draft [#235](https://github.com/Spankman/Monty-Racing/pull/235), branch
`trial/puntersedge-acceptance-20261126`, builds on draft #231 at
`0df55dccd230b69bba8e0be5f8d8ef9462f5c388`.
Production remains `623d46b449e46cfc5fa63b633c3f19b404bba41a`.
No merge/deployment, provider migration, purchase/subscription change or wagering.

## Completed genuine hosted check

[Planning run45677174261](https://github.com/Spankman/Monty-Racing/actions/runs/45677174261)
tested `e4062513d1ae3c41a21d562feed76d80e06bfd44`. `/v1/usage` authenticated
HTTP200. Account: **Free1500credits/month,30requests/minute**. Used67→86;
remaining1433→**1414**. Actual account delta19 agrees with paid endpoint headers:
board4, three meeting acceptances6, three race forms9. Usage calls had no cost
header; the original meter summary therefore reports unknown totals rather than
invented free credits. A subsequent reporting fix includes the final usage call
in the summary; the original receipt is preserved unchanged.

Planning: marker requested18:38:07UTC, Actions created18:38:13, job
started18:38:16, acquisition started18:38:37 and finished18:38:46.
Measured provider latencies: usage0.557–0.587s, board1.562s,
acceptances0.911–0.996s, form0.867–1.008s. Those are planning measurements,
**not** measured timed-capture/model/ChatGPT delivery performance.

Artifact [15051902190](https://github.com/Spankman/Monty-Racing/actions/runs/45677174261/artifacts/15051902190):
188987bytes; GitHub ZIP SHA-256
`c32ffc8f0ed2325b799fd411368d5a69cd94b1fd0c622fac93cf6dcb00df48b1`.
Aggregate receipt SHA-256
`fcd170f5f79c282b2df6506b10adfcdd957436fd966c93f3c95dec2d3a6b97dd`.
Encrypted evidence SHA-256
`7d76a0db7ad19bb030b65a29dc07e28300aefa51a3fe652df3bd678d6c073c92`.
Verified artifact SHA, ZIP CRC, receipt and ciphertext hashes, authenticated CMS
decryption and recovery of all7private files using the new recovery script.
Only aggregates/hashes/registration metadata are public. See
[original receipt](pe_trial_20261126/INITIAL_receipt.json).

## Actual preregistration

Preregistered04:38:39Brisbane, committed immutably at
`f12dde8b1d810a4027c29635087627a3dea4fb1d`.
Plan SHA-256 `0a130677908ca5d97fc939cd0ecaf2c999e84b95ad773fed61f24e588f0f691c`.
Protocol SHA-256 `16aeb128fe8ce5f9656702937942887994569a244ca4de4f1a67fbee0f0527c3`.
These are actual provider identities, not invented future cards:

|Race26Nov|PE race ID|Jump Brisbane|Four capture times Brisbane|
|---|---|---|---|
|HawkesburyR3,NSW provincial|5047da2a-a572-4c37-b0cc-6373327b8df2|14:00|13:00,13:45,13:55,13:58|
|RockhamptonR2,QLD provincial|88486ae8-7602-4651-8025-8d4fd7521b2a|14:20|13:20,14:05,14:15,14:18|
|GeraldtonR3,WA country|bfd65896-c8d5-4db5-9e90-ade1eb45070a|16:34|15:34,16:19,16:29,16:32|

Target18slots over26Nov–1Dec, minimum12complete races. **Only today's3actual
races are registered now.** Future cards have a rolling horizon and must be
registered before their first observation. Saturday selection rules prefer
Queensland and other-state metropolitan venues; weekdays/country/Queensland/
other-state coverage is checked cumulatively. An advertised meeting is not a
verified field or guaranteed future successful capture. No outcome-based
replacement, delayed backfill or invented coverage.

## Automation implemented

One enabled finite ChatGPT task combines08:30planning,11:30staging launch and
19:30daily reports (Brisbane), ending with a2Dec08:30read-only final catch-up.
This fits the account's5active-task limit; unrelated tasks were not changed.
Configuration was confirmed by the automation tool. Actual future unattended
execution/environment access remains **untested/pending**, not a production cron
acceptance claim. Its environment selection is inherited, with no confirmed
environment detail in the returned configuration; report missing workspace/auth
honestly if encountered.

Staging marker pushes trigger existing GitHub-hosted infrastructure; native
ChatGPT GitHub tools have demonstrably retrieved the completed artifact. This
is not a claim that the native read-only connector can dispatch workflows.
No default-branch schedule/merge is needed for the trial. Each capture step
uploads a separately immutable encrypted artifact immediately, enabling an
external GitHub creation timestamp check before jump. Invalid late windows and
rescheduled races remain visible. Duplicate phase requests return
ALREADY_LAUNCHED without another provider call; this was genuinely checked for
today's planning phase. C/production request handling is unchanged.

## Data and independent evidence

Recovered22runner forms with208prior-run candidate rows, all dated before26Nov;
zero same-day/future rows in this sample. No lifetime registration crosswalk or
original residual reconstruction was established. `form_as_at` equalled future
scheduled race times; the trial flags this and does not treat it as observation
or availability proof. No features were inserted, reconstructed speculatively,
retrained or activated.

A new **pretrial** RockhamptonR2 primary-source acquisition succeeded:
RQ HTML1.316s and PDF0.326s, both HTTP200. Existing parser rejects the absent
scratching section. This is an exact verification blocker, not a model NO BET.
TAB-first direct page also returnedHTTP200 in0.758s, but is app-shell HTML with
**zero runner/fixed-odds data markers**. HTTP200 is not direct price verification.
No challenge/TLS/login bypass was attempted. Unsupported authority venues,
final emergencies, direct full-book executable prices and collector independence
remain unresolved. These documents are not fresh betting evidence at the later
capture times. [Preflight evidence](pe_trial_20261126/PUBLIC_SOURCE_PREFLIGHT.json).

The existing strict `operations.prospective` admission/settlement gates remain
unchanged. Genuine V6/V7/market forecasts will be frozen privately before jump,
with diagnostic records excluded if independent operator/history attestation
is missing. Forecasts that fail admission cannot later be promoted using results.
Provider results alone do not settle them. **Current new-trial model executions0,
required timed observations0, admitted forecasts0, settlements0.** Prior genuine
V6/V7 evidence in #231 is retained, not presented as this trial's achievement.

## Budget, security and migration

Expected no-retry trial usage51PEcredits/day (306/six days); hard phase caps
24plan+32capture+6results=62/day,372/six days,500credit operational reserve.
First actual19credits consumed as above. This is not a measured national monthly
service bill. PE Free suffices for the proposed bounded trial based on the
verified allowance; no paid plan recommended yet. Krok comparison is limited to
14requests/day with1000credit reserve; if remaining quota is absent after the
first probe, subsequent comparisons stop. Actual Krok consumption is pending.
Krok subscription expiry is unknown; neither quota reset nor PE reset proves it.
No promise that replacement can be approved before an unverified expiry.

Raw licensed evidence uses AES-256-GCM CMS encryption. The public certificate is
tracked; private key remains mode0600 outside Git. Creating an Actions secret
was deniedHTTP403 by this connection and **not retried**. Secure durable owner
key custody remains necessary before this workspace is lost; currently no
independent key backup is claimed. Encrypted artifacts have90-day retention.
No provider secret was printed or published. Standard public-repository Ubuntu
Actions introduces no paid hosting/runner; no billing arrangement changed.

Migration and rollback procedure: [trial README](../trial/README.md).
Keep PE staging and Krok's approved configuration until evidence and explicit
owner migration approval. If a future approved PE config must be rolled back,
restore the prior provider config only while credentials/licence/freshness are
valid; otherwise DATA BLOCKED. Preserve every forecast/receipt. Present trial
rollback is simply disabling its task/stopping its staged jobs; production is
already unchanged.

## Validation and remaining acceptance

Local:16trial contract/security/timing tests; existing182operational tests
(198including16trial tests),158runner tests,13frozen tests/replay. All55V6artifact
hashes match; replay17987runners/1787races maxprobability difference
1.6653345369377348e-16; refitted=false. V7 pin remains
`efc51abb1595ef1eb8417e2d4e0d591f6d3c9378`, model SHA
`c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324`.
V6 frozen-model SHA
`f44e31f74ed017f915963950b17f144fbf6c994854403a39ba197fe5923d3fb7`;
manifest SHA
`99485842dc4d120f9c6f930889d42a6a317cfe9b6db2c6b5799a3e1063948c20`.
Exact final tested commit and GitHub CI links are recorded in draft235's body
once that head's checks finish; do not substitute an earlier green run.

Priority register: [REGISTER.md](../trial/REGISTER.md).
Outstanding: actual unattended captures and all strata/minimum12; independent
operator/source verification; missing authority adapters/scratching status;
original compatible history; admitted prospective settlement/performance;
Krok expiry; durable private key custody; owner-reviewed final migration/costs.
No owner intervention is needed to manually initiate each scheduled capture.
If future automation environment/credentials fail, report the precise failure
rather than claiming unattended execution. No full operational/provider
acceptance until the genuine six-day evidence exists.

IN MONTY WE TRUST.
