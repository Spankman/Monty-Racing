"""Credential-safe, bounded FormFav capture. Reads FORMFAV_API_KEY from env.

No provider prediction endpoints, account changes, retries, or scheduled work.
"""
import argparse,datetime,json,os
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen,build_opener,HTTPRedirectHandler

class FormFavError(RuntimeError):pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class Client:
    def __init__(self,key=None,opener=None):
        self._key=key or os.environ.get('FORMFAV_API_KEY','')
        if not self._key:raise FormFavError('FORMFAV_API_KEY is not configured')
        self._opener=opener or build_opener(NoRedirect()).open

    def get(self,path,params=None):
        if path not in ['/usage','/form/meetings','/form','/results','/results/meeting']:
            raise FormFavError('Unsupported data endpoint')
        url='https://api.formfav.com/v1'+path
        if params:url+='?'+urlencode(params)
        req=Request(url,headers={'X-API-Key':self._key,'Accept':'application/json'})
        try:
            with self._opener(req,timeout=25) as response:data=json.load(response)
        except HTTPError as exc:
            raise FormFavError(f'FormFav HTTP {exc.code}; no automatic retry') from None
        except (URLError,TimeoutError,OSError):
            raise FormFavError('FormFav network request failed; no automatic retry') from None
        except (ValueError,TypeError):raise FormFavError('FormFav returned invalid JSON') from None
        if not isinstance(data,dict):raise FormFavError('FormFav returned an invalid response object')
        return data

def capture(date,output,countries=('au','nz'),refresh=False,client=None):
    datetime.date.fromisoformat(date)
    client=client or Client();out=Path(output);out.mkdir(parents=True,exist_ok=True)
    usage=client.get('/usage')
    if usage.get('overQuota'):raise FormFavError('FormFav quota exhausted')
    query={'date':date,'race_code':'gallops','timezone':'Australia/Brisbane'}
    meetings=client.get('/form/meetings',query)
    selected=[m for m in meetings.get('meetings',[]) if m.get('country') in countries]
    (out/'meetings.json').write_text(json.dumps(meetings,indent=2))
    audit=[]
    for meeting in selected:
        slug=meeting['slug']
        # Slugs become local filenames, never unchecked paths.
        if not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in slug):
            raise FormFavError('Unsafe meeting slug')
        for race in meeting['races']:
            if race.get('abandoned'):continue
            number=int(race['raceNumber']);dest=out/f'{slug}-{number}.json'
            if dest.exists() and not refresh:
                card=json.loads(dest.read_text());cached=True
            else:
                card=client.get('/form',dict(query,track=slug,race=number,country=meeting['country']))
                cached=False
            if card.get('date')!=date or card.get('raceNumber')!=number or not isinstance(card.get('runners'),list):
                raise FormFavError('Race-card identity or schema disagreement')
            if not cached:dest.write_text(json.dumps(card,indent=2))
            audit.append({'track':meeting['track'],'race':number,'country':meeting['country'],
                          'runners':len(card['runners']),'cached':cached})
    result={'date':date,'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'tier':usage.get('tier'),'limit':usage.get('limit'),'races':audit,
            'provider_predictions_used':False,'betting_ready':False}
    (out/'capture_audit.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',required=True)
    parser.add_argument('--output-dir',default='race_day_output/formfav')
    parser.add_argument('--refresh',action='store_true',help='Refresh cached form cards once')
    args=parser.parse_args()
    try:
        audit=capture(args.date,args.output_dir,refresh=args.refresh)
        print(json.dumps({'tier':audit['tier'],'races':len(audit['races']),'provider_predictions_used':False}))
    except FormFavError as exc:raise SystemExit(str(exc))
