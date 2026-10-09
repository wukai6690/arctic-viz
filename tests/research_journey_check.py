"""Integrated navigation, source registration and downloadable report checks."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
TMP=ROOT/'test-results/tmp';TMP.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(TMP)
os.environ['ARCTIC_ENABLE_LOCAL_REVIEW']='0'
from streamlit.testing.v1 import AppTest
from src.source_library import resolve_source
from src.deep_case_content import load_deep_cases
import pymupdf

def run(path):
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
    if path!='app.py':app.switch_page(path).run()
    assert not app.exception,[e.message for e in app.exception]
    return app

home=run('app.py');assert any('阶段成果' in s.value for s in home.caption)
tour=run('pages/13_研究导览.py')
for stage in range(5):
    tour.radio(key='tour-stage').set_value(stage).run()
    assert not tour.exception
    assert tour.button[0] is not None
tour.radio(key='tour-stage').set_value(0).run()
next(b for b in tour.button if b.label=='下一步').click().run();assert tour.radio(key='tour-stage').value==1
case=run('pages/11_案例研究.py')
for cid in ['asbm','yamal','mosaic','yamal']:
    case.radio(key='case-choice').set_value(cid).run();assert not case.exception
    assert case.query_params['case']==[cid]
    assert any('PDF' in str(d.label) for d in case.get('download_button'))
case.switch_page('app.py').run()
case.session_state['_case_query_seen']='asbm';case.session_state['_case_pending']='asbm'
case.switch_page('pages/11_案例研究.py').run()
assert case.radio(key='case-choice').value=='asbm'
case.switch_page('app.py').run()
case.session_state['_case_pending']='asbm';case.switch_page('pages/11_案例研究.py').run()
assert case.radio(key='case-choice').value=='asbm' and not case.exception
for source in load_deep_cases()['sources']:
    record=resolve_source(source['url']);assert record['summary'] and source['id'] in record['research_ids']
reports=json.loads((ROOT/'static/reports/manifest.json').read_text(encoding='utf-8'))
for r in reports['reports']:
    path=ROOT/'static/reports'/r['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
    with pymupdf.open(path) as pdf:
        assert 3<=len(pdf)<=15
        assert all(len(page.get_text().strip())>40 for page in pdf)
        text=''.join(page.get_text() for page in pdf)
        assert '来源登记' in text
print('PASS: home, five tour steps, case switching/query, source resolution, and all report hashes/text/pages')
