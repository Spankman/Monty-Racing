"""Universal Monty race exclusion policy, applicable to V6, V7 and successors.

Never recommend betting on maidens, 2YO races or hurdles by default.
A race-specific explicit user request may override these restrictions.
No model weights or frozen V6 artifacts are modified.
"""
import re

def excluded_reasons(race):
    """Return exclusions using explicit race metadata, or conservative title cues.

    If category metadata is unavailable, caller must treat eligibility as
    unverified rather than silently assuming a race is eligible.
    """
    if not isinstance(race,dict):
        raise ValueError("race must be a dict")
    name=str(race.get("race_name") or race.get("name") or "").lower()
    category=str(race.get("race_type") or race.get("type") or "").lower()
    age=str(race.get("age_restriction") or race.get("age") or "").lower()
    text=" ".join((name,category,age))
    reasons=[]
    if race.get("is_maiden") is True or re.search(r"\bmaiden\b|\bmdn\b",text):
        reasons.append("MAIDEN")
    if race.get("is_two_year_old") is True or re.search(r"\b2\s*(?:yo|y/o|year[ -]?old|yrs?\s*old)\b|\bjuvenile\b|\b2yo\b",text):
        reasons.append("TWO_YEAR_OLD")
    if race.get("is_hurdle") is True or re.search(r"\bhurdles?\b|\bhcp\s*hurdle\b",text):
        reasons.append("HURDLE")
    return reasons

def betting_eligibility(race, explicitly_requested=False):
    reasons=excluded_reasons(race)
    if reasons and not explicitly_requested:
        return {"status":"NO_BET","reasons":reasons,"override_used":False}
    if reasons and explicitly_requested:
        return {"status":"OVERRIDE_ALLOWED","reasons":reasons,"override_used":True}
    # Lack of a trusted classification is not evidence of eligibility.
    trusted=any(k in race for k in ("is_maiden","is_two_year_old","is_hurdle"))
    if not trusted:
        return {"status":"CLASSIFICATION_UNVERIFIED","reasons":[],"override_used":False}
    return {"status":"ELIGIBLE","reasons":[],"override_used":False}
