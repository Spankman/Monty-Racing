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
    count = 1
    # First three short-priced ranked runners progressively expand the box.
    while count <= 3 and count < len(ranked) and float(ranked[count-1]["odds"]) < short_price:
        count += 1
    labels = {1: "BB", 2: "QUINELLA BOXED", 3: "TRIFECTA BOXED", 4: "FIRST FOUR BOXED"}
    return {"bet_type": labels[count], "selections": ranked[:count],
            "bet_authorised": False,
            "reason": "Win-odds selection only; exotic value not independently verified"}

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
        if not horse or not math.isfinite(p) or not 0 < p <= 1 or not math.isfinite(odds) or odds <= 1:
            raise ValueError("Invalid runner")
        ranked.append({"number":number,"horse":horse,"probability":p,
                       "odds":odds,"edge":p*odds-1})
    ranked.sort(key=lambda r:(-r["probability"],-r["edge"],(0,int(r["number"])) if r["number"].isdigit() else (1,r["number"])))
    if sum(r["probability"] for r in ranked) > 1.02:
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
    if best["edge"] >= min_edge and best["odds"] >= short_price:
        return {**result,"bet_type":"WIN","selections":[best],"bet_authorised":True,
                "reason":"Top-ranked runner has verified positive estimated win edge"}
    # An exotic is eligible only at the stage selected by the fixed-win prices.
    ladder=price_ladder(ranked,short_price=short_price)
    kind=ladder["bet_type"]
    quote=(exotic_quotes or {}).get(kind)
    if kind!="BB" and isinstance(quote,dict) and quote.get("verified") is True:
        try:
            joint=float(quote.get("calibrated_probability"))
            dividend=float(quote.get("decimal_dividend"))
        except (TypeError,ValueError,OverflowError):
            joint=dividend=math.nan
        if 0<joint<=1 and math.isfinite(dividend) and dividend>1 and joint*dividend-1>=min_edge:
            return {**result,"bet_type":kind,"selections":ladder["selections"],
                    "bet_authorised":True,
                    "reason":"Verified exotic quote and calibrated combination edge"}
    return {**result,"reason":"Best runner identified; no verified positive-value wager. NO BET"}
