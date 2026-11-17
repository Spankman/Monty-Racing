"""Fail-closed checks for accidental artifact drift, not cryptographic authorship."""
import hashlib,json
from pathlib import Path
from .config import HERE

class ArtifactError(ValueError):pass

def verify_artifacts(root=HERE,manifest_name='artifact_hashes.json'):
    root=Path(root).resolve();manifest=root/manifest_name
    if not manifest.is_file():raise ArtifactError('Artifact manifest is missing')
    entries=json.loads(manifest.read_text())
    if not isinstance(entries,dict) or not entries:raise ArtifactError('Artifact manifest is empty or invalid')
    for name,expected in entries.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root):raise ArtifactError('Unsafe artifact path: '+name)
        if not p.is_file():raise ArtifactError('Missing artifact: '+name)
        digest=hashlib.sha256()
        with p.open('rb') as h:
            for b in iter(lambda:h.read(1024*1024),b''):digest.update(b)
        if digest.hexdigest()!=expected:raise ArtifactError('Artifact hash mismatch: '+name)
    return len(entries)

def validate_model_contract(model,feature_names):
    import numpy as np
    feature_names=list(feature_names)
    if len(set(feature_names))!=len(feature_names):raise ArtifactError('Duplicate feature names')
    required=model.get('input_feature_names')
    if required is None or feature_names!=required:raise ArtifactError('Input feature schema/order mismatch')
    numeric=model.get('numeric_feature_names',[]);n=len(numeric)
    if not n or n%2:raise ArtifactError('Invalid numeric feature contract')
    active=numeric[:n//2]
    if numeric[n//2:]!=[x+'_missing' for x in active] or any(x not in feature_names for x in active):raise ArtifactError('Invalid missing-indicator contract')
    med=np.asarray(model.get('imputation_medians',[]));mean=np.asarray(model.get('mean',[]));scale=np.asarray(model.get('scale',[]))
    if med.shape!=(len(feature_names),) or mean.shape!=(n,) or scale.shape!=(n,):raise ArtifactError('Scaler dimensions mismatch')
    if not all(np.isfinite(x).all() for x in [med,mean,scale]) or (scale<=0).any():raise ArtifactError('Non-finite or invalid scaling values')
    expected=[x for x in numeric if x!='log_market_probability']
    if model.get('linear_feature_names')!=expected:raise ArtifactError('Linear feature order mismatch')
    methods=model.get('models',{})
    if model.get('selected') not in methods:raise ArtifactError('Selected model missing')
    for name,m in methods.items():
        if m.get('kind')=='linear':
            w=np.asarray(m.get('weights',[]))
            if w.shape!=(len(expected),) or not np.isfinite(w).all():raise ArtifactError('Coefficient dimensions/values mismatch: '+name)
    return active

if __name__=='__main__':print('PASS:',verify_artifacts(),'artifact hashes')
