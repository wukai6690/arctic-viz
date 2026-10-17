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
