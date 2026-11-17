import re
from datetime import datetime
from functools import lru_cache
import numpy as np,pandas as pd
def normal(s):return re.sub('[^a-z0-9]','',str(s).lower())

@lru_cache(None)
def full_clock_seconds(s):
    for fmt in ('%H:%M:%S.%f','%H:%M:%S','%I:%M:%S %p','%I:%M %p'):
        try:
            t=datetime.strptime(s.strip(),fmt);return t.hour*3600+t.minute*60+t.second+t.microsecond/1e6
        except (ValueError,AttributeError):pass
    return float('nan')


def clean_person(s):
    t=normal(s)
    return '' if t in {'','notnotified','tba','unknown','nonrider','nan','none','0','vacant'} else t


def condition(s):
    s=str(s).upper().replace(' ','')
    for prefix,key in [('HVY','heavy'),('HEAVY','heavy'),('SOFT','soft'),('GOOD','good'),('FIRM','firm'),('FAST','firm'),('AWT','synthetic'),('SYN','synthetic')]:
        if s.startswith(prefix):return key
    return 'unknown'


def numeric_class(s):
    s=str(s).upper();m=re.search(r'(?:BM|BENCHMARK)\s*(\d+)',s)
    return float(m.group(1)) if m else np.nan


def distance_band(value):return int(value)//400 if pd.notna(value) and np.isfinite(value) else -1


