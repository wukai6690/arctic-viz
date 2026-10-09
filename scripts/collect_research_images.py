"""Fetch a bounded set of dated NASA GIBS observations for editorial review.

Candidates are never published automatically. Review location, cloud cover,
dates and image content before adding any selected files to the website.
"""
import hashlib,io,json,sys
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.analysis-deps'))
from pyproj import Transformer
OUT=ROOT/'data/editorial/research_extension_images';OUT.mkdir(parents=True,exist_ok=True)
transform=Transformer.from_crs('EPSG:4326','EPSG:3413',always_xy=True)
layer='MODIS_Terra_CorrectedReflectance_TrueColor'
areas=[('sabetta',72.07,71.27,150000),('nyalesund',11.93,78.92,110000),('inuvik',-133.72,68.36,160000)]
jobs=[]
for pid,lon,lat,radius in areas:
    x,y=transform.transform(lon,lat)
    for date in ['2016-07-15','2016-08-05','2019-07-15','2023-07-15','2023-08-05','2025-07-15']:
        jobs.append((pid,date,[round(x-radius),round(y-radius),round(x+radius),round(y+radius)]))
def fetch(job):
    pid,date,bbox=job;target=OUT/f'{pid}-{date}.jpg'
    params={'SERVICE':'WMS','VERSION':'1.1.1','REQUEST':'GetMap','LAYERS':layer,'TIME':date,'STYLES':'','FORMAT':'image/jpeg','SRS':'EPSG:3413','WIDTH':900,'HEIGHT':900,'BBOX':','.join(map(str,bbox))}
    req=requests.Request('GET','https://gibs.earthdata.nasa.gov/wms/epsg3413/best/wms.cgi',params=params).prepare()
    try:
        if not target.exists():
            r=requests.get(req.url,timeout=65);r.raise_for_status()
            im=Image.open(io.BytesIO(r.content));assert im.size==(900,900)
            target.write_bytes(r.content)
        raw=target.read_bytes()
        result={'id':target.stem,'place_id':pid,'date':date,'bbox':bbox,'crs':'EPSG:3413','layer':layer,'url':req.url,'sha256':hashlib.sha256(raw).hexdigest(),'file':target.name,'credit':'NASA Worldview / EOSDIS GIBS · Terra MODIS','retrieved_at':datetime.fromtimestamp(target.stat().st_mtime,timezone.utc).isoformat(),'source_resolution':'250 m 影像图层；输出像素不代表新的空间分辨率'}
        print(target.name,flush=True);return result
    except Exception as e:
        print(f'FAILED {target.name}: {type(e).__name__}: {e}',flush=True);return {'id':target.stem,'error':str(e)}
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,jobs))
(OUT/'candidates.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
good=[r for r in results if 'error' not in r]
contact=Image.new('RGB',(6*210,3*240),'white');draw=ImageDraw.Draw(contact)
for i,r in enumerate(good):
    im=Image.open(OUT/r['file']);im.thumbnail((205,205));x=(i%6)*210;y=(i//6)*240
    contact.paste(im,(x,y));draw.text((x+3,y+208),r['id'],fill='black')
contact.save(OUT/'contact.jpg')
print('Downloaded',len(good),'of',len(jobs),flush=True)
