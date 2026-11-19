"""Conservative candidate extraction from permitted, already-captured article HTML.

Candidates are NEVER verified tips. They require independent matching to a
race-day field, actual capture time, source URL, author and race-off evidence.
No site fetches or model blending happen in this module.
"""
import argparse,json,re
from pathlib import Path
from bs4 import BeautifulSoup

PATTERNS=[
 re.compile(r'^\s*(?:best bet|next best|value bet|roughie)\s*[:\\-–]\s*(?:race\s*(\d+)\s*[,;: -]*)?(?:#\s*(\d+)\s*)?([A-Za-z][A-Za-z0-9\'’ .-]{2,60})\s*$',re.I),
 re.compile(r'^\s*race\s*(\d+)\s*[:\\-–]\s*#\s*(\d+)\s+([A-Za-z][A-Za-z0-9\'’ .-]{2,60})\s*$',re.I),
]
def extract(html,source_url,author='',captured_at=''):
    soup=BeautifulSoup(html,'html.parser')
    for node in soup(['script','style','nav','footer','header']):node.decompose()
    candidates=[];seen=set()
    for node in soup.select('p,li,h2,h3,h4'):
        # Only simple, self-contained lines; never infer picks from prose.
        if node.find(['p','li','h2','h3','h4']):continue
        line=' '.join(node.stripped_strings)
        if len(line)>130:continue
        for pattern in PATTERNS:
            m=pattern.fullmatch(line)
            if not m:continue
            race,number,horse=m.groups()
            horse=horse.strip(' .-')
            if len(horse)<3:continue
            key=(race or '',number or '',horse.casefold(),line.casefold())
            if key in seen:break
            seen.add(key)
            candidates.append({'race':race or None,'number':number or None,'horse_text':horse,
                'evidence_text':line,'source_url':source_url,'author':author,
                'captured_at':captured_at,'status':'CANDIDATE_ONLY_NOT_VERIFIED'})
            break
    return candidates

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('html_file')
    p.add_argument('--source-url',required=True);p.add_argument('--author',default='')
    p.add_argument('--captured-at',default='');p.add_argument('--output',default='expert_tip_candidates.json')
    a=p.parse_args()
    candidates=extract(Path(a.html_file).read_text(),a.source_url,a.author,a.captured_at)
    Path(a.output).write_text(json.dumps({'candidates':candidates,'verified_tip_count':0},indent=2)+'\n')
    print(json.dumps({'candidates':len(candidates),'verified_tip_count':0}))
