"""Offline issue240 archive audit and chronological fixed-model sensitivities.

No provider requests, model fit, pickle load or production configuration writes.
Exchange scheduled-off odds are explicitly NOT bookmaker fixed-win history.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd
from operations.audit.price_policy_study import fixed_predictors,minimal,read_months,DayBootstrap

BANDS=((10,20),(20,40),(40,60),(60,float('inf')))

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def serial_csv(path,rows):
    if not rows:return
    with Path(path).open('w') as file:
        writer=csv.DictWriter(file,list(rows[0]));writer.writeheader();writer.writerows(rows)

def archived(forecast,temperature):
    coverage=[];known=[];contrast=[]
    for race in forecast['races']:
        active=race['data_completeness']['active_runners']
        for version,model in race['models'].items():
            seen={}
            for field in ('ranked_runners','ordered_selections','roughies','best_bets','best_chance'):
                values=model.get(field) or []
                for row in [values] if isinstance(values,dict) else values:
                    key=str(row['number']);value=(row['horse'],row['odds'],row['probability'])
                    if key in seen and seen[key]!=value:raise ValueError('Contradictory archived row')
                    seen[key]=value
            rows=[dict(number=k,horse=v[0],odds=v[1],probability=v[2]) for k,v in seen.items()]
            complete=(len(rows)==active and active>0 and math.isclose(sum(r['probability'] for r in rows),1,abs_tol=1e-6))
            coverage.append(dict(meeting=race['meeting'],race=race['race'],version=version,status=model['status'],
                active_runners=active,preserved_runners=len(rows),unpreserved_runners=active-len(rows),
                longshots_preserved=sum(r['odds']>=10 for r in rows),complete_ranked_field=complete,
                saved_watches=len(model.get('roughies',[])),
                observed_book_lower_bound_pct=100*sum(1/r['odds'] for r in rows),
                full_book_pct=100*sum(1/r['odds'] for r in rows) if complete else None,
                exclusion_scope='Raw V6 watches empty implies no scored $10+ runner passed p*odds>1; missing identities/probabilities cannot be recovered' if version=='V6' and model['status']=='SCORED' and not model.get('roughies') else
                 'Raw V7 watches empty implies every scored $10+ runner failed p>=0.06 or p*odds>1, possibly both; individual cause unavailable' if version=='V7' and model['status']=='SCORED' and not model.get('roughies') else ';'.join(model.get('no_bet_reasons',[]))))
            total=sum(1/r['odds'] for r in rows) if complete else None
            for row in rows:
                p,odds=row['probability'],row['odds'];market=(1/odds)/total if total else None
                known.append(dict(meeting=race['meeting'],race=race['race'],version=version,**row,
                    market_probability=market,predictive_advantage=None if market is None else p-market,
                    numerical_ev=p*odds-1,above_10=odds>=10,
                    floor_pass=version!='V7' or p>=.06,positive_EV=p*odds>1,
                    price_timestamp=None,full_market_unavailable=not complete,betting_authorised=False))
            # Exact within-race feature-score contrasts do not need the omitted
            # full normaliser: T*log(p_i/p_j)-log((1/o_i)/(1/o_j)).
            if model['status']=='SCORED' and rows:
                first=rows[0];t=1 if version=='V6' else temperature
                for row in rows[1:]:
                    correction=t*math.log(row['probability']/first['probability'])-math.log(first['odds']/row['odds'])
                    contrast.append(dict(meeting=race['meeting'],race=race['race'],version=version,
                        first_number=first['number'],other_number=row['number'],temperature=t,
                        feature_logit_contrast=correction,feature_odds_multiplier=math.exp(correction)))
    summary=dict(run_id=forecast['run_id'],capture=forecast['captured_at'],valid_until=forecast['valid_until'],
        unique_provider_races=forecast['coverage']['provider_races'],accepted_races=len(forecast['races']),
        rejected_races=forecast['coverage']['provider_skips'],
        no_individual_exclusion_invented=True,provider_credit_calls=0,coverage=coverage,
        models={v:dict(scored_races=sum(r['status']=='SCORED' for r in coverage if r['version']==v),
            active_input_runners=sum(r['active_runners'] for r in coverage if r['version']==v and r['status']=='SCORED'),
            saved_runners=sum(r['preserved_runners'] for r in coverage if r['version']==v),
            missing_scored_runners=sum(r['unpreserved_runners'] for r in coverage if r['version']==v and r['status']=='SCORED'),
            saved_longshots=sum(r['longshots_preserved'] for r in coverage if r['version']==v),
            saved_roughie_watches=sum(r['saved_watches'] for r in coverage if r['version']==v),
            max_saved_pair_feature_logit_contrast=max([abs(x['feature_logit_contrast']) for x in contrast if x['version']==v] or [0])) for v in ('V6','V7')},
        limitation='Only archived rows were audited. No all-runner market rank, quote freshness, $10+ count or individual missing-runner exclusion can be inferred from trimmed ticket rows.')
    return summary,known,contrast


def place_labels(directory,months):
    frames=[];pins=json.loads((Path(__file__).parent/'Monty_Betfair_Monthly_Recovery.json').read_text())
    for month in months:
        path=Path(directory)/(month+'.csv')
        if digest(path)!=pins[month]['source_sha256']:raise ValueError('Historical place source pin mismatch')
        rows=pd.read_csv(path,dtype=str,keep_default_na=False,usecols=['WIN_MARKET_ID','SELECTION_ID','PLACE_RESULT'])
        rows=rows.drop_duplicates()
        bad=set(rows.loc[rows.duplicated(['WIN_MARKET_ID','SELECTION_ID'],keep=False),'WIN_MARKET_ID'])
        rows=rows.loc[~rows.WIN_MARKET_ID.isin(bad)]
        frames.append(rows)
    return pd.concat(frames,ignore_index=True)


def join_places(data,labels):
    # Labels are settlement-only; never available to predictor construction.
    joined=data.merge(labels,on=['WIN_MARKET_ID','SELECTION_ID'],how='left',validate='one_to_one')
    if len(joined)!=len(data):raise ValueError('Place merge count drift')
    return joined


def softmax(logits,ids):
    codes=pd.factorize(np.asarray(ids))[0];maxima=np.full(codes.max()+1,-np.inf);np.maximum.at(maxima,codes,logits)
    value=np.exp(logits-maxima[codes]);return value/np.bincount(codes,weights=value)[codes]


def sensitivities(predictions,ids,temperature):
    market=predictions['market'];result=dict(predictions)
    for name in ('v6','v7'):
        t=1 if name=='v6' else temperature
        # log(p)*T-log(market) recovers correction up to a race constant,
        # which cancels in softmax. It does NOT identify a form-only model.
        correction=t*np.log(predictions[name])-np.log(market)
        for strength in (0,.5,1.5):
            result[f'{name}_research_form_scale_{strength}']=softmax((np.log(market)+strength*correction)/t,ids)
        if name=='v7':result['v7_research_temperature_1']=softmax(np.log(market)+correction,ids)
    return result


def metric(data,p,mask,boot):
    odds=data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy();y=data.y.to_numpy();count=int(mask.sum())
    out=dict(runners=count,races=int(data.loc[mask,'WIN_MARKET_ID'].nunique()))
    if not count:return out
    net=y*(1+.95*(odds-1))-1;gross_roi=y*odds-1
    eligible=data.PLACE_RESULT.isin(['WINNER','LOSER']).to_numpy() if 'PLACE_RESULT' in data else np.zeros(len(data),bool)
    placed=data.PLACE_RESULT.eq('WINNER').to_numpy() if 'PLACE_RESULT' in data else np.zeros(len(data),bool)
    known=mask&eligible;returns=(y*(1+.95*(odds-1)))[mask];wins=np.sort(returns[returns>0])[::-1]
    stress=net[mask].sum()-wins[:3].sum()
    out.update(wins=int(y[mask].sum()),win_strike=float(y[mask].mean()),mean_probability=float(p[mask].mean()),
        calibration_gap=float((y-p)[mask].mean()),calibration_gap_ci=boot.interval(mask,y-p),
        runner_brier=float(np.square(y-p)[mask].mean()),
        mean_market_probability=float(data.market_probability.to_numpy()[mask].mean()),
        mean_model_uplift=float((p-data.market_probability.to_numpy())[mask].mean()),
        mean_absolute_model_uplift=float(np.abs(p-data.market_probability.to_numpy())[mask].mean()),
        brier_minus_market=float((np.square(y-p)-np.square(y-data.market_probability.to_numpy()))[mask].mean()),
        quote_roi_no_fee=float(gross_roi[mask].mean()),quote_roi_assumed_5pct_winnings_fee=float(net[mask].mean()),
        quote_roi_day_bootstrap_95=boot.interval(mask,net),
        largest_winner_gross_return_share=float(wins[0]/returns.sum()) if len(wins) else None,
        roi_if_top3_winner_payouts_removed=float(stress/count),
        place_labelled_runners=int(known.sum()),place_strike=float(placed[known].mean()) if known.any() else None,
        place_definition='Settled Betfair PLACE market; not assumed top3; no place ROI without verified executable place quotes')
    return out


def evaluate(data,predictions,label):
    data=data.reset_index(drop=True);boot=DayBootstrap(data.date);odds=data.BEST_AVAIL_BACK_AT_SCHEDULED_OFF.to_numpy();wins=data.y.to_numpy()==1
    book=pd.Series(1/odds).groupby(data.WIN_MARKET_ID).transform('sum').to_numpy()
    output=[];strata=[];months=[];calibration=[]
    for name,p in predictions.items():
        for lower,upper in BANDS:
            band=(odds>=lower)&(odds<upper)
            # Unchanged eligibility is reported separately from no-floor research.
            policies={'all_runners':band,'unchanged_watch_policy':band&(book>=1)&(p*odds>1)&((p>=.06) if name.startswith('v7') else True),
                'research_positive_model_uplift_and_EV':band&(book>=1)&(p*odds>1)&(p>predictions['market']+1e-12)}
            for policy,mask in policies.items():output.append(dict(cohort=label,model=name,band=f'{lower}-{upper}',policy=policy,**metric(data,p,mask,boot)))
            if name not in ('market','v6','v7'):continue
            for dimension,labels in [('going',data.going.fillna('unknown').astype(str)),('class',data.RACE_TYPE.fillna('unknown').astype(str)),
                ('distance',pd.cut(data.DISTANCE,[-np.inf,1200,1600,2000,np.inf],right=False,labels=['<1200','1200-1599','1600-1999','2000+']).astype(str))]:
                for value in sorted(labels.unique()):
                    mask=band&(labels.to_numpy()==value)
                    if mask.any():strata.append(dict(cohort=label,model=name,band=f'{lower}-{upper}',dimension=dimension,value=value,**metric(data,p,mask,boot)))
        for month in ['ALL']+(sorted(data.date.str[:7].unique()) if name in ('market','v6','v7') else []):
            mask=np.ones(len(data),bool) if month=='ALL' else data.date.str.startswith(month).to_numpy();wm=mask&wins
            delta=np.log(predictions['market'])-np.log(p)
            groups=data.WIN_MARKET_ID
            rank=pd.Series(p).groupby(groups).rank(ascending=False,method='min').to_numpy()
            m_rank=data.market_probability.groupby(groups).rank(ascending=False,method='min').to_numpy()
            months.append(dict(cohort=label,month=month,model=name,races=int(wm.sum()),
                log_loss=float(-np.log(p[wm]).mean()),race_brier=float(np.square(p[mask]-wins[mask]).sum()/wm.sum()),
                paired_logloss_minus_market=float(delta[wm].mean()),paired_logloss_day_bootstrap95=boot.interval(wm,delta),
                mean_absolute_probability_difference=float(np.abs(p[mask]-predictions['market'][mask]).mean()),
                mean_absolute_rank_difference=float(np.abs(rank[mask]-m_rank[mask]).mean()),
                    paired_logloss_minus_frozen=float((np.log(predictions[name.split('_')[0]])-np.log(p))[wm].mean()) if name!='market' else 0.0,
                    paired_logloss_minus_frozen_ci=boot.interval(wm,np.log(predictions[name.split('_')[0]])-np.log(p)) if name!='market' else [0.0,0.0]))
        for lo,hi in ((0,.01),(.01,.025),(.025,.05),(.05,.1),(.1,.2),(.2,1.01)):
            mask=(odds>=10)&(p>=lo)&(p<hi)
            if mask.any():calibration.append(dict(cohort=label,model=name,probability_bin=[lo,hi],**metric(data,p,mask,boot)))
    return dict(cohort=label,races=int(data.WIN_MARKET_ID.nunique()),runners=len(data),dates=[data.date.min(),data.date.max()],
        bands=output,strata=strata,chronological_months=months,calibration=calibration)


def history(directory,v7,output):
    names,score,count=fixed_predictors(v7)
    raw=json.loads((Path(v7)/'v7/artifacts/fold_3_model.json').read_text());t=raw['temperature']
    data=read_months(Path(directory));data=data.loc[data.date.ge('2026-06-01')].reset_index(drop=True)
    months=['2026_06','2026_08','2026_09','2026_10']
    data=join_places(data,place_labels(directory,months))
    predictions=score(data,minimal(data,names));arms=sensitivities(predictions,data.WIN_MARKET_ID,t)
    later=evaluate(data,arms,'2026 sparse fixed-model chronological replay')
    root=Path(__file__).resolve().parents[2]/'monty_v6/results'
    full=pd.read_csv(root/'joined_development_runners.csv.gz',dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    selected=full.date.between('2025-06-01','2025-06-15').to_numpy();earlier=full.loc[selected].reset_index(drop=True)
    with np.load(root/'frozen_feature_matrix.npz',allow_pickle=False) as z:
        if z['names'].tolist()!=names or len(z['X'])!=len(full):raise ValueError('Frozen historical schema/row mismatch')
        matrix=z['X'][selected].copy()
    earlier=join_places(earlier,place_labels(directory,['2025_06']))
    earlier_predictions=score(earlier,matrix)
    earlier_result=evaluate(earlier,sensitivities(earlier_predictions,earlier.WIN_MARKET_ID,t),'2025 June original full inputs; previously exposed V7 fold3 test')
    result=dict(schema='monty.roughies.history.v1',frozen_artifact_hashes=count,refitted=False,
        price_type='BEST_AVAIL_BACK_AT_SCHEDULED_OFF exchange proxy, NOT historical named-bookmaker fixed-win odds',
        chronological_protocol='Only frozen fold3 and V6; monthly evaluation after model/calibration cutoff. No new expanding-window refits; fold1/fold2 trained artifacts unavailable.',
        expert_90_10_test='NOT RUN: no eligible timestamped complete-field expert archive; never substitute market for experts',
        fee_assumptions='Flat one-unit WIN-only simulation; gross and assumed5% winnings fee shown; no fills/stake limits/deductions/net-market fee proof',
        performance_status='RETROSPECTIVE SIMULATION, not independently settled prospective performance',
        later=later,original=earlier_result,
        data_limits=['2026 May/July excluded by existing source pins','2026 going and contextual form unavailable; frozen imputation retained','Source raw race-class labels are not retrospectively invented benchmark classes','Place label missingness retained; no fabricated top3 or place ROI','Alternative correction strengths predeclared exploratory sensitivities, not calibrated independent form models; no production recommendation'])
    write(output,result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['archive','history']);p.add_argument('--forecast',type=Path);p.add_argument('--months',type=Path);p.add_argument('--v7',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    if a.mode=='history':
        r=history(a.months,a.v7,a.output/'historical_results.json');print(json.dumps({'later_races':r['later']['races'],'original_races':r['original']['races'],'refitted':False}))
    else:
        f=json.loads(a.forecast.read_text());t=json.loads((a.v7/'v7/artifacts/fold_3_model.json').read_text())['temperature']
        summary,rows,contrasts=archived(f,t);summary['forecast_sha256']=digest(a.forecast)
        write(a.output/'archive_summary.json',summary);serial_csv(a.output/'preserved_runner_audit.csv',rows);serial_csv(a.output/'pairwise_feature_contrasts.csv',contrasts)
        print(json.dumps(summary['models']))
if __name__=='__main__':main()
