"""Discover public expert-tip articles; never infer selections from article links.

Conservative discovery only. Source pages and article URLs are leads, NOT
pre-race tips. Fetching must respect site terms and robots restrictions.
"""
import argparse,datetime,json,re,urllib.parse,urllib.request,urllib.robotparser
from bs4 import BeautifulSoup

# Public landing pages are discovery leads, never proof of a tip.
# Source URLs must be checked for terms and robots permissions on every run.
SOURCES={
 'Just Horse Racing':'https://www.justhorseracing.com.au/tips/',
 'Racing and Sports':'https://www.racingandsports.com.au/news/racing/previews/',
 'Racenet':'https://www.racenet.com.au/',
 'Sky Racing':'https://www.skyracing.com.au/',
 'Punters':'https://www.punters.com.au/',
 'TAB':'https://www.tab.com.au/',
 'Sportsbet':'https://www.sportsbet.com.au/',
 'The Great Tip Off':'https://www.thegreattipoff.com/',
 'Racing.com':'https://www.racing.com/',
 'RacingBase':'https://www.racingbase.com.au/',
 'Bets.com.au':'https://www.bets.com.au/',
 'TAB NZ':'https://www.tab.co.nz/',
 'GoBet':'https://www.gobet.com.au/',
 'Racing SA':'https://www.racingsa.com.au/',
 'Before You Bet':'https://www.beforeyoubet.com.au/',
 'RSN':'https://www.rsn.net.au/',
}
USER_AGENT='MontyResearchBot/0.1 (research; respect robots.txt)'
def discover(source,url,max_links=30,fetcher=None):
    parts=urllib.parse.urlparse(url)
    if parts.scheme!='https' or not parts.hostname:raise ValueError('HTTPS source required')
    if fetcher is None:
        robots=urllib.robotparser.RobotFileParser()
        robots.set_url(f'{parts.scheme}://{parts.netloc}/robots.txt')
        try:
            robots.read()
        except Exception:
            return {'source':source,'status':'unavailable','reason':'Cannot check robots policy','articles':[]}
        if not robots.can_fetch(USER_AGENT,url):
            return {'source':source,'status':'rejected','reason':'Robots policy disallows fetch','articles':[]}
        request=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
        with urllib.request.urlopen(request,timeout=12) as response:
            if 'html' not in response.headers.get('Content-Type','').lower():
                raise ValueError('Source did not return HTML')
            html=response.read(600_000).decode('utf-8','replace')
    else:
        html=fetcher(url)
    soup=BeautifulSoup(html,'html.parser')
    seen=set();articles=[]
    for anchor in soup.select('a[href]'):
        label=anchor.get_text(' ',strip=True)
        href=urllib.parse.urljoin(url,anchor.get('href',''))
        link=urllib.parse.urlparse(href)
        if link.scheme!='https' or link.hostname!=parts.hostname:continue
        if href in seen or href==url:continue
        # Broad discovery, never parse these links as actual selections.
        if not re.search(r'(tip|best bet|preview|thursday best|racing)',label+' '+link.path,re.I):continue
        seen.add(href)
        articles.append({'url':href,'label':label[:180],'status':'located_unverified'})
        if len(articles)>=max_links:break
    return {'source':source,'status':'located' if articles else 'unavailable',
      'reason':'Article leads only; no tips or pre-off evidence established',
      'articles':articles}
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='expert_article_leads.json')
    p.add_argument('--source',choices=list(SOURCES))
    p.add_argument('--max-links',type=int,default=20)
    a=p.parse_args()
    out={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'sources':[],'verified_tip_count':0}
    for name,url in SOURCES.items():
        if a.source and name!=a.source:continue
        try:out['sources'].append(discover(name,url,max_links=a.max_links))
        except Exception as exc:out['sources'].append({'source':name,'status':'unavailable','reason':type(exc).__name__,'articles':[]})
    with open(a.output,'w') as f:json.dump(out,f,indent=2)
    print(json.dumps({'source_count':len(out['sources']),'article_leads':sum(len(s['articles']) for s in out['sources']),'verified_tip_count':0}))
if __name__=='__main__':main()
