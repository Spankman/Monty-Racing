# Sandown 18 November 2026 — first complete analyst-to-V6 comparison

Source: David Gately, The Great Tip Off, https://thegreattipoff.com/news/david-gately-horse-racing-tips-for-sandown-181126 .
Frozen V6 inputs: user's archived `Monty_2026-11-18_Connections_Run.zip`, `rankings.csv` (captured TAB fixed odds 17 Nov 2026, 18:24–18:29 QLD). No model was retrained; these are research-only predictions. Gately's complete eight-race top-ranked card is compared against archived V6 ranking; no results or outcomes used.

| Race | Gately #1 | V6 rank | V6 win probability | archived fixed win odds | V6 #1 |
|---|---|---:|---:|---:|---|
| 1 | #5 La La Lilly | 1 | 0.319504 | 2.60 | La La Lilly |
| 2 | #2 Royal Maximus | 1 | 0.405205 | 1.95 | Royal Maximus |
| 3 | #7 Sound Byte | 3 | 0.211915 | 4.20 | Oceans Blue |
| 4 | #2 Certainly Quiet | 4 | 0.156670 | 5.00 | Pariah Pearl |
| 5 | #4 Mickidabeel | 1 | 0.251035 | 3.20 | Mickidabeel |
| 6 | #6 Torn | 5 | 0.098671 | 8.00 | Flying Mikki |
| 7 | #4 Onavuitton | 2 | 0.177548 | 4.40 | Russian Choice |
| 8 | #1 Maisy | 3 | 0.164124 | 4.80 | Befuddle |

Agreement on top-ranked runner: 3/8. The other five analyst selections remain in V6 top five. This is descriptive, not proof of predictive improvement. In R6, Torn's V6 expected win return at $8 is `0.098670683 * 8 - 1 = -0.210635`, approximately -21.1%. In R2, Royal Maximus at $1.95 is also negative edge: `0.405205358 * 1.95 - 1 = -0.209850`. No recommendation to bet follows from analyst agreement alone.

**Source-audit status:** The Gately page is attributable to a named author and published for the 18 Nov card. Exact timezone-aware publication timestamp is not established from the article, so do not invent one or admit this into the strict timestamp-gated `source_audit.py` as a validated vote. The original model has incomplete feature coverage and the archived odds are not live. Some early published rankings include subsequently scratched horses; user handles final scratching checks.

**Next evaluation:** Capture original publication time with timezone, ingest each independently authored ranked card into a provenance registry, and test added information via chronological out-of-sample log loss and betting ROI. Never combine untrained vote shares into model probabilities.
