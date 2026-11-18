"""Leakage-safe, race-normalized expert fusion research.

Train only on historical, *resolved* races with complete V6 scores and audited
expert features. Strict chronology; race groups never split across folds.
Uses Python stdlib only. Never mutates V6 or outputs betting advice.
"""
import argparse
import csv
import json
import math
from collections import defaultdict

EPS = 1e-12

def _prob(x):
    x = float(x)
    if not 0 < x < 1 or not math.isfinite(x):
        raise ValueError("Invalid V6 probability")
    return x

def _features(row):
    # Missing expert features have no effect: no inferred pseudo-votes.
    if not row.get("expert_requirement_satisfied", False):
        return (0.0, 0.0, 0.0)
    return (float(row["expert_top1_share"]), float(row["expert_top3_share"]),
            float(row.get("expert_coverage", 0)) / 20.0)

def _group(rows):
    races = defaultdict(list)
    for row in rows:
        for key in ("race_id", "race_date", "number", "v6_probability", "won"):
            if key not in row:
                raise ValueError("Missing " + key)
        if int(row["won"]) not in (0, 1):
            raise ValueError("won must be 0 or 1")
        races[(str(row["race_date"]), str(row["race_id"]))].append(row)
    for key, field in races.items():
        if len(field) < 2 or sum(int(r["won"]) for r in field) != 1:
            raise ValueError("Race must have exactly one winner: " + str(key))
        if len({str(r["number"]) for r in field}) != len(field):
            raise ValueError("Duplicate saddlecloth: " + str(key))
        for row in field:
            _prob(row["v6_probability"])
            if row.get("expert_requirement_satisfied", False):
                f = _features(row)
                if any(not math.isfinite(x) or x < 0 or x > 1 for x in f):
                    raise ValueError("Invalid expert feature")
    return races

def predict(field, beta):
    # Normalize baseline probabilities within each race, then tilt by
    # expert features. beta=0 is a strictly comparable V6-normalized baseline.
    logits = [math.log(_prob(r["v6_probability"])) +
              sum(b * x for b, x in zip(beta, _features(r))) for r in field]
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    total = sum(exps)
    return [x / total for x in exps]

def log_loss(field, beta):
    probs = predict(field, beta)
    winner = next(i for i, r in enumerate(field) if int(r["won"]) == 1)
    return -math.log(max(EPS, probs[winner]))

def fit(train, l2=1.0, steps=500, lr=0.05):
    beta = [0.0, 0.0, 0.0]
    # Race-level mean loss, L2 penalty, deterministic full-batch gradient.
    for _ in range(steps):
        grad = [0.0] * 3
        for field in train:
            probs = predict(field, beta)
            expected = [sum(p * f[j] for p, r in zip(probs, field)
                            for f in [_features(r)]) for j in range(3)]
            winner = next(r for r in field if int(r["won"]) == 1)
            actual = _features(winner)
            for j in range(3):
                grad[j] += expected[j] - actual[j]
        for j in range(3):
            grad[j] = grad[j] / len(train) + l2 * beta[j]
            beta[j] -= lr * grad[j]
    return beta

def walk_forward(rows, min_train_races=100, test_races=50, l2=1.0):
    grouped = _group(rows)
    dates = sorted({day for day, _ in grouped})
    folds = []
    # Date boundaries, not runner counts: no same-day future information.
    for start in range(1, len(dates)):
        training = [field for (day, _), field in grouped.items() if day < dates[start]]
        if len(training) < min_train_races:
            continue
        testing = [field for (day, _), field in grouped.items() if day == dates[start]]
        if not testing:
            continue
        beta = fit(training, l2=l2)
        baseline = sum(log_loss(field, (0., 0., 0.)) for field in testing)
        fusion = sum(log_loss(field, beta) for field in testing)
        folds.append({"test_date": dates[start], "train_races": len(training),
                      "test_races": len(testing), "v6_logloss_sum": baseline,
                      "fusion_logloss_sum": fusion, "coefficients": beta,
                      "expert_eligible_races": sum(
                          any(r.get("expert_requirement_satisfied", False) for r in f)
                          for f in testing)})
    if not folds:
        return {"status": "INSUFFICIENT_HISTORICAL_DATA", "folds": 0,
                "required_min_training_races": min_train_races}
    n = sum(f["test_races"] for f in folds)
    return {"status": "RESEARCH_ONLY", "folds": len(folds), "test_races": n,
            "v6_mean_logloss": sum(f["v6_logloss_sum"] for f in folds) / n,
            "fusion_mean_logloss": sum(f["fusion_logloss_sum"] for f in folds) / n,
            "eligible_test_races": sum(f["expert_eligible_races"] for f in folds),
            "details": folds}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--historical", required=True, help="CSV with resolved races")
    p.add_argument("--output", default="v7_fusion_backtest.json")
    p.add_argument("--min-train-races", type=int, default=100)
    p.add_argument("--l2", type=float, default=1.0)
    args = p.parse_args()
    with open(args.historical, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["expert_requirement_satisfied"] = str(
            r.get("expert_requirement_satisfied", "")).lower() in ("true", "1")
    result = walk_forward(rows, args.min_train_races, l2=args.l2)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "details"}))

if __name__ == "__main__":
    main()
