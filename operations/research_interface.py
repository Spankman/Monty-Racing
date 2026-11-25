"""Research-only mathematical contracts. No learners fitted or production hook.

Benter-style log combination is a formula, not a claimed methodology replication.
Feature-only counterfactuals from market-conditional V6/V7 are not form models.
"""
from dataclasses import dataclass
from datetime import date,datetime
from pathlib import Path
import hashlib,json
from typing import Protocol
import numpy as np
import pandas as pd


class IndependentFormLearner(Protocol):
    """External research implementation; never automatically selected by Monty.
    Supply verified as-of nonmarket matrices and earlier-labelled whole races.
    Do not reuse conditional V6/V7 correction as independent form predictions.
    """
    def fit(self,features,labels,races):...
    def predict_proba(self,features,races):...
    def save(self,path):...


def distribution(p,races):
    p=np.asarray(p,float);g=pd.factorize(np.asarray(races))[0]
    if len(p)!=len(g) or not len(g) or (g<0).any() or not np.isfinite(p).all() or (p<=0).any() or not np.allclose(np.bincount(g,weights=p),1,atol=1e-10,rtol=0):raise ValueError('Complete positive race distributions required')
    return p,g

def normalise(scores,races):
    g=pd.factorize(np.asarray(races))[0];scores=np.asarray(scores,float)
    if not len(g) or len(g)!=len(scores) or (g<0).any() or not np.isfinite(scores).all():raise ValueError('Invalid race logits')
    maxima=np.full(g.max()+1,-np.inf);np.maximum.at(maxima,g,scores);p=np.exp(scores-maxima[g]);return p/np.bincount(g,weights=p)[g]

def market_baseline(odds,races):
    odds=np.asarray(odds,float)
    if not np.isfinite(odds).all() or (odds<=1).any():raise ValueError('Complete valid odds required')
    return normalise(-np.log(odds),races)

@dataclass(frozen=True)
class ModelProvenance:
    training_end:str
    calibration_end:str
    independent_of_current_market:bool
    artifact_sha256:str
    research_only:bool=True
    def validate(self,test_start):
        for d in (self.training_end,self.calibration_end,test_start):date.fromisoformat(d)
        if not self.research_only or not self.training_end<self.calibration_end<test_start:raise ValueError('Strict earlier training/calibration and research-only provenance required')
        if len(self.artifact_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.artifact_sha256):raise ValueError('Model artifact hash required')

def benter_combination(form,market,races,*,form_coefficient,market_coefficient,provenance,test_start):
    provenance.validate(test_start)
    if not provenance.independent_of_current_market:raise ValueError('Conditional feature correction cannot stand in for independent form predictions')
    form,g=distribution(form,races);market,_=distribution(market,races)
    if not np.isfinite([form_coefficient,market_coefficient]).all():raise ValueError('Finite frozen research combination coefficients required')
    return normalise(form_coefficient*np.log(form)+market_coefficient*np.log(market),races)

def adaptive_combination(form,market,races,*,weights,provenance,test_start):
    provenance.validate(test_start)
    if not provenance.independent_of_current_market:raise ValueError('Independent form provenance required')
    form,g=distribution(form,races);market,_=distribution(market,races);w=np.asarray(weights,float)
    if w.shape!=form.shape or not np.isfinite(w).all() or ((w<0)|(w>1)).any():raise ValueError('One bounded earlier-validated weight per row required')
    for group in set(g):
        if len(np.unique(w[g==group]))!=1:raise ValueError('Race-wide weights required for coherent mixture')
    return w*form+(1-w)*market

def calibrate(p,races,temperature,provenance,test_start):
    provenance.validate(test_start);p,_=distribution(p,races)
    if not np.isfinite(temperature) or temperature<=0:raise ValueError('Earlier-fitted positive temperature required')
    return normalise(np.log(p)/temperature,races)

def ablate(matrix,names,columns):
    result=np.array(matrix,float,copy=True)
    if len(set(names))!=len(names) or result.ndim!=2 or result.shape[1]!=len(names):raise ValueError('Feature schema mismatch')
    for column in columns:result[:,names.index(column)]=np.nan
    return result

def independent_form_columns(names):
    forbidden={'log_market_probability','market_probability','odds','fixed_win_odds','price','WIN_BSP','WIN_RESULT','PLACE_RESULT','y','winner','result'}
    if any(n in forbidden or n.startswith(('market_','log_market_','fixed_win_','WIN_','PLACE_','result_')) for n in names):raise ValueError('Current market/target labels excluded from independent form inputs')
    return tuple(names)

def walk_forward(rows,folds):
    """Whole-race/date split masks; labels remain outside feature matrices."""
    race_dates={}
    for r in rows:
        date.fromisoformat(r['date'])
        if race_dates.setdefault(r['race_id'],r['date'])!=r['date']:raise ValueError('Race spans dates')
        if r.get('features_verified_asof') is not True:raise ValueError('Feature availability provenance unverified')
        available=datetime.fromisoformat(r['feature_available_at'].replace('Z','+00:00'));jump=datetime.fromisoformat(r['scheduled_start'].replace('Z','+00:00'))
        if available.tzinfo is None or jump.tzinfo is None or available>=jump:raise ValueError('Unknown/future feature availability')
    output=[]
    for f in folds:
        for key in ('train_end','calibration_start','calibration_end','test_start','test_end'):date.fromisoformat(f[key])
        if not f['train_end']<f['calibration_start']<=f['calibration_end']<f['test_start']<=f['test_end']:raise ValueError('Chronology/embargo violation')
        masks=dict(train=[],calibration=[],test=[])
        for i,r in enumerate(rows):
            day=r['date']
            role='train' if day<=f['train_end'] else 'calibration' if f['calibration_start']<=day<=f['calibration_end'] else 'test' if f['test_start']<=day<=f['test_end'] else None
            if role in ('train','calibration') and (not r.get('result_verified') or r.get('result_available_date','9999-12-31')> (f['train_end'] if role=='train' else f['calibration_end'])):raise ValueError('Outcome unavailable at fit/calibration cutoff')
            if role:masks[role].append(i)
        output.append(dict(fold=dict(f),**masks))
    return output

def record_experiment(path,record):
    required={'experiment_id','code_commit','input_sha256','status','protocol','results_sha256','limitations'}
    if not required<=set(record) or record['status'] not in ('SUCCESS','NULL','NEGATIVE','BLOCKED'):raise ValueError('Complete research record required')
    if record.get('production_approved'):raise ValueError('Research interface cannot approve production')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(record,f,indent=2,allow_nan=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_verified_evidence(directory,clock=None):
    """Research reader for a receipt-verified private recovery, not public JSON.

    Does not invent results, horse identities, as-of historical validity or an
    independent form predictor. Work must join authenticated outcomes separately.
    """
    from operations.evidence.store import timestamp,sha
    from datetime import datetime,timezone
    root=Path(directory).resolve();m=json.loads((root/'evidence-manifest.json').read_text());clock=clock or datetime.now(timezone.utc)
    if clock>=timestamp(m['expires_at']):raise ValueError('Private evidence retention expired')
    arrays=[]
    for item in m['files']:
        path=(root/item['path']).resolve()
        if root not in path.parents or path.is_symlink() or sha(path.read_bytes())!=item['sha256']:raise ValueError('Private evidence integrity/path failure')
        if path.name=='feature-audit.npz':
            with np.load(path,allow_pickle=False) as z:
                arrays.append(dict(model=path.parent.name,path=item['path'],numbers=z['numbers'].tolist(),
                    feature_names=z['feature_names'].tolist(),original_values=z['original_values'].copy(),
                    observed=z['observed'].copy(),imputed_values=z['imputed_values'].copy(),
                    model_probability=z['model_probability'].copy(),market_probability=z['market_probability'].copy(),
                    term_names=z['term_names'].tolist(),term_contributions=z['term_contributions'].copy(),
                    features_verified_asof=False,independent_form_predictions=False,
                    warning='Verified numerical replay does not verify original historical publication vintage, provider fields or betting value.'))
    decisions=json.loads((root/'retention/declarations-and-decisions.json').read_text())
    return dict(schema='monty.research-evidence.v1',run_id=m['run_id'],source=m['source'],expires_at=m['expires_at'],
        arrays=arrays,decisions=decisions,result_labels=None,production_approved=False,
        restriction='Private licensed research only; no automatic cohort admission or result fabrication')
