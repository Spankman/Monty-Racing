"""Bounded same-race, same-book diagnostic; never changes scoring or approval."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
import time
from zoneinfo import ZoneInfo

from operations.audit.provider_entitlement_probe import request

BASE = 'https://krokodds.com.au'
BOOK = 'tab'


def utcnow():
    return datetime.now(timezone.utc)


def stamp(value):
    if type(value) in (int, float):
        return datetime.fromtimestamp(value / 1000, timezone.utc)
    instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if instant.utcoffset() is None:
        raise ValueError('Naive evidence time')
    return instant


def observation(rows, source):
    found = {}
    for row in rows:
        if source == 'flucs':
            points = row.get('books', {}).get(BOOK, [])
            price_field, time_field = 'win', 't'
        elif source == 'history':
            points = row.get('bookFlucs', {}).get(BOOK, [])
            price_field, time_field = 'odds', 'timestamp'
        elif source == 'form':
            points = [q for q in row.get('odds', []) if str(q.get('bookmaker', '')).casefold() == BOOK]
            price_field, time_field = 'win', 'captured_at'
        else:
            points = [q for q in row.get('odds', []) if str(q.get('bookmaker', '')).casefold() == BOOK]
            price_field, time_field = 'win', 'captured_at'
        # These records describe provider observations, never bookmaker update times.
        candidates = set()
        for q in points:
            try:
                price, at = float(q[price_field]), stamp(q[time_field])
                if math.isfinite(price) and price > 1:
                    candidates.add((at, price))
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                continue
        number = str(row.get('number', row.get('tab_number', '')))
        name = ' '.join(str(row.get('name', '')).casefold().split())
        if not number.isdigit() or not name or number in found:
            raise ValueError('Conflicting runner identity')
        if candidates:
            latest = max(at for at, _ in candidates)
            prices = {price for at, price in candidates if at == latest}
            if len(prices) == 1:
                found[number] = (name, latest, prices.pop())
    return found


def analyze(primary, secondary, now):
    same = [(p, secondary[n]) for n, p in primary.items()
            if n in secondary and p[0] == secondary[n][0]]
    deltas = [(b[1] - a[1]).total_seconds() for a, b in same]
    ages = [(now-b[1]).total_seconds() for _, b in same]
    return {'matched': len(same), 'newer': sum(x > 0 for x in deltas),
            'equal': sum(x == 0 for x in deltas), 'older': sum(x < 0 for x in deltas),
            'same_price': sum(a[2] == b[2] for a, b in same),
            'max_newer_seconds': max(deltas, default=None),
            'matched_second_age_range_s': [min(ages), max(ages)] if ages else None,
            'matched_second_fresh': sum(0 <= x < 300 for x in ages)}


def timed(origin, route, key, params):
    start = utcnow()
    status, payload = request(origin, route, key, params)
    status.update(started_at=start.isoformat(), received_at=utcnow().isoformat())
    return status, payload


def card(day, key, route='/api/v1/racing/meetings'):
    return timed(BASE, route, key, {'date': day, 'race_type': 'T', 'country': 'AU', 'limit': 50})


def match(payload, day, venue, race_number, require_type=True):
    return [r for m in (payload or {}).get('data', [])
            if str(m.get('date'))[:10] == day and str(m.get('venue','')).casefold() == venue.casefold()
            and (not require_type or m.get('type') == 'T')
            for r in m.get('races', []) if str(r.get('number')) == str(race_number)]


def main():
    day = utcnow().astimezone(ZoneInfo('Australia/Brisbane')).date().isoformat()
    key = os.getenv('KROK_API_KEY')
    venue, race_number = 'Launceston', 6
    slug = 'launceston'
    report = {'date': day, 'venue': venue, 'race': race_number, 'bookmaker': BOOK,
              'credential_configured': {name: bool(os.getenv(name)) for name in
                  ('KROK_API_KEY', 'KROK_FREE_API_KEY', 'FORMFAV_API_KEY', 'PUNTERSEDGE_API_KEY')},
              'scope': 'Single AU race and bookmaker; two collection windows, not long-run SLA evidence',
              'epochs': []}
    if not key:
        return report
    routes = {
        'meetings': ('/api/v1/racing/meetings', {'date':day,'country':'AU','race_type':'T','limit':50}),
        'dated': ('/api/v1/racing/meetings/'+day, {'country':'AU','race_type':'T','limit':50}),
        'flucs': ('/api/v1/racing/flucs', {'date':day,'venue':slug,'race_no':race_number,'race_type':'T','book':BOOK,'limit':20}),
        'history': ('/api/v1/racing/odds-history', {'date':day,'venue':slug,'raceNumber':race_number,'race_type':'T','limit':1}),
    }
    previous = {}
    for index in range(2):
        if index:
            time.sleep(65)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {name: pool.submit(timed, BASE, path, key, query) for name,(path,query) in routes.items()}
            snapshots = {name: future.result() for name,future in futures.items()}
        now = utcnow()
        epoch = {'comparison_at':now.isoformat(),'routes':{},'against_meetings':{},'against_prior_same_route':{}}
        vectors = {}
        anchor = match(snapshots['meetings'][1],day,venue,race_number)
        anchor_active = {str(r['number']): ' '.join(str(r['name']).casefold().split())
                         for r in anchor[0].get('runners',[]) if r.get('is_scratched') is False} if len(anchor)==1 else {}
        for name, (status,payload) in snapshots.items():
            try:
                rows = []
                if name == 'flucs':
                    data = (payload or {}).get('data') or {}
                    if (data.get('date')==day and data.get('venue_slug')==slug and str(data.get('race_no'))==str(race_number)
                            and (payload or {}).get('meta',{}).get('ambiguous_race_type') is False):
                        rows = data.get('runners', [])
                else:
                    races = match(payload,day,venue,race_number,require_type=name!='history')
                    if len(races)==1:
                        rows = races[0].get('runners',[])
                values = observation(rows, name)
                selected = {n:v for n,v in values.items() if anchor_active.get(n)==v[0]}
                vectors[name] = selected
                ages = [(now-at).total_seconds() for _,at,_ in selected.values()]
                status.update(rows=len(rows), named_matches=len(selected),
                              fresh=sum(0 <= age < 300 for age in ages),
                              age_range_s=[min(ages),max(ages)] if ages else None,
                              consistent_sample_times=len({v[1] for v in selected.values()})==1 if selected else False)
            except (KeyError,TypeError,AttributeError,ValueError):
                status['schema_or_identity_unverified'] = True
            epoch['routes'][name]=status
        epoch['provider_active_runners']=len(anchor_active)
        for name, values in vectors.items():
            if name!='meetings':
                epoch['against_meetings'][name]=analyze(vectors.get('meetings',{}),values,now)
            if index:
                epoch['against_prior_same_route'][name]=analyze(previous.get(name,{}),values,now)
        report['epochs'].append(epoch)
        previous=vectors
    return report


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
