# Monty multivariable feature specification

Observed history means only earlier retained Australian Betfair races, never a fabricated complete career. Horse identity requires selection ID and normalised name; current rider/trainer strings are normalised, and unknown placeholders are excluded from connections history. All same-day results are withheld until the next local date.

| Requested factor | Implementation | Data status for this experiment |
|---|---|---|
| Weight | Allocated weight, effective weight after known claim, change from previous observed weight | No verified historical values in matched source; inactive, never inferred |
| Going | Good/soft/heavy/firm/synthetic categories and horse's earlier performance on current category | Historical TAB-derived meeting condition available; exact per-race publication history absent |
| Distance | Metres, 400m bands, horse's distance and track-distance residuals, rise/drop from last start | Available |
| Gear | First blinkers, blinkers off, first tongue tie, first winkers | Verified timestamped overlay supported; no historical values recovered in this experiment |
| Gelding | Existing status separate from first run after reported gelding | Both unknown without explicit dated evidence; neither inferred from horse name or present-day sex |
| Trainer | Prior 90/365-day performance relative to market, change of trainer | Matched historical trainer names available; history coverage starts 2025 |
| Jockey | Prior 90/365-day performance, change of jockey | Matched historical rider names available; NOT NOTIFIED is missing |
| Jockey/trainer | Prior combined performance with sample-size shrinkage | Available on matched history |
| Horse/jockey | Prior combination performance | Available on matched history |
| Recent form | Last three/five observed win outcomes and performance relative to prior odds | Available; does not pretend to know unreported finishing positions |
| Longer form | All observed and trailing 365-day starts, wins and residual performance | Available from 2020 source coverage, incomplete horse histories |
| Barrier | Draw, draw relative to retained field size, inner/outer draw, interaction with distance | Available; original stall number is retained and can exceed field size after scratches |
| Track | Horse's prior track and track-distance record | Available |
| Class | Numeric benchmark and change where comparable BM labels exist | Other class labels remain unknown; Group/maiden/BM categories are not forced into invented equivalence |
| Fitness | Days since observed run, 60-day resumption, seven-day backup | Available; missing observed races limit fitness interpretation |
| Age/sex | Age and gelding flag | Supported in verified overlay; no recovered values |
| Pace/sectionals | Requires prior-run sectionals, running style and verified pace inputs | Not recovered; not included or claimed |

Rates use fixed shrinkage and prior market expectation to avoid promoting a jockey/trainer from a few easy favourite wins. A nonlinear candidate can learn interactions among the available numeric features; it is compared with a market-offset linear model and the market itself. No fixed folklore bonus is assigned for blinkers, gelding or dropping in weight.

## Supplying verified missing fields

Optional `verified_overlay.csv` must contain `date,track,race,horse,source_url,published_at,scheduled_start_utc` plus any available columns:

`allocated_weight,claim_kg,age,is_gelding,first_after_gelding,blinkers_first,blinkers_off,tongue_tie_first,winkers_first`.

Every source publication timestamp must be parseable, in or convertible to UTC, and no later than scheduled start. Exact race/runner identity is required; duplicate identities are rejected. Dates and times must come from evidence, not a timestamp fabricated to pass validation. An empty value remains unknown; a zero gear flag means an explicit verified absence. Claimed kilograms are not subtracted twice: supply allocated pre-claim weight and the known claim separately. The timestamp checks cannot themselves prove a source's accuracy or that an event flag is true; sources still require review. No example row containing invented race inputs is loaded into training.

## Timing and evaluation limits

Current static trainer/rider/barrier/going values were reconstructed from a public historical TAB-derived result compilation, with incomplete field-publication provenance. A condition recorded at meeting end can differ from the condition before an earlier race. This is therefore exploratory feature research, not a verified point-in-time live backtest. All 2025 diagnostic dates were already exposed in V5; no new unseen-performance or profitability claim is permitted. Previously scored September–October 2026 is not opened or reused here.
