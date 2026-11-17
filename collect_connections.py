"""Cache unique FormFav connection statistics and relevant Betfair metadata.

One bounded capture, no scheduler. FORMFAV_API_KEY stays in the environment.
"""
import argparse,collections,concurrent.futures,datetime,json,threading
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import pandas as pd
import race_day
from formfav_client import Client,FormFavError
from connections_enrichment import stats_file

SLUGS={'Sandown':'sandown-lakeside','Warwick Farm':'warwick-farm','Doomben':'doomben','Gawler':'gawler','Belmont':'belmont'}

def collect(inputs,cards,latest,output,date,client=None,workers=6):
    datetime.date.fromisoformat(date)
    if not 1<=workers<=6:raise ValueError('Use one to six workers')
    client=client or Client();usage=client.get('/usage')
    if usage.get('overQuota'):raise FormFavError('FormFav quota exhausted')
    out=Path(output);out.mkdir(parents=True,exist_ok=True);people={'jockey':set(),'trainer':set()};bindings=[]
    for row in inputs.itertuples():
        card=json.loads((Path(cards)/f'{SLUGS[row.meeting]}-{int(row.race)}.json').read_text())
        if card.get('date')!=date or card.get('raceNumber')!=int(row.race):raise ValueError('Source card date/race mismatch')
        runners=[r for r in card['runners'] if r['number']==int(row.number)]
        from monty.normalization import normal
        if len(runners)!=1 or normal(runners[0]['name'])!=normal(row.horse):raise ValueError('Source connection binding mismatch')
        b={'meeting':row.meeting,'race':int(row.race),'number':int(row.number),'horse':row.horse}
        for kind in people:
            name=runners[0].get(kind,'')
            if name and name.lower() not in ['not notified','unknown','tba']:
                people[kind].add(name);b[kind]=name
        bindings.append(b)
    (out/'runner_connections.json').write_text(json.dumps(bindings))
    markets=sorted(latest.market_id.astype(str).unique())
    if any(not m.isdigit() for m in markets):raise ValueError('Invalid historical market ID')
    jobs=[('metadata',m,None) for m in markets]+[(k,n,w) for k,names in people.items() for n in sorted(names) for w in [90,365]]
    stop=threading.Event()
    def fetch(job):
        kind,name,window=job;info={'kind':kind,'name':name,'window':window}
        path=out/('market-'+name+'.json') if kind=='metadata' else stats_file(out,kind,name,window)
        if path.exists():return dict(info,status='cached')
        if stop.is_set():return dict(info,status='stopped')
        try:
            if kind=='metadata':
                with urlopen('https://apigateway.betfair.com.au/hub/raceevent/1.'+name,timeout=20) as response:data=json.load(response)
            else:data=client.stats(kind,name,window)
            path.write_text(json.dumps({'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'query':info,'data':data}))
            return dict(info,status=200)
        except HTTPError as exc:return dict(info,status=exc.code)
        except FormFavError as exc:
            message=str(exc)
            if any('HTTP '+str(code) in message for code in [401,402,403,429]):stop.set()
            return dict(info,status=message)
        except Exception as exc:return dict(info,status=type(exc).__name__)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:results=list(pool.map(fetch,jobs))
    audit={'date':date,'tier':usage.get('tier'),'remaining_at_start':usage.get('remaining'),
           'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'unique_connections':{k:len(v) for k,v in people.items()},'requested':len(jobs),
           'statuses':dict(collections.Counter(str(r['status']) for r in results)),'results':results,
           'provider_predictions_used':False}
    (out/'collection_audit.json').write_text(json.dumps(audit,indent=2));return audit

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ['inputs','cards','latest','output-dir','date']:parser.add_argument('--'+arg,required=True)
    args=parser.parse_args()
    audit=collect(pd.read_csv(args.inputs),args.cards,pd.read_csv(args.latest,dtype={'market_id':str}),args.output_dir,args.date)
    print(json.dumps({'requested':audit['requested'],'statuses':audit['statuses']}))
