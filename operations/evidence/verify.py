"""Receipt-bound private decryption and numerical replay; no pickle or fitting."""
from datetime import datetime,timezone
from pathlib import Path
import argparse,io,json,stat,subprocess,zipfile
import numpy as np
from operations.evidence.store import encoded,sha,timestamp,write,public_metadata


def safe_archive(raw):
    z=zipfile.ZipFile(io.BytesIO(raw));names=z.namelist()
    if len(set(names))!=len(names) or len(names)>10000 or sum(i.file_size for i in z.infolist())>200_000_000:raise ValueError('Archive bounds/duplicates')
    for item in z.infolist():
        p=Path(item.filename)
        if p.is_absolute() or '..' in p.parts or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Unsafe archive member')
    if z.testzip() is not None:raise ValueError('ZIP CRC failure')
    return z

def replay_arrays(raw,model_bytes=None,version=None,expected_model_sha=None):
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        terms=z['transformed_terms'];weights=z['term_weights'];contributions=z['term_contributions']
        if model_bytes is not None:
            if sha(model_bytes)!=expected_model_sha:raise ValueError('Pinned frozen model digest mismatch')
            m=json.loads(model_bytes);names=m['input_feature_names'] if version=='V6' else m['names']
            active=m['numeric_feature_names'][:len(m['numeric_feature_names'])//2] if version=='V6' else [n for n,a in zip(names,m['active']) if a]
            term_names=m['numeric_feature_names'] if version=='V6' else active+[n+'_missing' for n in active]
            if names!=z['feature_names'].tolist() or term_names!=z['term_names'].tolist():raise ValueError('Feature schema mismatch')
            original=z['original_values'];finite=np.isfinite(original);medians=m['imputation_medians'] if version=='V6' else m['medians']
            filled=np.where(finite,original,np.array(medians));ix=[names.index(n) for n in active]
            expected_terms=np.column_stack([filled[:,ix],(~finite[:,ix]).astype(float)])
            expected_terms=(expected_terms-np.array(m['mean']))/np.array(m['scale'])
            selected=m['models'][m['selected']] if version=='V6' else m
            expected_weights=np.zeros(len(term_names));indices=[i for i,n in enumerate(term_names) if version!='V6' or n!='log_market_probability'];expected_weights[indices]=selected['weights']
            if not np.array_equal(z['observed'],finite) or not np.array_equal(z['missing_indicators'],~finite):raise ValueError('Missingness indicators differ')
            if not np.allclose(filled,z['imputed_values'],equal_nan=True,rtol=0,atol=0) or not np.allclose(terms,expected_terms,rtol=0,atol=1e-12) or not np.array_equal(weights,expected_weights):raise ValueError('Frozen preprocessing/weights differ')
            if float(z['temperature'])!=(1 if version=='V6' else m['temperature']):raise ValueError('Frozen temperature differs')
        if not np.allclose(terms*weights,contributions,rtol=0,atol=1e-12):raise ValueError('Term contribution mismatch')
        correction=contributions.sum(axis=1)
        if not np.allclose(correction,z['feature_correction'],rtol=0,atol=1e-12):raise ValueError('Feature correction mismatch')
        scores=(np.log(z['market_probability'])+correction)/float(z['temperature'])
        p=np.exp(scores-scores.max());p/=p.sum()
        if 'gross_point_expected_value' in z:
            if not np.allclose(z['gross_point_expected_value'],z['market_normalisation_edge']+z['model_edge_contribution'],rtol=0,atol=1e-12):raise ValueError('Market/model value decomposition differs')
            if not np.allclose(z['model_probability_uplift'],z['conditional_feature_probability_effect']+z['market_temperature_probability_effect'],rtol=0,atol=1e-12):raise ValueError('Calibration/conditional feature decomposition differs')
        error=float(np.max(np.abs(p-z['reported_probability'])))
        if error>1e-12:raise ValueError('Genuine model probability replay mismatch')
        return dict(runners=len(p),features=len(z['feature_names']),terms=len(weights),maximum_probability_difference=error,
                    cancelled_terms=int(z['fully_cancelled_terms'].sum()),no_model_fit=True)

def open_bundle(cipher,key,receipt_path,forecast_path,expected_receipt_sha,output,clock=None):
    clock=clock or datetime.now(timezone.utc);receipt_bytes=Path(receipt_path).read_bytes()
    if sha(receipt_bytes)!=expected_receipt_sha:raise ValueError('Externally anchored receipt hash mismatch')
    receipt=json.loads(receipt_bytes);forecast_bytes=Path(forecast_path).read_bytes();forecast=json.loads(forecast_bytes)
    if sha(forecast_bytes)!=receipt['forecast_sha256']:raise ValueError('Receipt/forecast mismatch')
    index=receipt['evidence']
    if index!=forecast['evidence'] or index.get('status') not in ('SEALED','SEALED_INCOMPLETE'):raise ValueError('Evidence binding unavailable')
    if clock>=timestamp(index['expires_at']):raise ValueError('Private retention expired; recovery refused')
    cipher_bytes=Path(cipher).read_bytes()
    if sha(cipher_bytes)!=index['cipher_sha256']:raise ValueError('Cipher digest mismatch')
    decrypted=subprocess.run(['openssl','cms','-decrypt','-binary','-inform','DER','-inkey',str(key)],input=cipher_bytes,capture_output=True)
    if decrypted.returncode:raise ValueError('Authenticated decryption failed')
    z=safe_archive(decrypted.stdout);manifest_bytes=z.read('manifest.json');manifest=json.loads(manifest_bytes)
    if sha(manifest_bytes)!=index['manifest_sha256']:raise ValueError('Manifest digest mismatch')
    prediction=json.loads(z.read('private/retention/prediction.json'))
    if forecast.get('delivery_visibility')=='PRIVATE_EVIDENCE_ONLY':
        if encoded(forecast)!=encoded(public_metadata(prediction,index)):raise ValueError('Public metadata/private prediction mismatch')
    else:
        public_prediction=dict(forecast);public_prediction.pop('evidence')
        if encoded(public_prediction)!=encoded(prediction):raise ValueError('Public/private predictions differ')
    if sha(encoded(prediction))!=manifest['prediction_sha256'] or index['prediction_sha256']!=manifest['prediction_sha256']:raise ValueError('Prediction evidence mismatch')
    if manifest['run_id']!=forecast['run_id'] or receipt['run_id']!=forecast['run_id']:raise ValueError('Run identity mismatch')
    if manifest['expires_at']!=index['expires_at']:raise ValueError('Retention metadata mismatch')
    expected={'manifest.json'}|{'private/'+row['path'] for row in manifest['files']}
    if set(z.namelist())!=expected:raise ValueError('Unexpected/missing evidence files')
    replays=[]
    for row in manifest['files']:
        raw=z.read('private/'+row['path'])
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise ValueError('Inner artifact integrity mismatch')
        if row['path'].endswith('/feature-audit.npz'):
            directory=Path(row['path']).parent;version=directory.name
            model_bytes=z.read('private/'+(directory/'frozen-model.json').as_posix())
            replays.append(dict(model=version,**replay_arrays(raw,model_bytes,version,forecast['models'][version]['model_sha256'])))
    output=Path(output).resolve();repo=Path(__file__).resolve().parents[2]
    if output==repo or repo in output.parents or output.exists():raise ValueError('New private recovery path outside repository required')
    output.mkdir(parents=True,mode=0o700)
    for row in manifest['files']:write(output/row['path'],z.read('private/'+row['path']))
    write(output/'evidence-manifest.json',manifest_bytes)
    return dict(run_id=manifest['run_id'],verified_files=len(manifest['files']),model_replays=replays,
                original_capture=manifest['original_capture'],complete=index['complete'],expires_at=index['expires_at'])

def expired_bundles(root,clock=None,apply=False):
    clock=clock or datetime.now(timezone.utc);result=[]
    root=Path(root)
    if root.is_symlink():raise ValueError('Symlink retention root rejected')
    for index_path in root.glob('*/evidence-sealed/evidence-index.json'):
        if any(p.is_symlink() for p in (index_path,index_path.parent,index_path.parent.parent)):continue
        index=json.loads(index_path.read_text());cipher=index_path.parent/'evidence.cms'
        if index.get('schema')!='monty.evidence-index.v1' or clock<timestamp(index['expires_at']) or not cipher.exists() or cipher.is_symlink():continue
        if sha(cipher.read_bytes())!=index['cipher_sha256']:raise ValueError('Do not purge an unverified changed archive')
        result.append(dict(path=str(cipher),cipher_sha256=index['cipher_sha256'],expired_at=index['expires_at'],deleted=apply))
        if apply:cipher.unlink()  # Preserve public receipt, index and audit of expiry.
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--cipher',required=True);p.add_argument('--key',required=True);p.add_argument('--receipt',required=True);p.add_argument('--forecast',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(open_bundle(a.cipher,a.key,a.receipt,a.forecast,a.receipt_sha256,a.output)))
if __name__=='__main__':main()
