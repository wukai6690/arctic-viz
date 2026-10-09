"""Data joins, evidence boundaries, exact selections, and real Streamlit reruns."""
import hashlib,io,json,logging,os,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
from src.research_extension_data import *
from src.source_library import resolve_source
from src.research_catalog import research_catalog
from streamlit.testing.v1 import AppTest
for name in ['streamlit','streamlit.runtime.scriptrunner_utils.script_run_context']:logging.getLogger(name).setLevel(logging.ERROR)
d=extension_data();sources=extension_sources();projects={p['id'] for p in research_catalog()['projects']};checks=[]
def inspect(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=='source_id':assert v in sources,v
            elif k in ['source_ids','extra_source_ids']:assert all(x in sources for x in v),v
            elif k=='project_id':assert v in projects,v
            elif k=='project_ids':assert set(v)<=projects,v
            else:inspect(v)
    elif isinstance(obj,list):
        for v in obj:inspect(v)
inspect(d)
assert len({s['id'] for s in d['sources']})==len(d['sources'])
for s in d['sources']:
    record=resolve_source(s['url']);assert record['summary'] and record['locator'] and record['research_id']==s['id']
    assert len(s['excerpt'].split())<=25
assert all(mechanism_rows(p) for p in projects)
assert d['shipping']['observations']==[{'year':2013,'unique_ships':1298,'distance_million_nm':6.1},{'year':2025,'unique_ships':1812,'distance_million_nm':11.9}]
assert 'Polar Code' in d['shipping']['geography']
assert next(r for r in d['activities'] if r['id']=='mosaic-start')['stage']=='计划节点'
assert next(r for r in d['policies'] if r['id']=='no2021')['date']=='2021-01-26'
checks.append('Every source and project join resolves; all seven projects have evidence; plan/publication/operation dates stay distinct')
for left in d['policies']:
    for right in d['policies']:
        if left==right:continue
        for theme in left['themes']:
            rows=policy_comparison(left['id'],right['id'],theme);selection=dict(left=left['id'],right=right['id'],theme=theme)
            payload=research_bundle('policy',selection,rows)
            assert payload==research_bundle('policy',selection,rows)
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                assert z.testzip() is None
                assert json.loads(z.read('manifest.json'))['selection']==selection
                assert json.loads(z.read('records.json'))==rows
                ids={s['id'] for s in json.loads(z.read('sources.json'))};assert ids=={left['source_id'],right['source_id']}
try:policy_comparison('no2021','no2021','科研合作')
except ValueError:pass
else:raise AssertionError('Self-comparison was accepted')
checks.append('All 80 policy/topic combinations export exact choices and corresponding sources; archives are repeatable')
places=json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'))['places']
for p in places:
    h=history_records(p['id'])
    if not h:continue
    assert len(h['items'])>=3 and h['comparison_limit']
    photos={x['id']:x for x in p['photos']}
    for i in h['items']:
        x=photos[i['photo_id']];assert x['license'] and x['author'] and x['date']
        assert hashlib.sha256((ROOT/'static/places'/Path(x['src']).name).read_bytes()).hexdigest()==x['sha256']
checks.append('Historical photo groups use existing verified files and keep dates, attribution and limits')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
app.switch_page('pages/5_中国安全风险.py').run()
def healthy():assert not app.exception,[e.message for e in app.exception]
healthy()
app.selectbox(key='policy-left').set_value('no2025').run();healthy()
assert app.selectbox(key='policy-right').value!='no2025'
app.selectbox(key='policy-right').set_value('cn2018').run()
app.radio(key='policy-theme').set_value('技术与设施').run();healthy()
app.selectbox(key='mechanisms-direction').set_value('地缘与制度 → 技术').run();healthy()
assert app.selectbox(key='mechanisms-choice').value in ['asbm-demand','council-conditions']
app.selectbox(key='mechanisms-status').set_value('有分工事实').run();healthy()
assert any('没有对应材料' in e.value for e in app.info)
app.selectbox(key='mechanisms-status').set_value('全部证据状态').run();healthy()
for tid in ['science','data','transport','cooperation']:app.selectbox(key='security-task').set_value(tid).run();healthy()
for sid in ['comms','access','shipping']:
    app.selectbox(key='scenario-choice').set_value(sid).run();healthy()
    app.checkbox(key='scenario-changed-'+sid).check().run();healthy()
    assert app.radio(key='scenario-option-'+sid).value
app.selectbox(key='perspective-role').set_value('原住民组织').run();healthy()
checks.append('Policy changes reset incompatible selections; filters handle empty results; all four tasks and three hypothetical conditions run')
app.switch_page('pages/4_极地核心技术.py').run()
for pid in sorted(projects):
    app.selectbox(key='project_choice').set_value(pid).run();healthy()
    assert any(r['need']==m.value for r in d['capabilities'] if r['project_id']==pid for m in app.markdown)
checks.append('All seven project pages render capability/activity and mechanism tabs without errors')
app.switch_page('pages/8_区域联动研究.py').run();healthy()
app.radio(key='shipping-metric').set_value('航行距离').run();healthy()
app.selectbox(key='activities-project').set_value('asbm').run();healthy()
app.switch_page('pages/1_北极全景地图.py').run()
for pid in ['sabetta','kiruna','nyalesund','inuvik']:
    app.selectbox(key='atlas_choice').set_value(pid).run();healthy()
    h=history_records(pid)
    if h:
        app.selectbox(key='history-left-'+pid).set_value(h['items'][-1]['photo_id']).run();healthy()
        assert app.selectbox(key='history-right-'+pid).value!=h['items'][-1]['photo_id']
checks.append('Shipping/project activity views and time-stamped photo selectors rerun correctly; missing history stays explicit')
out=ROOT/'test-results/research-extension';out.mkdir(parents=True,exist_ok=True)
(out/'data-report.json').write_text(json.dumps({'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
