"""Offline AU research on the original verified archive. Emits aggregates only."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.optimize import minimize
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import HistGradientBoostingClassifier

from operations.audit.roughies_240 import digest, join_places, place_labels, softmax
from operations.audit.price_policy_study import DayBootstrap, fixed_predictors

FEATURES = (
    "distance_km", "log_field_size", "barrier_fraction", "barrier_x_distance",
    "observed_starts_log", "observed_win_rate", "last3_win_rate", "last5_win_rate",
    "days_since_run_log", "resuming_60d", "quick_backup_7d", "distance_change_km",
    "benchmark_class", "benchmark_class_change", "jockey_changed", "trainer_changed",
)
FOLDS = (
    ("2025-02-15", "2025-03-01", "2025-03-31"),
    ("2025-03-15", "2025-04-01", "2025-04-30"),
    ("2025-04-15", "2025-05-01", "2025-05-31"),
    ("2025-05-15", "2025-06-01", "2025-06-15"),
)
BANDS = ((10, 20), (20, 40), (40, 60), (60, np.inf))


INTENT_FEATURES = (
    "last_start_won", "last_start_beaten_favourite", "last_win_x_up_in_trip",
    "last_win_x_class_change", "last_win_x_log_recency", "jockey_prior_starts_log",
    "jockey_prior_win_rate", "trainer_prior_starts_log", "trainer_prior_win_rate",
)


def prior_roles(data, raw):
    """Populate from the archived identity proxy, strictly before the current date."""
    if not data.date.is_monotonic_increasing:
        raise ValueError("History must be sorted by date")
    previous = {}
    jockey = defaultdict(lambda: [0, 0])
    trainer = defaultdict(lambda: [0, 0])
    out = np.full((len(data), len(INTENT_FEATURES)), np.nan)
    trip, cls, recency = (FEATURES.index(n) for n in (
        "distance_change_km", "benchmark_class_change", "days_since_run_log"))
    for _, day in data.groupby("date", sort=False):
        updates = []
        for race, field in day.groupby("WIN_MARKET_ID", sort=False):
            prices = field.BEST_AVAIL_BACK_AT_SCHEDULED_OFF
            favourite = None if prices.eq(prices.min()).sum() != 1 else prices.idxmin()
            for row in field.itertuples():
                i = row.Index
                key = (row.SELECTION_ID, row.name_key)
                if key in previous:
                    won, beaten = previous[key]
                    out[i, :5] = (won, beaten, won*(raw[i, trip] >= .2)
                        if np.isfinite(raw[i, trip]) else np.nan,
                        won*raw[i, cls], won*raw[i, recency])
                for offset, table, role in ((5, jockey, row.jockey), (7, trainer, row.trainer)):
                    if isinstance(role, str) and role:
                        n, wins = table[role]
                        if n:
                            out[i, offset:offset+2] = (np.log1p(n), (wins + 2)/(n + 20))
                updates.append((key, row.jockey, row.trainer, row.y,
                                float(i == favourite and not row.y) if favourite is not None else np.nan))
        # Same-day repeat horse keys leave the last start ambiguous.
        repeated = pd.Series([key for key, *_ in updates]).duplicated(keep=False)
        for is_repeated, (key, j, t, won, beaten) in zip(repeated, updates):
            if is_repeated:
                previous.pop(key, None)
            else:
                previous[key] = (won, beaten)
            for table, role in ((jockey, j), (trainer, t)):
                if isinstance(role, str) and role:
                    table[role][0] += 1
                    table[role][1] += won
    return out


def design(raw, train):
    # Fit scale and imputation on the fit period only. Keep missingness explicit.
    filled = np.zeros(raw.shape[1])
    for col, values in enumerate(raw[train].T):
        finite = values[np.isfinite(values)]
        if len(finite):
            filled[col] = np.median(finite)
    missing = ~np.isfinite(raw)
    x = np.where(missing, filled, raw)
    scale = x[train].std(axis=0)
    return np.column_stack(((x - filled) / np.where(scale > 0, scale, 1), missing))


def fit_logits(x, y, race, penalty, initial=None, bounds=None):
    def objective(w):
        p = softmax(x @ w, race)
        loss = -np.log(np.clip(p[y], 1e-300, 1)).mean()
        gradient = x.T @ (p-y) / y.sum()
        return loss + penalty * (w @ w)/2, gradient + penalty*w

    w = np.zeros(x.shape[1]) if initial is None else initial
    result = minimize(objective, w, jac=True, bounds=bounds, method="L-BFGS-B",
                      options={"maxiter": 500, "ftol": 1e-11})
    if not result.success:
        raise RuntimeError(result.message)
    return result.x


def harville_place(p, race, slots):
    """Sequential fractional renormalization, evaluated only on known 2/3 slots."""
    out = np.full(len(p), np.nan)
    for group in pd.Series(np.arange(len(p))).groupby(race, sort=False).indices.values():
        if not np.isin(slots[group[0]], (2, 3)):
            continue
        v = p[group]
        second = v[:, None] * v[None, :] / np.maximum(1-v[:, None], 1e-15)
        np.fill_diagonal(second, 0)
        out[group] = v + second.sum(axis=0)
        if slots[group[0]] == 3:
            third_base = second / np.maximum(1-v[:, None]-v[None, :], 1e-15)
            out[group] += v * (third_base.sum()-third_base.sum(axis=0)-third_base.sum(axis=1))
    return out


def metrics(data, predictions):
    y = data.y.to_numpy().astype(bool)
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    settled_place = data.PLACE_RESULT.isin(["WINNER", "LOSER"]).to_numpy()
    place = data.PLACE_RESULT.eq("WINNER").to_numpy()
    race = data.WIN_MARKET_ID.to_numpy()
    grouped = pd.Series(np.arange(len(data))).groupby(race)
    counts = pd.Series(place).groupby(race).transform("sum").to_numpy()
    complete = pd.Series(settled_place).groupby(race).transform("all").to_numpy()
    slots = np.where(complete, counts, 0)
    grouped_date = DayBootstrap(data.date)
    market = predictions["market"]
    gross = 1 + .95*(odds-1)
    returns = y*gross-1
    book = pd.Series(1/odds).groupby(race).transform("sum").to_numpy()
    result = {}

    def band_stats(mask, p):
        n = int(mask.sum())
        if not n:
            return {"n": 0}
        paid = np.sort(gross[mask & y])
        place_known = mask & settled_place
        return dict(n=n, wins=int(y[mask].sum()), win_strike=float(y[mask].mean()),
                    place_labels=int(place_known.sum()),
                    place_strike=float(place[place_known].mean()) if place_known.any() else None,
                    predicted=float(p[mask].mean()), roi=float(returns[mask].mean()),
                    roi_interval=grouped_date.interval(mask, returns),
                    roi_zero_top_3_payouts=float((returns[mask].sum()-paid[-3:].sum())/n))

    for name, p in predictions.items():
        top = np.zeros(len(data), dtype=bool)
        top[pd.Series(p).groupby(race, sort=False).idxmax()] = True
        delta = np.log(market)-np.log(p)
        pr_place = harville_place(p, race, slots)
        place_valid = complete & np.isin(slots, (2, 3))
        conditions = {}
        for column in ("going", "RACE_TYPE"):
            for label in sorted(data[column].dropna().unique()):
                mask = data[column].eq(label).to_numpy() & y
                if mask.any():
                    conditions[f"{column}={label}"] = dict(races=int(mask.sum()),
                        logloss_delta=float(delta[mask].mean()))
        calibration_delta = {}
        for reference in ("market_temperature", "v6", "v7"):
            if reference in predictions and reference != name:
                differences = np.log(predictions[reference])-np.log(p)
                calibration_delta[reference] = dict(mean=float(differences[y].mean()),
                                                    ci=grouped_date.interval(y, differences))
        result[name] = dict(
            races=grouped.ngroups, log_loss=float(-np.log(p[y]).mean()),
            race_brier=float(np.square(y-p).sum()/y.sum()),
            delta_market=float(delta[y].mean()), delta_ci=grouped_date.interval(y, delta),
            top_pick=band_stats(top, p), strata=conditions, paired=calibration_delta,
            harville_place_runner_brier=float(np.square(place[place_valid]-pr_place[place_valid]).mean())
                if place_valid.any() else None,
            harville_place_runners=int(place_valid.sum()),
            probability_calibration=[
                dict(lo=lo, hi=hi, n=int(mask.sum()), predicted=float(p[mask].mean()),
                     observed=float(y[mask].mean()))
                for lo, hi in zip((0, .03, .06, .10, .2, .4), (.03, .06, .10, .2, .4, 1.01))
                if (mask := (p >= lo) & (p < hi)).any()],
            roughies={str(lo): {label: band_stats((odds >= lo) & (odds < hi) & eligible, p)
                               for label, eligible in {
                                   "all": np.ones(len(data), dtype=bool),
                                   "uplift_and_fee_adjusted_point_ev":
                                       (p > market+1e-12) & (p*gross > 1) & (book >= 1-1e-12),
                               }.items()} for lo, hi in BANDS},
        )
    return result


def run(months, v7):
    names, frozen, verified = fixed_predictors(v7)
    root = Path(__file__).resolve().parents[2] / "monty_v6/results"
    runners = root / "joined_development_runners.csv.gz"
    matrix = root / "frozen_feature_matrix.npz"
    data = pd.read_csv(runners, dtype={"WIN_MARKET_ID": str, "SELECTION_ID": str})
    with np.load(matrix, allow_pickle=False) as archive:
        if archive["names"].tolist() != names:
            raise ValueError("Unexpected frozen feature order")
        full = archive["X"]
    if len(full) != len(data) or data.duplicated(["WIN_MARKET_ID", "SELECTION_ID"]).any():
        raise ValueError("Unexpected archive alignment")
    market = data.market_probability.to_numpy()
    race = data.WIN_MARKET_ID.to_numpy()
    wins = data.y.to_numpy().astype(bool)
    field = data.groupby("WIN_MARKET_ID")
    if not (field.y.sum().eq(1).all() and field.date.nunique().eq(1).all()
            and np.allclose(field.market_probability.sum(), 1)
            and np.allclose(full[:, names.index("log_market_probability")], np.log(market))):
        raise ValueError("Archive outcomes, race keys or matrix alignment fail")
    labels = place_labels(months, ["2025_05", "2025_06"])
    data = join_places(data, labels)
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    if not np.all(np.isfinite(odds) & (odds > 1)):
        raise ValueError("Invalid exchange quote")
    inverse_odds = 1/odds
    total = pd.Series(inverse_odds).groupby(race).transform("sum").to_numpy()
    if not np.allclose(inverse_odds/total, market, atol=1e-14, rtol=1e-12):
        raise ValueError("Market baseline differs from normalized archived quotes")
    raw = full[:, [names.index(k) for k in FEATURES]]
    # Archive rows may be reordered within dates by the private place merge.
    intent = prior_roles(data, raw)
    enriched = np.column_stack((raw, intent))
    coverage = np.isfinite(raw).mean(axis=1)
    race_coverage = pd.Series(coverage).groupby(race).transform("mean").to_numpy()
    arms, folds = [], []
    for cutoff, start, end in FOLDS:
        train = data.date.lt(cutoff).to_numpy()
        calibration = data.date.ge(cutoff).to_numpy() & data.date.lt(start).to_numpy()
        test = data.date.between(start, end).to_numpy()
        x = design(raw, train)
        w = fit_logits(x[train], wins[train], race[train], penalty=.01)
        form = x @ w
        extra_x = design(enriched, train)
        extended = extra_x @ fit_logits(extra_x[train], wins[train], race[train], penalty=.01)
        market_log = np.log(market)
        pair = np.column_stack((form, market_log))
        adaptive = np.column_stack((pair, form*(race_coverage-.9)))
        coeff = {}
        for label, z in (("market_temperature", pair[:, 1:]),
                         ("benter", pair), ("adaptive", adaptive),
                         ("intent_combined", np.column_stack((extended, market_log)))):
            coeff[label] = fit_logits(z[calibration], wins[calibration], race[calibration],
                                      penalty=.002, initial=np.r_[np.zeros(z.shape[1]-1), 1.])
        pls = PLSRegression(n_components=4, scale=False).fit(x[train], wins[train].astype(float))
        pls_scores = pls.transform(x)
        pls_w = fit_logits(pls_scores[train], wins[train], race[train], penalty=.01)
        boost = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15,
            learning_rate=.06, l2_regularization=1, early_stopping=False, random_state=42)
        boost.fit(x[train], wins[train])
        boosted = boost.decision_function(x)
        boost_pair = np.column_stack((boosted, market_log))
        bw = fit_logits(boost_pair[calibration], wins[calibration], race[calibration], penalty=.002)
        logits = dict(fundamental=form, market_temperature=pair[:, 1:] @ coeff["market_temperature"],
                      intent_fundamental=extended,
                      intent_combined=np.column_stack((extended, market_log)) @ coeff["intent_combined"],
                      benter=pair @ coeff["benter"], adaptive=adaptive @ coeff["adaptive"],
                      pls_inspired=pls_scores @ pls_w, boost_fundamental=boosted,
                      boost_combined=boost_pair @ bw, uniform=np.zeros(len(data)))
        preds = {k: softmax(value[test], race[test]) for k, value in logits.items()}
        preds["market"] = market[test]
        if start == "2025-06-01":
            preds.update(frozen(data.loc[test], full[test]))
        observed = data.loc[test].reset_index(drop=True)
        arms.append((observed, preds))
        folds.append(dict(fit_end_exclusive=cutoff, calibration_start=cutoff, test_start=start,
                          test_end=end, fitted_races=int(wins[train].sum()),
                          calibration_races=int(wins[calibration].sum()), day_count=observed.date.nunique(),
                          coefficients={k: v.tolist() for k, v in coeff.items()},
                          adaptive_form_weight_range=[float(np.min(coeff["adaptive"][0]+coeff["adaptive"][2]*(race_coverage[test]-.9))),
                                                      float(np.max(coeff["adaptive"][0]+coeff["adaptive"][2]*(race_coverage[test]-.9)))],
                          boost_combination_weights=bw.tolist(), results=metrics(observed, preds)))
    common = set.intersection(*(set(p) for _, p in arms))
    pool = {k: np.concatenate([p[k] for _, p in arms]) for k in sorted(common)}
    return dict(archive_sha256={p.name: digest(p) for p in (runners, matrix)},
                software=dict(numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__,
                              scikit_learn=sklearn.__version__), verified_v6_artifacts=verified,
                features={k: float(np.isfinite(v).mean()) for k, v in zip(FEATURES, raw.T)},
                intent_features={k: float(np.isfinite(v).mean()) for k, v in zip(INTENT_FEATURES, intent.T)},
                archive_context_observed={k: int(data[k].notna().sum()) for k in (
                    "barrier", "jockey", "trainer", "class_text", "going_text",
                    "allocated_weight", "age", "is_gelding", "first_after_gelding", "blinkers_first")},
                place_source_sha256={month: digest(months / f"{month}.csv")
                                     for month in ("2025_05", "2025_06")},
                total_archive_runners=len(data), total_archive_races=field.ngroups,
                scope="Retrospective scheduled-off exchange quotes; no fixed-win, fills, or prospective evidence",
                folds=folds, pooled=metrics(pd.concat([d for d, _ in arms], ignore_index=True), pool))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=Path, required=True)
    parser.add_argument("--v7", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(args.months, args.v7), indent=2, allow_nan=False)+"\n")
