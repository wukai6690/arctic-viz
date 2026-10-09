"""Stage selected Commons images; publish only after explicit visual inspection."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import atlas_assets
from expand_real_photos import contact_sheets
OUT=ROOT/'data/editorial/place_enrichment'

def lookup():
    pages={}
    for folder in ['research','photo_expansion','place_enrichment']:
        for path in sorted((ROOT/'data/editorial'/folder).glob('*.json')):
            data=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data,dict):continue
            for page in data.get('query',{}).get('pages',{}).values():
                if page.get('imageinfo'):pages[str(page['pageid'])]=page
    return pages

def get_image(url,**kwargs):
    response=requests.get(url,headers=atlas_assets.AGENT,timeout=25,**kwargs)
    if response.status_code==429:
        response.close();time.sleep(60)
        response=requests.get(url,headers=atlas_assets.AGENT,timeout=25,**kwargs)
    response.raise_for_status();return response

def stage():
    atlas_assets.get=get_image
    pages=lookup();selection=json.loads((OUT/'selected.json').read_text(encoding='utf-8'))
    stage_path=OUT/'staged.json';staged=json.loads(stage_path.read_text(encoding='utf-8')) if stage_path.exists() else []
    done={p['photo']['id'] for p in staged};failed=[]
    for item in selection:
        if item['id'] in done:continue
        page=pages[item['id']];title=page['title'].removeprefix('File:')
        if page['imageinfo'][0]['width']<500:
            print('SKIP SMALL',item['id'],flush=True);continue
        try:
            _,photo=atlas_assets.publish_photo((item['owner'],[title,item['caption']],{title:page}))
            photo.update(topic=item['topic'],subject_scope=item['scope'],media_kind=item.get('media_kind','photograph'))
            staged.append({**item,'photo':photo});done.add(photo['id'])
            stage_path.write_text(json.dumps(staged,ensure_ascii=False,indent=2),encoding='utf-8')
            print('STAGED',item['owner'],photo['id'],flush=True)
        except Exception as error:
            failed.append({**item,'error':str(error)[:350]});print('FAILED',item['owner'],item['id'],str(error)[:150],flush=True)
        time.sleep(2)
    (OUT/'failed.json').write_text(json.dumps(failed,ensure_ascii=False,indent=2),encoding='utf-8')
    contact_sheets(staged)

def publish():
    staged=json.loads((OUT/'staged.json').read_text(encoding='utf-8'))
    decisions=json.loads((OUT/'review.json').read_text(encoding='utf-8'))
    assert {p['photo']['id'] for p in staged}==set(decisions),'Every image must be inspected'
    path=ROOT/'data/reference/places.json';catalog=json.loads(path.read_text(encoding='utf-8'))
    places={p['id']:p for p in catalog['places']}
    hashes={p['sha256'] for place in places.values() for p in place['photos']};added=0
    for item in staged:
        photo=item['photo'];decision=decisions[photo['id']]
        if decision['status']!='accept':continue
        if any(p['id']==photo['id'] for p in places[item['owner']]['photos']):continue
        local=ROOT/'static/places'/Path(photo['src']).name
        assert hashlib.sha256(local.read_bytes()).hexdigest()==photo['sha256']
        assert photo['sha256'] not in hashes
        photo.update(reviewed_at='2026-10-09',review_note=decision['note'],caption=decision.get('caption',photo['caption']))
        places[item['owner']]['photos'].append(photo);hashes.add(photo['sha256']);added+=1
    catalog.update(version='places-2026-10-09-v4',retrieved_at=datetime.now(timezone.utc).isoformat())
    temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)
    print('ADDED',added,'TOTAL PLACE PHOTOS',sum(len(p['photos']) for p in places.values()))

def thumbnails():
    selected=json.loads((OUT/'selected.json').read_text(encoding='utf-8'))
    pages=lookup();ids=[p['id'] for p in selected if 500<=pages[p['id']]['imageinfo'][0]['width']<1000]
    response=requests.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','pageids':'|'.join(ids),'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':500},headers=atlas_assets.AGENT,timeout=35)
    response.raise_for_status()
    (OUT/'zz-thumbnails.json').write_text(json.dumps(response.json(),ensure_ascii=False,indent=2),encoding='utf-8')
    print('THUMBNAILS',len(ids))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['stage','publish','thumbnails']);args=parser.parse_args()
    {'stage':stage,'publish':publish,'thumbnails':thumbnails}[args.mode]()
