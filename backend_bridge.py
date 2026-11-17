#!/usr/bin/env python3
"""Prepare auditable Monty rows for MCPBackend; optional server-side upload.
No API keys are embedded. Defaults to offline preview; only verified pre-race
predictions may be frozen. Does not fetch Krok or run a hosted scheduler.
"""
import argparse, csv, datetime as dt, json, os, urllib.request
from pathlib import Path

BASE='https://data.mcpbackend.com/v1/proj_ux75e6u4pnyjh8lf6qk71ih0/db'

def prepare(snapshot, scored_csv, audit, freeze=False):
    if not audit.get('race_count') or not audit.get('runner_count'):
        raise ValueError('Missing successful scoring audit')
    if freeze and not audit.get('tab_verified'):
        raise ValueError('Cannot freeze unverified predictions; independently verify TAB fields and prices first')
    date=snapshot['date']
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    runners=snapshot['runners']
    with open(scored_csv, newline='', encoding='utf-8') as handle:
        scored=list(csv.DictReader(handle))
    expected={(str(r['meeting']).upper(),str(r['race']),str(r['number'])) for r in runners}
    actual={(r['meeting'].upper(),r['race'],r['number']) for r in scored}
    if len(expected)!=len(runners) or len(actual)!=len(scored) or expected!=actual:
        raise ValueError('Runner identities do not match scored output')
    meeting_rows=[];runner_rows=[];pred_rows=[];seen=set()
    for r in runners:
        venue=str(r['meeting']);race=str(r['race']);number=int(r['number'])
        race_ref=f'{date}|{venue.upper()}|R{race}'
        if venue.upper() not in seen:
            seen.add(venue.upper())
            meeting_rows.append(dict(race_date=date,country='NZ' if str(r.get('country','')).upper()=='NZ' else 'AU',venue=venue,meeting_ref=f'{date}|{venue.upper()}',source='Krok snapshot (unverified)',collected_at=now))
        runner_rows.append(dict(race_ref=race_ref,race_date=date,venue=venue,race_number=int(race),saddlecloth=number,horse_name=r['horse'],scratched=False,odds_decimal=float(r['odds']),features={k:v for k,v in r.items() if k not in ('meeting','race','number','horse','odds') and not k.startswith('_')},source='Krok snapshot (unverified)',collected_at=now))
    if freeze:
        for s in scored:
            race_ref=f"{date}|{s['meeting'].upper()}|R{s['race']}"
            pred_rows.append(dict(race_ref=race_ref,runner_ref=f"{race_ref}|#{s['number']}",model_version='V6 frozen',predicted_win_probability=float(s['monty_prob']),market_odds=float(s['odds']),value_edge=float(s['edge']),selection_type=s['category'],frozen_at=now,input_fingerprint=audit['source_sha256']))
    return {'race_meetings':meeting_rows,'runners':runner_rows,'monty_predictions':pred_rows}

def upload(rows,key):
    if not key: raise ValueError('MCPBACKEND_API_KEY is required for --upload')
    counts={}
    for table,items in rows.items():
        counts[table]=0
        for item in items:
            data=json.dumps(item).encode()
            req=urllib.request.Request(BASE+'/'+table,data=data,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req,timeout=20) as response:
                if response.status not in (200,201):raise RuntimeError(f'{table}: HTTP {response.status}')
            counts[table]+=1
    return counts

def main():
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--scored',required=True);p.add_argument('--audit',required=True);p.add_argument('--output',default='backend_preview.json');p.add_argument('--freeze',action='store_true');p.add_argument('--upload',action='store_true');a=p.parse_args()
    rows=prepare(json.loads(Path(a.snapshot).read_text()),a.scored,json.loads(Path(a.audit).read_text()),a.freeze)
    Path(a.output).write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({k:len(v) for k,v in rows.items()}))
    if a.upload:print('Uploaded:',upload(rows,os.getenv('MCPBACKEND_API_KEY')))
if __name__=='__main__':main()
