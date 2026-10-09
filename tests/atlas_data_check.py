"""Validate source joins, coordinates, image identity, and generate QA sheets."""
import hashlib,json,math
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/research'
OUT.mkdir(parents=True,exist_ok=True)
catalog=json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'))
research=json.loads((ROOT/'data/reference/research.json').read_text(encoding='utf-8'))
media=json.loads((ROOT/'data/reference/project_media.json').read_text(encoding='utf-8'))
places=catalog['places'];ids={p['id'] for p in places};source_ids={s['id'] for s in research['sources']}
assert len(ids)==len(places)==29
photos=[]
for p in places:
    assert -90<=p['latitude']<=90 and -180<=p['longitude']<=180,p['id']
    assert len(p['photos'])>=3,p['id']
    assert len({x['sha256'] for x in p['photos']})==len(p['photos'])
    photos.extend((p['id'],i,x) for i,x in enumerate(p['photos'],1))
photos.extend((pid,i,x) for pid,items in media.items() for i,x in enumerate(items,1))
for pid,i,photo in photos:
    path=ROOT/'static/places'/Path(photo['src']).name
    assert photo['author'] and photo['license_url'] and photo['source_url'],(pid,i)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==photo['sha256'],(pid,i)
    with Image.open(path) as im:assert min(im.size)>=150;im.verify()
for p in research['projects']:
    assert set(p['place_ids'])<=ids
    for item in p['facts']+p['timeline']+p['relationships']:assert item['source_id'] in source_ids,item
    assert p['limits'] and p['interpretation']
    assert len({e['id'] for e in p['relationships']})==len(p['relationships'])
assert not next(p for p in research['projects'] if p['id']=='asbm')['place_ids']
assert all('HK ' not in x['title'] and 'Victoria' not in x['title'] for x in next(p for p in places if p['id']=='shanghai')['photos'])
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
new=[x for x in photos if x[0] not in ['bering','rauma','greenland','kullorsuaq','kiruna','nuuk','pituffik','narvik','kola']]
for start in range(0,len(new),12):
    sheet=Image.new('RGB',(1200,880),'#f5f7f3');draw=ImageDraw.Draw(sheet)
    for n,(pid,i,photo) in enumerate(new[start:start+12]):
        col=n%3;row=n//3
        with Image.open(ROOT/'static/places'/Path(photo['src']).name) as im:
            thumb=ImageOps.contain(im.convert('RGB'),(388,185));sheet.paste(thumb,(col*400+(388-thumb.width)//2,row*220))
        draw.text((col*400+8,row*220+190),f'{pid} #{i}',font=font,fill='#304d43')
    sheet.save(OUT/f'photo-review-{start//12+1}.jpg',quality=88)
report={'places':len(places),'place_photos':sum(len(p['photos']) for p in places),'project_photos':sum(len(x) for x in media.values()),'projects':len(research['projects']),'relationships':sum(len(p['relationships']) for p in research['projects']),'primary_sources':len(source_ids),'validated_images':len(photos),'joins_and_coordinates':'passed'}
(OUT/'data-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
