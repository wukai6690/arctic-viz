"""Discover, stage, then append explicitly selected, licensed photographs."""
import argparse,concurrent.futures,hashlib,json,time,sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from atlas_assets import get,publish_photo
OUT=ROOT/'data/editorial/photo_expansion';OUT.mkdir(parents=True,exist_ok=True)
QUERIES={
 'mosaic':'MOSAiC expedition','chars':'Canadian High Arctic Research Station','awipev':'AWIPEV',
 'yamal':'Yamal LNG','asbm':'Arctic Satellite Broadband Mission','inuvik_station':'Inuvik Satellite Station',
 'bering':'Little Diomede island','rauma':'Rauma Finland harbour','greenland':'Ilulissat Icefjord',
 'kullorsuaq':'Kullorsuaq','kiruna':'Kiruna Sweden','nuuk':'Nuuk Greenland','pituffik':'Pituffik Space Base',
 'narvik':'Narvik harbour','kola':'Kola peninsula',
}
def search(key,query):
    target=OUT/(key+'.json')
    if not target.exists():
        data=get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json','generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':18,'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':1280}).json()
        target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return key,len(json.loads(target.read_text(encoding='utf-8')).get('query',{}).get('pages',{}))
def pages():
    result={}
    for directory in [ROOT/'data/editorial/research',OUT]:
        for path in directory.glob('*.json'):
            data=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data,dict):
                for item in data.get('query',{}).get('pages',{}).values():
                    if item.get('imageinfo'):result[item['title'].removeprefix('File:')]=item
    overrides=OUT/'thumb_overrides.json'
    if overrides.exists():
        for item in json.loads(overrides.read_text(encoding='utf-8')).get('query',{}).get('pages',{}).values():
            result[item['title'].removeprefix('File:')]=item
    return result
def stage():
    selections=json.loads((OUT/'selections.json').read_text(encoding='utf-8'));lookup=pages();result=[];failed=[]
    for item in selections:
        try:_,photo=publish_photo((item['owner'],[item['title'],item['caption']],lookup))
        except Exception as error:
            failed.append({'selection':item,'error':str(error)[:500]})
            print('FAILED',item['title'],str(error)[:120],flush=True)
            continue
        photo.update(subject_scope=item['subject_scope'],reviewed_at='2026-10-09',media_kind='photograph')
        result.append({**item,'photo':photo});print(item['owner'],photo['title'],flush=True)
        (OUT/'staged.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        time.sleep(2)
    (OUT/'failed_downloads.json').write_text(json.dumps(failed,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'staged.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    contact_sheets(result)
    print('STAGED',len(result),flush=True)

def contact_sheets(result):
    qa=ROOT/'test-results/photo-expansion';qa.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    for offset in range(0,len(result),12):
        sheet=Image.new('RGB',(1440,1100),'#edf4fa');draw=ImageDraw.Draw(sheet)
        for n,item in enumerate(result[offset:offset+12]):
            x=(n%3)*480;y=(n//3)*275
            with Image.open(ROOT/'static/places'/Path(item['photo']['src']).name) as im:
                thumb=ImageOps.contain(im.convert('RGB'),(464,232));sheet.paste(thumb,(x+(464-thumb.width)//2,y))
            draw.text((x+8,y+238),f'{offset+n+1}: {item["owner"]} / {item["photo"]["id"]}',font=font,fill='#243f57')
        sheet.save(qa/f'sheet-{offset//12+1:02}.jpg',quality=90)

def recover():
    # Ask Commons for its supported smaller thumbnail; do not alter the photograph.
    titles=['Yamalspg.jpg','Сабетта. СПГ.jpg']
    data=get('https://commons.wikimedia.org/w/api.php',params={'action':'query','format':'json',
        'titles':'|'.join('File:'+t for t in titles),'prop':'imageinfo','iiprop':'url|extmetadata|size','iiurlwidth':640}).json()
    (OUT/'thumb_overrides.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lookup={p['title'].removeprefix('File:'):p for p in data['query']['pages'].values()}
    selections=json.loads((OUT/'selections.json').read_text(encoding='utf-8'))
    result=json.loads((OUT/'staged.json').read_text(encoding='utf-8'));present={p['title'] for p in result}
    for item in selections:
        if item['title'] not in titles or item['title'] in present:continue
        try:_,photo=publish_photo((item['owner'],[item['title'],item['caption']],lookup))
        except Exception as error:print('UNAVAILABLE',item['title'],str(error)[:100],flush=True);continue
        photo.update(subject_scope=item['subject_scope'],reviewed_at='2026-10-09',media_kind='photograph')
        result.append({**item,'photo':photo});print('RECOVERED',item['title'],flush=True)
    order={item['title']:i for i,item in enumerate(selections)}
    result.sort(key=lambda item:order[item['title']])
    (OUT/'staged.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    contact_sheets(result)
def publish():
    items=json.loads((OUT/'staged.json').read_text(encoding='utf-8'))
    decisions=json.loads((OUT/'visual_review.json').read_text(encoding='utf-8'))
    if set(decisions)!={i['photo']['id'] for i in items}:raise ValueError('Every staged photograph needs an explicit visual decision')
    catalog=json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'));media=json.loads((ROOT/'data/reference/project_media.json').read_text(encoding='utf-8'))
    places={p['id']:p for p in catalog['places']};added=0
    existing={p['sha256'] for x in places.values() for p in x['photos']}|{p['sha256'] for x in media.values() for p in x}
    for item in items:
        photo=item['photo'];decision=decisions[photo['id']]
        if decision['status']!='accept':continue
        path=ROOT/'static/places'/Path(photo['src']).name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=photo['sha256']:raise ValueError('Image differs from the inspected file')
        target=places[item['owner']]['photos'] if item['kind']=='place' else media.setdefault(item['owner'],[])
        if any(p['id']==photo['id'] for p in target):continue
        if photo['sha256'] in existing:raise ValueError('Duplicate image content: '+photo['title'])
        photo['caption']=decision.get('caption',photo['caption'])
        photo['review_note']=decision['note'];target.append(photo);existing.add(photo['sha256']);added+=1
    catalog.update(version='places-2026-10-09-v3',retrieved_at=datetime.now(timezone.utc).isoformat())
    for name,value in [('places.json',catalog),('project_media.json',media)]:
        path=ROOT/'data/reference'/name;temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)
    print('ADDED',added,'PLACE',sum(len(p['photos']) for p in places.values()),'PROJECT',sum(len(p) for p in media.values()))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['search','stage','recover','publish']);a=p.parse_args()
    if a.mode=='search':
        for key,query in QUERIES.items():
            try:print(search(key,query),flush=True)
            except Exception as e:print(key,'FAILED',str(e)[:150],flush=True)
            time.sleep(2)
    elif a.mode=='stage':stage()
    elif a.mode=='recover':recover()
    else:publish()
