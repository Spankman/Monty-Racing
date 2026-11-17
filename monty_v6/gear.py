"""Conservative parsing of explicit published gear-change text, not sex strings."""
import math,re
FLAGS=['first_after_gelding','blinkers_first','blinkers_off','tongue_tie_first','winkers_first']
def parse_gear_change(text,complete_published_list=False):
    result={k:math.nan for k in FLAGS}
    if text is None or not str(text).strip():
        return {k:0. for k in FLAGS} if complete_published_list else result
    t=re.sub(r'\s+',' ',str(text).lower().replace('-',' ')).strip()
    if complete_published_list:result={k:0. for k in FLAGS}
    if re.search(r'\bgelded\b',t):result['first_after_gelding']=1.
    if re.search(r'\bblinkers\s+(?:on\s+)?first time\b',t):result['blinkers_first']=1.
    if re.search(r'\bblinkers\s+off(?: first time| again)?\b',t):result['blinkers_off']=1.
    if re.search(r'\btongue tie\s+(?:on\s+)?first time\b',t):result['tongue_tie_first']=1.
    if re.search(r'\bwinkers\s+(?:on\s+)?first time\b',t):result['winkers_first']=1.
    return result
