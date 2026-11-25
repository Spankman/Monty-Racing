"""Immutable prospective comparison records; no betting approval or model fitting."""
import hashlib,json,math
from datetime import timedelta
from pathlib import Path
from monty_operations import timestamp,write,MAX_AGE_SECONDS,utcnow


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def freeze(forecast, race, verification, path, now=None):
    now=now or utcnow();captured=timestamp(race['captured_at']);jump=timestamp(race['scheduled_start'])
    if not (0 <= (now-captured).total_seconds() < MAX_AGE_SECONDS and now<jump):
        raise ValueError('Only current pre-jump records can be frozen prospectively')
    models={}
    for version in ('V6','V7'):
        model=race['models'][version]
        if model['status']!='SCORED' or timestamp(model['decision_at'])>=jump or model.get('expired_at_completion'):
            raise ValueError('Both genuine pre-jump models required')
        rows=model['ranked_runners']
        if not rows or not math.isclose(sum(r['probability'] for r in rows),1,abs_tol=1e-9):raise ValueError('Invalid model distribution')
        models[version]=dict(research_only=version=='V7',model=forecast['models'][version],
                            decision_at=model['decision_at'],rows=rows,input_evidence=model.get('input_evidence'))
    a,b=models['V6']['rows'],models['V7']['rows']
    key=lambda rs:{r['number']:(r['horse'],r['odds']) for r in rs}
    if key(a)!=key(b):raise ValueError('Different model fields or odds')
    total=sum(1/r['odds'] for r in a)
    baseline=[dict(number=r['number'],horse=r['horse'],odds=r['odds'],probability=(1/r['odds'])/total) for r in a]
    from urllib.parse import urlsplit
    sources=verification.get('sources',[])
    authority={'www.racingqueensland.com.au','racing.racingnsw.com.au','www.racingaustralia.horse','www.racing.com','www.rwwa.com.au','www.racingsa.com.au','www.tasracing.com.au'}
    operators={'www.tab.com.au','www.sportsbet.com.au','www.tabtouch.com.au'}
    roles=set()
    for source in sources:
        try:
            host=urlsplit(source['source_url']).hostname
            fresh=0 <= (now-timestamp(source['observed_at'])).total_seconds() < MAX_AGE_SECONDS
            same_race=source.get('date')==forecast['date'] and str(source.get('meeting','')).casefold()==race['meeting'].casefold() and str(source.get('race'))==str(race['race'])
            valid=same_race and source.get('status')=='CAPTURED' and source.get('http_status')==200 and fresh and len(source.get('sha256',''))==64
            if valid and host in authority:roles.add('authority')
            if valid and host in operators:roles.add('operator')
        except (ValueError,TypeError,KeyError):pass
    admitted=all(verification.get(k) is True for k in ('race_verified','fixed_win_verified','emergency_status_verified')) and roles=={'authority','operator'}
    record=dict(schema='monty.prospective.v1',run_id=forecast['run_id'],date=forecast['date'],
        meeting=race['meeting'],race=race['race'],country=race['country'],captured_at=race['captured_at'],
        frozen_at=now.isoformat(),scheduled_start=race['scheduled_start'],
        provider_snapshot_sha256=forecast['provider_snapshot_sha256'],shared_model_input_sha256=race['shared_model_input_sha256'],
        verification=verification,cohort='VERIFIED PROSPECTIVE' if admitted else 'UNVERIFIED DIAGNOSTIC — NOT ADMITTED',
        cohort_admitted=admitted,models=models,market_baseline=baseline,
        market_integrity=race.get('market_integrity'),betting_authorised=False)
    if Path(path).exists() or Path(str(path)+'.receipt.json').exists():raise FileExistsError('Immutable prospective record already exists')
    write(path,record)
    receipt=dict(record_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),record_path=Path(path).name,
                 run_id=record['run_id'],cohort_admitted=admitted)
    write(str(path)+'.receipt.json',receipt)
    return record


def settle(record_path, result, output, now=None):
    """Result adapter must supply independently captured official lineage + digest.

    Research-only caller-authenticated contract: CLI does not accept a bare winner.
    No dividend estimates, stakes, ROI or retrospective promotion into the cohort.
    """
    now=now or utcnow();p=Path(record_path);receipt=json.loads(Path(str(p)+'.receipt.json').read_text())
    if hashlib.sha256(p.read_bytes()).hexdigest()!=receipt['record_sha256']:raise ValueError('Forecast integrity mismatch')
    record=json.loads(p.read_text());jump=timestamp(record['scheduled_start'])
    if not record['cohort_admitted']:raise ValueError('Unverified diagnostics excluded from prospective cohort')
    if not (jump<=timestamp(result['observed_at'])<=now and result.get('official') is True and result.get('status')=='FINAL'):
        raise ValueError('Independently observed final post-jump official result required')
    from urllib.parse import urlsplit
    allowed={'www.racingqueensland.com.au','racing.racingnsw.com.au','www.racingaustralia.horse','www.racing.com','www.rwwa.com.au','www.racingsa.com.au','www.tasracing.com.au'}
    if urlsplit(result['source_url']).scheme!='https' or urlsplit(result['source_url']).hostname not in allowed or len(result.get('source_sha256',''))!=64:
        raise ValueError('Official result provenance missing')
    if any(str(result.get(k))!=str(record[k]) for k in ('date','country','meeting','race')):raise ValueError('Result race identity mismatch')
    runners={r['number']:r['horse'] for r in record['market_baseline']}
    if result.get('active_runners')!=runners or result.get('late_field_change') is not False:
        raise ValueError('Field change/unverified active result field; manual review required')
    winners=result['winners']
    if len(winners)!=1 or winners[0] not in runners:raise ValueError('Dead heat/invalid winner not supported')
    winner=winners[0]
    def metrics(rows):
        probs={r['number']:r['probability'] for r in rows}
        order=sorted(rows,key=lambda r:-r['probability'])
        return dict(log_loss=-math.log(probs[winner]),brier=sum((v-(n==winner))**2 for n,v in probs.items()),
                    winner_rank=next(i for i,r in enumerate(order,1) if r['number']==winner),top_pick_won=order[0]['number']==winner)
    scores={v:metrics(m['rows']) for v,m in record['models'].items()};scores['MARKET']=metrics(record['market_baseline'])
    out=dict(schema='monty.settlement.v1',forecast_sha256=receipt['record_sha256'],official_result=result,
             settled_at=now.isoformat(),metrics=scores,betting_authorised=False,
             limitation='One race is not evidence of predictive superiority; aggregate untouched prospective records')
    write(output,out)
    return out
