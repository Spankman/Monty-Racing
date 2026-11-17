#!/usr/bin/env python3
"""TAB meeting discovery from saved HTML or live page (where network access is available).
Discovery is NOT a field/odds feed. Never claims a meeting is fully scored.
"""
import argparse,datetime,json,re,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
URL='https://www.tabtouch.com.au/racing/future-final-field'
NON_AU_NZ={'ENG','IRE','USA','UK','FR','JPN','HK','SAF','SGP'}
OTHER_CODES={'ALBION PARK','CANNINGTON','MELTON','MENANGLE','REDC LIFFE','RE DCLIFFE','WENTWORTH PARK'}
# Conservative: only positive verified thoroughbred venues are eligible; others are held for review.
KNOWN={'ASCOT','DARWIN','DOOMBEN','DUBBO','DUNKELD','GUNDAGAI','ILLAWARRA GRANGE','IPSWICH','MORPHETTVILLE','NEWCASTLE','ORANGE','RICCARTON PARK - NZ','SANDOWN - HILLSIDE','TAURANGA - NZ','TOOWOOMBA','GOLD COAST POLY','MORPHETTVILLE PARKS'}
def discover(html,date):
 soup=BeautifulSoup(html,'html.parser')
 target=datetime.date.fromisoformat(date)
 # Site's schedule headings are calendar-date scoped; inspect the section only.
 heading=None
 for el in soup.find_all(['h1','h2','h3','h4','th','strong','div','span']):
  s=el.get_text(' ',strip=True)
  if len(s)<60 and target.strftime('%d %b %Y').lstrip('0').lower() in s.lower():heading=el;break
 if heading is None:raise ValueError('Requested date heading not found: refuse to use another day')
 # Prefer table containing heading; fallback to sibling scan until next date heading.
 parent=heading.find_parent('table')
 if parent:
  rows=parent.find_all('tr')
  start=next((i for i,r in enumerate(rows) if heading in r.descendants),0)
  textrows=[r.get_text(' ',strip=True) for r in rows[start+1:]]
 else:
  textrows=[]
  for sib in heading.next_elements:
   if getattr(sib,'name',None) in ('h1','h2','h3','h4') and re.search(r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{1,2}\s+[A-Z][a-z]{2}\s+20\d{2}',sib.get_text(' ',strip=True)):break
   if getattr(sib,'name',None)=='tr':textrows.append(sib.get_text(' ',strip=True))
 results=[];seen=set()
 for line in textrows:
  m=re.search(r'^(.*?)\s+(\d+)\s*$',line)
  if not m:continue
  venue=m.group(1).strip().upper();n=int(m.group(2))
  if not venue or venue in seen:continue
  seen.add(venue)
  country='NZ' if venue.endswith('- NZ') else 'AU'
  status='eligible' if venue in KNOWN else 'review_required'
  if any(venue.endswith(' - '+x) for x in NON_AU_NZ):status='excluded_foreign'
  if venue in OTHER_CODES:status='excluded_other_code'
  results.append({'meeting':venue,'country':country,'market_count':n,'status':status})
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--html',help='Saved TABtouch page HTML');p.add_argument('--output',default='meeting_discovery.json');p.add_argument('--fetch',action='store_true');a=p.parse_args()
 if not a.html and not a.fetch:p.error('Provide --html or --fetch')
 if a.fetch:
  req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 MontyResearch/0.3'})
  with urllib.request.urlopen(req,timeout=20) as r:raw=r.read().decode('utf-8','replace')
 else:raw=Path(a.html).read_text(encoding='utf-8')
 meetings=discover(raw,a.date)
 obj={'date':a.date,'source':URL if a.fetch else str(Path(a.html).resolve()),'source_type':'TABtouch meeting markets (not official TAB.com.au runner verification)','meetings':meetings,'eligible_count':sum(x['status']=='eligible' for x in meetings),'runners_verified':0,'odds_verified':0,'ready_to_score':False}
 Path(a.output).write_text(json.dumps(obj,indent=2)+'\n');print(json.dumps(obj,indent=2))
if __name__=='__main__':main()
