"""Audit actual model-input coverage by source without guessing feature equivalence.

Input: frozen_model.json and one or more normalized runner snapshots.
Each source is evaluated independently; this does not join horse identities,
claim FormFav/Krok API access, or establish predictive value.
"""
import argparse,json,math
from pathlib import Path

def audit(model_path,sources):
    model=json.loads(Path(model_path).read_text())
    features=model['input_feature_names']
    if len(features)!=len(set(features)):raise ValueError('Duplicate model features')
    result={'schema':'monty-source-feature-coverage-v1','model_features':len(features),'sources':{},
            'note':'Observed numeric model-input keys only; no inference from provider field names, no prediction accuracy claim.'}
    for label,path in sources.items():
        snap=json.loads(Path(path).read_text())
        runners=snap.get('runners')
        if not isinstance(runners,list) or not runners:raise ValueError('Missing runner records for '+label)
        identities=set()
        for row in runners:
            if not isinstance(row,dict):
                raise ValueError('Invalid runner row for '+label)
            identity=tuple(str(row.get(k,'')).strip().casefold() for k in ('meeting','race','number','horse'))
            if any(not x for x in identity):
                raise ValueError('Missing runner identity for '+label)
            if identity in identities:
                raise ValueError('Duplicate runner identity for '+label)
            identities.add(identity)
        counts={}
        for feature in features:
            counts[feature]=sum(1 for r in runners if isinstance(r,dict) and isinstance(r.get(feature),(int,float))
                and not isinstance(r.get(feature),bool) and math.isfinite(r[feature]))
        n=len(runners)
        result['sources'][label]={'runners':n,'identity_checked':True,'fully_observed_features':sorted(k for k,v in counts.items() if v==n),
          'partially_observed_features':sorted(k for k,v in counts.items() if 0<v<n),
          'unobserved_features':sorted(k for k,v in counts.items() if v==0),
          'observed_counts':counts,
          'mean_input_coverage':sum(counts.values())/(n*len(features))}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('model');p.add_argument('--source',action='append',required=True,help='label=normalized_snapshot.json')
    p.add_argument('--output',default='source_feature_coverage.json')
    a=p.parse_args();sources={}
    for item in a.source:
        if '=' not in item:raise SystemExit('Expected label=path')
        label,path=item.split('=',1)
        if not label or not path or label in sources:raise SystemExit('Invalid/duplicate source label')
        sources[label]=path
    result=audit(a.model,sources)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{'runners':v['runners'],'mean_input_coverage':v['mean_input_coverage']} for k,v in result['sources'].items()}))
