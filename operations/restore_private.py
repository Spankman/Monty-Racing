"""Reuse the existing private-archive restore contract; never publish archive bytes."""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.parse
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from restore_archive import restore


def main():
    url=os.environ.get('V6_ARCHIVE_URL','').strip()
    if not url:
        print('Private archive source absent; existing artifact verification will decide readiness.')
        return
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Archive requires HTTPS without embedded credentials')
    headers={'User-Agent':'Monty-operations-restore','Accept':'application/vnd.github+json'}
    token=os.environ.get('V6_ARCHIVE_TOKEN','').strip()
    if token:headers['Authorization']='Bearer '+token
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):raise ValueError('Archive redirects prohibited')
    opener=urllib.request.build_opener(NoRedirect)
    def fetch(uri):
        if urllib.parse.urlsplit(uri).hostname!=parsed.hostname:raise ValueError('Archive host changed')
        with opener.open(urllib.request.Request(uri,headers=headers),timeout=60) as r:
            data=r.read(100_000_001)
        if len(data)>100_000_000:raise ValueError('Archive size limit')
        return data
    if parsed.hostname=='api.github.com' and '/contents/' in parsed.path:
        data=json.loads(fetch(url));sha=data['sha']
        blob=json.loads(fetch('https://api.github.com'+parsed.path.split('/contents/',1)[0]+'/git/blobs/'+sha))
        if blob.get('sha')!=sha or blob.get('encoding')!='base64':raise ValueError('Invalid archive blob')
        raw=base64.b64decode(blob['content'])
    else:raw=fetch(url)
    if len(raw)>100_000_000:raise ValueError('Archive size limit')
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'original.zip';p.write_bytes(raw)
        print('Original manifest-matching files restored:',restore(p))

if __name__=='__main__':main()
