"""Reconcile research predictions with externally supplied results without modifying predictions.

This produces descriptive results ONLY. A result file is not proof of official
settlement or independently verified race results.
"""
import argparse,csv,hashlib,json,datetime
from pathlib import Path

def reconcile(ledger_path,results_path,output):
    ledger_path=Path(ledger_path);results_path=Path(results_path);output=Path(output)
    with ledger_path.open(newline='') as f:pred=list(csv.DictReader(f))
    with results_path.open(newline='') as f:results=list(csv.DictReader(f))
    if not pred or not results:raise ValueError('Empty predictions or results')
    required={'meeting','race','number','horse','finish_position','result_source','result_captured_utc'}
    if any(not required.issubset(r) for r in results):raise ValueError('Missing result columns')
    keys=set();lookup={}
    for r in results:
        key=(r['meeting'].strip().casefold(),r['race'].strip(),r['number'].strip())
        if not all(key) or key in keys:raise ValueError('Duplicate or invalid result identity')
        keys.add(key)
        if not r['horse'].strip() or not r['result_source'].strip() or not r['result_captured_utc'].strip():
            raise ValueError('Missing source, timestamp or horse')
        try:
            captured=datetime.datetime.fromisoformat(r['result_captured_utc'].strip().replace('Z','+00:00'))
        except ValueError as exc:
            raise ValueError('Invalid result capture timestamp') from exc
        if captured.tzinfo is None or captured.utcoffset() is None:
            raise ValueError('Result timestamp must include timezone')
        pos=r['finish_position'].strip()
        if not pos.isdigit() or int(pos)<1:raise ValueError('Only positive numeric finishing positions supported')
        lookup[key]=r
    # A complete result must have exactly one winner per race and no repeated
    # finishing positions. Dead heats and non-finishers need a separate schema.
    by_race={}
    for key,r in lookup.items():
        race_key=key[:2]
        by_race.setdefault(race_key,[]).append(int(r['finish_position']))
    for race_key,positions in by_race.items():
        if positions.count(1)!=1 or len(set(positions))!=len(positions):
            raise ValueError('Ambiguous winner or finishing positions: '+str(race_key))
    seen=set();joined=[]
    for p in pred:
        key=(p['meeting'].strip().casefold(),p['race'].strip(),p['number'].strip())
        if not all(key) or key in seen:raise ValueError('Duplicate or invalid prediction identity')
        seen.add(key)
        r=lookup.get(key)
        if r is None:raise ValueError('Incomplete results: '+str(key))
        if p['horse'].strip().casefold()!=r['horse'].strip().casefold():
            raise ValueError('Horse identity mismatch')
        if p.get('pre_off_proven')!='false' or p.get('status')!='UNAPPROVED RESEARCH — NO BET':
            raise ValueError('Unexpected prediction provenance or status')
        joined.append({'record_id':p['record_id'],'meeting':p['meeting'],'race':p['race'],
          'number':p['number'],'horse':p['horse'],'finish_position':r['finish_position'],
          'result_source':r['result_source'],'result_captured_utc':r['result_captured_utc'],
          'research_ranked_winner':str(int(r['finish_position'])==1).lower(),
          'pre_off_proven':'false','result_independently_verified':'false',
          'bet_settlement':'NOT_APPLICABLE_RESEARCH_ONLY'})
    if len(lookup)!=len(joined):raise ValueError('Extra unmatched result runners')
    report={'schema':'monty-research-results-v1','ledger_sha256':hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
      'results_sha256':hashlib.sha256(results_path.read_bytes()).hexdigest(),
      'records':joined,'pre_off_proven':False,'result_independently_verified':False,
      'warning':'External result rows are unverified. No ROI, betting edge, or pre-off claim is supported.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(report,f,indent=2)
    return {'records':len(joined),'pre_off_proven':False,'betting_status':'NO BET'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ledger');p.add_argument('results');p.add_argument('--output',default='research_result_reconciliation.json')
    a=p.parse_args();print(json.dumps(reconcile(a.ledger,a.results,a.output)))
