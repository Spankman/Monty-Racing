"""Offline PE response wrapper + genuine frozen engines + command delivery.

The transport returns explicitly synthetic data. It never uses a provider key,
performs a network request or demonstrates live/provider licensing acceptance.
"""
import io,json,os,sys,time,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
import monty_operations as ops
from puntersedge_adapter import Client
from operations.puntersedge_capture import execute
from operations.render import render


def run(output,v7):
    at=datetime.now(timezone.utc);day=at.astimezone(ops.TZ).date().isoformat();calls=[]
    race=dict(race_id='SYNTHETIC-PE',venue='Engineering Fixture',race_number=1,country='AU',category='horse',start_time=(at+timedelta(minutes=20)).isoformat(),race_name='BM64 SYNTHETIC',race_class='BM64',distance_m=1400,track_condition='Good 4',
        runners=[dict(number=i,name='SYNTHETIC RUNNER '+str(i),barrier=i,weight=55+i/2,bookmakers=[dict(key='tab',win_price=p,last_update=at.isoformat(),age_basis='poll')]) for i,p in enumerate([2.5,4,6,10,20,40],1)],scratchings=[dict(number=7,name='SYNTHETIC SCRATCHED RUNNER')])
    body=json.dumps([race]).encode()
    class Response(io.BytesIO):
        status=200;headers={'X-Credits-Cost':'2'}
    def opener(*args,**kwargs):calls.append(1);return Response(body)
    policy=json.loads((Path(__file__).parent/'evidence/policy.example.json').read_text())
    policy['sources']['PuntersEdge']=dict(private_retention_permitted=True,permission_reference='EXPLICITLY SYNTHETIC OFFLINE TRANSPORT; not permission for real provider data',review_expires_at=(at+timedelta(days=1)).isoformat())
    client=Client('SYNTHETIC_OFFLINE_KEY',opener=opener)
    began=time.monotonic();f=execute(client,day,output,v7,run_id=os.getenv('GITHUB_RUN_ID','offline')+'-pe-fixture',venue=race['venue'],race_id=race['race_id'],request=ops.command('RM6',day),policy=policy,fixture=True)
    elapsed=time.monotonic()-began;output=Path(output)
    assert len(calls)==1 and f['evidence']['complete'] and f['evidence']['raw_http_pages']==1
    assert f['evidence']['encrypted_checkpoints']>=3 and not (output/'private').exists()
    commands=['RM6','RM7','RM6PS','RM7PS','RMV6PS','RMV7PS','RM6 Engineering Fixture 1','RM7 Engineering Fixture 1','RM6PS Engineering Fixture 1','RM7PS Engineering Fixture 1','Engineering Fixture 1']
    results=[]
    for text in commands:
        req=ops.command(text,day);view=ops.projection(f,req,at+timedelta(seconds=30));repeat=ops.projection(f,req,at+timedelta(seconds=30))
        assert view==repeat and len(view['races'])==1
        m=view['races'][0]['result'];assert m['status']=='SCORED'
        assert f['races'][0]['models'][req['version']]['ranked_runners']
        if req['view']=='official':assert m.get('diagnostic_assessment') and not m['ordered_selections']
        else:assert m.get('ranked_runners')
        assert m['betting_authorised'] is False
        mobile=ops.ticket(view,now=at+timedelta(seconds=30));html=render(view,now=at+timedelta(seconds=30))
        assert 'IN MONTY WE TRUST' in mobile.upper() and 'RUFFIES TO WATCH' in mobile
        assert 'RUFFIES TO WATCH' in html
        expired=ops.projection(f,req,ops.timestamp(f['captured_at'])+timedelta(seconds=300));assert not expired['races'][0]['result']['ordered_selections']
        results.append(dict(command=text,model=req['version'],inference='SCORED',classification=m['prediction_classification'],betting_authorised=False,repeated_retrieval='IDENTICAL',expiry='SELECTIONS_WITHHELD'))
    assert len(calls)==1 # Views and expiry never acquire or rescore.
    r=json.loads((output/'public/receipt.json').read_text())
    aggregate=dict(schema='monty.readiness-acceptance.v1',classification='OFFLINE SYNTHETIC HTTP + GENUINE FROZEN INFERENCE; NOT LIVE ACCEPTANCE',source_commit=f['evidence']['source_code_commit'],run_id=f['run_id'],simulated_transport_calls=len(calls),actual_provider_calls=0,actual_provider_credits=0,simulated_meter_reservation=client.reserved,engine_elapsed_seconds=elapsed,
        commands=results,models=f['models'],evidence=f['evidence'],receipt_sha256=hashlib.sha256((output/'public/receipt.json').read_bytes()).hexdigest(),plaintext_cleanup=r['private_plaintext_cleanup'])
    (output/'public/readiness-acceptance.json').write_text(json.dumps(aggregate,indent=2)+'\n')
    print(json.dumps({k:aggregate[k] for k in ('classification','run_id','receipt_sha256','engine_elapsed_seconds','actual_provider_calls')}))
    return aggregate

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
