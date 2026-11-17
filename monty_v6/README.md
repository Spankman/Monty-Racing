# Maintenance update: V6.1

The pipeline has been modularised and automatic integrity/schema checks added. See MAINTENANCE.md. Research predictions and conclusions are unchanged. Exact runtime pins are retained. The repaired pack includes all V5 dependencies; no separate V5 download is needed.

# Monty 6.0 multivariable research

Run `python run_multivariable.py` with Python 3.11+, numpy, pandas, scipy and scikit-learn. Run safeguards with `python -m unittest discover -s monty_v6 -p 'test_*.py'` from the package parent.

This adds 44 observed historical feature definitions and 11 explicitly missing/overlay-supported definitions. See FEATURES.md for actual coverage and interpretation, rather than assuming every field influenced the fitted model.

## Files needed for reproduction

Keep the included `monty_v5/run_research.py` beside this `monty_v6` directory. From the previously saved `Monty_v5_Data_Code_and_Results.zip`, place `monty_v5/results/cleaned_eligible_runners.csv.gz` in that relative location. All additional 2025 static metadata and the recovered April source CSV are included here. This avoids duplicating the large V5 source table. No remote service or credentials are needed to rerun the saved experiment.

Source static metadata: https://github.com/xx36Mostafa/horse-racing-ml-pipeline , author Mostafa Nasser. Downloaded `racing-data.csv` SHA-256 is in source_join_audit.json. Betfair original sources are listed in the earlier data-discovery pack and in this pack's April recovery manifest.

## Model and limits

Outcome labels come exclusively from the cleaned Betfair sample, not from the supplementary source's incomplete finishing positions. Supplementary static fields are exact-joined by date, normalised venue, race and horse name, then checked for matching distance. Conflicting static records are excluded; no fuzzy guesswork. Only whole races with complete matched supplied-runner fields and a consistent going category enter the new experiment.

Training uses January–March 2025, model selection April, diagnostic May–15 June. All dates were already exposed in earlier development; this is feature exploration, not a fresh holdout. September–October 2026 was not scored again. Earlier 2020–2024 data supply outcome history. Trainer/jockey/going history begins only where supplementary fields are available, mostly 2025. Missing historical starts do not imply no previous career starts.

Static historical fields are reconstructed from result records rather than timestamped field snapshots. Going can represent a final meeting rating, and jockeys can be late replacements. This prevents a certified pre-race performance claim. Results are assumed available on the next local date, since exact publication timestamps are missing. All same-day outcomes are withheld; no future jockey/trainer strike rate is looked up or substituted.

April 2025 source times use AM/PM formatting. V5 conservatively excluded these unreadable clocks; this run recovers 1,447 eligible races using a parser that handles both 12- and 24-hour formats. The original V5 outputs are preserved. Unknown historical distances are skipped in distance-band histories and never treated as zero-distance races.

Models compared: market baseline; three regularised linear market-offset models; one fixed histogram gradient boosting classifier blended 10%/25% with the market. Scaling and imputation use training rows only. Unknown data retain explicit missing flags. Features with no training observations or no variance are excluded, so weights and gear do not acquire invented coefficients. Median imputation is a model operation, not a claim that the source supplied the value.

Historical quote returns are illustrative: one unit per top pick at scheduled-start displayed back price, 5% commission on winning profit, no sizes/latency/reduction-factor history. Zero actual bets. Winner-among-top-four is not four-finisher prediction accuracy. Uncertainty intervals do not account for all data provenance or model-selection uncertainty.

Optional verified_overlay.csv is described in FEATURES.md. Gear parsing in gear.py detects explicit change events; it does not infer first-after-gelding from a horse being described as a gelding. Tests include this distinction, timestamp rejection and same-day/future-result protection.

No current tips, automated job, betting action or publication has been configured by this work. The saved boosting pickle is a locally generated research artifact, not the selected production model. The frozen coefficients, scaler and exact chosen method are in results/frozen_model.json.
