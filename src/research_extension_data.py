"""Frozen research cards, explicit evidence status and deterministic exports."""
import csv,io,json,zipfile
from src.presentation import ROOT

def extension_data():
    return json.loads((ROOT/'data/reference/research_extensions.json').read_text(encoding='utf-8'))

def extension_sources():
    original=json.loads((ROOT/'data/reference/research.json').read_text(encoding='utf-8'))
    return {s['id']:s for s in [*original['sources'],*extension_data()['sources']]}

def mechanism_rows(project_id=None,direction='全部方向',status='全部证据状态'):
    return [r for r in extension_data()['mechanisms']
            if (project_id is None or project_id in r['project_ids'])
            and (direction=='全部方向' or r['direction']==direction)
            and (status=='全部证据状态' or r['status']==status)]

def policy_comparison(left_id,right_id,theme):
    policies={p['id']:p for p in extension_data()['policies']}
    if left_id==right_id:raise ValueError('请选择两份不同的材料')
    if theme not in policies[left_id]['themes'] or theme not in policies[right_id]['themes']:raise ValueError('未知比较主题')
    return [dict(document=p['name'],date=p['date'],genre=p['genre'],theme=theme,reading=p['themes'][theme],source_id=p['source_id'],scope=p['scope']) for p in (policies[left_id],policies[right_id])]

def filtered_activities(project_id=None):
    return sorted([r for r in extension_data()['activities'] if project_id is None or r['project_id']==project_id],key=lambda r:r['date'])

def csv_bytes(rows):
    if not rows:return b'\xef\xbb\xbf'
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
    writer.writeheader()
    for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    return out.getvalue().encode('utf-8-sig')

def research_bundle(kind,selection,rows):
    """Only the selected material is exported; repeated inputs keep identical bytes."""
    sources=extension_sources();ids=set()
    def gather(value):
        if isinstance(value,dict):
            for key,v in value.items():
                if key=='source_id':ids.add(v)
                elif key in {'source_ids','extra_source_ids'}:ids.update(v)
                else:gather(v)
        elif isinstance(value,list):
            for v in value:gather(v)
    gather(rows)
    selected_sources=[sources[k] for k in sorted(ids)]
    manifest=dict(kind=kind,selection=selection,version=extension_data()['version'],reviewed_at=extension_data()['reviewed_at'],
                  interpretation='事实、主体表述、研究解释和假设情景分别保留。空缺不表示不存在；本包不包含未获授权的原网页全文。')
    content={'manifest.json':json.dumps(manifest,ensure_ascii=False,indent=2),'records.json':json.dumps(rows,ensure_ascii=False,indent=2),
             'sources.json':json.dumps(selected_sources,ensure_ascii=False,indent=2),'records.csv':csv_bytes(rows),
             '阅读说明.txt':'UTF-8 编码。manifest 为当前选择与版本；records 为所选内容；sources 为对应出处。假设情景不是预测或已发生事件。'}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in content.items():
            info=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,value)
    return buffer.getvalue()

def history_records(pid):
    path=ROOT/'data/reference/place_history.json'
    if not path.exists():return None
    return next((p for p in json.loads(path.read_text(encoding='utf-8'))['places'] if p['place_id']==pid),None)
