#!/usr/bin/env python3
"""Collect a documented JSON race snapshot, preserving source/provenance.

This is a configurable adapter, NOT an undocumented TAB API. Live URLs must be
supplied explicitly. The downloaded response is saved verbatim for audit.
"""
import argparse, datetime, hashlib, json, urllib.request
from pathlib import Path

def collect(source, raw_path, manifest_path, date, timeout=20):
    if source.startswith(('https://','http://')):
        if not source.startswith('https://'):
            raise ValueError('Only HTTPS remote sources are accepted')
        req=urllib.request.Request(source,headers={'User-Agent':'MontyRaceDay/0.4 (research; no credentials)','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=timeout) as response:
            data=response.read(15_000_001)
        if len(data)>15_000_000:raise ValueError('Response too large')
    else:
        data=Path(source).read_bytes()
    payload=json.loads(data)
    if isinstance(payload,list):rows=payload;metadata={}
    elif isinstance(payload,dict):
        rows=payload.get('runners')
        metadata=payload
    else:raise ValueError('JSON must be list or object')
    if not isinstance(rows,list) or not rows:raise ValueError('Nonempty runners list required')
    if not all(isinstance(r,dict) for r in rows):raise ValueError('Runner records must be objects')
    # Race-level active counts MUST come from an independently supplied, auditable
    # manifest; no inference from the potentially incomplete runner payload.
    races=metadata.get('races',[])
    if not isinstance(races,list) or not races:raise ValueError('Source must provide independently verified race counts in races[]')
    for race in races:
        if not isinstance(race.get('expected_active_runners'),int):raise ValueError('Missing independently verified active count')
    if metadata.get('date') and metadata['date']!=date:raise ValueError('Source date differs from requested date')
    raw_path=Path(raw_path);raw_path.parent.mkdir(parents=True,exist_ok=True)
    raw_path.write_bytes(data)
    captured=datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest={'date':date,'source':source,'captured_at':captured,'sha256':hashlib.sha256(data).hexdigest(),'races':races,'source_asserted_counts':True,'tab_verified':False}
    Path(manifest_path).write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--date',required=True);p.add_argument('--raw',default='snapshot.json');p.add_argument('--manifest',default='snapshot_manifest.json');a=p.parse_args()
    print(json.dumps(collect(a.source,a.raw,a.manifest,a.date),indent=2))
