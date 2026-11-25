"""Immutable prospective comparison records; no betting approval or model fitting."""
import hashlib,json,math,re
from urllib.parse import urlsplit
from pathlib import Path
from monty_operations import timestamp,write,MAX_AGE_SECONDS,utcnow


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


AUTHORITY_HOSTS = {'www.racingqueensland.com.au','racing.racingnsw.com.au','www.racingaustralia.horse',
                   'www.racing.com','www.rwwa.com.au','www.racingsa.com.au','www.tasracing.com.au'}
OPERATOR_HOSTS = {'www.tab.com.au','www.sportsbet.com.au','www.tabtouch.com.au'}


def source_host(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.username or parts.password or parts.port not in (None, 443):
        return None
    return parts.hostname


def is_sha256(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def admission_blockers(record):
    """Require independently reconciled evidence bound to the scored snapshot.

    Callers must authenticate the source bytes and reconcile their contents.
    Metadata and hashes here validate the record contract, not source authorship.
    """
    verification = record['verification']
    now = timestamp(record['frozen_at'])
    blockers = list(verification.get('blockers', []))
    for key in ('race_verified', 'fixed_win_verified', 'emergency_status_verified'):
        if verification.get(key) is not True:
            blockers.append(key+'_required')
    roles = set()
    for source in verification.get('sources', []):
        try:
            host = source_host(source['source_url'])
            age = (now-timestamp(source['observed_at'])).total_seconds()
            same_race = (source.get('date') == record['date']
                         and str(source.get('meeting','')).casefold() == record['meeting'].casefold()
                         and str(source.get('race')) == str(record['race']))
            valid = (same_race and source.get('status') == 'CAPTURED' and source.get('http_status') == 200
                     and 0 <= age < MAX_AGE_SECONDS and is_sha256(source.get('sha256')))
            if valid and host in AUTHORITY_HOSTS:
                roles.add('authority')
            if valid and host in OPERATOR_HOSTS:
                roles.add('operator')
        except (ValueError, TypeError, KeyError):
            continue
    if roles != {'authority', 'operator'}:
        blockers.append('fresh_primary_authority_and_operator_evidence_required')
    market = record.get('market_integrity') or {}
    if (market.get('status') != 'EVIDENCE_REVIEW_REQUIRED' or market.get('warnings') != []
            or market.get('complete_price_vector') is not True
            or market.get('quote_timestamp_count') != len(record['market_baseline'])
            or len(market.get('bookmakers') or []) != 1):
        blockers.append('complete_current_nonquarantined_book_required')
    else:
        try:
            recorded_vector = {str(row['number']): (row['horse'], row['odds'])
                               for row in market['market_only_baseline']}
            frozen_vector = {str(row['number']): (row['horse'], row['odds'])
                             for row in record['market_baseline']}
            valid_book = (len(recorded_vector) == len(market['market_only_baseline']) == len(frozen_vector)
                          and recorded_vector == frozen_vector
                          and math.fsum(1/odds for _, odds in frozen_vector.values()) >= 1)
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            valid_book = False
        if not valid_book:
            blockers.append('market_audit_vector_mismatch_or_underround')
    history = verification.get('compatible_history') or {}
    if (history.get('verified') is not True or not is_sha256(history.get('crosswalk_sha256'))
            or not is_sha256(history.get('manifest_sha256'))
            or not is_sha256(record['shared_model_input_sha256'])
            or history.get('shared_model_input_sha256') != record['shared_model_input_sha256']):
        blockers.append('compatible_asof_history_attestation_required')
    return list(dict.fromkeys(blockers))


def freeze(forecast, race, verification, path, now=None):
    now=now or utcnow();captured=timestamp(race['captured_at']);jump=timestamp(race['scheduled_start'])
    if not (0 <= (now-captured).total_seconds() < MAX_AGE_SECONDS and now<jump):
        raise ValueError('Only current pre-jump records can be frozen prospectively')
    models={}
    for version in ('V6','V7'):
        model=race['models'][version]
        if (model['status'] != 'SCORED' or model.get('expired_at_completion')
                or not captured <= timestamp(model['decision_at']) <= now):
            raise ValueError('Both genuine pre-jump models required')
        rows = model['ranked_runners']
        if (not rows or len({r['number'] for r in rows}) != len(rows)
                or not all(type(r['probability']) in (int, float) and 0 < r['probability'] <= 1
                           and type(r['odds']) in (int, float) and math.isfinite(r['odds']) and r['odds'] > 1
                           for r in rows)
                or not math.isclose(sum(r['probability'] for r in rows), 1, rel_tol=0, abs_tol=1e-9)):
            raise ValueError('Invalid model distribution or market vector')
        models[version]=dict(research_only=version=='V7',model=forecast['models'][version],
                            decision_at=model['decision_at'],rows=rows,input_evidence=model.get('input_evidence'))
    a,b=models['V6']['rows'],models['V7']['rows']
    key=lambda rs:{r['number']:(r['horse'],r['odds']) for r in rs}
    if key(a)!=key(b):raise ValueError('Different model fields or odds')
    total=sum(1/r['odds'] for r in a)
    baseline=[dict(number=r['number'],horse=r['horse'],odds=r['odds'],probability=(1/r['odds'])/total) for r in a]
    record=dict(schema='monty.prospective.v1',run_id=forecast['run_id'],date=forecast['date'],
        meeting=race['meeting'],race=race['race'],country=race['country'],captured_at=race['captured_at'],
        frozen_at=now.isoformat(),scheduled_start=race['scheduled_start'],
        provider_snapshot_sha256=forecast['provider_snapshot_sha256'],shared_model_input_sha256=race['shared_model_input_sha256'],
        verification=verification,models=models,market_baseline=baseline,
        market_integrity=race.get('market_integrity'),betting_authorised=False)
    blockers = admission_blockers(record)
    admitted = not blockers
    record.update(cohort_admitted=admitted, admission_blockers=blockers,
                  cohort='VERIFIED PROSPECTIVE' if admitted else 'UNVERIFIED DIAGNOSTIC — NOT ADMITTED')
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
    if not record['cohort_admitted'] or admission_blockers(record):raise ValueError('Unverified diagnostics excluded from prospective cohort')
    if not (jump<=timestamp(result['observed_at'])<=now and result.get('official') is True and result.get('status')=='FINAL'):
        raise ValueError('Independently observed final post-jump official result required')
    if source_host(result['source_url']) not in AUTHORITY_HOSTS or not is_sha256(result.get('source_sha256')):
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
