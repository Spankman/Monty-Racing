"""Evidence-based feature prioritisation on held-out chronological folds.

Caller supplies predictions from models FIT ONLY ON TRAINING DATA for each fold.
This module does not fit or alter Monty V6.
"""
import math

def log_loss(y, p):
    if len(y) != len(p) or not y:
        raise ValueError("Nonempty aligned outcomes/probabilities required")
    total = 0.0
    for actual, prob in zip(y, p):
        if actual not in (0, 1) or not isinstance(prob, (int,float)) or not math.isfinite(prob) or not 0 <= prob <= 1:
            raise ValueError("Invalid outcome or probability")
        q = max(1e-12, min(1 - 1e-12, prob))
        total -= actual * math.log(q) + (1 - actual) * math.log(1-q)
    return total / len(y)

def rank_feature_groups(folds, minimum_improvement=0.0005):
    """Ablation ranking using paired, out-of-sample probabilities.

    folds: list of {y, baseline, without: {feature_group: probabilities}}.
    Positive delta = removal worsened log loss, so feature group helped.
    Require each group on every fold; never infer weights from training scores.
    """
    if not folds:
        raise ValueError("At least one held-out fold required")
    groups = set(folds[0]["without"])
    if not groups or any(set(f["without"]) != groups for f in folds):
        raise ValueError("Identical ablation groups required across folds")
    output = []
    for group in sorted(groups):
        deltas, n = [], 0
        for f in folds:
            y = f["y"]
            deltas.append(log_loss(y, f["without"][group]) - log_loss(y, f["baseline"]))
            n += len(y)
        mean = sum(deltas) / len(deltas)
        output.append({
            "group": group,
            "mean_logloss_gain": mean,
            "fold_gains": deltas,
            "folds_positive": sum(d > 0 for d in deltas),
            "folds": len(deltas),
            "observations": n,
            "priority": "high" if mean >= minimum_improvement and all(d > 0 for d in deltas)
                        else "investigate" if mean > 0 else "low",
        })
    return sorted(output, key=lambda r: r["mean_logloss_gain"], reverse=True)
