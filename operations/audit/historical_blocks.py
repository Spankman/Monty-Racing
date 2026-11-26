"""Repeatable research-only block tests and archive coverage, on #242's cohort."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import LogisticRegression

from operations.audit import fundamental_study as base
from operations.audit.price_policy_study import DayBootstrap
from operations.audit.roughies_240 import digest, join_places, place_labels, softmax

ENGINEERING_SHA = "112703369ad8386df50801627b02b2c656092cf2"

BLOCKS = {
    "prior_start": ("observed_starts_log", "observed_win_rate", "last3_win_rate",
                    "last5_win_rate", "days_since_run_log", "resuming_60d", "quick_backup_7d"),
    "trainer": ("trainer_changed", "trainer_prior_starts_log", "trainer_prior_win_rate"),
    "jockey": ("jockey_changed", "jockey_prior_starts_log", "jockey_prior_win_rate"),
    "distance": ("distance_change_km", "distance_km",
                 "prior_similar_trip_win_rate", "prior_similar_trip_starts_log"),
    "class": ("benchmark_class", "benchmark_class_change"),
    "going": ("prior_same_going_win_rate", "prior_same_going_starts_log"),
    "barrier": ("barrier_fraction", "barrier_x_distance"),
    "intent": ("last_start_won", "last_start_beaten_favourite", "last_win_x_up_in_trip",
               "last_win_x_class_change", "last_win_x_log_recency"),
}


def suitability(rows):
    """Build from earlier local dates only, with archive-local horse keys."""
    if not rows.date.is_monotonic_increasing:
        raise ValueError("History must be sorted by local date")
    history = {}
    out = np.full((len(rows), 4), np.nan)
    for _, day in rows.groupby("date", sort=False):
        route = list(day.itertuples())
        for row in route:
            prior = history.get((row.SELECTION_ID, row.name_key), ())
            trip = [win for metres, _, win in prior if abs(metres-row.DISTANCE) <= 200]
            going = [win for _, surface, win in prior if surface == row.going]
            for off, sample in ((0, trip), (2, going if row.going in
                                          ("good", "soft", "heavy", "firm", "synthetic") else [])):
                if sample:
                    out[row.Index, off:off+2] = ((sum(sample)+.5)/(len(sample)+5), np.log1p(len(sample)))
        for row in route:
            history.setdefault((row.SELECTION_ID, row.name_key), []).append(
                (row.DISTANCE, row.going, row.y))
    return out


def check_interface(checkout, names):
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip() != ENGINEERING_SHA:
        raise ValueError("Require exact #243 research interface")
    path = "operations/research_interface.py"
    if subprocess.check_output(["git", "diff", "HEAD", "--", path], cwd=checkout):
        raise ValueError("Research interface has local modifications")
    spec = importlib.util.spec_from_file_location("monty_staged_research_interface", checkout/path)
    interface = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = interface
    spec.loader.exec_module(interface)
    interface.independent_form_columns(names)
    try:
        interface.walk_forward([{"date":"2025-01-01","race_id":"archive example",
                                 "features_verified_asof":False}], [])
    except ValueError as exc:
        return dict(commit=ENGINEERING_SHA, feature_names_passed=True, archive_gate=str(exc))
    raise RuntimeError("Unverified archive should be rejected by the prospective interface")


def run(root, v7, register_path, engineering, months):
    names, score, verified = base.fixed_predictors(v7)
    runners = root / "joined_development_runners.csv.gz"
    matrix = root / "frozen_feature_matrix.npz"
    data = pd.read_csv(runners, dtype={"WIN_MARKET_ID": str, "SELECTION_ID": str})
    with np.load(matrix, allow_pickle=False) as f:
        if names != f["names"].tolist():
            raise ValueError("Frozen feature order mismatch")
        full = f["X"]
    groups = data.groupby("WIN_MARKET_ID")
    y = data.y.to_numpy() == 1
    market = data.market_probability.to_numpy()
    odds = data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()
    race = data.WIN_MARKET_ID.to_numpy()
    if (len(data) != len(full) or not groups.y.sum().eq(1).all() or
            not groups.date.nunique().eq(1).all() or data.duplicated(
                ["WIN_MARKET_ID","SELECTION_ID"]).any() or
            not np.allclose(full[:, names.index("log_market_probability")], np.log(market))):
        raise ValueError("Broken archive alignment")
    normalized = softmax(-np.log(odds), race)
    if not np.allclose(market, normalized, atol=1e-14, rtol=1e-12):
        raise ValueError("Market mismatch")
    raw = full[:, [names.index(k) for k in base.FEATURES]]
    expanded = np.column_stack((raw, base.prior_roles(data, raw), suitability(data)))
    expanded_names = (*base.FEATURES, *base.INTENT_FEATURES, *BLOCKS["distance"][-2:], *BLOCKS["going"])
    interface = check_interface(engineering, expanded_names)
    selections = {"all": np.ones(len(expanded_names), dtype=bool)}
    selections.update({f"minus_{block}": np.array([k not in members for k in expanded_names])
                       for block, members in BLOCKS.items()})
    study = []
    for fit_end, test_start, test_end in base.FOLDS:
        train = data.date.lt(fit_end).to_numpy()
        cal = data.date.ge(fit_end).to_numpy() & data.date.lt(test_start).to_numpy()
        test = data.date.between(test_start, test_end).to_numpy()
        x = base.design(expanded, train)
        log_market = np.log(market)
        arms = {"market": market[test]}
        def estimate(z, penalty=.002):
            w = base.fit_logits(z[cal], y[cal], race[cal], penalty=penalty)
            return softmax(z[test] @ w, race[test])
        arms["calibrated_market"] = estimate(log_market[:, None])
        for key, keep in selections.items():
            columns = np.r_[keep, keep]
            z = x[:, columns]
            w = base.fit_logits(z[train], y[train], race[train], penalty=.01)
            form = z @ w
            if key == "all":
                raw_form = form
            arms[f"form_{key}"] = softmax(form[test], race[test])
            arms[f"blend_{key}"] = estimate(np.column_stack((form, log_market)))
        # Paper-informed eight-component logistic output, with entirely earlier
        # fit/calibration and allocation of unit probability mass to each race.
        z = PLSRegression(n_components=8, scale=False).fit(x[train], y[train].astype(float)).transform(x)
        model = LogisticRegression(C=1, max_iter=500).fit(z[train], y[train])
        form = np.log(np.clip(expit(model.decision_function(z)), 1e-12, 1))
        arms["pls8_form_adapted"] = softmax(form[test], race[test])
        arms["pls8_blend_adapted"] = estimate(np.column_stack((form, log_market)))
        completeness = pd.Series(np.isfinite(expanded).mean(axis=1)).groupby(
            race).transform("mean").to_numpy()
        # Fits a common block and a form x race completeness interaction.
        arms["adaptive"] = estimate(np.column_stack((raw_form, log_market,
                                                     raw_form*(completeness-.9))))
        if test_start == "2025-06-01":
            arms.update(score(data.loc[test], full[test]))
        study.append((data.loc[test].reset_index(drop=True), arms))

    def evaluate(rows, arms):
        winners = rows.y.to_numpy() == 1
        boot = DayBootstrap(rows.date)
        metrics = {}
        for key, p in arms.items():
            if key == "market":
                ref = p
            elif key.startswith("form_minus"):
                ref = arms["form_all"]
            elif key.startswith("blend_minus"):
                ref = arms["blend_all"]
            else:
                ref = arms["calibrated_market"]
            delta = np.log(ref) - np.log(p)
            top = pd.Series(p).groupby(rows.WIN_MARKET_ID,sort=False).idxmax().to_numpy()
            odds = rows.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy()[top]
            metrics[key] = dict(log_loss=float(-np.log(p[winners]).mean()),
                race_brier=float(np.square(winners-p).sum()/winners.sum()),
                win_strike=float(winners[top].mean()),
                quote_proxy_roi=float(np.where(winners[top],.95*(odds-1),-1).mean()),
                paired_delta=float(delta[winners].mean()), paired_ci=boot.interval(winners,delta))
        return metrics

    all_rows = pd.concat([rows for rows,_ in study], ignore_index=True)
    common = set.intersection(*(set(p) for _, p in study))
    pooled = {key: np.concatenate([arms[key] for _, arms in study]) for key in sorted(common)}
    labels = place_labels(months, ["2025_05", "2025_06"])
    focal = ("market", "calibrated_market", "form_all", "blend_all", "adaptive",
             "pls8_form_adapted", "pls8_blend_adapted")
    june_rows, june_arms = study[-1]
    pooled_diagnostics = base.metrics(join_places(all_rows, labels),
                                      {k: pooled[k] for k in focal})
    june_diagnostics = base.metrics(join_places(june_rows, labels),
                                    {k: june_arms[k] for k in (*focal,"v6","v7")})
    context = pd.read_csv(register_path)
    if set(context.feature) != set(names):
        raise ValueError("Source register and archive features differ")
    def count(values):
        finite = np.isfinite(values)
        return dict(runners=int(finite.sum()), races=int(pd.Series(race[finite]).nunique()),
                    runner_pct=100*float(finite.mean()))
    coverage = {k:count(values) for k,values in zip(names,full.T)}
    coverage.update({k:count(values) for k,values in zip(expanded_names,expanded.T)
                     if k not in coverage})
    return dict(staged_research_interface=interface, archive_sha256={p.name:digest(p) for p in (runners,matrix)},
        archive_period=[data.date.min(),data.date.max()], archive_runners=len(data),
        archive_races=groups.ngroups, v6_artifacts_verified=verified, coverage=coverage,
        folds=base.FOLDS, test_races=int(all_rows.y.sum()),
        pooled=evaluate(all_rows,pooled), pooled_diagnostics=pooled_diagnostics,
        june_diagnostics=june_diagnostics,
        place_source_sha256={m: digest(months/f"{m}.csv") for m in ("2025_05","2025_06")},
        fold_metrics=[evaluate(rows,arms) for rows,arms in study],
        note="Exposed 2025 archive, retrospective exchange quote proxies and unverified source vintage.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v7",type=Path,required=True)
    parser.add_argument("--months",type=Path,required=True)
    parser.add_argument("--engineering",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a = parser.parse_args()
    root = Path(__file__).resolve().parents[2]/"monty_v6/results"
    register = Path(__file__).with_name("AU_FREE_DATA_55_FEATURE_MATRIX.csv")
    a.output.write_text(json.dumps(run(root,a.v7,register,a.engineering,a.months),indent=2,allow_nan=False)+"\n")
