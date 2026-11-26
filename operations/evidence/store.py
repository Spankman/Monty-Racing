"""Opt-in, licence-gated private evidence; no provider acquisition or model fit.

Artifacts are tamper-evident, not an external WORM guarantee. Public receipts
contain hashes/counts only. No private keys, credentials or raw data in Git.
"""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import hashlib,json,os,re,stat,subprocess,tempfile,zipfile

HERE=Path(__file__).resolve().parent

def now():return datetime.now(timezone.utc)
def timestamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('Timezone required')
    return parsed.astimezone(timezone.utc)
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open('xb') as f:f.write(data)
    path.chmod(0o600)
def no_secrets(value):
    """Reject rather than silently edit an allegedly original source snapshot."""
    if isinstance(value,dict):
        for key,item in value.items():
            if re.search(r'^(?:x[-_]?)?(?:api[-_]?key|authorization|password|secret|access[-_]?token|refresh[-_]?token|cookie)$',str(key),re.I):
                raise ValueError('Credential-shaped field; evidence not retained')
            no_secrets(item)
    elif isinstance(value,list):
        for item in value:no_secrets(item)
    elif isinstance(value,str):
        if any(len(secret)>=12 and secret in value for name in ('KROK_API_KEY','PUNTERSEDGE_API_KEY','V6_ARCHIVE_TOKEN','GH_TOKEN','GITHUB_TOKEN') if (secret:=os.getenv(name,''))):
            raise ValueError('Configured credential detected; evidence not retained')
        if 'PRIVATE KEY-----' in value or re.search(r'https?://[^/\s]+:[^/@\s]+@|[?&](?:api_key|token|access_token|key)=',value,re.I):
            raise ValueError('Credential-shaped content; evidence not retained')

class Recorder:
    def __init__(self,output,run_id,source,policy=None,certificate=None,clock=now):
        self.output=Path(output).resolve();self.source=source if source in ('Krok','PuntersEdge','SIMULATED FIXTURE','HISTORICAL REPLAY') else 'UNRECOGNISED_PROVIDER';self.run_id=str(run_id);self.clock=clock
        self.root=self.output/'private'/'retention';self.raw_count=0;self.errors=[]
        self.policy=None;self.enabled=False;self.status='NOT_CONFIGURED';self.created=clock()
        self.checkpoint_count=0;self.checkpoint_errors=[]
        self.cert=Path(certificate or os.getenv('MONTY_EVIDENCE_CERTIFICATE') or HERE/'recipient-public.pem')
        if policy is None:policy=os.getenv('MONTY_EVIDENCE_POLICY') or None
        if policy is None:return
        try:
            p=json.loads(Path(policy).read_text()) if not isinstance(policy,dict) else dict(policy)
            allow=p['sources'].get(source,{})
            if (p.get('schema')!='monty.evidence-policy.v1' or p.get('enabled') is not True
                or allow.get('private_retention_permitted') is not True or not allow.get('permission_reference')
                or timestamp(allow['review_expires_at'])<=self.created):raise ValueError('Retention policy not approved/current')
            if type(p['retention_days']) is not int or not 1<=p['retention_days']<=7:raise ValueError('Retention outside reviewed cap')
            if type(p['max_bundle_bytes']) is not int or not 1<=p['max_bundle_bytes']<=100_000_000:raise ValueError('Bundle bound invalid')
            if not self.cert.is_file() or b'PRIVATE KEY' in self.cert.read_bytes():raise ValueError('Public-only recipient certificate required')
            self.policy=p;self.enabled=True;self.status='COLLECTING'
            write(self.output/'evidence-intent.json',encoded(dict(schema='monty.evidence-intent.v1',run_id=self.run_id,source=self.source,created_at=self.created.isoformat(),expires_at=(self.created+timedelta(days=p['retention_days'])).isoformat(),policy_sha256=sha(encoded(p)))))
        except Exception:
            self.enabled=False;self.policy=None;self.status='POLICY_OR_KEY_CONFIGURATION_BLOCKED'
    def checkpoint(self,stage):
        """Encrypted bounded best-effort crash evidence, never a completed forecast.
        No plaintext staging ZIP or external calls. Existing checkpoint files are
        exclusive; interrupted checkpoints are not silently used as predictions.
        """
        if not self.enabled:return
        try:
            if stage not in ('http_response','provider_captured','race_scored'):raise ValueError('Unknown checkpoint stage')
            base=self.output/'evidence-checkpoints';base.mkdir(mode=0o700,exist_ok=True)
            if self.checkpoint_count>=100:raise ValueError('Checkpoint count bound')
            entries=[];total=0
            for path in sorted((self.output/'private').rglob('*')):
                if path.is_symlink():raise ValueError('Checkpoint symlink')
                if not path.is_file():continue
                if path.suffix not in ('.json','.jsonl','.csv','.npz','.txt'):raise ValueError('Checkpoint artifact type')
                raw=path.read_bytes();total+=len(raw)
                if total>self.policy['max_bundle_bytes']:raise ValueError('Checkpoint size bound')
                if path.suffix=='.json':no_secrets(json.loads(raw))
                elif path.suffix=='.jsonl':
                    for line in raw.splitlines():no_secrets(json.loads(line))
                elif path.suffix in ('.csv','.txt'):no_secrets(raw.decode('utf-8'))
                entries.append((path.relative_to(self.output/'private').as_posix(),raw))
            manifest=dict(schema='monty.interrupted-evidence.v1',run_id=self.run_id,source=self.source,stage=stage,
                execution_status='IN_PROGRESS_NOT_A_FORECAST',created_at=self.clock().isoformat(),
                expires_at=(self.created+timedelta(days=self.policy['retention_days'])).isoformat(),
                policy_sha256=sha(encoded(self.policy)),files=[dict(path=n,sha256=sha(b),bytes=len(b)) for n,b in entries])
            import io
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('manifest.json',encoded(manifest))
                for name,raw in entries:z.writestr('private/'+name,raw)
            encrypted=subprocess.run(['openssl','cms','-encrypt','-aes-256-gcm','-binary','-outform','DER',str(self.cert)],input=buffer.getvalue(),capture_output=True,check=True).stdout
            if sum(p.stat().st_size for p in base.glob('*.cms'))+len(encrypted)>self.policy['max_bundle_bytes']:raise ValueError('Cumulative checkpoint bound')
            prefix=base/f'{self.checkpoint_count:04}'
            write(prefix.with_suffix('.cms'),encrypted)
            write(prefix.with_suffix('.json'),encoded(dict(schema='monty.checkpoint-index.v1',run_id=self.run_id,stage=stage,
                status='IN_PROGRESS_NOT_A_FORECAST',cipher_sha256=sha(encrypted),manifest_sha256=sha(encoded(manifest)),
                expires_at=manifest['expires_at'],files=len(entries))))
            self.checkpoint_count+=1
        except Exception:self.checkpoint_errors.append('checkpoint_capture_failed')
    def raw(self,body,endpoint):
        if not self.enabled:return
        try:
            if not endpoint.startswith(('/api/v1/racing/','/v1/racing/')):return
            value=json.loads(body);no_secrets(value)
            # Endpoint has no headers/query/token; the caller supplies an allowlisted path.
            if not re.fullmatch(r'/[A-Za-z0-9/_-]+',endpoint):raise ValueError('Unsafe endpoint metadata')
            target=self.root/f'raw-{self.raw_count:04}.json';write(target,body)
            write(self.root/f'raw-{self.raw_count:04}.meta.json',encoded(dict(endpoint=endpoint,observed_at=self.clock().isoformat(),sha256=sha(body))))
            self.raw_count+=1
            self.checkpoint('http_response')
        except Exception:self.errors.append('raw_capture_rejected')
    def snapshot(self,payload):
        if not self.enabled:return
        try:no_secrets(payload);write(self.root/'provider-snapshot.json',encoded(payload))
        except Exception:self.errors.append('canonical_snapshot_rejected')
    def seal(self,prediction):
        base=dict(schema='monty.evidence-index.v1',source=self.source,status=self.status,complete=False,
                  raw_http_pages=self.raw_count,errors=list(self.errors),encrypted_checkpoints=self.checkpoint_count,checkpoint_errors=list(self.checkpoint_errors))
        if not self.enabled:return base
        try:
            no_secrets(prediction)
            if not (self.root/'provider-snapshot.json').exists():self.errors.append('complete_canonical_provider_snapshot_missing')
            if self.source in ('Krok','PuntersEdge') and not self.raw_count:self.errors.append('original_http_bytes_not_supplied')
            source=json.loads((self.root/'provider-snapshot.json').read_text()) if (self.root/'provider-snapshot.json').exists() else {}
            write(self.root/'declarations-and-decisions.json',encoded(declaration_audit(source,prediction)))
            diagnostics=[json.loads(p.read_text()) for p in sorted((self.output/'private').glob('*/V[67]/feature-audit.json'))]
            expected=sum(m.get('status')=='SCORED' for r in prediction.get('races',[]) for m in r.get('models',{}).values())
            observed=len(list((self.output/'private').glob('*/V[67]/feature-audit.json')))
            if observed!=expected:self.errors.append('scored_model_feature_audit_count_mismatch')
            write(self.root/'prediction.json',encoded(prediction))
            write(self.root/'retention-policy.json',encoded(self.policy))
            original_manifest=HERE.parents[1]/'monty_v6/artifact_hashes.json'
            if original_manifest.exists():write(self.root/'original-v6-artifact-hashes.json',original_manifest.read_bytes())
            files=[];total=0
            for path in sorted((self.output/'private').rglob('*')):
                if path.is_symlink():raise ValueError('Evidence symlink rejected')
                if not path.is_file():continue
                if path.suffix not in ('.json','.jsonl','.csv','.npz','.txt'):raise ValueError('Unexpected private artifact type')
                data=path.read_bytes();total+=len(data)
                if total>self.policy['max_bundle_bytes']:raise ValueError('Bundle exceeds bound')
                if path.suffix in ('.json','.jsonl'):
                    if path.suffix=='.json':no_secrets(json.loads(data))
                    else:
                        for line in data.splitlines():no_secrets(json.loads(line))
                elif path.suffix in ('.csv','.txt'):
                    # Engine CSVs can contain sensitive-looking source strings.
                    no_secrets(data.decode('utf-8'))
                files.append(dict(path=path.relative_to(self.output/'private').as_posix(),sha256=sha(data),bytes=len(data)))
            expires=self.created+timedelta(days=self.policy['retention_days'])
            repo=HERE.parents[1]
            try:
                code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
                code_clean=subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=repo,capture_output=True).returncode==0
            except Exception:code_commit=None;code_clean=False
            manifest=dict(schema='monty.private-evidence.v1',source_code_commit=code_commit,source_checkout_clean=code_clean,run_id=self.run_id,source=self.source,
                created_at=self.created.isoformat(),expires_at=expires.isoformat(),files=files,
                policy_sha256=sha(encoded(self.policy)),prediction_sha256=sha(encoded(prediction)),
                source_models=prediction.get('models',{}),recipient_certificate_sha256=sha(self.cert.read_bytes()),
                original_capture='RAW_HTTP_PAGES_AND_CANONICAL_SNAPSHOT' if self.raw_count else 'CALLER_SUPPLIED_CANONICAL_SNAPSHOT_ONLY',
                limitation='Caller-supplied snapshots cannot reconstruct original HTTP bytes; no claim of missing pages',errors=self.errors)
            manifest_bytes=encoded(manifest)
            sealed=self.output/'evidence-sealed';sealed.mkdir(mode=0o700,exist_ok=False)
            with tempfile.TemporaryDirectory(dir=self.output) as temp:
                temp=Path(temp);archive=temp/'plain.zip';cipher=temp/'cipher.cms'
                with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
                    z.writestr('manifest.json',manifest_bytes)
                    for item in files:z.write(self.output/'private'/item['path'],'private/'+item['path'])
                subprocess.run(['openssl','cms','-encrypt','-aes-256-gcm','-binary','-outform','DER','-in',str(archive),'-out',str(cipher),str(self.cert)],check=True,capture_output=True)
                write(sealed/'evidence.cms',cipher.read_bytes())
            complete=not self.errors
            index=dict(base,status='SEALED' if complete else 'SEALED_INCOMPLETE',complete=complete,
                cipher_sha256=sha((sealed/'evidence.cms').read_bytes()),manifest_sha256=sha(manifest_bytes),
                prediction_sha256=manifest['prediction_sha256'],policy_sha256=manifest['policy_sha256'],recipient_certificate_sha256=manifest['recipient_certificate_sha256'],
                source_code_commit=code_commit,source_checkout_clean=code_clean,expires_at=expires.isoformat(),retention_days=self.policy['retention_days'],private_files=len(files),model_diagnostics=diagnostics,
                original_capture=manifest['original_capture'],artifact_name='monty-inference-evidence-'+str(os.getenv('GITHUB_RUN_ID',self.run_id))+'-'+str(os.getenv('GITHUB_RUN_ATTEMPT','1')),
                artifact_file='evidence.cms',errors=list(self.errors))
            artifact_name=os.getenv('MONTY_EVIDENCE_ARTIFACT_NAME')
            if artifact_name:
                if not re.fullmatch(r'[A-Za-z0-9_.-]{1,200}',artifact_name):raise ValueError('Invalid artifact identity')
                index['artifact_name']=artifact_name
            write(sealed/'evidence-index.json',encoded(index));return index
        except Exception:
            return dict(base,status='RETENTION_FAILED',errors=self.errors+['seal_failed'])


def declaration_audit(source,prediction):
    races={(r['meeting'].casefold(),str(r['race'])):r for r in prediction.get('races',[])}
    declared=[];scored=[]
    for meeting in source.get('data',[]) if isinstance(source,dict) else []:
        for race in meeting.get('races',[]):
            key=(str(meeting.get('venue','')).casefold(),str(race.get('number')));forecast=races.get(key)
            for row in race.get('runners',[]):
                number=str(row.get('number'));models={}
                for version in ('V6','V7'):
                    model=(forecast or {}).get('models',{}).get(version,{})
                    rank=next((r for r in model.get('ranked_runners',[]) if str(r['number'])==number),None)
                    reasons=list(model.get('no_bet_reasons',[]))
                    if row.get('is_scratched') is True:reasons.append('source_declared_scratched')
                    elif forecast is None:
                        matching=[s for s in prediction.get('coverage',{}).get('provider_skips',[]) if s.startswith(str(meeting.get('venue'))+' R'+str(race.get('number'))+':')]
                        reasons+=matching or ['not_in_accepted_forecast; inspect provider_skips']
                    elif rank is None:reasons.append('runner_not_scored_by_this_model')
                    models[version]=dict(status=model.get('status','NOT_ASSESSED'),runner_status='SCRATCHED' if row.get('is_scratched') is True else 'SCORED' if rank else 'NOT_SCORED',
                        probability=rank.get('probability') if rank else None,reasons=list(dict.fromkeys(reasons)))
                declared.append(dict(meeting=meeting.get('venue'),race=str(race.get('number')),number=number,horse=row.get('name'),
                    source_scratched=row.get('is_scratched'),models=models))
    for race in prediction.get('races',[]):
        for version,model in race.get('models',{}).items():
            for row in model.get('ranked_runners',[]):
                reasons=[];odds=row['odds'];p=row['probability']
                if odds<(6 if version=='V6' else 4):reasons.append('below_existing_watch_price_floor')
                if version=='V7' and p<.06:reasons.append('below_existing_V7_watch_probability_floor')
                if p*odds<=1:reasons.append('nonpositive_point_expected_value')
                detail=next((r for r in model.get('ruffies_to_watch',{}).get('rows',[]) if r['number']==row['number']),None)
                scored.append(dict(meeting=race['meeting'],race=race['race'],model=version,**row,
                    original_watch_gate_reasons=reasons,roughie_reporting_audit=detail,
                    approval_reasons=model.get('no_bet_reasons',[]),betting_decision=model.get('betting_decision'),
                    captured_at=race['captured_at'],capture_valid_until=prediction.get('valid_until')))
    return dict(schema='monty.declared-scored-audit.v1',declared=declared,scored=scored,
        provider_skips=prediction.get('coverage',{}).get('provider_skips',[]),
        limitation='Canonical input roster; additional original HTTP page rosters remain in raw source files. Unknown names/statuses remain unknown.')


def public_metadata(prediction,index):
    """Safe retrieval envelope when public derived-display rights are absent.
    Detailed rows remain only in the encrypted private packet, never public Git.
    """
    keys=('schema','date','timezone','run_id','generated_at','receipt','source_mode','status','models','blockers',
          'captured_at','valid_until','provider_snapshot_sha256','operational_outcome','operational_reason','qualifying_forecasts')
    value={k:prediction[k] for k in keys if k in prediction}
    value.update(races=[],evidence=index,private_assessment_count=len(prediction.get('races',[])),
        delivery_visibility='PRIVATE_EVIDENCE_ONLY',
        privacy_notice='Detailed predictions withheld from public GitHub: public derived-display rights are not established. This is a delivery/licensing restriction, not a predictive NO BET. Use authorised private evidence recovery.')
    return value


def public_result(prediction,index,recorder):
    allow=(recorder.policy or {}).get('sources',{}).get(recorder.source,{})
    permitted=(allow.get('public_derived_forecasts_permitted') is True and bool(allow.get('public_display_permission_reference')))
    if prediction.get('source_mode')=='SIMULATED FIXTURE' or (recorder.enabled and permitted):return dict(prediction,evidence=index)
    return public_metadata(prediction,index)
