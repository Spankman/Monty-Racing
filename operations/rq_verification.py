"""Primary Queensland field acquisition. One authority PDF per meeting batch.

Authority facts verify fields, never prices, historical joins or betting value.
Keep downloaded documents private and obey their reuse restrictions.
"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from operations.public_sources import capture,rq_declaration


def capture_races(day,races,directory,fetch=capture):
    pdfs={};result=[]
    for number in races:
        url=f'https://www.racingqueensland.com.au/racing/full-calendar/thoroughbred/meeting/ipsw/{day.replace("-","")}/race/{int(number)}'
        meta,body=fetch(url,directory);row=dict(race=str(number),sources=[meta],primary_authority='Racing Queensland',
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
                facts=rq_declaration(body,pdf,day,'Ipswich',number)
                row.update(facts=facts,verified=facts['field_verified'] and facts['emergency_status_verified'])
            except Exception as exc:row.update(blocker=type(exc).__name__, blocker_stage=stage)
        result.append(row)
    return result
