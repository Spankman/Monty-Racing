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


def probe_form(payload,target,key):
    """One documented existing-provider probe; only aggregate schema published."""
    from collections import Counter
    from krok_client import get,ProviderError
    race=next((r for m in payload['data'] if m.get('venue')==target['meeting']
               for r in m.get('races',[]) if str(r.get('number'))==str(target['race'])),{})
    race_id=race.get('race_id') or race.get('race_key_v2') or race.get('race_key')
    # The endpoint-specific documentation also accepts numeric source IDs.
    # Never invent a slug or pass corp_/racehub_ source IDs as canonical IDs.
    if not race_id and str(race.get('id','')).isdigit():race_id=str(race['id'])
    if not race_id:return dict(attempted=False,reason='No provider-supplied documented field-form identifier')
    try:
        data=get('/api/v1/racing/field-form',{'race_id':race_id},key)
        allowed={'runners','history','last_starts','recent_form','past_runs','form','date','runner_id','selection_id',
                 'finish_position','win_bsp','starting_price','market_probability','BEST_AVAIL_BACK_AT_SCHEDULED_OFF',
                 'barrier','jockey','trainer','track_condition','distance','weight'}
        field=data.get('data')
        source_meeting=next(m for m in payload['data'] if m.get('venue')==target['meeting'])
        expected={(str(r.get('number')),str(r.get('name','')).strip().casefold()) for r in race.get('runners',[])}
        observed={(str(r.get('tab_number')),str(r.get('name','')).strip().casefold()) for r in field.get('runners',[])} if isinstance(field,dict) else set()
        identity_verified=bool(expected and observed==expected and str(field.get('date',''))[:10]==str(source_meeting['date'])[:10] and str(field.get('venue','')).casefold()==target['meeting'].casefold()
                               and str(field.get('race_number'))==str(target['race'])
                               and len(field.get('runners',[]))==len({n for n,_ in observed})==len(race.get('runners',[]))) if isinstance(field,dict) else False
        counts=Counter()
        def walk(value):
            if isinstance(value,dict):
                for k,v in value.items():
                    if k in allowed and v not in (None,'',[],{}):counts[k]+=1
                    walk(v)
            elif isinstance(value,list):
                for v in value:walk(v)
        walk(data.get('data'))
        return dict(attempted=True,success=True,field_identity_matches=identity_verified,data_shape=type(data.get('data')).__name__,
                    available_schema_counts=dict(counts),historical_feature_compatibility_verified=False,
                    limitation='Availability probe only; no historical features or outcomes injected into either frozen model')
    except ProviderError as exc:return dict(attempted=True,success=False,http_status=exc.status)
    except Exception as exc:return dict(attempted=True,success=False,error_type=type(exc).__name__)


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
    requests=[(text,'AU') for text in commands]+[('RM6','NZ'),('RM7','NZ')]
    summary=dict(schema='monty.repair.live-acceptance.v1',date=day,captured_at=captured.isoformat(),
                 source_mode='LIVE',production_publication=False,commands=[],provider_audit=audit)
    base=Path('operations_output');tag=os.environ['GITHUB_RUN_ID']
    for i,(text,country) in enumerate(requests):
        start=time.monotonic();req=ops.command(text,day,country);run_id=f'{tag}-diagnostic-{i+1}'
        out=base/run_id
        result=ops.execute(day,out,'v7_engine',run_id=run_id,payload=payload,captured=captured,request=req,timings=True)
        public=out/'public'
        view=ops.projection(result,req)
        ops.write(public/'requested-view.json',view)
        (public/'requested-ticket.txt').write_text(ops.ticket(view))
        receipt=json.loads((public/'receipt.json').read_text())
        summary['commands'].append(dict(command=text,country=country,run_id=run_id,status=result['status'],models=result['models'],
           elapsed_seconds=round(time.monotonic()-start,3),capture_age_seconds=(ops.utcnow()-captured).total_seconds(),
           forecast_sha256=receipt['forecast_sha256'],receipt_sha256=ops.sha(public/'receipt.json'),
           coverage=result['coverage'],classifications={v:sorted({r['models'][v].get('prediction_classification','UNKNOWN') for r in result['races']}) for v in ['V6','V7']}))
    summary['field_form_probe']=probe_form(payload,target,key)
    directory=base/(tag+'-diagnostic-summary')/'public'
    ops.write(directory/'live-acceptance.json',summary)
    print(json.dumps(summary,allow_nan=False))
    if any(c['status']!='COMPLETED_ASSESSMENTS' for c in summary['commands']):
        raise SystemExit('Live acceptance incomplete: inspect semantic outcomes')


if __name__=='__main__':main()
