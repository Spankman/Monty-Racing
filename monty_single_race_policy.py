"""Single-race quick-mode policy and transparent fallback routing.

This module routes *available verified outputs*, not model execution. It never
manufactures selections or converts a research-only score into an approved bet.
"""
from dataclasses import dataclass

BET_ORDER=('WIN','QUINELLA_2','TRIFECTA_BOX_3','FIRST_FOUR_4')
MODEL_ORDER=('V7','V7_LE','V6','FORM_ASSESSMENT')

@dataclass(frozen=True)
class SelectionRoute:
    source:str
    selections:tuple
    official_model_output:bool
    race_only_lower_expectations:bool
    betting_authorised:bool
    reason:str

def route_single_race(outputs, *, eligible=True, override=False):
    """Select first *actual* nonempty candidate set, never inferred model results.

    outputs: dict of source name to actual selection records, or None if
    unavailable. Each record must have meeting, race, number and horse.
    Excluded race types require an explicit per-race override.
    """
    if not eligible and not override:
        return SelectionRoute('NO_BET',(),False,False,False,'Race type excluded; explicit race override required')
    for source in MODEL_ORDER:
        picks=outputs.get(source)
        if picks is None:continue
        if not isinstance(picks,(list,tuple)) or not picks:continue
        if any(not isinstance(p,dict) or any(not str(p.get(k,'')).strip()
               for k in ('meeting','race','number','horse')) for p in picks):
            continue
        keys={(str(p['meeting']).casefold(),str(p['race']),str(p['number'])) for p in picks}
        if len(keys)!=len(picks):continue
        model=source in ('V7','V7_LE','V6')
        # The router cannot independently prove model execution or timing.
        # Even model-labelled inputs remain unauthorised without external checks.
        return SelectionRoute(source,tuple((p['meeting'],p['race'],p['number'],p['horse']) for p in picks),
            model,source=='V7_LE',False,'Candidate selections only; verify provenance, timing and betting rules externally')
    return SelectionRoute('NO_BET',(),False,False,False,'No actual selections available from any source')

def next_bet_type(current):
    """Presentation escalation only; does not claim value or authorize staking."""
    if current not in BET_ORDER:raise ValueError('Unknown bet type')
    i=BET_ORDER.index(current)
    return BET_ORDER[i+1] if i+1<len(BET_ORDER) else None

def route_full_day(outputs, *, explicit_le=False):
    """Full-day selections never silently lower expectations.

    Caller must supply genuine externally verified output. This function only
    routes provided candidates, never executes models or approves betting.
    """
    allowed=('V7','V7_LE') if explicit_le else ('V7',)
    for source in allowed:
        if source=='V7_LE' and not explicit_le:
            continue
        candidate=route_single_race({source:outputs.get(source)})
        if candidate.source==source:
            return candidate
    return SelectionRoute('NO_BET',(),False,False,False,
                          'No qualifying full-day V7 selections; LE requires explicit authorization')
