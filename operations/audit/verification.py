"""Offline reconciliation of independently sourced race and quote observations.

Source adapters must establish lineage and timestamps before calling this
comparison. A matching race does not imply complete meeting inventory.
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import re
import unicodedata


def name(value):
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


def field(rows):
    identity = {}
    for number, horse, scratched in rows:
        if type(number) is not int or number < 1 or type(scratched) is not bool:
            raise ValueError('Invalid saddlecloth or scratching status')
        if number in identity or not name(horse):
            raise ValueError('Duplicate saddlecloth or missing horse name')
        identity[number] = (name(horse), scratched)
    if not identity:
        raise ValueError('Empty declared field')
    return identity


def reconcile(provider, authority, operator, *, decision_at, max_age: timedelta):
    """Return mismatches and separate factual and price attestations."""
    def fresh(row):
        return row['lineage'] and timedelta(0) <= decision_at-row['observed_at'] < max_age

    mismatches = []
    if provider['lineage'] == authority['lineage']:
        mismatches.append('independent_source_lineage_missing')
    if not fresh(provider) or not fresh(authority):
        mismatches.append('source_observation_unavailable_or_stale')
    if authority['race_key'] != provider['race_key']:
        mismatches.append('race_identity_mismatch')
    for key in ('status', 'distance_m', 'condition', 'surface', 'scheduled_start'):
        if provider[key] is None or provider[key] != authority[key]:
            mismatches.append(key + '_missing_or_mismatched')
    if not isinstance(authority['condition'], str) or not re.fullmatch(
        r'(?:Firm [12]|Good [34]|Soft [5-7]|Heavy (?:[89]|10)|Synthetic)', authority['condition']
    ):
        mismatches.append('unverified_condition_grade')
    if authority['status'] != 'open' or authority['scheduled_start'] is None or decision_at >= authority['scheduled_start']:
        mismatches.append('race_not_open')
    try:
        declared = field(authority['runners'])
        if field(provider['runners']) != declared:
            mismatches.append('field_or_scratching_mismatch')
    except (TypeError, ValueError):
        declared = {}
        mismatches.append('invalid_declared_field')
    race_ok = not mismatches
    if provider['lineage'] == operator['lineage'] or not fresh(operator):
        mismatches.append('independent_operator_observation_unavailable_or_stale')
    if operator['race_key'] != provider['race_key']:
        mismatches.append('operator_race_identity_mismatch')
    if operator['market'] != 'fixed_win' or not operator['bookmaker']:
        mismatches.append('fixed_win_operator_unverified')
    active = {number for number, (_, scratched) in declared.items() if not scratched}
    try:
        if field(operator['runners']) != declared:
            raise ValueError
        for row in (provider, operator):
            if set(row['quotes']) != active or not active:
                raise ValueError
        for number in active:
            price, book = provider['quotes'][number]
            direct, direct_book = operator['quotes'][number]
            price, direct = Decimal(str(price)), Decimal(str(direct))
            if (not price.is_finite() or price <= 1 or price != direct
                    or book != direct_book or book != operator['bookmaker']):
                raise ValueError
    except (InvalidOperation, TypeError, ValueError):
        mismatches.append('fixed_win_field_price_or_bookmaker_mismatch')
    return dict(race_verified=race_ok, fixed_win_verified=not mismatches, blockers=mismatches)
