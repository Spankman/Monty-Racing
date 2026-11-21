"""Shared post-scoring Monty recommendation ladder (all versions).

Research-only until supplied verified pre-race best bets and independently
qualified supporting runners. Never changes frozen V6/V7 probabilities.
"""
from itertools import permutations

def exotic_ladder(primary, supporting, *, short_price_limit, verified=False, stake_per_combination=None):
    """Return eligible *options*, not bets. Each runner: number, odds, qualified.

    The user supplies the short-price limit explicitly. No automatic extra
    runner is selected from rank alone. Supporting runners are independently
    qualified in order of preference. Ruffies are never eligible.
    """
    if short_price_limit is None or short_price_limit <= 1:
        raise ValueError('Explicit short-price limit required')
    if primary.get('selection_type') == 'RUFFY':
        return {'selection_type':'RUFFY','options':[{'bet_type':'WIN','numbers':[primary['number']]}],
                'status':'WIN ONLY'}
    if primary.get('selection_type') != 'BEST BET':
        return {'options':[],'status':'NO BET'}
    if not verified:
        return {'options':[],'status':'RESEARCH ONLY — NO BET'}
    def qualified(r):
        try:return bool(r['qualified']) and 1 < float(r['odds']) < float('inf')
        except (KeyError,TypeError,ValueError):return False
    if not qualified(primary):
        return {'options':[],'status':'NO BET — unverified primary'}
    options=[{'bet_type':'WIN','numbers':[primary['number']],'combinations':1}]
    if float(primary['odds']) >= short_price_limit:
        return {'options':options,'status':'WIN ONLY — primary not short-priced'}
    chosen=[primary];seen={str(primary['number'])}
    for r in supporting:
        if not qualified(r) or str(r['number']) in seen:continue
        chosen.append(r);seen.add(str(r['number']))
        if len(chosen)==2:
            options.append({'bet_type':'QUINELLA','numbers':[x['number'] for x in chosen],'combinations':1})
        elif len(chosen)==3 and all(float(x['odds'])<short_price_limit for x in chosen[:2]):
            options.append({'bet_type':'BOXED TRIFECTA','numbers':[x['number'] for x in chosen],'combinations':6})
        elif len(chosen)==4 and all(float(x['odds'])<short_price_limit for x in chosen[:3]):
            options.append({'bet_type':'BOXED FIRST FOUR','numbers':[x['number'] for x in chosen],'combinations':24})
        if len(chosen)>=4:break
        if float(chosen[-1]['odds'])>=short_price_limit:break
    if stake_per_combination is not None:
        if stake_per_combination<=0:raise ValueError('Stake must be positive')
        for o in options:o['total_stake']=round(o['combinations']*stake_per_combination,2)
    return {'options':options,'status':'OPTIONS ONLY — verify value before staking'}

