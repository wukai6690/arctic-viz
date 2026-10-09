"""Image provenance, filter accuracy, paging, and every project dossier."""
import json,logging,os,sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
from src.photo_views import photo_records,filter_photos
from src.research_catalog import project_media,research_catalog
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.ERROR)
records=photo_records()
assert len(records)==len({p['id'] for p in records})==len({p['sha256'] for p in records})
assert set(project_media())=={p['id'] for p in research_catalog()['projects']}
assert len(filter_photos(records,query='MOSAiC'))>=5
assert all(p['owner_id']=='mosaic' for p in filter_photos(records,owner='project:mosaic'))
assert not filter_photos(records,query='definitely-no-actual-photograph')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=40).run()
app.switch_page('pages/9_实景图集.py').run()
assert not app.exception
app.selectbox(key='gallery-page').set_value(2).run()
assert not app.exception
app.selectbox(key='gallery-kind').set_value('项目影像').run()
assert app.selectbox(key='gallery-page').value==1
app.selectbox(key='gallery-owner').set_value('project:mosaic').run()
assert len(app.get('imgs'))==len(project_media()['mosaic'])
app.text_input(key='gallery-query').set_value('no-such-photo-994').run()
assert any('没有符合条件' in x.value for x in app.info)
assert len(app.get('imgs'))==0
app.text_input(key='gallery-query').set_value('').run()
assert not app.exception
app.switch_page('pages/4_极地核心技术.py').run()
for project in research_catalog()['projects']:
    app.selectbox(key='project_choice').set_value(project['id']).run()
    assert not app.exception,project['id']
    assert len(app.get('imgs'))>=1,project['id']
    displayed=[x.value for x in app.markdown]
    assert any(project_media()[project['id']][0]['caption'] in s for s in displayed),project['id']
report={'photographs':len(records),'unique_files':len({p['sha256'] for p in records}),
    'projects_with_media':len(project_media()),'filter_paging_and_empty_state':'passed','all_project_photographs':'passed'}
out=ROOT/'test-results/photo-expansion';out.mkdir(parents=True,exist_ok=True)
(out/'gallery-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
