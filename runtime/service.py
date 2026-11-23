"""Portable warm Python serving layer. Deployment/client compatibility is NOT implied."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import fcntl
import json
from pathlib import Path
import sqlite3
import threading
import time
import uuid

from monty_operations import command, projection, freshness, timestamp, utcnow, execute as frozen_execute
from runtime.provider import ProviderFailure


def canonical(text):
    text=text.strip()
    aliases={'RMV6PS':'RM6PS','RMV7PS':'RM7PS'}
    return aliases.get(text.upper(),text)


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FrozenEngine:
    def __init__(self,v7_root):self.v7_root=Path(v7_root).resolve()
    def __call__(self,req,out,job,payload,captured):
        result=frozen_execute(req['date'],out,self.v7_root,run_id=job,payload=payload,captured=captured,request=req)
        return result,Path(out)/'public/receipt.json'


class Service:
    def __init__(self,directory,provider,engine,*,clock=utcnow,asynchronous=True):
        self.directory=Path(directory).resolve();self.directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        if self.directory.stat().st_mode & 0o077:
            raise ValueError('Runtime state must be private to its owner (mode 0700)')
        self.owner=(self.directory/'worker.lock').open('a')
        try:fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            self.owner.close()
            raise ValueError('A runtime already owns this state directory') from None
        self.db=sqlite3.connect(self.directory/'state.sqlite',check_same_thread=False)
        self.db.row_factory=sqlite3.Row;self.lock=threading.RLock();self.clock=clock
        self.provider=provider;self.engine=engine;self.asynchronous=asynchronous
        self.pool=ThreadPoolExecutor(max_workers=1)
        self.snapshot=None;self.snapshot_date=None;self.snapshot_time=None
        self.db.executescript('''PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,scope TEXT,status TEXT,created TEXT,updated TEXT,error TEXT,forecast_path TEXT,receipt_path TEXT,retry_after INTEGER);
          CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,job TEXT,request_json TEXT,idem TEXT UNIQUE,created TEXT);
          CREATE UNIQUE INDEX IF NOT EXISTS active_scope ON jobs(scope) WHERE status IN ('QUEUED','RUNNING');''')
        # A crashed worker is never left indefinitely RUNNING or silently replayed.
        self.db.execute("UPDATE jobs SET status='FAILED',error='WORKER_RESTARTED',updated=? WHERE status IN ('QUEUED','RUNNING')",(self.clock().isoformat(),));self.db.commit()

    def close(self):
        self.pool.shutdown(wait=True);self.db.close()
        fcntl.flock(self.owner,fcntl.LOCK_UN);self.owner.close()

    def _verified(self,job):
        f=json.loads(Path(job['forecast_path']).read_text())
        r=json.loads(Path(job['receipt_path']).read_text())
        if (f['run_id']!=job['id'] or r['run_id']!=job['id'] or r['status']!=f['status']
            or r['forecast_sha256']!=digest(job['forecast_path'])):
            raise ValueError('Forecast integrity mismatch')
        return f,r

    def _req(self,text,day=None,country=None):
        req=command(canonical(text),day,country)
        if req['view']=='status':return req
        if req['date']!=self.clock().astimezone(__import__('monty_operations').TZ).date().isoformat():
            raise ValueError('Live requests require the current Brisbane date')
        return req

    @staticmethod
    def _scope(req):
        # Model/view are excluded because one execution always computes BOTH frozen models.
        return json.dumps([req['date'],(req.get('meeting') or '').casefold(),req.get('race'),req.get('country')],separators=(',',':'))

    def _fresh(self,job,req):
        if job['status']!='COMPLETED' or not job['forecast_path']:return False
        try:f,_=self._verified(job)
        except (OSError,ValueError,KeyError,TypeError):return False
        if not f.get('captured_at'):return False
        age=(self.clock()-datetime.fromisoformat(f['captured_at'])).total_seconds()
        if not 0<=age<=300:return False
        if not f.get('valid_until') or self.clock()>timestamp(f['valid_until']):return False
        # A recently captured card may contain closed races; do not reuse it
        # if no relevant upcoming field remains.
        return any(freshness(r,self.clock())=='FRESH AT CHECK TIME' for r in f['races'])

    def submit(self,text,*,date=None,country=None,idempotency_key=None,request_id=None):
        req=self._req(text,date,country)
        if req['view']=='status':return self.status(request_id)
        with self.lock:
            if idempotency_key:
                existing=self.db.execute('SELECT id,request_json FROM requests WHERE idem=?',(idempotency_key,)).fetchone()
                if existing:
                    if json.loads(existing['request_json'])!=req:raise ValueError('Idempotency key belongs to a different command')
                    return self.status(existing['id'])
            scope=self._scope(req);job=self.db.execute('SELECT * FROM jobs WHERE scope=? ORDER BY created DESC,rowid DESC LIMIT 1',(scope,)).fetchone()
            reuse=job is not None and (job['status'] in ('QUEUED','RUNNING') or self._fresh(job,req))
            now=self.clock().isoformat();job_id=job['id'] if reuse else uuid.uuid4().hex
            if not reuse:
                queued=self.db.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('QUEUED','RUNNING')").fetchone()[0]
                if queued>=16:raise ValueError('Request queue is full; check status before retrying')
                self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)',(job_id,scope,'QUEUED',now,now,None,None,None,0))
            rid=uuid.uuid4().hex
            self.db.execute('INSERT INTO requests VALUES(?,?,?,?,?)',(rid,job_id,json.dumps(req,sort_keys=True),idempotency_key,now));self.db.commit()
            if not reuse:
                if self.asynchronous:self.pool.submit(self._work,job_id,req)
                else:self._work(job_id,req)
            return self.status(rid)

    def _work(self,job,req):
        started=time.monotonic()
        with self.lock:self.db.execute("UPDATE jobs SET status='RUNNING',updated=? WHERE id=?",(self.clock().isoformat(),job));self.db.commit()
        try:
            now=self.clock()
            age=(now-self.snapshot_time).total_seconds() if self.snapshot_time else float('inf')
            if self.snapshot is None or self.snapshot_date!=req['date'] or not 0<=age<=300:
                payload=self.provider.fetch(req['date']);captured=self.clock()
                self.snapshot=payload;self.snapshot_time=captured;self.snapshot_date=req['date']
            else:payload=self.snapshot;captured=self.snapshot_time
            out=self.directory/'runs'/job
            forecast,receipt=self.engine(req,out,job,payload,captured)
            fp=out/'public/forecast.json'
            # Real engine writes these exact immutable bytes. Test engines must
            # obey the same contract and cannot substitute another result.
            f=json.loads(fp.read_text());r=json.loads(receipt.read_text())
            if f['run_id']!=job or r['run_id']!=job or r['status']!=f['status'] or r['forecast_sha256']!=digest(fp):raise ValueError('Forecast integrity mismatch')
            status='FAILED' if f['status']=='FAILED' else 'COMPLETED'
            error='ENGINE_REJECTED_INPUT' if status=='FAILED' else None
            with self.lock:
                self.db.execute('UPDATE jobs SET status=?,updated=?,error=?,forecast_path=?,receipt_path=? WHERE id=?',
                    (status,self.clock().isoformat(),error,str(fp),str(receipt),job));self.db.commit()
        except Exception as exc:
            code=exc.code if isinstance(exc,ProviderFailure) else 'INFERENCE_FAILED_'+type(exc).__name__
            retry=exc.retry_after if isinstance(exc,ProviderFailure) else 0
            with self.lock:
                self.db.execute("UPDATE jobs SET status='FAILED',updated=?,error=?,retry_after=? WHERE id=?",(self.clock().isoformat(),code,retry,job));self.db.commit()
        finally:
            # No raw provider payload or credential is copied into these metrics.
            with (self.directory/'timings.jsonl').open('a') as f:
                f.write(json.dumps(dict(job_id=job,elapsed_seconds=time.monotonic()-started))+'\n')

    def status(self,request_id=None):
        with self.lock:
            request=self.db.execute('SELECT * FROM requests '+('WHERE id=?' if request_id else 'ORDER BY created DESC,rowid DESC LIMIT 1'),(request_id,) if request_id else ()).fetchone()
            if request is None:return dict(request_id=request_id,request_status='NOT_FOUND')
            job=self.db.execute('SELECT * FROM jobs WHERE id=?',(request['job'],)).fetchone();req=json.loads(request['request_json'])
            value=dict(request_id=request['id'],job_id=job['id'],request_status=job['status'],created_at=request['created'],updated_at=job['updated'],
                       command=req['command'],semantic_outcome=None,captured_at=None,capture_age_seconds=None,valid_until=None,
                       error=job['error'],retry_after_seconds=job['retry_after'],betting_authorised=False)
            if job['forecast_path']:
                try:f,receipt=self._verified(job)
                except (OSError,ValueError,KeyError,TypeError):
                    return dict(value,request_status='FAILED',error='INTEGRITY_CHECK_FAILED')
                captured=f.get('captured_at');age=(self.clock()-datetime.fromisoformat(captured)).total_seconds() if captured else None
                value.update(semantic_outcome=f['status'],model_outcome=f.get('models',{}).get(req['version'],{}).get('status'),
                             captured_at=captured,capture_age_seconds=age,valid_until=f.get('valid_until'),receipt=receipt,
                             receipt_sha256=digest(job['receipt_path']))
                fresh=self._fresh(job,req)
                value['freshness']='FRESH' if fresh else 'EXPIRED' if captured else 'UNVERIFIED'
                if job['status']=='COMPLETED' and not fresh:value['request_status']='EXPIRED'
                if job['status']=='COMPLETED' and fresh:
                    view=projection(f,req,self.clock());value['view']=view
                    from monty_operations import ticket
                    from operations.render import render
                    value['ticket']=ticket(view,now=self.clock())
                    value['ticket_html']=render(view,now=self.clock())
            return value
