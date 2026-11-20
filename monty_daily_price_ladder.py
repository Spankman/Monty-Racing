"""Daily Monty display adapter. Does not change V6 scores or authorise wagers.

Input: already-qualified race shortlists, with runners ranked by winning chance.
Do not use this module to promote unqualified races into selections.
"""
from monty_single_race_ladder import price_ladder

LABELS={"BB":"BB","QUINELLA BOXED":"Q (boxed)","TRIFECTA BOXED":"T (boxed)","FIRST FOUR BOXED":"FF (boxed)"}

def format_daily(shortlists):
    """Group qualified race picks by meeting, retaining race order."""
    groups={}
    for item in shortlists:
        meeting=str(item["meeting"]).strip()
        race=int(item["race"])
        if not meeting or race<1:
            raise ValueError("Invalid meeting or race")
        ranked=item["ranked"]
        if not item.get("qualified",False):
            continue
        result=price_ladder(ranked)
        selected=result["selections"]
        line=f"R{race} — {LABELS[result['bet_type']]}: "+ " → ".join(
            (f"**#{r['number']} {r['horse']}**" if i==0 else f"#{r['number']} {r['horse']}")
            for i,r in enumerate(selected))
        groups.setdefault(meeting,[]).append((race,line))
    return "\n\n".join(
        "**"+meeting+"**\n"+"\n".join(line for _,line in sorted(lines))
        for meeting,lines in groups.items())
