"""Resolve reviewed, same-race identity links without matching on name alone."""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from operations.audit.verification import name


@dataclass(frozen=True)
class Evidence:
    source: str
    source_id: str
    race: tuple  # jurisdiction, local date, canonical venue, race number, metres
    saddlecloth: int
    horse: str
    observed_at: datetime
    reference: str  # stored raw evidence locator and digest in the caller's archive
    birth_year: int | None = None
    sex: str | None = None
    country: str | None = None
    trainer: str | None = None


def resolve(authority, external, cutoff):
    """Return same-race links and per-runner blockers from normalized evidence.

    Callers authenticate lineage, venue aliases, source IDs and timestamps.
    Authority IDs must be registration/profile IDs. Krok IDs are entry-scoped.
    """
    if cutoff.utcoffset() is None:
        raise ValueError('Timezone-aware cutoff required')

    def index(rows):
        indexed = defaultdict(list)
        for row in rows:
            if (row.source and row.source_id.strip() and name(row.horse)
                    and row.reference and row.observed_at.utcoffset() is not None
                    and row.observed_at <= cutoff and len(row.race) == 5
                    and all(row.race) and type(row.saddlecloth) is int and row.saddlecloth > 0):
                indexed[row.race, row.saddlecloth].append(row)
        return indexed

    authoritative = index(authority)
    observed = index(external)
    links, blocked = [], []
    for key, registered in authoritative.items():
        for source in ('Krok', 'Betfair'):
            candidates = [row for row in observed.get(key, []) if row.source == source]
            if len(registered) != 1 or registered[0].source != 'authority':
                reason = 'ambiguous_authority'
            elif len(candidates) != 1:
                reason = 'missing_or_ambiguous_external'
            elif name(registered[0].horse) != name(candidates[0].horse):
                reason = 'name_disagreement'
            elif any(getattr(registered[0],attr) is not None and getattr(candidates[0],attr) is not None and str(getattr(registered[0],attr)).strip().casefold()!=str(getattr(candidates[0],attr)).strip().casefold() for attr in ('birth_year','sex','country','trainer')):
                reason='conflicting_identity_attributes'
            else:
                links.append((registered[0], candidates[0]))
                continue
            blocked.append((key, source, reason))

    repeated=defaultdict(set)
    for registered,row in links:repeated[registered.race,registered.source_id].add(registered.saddlecloth)
    links2=[]
    for registered,row in links:
        if len(repeated[registered.race,registered.source_id])>1:
            blocked.append(((row.race,row.saddlecloth),row.source,'same_registration_twice_in_race'))
        else:links2.append((registered,row))
    links=links2
    ids = defaultdict(set)
    for registered, row in links:
        ids[row.source, row.source_id].add(registered.source_id)
    verified = []
    for registered, row in links:
        if len(ids[row.source, row.source_id]) > 1:
            blocked.append(((row.race, row.saddlecloth), row.source, 'conflicting_registration'))
        else:
            verified.append((registered, row))
    return verified, blocked
