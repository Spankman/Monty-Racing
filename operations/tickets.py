"""Paired text/HTML tickets from one shared forecast; never generates an image."""
from monty_operations import projection,ticket,utcnow
from operations.render import render


def paired(forecast,now=None):
    now=now or utcnow();unique={}
    for race in forecast.get('races',[]):
        key=(race['country'],race['meeting'].casefold(),str(race['race']))
        if key in unique and unique[key]!=race:
            raise ValueError('Conflicting duplicate race; refusing to choose a forecast')
        unique[key]=race
    source=dict(forecast,races=list(unique.values()))
    views=[projection(source,dict(version=v,view=mode),now) for v,mode in [('V6','official'),('V7','shadow')]]
    return dict(run_id=forecast['run_id'],provider_snapshot_sha256=forecast.get('provider_snapshot_sha256'),
                tickets=[dict(version=v['version'],text=ticket(v,now=now),html=render(v,now=now)) for v in views],
                image_generated=False)



def combined(forecast, now=None):
    """Deduplicate shared forecasts while preserving the selected model's ladder."""
    now = now or utcnow()
    views = [projection(forecast, dict(version=version, view=mode), now)
             for version, mode in [('V6', 'provisional'), ('V7', 'shadow')]]
    by_race = {}
    for view in views:
        for race in view['races']:
            result = race['result']
            if result['freshness_at_retrieval'] != 'FRESH AT CHECK TIME':
                continue
            key = race['country'], race['meeting'].casefold(), str(race['race'])
            entries = by_race.setdefault(key, {})
            if view['version'] in entries and entries[view['version']] != race:
                raise ValueError('Conflicting duplicate race')
            entries[view['version']] = race

    races = []
    for entries in by_race.values():
        # Keep V6's current ranked combination intact when the models overlap.
        ranked = [race for race in entries.values() if race['result'].get('ordered_selections')]
        watches = [race for race in entries.values() if race['result'].get('roughies')]
        if not ranked and not watches:
            continue
        race = (ranked or watches)[0]
        version = race['result'].get('model_version') or next(
            model for model, candidate in entries.items() if candidate is race)
        result = dict(race['result'])
        result.pop('ranked_runners', None)
        result.pop('ruffies_to_watch', None)
        numbers = {str(row['number']) for row in result.get('ordered_selections', [])}
        roughy = next((row for candidate in watches for row in candidate['result']['roughies']
                       if str(row['number']) not in numbers), None)
        # Avoid showing a V7 watch on a V6 line without its model classification.
        if roughy:
            engine = next(model for model, candidate in entries.items()
                          if roughy in candidate['result'].get('roughies', []))
            roughy = dict(roughy, assessment_engine=engine + (' research only' if engine == 'V7' else ' provisional'))
        result.update(assessment_engine=version + (' research only' if version == 'V7' else ' provisional'),
                      roughies=[roughy] if roughy else [])
        races.append(dict(race, result=result))

    races.sort(key=lambda race: (race['meeting'].casefold(), int(race['race'])))
    return dict(views[0], version='Combined', view='combined', races=races)
