"""Paired text/HTML tickets from one shared forecast; never generates an image."""
import json
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
