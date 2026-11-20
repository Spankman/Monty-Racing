"""Single-race ranked selection ladder, with explicit research-only safeguards.

Returns a ranked selection even when no wager can be justified. Exotic bets
require verified quoted dividends/odds and calibrated joint probabilities;
a short win price alone is not proof of exotic value.
"""
import math

def choose(runners, *, approved=False, min_edge=0.05, short_price=3.0,
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
    ranked.sort(key=lambda r:(-r["probability"],-r["edge"],int(r["number"]) if r["number"].isdigit() else r["number"]))
    if sum(r["probability"] for r in ranked) > 1.02:
        raise ValueError("Inconsistent race probabilities")
    best=ranked[0]
    result={"ranked":ranked,"best":best,"bet_type":"RANKED PICK",
            "selections":[best],"bet_authorised":False,
            "reason":"Unapproved research model: selection only, NO BET"}
    if not approved:
        return result
    # Try each eligible win candidate in model order, never force a negative-edge win bet.
    for r in ranked:
        if r["edge"] >= min_edge and r["odds"] >= short_price:
            return {**result,"bet_type":"WIN","selections":[r],"bet_authorised":True,
                    "reason":"Verified positive estimated win edge"}
    # The highest probability horse remains first in every exotic display.
    # Exotic quotes must explicitly supply verified edge and approved joint probability.
    for kind,n in (("QUINELLA BOXED",2),("TRIFECTA BOXED",3),("FIRST FOUR BOXED",4)):
        if len(ranked)<n:continue
        quote=(exotic_quotes or {}).get(kind)
        if not isinstance(quote,dict) or quote.get("verified") is not True:
            continue
        joint=quote.get("calibrated_probability")
        dividend=quote.get("decimal_dividend")
        if joint is None or dividend is None:continue
        joint=float(joint);dividend=float(dividend)
        if not (math.isfinite(joint) and 0<joint<=1 and math.isfinite(dividend) and dividend>1):
            continue
        if joint*dividend-1 >= min_edge:
            return {**result,"bet_type":kind,"selections":ranked[:n],
                    "bet_authorised":True,"reason":"Verified exotic quote and calibrated combination edge"}
    return {**result,"reason":"Best runner identified; no verified positive-value wager. NO BET"}
