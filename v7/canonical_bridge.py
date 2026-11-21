"""Convert independently checked Monty canonical race rows to V7 inference fields.

Conversion never certifies source verification or timing. The caller must
explicitly attest field verification after checking active runners and quotes.
"""
import datetime as dt
import numpy as np
import pandas as pd

def to_v7_fields(rows, *, date, country, source_url, field_verified=False):
    if not field_verified:
        raise ValueError("Independent active-field verification required")
    if country not in ("AU", "NZ") or not source_url or not str(source_url).startswith("https://"):
        raise ValueError("Country and attributable HTTPS source required")
    try:
        parsed_date = dt.date.fromisoformat(str(date))
    except (ValueError, TypeError):
        raise ValueError("Invalid race date; expected YYYY-MM-DD") from None
    if parsed_date > dt.date.today() + dt.timedelta(days=365):
        raise ValueError("Race date implausibly far in the future")
    df = pd.DataFrame(rows).copy()
    required = {"meeting", "race", "number", "horse", "odds"}
    if not required.issubset(df.columns) or df.empty:
        raise ValueError("Missing canonical runner fields")
    if df[list(required)].isna().any().any():
        raise ValueError("Incomplete runner identity or price")
    for key in ("meeting", "race", "number", "horse"):
        if df[key].astype(str).str.strip().eq("").any():
            raise ValueError("Blank runner identity")
    df["fixed_win_odds"] = pd.to_numeric(df["odds"], errors="raise")
    if not np.isfinite(df["fixed_win_odds"]).all() or not df["fixed_win_odds"].gt(1).all():
        raise ValueError("Invalid fixed-win odds")
    df["race_id"] = country + "|" + df["meeting"].astype(str).str.upper() + "|" + df["race"].astype(str)
    df["runner_id"] = df["number"].astype(str)
    if df.duplicated(["race_id", "runner_id"]).any() or (df.groupby("race_id").size() < 3).any():
        raise ValueError("Duplicate runner or insufficient active field")
    df["date"] = date
    df["country"] = country
    df["source_url"] = source_url
    df["field_verified"] = True
    return df
