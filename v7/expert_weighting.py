"""Isolated pre-race expert study. Run with python -m v7.expert_weighting."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from math import isclose, isfinite, log, sqrt
from pathlib import Path
import re
from statistics import mean, stdev
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from monty_prospective_ledger import parse_time


WEIGHTS = (0, 5, 10, 15, 20)
BASELINE = 10
MIN_RACES = 100
MIN_DAYS = 20
MIN_ORIGINS = 5
MAX_ORIGINS = 20
MIN_FEATURE_COVERAGE = .60
REVIEW_LIMIT = 300
BRISBANE = ZoneInfo('Australia/Brisbane')
V6_MODEL_SHA256 = 'f44e31f74ed017f915963950b17f144fbf6c994854403a39ba197fe5923d3fb7'
V7_MODEL_SHA256 = 'c7e42a414fc672539ed6a6403e9902f5cb3349d699b7d5d78547ba5c8db3f324'
ARMS = ('v6_frozen', 'v7_unchanged', 'market', 'expert_consensus',
        *('fixed_' + str(w) for w in WEIGHTS), 'dynamic')


def earlier(left, right):
    return parse_time(left) < parse_time(right)


def date_at(timestamp):
    return parse_time(timestamp).astimezone(BRISBANE).date()


def evidence_url(value):
    try:
        url = urlsplit(value)
        return url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password
    except (ValueError, TypeError, AttributeError):
        return False


def probabilities(values, runners):
    if (set(values) != set(runners) or any(type(p) not in (float, int) or not 0 <= p <= 1
                                         for p in values.values()) or not isclose(sum(values.values()), 1, abs_tol=1e-7)):
        raise ValueError('Probability vector does not match the frozen active field')
    return values


def best(vector):
    return min(vector, key=lambda runner: (-vector[runner], runner))


def mixture(a, b, fraction):
    return {runner: (1 - fraction) * p + fraction * b[runner] for runner, p in a.items()}


def consensus(tips, runners, cutoff):
    """Count one corroborated origin per group, independent of site and aliases."""
    authors = defaultdict(set)
    documents = defaultdict(set)
    accepted = []
    rejected = Counter()
    for tip in tips:
        try:
            author = re.sub(r'[^a-z0-9]+', '', tip['author_id'].casefold())
            group = tip['independence_group'].strip().casefold()
            if not (tip['provenance_verified'] is True and author and group
                    and evidence_url(tip['source_url']) and evidence_url(tip['independence_evidence'])
                    and re.fullmatch(r'[a-f0-9]{64}', tip['evidence_sha256'])
                    and tip['number'] in runners and tip['horse'] == runners[tip['number']]
                    and parse_time(tip['published_at']) <= parse_time(tip['captured_at'])
                    and parse_time(tip['captured_at']) <= parse_time(tip['verified_at'])
                    and earlier(tip['captured_at'], cutoff) and earlier(tip['verified_at'], cutoff)):
                raise ValueError('ineligible evidence')
        except (ValueError, TypeError, KeyError, AttributeError):
            rejected['unverified_or_late_tip'] += 1
            continue
        authors[author].add(group)
        documents[tip['source_url']].add(group)
        documents[tip['evidence_sha256']].add(group)
        accepted.append((author, group, tip))
    votes = defaultdict(set)
    retained = defaultdict(list)
    for author, group, tip in accepted:
        if any(len(groups) != 1 for groups in (authors[author], documents[tip['source_url']],
                                               documents[tip['evidence_sha256']])):
            rejected['conflicting_author_or_document_origins'] += 1
            continue
        votes[group].add(tip['number'])
        retained[group].append(tip)
    distinct = {group: next(iter(picks)) for group, picks in votes.items() if len(picks) == 1}
    rejected['conflicting_group_vote'] = len(votes) - len(distinct)
    if not MIN_ORIGINS <= len(distinct) <= MAX_ORIGINS:
        return None, distinct, retained, dict(rejected)
    counts = Counter(distinct.values())
    return {n: counts[n] / len(distinct) for n in runners}, distinct, retained, dict(rejected)


def validate_result(forecast, result):
    if not (result['race_id'] == forecast['race_id'] and result['official_verified'] is True
            and result['status'] == 'official_single_winner'
            and evidence_url(result['source_url']) and result['winner'] in forecast['runners']
            and sorted(result['active_runners']) == sorted(forecast['runners'])
            and earlier(forecast['cutoff_at'], result['race_off_at'])
            and earlier(result['race_off_at'], result['settled_at'])
            and parse_time(result.get('recorded_at', result['settled_at'])) >= parse_time(result['settled_at'])):
        raise ValueError('Unverified, changed-field, void or incompatible settlement')
    return result


def settled(forecasts, results, as_of):
    rows = []
    excluded = Counter()
    for forecast in forecasts:
        if not earlier(forecast['cutoff_at'], as_of):
            continue
        result = results.get(forecast['race_id'])
        if not result:
            excluded['pending_at_cutoff'] += 1
            continue
        try:
            validate_result(forecast, result)
            if not earlier(result.get('recorded_at', result['settled_at']), as_of):
                excluded['pending_at_cutoff'] += 1
                continue
        except (ValueError, TypeError, KeyError):
            excluded['invalid_or_changed_field'] += 1
            continue
        rows.append((forecast, result))
    return sorted(rows, key=lambda row: (parse_time(row[0]['cutoff_at']), row[0]['race_id'])), excluded


def log_loss(vector, winner):
    return -log(max(vector[winner], 1e-15))


def calibrate(history):
    eligible = [(f, r) for f, r in history if f['raw_consensus'] is not None and f['odds_verified']
                and f['coverage_gate']]
    if len(eligible) < MIN_RACES or len({date_at(f['cutoff_at']) for f, _ in eligible}) < MIN_DAYS:
        return None, len(eligible)
    # Shrink votes toward the verified market, fitted only on already-settled races.
    # A coefficient of zero means the training data did not support any vote signal.
    def loss(strength):
        return mean(log_loss(mixture(f['vectors']['market'], f['raw_consensus'], strength), r['winner'])
                    for f, r in eligible[-REVIEW_LIMIT:])

    return min((0.0, .1, .2, .3, .4, .5), key=loss), len(eligible)


def profit(forecast, result, arm):
    pick = best(forecast['vectors'][arm])
    return forecast['odds'][pick] * (pick == result['winner']) - 1


def paired(rows, candidate, reference):
    by_day = defaultdict(list)
    gains = []
    for forecast, result in rows:
        options = forecast['vectors']
        gain = log_loss(options[reference], result['winner']) - log_loss(options[candidate], result['winner'])
        gains.append(gain)
        by_day[date_at(forecast['cutoff_at'])].append(gain)
    average = mean(gains)
    residuals = [sum(values) - len(values) * average for values in by_day.values()]
    error = stdev(residuals) * sqrt(len(residuals)) / len(gains)
    # Conservative normal margin for paired comparisons across five weight arms.
    return {'gain': average, 'lower': average - 2.8 * error, 'upper': average + 2.8 * error,
            'profit_delta': sum(profit(f, r, candidate) - profit(f, r, reference) for f, r in rows)}


def weight_decision(history, prior):
    rows = [(f, r) for f, r in history if f['odds_verified'] and 'expert_consensus' in f['vectors']][-REVIEW_LIMIT:]
    days = len({date_at(f['cutoff_at']) for f, _ in rows})
    audit = {'holdout_races': len(rows), 'holdout_days': days, 'prior_expert_pct': prior}
    if len(rows) < MIN_RACES or days < MIN_DAYS:
        return 0, dict(audit, reason='INSUFFICIENT_OUT_OF_SAMPLE_EVIDENCE')
    versus_model = {w: paired(rows, f'fixed_{w}', 'fixed_0') for w in WEIGHTS[1:]}
    versus_market = {w: paired(rows, f'fixed_{w}', 'market') for w in WEIGHTS[1:]}
    audit.update(versus_model={str(w): v for w, v in versus_model.items()},
                 versus_market={str(w): v for w, v in versus_market.items()})
    target = BASELINE if prior is None else prior
    if target == 0:
        target = 5
    evidence = versus_model[target]
    market = versus_market[target]
    if evidence['upper'] < 0 or (evidence['gain'] <= 0 and evidence['profit_delta'] < 0):
        lower = target - 5
        supported = lower > 0 and all(t['gain'] > 0 and t['profit_delta'] >= 0
                                      for t in (versus_model[lower], versus_market[lower]))
        return lower if supported else 0, dict(audit, reason='DETERIORATION_REDUCED_WEIGHT')
    if (evidence['gain'] <= 0 or market['gain'] <= 0
            or evidence['profit_delta'] < 0 or market['profit_delta'] < 0):
        return 0, dict(audit, reason='BASELINE_LACKS_COMPARATIVE_SUPPORT')
    step = target + 5
    if prior and step <= max(WEIGHTS):
        next_model, next_market = versus_model[step], versus_market[step]
        incremental = paired(rows, f'fixed_{step}', f'fixed_{target}')
        audit['incremental'] = incremental
        if all(test['lower'] > 0 and test['profit_delta'] >= 0
               for test in (next_model, next_market, incremental)):
            return step, dict(audit, reason='VERIFIED_PAIRED_IMPROVEMENT')
    return target, dict(audit, reason='SUPPORTED_90_10_BASELINE' if prior is None else 'RETAIN_SUPPORTED_WEIGHT')


def forecast(card, previous, results):
    cutoff = card['cutoff_at']
    if not earlier(cutoff, card['scheduled_start']):
        raise ValueError('Forecast must precede scheduled start')
    runners = card['runners']
    if len(runners) < 2 or set(runners) != set(card['odds']):
        raise ValueError('Incomplete matched field and market')
    odds = card['odds']
    if not all(type(price) in (int, float) and isfinite(price) and price > 1 for price in odds.values()):
        raise ValueError('Invalid common fixed-win quotes')
    if not (parse_time(card['odds_captured_at']) <= parse_time(cutoff)
            and all(parse_time(card['model_captured_at'][v]) <= parse_time(cutoff) for v in ('v6', 'v7'))):
        raise ValueError('Market or model evidence after forecast cutoff')
    for version, model_sha in (('v6', V6_MODEL_SHA256), ('v7', V7_MODEL_SHA256)):
        artifact = card['model_artifacts'][version]
        if (artifact['model_sha256'] != model_sha or not evidence_url(artifact['forecast_url'])
                or not re.fullmatch(r'[a-f0-9]{64}', artifact['forecast_sha256'])):
            raise ValueError('Missing evidence for the exact frozen model forecast')
    v6, v7 = (probabilities(card['models'][v], runners) for v in ('v6', 'v7'))
    if not re.fullmatch(r'[a-f0-9]{64}', card.get('shared_model_input_sha256', '')):
        raise ValueError('Missing common V6/V7 field snapshot hash')
    odds_verified = card.get('odds_verified') is True and evidence_url(card.get('odds_source'))
    coverage = card.get('v7_feature_coverage')
    coverage_gate = type(coverage) in (int, float) and MIN_FEATURE_COVERAGE <= coverage <= 1
    market = {n: (1 / odds[n]) / sum(1 / x for x in odds.values()) for n in runners}
    raw, votes, tips, rejected = consensus(card.get('tips', []), runners, cutoff)
    history, _ = settled(previous, results, cutoff) if raw is not None and odds_verified and coverage_gate else ([], {})
    strength, training = calibrate(history)
    vectors = dict(v6_frozen=v6, v7_unchanged=v7, market=market)
    vectors.update({f'fixed_{w}': v7 for w in WEIGHTS})
    dynamic_weight = 0
    decision = {'reason': 'NO_VERIFIED_INDEPENDENT_CONSENSUS' if raw is None else
                'UNVERIFIED_FIXED_WIN_QUOTES' if not odds_verified else
                'INSUFFICIENT_MODEL_FEATURE_COVERAGE' if not coverage_gate else
                'INSUFFICIENT_CALIBRATION_OR_NO_VOTE_SIGNAL'}
    if strength:
        expert = mixture(market, raw, strength)
        vectors['expert_consensus'] = expert
        vectors.update({f'fixed_{w}': mixture(v7, expert, w / 100) for w in WEIGHTS})
        past = sorted((f for f in previous if earlier(f['cutoff_at'], cutoff) and f['decision'].get('policy_review')),
                      key=lambda f: parse_time(f['cutoff_at']))
        last = past[-1] if past else None
        if last and date_at(last['cutoff_at']).isocalendar()[:2] == date_at(cutoff).isocalendar()[:2]:
            dynamic_weight = last['expert_pct']
            decision = dict(last['decision'], reason='RETAIN_WEEKLY_REVIEW', policy_review=False,
                            review_race_id=last['race_id'])
        else:
            prior = last['expert_pct'] if last else None
            dynamic_weight, decision = weight_decision(history, prior)
            decision['policy_review'] = decision['reason'] != 'INSUFFICIENT_OUT_OF_SAMPLE_EVIDENCE'
    vectors['dynamic'] = vectors[f'fixed_{dynamic_weight}']
    return {'schema': 1, 'status': 'RESEARCH ONLY — NO BET',
            **{key: card.get(key) for key in ('race_id', 'classification', 'cutoff_at', 'scheduled_start',
                                              'runners', 'odds', 'odds_source', 'odds_captured_at',
                                              'model_captured_at', 'model_artifacts', 'shared_model_input_sha256')},
            'odds_verified': odds_verified,
            'v7_feature_coverage': coverage if type(coverage) in (float, int) and isfinite(coverage) else None,
            'coverage_gate': coverage_gate,
            'raw_consensus': raw, 'vectors': vectors,
            'picks': {arm: best(vector) for arm, vector in vectors.items()},
            'expert_pct': dynamic_weight, 'monty_pct': 100 - dynamic_weight,
            'expert_pct_by_arm': {arm: (dynamic_weight if arm == 'dynamic' else
                                       100 if arm == 'expert_consensus' else
                                       int(arm[6:]) if arm.startswith('fixed_') and 'expert_consensus' in vectors else 0)
                                  for arm in vectors},
            'calibration_races': training, 'vote_calibration_strength': strength, 'decision': decision,
            'independent_group_votes': votes, 'tip_evidence': dict(tips), 'excluded_tips': rejected}


def odds_band(price):
    return next((label for limit, label in ((2, '1–<2'), (4, '2–<4'), (8, '4–<8'),
                                             (15, '8–<15')) if price < limit), '15+')


def metrics(rows, arm):
    if not rows:
        return {'races': 0, 'selections': 0, 'wins': None, 'strike_rate': None, 'profit_units': None,
                'roi': None, 'log_loss': None, 'multiclass_brier': None, 'top_pick_ece': None,
                'max_drawdown_units': None}
    hits, losses, briers = [], [], []
    bins = defaultdict(list)
    equity = peak = drawdown = 0.0
    # Settle on the real sequence of known outcomes for drawdown.
    for f, r in sorted(rows, key=lambda row: (parse_time(row[1]['settled_at']), row[0]['race_id'])):
        vector, winner = f['vectors'][arm], r['winner']
        pick = best(vector)
        hit = pick == winner
        hits.append(hit)
        losses.append(log_loss(vector, winner))
        briers.append(sum((p - (n == winner)) ** 2 for n, p in vector.items()))
        bins[min(9, int(10 * vector[pick]))].append((vector[pick], hit))
        equity += profit(f, r, arm)
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    calibration = {b: {'n': len(ps), 'mean_probability': mean(p for p, _ in ps),
                       'observed_win_rate': mean(hit for _, hit in ps)} for b, ps in sorted(bins.items())}
    ece = sum(c['n'] * abs(c['mean_probability'] - c['observed_win_rate']) for c in calibration.values()) / len(rows)
    return {'races': len(rows), 'selections': len(rows), 'wins': sum(hits), 'strike_rate': mean(hits),
            'profit_units': equity, 'roi': equity / len(rows), 'log_loss': mean(losses),
            'multiclass_brier': mean(briers), 'top_pick_ece': ece, 'top_pick_calibration_bins': calibration,
            'max_drawdown_units': drawdown}


def review(forecasts, results, as_of, days=None):
    if days:
        since = date_at(as_of) - timedelta(days=days - 1)
        forecasts = [f for f in forecasts if date_at(f['cutoff_at']) >= since]
    forecasts = [f for f in forecasts if earlier(f['cutoff_at'], as_of)]
    rows, excluded = settled(forecasts, results, as_of)
    common = [(f, r) for f, r in rows if f['odds_verified'] and 'expert_consensus' in f['vectors']]
    baseline = [(f, r) for f, r in rows if f['odds_verified']]
    seen = sorted(rows, key=lambda row: parse_time(row[0]['cutoff_at']))
    distributions = {}
    classifications = sorted({f['classification'] for f, _ in common if f['classification']})
    for arm in ARMS:
        distributions[arm] = dict(metrics(common, arm),
                                  by_class={c: metrics([(f, r) for f, r in common if f['classification'] == c], arm)
                                            for c in classifications},
                                  by_odds={b: metrics([(f, r) for f, r in common if
                                                      odds_band(f['odds'][best(f['vectors'][arm])]) == b], arm)
                                           for b in ('1–<2', '2–<4', '4–<8', '8–<15', '15+')})
    individual = defaultdict(list)
    authors = defaultdict(list)
    for f, r in baseline:
        for group, pick in f['independent_group_votes'].items():
            individual[group].append((pick == r['winner'], f['odds'][pick]))
            for author in {tip['author_id'] for tip in f['tip_evidence'][group]}:
                authors[author].append((pick == r['winner'], f['odds'][pick]))

    def individual_metrics(entries):
        calculated = {}
        for group, outcomes in sorted(entries.items()):
            net = sum(price * hit - 1 for hit, price in outcomes)
            calculated[group] = {'races': len(outcomes), 'strike_rate': mean(hit for hit, _ in outcomes),
                                 'profit_units': net, 'roi': net / len(outcomes)}
        return calculated
    by_weight = Counter(f['expert_pct'] for f in forecasts)
    reasons = Counter(f['decision']['reason'] for f in forecasts)
    return {'status': 'RESEARCH ONLY — NO BET', 'as_of': as_of, 'days': days, 'frozen_races': len(forecasts),
            'settled_races': len(seen), 'settlement_exclusions': dict(excluded),
            'matched_expert_races': len(common), 'matched_verified_market_races': len(baseline),
            'comparison': distributions,
            'model_only_common': {arm: metrics(baseline, arm) for arm in ('v6_frozen', 'v7_unchanged', 'market')},
            'individual_consensus_groups': individual_metrics(individual),
            'individual_analysts': individual_metrics(authors),
            'expert_weight_distribution': dict(sorted(by_weight.items())), 'weight_decision_reasons': dict(reasons),
            'weight_changes': Counter(f"{f['decision']['prior_expert_pct']}→{f['expert_pct']}" for f in forecasts
                                      if f['decision'].get('policy_review')
                                      and f['decision'].get('prior_expert_pct') != f['expert_pct']),
            'expert_contribution': {'qualified_consensus_races': sum(f['raw_consensus'] is not None for f in forecasts),
                                    'top_pick_changes_on_common_set': sum(f['picks']['dynamic'] != f['picks']['fixed_0']
                                                                          for f, _ in common)},
            'settlement_basis': 'One simulated unit per arm on its top WIN pick. Return at the same captured '
                                'verified fixed quote per horse. Official dividends retained as evidence, '
                                'never substituted for fixed-win prices. No actual wagers or exotics.'}


def load_records(directory):
    records = []
    for path in sorted(Path(directory).glob('*.json')):
        envelope = json.loads(path.read_text())
        value = envelope['record']
        if digest(value) != envelope['sha256']:
            raise ValueError(f'Ledger hash mismatch: {path}')
        records.append(value)
    if len({record['race_id'] for record in records}) != len(records):
        raise ValueError('Duplicate race in ledger')
    return records


def digest(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, allow_nan=False).encode()).hexdigest()


def persist(directory, record):
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(record['race_id'].encode()).hexdigest()
    with NamedTemporaryFile(dir=target, mode='w', encoding='utf-8') as file:
        json.dump({'sha256': digest(record), 'record': record}, file, indent=2, allow_nan=False)
        file.flush()
        (target / (name + '.json')).hardlink_to(file.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=Path('research-expert-ledger'))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze').add_argument('card', type=Path)
    sub.add_parser('settle').add_argument('result', type=Path)
    view = sub.add_parser('review')
    view.add_argument('--as-of', required=True)
    view.add_argument('--days', choices=(1, 7), type=int)
    replay = sub.add_parser('replay')
    replay.add_argument('archive', type=Path)
    replay.add_argument('--as-of', required=True)
    args = parser.parse_args()
    if args.command == 'replay':
        archive = json.loads(args.archive.read_text())
        forecasts = []
        results = {r['race_id']: r for r in archive['results']}
        cards = sorted(archive['cards'], key=lambda c: (parse_time(c['cutoff_at']), c['race_id']))
        if len({c['race_id'] for c in cards}) != len(cards) or len(results) != len(archive['results']):
            raise ValueError('Duplicate archived race or result')
        for card in cards:
            if earlier(card['cutoff_at'], args.as_of):
                forecasts.append(forecast(card, forecasts, results))
        output = review(forecasts, results, args.as_of)
    else:
        forecasts = load_records(args.ledger / 'forecasts')
        results = {r['race_id']: r for r in load_records(args.ledger / 'results')}
        if args.command == 'freeze':
            card = json.loads(args.card.read_text())
            now = datetime.now(timezone.utc)
            if not parse_time(card['cutoff_at']) <= now < parse_time(card['scheduled_start']):
                raise ValueError('Use replay for an archived or already-due race')
            # The real decision time determines which settled records are known.
            card['cutoff_at'] = now.isoformat()
            output = forecast(card, forecasts, results)
            persist(args.ledger / 'forecasts', output)
        elif args.command == 'settle':
            output = json.loads(args.result.read_text())
            selected = next((f for f in forecasts if f['race_id'] == output['race_id']), None)
            if selected is None:
                raise ValueError('No frozen forecast for result')
            validate_result(selected, output)
            now = datetime.now(timezone.utc)
            if parse_time(output['settled_at']) > now:
                raise ValueError('Settlement cannot be in the future')
            output['recorded_at'] = now.isoformat()
            persist(args.ledger / 'results', output)
        else:
            output = review(forecasts, results, args.as_of, args.days)
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
