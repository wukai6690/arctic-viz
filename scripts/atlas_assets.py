"""Discover Commons assets, then publish only explicitly reviewed selections."""
import argparse, concurrent.futures, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/editorial/research'
AGENT={'User-Agent':'ArcticResearchStudentAtlas/0.3 (educational geography atlas; Wikimedia attribution retained)'}
QUERIES={
 'longyearbyen':('Longyearbyen','Longyearbyen'),
 'nyalesund':('Ny Alesund research station','Ny-Ålesund'),
 'tromso':('Tromso harbour city','Tromsø'),
 'svalsat':('Svalbard Satellite Station','Svalbard Satellite Station'),
 'esrange':('Esrange Space Center','Esrange'),
 'murmansk':('Murmansk port','Murmansk'),
 'sabetta':('Sabetta port','Sabetta'),
 'tiksi':('Tiksi','Tiksi'),
 'pevek':('Pevek port','Pevek'),
 'reykjavik':('Reykjavik harbour','Reykjavík'),
 'akureyri':('Akureyri harbour','Akureyri'),
 'cambridgebay':('Cambridge Bay Nunavut','Cambridge Bay'),
 'inuvik':('Inuvik town','Inuvik'),
 'utqiagvik':('Utqiagvik Barrow Alaska','Utqiagvik, Alaska'),
 'nome':('Nome Alaska port','Nome, Alaska'),
 'churchill':('Churchill Manitoba town port','Churchill, Manitoba'),
 'resolute':('Resolute Nunavut','Resolute, Nunavut'),
 'bremerhaven':('Polarstern Bremerhaven','Bremerhaven'),
 'helsinki':('Helsinki icebreaker harbour','Helsinki'),
 'shanghai':('Xue Long 2','Shanghai'),
 'shanghai_extra':('Jiangnan Shipyard','Shanghai'),
 'churchill_extra':('Churchill Manitoba','Churchill, Manitoba'),
 'helsinki_extra':('Katajanokka icebreakers','Helsinki'),
}

def get(url,**kwargs):
    for attempt in range(3):
        try:
            r=requests.get(url,headers=AGENT,timeout=45,**kwargs)
            if r.status_code==429:
                delay=r.headers.get('Retry-After','30')
                time.sleep(min(60,max(15,int(delay))) if delay.isdigit() else 30)
            r.raise_for_status();return r
        except requests.RequestException:
            if attempt==2:raise
            time.sleep(2+attempt*2)

def discover(item):
    key,(query,wiki)=item
    f=OUT/(key+'.json')
    data=json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
    if not data.get('query',{}).get('pages'):
        data=get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':12,'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':960}).json()
        f.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    coord=OUT/(key+'-coordinates.json')
    if not coord.exists():
        try:
            value=get('https://en.wikipedia.org/w/api.php',params={'action':'query','format':'json','titles':wiki,'prop':'coordinates|pageprops','coprimary':'primary','redirects':1}).json()
            coord.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as e:print(key,'coordinate lookup:',type(e).__name__,flush=True)
    pages=sorted(data.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',0))
    plain=lambda text:BeautifulSoup(text or '', 'html.parser').get_text(' ',strip=True)
    candidates=[{'id':p['pageid'],'title':p['title'].removeprefix('File:'),'description':plain(p['imageinfo'][0]['extmetadata'].get('ImageDescription',{}).get('value',''))[:350],'license':p['imageinfo'][0]['extmetadata'].get('LicenseShortName',{}).get('value','')} for p in pages if p.get('imageinfo')]
    (OUT/(key+'-summary.json')).write_text(json.dumps(candidates,ensure_ascii=False,indent=2),encoding='utf-8')
    return key,len(candidates)

def publish_photo(task):
    place_id,selection,pages=task
    title,caption=selection
    page=pages[title];info=page['imageinfo'][0];meta=info['extmetadata']
    def value(k):return BeautifulSoup(meta.get(k,{}).get('value',''),'html.parser').get_text(' ',strip=True)
    license_name=value('LicenseShortName')
    if not license_name.startswith(('CC BY','CC0','Public domain')):raise ValueError((title,license_name))
    filename=f'{place_id}-{page["pageid"]}.jpg';target=ROOT/'static/places'/filename
    url=info.get('thumburl',info['url']).split('?')[0]
    if target.exists():content=target.read_bytes()
    else:
        response=get(url,stream=True)
        if not response.headers.get('Content-Type','').startswith('image/'):raise ValueError('Invalid image '+title)
        content=b''
        for chunk in response.iter_content(65536):
            content+=chunk
            if len(content)>12*1024*1024:raise ValueError('Oversized image '+title)
    with Image.open(io.BytesIO(content)) as im:
        width,height=im.size;im.verify()
    if width<500 or height<150:raise ValueError('Small image '+title)
    target.write_bytes(content)
    return place_id,dict(id=str(page['pageid']),title=title,caption=caption,src='/app/static/places/'+filename,
        source_url=info['descriptionurl'],original_url=info['url'],download_url=url,author=value('Artist') or value('Credit'),
        license=license_name,license_url=value('LicenseUrl') or 'https://commons.wikimedia.org/wiki/Commons:Public_domain',
        date=value('DateTimeOriginal') or '来源未注明拍摄日期',width=width,height=height,sha256=hashlib.sha256(content).hexdigest(),bytes=len(content),
        changes='使用来源提供的缩略版本；保留完整画面。')

def publish():
    definitions=json.loads((ROOT/'data/editorial/atlas_additions.json').read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'))
    pages={}
    for path in OUT.glob('*.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict):continue
        for p in value.get('query',{}).get('pages',{}).values():
            if p.get('imageinfo'):pages[p['title'].removeprefix('File:')]=p
    photos={p['id']:[] for p in definitions}
    tasks=[(p['id'],s,pages) for p in definitions for s in p['files']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for pid,photo in pool.map(publish_photo,tasks):photos[pid].append(photo);print(pid,photo['title'],flush=True)
    selections=json.loads((ROOT/'data/editorial/project_media_selections.json').read_text(encoding='utf-8'))
    media_path=ROOT/'data/reference/project_media.json'
    project_media=json.loads(media_path.read_text(encoding='utf-8')) if media_path.exists() else {}
    for pid,items in selections.items():
        refreshed=[publish_photo((pid,item,pages))[1] for item in items]
        refreshed_ids={p['id'] for p in refreshed}
        project_media[pid]=refreshed+[p for p in project_media.get(pid,[]) if p['id'] not in refreshed_ids]
    (ROOT/'data/reference/project_media.json').write_text(json.dumps(project_media,ensure_ascii=False,indent=2),encoding='utf-8')
    by_id={p['id']:p for p in catalog['places']}
    for p in definitions:
        coords=json.loads((OUT/(p['id']+'-coordinates.json')).read_text(encoding='utf-8'))
        wp=next(iter(coords['query']['pages'].values()));coordinate=wp['coordinates'][0]
        item={k:v for k,v in p.items() if k!='files'}
        refreshed_ids={photo['id'] for photo in photos[p['id']]}
        photos[p['id']]+=[photo for photo in by_id.get(p['id'],{}).get('photos',[]) if photo['id'] not in refreshed_ids]
        item.update(latitude=coordinate['lat'],longitude=coordinate['lon'],photos=photos[p['id']],aliases=p.get('aliases',[]),
            coordinate_source='https://en.wikipedia.org/wiki/'+quote(wp['title'].replace(' ','_')),
            coordinate_precision='地点中心的公开目录坐标；非事件定位',reviewed_at='2026-10-09')
        by_id[p['id']]=item
    catalog.update(version='places-2026-10-09-v3',retrieved_at=datetime.now(timezone.utc).isoformat(),places=list(by_id.values()))
    (ROOT/'data/reference/places.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PUBLISHED',len(by_id),'places',sum(len(p['photos']) for p in by_id.values()),'photos')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['search','publish']);parser.add_argument('--only',nargs='*');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.mode=='publish':publish()
    else:
        items=[x for x in QUERIES.items() if not args.only or x[0] in args.only]
        for item in items:
            try:
                key,count=discover(item);print(key,count,flush=True)
            except Exception as error:print(item[0],type(error).__name__,str(error)[:100],flush=True)
            time.sleep(3)
