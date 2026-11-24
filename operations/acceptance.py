"""Branch-only live acceptance using one real provider capture; no publication.

Uses the existing Actions secrets and frozen engines. Writes derived forecasts
and receipts only to the workflow artifact. Never creates operational issues,
modifies the results branch, or authorises bets.
"""
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import monty_operations as ops
from krok_adapter import fetch


def main():
    if os.environ.get('GITHUB_REF_NAME') != 'fix/prediction-approval-diagnostics':
        raise SystemExit('Live diagnostic is restricted to the repair branch')
    day=ops.utcnow().astimezone(ops.TZ).date().isoformat()
    key=os.environ.get('KROK_API_KEY','').strip()
    if not key:raise SystemExit('Live acceptance blocked: KROK_API_KEY absent')
    payload=fetch(day,key);captured=ops.utcnow()
    snapshot,audit=ops.normalized_snapshot(payload,day)
    meta=ops.metadata(payload,day)
    candidates=[r for r in snapshot['races'] if
                (r['meeting'].casefold(),str(r['race'])) in meta
                and meta[(r['meeting'].casefold(),str(r['race']))]['country']=='AU']
    candidates=[r for r in candidates if ops.timestamp(meta[(r['meeting'].casefold(),str(r['race']))]['scheduled_start'])>captured+timedelta(minutes=10)]
    if not candidates:raise SystemExit('Live acceptance blocked: no eligible upcoming AU race')
    target=candidates[0]
    commands=['RM6','RM7','RM6PS','RM7PS']
    commands += [f"{name} {target['meeting']} {target['race']}" for name in commands]
    summary=dict(schema='monty.repair.live-acceptance.v1',date=day,captured_at=captured.isoformat(),
                 source_mode='LIVE',production_publication=False,commands=[],provider_audit=audit)
    base=Path('operations_output');tag=os.environ['GITHUB_RUN_ID']
    for i,text in enumerate(commands):
        start=time.monotonic();req=ops.command(text,day,'AU');run_id=f'{tag}-diagnostic-{i+1}'
        out=base/run_id
        result=ops.execute(day,out,'v7_engine',run_id=run_id,payload=payload,captured=captured,request=req,timings=True)
        public=out/'public'
        view=ops.projection(result,req)
        ops.write(public/'requested-view.json',view)
        (public/'requested-ticket.txt').write_text(ops.ticket(view))
        receipt=json.loads((public/'receipt.json').read_text())
        summary['commands'].append(dict(command=text,run_id=run_id,status=result['status'],models=result['models'],
           elapsed_seconds=round(time.monotonic()-start,3),capture_age_seconds=(ops.utcnow()-captured).total_seconds(),
           forecast_sha256=receipt['forecast_sha256'],receipt_sha256=ops.sha(public/'receipt.json'),
           coverage=result['coverage'],classifications={v:sorted({r['models'][v].get('prediction_classification','UNKNOWN') for r in result['races']}) for v in ['V6','V7']}))
    directory=base/(tag+'-diagnostic-summary')/'public'
    ops.write(directory/'live-acceptance.json',summary)
    print(json.dumps(summary,allow_nan=False))
    if any(c['status']!='COMPLETED_ASSESSMENTS' for c in summary['commands']):
        raise SystemExit('Live acceptance incomplete: inspect semantic outcomes')


if __name__=='__main__':main()
