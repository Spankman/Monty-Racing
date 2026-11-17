"""Offline integration of dated verified metadata and separate Pro statistics."""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
import race_day
from betfair_metadata import match_metadata,jockey_change
from monty.normalization import normal
from monty.integrity import verify_artifacts,validate_model_contract

def stats_file(cache,kind,name,window):
    return Path(cache)/(kind+'-'+hashlib.sha256(name.encode()).hexdigest()[:20]+'-'+str(window)+'.json')

def supplement(binding,cache):
    out={k:binding[k] for k in ['meeting','race','number','horse']}
    for kind in ['jockey','trainer']:
        name=binding.get(kind)
        for window in [90,365]:
            prefix=f'support_{kind}_{window}d_'
            path=stats_file(cache,kind,name,window) if name else None
            if path is None or not path.exists():out[prefix+'status']='unavailable';continue
            record=json.loads(path.read_text());data=record['data'];recent=data.get('recentStats') or {}
            if data.get('isAmbiguous') or normal(data.get(kind+'Name',''))!=normal(name):
                out[prefix+'status']='identity_unverified';continue
            if recent.get('windowDays')!=window:out[prefix+'status']='window_unverified';continue
            out[prefix+'status']='available';out[prefix+'captured_at_utc']=record['captured_at_utc']
            out[prefix+'name']=data[kind+'Name']
            for source,target in [('totalStarts','starts'),('totalWins','wins'),('overallWinRate','win_rate'),('overallPlaceRate','place_rate')]:
                v=recent.get(source)
                if isinstance(v,(int,float)) and not isinstance(v,bool) and np.isfinite(v):out[prefix+target]=v
    return out

def enrich(inputs,history,latest,bindings,observations,cache):
    """Only one exact V6 input is added: verified last-start jockey change."""
    result=inputs.copy();cache=Path(cache);matched={};metadata_audit=[];changes=[]
    binding_map={(b['meeting'],int(b['race']),int(b['number'])):b for b in bindings}
    venue_names={'SANDOWN':'Sandown','WARWICK-FARM':'Warwick Farm','DOOMBEN':'Doomben','GAWLER':'Gawler','BELMONT':'Belmont'}
    tab={}
    for observation in observations:
        pieces=observation['url'].split('/racing/')[1].split('/')
        for r in observation['runners']:
            tab[(venue_names[pieces[1]],int(pieces[4]),int(r['id'].split('-')[-1]))]=r['name']
    for market in latest.market_id.astype(str).unique():
        path=cache/('market-'+market+'.json')
        if not path.exists():metadata_audit.append({'market':market,'status':'unavailable'});continue
        rows=history[history.WIN_MARKET_ID.astype(str)==market]
        try:
            data=json.loads(path.read_text())['data'];accepted,extras=match_metadata(rows,data)
            matched[market]=accepted
            metadata_audit.append({'market':market,'status':'matched','retained_runners':len(accepted),'extra_entries_ignored':len(extras)})
        except (ValueError,KeyError) as e:metadata_audit.append({'market':market,'status':'rejected','reason':str(e)})
    latest_map={(r.meeting,int(r.race),int(r.number)):r for r in latest.itertuples()}
    for idx,current in result.iterrows():
        key=(current.meeting,int(current.race),int(current.number));entry=latest_map.get(key)
        if entry is None:continue
        binding=binding_map[key]
        if normal(binding['horse'])!=normal(current.horse):raise ValueError('Current source binding mismatch')
        if normal(entry.horse)!=normal(current.horse):raise ValueError('Latest-start horse binding mismatch')
        eligible=history[(history.WIN_MARKET_ID.astype(str)==str(entry.market_id)) & (history.SELECTION_ID.astype(str)==str(entry.selection_id))]
        if len(eligible)!=1 or eligible.iloc[0].date!=entry.verified_last_date:
            raise ValueError('Latest-start retained date/identity mismatch')
        old=matched.get(str(entry.market_id),{}).get(str(entry.selection_id))
        if not old:continue
        value=jockey_change(old.get('jockeyName'),binding.get('jockey'),tab.get(key,''))
        if value is not None:
            result.loc[idx,'jockey_changed']=value
            changes.append({'meeting':key[0],'race':key[1],'number':key[2],'horse':current.horse,
                'prior_date':entry.verified_last_date,'market_id':str(entry.market_id),
                'prior_jockey':old.get('jockeyName'),'current_jockey':binding.get('jockey'),'jockey_changed':value})
    return result,pd.DataFrame([supplement(b,cache) for b in bindings]),metadata_audit,changes

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['inputs','history','latest','bindings','observations','cache','output-dir']:p.add_argument('--'+arg,required=True)
    a=p.parse_args();out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    history=pd.read_csv(a.history,dtype={'WIN_MARKET_ID':str,'SELECTION_ID':str})
    latest=pd.read_csv(a.latest,dtype={'market_id':str,'selection_id':str})
    d,s,m,c=enrich(pd.read_csv(a.inputs),history,latest,json.loads(Path(a.bindings).read_text()),json.loads(Path(a.observations).read_text()),a.cache)
    d.to_csv(out/'inputs.csv',index=False);s.to_csv(out/'connections_supplement.csv',index=False)
    pd.DataFrame(c).to_csv(out/'jockey_change_audit.csv',index=False)
    (out/'metadata_audit.json').write_text(json.dumps(m,indent=2))
    scored=race_day.run(out/'inputs.csv',out/'scores.csv')
    model=json.loads((race_day.ROOT/'results/frozen_model.json').read_text());active=validate_model_contract(model,model['input_feature_names'])
    counts=[sum(f in ['log_market_probability','log_field_size'] or f in r and pd.notna(r[f]) for f in active) for r in d.to_dict('records')]
    report={'runners':len(d),'races':scored.groupby(['meeting','race']).ngroups,'jockey_change_features_added':len(c),
        'matched_markets':sum(r['status']=='matched' for r in m),'active_feature_range':[min(counts),max(counts)],
        'supplement_statuses':{col:s[col].value_counts().to_dict() for col in s if col.endswith('_status')},
        'original_artifacts_verified':verify_artifacts(race_day.ROOT),'provider_predictions_used':False,'retrained':False,
        'provisional_run_authorized':True,'statistics_substituted_for_residuals':False,
        'odds_source':'Saved TAB fixed win capture 17 November 18:24–18:29 Queensland; not refreshed in this rerun'}
    (out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
