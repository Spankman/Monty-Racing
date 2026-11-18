"""Conservative dynamic expert blend for Monty V7 research.

This is a deterministic heuristic, NOT learned weights. Expert influence
depends on independently verified source coverage and agreement. Without
verified independence the blend remains zero. Never alters V6 artifacts.
"""
import math
from collections import Counter

def dynamic_expert_blend(runners, max_blend=0.20, min_independent=2):
    if not 0 <= max_blend <= 0.30:
        raise ValueError("Invalid maximum expert influence")
    if min_independent < 2:
        raise ValueError("Require at least two independent editorial voices")
    votes=[]
    for runner in runners:
        # A verified source may only vote for one horse in the race.
        sources=runner.get("verified_independent_sources",[])
        if not isinstance(sources,list):
            raise ValueError("verified_independent_sources must be a list")
        for source in set(sources):
            if not isinstance(source,str) or not source.strip():
                raise ValueError("Invalid source")
            votes.append((source,str(runner["number"])))
    by_source={}
    for source,horse in votes:
        if source in by_source and by_source[source]!=horse:
            raise ValueError("Same independent source endorsed multiple horses")
        by_source[source]=horse
    n=len(by_source)
    if n < min_independent:
        return {"blend":0.0,"independent_experts":n,"agreement":None,
                "reason":"INSUFFICIENT_VERIFIED_INDEPENDENT_EXPERTS"}
    counts=Counter(by_source.values())
    agreement=max(counts.values())/n
    # Scale from no influence at divided votes to max at unanimous votes.
    # Coverage saturates at five independent sources.
    coverage=min(n/5,1.0)
    strength=max(0.0,(agreement-0.5)/0.5)
    blend=min(max_blend,max_blend*coverage*strength)
    return {"blend":round(blend,6),"independent_experts":n,
            "agreement":round(agreement,6),"reason":"PROVISIONAL_HEURISTIC_NOT_CALIBRATED"}

def rank_dynamic(overlay,max_blend=0.20):
    from expert_consensus_experiment.provisional_rank import provisional_rank
    output=[]
    for race in overlay["races"]:
        d=dynamic_expert_blend(race["runners"],max_blend=max_blend)
        # Only verified independent endorsements contribute; generic mentions do not.
        sanitized={**race,"runners":[{**r,
                    "expert_mentions":len(set(r.get("verified_independent_sources",[])))}
                    for r in race["runners"]]}
        result=provisional_rank({"races":[sanitized]},expert_blend=d["blend"])["races"][0]
        result["dynamic_expert_evidence"]=d
        output.append(result)
    return {"status":"PROVISIONAL_DYNAMIC_V7_RESEARCH_ONLY",
            "races":output,"maximum_expert_blend":max_blend}
