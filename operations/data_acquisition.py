"""Private application batching, safe credit accounting and immutable history.

No persistent/shared HTTP cache for live no-store responses. Reuse only a
current in-process capture; every timestamp remains its original observation.
No provider/model substitution, background polling or billing changes.
"""
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import hashlib,json,time,threading


def record_usage(rows,url,status,headers,command,started):
    safe={}
    for key in ('X-Credits-Cost','X-Credits-Remaining','X-Credits-Limit','X-RateLimit-Limit','X-RateLimit-Remaining'):
        value=headers.get(key)
        if isinstance(value,str) and value.isascii() and value.isdigit():safe[key.lower()]=int(value)
    rows.append(dict(endpoint=urlsplit(url).path,status=status,command=command,
        attempted_at=datetime.now(timezone.utc).isoformat(),elapsed_seconds=round(time.monotonic()-started,6),
        **safe,credit_cost_known='x-credits-cost' in safe))


def usage_summary(rows):
    costs=[r['x-credits-cost'] for r in rows if r.get('credit_cost_known')]
    return dict(attempts=len(rows),measured_credits=sum(costs),unknown_cost_attempts=len(rows)-len(costs),
                remaining_balance_is_not_monty_usage=True)


class CaptureBatch:
    """One date/country capture shared across commands; thread-coalesced locally.

    Cross-job caching is intentionally absent: no-store and independent field
    changes must not be hidden by a persistent raw response cache.
    """
    def __init__(self,fetcher,key,clock=None):
        self.fetcher=fetcher;self._key=key;self.clock=clock or (lambda:datetime.now(timezone.utc))
        self._entries={};self._lock=threading.Lock();self.usage=[];self.receipts=[]

    def get(self,day,country,command):
        if command.strip().upper()=='C':raise ValueError('C never acquires provider data')
        identity=(day,country)
        with self._lock:
            now=self.clock();entry=self._entries.get(identity)
            from monty_operations import command as parse
            request=parse(command,day,country)
            if entry and eligible(entry['payload'],entry['captured_at'],now,request.get('meeting'),request.get('race')):
                self.receipts.append(dict(command=command,cache='CURRENT_IN_PROCESS_CAPTURE',credits=0,
                    captured_at=entry['captured_at'].isoformat(),acquisition_id=entry['acquisition_id']))
                return json.loads(json.dumps(entry['payload'])),entry['captured_at']
            before=len(self.usage)
            payload=self.fetcher(day,self._key,meter=self.usage,command=command,country=country)
            captured=self.clock();digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
            self._entries[identity]=dict(payload=payload,captured_at=captured,acquisition_id=digest)
            self.receipts.append(dict(command=command,cache='NETWORK_ACQUISITION',captured_at=captured.isoformat(),
                acquisition_id=digest,**usage_summary(self.usage[before:])))
            return json.loads(json.dumps(payload)),captured


def eligible(payload,captured,now,meeting_name=None,race_number=None):
    from operations.market_integrity import quote_evidence,timestamp
    if not 0<=(now-captured).total_seconds()<300:return False
    seen=0
    for meeting in payload.get('data',[]):
        if meeting_name and str(meeting.get('venue','')).casefold()!=meeting_name.casefold():continue
        for race in meeting.get('races',[]):
            if race_number and str(race.get('number'))!=str(race_number):continue
            try:
                if timestamp(race['jump_time'])<=now:continue
            except (KeyError,ValueError,TypeError,AttributeError):return False
            for runner in race.get('runners',[]):
                if runner.get('is_scratched') is True:continue
                if runner.get('is_scratched') is not False:return False
                quote=quote_evidence(runner);values=quote['quote_timestamps']
                if not values or quote['odds'] is None:return False
                try:
                    parsed=[timestamp(v) for v in values]
                    if len(set(parsed))!=1 or not 0<=(now-parsed[0]).total_seconds()<300 or parsed[0]>captured:return False
                except (ValueError,TypeError,AttributeError):return False
                seen+=1
    return seen>0


class HistoryStore:
    """Append-only private content-addressed versions; conditional headers only
    for sources that explicitly permit them. Never writes frozen model paths.
    Network access stays in source-specific adapters with their own allowlists.
    """
    def __init__(self,root):
        self.root=Path(root).resolve()
        repo=Path(__file__).resolve().parents[1]
        if any(self.root==repo/p or repo/p in self.root.parents for p in ('monty_v6','v7')):
            raise ValueError('Frozen artifact directories are not a history store')
        self.root.mkdir(parents=True,exist_ok=True)
    def update(self,source,event,body,*,observed_at,etag=None,last_modified=None):
        identity=hashlib.sha256((source+'\n'+event).encode()).hexdigest()
        digest=hashlib.sha256(body).hexdigest();folder=self.root/identity;folder.mkdir(exist_ok=True)
        blob=folder/(digest+'.bin')
        if blob.exists() and hashlib.sha256(blob.read_bytes()).hexdigest()!=digest:raise ValueError('Historical blob integrity mismatch')
        if not blob.exists():
            with blob.open('xb') as handle:handle.write(body)
        record=dict(source=source,event=event,sha256=digest,observed_at=observed_at,etag=etag,last_modified=last_modified)
        observation=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
        target=folder/(observation+'.json')
        if not target.exists():
            with target.open('x') as handle:json.dump(record,handle,sort_keys=True)
        return record
    @staticmethod
    def conditional_headers(record,*,permitted=False):
        if not permitted:return {}
        return {key:record[field] for key,field in [('If-None-Match','etag'),('If-Modified-Since','last_modified')]
                if isinstance(record.get(field),str) and '\r' not in record[field] and '\n' not in record[field]}


def independent_lineage(a,b):
    """A different brand/API domain or price agreement is insufficient."""
    required=('collector','upstream','evidence_sha256')
    if any(not x.get(k) for x in (a,b) for k in required):return False
    return (a['collector']!=b['collector'] and a['upstream']!=b['upstream']
            and all(len(x['evidence_sha256'])==64 and all(c in '0123456789abcdef' for c in x['evidence_sha256']) for x in (a,b)))
