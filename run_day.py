#!/usr/bin/env python3
"""Audited snapshot -> normalized runner field -> frozen V6 scoring."""
import argparse,json,subprocess,sys
from pathlib import Path
from collect_runners import collect
from import_fields import convert

def run(source,date,outdir):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    manifest=collect(source,out/'source_snapshot.json',out/'manifest.json',date)
    audit=convert(out/'source_snapshot.json',out/'manifest.json',out/'validated_runners.csv',out/'intake_audit.json')
    if not audit['ready']:
        raise ValueError('Runner field validation failed: '+json.dumps(audit['issues']))
    subprocess.run([sys.executable,str(Path(__file__).parent/'race_day.py'),str(out/'validated_runners.csv'),'--complete-fields','--output',str(out/'monty_selections.csv')],check=True)
    report={'date':date,'source':manifest['source'],'source_sha256':manifest['sha256'],'race_count':audit['races'],'runner_count':audit['active_runners'],'tab_verified':False,'note':'Source-provided active runner counts are assertions, not independently verified by this software. Verify TAB fields, scratchings, prices before betting.'}
    (out/'run_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',help='HTTPS JSON endpoint or local JSON snapshot');p.add_argument('--date',required=True);p.add_argument('--output-dir',default='race_day_output');a=p.parse_args()
    print(json.dumps(run(a.source,a.date,a.output_dir),indent=2))
