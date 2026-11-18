"""Provisional V7 ranking, NOT a calibrated probability or betting system.

Combine a frozen V6 probability ranking with independently named expert
endorsements. The 10% expert blend is a declared *heuristic* and must be
evaluated prospectively before promotion. A race's runners are ranked
relative to one another; no expert votes are fabricated.
"""
import math

def provisional_rank(overlay, expert_blend=0.10):
    if not 0 <= expert_blend <= 1:
        raise ValueError("expert_blend must be between 0 and 1")
    output=[]
    for race in overlay["races"]:
        rows=race["runners"]
        values=[]
        for row in rows:
            raw=row.get("v6_win_probability")
            if raw is None:
                raise ValueError("Missing V6 win probability")
            p=float(raw)
            if not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError("Invalid V6 win probability")
            values.append(p)
        total=sum(values)
        if total <= 0:
            raise ValueError("Zero V6 probability mass")
        counts=[int(row.get("expert_mentions",0)) for row in rows]
        if any(n<0 for n in counts):
            raise ValueError("Negative expert count")
        max_count=max(counts,default=0)
        # If no expert coverage, do not dilute V6 or invent consensus.
        alpha=expert_blend if max_count else 0.0
        ranked=[]
        for row,p,n in zip(rows,values,counts):
            # Score is a relative ranking index, not a win probability.
            score=(1-alpha)*(p/total)+alpha*(n/max_count if max_count else 0)
            ranked.append({**row,"provisional_rank_score":round(score,8),
                           "rank_score_is_probability":False,
                           "expert_blend_used":alpha})
        ranked.sort(key=lambda r:(-r["provisional_rank_score"],-float(r["v6_win_probability"]),str(r["number"])))
        output.append({**race,"runners":ranked,
                       "betting_recommendation":"NO_BET" if race["betting_eligibility"]["status"]=="NO_BET" else "RESEARCH_ONLY"})
    return {"status":"PROVISIONAL_V7_RANKING_NOT_VALIDATED",
            "expert_blend":expert_blend,"races":output}

def main():
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument("--overlay",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--expert-blend",type=float,default=0.10)
    args=parser.parse_args()
    data=json.loads(Path(args.overlay).read_text(encoding="utf-8"))
    result=provisional_rank(data,args.expert_blend)
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"race_count":len(result["races"])}))

if __name__=="__main__":
    main()
