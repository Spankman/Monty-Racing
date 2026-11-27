"""Primary Queensland field acquisition. One authority PDF per meeting batch.

Authority facts verify fields, never prices, historical joins or betting value.
Keep downloaded documents private and obey their reuse restrictions.
"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from operations.public_sources import capture,rq_declaration


def capture_races(day,races,directory,fetch=capture, *, meeting='Ipswich', meeting_code='ipsw'):
    # Explicit allowlist prevents arbitrary URL construction and silent venue aliases.
    if (meeting, meeting_code) not in {('Ipswich', 'ipsw'), ('Rockhampton', 'rock'), ('Cairns', 'crns')}:
        raise ValueError('Authority meeting mapping not validated')
    races=list(dict.fromkeys(int(number) for number in races))
    if any(number < 1 for number in races):raise ValueError('Invalid race number')
    if not races:return []
    meeting_url=f'https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/{meeting_code}/{day.replace("-", "")}'
    scratching_meta,scratching_body=fetch(meeting_url,directory)
    pdfs={};result=[]
    for number in races:
        url=f'https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/{meeting_code}/{day.replace("-","")}/race/{int(number)}'
        meta,body=fetch(url,directory);row=dict(race=str(number),sources=[meta,scratching_meta],primary_authority='Racing Queensland',
            verified=False,price_verification=False)
        if body:
            stage='authority_pdf_link'
            try:
                links=[urljoin(url,a['href']) for a in BeautifulSoup(body,'html.parser').find_all('a',href=True) if 'Race Fields PDF' in a.get_text(' ',strip=True)]
                if len(links)!=1:raise ValueError('Authority field PDF unavailable or ambiguous')
                stage='authority_pdf_fetch'
                if links[0] not in pdfs:pdfs[links[0]]=fetch(links[0],directory)
                pdf_meta,pdf=pdfs[links[0]];row['sources'].append(pdf_meta)
                if not pdf:raise ValueError('Authority PDF acquisition blocked')
                stage='authority_declaration_parse'
                if not scratching_body:raise ValueError('Authority meeting scratching acquisition blocked')
                # Validate the separate page identity before consuming withdrawals.
                from operations.public_sources import rq_facts
                rq_facts(scratching_body,day,meeting,number)
                facts=rq_declaration(body,pdf,day,meeting,number,scratchings_body=scratching_body)
                row.update(facts=facts,verified=facts['field_verified'] and facts['emergency_status_verified'])
            except Exception as exc:row.update(blocker=type(exc).__name__, blocker_stage=stage, blocker_detail=str(exc))
        result.append(row)
    return result
