"""Owner-authorised one-capture live recovery check. Aggregate-only artifact.

No production delivery, provider fallback, trial mutation or retention grant.
Detailed projections are checked transiently, never published to public Actions.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import monty_operations as ops
from operations.evidence import store
from operations.tickets import combined,paired
from puntersedge_adapter import fetch_board


def main():
    day=ops.utcnow().astimezone(ops.TZ).date().isoformat();started=time.monotonic()
    meter=[]
    payload,captured=fetch_board(day,os.environ['PUNTERSEDGE_API_KEY'],meter=meter,command='OWNER_RECOVERY_ACCEPTANCE')
    report=dict(schema='monty.recovery-acceptance.v1',date=day,commit=os.environ['GITHUB_SHA'],
        workflow_url='https://github.com/Spankman/Monty-Racing/actions/runs/'+os.environ['GITHUB_RUN_ID'],
        provider='PuntersEdge',capture=captured.isoformat(),acquisition=payload['meta'],
        request_usage=meter,commands={},production_changed=False,raw_data_published=False)
    original=store.public_result
    def inspect(prediction,index,recorder):
        # Evaluate actual current projections before the licensed delivery filter.
        now=ops.utcnow();first=next((r for r in prediction['races'] if r['models']['V6']['status']=='SCORED' and r['models']['V7']['status']=='SCORED'),None)
        commands=['RM6','RM7','RM6PS','RM7PS']
        if first:commands += ['RM6 '+first['meeting']+' '+str(first['race']),'RM7 '+first['meeting']+' '+str(first['race'])]
        for text in commands:
            view=ops.projection(prediction,ops.command(text,day),now);slip=ops.ticket(view,now=now)
            report['commands'][text]=dict(races=len(view['races']),ranked_assessments=sum(bool((r['result'].get('diagnostic_assessment') or r['result']).get('ordered_selections')) for r in view['races']),
                slip_sha256=hashlib.sha256(slip.encode()).hexdigest(),betting_authorised=False)
        pair=paired(prediction,now);report['paired_ticket_hashes']=[hashlib.sha256(t['text'].encode()).hexdigest() for t in pair['tickets']]
        combined_view = combined(prediction, now)
        report['combined_ticket'] = dict(
            assessment_races=len(combined_view['races']),
            ticket_sha256=hashlib.sha256(ops.ticket(combined_view, now=now).encode()).hexdigest())
        report['read_only_status_check'] = dict(run_id=ops.projection(prediction, ops.command('C', day), now)['run_id'],
                                               live_command_submission=False)
        report['scoring']={v:m for v,m in prediction['models'].items()}
        report['coverage']=prediction['coverage'];report['status']=prediction['status']
        report['forecast_content_sha256']=hashlib.sha256(store.encoded(prediction)).hexdigest()
        report['capture_age_at_projection_seconds']=(now-captured).total_seconds()
        report['official_verification']='NOT SATISFIED — retain all independent field/history/value gates'
        report['private_delivery']='NOT ACCEPTED — public derived-display permission and private retrieval route unresolved'
        return original(prediction,index,recorder)
    store.public_result=inspect
    result=ops.execute(day,'operations_output/recovery-live','v7_engine',run_id=os.environ['GITHUB_RUN_ID'],payload=payload,captured=captured,request=ops.command('RM6',day),evidence_source='PuntersEdge')
    report['private_delivery']=result.get('private_delivery') or dict(status='PRIVATE_DELIVERY_BLOCKED')
    report['elapsed_seconds']=time.monotonic()-started
    p=Path('operations_output/recovery-aggregate');p.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(report,sort_keys=True,indent=2,allow_nan=False).encode();(p/'report.json').write_bytes(raw)
    (p/'report.sha256').write_text(hashlib.sha256(raw).hexdigest()+'  report.json\n')
    print(json.dumps({k:report.get(k) for k in ('provider','status','elapsed_seconds','capture_age_at_projection_seconds','private_delivery')}))
    if not report.get('scoring') or not all(report['scoring'][v].get('scored_races',0) for v in ('V6','V7')):
        raise SystemExit('No genuine paired scoring: inspect semantic report, not job colour')

if __name__=='__main__':main()
