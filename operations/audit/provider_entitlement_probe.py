"""One-shot, count-only provider capability probe. Never publish raw data."""
from collections import Counter
from datetime import date, datetime
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(origin, route, key, params=None):
    req = Request(origin + route + ('?' + urlencode(params) if params else ''),
                  headers={'X-API-Key': key, 'Accept': 'application/json'})
    try:
        with build_opener(NoRedirect()).open(req, timeout=20) as response:
            raw = response.read(10_000_001)
            evidence = {'status': response.status}
            for field in ('X-Credits-Cost', 'X-Credits-Remaining', 'X-Credits-Reset',
                          'Retry-After', 'X-RateLimit-Limit', 'X-RateLimit-Remaining'):
                value = response.headers.get(field, '')
                if value.isascii() and value.isdigit():
                    evidence[field.lower()] = int(value)
        if len(raw) > 10_000_000:
            return dict(evidence, error='oversize'), None
        data = json.loads(raw)
        if not isinstance(data, dict):
            return dict(evidence, error='unexpected_payload_type'), None
        return evidence, data
    except HTTPError as exc:
        return {'status': exc.code}, None
    except (OSError, URLError, ValueError):
        return {'error': 'transport_or_payload_failure'}, None


def call_formfav(day, key):
    if not key:
        return {'credential_configured': False}
    origin = 'https://api.formfav.com'
    query = {'date': day, 'race_code': 'gallops', 'country': 'au', 'timezone': 'Australia/Brisbane'}
    usage, account = request(origin, '/v1/usage', key)
    report = {'credential_configured': True, 'usage': usage}
    if not account:
        return report
    for field in ('tier', 'limit', 'used', 'remaining', 'overQuota'):
        value = account.get(field)
        if isinstance(value, (int, bool)) or isinstance(value, str) and value.casefold() in (
            'free', 'pro', 'premium', 'trial', 'enterprise'
        ):
            usage[field] = value
    if account.get('overQuota'):
        return report
    status, cards = request(origin, '/v1/form/meetings', key, query)
    report['meetings'] = status
    meetings = (cards or {}).get('meetings') or []
    status['meeting_count'] = len(meetings) if isinstance(meetings, list) else None
    targets = [(m['slug'], r['raceNumber']) for m in meetings if m.get('country') == 'au'
               and re.fullmatch('[a-z0-9-]+', m.get('slug') or '')
               for r in m.get('races', []) if type(r.get('raceNumber')) is int and not r.get('abandoned')]
    if targets:
        track, race = targets[0]
        params = dict(query, track=track, race=race)
        status, form = request(origin, '/v1/form', key, params)
        rows = (form or {}).get('runners') or []
        report['form'] = dict(status, runner_count=len(rows))
        if str(usage.get('tier', '')).casefold() == 'premium':
            status, prices = request(origin, '/v1/prices', key, params)
            offers = [offer for row in (prices or {}).get('runners', [])
                      for offer in row.get('prices', []) if isinstance(offer, dict)]
            report['prices'] = dict(status, offer_count=len(offers),
                                    captured_at_count=sum(bool(o.get('capturedAt')) for o in offers))
    return report


def call_krok(day, key):
    if not key:
        return {'credential_configured': False}
    origin = 'https://krokodds.com.au'
    status, card = request(origin, '/api/v1/racing/meetings', key,
                           {'date': day, 'race_type': 'T', 'limit': 50})
    report = {'credential_configured': True, 'meetings_first_page': status}
    if not card:
        return report
    meetings = card.get('data') or []
    meta = card.get('meta') or {}
    status.update(page_count=1, meetings=len(meetings), more_pages=bool(meta.get('has_more')))
    races = [r for m in meetings if m.get('country') == 'AU' for r in m.get('races', [])]
    allowed = ('bookmaker', 'updated_at', 'updatedAt', 'timestamp', 'capturedAt', 'captured_at', 'win')
    offers = [o for race in races for runner in race.get('runners', [])
              for o in runner.get('odds', []) if isinstance(o, dict)]
    observed = Counter(field for offer in offers for field in allowed if offer.get(field) is not None)
    status.update(au_race_count=len(races), offer_count=len(offers), offer_fields=dict(observed))
    for race in races:
        race_id = race.get('race_key_v2') or race.get('race_key') or race.get('race_id') or race.get('id')
        if isinstance(race_id, str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', race_id):
            evidence, form = request(origin, '/api/v1/racing/field-form', key, {'race_id': race_id})
            report['field_form'] = dict(evidence, returned_object=form is not None)
            break
    return report


if __name__ == '__main__':
    day = os.getenv('PROBE_DATE') or datetime.now(ZoneInfo('Australia/Brisbane')).date().isoformat()
    date.fromisoformat(day)
    output = {'date': day}
    for key, method in [('krok', call_krok), ('formfav', call_formfav)]:
        try:
            output[key] = method(day, os.getenv(key.upper()+'_API_KEY'))
        except (AttributeError, KeyError, TypeError, ValueError):
            output[key] = {'error': 'unexpected_provider_schema'}
    print(json.dumps(output, indent=2))
