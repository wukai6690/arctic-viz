"""Real navigation regressions: submitted records and matching map/detail state."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'test-results/tmp';OUT.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(OUT);os.environ['ARCTIC_ENABLE_LOCAL_REVIEW']='0'
from streamlit.testing.v1 import AppTest

def by_label(elements,label):return next(e for e in elements if e.label==label)
def healthy(app):assert not app.exception,[e.message for e in app.exception]

app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
app.switch_page('pages/12_研究过程.py').run();healthy(app)
by_label(app.text_input,'记录编号').set_value('audit-plan-only')
by_label(app.text_area,'这次活动要回答什么问题').set_value('界面测试用计划；未开展调研。')
by_label(app.selectbox,'活动类型').select('用户试用')
by_label(app.button,'整理为可下载记录').click().run();healthy(app)
expected=dict(app.session_state['_fieldwork_export'])
app.switch_page('app.py').run().switch_page('pages/12_研究过程.py').run();healthy(app)
assert by_label(app.text_input,'记录编号').value==expected['id']
assert by_label(app.text_area,'这次活动要回答什么问题').value==expected['question']
assert by_label(app.selectbox,'活动类型').value=='用户试用'
assert dict(app.session_state['_fieldwork_export'])==expected
by_label(app.text_area,'记录摘要').set_value('继续修改的是同一份测试计划。')
by_label(app.button,'整理为可下载记录').click().run()
assert app.session_state['_fieldwork_export']['summary']=='继续修改的是同一份测试计划。'
by_label(app.text_input,'记录编号').set_value('bad id')
by_label(app.button,'整理为可下载记录').click().run()
app.switch_page('app.py').run().switch_page('pages/12_研究过程.py').run();healthy(app)
assert by_label(app.text_input,'记录编号').value=='bad id'
assert '_fieldwork_export' not in app.session_state
by_label(app.button,'开始新记录').click().run();healthy(app)
assert by_label(app.text_input,'记录编号').value=='' and by_label(app.selectbox,'活动类型').value=='访谈'
assert '_fieldwork_export' not in app.session_state

app.switch_page('pages/1_北极全景地图.py').run()
app.selectbox(key='atlas_choice').select('sabetta').run()
app.switch_page('pages/4_极地核心技术.py').run().switch_page('pages/1_北极全景地图.py').run();healthy(app)
assert app.selectbox(key='atlas_choice').value==app.session_state['atlas_focus']=='sabetta'
app.button(key='atlas_reset').click().run();healthy(app)
assert 'atlas_focus' not in app.session_state and app.selectbox(key='atlas_choice').value=='sabetta'
app.selectbox(key='atlas_kind').select('空间设施').run()
app.text_input(key='atlas_search').set_value('no-match-acceptance').run()
app.text_input(key='atlas_search').set_value('').run();healthy(app)
assert app.selectbox(key='atlas_kind').value=='空间设施' and len(app.selectbox(key='atlas_choice').options)==3
app.switch_page('app.py').run();app.session_state['_atlas_pending_place']='inuvik'
app.switch_page('pages/1_北极全景地图.py').run();healthy(app)
assert app.selectbox(key='atlas_choice').value=='inuvik'
# A new regional study must keep its newly requested filter, not resurrect the old place.
app.switch_page('app.py').run();app.session_state['_study_active']=True;app.session_state['_study_region']='chukchi'
app.switch_page('pages/1_北极全景地图.py').run();healthy(app)
assert app.session_state['atlas-study-filter'] is True
assert app.selectbox(key='atlas_choice').value in ['utqiagvik','bering','nome','pevek']
print('PASS: restored submitted drafts, correction of invalid input, new empty record, consistent map/detail on return and new-region precedence')
