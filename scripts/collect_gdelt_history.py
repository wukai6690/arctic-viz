"""Resumable GDELT 1.0 daily backfill. Source dates never imply event-occurrence coverage."""
import argparse,csv,hashlib,io,json,math,re,sys,time,zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlparse,unquote
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.study_data import DATA,safe_url
TERMS=('arctic','svalbard','spitsbergen','barents','kara sea','chukchi','beaufort','greenland','murmansk','tromso','tromsø','sabetta','northern sea route','northwest passage','ny-alesund','北极','格陵兰')
QUAD={1:'言语合作',2:'物质合作',3:'言语冲突',4:'物质冲突'}
FILTER_VERSION='arctic-candidate-v3-word-boundaries'

def relevance_terms(text):
    text=re.sub(r'[-_]+',' ',unquote(text).casefold())
    return [t for t in TERMS if re.search(r'(?<![a-z])'+re.escape(t.replace('-',' '))+r'(?![a-z])',text)]

def parse_archive(body,archive_date,source_id):
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        files=[f for f in archive.infolist() if not f.is_dir()]
        if len(files)!=1 or files[0].file_size>350_000_000:raise ValueError('Unexpected ZIP contents/size')
        content=archive.read(files[0])
    records={};quarantine=[];scanned=0
    for line,r in enumerate(csv.reader(io.StringIO(content.decode('utf-8-sig')),delimiter='\t'),1):
        scanned+=1
        try:
            if len(r)!=58:raise ValueError('expected 58 columns')
            event_date=datetime.strptime(r[1],'%Y%m%d').date().isoformat()
            if event_date>archive_date:raise ValueError('future event date within archive')
            lat=float(r[53]) if r[53] else None;lon=float(r[54]) if r[54] else None
            if lat is not None and (not math.isfinite(lat) or not -90<=lat<=90):raise ValueError('latitude')
            if lon is not None and (not math.isfinite(lon) or not -180<=lon<=180):raise ValueError('longitude')
            geo=int(r[49]);quad=int(r[29]);hits=relevance_terms(r[50]+' '+r[57])
            if not hits and not (lat is not None and lat>=66.563):continue
            if not r[0].isdigit() or quad not in QUAD:raise ValueError('event identifier/class')
            if not safe_url(r[57]):raise ValueError('source URL')
            if not math.isfinite(float(r[30])):raise ValueError('non-finite Goldstein value')
            rid='gdelt1:'+r[0]
            records[rid]=dict(id=rid,gdelt_id=r[0],dataset='GDELT 1.0',date=event_date,archive_date=archive_date,actor1=r[6],actor2=r[16],actor1_country=r[7],actor2_country=r[17],event_code=r[26],quad_class=quad,category=QUAD[quad],goldstein=float(r[30]),latitude=lat,longitude=lon,geo_type=geo,location=r[50],source_url=r[57],source_id=source_id,source_line=line,relevance_reasons=hits or ['北极圈以北地理编码'],status='pending')
        except (ValueError,IndexError) as e:quarantine.append({'line':line,'reason':str(e)})
    return list(records.values()),dict(scanned_rows=scanned,candidate_rows=len(records),quarantine_count=len(quarantine),quarantine=quarantine)

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False),encoding='utf-8');temp.replace(path)

def collect_day(day,reprocess=False):
    iso=day.isoformat();out=DATA/'gdelt/daily'/f'{iso}.json';raw=DATA/'raw/gdelt'/f'{day:%Y%m%d}.export.CSV.zip'
    previous=json.loads(out.read_text(encoding='utf-8')) if out.exists() else None
    if previous and not reprocess:
        if previous['source']['filter_version']!=FILTER_VERSION:raise ValueError('Cached filter is outdated; run with --reprocess')
        return {'date':iso,'status':'cached'}
    url=f'https://data.gdeltproject.org/events/{day:%Y%m%d}.export.CSV.zip';raw.parent.mkdir(parents=True,exist_ok=True)
    if raw.exists():body=raw.read_bytes()
    else:
        error=None
        for attempt in range(3):
            try:
                with requests.get(url,stream=True,timeout=(15,90),headers={'User-Agent':'ArcticResearch/0.2 (academic archive study)'}) as response:
                    response.raise_for_status()
                    if urlparse(response.url).hostname!='data.gdeltproject.org':raise ValueError('Unexpected redirect')
                    chunks=[];size=0
                    for chunk in response.iter_content(262144):
                        size+=len(chunk)
                        if size>80_000_000:raise ValueError('Daily archive exceeds 80 MB limit')
                        chunks.append(chunk)
                    body=b''.join(chunks)
                # Validate ZIP CRC before storing.
                with zipfile.ZipFile(io.BytesIO(body)) as z:
                    if z.testzip():raise ValueError('ZIP CRC mismatch')
                raw.write_bytes(body);break
            except Exception as exc:
                error=exc
                if attempt==2:raise
                time.sleep(1+attempt)
    digest=hashlib.sha256(body).hexdigest();source_id='gdelt1:'+digest
    records,stats=parse_archive(body,iso,source_id)
    if previous and previous['source']['sha256']!=digest:raise ValueError('Raw archive differs from the recorded SHA256')
    source=dict(id=source_id,url=url,sha256=digest,bytes=len(body),retrieved_at=previous['source']['retrieved_at'] if previous else datetime.now(timezone.utc).isoformat(),processed_at=datetime.now(timezone.utc).isoformat(),dataset='GDELT 1.0',filter_version=FILTER_VERSION)
    coverage=dict(archive_date=iso,status='complete' if not stats['quarantine_count'] else 'quarantined',**{k:v for k,v in stats.items() if k!='quarantine'})
    atomic(out,dict(source=source,coverage=coverage,records=records,quarantine=stats['quarantine']))
    return {'date':iso,**coverage}

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',required=True);p.add_argument('--end',required=True);p.add_argument('--max-files',type=int,default=31);p.add_argument('--workers',type=int,default=2);p.add_argument('--reprocess',action='store_true');a=p.parse_args()
    start,end=date.fromisoformat(a.start),date.fromisoformat(a.end)
    if not date(2013,4,1)<=start<=end<date.today():raise ValueError('Use completed GDELT daily archive dates from 2013-04-01')
    if not 1<=a.max_files<=366 or not 1<=a.workers<=3:raise ValueError('Bounded runs: 1–366 files, 1–3 workers')
    days=[start+timedelta(days=i) for i in range((end-start).days+1)];todo=[d for d in days if a.reprocess or not (DATA/'gdelt/daily'/f'{d.isoformat()}.json').exists()][:a.max_files]
    results=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(collect_day,d,a.reprocess):d for d in todo}
        for future in as_completed(futures):
            try:result=future.result()
            except Exception as e:result={'date':futures[future].isoformat(),'status':'failed','reason':str(e)}
            results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
    atomic(DATA/'gdelt/last_run.json',dict(start=a.start,end=a.end,requested_days=len(days),processed=results,remaining=sum(not (DATA/'gdelt/daily'/f'{d.isoformat()}.json').exists() for d in days),completed_at=datetime.now(timezone.utc).isoformat()))
    if any(r['status']=='failed' for r in results):sys.exit(1)

if __name__=='__main__':main()
