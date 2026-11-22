"""Daily Monty display adapter. Does not change V6 scores or authorise wagers.

Input: already-qualified race shortlists, with runners ranked by winning chance.
Do not use this module to promote unqualified races into selections.
"""
from monty_single_race_ladder import price_ladder

LABELS={"NO BET":"NO BET","BB":"BB","QUINELLA BOXED":"Q (boxed)","TRIFECTA BOXED":"T (boxed)","FIRST FOUR BOXED":"FF (boxed)"}

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
        classification = item.get("classification") or "Unverified"
        lines = [f"R{race} · {classification} · {LABELS[result['bet_type']]} assessment · NO BET"]
        for index, row in enumerate(selected):
            display = f"#{row['number']} {row['horse']} ${float(row['odds']):.2f}"
            lines.append(f"- **Best Bet · {display}**" if index == 0 else f"- {display}")
        line = "\n".join(lines)
        groups.setdefault(meeting,[]).append((race,line))
    return "\n\n".join(
        "**"+meeting+"**\n"+"\n".join(line for _,line in sorted(lines))
        for meeting,lines in groups.items())
