"""Leakage-safe research gate for expert-weight recommendations.

Uses past, fully settled races only. A positive expert ROI is NOT proof
that blending improves Monty; without comparative out-of-sample metrics,
the effective expert weight stays zero.
"""
import argparse, json
from pathlib import Path
import pandas as pd

def gate(report_path, comparison_path=None, min_races=100):
    report=json.loads(Path(report_path).read_text())
    experts=report.get('experts',[])
    qualified=[e for e in experts if int(e.get('races',0))>=min_races]
    result={'expert_weight':0.0,'qualified_sources':[e['source'] for e in qualified],
      'reason':'No validated chronological comparison against Monty and market',
      'status':'RESEARCH ONLY — NO BET'}
    if comparison_path is None:return result
    comp=json.loads(Path(comparison_path).read_text())
    # Require independent validation, sufficient settled races, and a
    # documented positive improvement versus both Monty and market.
    if not comp.get('chronological_holdout_verified',False):
        result['reason']='Chronological holdout not verified';return result
    if int(comp.get('holdout_races',0))<min_races or not qualified:
        result['reason']='Insufficient independent holdout races or expert history';return result
    if not comp.get('same_races_same_odds',False):
        result['reason']='Baselines not compared on identical races and odds';return result
    if not comp.get('provenance_verified',False):
        result['reason']='Holdout provenance not verified';return result
    # This is an eligibility flag, not an automatic switch to betting.
    result['reason']='Comparison eligible for independent audit; no automatic weight activation'
    result['eligible_for_manual_review']=True
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('expert_performance')
    p.add_argument('--comparison')
    p.add_argument('--min-races',type=int,default=100)
    p.add_argument('--output',default='expert_weight_gate.json')
    a=p.parse_args()
    result=gate(a.expert_performance,a.comparison,a.min_races)
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
