"""Extract Sportsbet/Punters PDF form without treating SP as V6 market probability.

Runner blocks are identified by meeting/race/saddlecloth/name. Historical starts
are source observations, not automatically eligible V6 training observations.
"""
import re
from datetime import datetime
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd
from monty.normalization import normal, numeric_class

RACE = re.compile(r'^ Race (\d+) (.+)$', re.M)
HORSE = re.compile(r'^[ \t]{5,}(\d+) ([A-Z][A-Z0-9 .’\'()&/\-]+?)[ \t]{5,}[^\n]*$', re.M)
START = re.compile(r'^[ \t]*(\d+)[ \t]+of[ \t]+(\d+)[ \t]+([A-Z][A-Z0-9-]*?)[ \t]*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[ \t]+(\d{1,2}[A-Z][a-z]{2}\d{2})[ \t]+(\d+)m[ \t]+(.+)$', re.M)
DETAIL = re.compile(r'^(.*?)\s+(Good|Soft|Heavy|Firm|Synth|Synthetic|Fast)(\d*)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+)\s+(\d+(?:\.\d+)?)(?:\s|$)')

def parse_text(text, meeting, date):
    header=re.search(r'(\d{1,2})(?:st|nd|rd|th)\s+(\w+)\s+(\d{4})',text[:500])
    if not header or datetime.strptime(' '.join(header.groups()),'%d %B %Y').strftime('%Y-%m-%d')!=date:
        raise ValueError('PDF date header mismatch')
    races=[];runners=[];starts=[];unparsed=[]
    sections=list(RACE.finditer(text))
    for i,rm in enumerate(sections):
        section=text[rm.start():sections[i+1].start() if i+1<len(sections) else len(text)]
        race=int(rm[1]);card=section.split('Speedmap:')[0]
        entries={int(m[1]):m[2] for m in re.finditer(r'^\s*(\d+)\.\s+(.+)$',card,re.M)}
        races.append({'meeting':meeting,'race':race,'date':date,'heading':rm[2],
                      'benchmark_class':numeric_class(card),'card_entries':len(entries)})
        blocks=list(HORSE.finditer(section))
        for j,hm in enumerate(blocks):
            number=int(hm[1]);name=hm[2].strip()
            if number not in entries or not normal(entries[number]).startswith(normal(name)):
                raise ValueError(f'Runner block disagrees with card: {meeting} R{race} #{number} {name}')
            block=section[hm.start():blocks[j+1].start() if j+1<len(blocks) else len(section)]
            runner={'meeting':meeting,'race':race,'number':number,'horse':name,
                    'scratched':'SCRATCHED' in entries[number],
                    'first_starter':'FIRST STARTER' in block,'card_row':entries[number]}
            career=re.search(r'Career\s+(\d+):(\d+)-(\d+)-(\d+)',block)
            if career:runner.update(career_starts=int(career[1]),career_wins=int(career[2]))
            runners.append(runner)
            for line in block.splitlines():
                if (re.search(r'\b\d{1,2}[A-Z][a-z]{2}\d{2}\s+\d+m\b',line)
                        and not START.match(line)
                        and not re.search(r'\b(?:TRL|BT|JO)\b|J/O|Jump\s*Out',line,re.I)):
                    # Includes DNF/PU and nonstandard layouts. An unread latest
                    # start must prevent use of an earlier parsed start.
                    unparsed.append({'meeting':meeting,'race':race,'number':number,'raw_row':line.strip()})
            for sm in START.finditer(block):
                rest=sm[6].strip()
                trial=bool(re.search(r'\b(?:TRL|BT|JO)\b|J/O|Jump\s*Out',rest,re.I))
                raw=sm[0].strip()
                if trial:continue
                date_run=datetime.strptime(sm[4],'%d%b%y').strftime('%Y-%m-%d')
                if date_run>=date:raise ValueError('Current/future outcome in pre-race PDF')
                detail=DETAIL.match(rest)
                entry={k:runner[k] for k in ['meeting','race','number','horse']}
                entry.update(date=date_run,track_code=sm[3],distance_m=int(sm[5]),
                             finish=int(sm[1]),field_size=int(sm[2]),raw_row=raw)
                if detail:
                    entry.update(class_text=detail[1].strip(),going=(detail[2]+detail[3]).lower(),
                                 jockey=detail[4].strip(),weight=float(detail[5]),barrier=int(detail[6]),
                                 printed_sp=float(detail[7]))
                    starts.append(entry)
                else:
                    # Wrapped/truncated details may conceal a trial suffix.
                    # Quarantine rather than counting these as race starts.
                    unparsed.append({'meeting':meeting,'race':race,'number':number,'raw_row':raw})
    return races,runners,starts,unparsed

def read_pdf(path,meeting,date):
    text=subprocess.check_output(['pdftotext','-layout',str(Path(path)),'-'],text=True)
    return parse_text(text,meeting,date)

TRACK_CODES={'EFM':'Eagle Farm','GAWL':'Gawler','BLMT':'Belmont','ASCT':'Ascot',
 'GCST':'Gold Coast','IPSW':'Ipswich','NTHM':'Northam','MORP':'Morphettville',
 'MBR':'Murray Bridge','CRAN':'Cranbourne','WFM':'Warwick Farm','SBYN':'Strathalbyn',
 'HALI':'Halidon','SEYM':'Seymour','HAWK':'Hawkesbury','BKVA':'Balaklava',
 'NCLE':'Newcastle','SCST':'Sunshine Coast','BDGO':'Bendigo','KGR':'Kembla Grange',
 'TWBC':'Toowoomba','KYNE':'Kyneton','RAND':'Randwick','YORK':'York',
 'PAKM':'Pakenham','RHIL':'Rosehill','WYNG':'Wyong','SALE':'Sale','BUNB':'Bunbury',
 'GATT':'Gatton','COLI':'Collie','KCOY':'Kilcoy','CSNO':'Casino','PTL':'Port Lincoln',
 'MTG':'Mount Gambier','BDLE':'Bairnsdale','BRAT':'Ballarat','WAGG':'Wagga',
 'ILLA':'Illawarra Grange','QBYN':'Queanbeyan','CANB':'Canberra','GTON':'Geraldton',
 'LEIN':'Leinster','LEON':'Leonora','ROCK':'Rockhampton','PNLA':'Penola',
 'MTNG':'Manangatang','TRAR':'Traralgon','KILM':'Kilmore','MORT':'Mortlake',
 'HTON':'Hamilton','HSHM':'Horsham','MRYA':'Moruya','FLEM':'Flemington',
 'CAUL':'Caulfield','GEEL':'Geelong','MOOR':'Moora'}

def match_start(start, history):
    """Require a complete retained market and multi-field evidence, not name alone."""
    track=TRACK_CODES.get(start['track_code'])
    if not track:return None,'unmapped_track_code'
    candidates=history[(history.date==start['date']) & (history.TRACK==track)
        & (history.DISTANCE==start['distance_m'])
        & (history['_name_key'] if '_name_key' in history else history.SELECTION_NAME.map(normal)).eq(normal(start['horse']))]
    if len(candidates)!=1:return None,'missing_or_ambiguous_historical_row'
    row=candidates.iloc[0]
    field=history[history.WIN_MARKET_ID==row.WIN_MARKET_ID]
    if len(field)!=start['field_size']:return None,'historical_field_size_disagrees'
    if int(row.y)!=int(start['finish']==1):return None,'historical_outcome_disagrees'
    if not field.y.sum()==1:return None,'historical_market_not_single_winner'
    quotes=pd.to_numeric(field.BEST_AVAIL_BACK_AT_SCHEDULED_OFF,errors='coerce')
    if not np.isfinite(quotes).all() or not (quotes>1).all():return None,'missing_historical_market_quotes'
    return row,'matched_retained_market'

def last_start_features(start,current_distance_m,current_class,date):
    """Call only after latest PDF race is verified as the latest eligible race."""
    days=(datetime.fromisoformat(date)-datetime.fromisoformat(start['date'])).days
    if days<=0:raise ValueError('Historical start must precede prediction date')
    delta=current_distance_m-start['distance_m']
    previous_class=numeric_class(start.get('class_text',''))
    return {'days_since_run_log':np.log1p(min(days,730)),
        'resuming_60d':float(days>=60),'quick_backup_7d':float(days<=7),
        'distance_change_km':delta/1000,'up_200m':float(delta>=200),
        'down_200m':float(delta<=-200),
        'benchmark_class_change':current_class-previous_class
            if np.isfinite(current_class) and np.isfinite(previous_class) else np.nan}
