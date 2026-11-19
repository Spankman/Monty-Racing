"""Conservative research performance gate: never calculate betting ROI from unverified data."""
import argparse,json
from pathlib import Path

BET_TYPES=('WIN','QUINELLA_2','TRIFECTA_BOX_3')

def report(reconciliation_path,output):
    data=json.loads(Path(reconciliation_path).read_text())
    if data.get('schema')!='monty-research-results-v1':raise ValueError('Unsupported reconciliation schema')
    rows=data.get('records')
    if not isinstance(rows,list) or not rows:raise ValueError('No reconciled records')
    if data.get('pre_off_proven') is not False or data.get('result_independently_verified') is not False:
        raise ValueError('Research-only reconciliation expected')
    if any(r.get('bet_settlement')!='NOT_APPLICABLE_RESEARCH_ONLY' for r in rows):
        raise ValueError('Unexpected betting settlement data')
    metrics={kind:{'bets':0,'stakes':None,'returns':None,'profit':None,'roi':None,
                   'status':'BLOCKED_UNVERIFIED_PREOFF_AND_RESULTS'} for kind in BET_TYPES}
    result={'schema':'monty-performance-gate-v1','source_reconciliation':str(reconciliation_path),
      'records_reviewed':len(rows),'performance':metrics,'no_bet':True,
      'warning':'No pre-off proof, official result verification, actual placed bets, or dividends. ROI is intentionally unavailable.'}
    out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(result,f,indent=2)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('reconciliation');p.add_argument('--output',default='research_performance_gate.json')
    a=p.parse_args();print(json.dumps(report(a.reconciliation,a.output)))
