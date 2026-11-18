# Expert source intake registry — candidate sources, not connected feeds

Minimum 5 and maximum 20 independently authored expert evaluations per race. These are discovery targets; none is yet a validated machine-readable historical feed.

| Source | URL | Candidate content | Audit before use |
|---|---|---|---|
| Racenet | https://www.racenet.com.au/ | Named analyst tips | Publication timestamps, archive, permissions |
| Sky Racing | https://www.skyracing.com.au/ | Form Line expert panel | Video transcription reliability, original air time, panel independence |
| Punters | https://www.punters.com.au/ | Named tipsters and tips | Historical availability, licensing |
| TAB | https://www.tab.com.au/ | Editorial picks and market quotes | Separate odds from expert signals; provenance |
| Sportsbet | https://www.sportsbet.com.au/huddle/horse-racing/tips | Best Bets analysts | Identify actual author, syndicated content, timestamps |
| The Great Tip Off | https://thegreattipoff.com/ | Individual tipster rankings and tracked histories | Confirm timestamps, paid/free access and licensing |
| Racing.com | https://www.racing.com/ | Named form analysts | Archive access, publication times, duplication |

## Admission criteria

1. Source record must contain expert identity, source URL, race/runner identities, original publication time and capture time. Preserve revision history and only include versions published before race cutoff.
2. Count unique **independent analyst identities**, not websites. Syndicated or copied tips count once. Explicitly identify common editorial origin where known.
3. No inferred selections from odds, market moves, or vague prose. No post-race articles, unverified scraped tips, or fabricated timestamps.
4. For 5–20 eligible experts, compute consensus; otherwise mark feature unavailable and run independent baseline without pretending zero support.
5. Maintain per-source coverage, errors, freshness, permissions and historical strike rate, with weights trained only on prior races.
6. Compare V6, consensus-only and combined models on identical chronological AU/NZ test sets, and validate actual ROI with available pre-race quotes.

Status 18 November 2026: source candidates registered; no historical data collected or feed connected in this branch.
