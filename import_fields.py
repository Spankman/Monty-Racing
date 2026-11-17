#!/usr/bin/env python3
"""Normalize independently obtained TAB-style CSV/JSON runner snapshots.
Does not fetch websites or assert completeness. Requires explicit race-level expected counts.
"""
import argparse,csv,json,datetime,re
from pathlib import Path
MODEL=Path(__file__).resolve().parent/'monty_v6/results/frozen_model.json'
FEATURE_NAMES=set(json.loads(MODEL.read_text())['input_feature_names'])
from pathlib import Path

ALIASES={
 'meeting':['meeting','track','venue','meeting_name'],
 'race':['race','race_number','race_no','raceNumber'],
 'number':['number','saddlecloth','saddlecloth_number','runner_number','tab_number'],
 'horse':['horse','horse_name','runner','runner_name','name'],
 'odds':['odds','win_odds','fixed_win','fixed_odds','win_price','price'],
 'scratched':['scratched','is_scratched','scratch','status'],
}
def pick(d,keys):
 for k in keys:
  if k in d and d[k] is not None:return d[k]
 return None
def scratched(v):
 return str(v).strip().lower() in ('1','true','yes','scratched','scr','withdrawn')
def read(path):
 if path.suffix.lower()=='.json':
  obj=json.loads(path.read_text())
  if isinstance(obj,dict):obj=obj.get('runners',obj.get('data'))
  if not isinstance(obj,list):raise ValueError('JSON must contain a runner list or {"runners": [...]}')
  return obj
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def convert(src,manifest,dst,report):
 rows=read(Path(src)); meta=json.loads(Path(manifest).read_text())
 # Expected active runner count per race is independently confirmed by operator.
 races=meta.get('races',[])
 expected={(str(x['meeting']).strip().upper(),str(x['race']).strip()):x for x in races}
 if not expected:raise ValueError('Manifest needs independently verified races with expected_active_runners')
 out=[];issues=[];seen=set();counts={k:0 for k in expected}
 for i,r in enumerate(rows,1):
  if not isinstance(r,dict):issues.append(f'row {i}: not an object');continue
  vals={k:pick(r,a) for k,a in ALIASES.items()}
  if any(vals[k] is None or str(vals[k]).strip()=='' for k in ['meeting','race','number','horse']):issues.append(f'row {i}: missing identity');continue
  key=(str(vals['meeting']).strip().upper(),str(vals['race']).strip())
  if key not in expected:issues.append(f'row {i}: race {key} absent from manifest');continue
  if scratched(vals['scratched']):continue
  ident=(key,str(vals['number']).strip())
  if ident in seen:issues.append(f'row {i}: duplicate runner {ident}');continue
  seen.add(ident)
  try:
   price=float(str(vals['odds']).replace('$','').strip())
   if not 1<price<float('inf'):raise ValueError()
  except (ValueError,TypeError):issues.append(f'row {i}: missing/invalid active runner odds');continue
  counts[key]+=1
  item={'meeting':str(vals['meeting']).strip(),'race':key[1],'number':ident[1], 'horse':str(vals['horse']).strip(),'odds':price}
  # Preserve V6 feature columns without trusting arbitrary metadata as numeric.
  for feature in FEATURE_NAMES:
   if feature in r and r[feature] not in (None,''):
    try:item[feature]=float(r[feature])
    except (ValueError,TypeError):issues.append(f'row {i}: invalid numeric V6 feature {feature}')
  out.append(item)
 for key,m in expected.items():
  n=m.get('expected_active_runners')
  if not isinstance(n,int) or n<2:issues.append(f'{key}: expected_active_runners must be integer >=2')
  elif counts[key]!=n:issues.append(f'{key}: found {counts[key]} active priced runners, expected {n}')
 for field in ('captured_at','source'):
  if not meta.get(field):issues.append(f'manifest missing {field}')
 try:
  dt=datetime.datetime.fromisoformat(meta['captured_at'].replace('Z','+00:00'))
  if dt.tzinfo is None:issues.append('captured_at must have timezone offset')
 except (ValueError,KeyError,AttributeError):issues.append('invalid captured_at')
 audit={'ready':not issues,'source':meta.get('source'),'captured_at':meta.get('captured_at'),'races':len(expected),'active_runners':len(out),'issues':issues}
 Path(report).write_text(json.dumps(audit,indent=2)+'\n')
 if issues:
  Path(dst).unlink(missing_ok=True)
  return audit
 with Path(dst).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['meeting','race','number','horse','odds']+sorted({k for row in out for k in row if k in FEATURE_NAMES}));w.writeheader();w.writerows(out)
 return audit
if __name__=='__main__':
 p=argparse.ArgumentParser(description='Normalize supplied runner snapshots; no live fetching')
 p.add_argument('snapshot');p.add_argument('manifest');p.add_argument('--output',default='normalized_fields.csv');p.add_argument('--audit',default='intake_audit.json')
 a=p.parse_args();result=convert(a.snapshot,a.manifest,a.output,a.audit)
 print(json.dumps(result,indent=2));raise SystemExit(0 if result['ready'] else 2)
