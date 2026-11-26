"""Pre-outcome planning sensitivity only. No race data, model fitting or API.

Paired Gaussian approximations use EFFECTIVE per-race SD and an explicit design
factor. Binomial ROI is an optimistic independent equal-price planning bound,
not realistic betting profitability or exact power for clustered returns.
"""
from datetime import date
from statistics import NormalDist
from math import ceil,sqrt,isfinite
from pathlib import Path
import json,sys
from scipy.stats import binom
N=NormalDist()


def required_pairs(effect,sd,*,alpha=.05,power=.8,design=1):
    if not all(isfinite(v) for v in (effect,sd,alpha,power,design)) or effect<=0 or sd<=0 or not 0<alpha<1 or not .5<power<1 or design<1:raise ValueError('Valid planning inputs required')
    return ceil(design*((N.inv_cdf(1-alpha/2)+N.inv_cdf(power))*sd/effect)**2)


def minimum_effect(pairs,sd,*,alpha=.05,power=.8,design=1):
    if type(pairs) is not int or pairs<=0:raise ValueError('Positive race count required')
    required_pairs(1,sd,alpha=alpha,power=power,design=design)
    return (N.inv_cdf(1-alpha/2)+N.inv_cdf(power))*sd*sqrt(design/pairs)


def binomial_roi_power(bets,odds,roi,alpha=.05):
    """Reject zero-ROI null on upper tail. Assumes all bets filled, equal odds,
    independent outcomes, no deductions. NOT the real heterogeneous ROI test.
    """
    if type(bets) is not int or bets<=0 or not isfinite(odds) or odds<=1 or not 0<alpha<1 or not 0<roi<odds-1:raise ValueError('Invalid scenario')
    p0=1/odds;p1=(1+roi)/odds
    critical=int(binom.ppf(1-alpha,bets,p0))+1
    return dict(bets=bets,odds=odds,assumed_roi=roi,critical_wins=critical,
                size=float(binom.sf(critical-1,bets,p0)),power=float(binom.sf(critical-1,bets,p1)),
                probability_no_wins=float(binom.pmf(0,bets,p1)))


def roi_required_normal(odds,roi,*,alpha=.05,power=.8,design=1):
    # Approximate upper-tail zero-ROI test with null/alternative variances.
    binomial_roi_power(1,odds,roi,alpha)
    if not .5<power<1 or design<1:raise ValueError('Invalid planning power/design')
    return ceil(design*((N.inv_cdf(1-alpha)*sqrt(odds-1)+N.inv_cdf(power)*sqrt((1+roi)*(odds-1-roi)))/roi)**2)


def wilson_half_width(n,p=.5,z=1.959963984540054):
    if type(n) is not int or n<=0 or not 0<=p<=1:raise ValueError('Invalid bin precision scenario')
    return z*sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)


def assessment():
    # No observed outcomes or fitted parameters from the registered cohort.
    pairs=[250,500,1000,1500];sd_grid=[.02,.05,.1]
    effects=[.001,.002,.005,.01]
    means=[dict(effect=e,sd=s,design=d,power=p,alpha=a,required_races=required_pairs(e,s,alpha=a,power=p,design=d))
           for e in effects for s in sd_grid for d in [1,1.5,3] for p in [.8,.9] for a in [.05,.05/6]]
    roi=[binomial_roi_power(n,o,r) for n in [100,500,1000,5000] for o in [10,20,40,60,100] for r in [.05,.10,.20]]
    # Rounded historical interval as a SCALE diagnostic, not verified pilot SD.
    lo,hi=-.001196,.001792;n_old=4129
    effective_sd=(hi-lo)/(2*N.inv_cdf(.975))*sqrt(n_old)
    return dict(schema='monty.power-planning.v1',classification='HYPOTHETICAL PRE-OUTCOME POWER SENSITIVITY, NOT ACHIEVED POWER',
        locked_window=dict(start='2027-01-04',end='2027-03-28',days=(date(2027,3,28)-date(2027,1,4)).days+1,formal_protocol_modified=False),
        actual_eligible_races=None,actual_selection_counts=None,verified_paired_sd=None,verified_cluster_structure=None,
        primary='paired race log loss: Benter blend minus calibrated market; negative is better',
        mean_planning=means,mde=[dict(races=n,sd=s,design=d,mde80=minimum_effect(n,s,design=d)) for n in pairs for s in sd_grid for d in [1,1.5,3]],
        historical_scale_only=dict(source_commit='29239357579422148091a3320401d5e0572d774c',races=n_old,rounded_day_bootstrap_interval=[lo,hi],effective_sd_from_normal_interval=effective_sd,
            limitation='Exploratory already-examined retrospective sample; approximate normal-equivalent scale, NOT independent target-cohort pilot variance'),
        paired_strike_scenarios=[dict(discordance=q,improvement=e,design=1.5,required_races=required_pairs(e,sqrt(q-e*e),design=1.5)) for q in [.10,.20,.30] for e in [.01,.02,.03]],
        binomial_roi_scenarios=roi,
        roi_normal_approximation=[dict(odds=o,roi=r,design=d,power=.8,alpha=.05,required_bets=roi_required_normal(o,r,design=d)) for o in [10,20,40,60,100] for r in [.05,.10,.20] for d in [1,1.5]],
        calibration_precision=[dict(bin_count=n,nominal_p=p,independent_wilson95_half_width=wilson_half_width(n,p)) for n in [100,500,1000] for p in [.02,.05,.10,.30]],
        rules=['No tuning/opening target outcomes','No automatic date extension or revised preregistration','One primary endpoint unchanged; alpha/6 only a conservative secondary planning scenario, not a protocol amendment',
               'Cluster at race then whole Brisbane day/meeting; repeated participants and serial dependence require sensitivity',
               'Actual ROI uses heterogeneous verified executable prices/deductions, paired cluster bootstrap and rare-winner stress; binomial scenarios are optimistic',
               'No model promotion or production thresholds from power outputs'])

if __name__=='__main__':
    value=json.dumps(assessment(),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    if len(sys.argv)==2:Path(sys.argv[1]).write_text(value)
    else:print(value,end='')
