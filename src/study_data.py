"""Research scope, coverage-aware summaries and local evidence review."""
from __future__ import annotations
import calendar, hashlib, json, math, re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/analysis'
ASSOCIATIONS={
 'barents':['murmansk','kola','tromso','longyearbyen','nyalesund','svalsat','narvik'],
 'kara':['sabetta'],
 'chukchi':['utqiagvik','bering','nome','pevek'],
}
# These are research background links to coastal/service nodes, not points inside sea polygons.
PROJECT_REGIONS={'mosaic':['barents'],'awipev':['barents'],'yamal':['kara'],'asbm':['barents','kara','chukchi']}

def read_json(name,default=None):
    path=DATA/name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def regional_data():return read_json('regional_ice.json')
def region_definitions():return {r['id']:r for r in regional_data()['regions']}
def region_geometry():return read_json('regions.geojson')
def ice_frame():return pd.DataFrame(regional_data()['records'])

def monthly_summary(region_id,month,start,end,metric='extent'):
    if metric not in ['extent','area'] or not 1<=month<=12 or start>end:raise ValueError('Invalid comparison scope')
    df=ice_frame();field=metric+'_km2'
    frame=df[(df.region_id==region_id)&(df.month==month)&df.year.between(start,end)].set_index('year').reindex(range(start,end+1))
    valid=frame[field].dropna();n=len(valid);baseline=frame[metric+'_baseline_km2'].dropna()
    low_years=valid.index[np.isclose(valid,valid.min(),atol=.0005,rtol=0)].tolist() if n else []
    # Descriptive least-squares slope only: not a causal estimate or significance test.
    slope=float(np.polyfit(valid.index.to_numpy(dtype=float),valid.to_numpy(dtype=float),1)[0]*10) if n>=3 else None
    residual=None
    if n>=4 and len(valid)==end-start+1:
        residual=valid.to_numpy()-np.polyval(np.polyfit(valid.index.to_numpy(dtype=float),valid.to_numpy(),1),valid.index)
    ac=float(np.corrcoef(residual[:-1],residual[1:])[0,1]) if residual is not None and np.std(residual)>1e-8 and np.std(residual[:-1])>1e-8 and np.std(residual[1:])>1e-8 else None
    return dict(n=n,expected=end-start+1,missing=end-start+1-n,low_years=low_years,min_km2=float(valid.min()) if n else None,
                mean_km2=float(valid.mean()) if n else None,baseline_km2=float(baseline.iloc[0]) if len(baseline) else None,slope_per_decade_km2=slope,residual_lag1=ac,series=frame.reset_index())

def project_nodes(region,start,end):
    catalog=json.loads((ROOT/'data/reference/research.json').read_text(encoding='utf-8'))
    sources={s['id']:s for s in catalog['sources']};rows=[]
    for p in catalog['projects']:
        direct=PROJECT_REGIONS.get(p['id'],[])
        if region!='all' and region not in direct:continue
        for item in p['timeline']:
            if start<=int(item['date'][:4])<=end:
                rows.append(dict(project_id=p['id'],project=p['title'],date=item['date'],precision=item['precision'],label=item['label'],source_url=sources[item['source_id']]['url'],scope='北极服务背景' if p['id']=='asbm' else '区域关联案例'))
    return sorted(rows,key=lambda r:r['date'])

def safe_url(url):
    p=urlparse(str(url));return p.scheme in ['http','https'] and bool(p.hostname) and not p.username

def candidates():
    merged={}
    for path in sorted((DATA/'gdelt/daily').glob('*.json')):
        for r in json.loads(path.read_text(encoding='utf-8'))['records']:
            if r['id'] not in merged:merged[r['id']]={**r,'archive_dates':[r['archive_date']]}
            elif r['archive_date'] not in merged[r['id']]['archive_dates']:merged[r['id']]['archive_dates'].append(r['archive_date'])
    for key,review in reviews().items():
        if key in merged:merged[key].update(review)
    return list(merged.values())

def reviews():
    path=DATA/'event_reviews.jsonl';result={}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                item=json.loads(line);result[item['id']]=item
    return result

def verified_events():
    """Count reviewed real-world events once, not articles or machine-coded records."""
    grouped={}
    for r in candidates():
        if r.get('status')!='verified':continue
        key=r['event_key']
        if key not in grouped:grouped[key]={'event_key':key,'date':r['event_date'],'region_id':r['region_id'],'claim':r['claim'],'candidate_ids':[],'evidence_urls':[]}
        grouped[key]['candidate_ids'].append(r['id'])
        if r['evidence_url'] not in grouped[key]['evidence_urls']:grouped[key]['evidence_urls'].append(r['evidence_url'])
    return sorted(grouped.values(),key=lambda r:r['date'])

def save_review(record_id,status,reviewer,note,event_key='',event_date='',region_id='',evidence_url='',claim=''):
    if status not in ['verified','excluded','pending']:raise ValueError('Unknown review status')
    if not reviewer.strip() or len(note.strip())<8:raise ValueError('请填写核验人和至少 8 字的核验说明。')
    if any(len(str(x))>10000 for x in [reviewer,note,event_key,evidence_url,claim]):raise ValueError('单项内容过长。')
    if record_id not in {x['id'] for x in candidates()}:raise ValueError('Candidate no longer exists')
    if status=='verified':
        if not event_key.strip() or not claim.strip() or region_id not in [*region_definitions(),'pan_arctic']:raise ValueError('确认事件需要事件归并编号、事实摘要和研究区域。')
        if not safe_url(evidence_url):raise ValueError('请填写可打开的原文依据网址。')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',event_date) or date.fromisoformat(event_date)>date.today():raise ValueError('请填写有效的事件日期，且不能晚于今天。')
        for other in reviews().values():
            if other['id']!=record_id and other.get('status')=='verified' and other.get('event_key')==event_key and (other.get('event_date'),other.get('region_id'))!=(event_date,region_id):
                raise ValueError('同一现实事件编号已有不同日期或区域，请核对后合并。')
    record=dict(id=record_id,status=status,reviewer=reviewer.strip(),note=note.strip(),event_key=event_key.strip(),event_date=event_date,region_id=region_id,evidence_url=evidence_url,claim=claim,reviewed_at=datetime.now(timezone.utc).isoformat())
    DATA.mkdir(parents=True,exist_ok=True)
    with (DATA/'event_reviews.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    return record

def coverage_records():
    return [json.loads(p.read_text(encoding='utf-8'))['coverage'] for p in sorted((DATA/'gdelt/daily').glob('*.json'))]

def coverage_table(start,end):
    ice=ice_frame();coverage=coverage_records();rows=[]
    for year in range(start,end+1):
        dates={r['archive_date'] for r in coverage if r['archive_date'].startswith(str(year)) and r['status']=='complete'}
        days=366 if calendar.isleap(year) else 365
        for region in region_definitions().values():
            count=int(ice[(ice.region_id==region['id'])&(ice.year==year)].extent_km2.notna().sum())
            rows.append({'海区':region['name'],'年份':year,'海冰有效月份':count,'海冰应有月份':12,'GDELT已采集日档':len(dates),'GDELT全年日档':days,'GDELT说明':'日档齐全，仍需事件核验' if len(dates)==days else '有限窗口，不能按全年计数','专利':'检索样本，非完整年度统计'})
    return pd.DataFrame(rows)

PATENT_COLUMNS=['publication_id','family_id','title','priority_date','publication_date','applicant','technology','source_url','relevance_note']
def validate_patents(frame):
    missing=set(PATENT_COLUMNS)-set(frame.columns)
    if missing:raise ValueError('缺少字段：'+', '.join(sorted(missing)))
    if not 0<len(frame)<=50000:raise ValueError('一次导入需有 1—50,000 条记录。')
    clean=frame.fillna('').copy();issues=[];seen=set();families={}
    for index,row in clean.iterrows():
        line=int(index)+2
        try:
            if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]+',str(row.publication_id)):raise ValueError('公开号格式错误')
            for name in PATENT_COLUMNS:
                if not str(row[name]).strip():raise ValueError(name+' 为空')
            priority=date.fromisoformat(str(row.priority_date));publication=date.fromisoformat(str(row.publication_date))
            if priority>publication or publication>date.today():raise ValueError('日期顺序错误或公开日期在未来')
            if not safe_url(row.source_url):raise ValueError('来源网址格式错误')
            if row.publication_id in seen:raise ValueError('重复公开号')
            seen.add(row.publication_id)
            if row.family_id in families and families[row.family_id]!=str(row.priority_date):raise ValueError('同一专利族的最早优先权日不一致')
            families[row.family_id]=str(row.priority_date)
        except ValueError as e:issues.append({'行':line,'原因':str(e)})
    if issues:return None,issues
    # A family table is a descriptive sample. Multiple technologies stay as labels, not multiple inventions.
    family=clean.sort_values(['priority_date','publication_date']).groupby('family_id',as_index=False).agg(priority_date=('priority_date','first'),title=('title','first'),applicant=('applicant',lambda x:'；'.join(sorted(set(x)))),technology=('technology',lambda x:'；'.join(sorted(set(x)))),publication_count=('publication_id','count'),source_url=('source_url','first'))
    return family,[]

def collection_progress():
    items=coverage_records()
    return dict(files=len(items),days=sorted({i['archive_date'] for i in items}),candidates=len(candidates()),reviewed=len([r for r in reviews().values() if r['status']=='verified']))
