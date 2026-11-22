"""Single-race ranked selection ladder, with explicit research-only safeguards.

Returns a ranked selection even when no wager can be justified. Exotic bets
require verified quoted dividends/odds and calibrated joint probabilities;
a short win price alone is not proof of exotic value.
"""
import math

def price_ladder(ranked, *, short_price=4.0):
    """Select BB/Q/T/FF by individual WIN odds only; no exotic dividends."""
    if not ranked:
        raise ValueError("Empty ranked field")
    if ranked[0].get("roughie") is True or ranked[0].get("evidence_verified") is False:
        return {"bet_type": "NO BET", "selections": ranked[:1],
                "bet_authorised": False, "reason": "Leader requires separate win-only review"}
    count = 1
    while count <= 3 and float(ranked[count - 1]["odds"]) < short_price:
        if (count == len(ranked) or ranked[count].get("evidence_verified") is False
                or ranked[count].get("roughie") is True
                or ranked[count].get("probability", ranked[count].get("research_prob", 1)) <= 0):
            return {"bet_type": "NO BET", "selections": ranked[:1],
                    "bet_authorised": False, "reason": "Next runner lacks usable evidence"}
        count += 1
    labels = {1: "BB", 2: "QUINELLA BOXED", 3: "TRIFECTA BOXED", 4: "FIRST FOUR BOXED"}
    return {"bet_type": labels[count], "selections": ranked[:count],
            "bet_authorised": False, "reason": "Price progression for research review"}


def choose(runners, *, approved=False, min_edge=0.05, short_price=4.0,
           exotic_quotes=None):
    if not runners:
        raise ValueError("Empty race field")
    ranked=[]
    seen=set()
    for row in runners:
        number=str(row["number"]).strip()
        if not number or number in seen:
            raise ValueError("Invalid or duplicate saddlecloth")
        seen.add(number)
        horse=str(row["horse"]).strip()
        p=float(row["research_prob"])
        odds=float(row["odds"])
        if not horse or not math.isfinite(p) or not 0 <= p <= 1 or not math.isfinite(odds) or odds <= 1:
            raise ValueError("Invalid runner")
        ranked.append({"number":number,"horse":horse,"probability":p,
                       "odds":odds,"edge":p*odds-1,
                       "evidence_verified": row.get("evidence_verified"),
                       "roughie": row.get("roughie") is True})
    ranked.sort(key=lambda r:(-r["probability"],-r["edge"],(0,int(r["number"])) if r["number"].isdigit() else (1,r["number"])))
    if not 0 < sum(r["probability"] for r in ranked) <= 1.02:
        raise ValueError("Inconsistent race probabilities")
    best=ranked[0]
    result={"ranked":ranked,"best":best,"bet_type":"RANKED PICK",
            "selections":[best],"bet_authorised":False,
            "reason":"Unapproved research model: selection only, NO BET"}
    if not approved:
        return {**result, **price_ladder(ranked, short_price=short_price)}
    # Single-race BB must always be the top-ranked horse. If its win price
    # is too short, progress to Q/T/FF; never silently substitute a lower
    # ranked horse as the win selection.
    if (best["edge"] >= min_edge and best["odds"] >= short_price
            and best["evidence_verified"] is not False):
        return {**result,"bet_type":"WIN","selections":[best],"bet_authorised":True,
                "reason":"Top-ranked runner has verified positive estimated win edge"}
    # An exotic is eligible only at the stage selected by the fixed-win prices.
    ladder=price_ladder(ranked,short_price=short_price)
    kind=ladder["bet_type"]
    quote=(exotic_quotes or {}).get(kind)
    if kind in ("QUINELLA BOXED", "TRIFECTA BOXED", "FIRST FOUR BOXED"):
        selections = ladder["selections"]
        expected = {r["number"] for r in selections}
        numbers = quote.get("runner_numbers") if isinstance(quote, dict) else None
        if (isinstance(numbers, list) and len(numbers) == len(expected)
                and {str(number) for number in numbers} == expected
                and quote.get("verified") is True):
            try:
                joint = float(quote["calibrated_probability"])
                payout = float(quote["return_units"])
                cost = float(quote["cost_units"])
            except (KeyError, TypeError, ValueError, OverflowError):
                joint = payout = cost = math.nan
            if (0 < joint <= 1 and math.isfinite(payout) and math.isfinite(cost)
                    and cost > 0 and payout > cost and joint * payout / cost - 1 >= min_edge):
                return {**result, "bet_type": kind, "selections": selections,
                        "cost_units": cost, "return_units_if_hit": payout,
                        "bet_authorised": True,
                        "reason": "Verified quote and calibrated combination edge"}
    return {**result,"reason":"Best runner identified; no verified positive-value wager. NO BET"}
