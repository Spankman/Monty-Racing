"""Replay frozen probabilities without refitting or reading outcome labels."""
import json,pickle
from pathlib import Path
import numpy as np,pandas as pd
from .config import HERE
from .integrity import ArtifactError,verify_artifacts,validate_model_contract
from .model_math import probabilities

def score_features(X,feature_names,market_probabilities,market_ids,root=HERE):
    root=Path(root)
    verify_artifacts(root)
    model=json.loads((root/'results/frozen_model.json').read_text())
    active=validate_model_contract(model,feature_names)
    X=np.asarray(X,float);base=np.asarray(market_probabilities,float);g=pd.factorize(market_ids)[0]
    if X.ndim!=2 or X.shape[1]!=len(feature_names) or len(base)!=len(X) or len(g)!=len(X) or not len(X):raise ArtifactError('Input array dimensions mismatch')
    if (g<0).any() or not np.isfinite(base).all() or (base<=0).any():raise ArtifactError('Invalid race identities or market probabilities')
    if not np.allclose(np.bincount(g,weights=base),1,atol=1e-9,rtol=0):raise ArtifactError('Market probabilities must sum to one in each race')
    finite=np.isfinite(X);Xi=np.where(finite,X,np.asarray(model['imputation_medians']))
    idx=[list(feature_names).index(n) for n in active]
    Z=np.column_stack([Xi[:,idx],(~finite[:,idx]).astype(float)])
    Z=(Z-np.asarray(model['mean']))/np.asarray(model['scale'])
    selected=model['models'][model['selected']]
    if selected['kind']=='market':return base.copy()
    if selected['kind']=='linear':
        formidx=[i for i,n in enumerate(model['numeric_feature_names']) if n!='log_market_probability']
        return probabilities(np.log(base)+Z[:,formidx]@np.array(selected['weights']),g)
    if selected['kind']=='boost':
        import sklearn
        if model.get('sklearn_version')!=sklearn.__version__:raise ArtifactError('Boosting runtime version mismatch')
        # Integrity must pass before deserialising a research binary.
        with (root/'results/boosting_model.pkl').open('rb') as h:boost=pickle.load(h)
        if boost.n_features_in_!=Z.shape[1]:raise ArtifactError('Boosting feature dimensions mismatch')
        q=boost.predict_proba(Z)[:,1];q=q/np.bincount(g,weights=q)[g]
        blend=selected['blend'];return (1-blend)*base+blend*q
    raise ArtifactError('Unknown model kind')
