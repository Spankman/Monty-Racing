"""Read-only roughie audit. Missing archived quotes remain missing."""
import argparse
import csv
import hashlib
import json
from math import fsum, isclose, isfinite
from pathlib import Path


def audit_forecast(forecast):
    races, runners = [], []
    for race in forecast['races']:
        key = {'meeting': race['meeting'], 'race': race['race']}
        models = race['models']
        expected = race['data_completeness']['active_runners']
        odds, names, values, watches = {}, {}, {}, {}
        for version, model in models.items():
            by_number = {}
            for field in ('ranked_runners', 'ordered_selections', 'roughies', 'best_bets', 'best_chance'):
                rows = model.get(field) or []
                for row in ([rows] if isinstance(rows, dict) else rows):
                    number = str(row['number'])
                    price, probability = float(row['odds']), float(row['probability'])
                    if not (isfinite(price) and price > 1 and 0 < probability <= 1):
                        raise ValueError(f'Invalid archived quote/probability: {key}, {number}')
                    if (odds.setdefault(number, price) != price
                            or names.setdefault(number, row['horse']) != row['horse']
                            or by_number.setdefault(number, probability) != probability):
                        raise ValueError(f'Conflicting archived runner: {key}, {number}')
            values[version] = by_number
            watches[version] = {str(r['number']) for r in model.get('roughies', []) if r['odds'] >= 10}
        if len(odds) > expected or set(odds) & {str(row['number']) for row in race.get('scratchings', [])}:
            raise ValueError(f'Archived active-field inconsistency: {key}')
        observed = fsum(1/price for price in odds.values())
        complete = len(odds) == expected and expected > 0
        total = observed if complete else None
        state = ('underround' if total < 1 else 'overround' if total > 1 else 'even') if complete else (
            'overround lower bound' if observed >= 1 else 'unknown')
        for version, probabilities in values.items():
            if len(probabilities) == expected and expected and not isclose(fsum(probabilities.values()), 1, abs_tol=1e-6):
                raise ValueError(f'Unnormalized model: {key}, {version}')
        races.append(dict(key, v6_status=models['V6']['status'], expected=expected,
                          observed=len(odds), observed_book_pct=100*observed,
                          book_pct=None if total is None else 100*total, assessment=state,
                          v6_watches=len(watches['V6']), v7_watches=len(watches['V7'])))
        for number, price in odds.items():
            implied = 1/price
            market = implied/total if complete else None
            row = dict(key, number=number, horse=names[number], odds=price,
                       market_probability=market, book_only_edge=None if not complete else 1/total-1)
            for version, probabilities in values.items():
                p = probabilities.get(number)
                row[version+'_probability'] = p
                row[version+'_watch'] = number in watches[version]
                row[version+'_edge'] = None if p is None else p*price-1
                row[version+'_uplift_pp'] = None if p is None or market is None else 100*(p-market)
                row[version+'_market_only_watch'] = None if market is None else (
                    price >= 10 and market >= (.06 if version == 'V7' else 0) and market > implied)
            runners.append(row)
    return races, runners


def historical(paths, replay=None, diagnostic=None):
    import pandas as pd
    import numpy as np

    price = 'BEST_AVAIL_BACK_AT_SCHEDULED_OFF'
    market_id = 'WIN_MARKET_ID'
    if replay is None:
        data = pd.concat([pd.read_csv(p, dtype={market_id: str}) for p in paths], ignore_index=True)
    else:
        keys = [market_id, 'TAB_NUMBER']
        odds = pd.read_csv(replay, dtype={market_id: str})
        predictions = pd.read_csv(diagnostic, dtype={market_id: str})
        data = predictions.merge(odds[keys+[price, 'WIN_BSP']], on=keys, validate='one_to_one')
        if len(data) != len(predictions):
            raise ValueError('Incomplete frozen V6 replay merge')
    implied = 1/data[price]
    book = implied.groupby(data[market_id]).transform('sum')
    if not np.allclose(implied/book, data.market_probability, rtol=0, atol=1e-10):
        raise ValueError('Historical quote/probability mismatch')
    if not data.groupby(market_id).y.sum().eq(1).all():
        raise ValueError('Historical races must have one winner')
    result = dict(races=int(data[market_id].nunique()), dates=[data.date.min(), data.date.max()],
                  underround_races=int(data.loc[book < 1-1e-12, market_id].nunique()),
                  geelong_like_races=int(data.loc[book <= .9592, market_id].nunique()),
                  launceston_like_races=int(data.loc[book <= .7275, market_id].nunique()))
    masks = {'market_only_v6': (book < 1-1e-12),
             'market_only_v7_probability_floor': (book < 1-1e-12) & (data.market_probability >= .06)}
    if replay is not None:
        masks['frozen_v6'] = data.selected_probability*data[price] > 1
        masks['frozen_v6_no_underround'] = masks['frozen_v6'] & (book >= 1-1e-12)
        masks['frozen_v6_positive_uplift_and_edge'] = masks['frozen_v6'] & (data.selected_probability > data.market_probability)
        masks['frozen_v6_price_normalized_to_even_book'] = data.selected_probability > data.market_probability
    for arm, rule in masks.items():
        eligible = data.loc[(data[price] >= 10) & rule]
        groups = eligible.groupby(market_id)[market_id].transform('size')
        for tier, cohort in [('all', eligible), ('cluster_5_plus', eligible.loc[groups >= 5])]:
            valid_bsp = cohort.WIN_BSP.notna() & (cohort.WIN_BSP > 1)
            stake = len(cohort)
            def pnl(rows, column):
                return np.where(rows.y.eq(1), .95*(rows[column]-1), -1).sum()
            unit_pnl = float(pnl(cohort, price))
            result[f'{arm}_{tier}'] = dict(
                races=int(cohort[market_id].nunique()), watches=stake, winners=int(cohort.y.sum()),
                quote_units=unit_pnl, quote_roi=unit_pnl/stake if stake else None,
                largest_winning_quote=float(cohort.loc[cohort.y.eq(1), price].max()) if cohort.y.any() else None,
                bsp_watches=int(valid_bsp.sum()),
                bsp_roi=float(pnl(cohort.loc[valid_bsp], 'WIN_BSP')/valid_bsp.sum()) if valid_bsp.any() else None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('forecast', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--history', nargs='+', type=Path)
    parser.add_argument('--replay-runners', type=Path)
    parser.add_argument('--replay-predictions', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.forecast.read_bytes()
    forecast = json.loads(raw)
    races, runners = audit_forecast(forecast)
    for filename, rows in [('race_books.csv', races), ('runner_comparison.csv', runners)]:
        with (args.output/filename).open('w') as out:
            writer = csv.DictWriter(out, rows[0], lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    result = dict(forecast_sha256=hashlib.sha256(raw).hexdigest(), race_records=len(races),
                  complete_quote_vectors=sum(r['book_pct'] is not None for r in races))
    if args.history:
        result['exchange_snapshot_baseline'] = historical(args.history)
    if args.replay_runners and args.replay_predictions:
        result['frozen_v6_replay'] = historical([], args.replay_runners, args.replay_predictions)
    (args.output/'results.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
