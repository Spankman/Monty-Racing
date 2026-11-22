"""White/black/gold tickets from the normalized forecast; no scoring decisions."""
import html
import json
from pathlib import Path
from monty_operations import refresh_view, ticket


def render(view, *, archived=False, now=None):
    if not archived:
        view = refresh_view(view, now)
    e=html.escape
    title=f"MONTY {view['version']} — "+('SHADOW SELECTION SLIP (RESEARCH ONLY)' if view['version']=='V7' else 'OFFICIAL SELECTION SLIP' if view['view']=='official' else 'PROVISIONAL SELECTION SLIP')
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
      '<title>'+e(title)+'</title><style>body{background:white;color:#111;font:16px Arial;margin:0;padding:24px}main{max-width:760px;margin:auto;border-top:6px solid #b29446;padding-top:12px}h1{font-size:22px}h2{font-size:18px;color:#715917;margin-top:24px}table{width:100%;border-collapse:collapse}td{padding:6px 0;vertical-align:top}td:last-child{text-align:right;white-space:nowrap}p{line-height:1.5}textarea{box-sizing:border-box;width:100%;min-height:240px}section{border-bottom:1px solid #ded5bc;padding-bottom:12px}footer{color:#715917;margin-top:24px;font-weight:bold}</style><main>',
      '<h1>'+e(title)+'</h1><p>'+e(view['date'])+' · Australia/Brisbane</p><p><b>NO BET — no qualified wagers. Provisional rankings are not betting recommendations.</b></p>']
    if archived:
        parts.append('<p>ARCHIVED SNAPSHOT — check request freshness before use</p>')
    for meeting in dict.fromkeys(r['meeting'] for r in view['races']):
        parts.append('<h2>'+e(meeting)+'</h2>')
        for race in [r for r in view['races'] if r['meeting']==meeting]:
            result=race['result'];parts.append('<section><p>R'+e(str(race['race']))+' · '+e(result.get('progression_bet_type','NO BET'))+' assessment · <b>NO BET</b></p><table>')
            for i,row in enumerate(result.get('ordered_selections',[])):
                text='#'+str(row['number'])+' '+row['horse'];text=e(text)
                if i==0:text='<b>'+text+'</b>'
                parts.append('<tr><td>'+text+'</td><td>$'+format(row['odds'],'.2f')+'</td></tr>')
            if view['view'] in ('provisional', 'shadow'):
                for roughie in result.get('roughies',[]):
                    parts.append('<tr><td>RUFFY / VALUE WATCH · WIN ONLY · #'+e(str(roughie['number']))+' '+e(roughie['horse'])+' · NO BET</td><td>$'+format(roughie['odds'],'.2f')+'</td></tr>')
            parts.append('</table><p>'+e('; '.join(result.get('no_bet_reasons',[])))+'</p><p>Captured '+e(str(race['captured_at']))+' · '+e('Historical quote' if archived else result.get('freshness_at_retrieval','UNKNOWN'))+'</p></section>')
    parts+=['<footer>IN MONTY WE TRUST</footer><h2>Copy plain text</h2><textarea readonly aria-label="Copyable Monty ticket">'+e(ticket(view, archived=archived, now=now))+'</textarea></main></html>']
    return ''.join(parts)


def render_all(directory):
    for p in Path(directory).glob('v[67]-*.json'):
        view=json.loads(p.read_text());p.with_suffix('.html').write_text(render(view, archived=True))

if __name__=='__main__':
    import sys
    render_all(sys.argv[1])
