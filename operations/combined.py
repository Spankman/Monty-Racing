"""One copyable daily ticket projected from a shared capture."""
from monty_operations import projection, utcnow


def combined_ticket(forecast, now=None):
    now = now or utcnow()
    unique={}
    for race in forecast.get('races',[]):
        key=(race['country'],race['meeting'].casefold(),str(race['race']))
        if key in unique and unique[key]!=race:raise ValueError('Conflicting duplicate race')
        unique[key]=race
    forecast=dict(forecast,races=list(unique.values()))
    views = [
        projection(forecast, {'version': 'V6', 'view': 'provisional'}, now),
        projection(forecast, {'version': 'V7', 'view': 'shadow'}, now),
    ]
    races = {}
    for view in views:
        label = 'V6 provisional' if view['version'] == 'V6' else 'V7 research only'
        for race in view['races']:
            result = race['result']
            identity = race['country'], race['meeting'].casefold(), race['race']
            entry = races.setdefault(identity, dict(race, result=dict(
                result, ordered_selections=[], roughies=[], assessment_engines='')))
            target = entry['result']
            # V6 has display precedence if both engines offer a best-chance
            # assessment. Keep exotic combinations intact as ranked.
            rows = result.get('ordered_selections', [])
            if rows and not target['ordered_selections']:
                target['ordered_selections'] = rows
                target['progression_bet_type'] = result['progression_bet_type']
                target['assessment_engines'] = label
            # V6 has precedence on duplicates, including exotic legs.
            seen = {row['number'] for row in target['ordered_selections'] + target['roughies']}
            if not target['roughies']:
                target['roughies'] = [
                    dict(row, assessment_engine=label)
                    for row in result.get('roughies', []) if row['number'] not in seen
                ][:1]
            target['no_bet_reasons'] = list(dict.fromkeys(
                target['no_bet_reasons'] + result.get('no_bet_reasons', [])))
    # A later engine can fill the ladder for a race first seen as a ruffy.
    for race in races.values():
        result = race['result']
        numbers = {row['number'] for row in result['ordered_selections']}
        result['roughies'] = [row for row in result['roughies'] if row['number'] not in numbers]
    entries = [race for race in races.values()
               if race['result']['ordered_selections'] or race['result']['roughies']]
    return dict(views[0], version='Combined', view='combined', races=entries,
                status='ASSESSMENTS ONLY' if entries else 'NO CURRENT ASSESSMENTS')
