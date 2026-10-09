"""Refresh explicitly selected open-license reading material and photo candidates.

This is an editorial collection command, never a request-time web scraper.
"""
import argparse, hashlib, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/library'
EDITORIAL = ROOT / 'data/editorial/place_enrichment'
TITLES = dict(zip(
    'bering rauma greenland kullorsuaq kiruna nuuk pituffik narvik kola longyearbyen nyalesund tromso svalsat esrange murmansk sabetta tiksi pevek reykjavik akureyri cambridgebay inuvik utqiagvik nome churchill resolute bremerhaven helsinki shanghai jiangnan'.split(),
    ['Bering Strait','Rauma, Finland','Greenland','Kullorsuaq','Kiruna','Nuuk','Pituffik Space Base','Narvik','Kola Peninsula','Longyearbyen','Ny-Ålesund','Tromsø','Svalbard Satellite Station','Esrange','Murmansk','Sabetta','Tiksi','Pevek','Reykjavík','Akureyri','Cambridge Bay','Inuvik','Utqiagvik, Alaska','Nome, Alaska','Churchill, Manitoba','Resolute, Nunavut','Bremerhaven','Helsinki','Shanghai','Jiangnan Shipyard']))
QUERIES = {
    'tiksi':'Tiksi harbour town', 'nome':'Nome Alaska city street',
    'bremerhaven':'Bremerhaven city harbour museum', 'helsinki':'Helsinki market square harbour',
    'shanghai':'Jiangnan Shipyard Changxing', 'svalsat':'Svalbard Satellite Station',
    'nyalesund':'Ny Alesund railway village', 'tromso':'Tromso bridge cathedral',
    'resolute':'Resolute Nunavut town', 'utqiagvik':'Utqiagvik Barrow whale bone',
    'inuvik':'Inuvik church town', 'cambridgebay':'Cambridge Bay Nunavut landscape',
    'murmansk':'Murmansk city Lenin', 'sabetta':'Sabetta Yamal LNG',
    'akureyri':'Akureyri church town', 'reykjavik':'Reykjavik city Tjornin',
    'churchill':'Churchill Manitoba polar bear', 'kullorsuaq':'Kullorsuaq settlement',
}
SESSION = requests.Session()
SESSION.headers['User-Agent'] = 'ArcticResearchStudentAtlas/0.4 (educational atlas; attribution retained)'

def fetch(url, params):
    response = SESSION.get(url, params=params, timeout=35)
    if response.status_code == 429:
        delay=response.headers.get('Retry-After','60')
        time.sleep(max(60, int(delay)) if delay.isdigit() else 60)
        response=SESSION.get(url, params=params, timeout=35)
    response.raise_for_status()
    return response.json()

def articles():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'texts').mkdir(exist_ok=True)
    registry = OUT/'articles.json'
    records = json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else {}
    rights_path = OUT/'wikipedia-rights.json'
    rights = json.loads(rights_path.read_text(encoding='utf-8')) if rights_path.exists() else fetch('https://en.wikipedia.org/w/api.php', {'action':'query','format':'json','meta':'siteinfo','siprop':'rightsinfo'})
    rights_path.write_text(json.dumps(rights, ensure_ascii=False, indent=2), encoding='utf-8')
    license_info = rights['query']['rightsinfo']
    for owner, title in TITLES.items():
        if owner in records and (OUT/records[owner]['text_path']).exists():
            print('CACHED', owner, flush=True); continue
        try:
            data = fetch('https://en.wikipedia.org/w/api.php', {'action':'query','format':'json','titles':title,'redirects':1,'prop':'extracts|info|revisions','explaintext':1,'exsectionformat':'wiki','inprop':'url','rvprop':'ids|timestamp'})
            page = next(iter(data['query']['pages'].values()))
            body = page.get('extract','').strip()
            if len(body) < 300 or not page.get('revisions'): raise ValueError('Missing article text or revision')
            revision = page['revisions'][0]
            path = 'texts/'+owner+'.txt'
            (OUT/path).write_text(body, encoding='utf-8')
            records[owner] = {'id':'wiki-'+owner, 'place_id':owner if owner!='jiangnan' else 'shanghai', 'title':page['title'], 'url':page['fullurl'], 'requested_url':'https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_')), 'publisher':'Wikipedia contributors', 'kind':'开放许可正文', 'language':'en', 'license':license_info['text'], 'license_url':license_info['url'], 'revision':revision['revid'], 'revised_at':revision['timestamp'], 'retrieved_at':datetime.now(timezone.utc).isoformat(), 'revision_url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision['revid']), 'history_url':page['fullurl']+'?action=history', 'text_path':path, 'sha256':hashlib.sha256((OUT/path).read_bytes()).hexdigest(), 'characters':len(body), 'changes':'API 提取的纯文本；保留正文，不含图片、脚注链接和版式。百科背景材料，不替代项目一手证据。'}
            registry.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
            print('SAVED', owner, page['title'], len(body), flush=True)
        except Exception as error:
            print('FAILED',owner,str(error)[:180],flush=True)
            if isinstance(error,requests.HTTPError) and error.response.status_code==429:break
        time.sleep(8)

def photos():
    EDITORIAL.mkdir(parents=True, exist_ok=True)
    for owner, query in QUERIES.items():
        target=EDITORIAL/(owner+'.json')
        if target.exists(): continue
        try:
            data=fetch('https://commons.wikimedia.org/w/api.php', {'action':'query','format':'json','generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':16,'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':960})
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2),encoding='utf-8')
            print('PHOTOS',owner,len(data.get('query',{}).get('pages',{})),flush=True)
        except Exception as error:
            print('FAILED',owner,str(error)[:180],flush=True)
            if isinstance(error,requests.HTTPError) and error.response.status_code==429:break
        time.sleep(8)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['articles','photos']);parser.add_argument('--owners',nargs='*');args=parser.parse_args()
    if args.owners:QUERIES={k:v for k,v in QUERIES.items() if k in args.owners}
    articles() if args.mode=='articles' else photos()
