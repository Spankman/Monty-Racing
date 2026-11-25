"""Genuine frozen inference on explicitly synthetic inputs, zero provider calls."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import hashlib,json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import monty_operations as ops

def run(output,v7):
    at=datetime.now(timezone.utc);day=at.astimezone(ops.TZ).date().isoformat()
    payload=dict(success=True,data=[dict(venue='Engineering Fixture',country='AU',type='T',date=day,races=[dict(number=1,name='BM64 ENGINEERING SYNTHETIC',race_class='BM64',distance_m=1400,track_condition='Good 4',jump_time=(at+timedelta(minutes=20)).isoformat(),runner_count=7,
        runners=[dict(number=i,name='SYNTHETIC RUNNER '+str(i),barrier=i,weight=55+i/2,is_scratched=False,odds=[dict(bookmaker='TAB',win=price,captured_at=at.isoformat())]) for i,price in enumerate([2.5,4,6,10,20,40],1)]+[dict(number=7,name='SYNTHETIC SCRATCHED RUNNER',is_scratched=True)])])],meta=dict(has_more=False))
    result=ops.execute(day,Path(output),Path(v7),run_id=os.environ.get('GITHUB_RUN_ID','offline-evidence')+'-fixture',payload=payload,captured=at,fixture=True,
        evidence_policy=Path(__file__).parent/'evidence/policy.example.json')
    receipt=json.loads((Path(output)/'public/receipt.json').read_text())
    if not result['evidence']['complete'] or not all(r['models'][v]['status']=='SCORED' for r in result['races'] for v in ('V6','V7')):raise ValueError('Frozen fixture inference/evidence acceptance failed')
    aggregate=dict(classification='OFFLINE SYNTHETIC INPUTS, GENUINE FROZEN V6/V7 INFERENCE; NOT LIVE ACCEPTANCE',provider_calls=0,
        models=result['models'],source_snapshot_sha256=result['provider_snapshot_sha256'],evidence=result['evidence'],
        receipt_sha256=hashlib.sha256((Path(output)/'public/receipt.json').read_bytes()).hexdigest(),
        scored={v:sum(len(r['models'][v]['ranked_runners']) for r in result['races']) for v in ('V6','V7')},
        feature_audits=result['evidence']['model_diagnostics'],private_plaintext_cleanup=receipt['private_plaintext_cleanup'])
    # Synthetic forecasts are clearly labelled; no licensed raw source here.
    (Path(output)/'public/engineering-acceptance.json').write_text(json.dumps(aggregate,indent=2)+'\n')
    print(json.dumps({k:aggregate[k] for k in ('classification','provider_calls','scored','receipt_sha256')}))
    return aggregate
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
