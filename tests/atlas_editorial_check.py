"""Verify exact thematic joins, navigation/filter state, and complete photo ordering."""
import json,logging,os,sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
from src.atlas_views import THEMES,themed_places
from src.evidence_views import place_catalog
from src.research_catalog import research_catalog,place_category
from src.photo_views import photo_records,filter_photos,diverse_photos
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.ERROR)
places=place_catalog()['places'];projects=research_catalog()['projects'];checks=[]
assert len(themed_places(places,projects,'全部地点'))==29
assert {p['id'] for p in themed_places(places,projects,'通信设施')}=={'esrange','inuvik'}
assert {p['id'] for p in themed_places(places,projects,'能源运输')}=={'sabetta'}
for theme,setting in THEMES.items():
    rows=themed_places(places,projects,theme)
    if setting['projects'] is not None:
        expected={place for p in projects if p['id'] in setting['projects'] for place in p['place_ids']}
        assert {p['id'] for p in rows}==expected
    elif setting.get('category'):assert all(place_category(p)==setting['category'] for p in rows)
checks.append('All 29 places retained; research themes resolve exact existing project/place joins; no fictitious ASBM ground station')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
app.switch_page('pages/1_北极全景地图.py').run()
def healthy():assert not app.exception,[e.message for e in app.exception]
healthy()
for theme in THEMES:
    app.selectbox(key='atlas-theme').set_value(theme).run();healthy()
    assert app.selectbox(key='atlas_choice').value in {p['id'] for p in themed_places(places,projects,theme)}
app.selectbox(key='atlas-theme').set_value('通信设施').run()
app.session_state['_atlas_pending_place']='sabetta';app.run();healthy()
assert app.selectbox(key='atlas-theme').value=='全部地点'
assert app.selectbox(key='atlas_choice').value=='sabetta'
app.selectbox(key='atlas_kind').set_value('空间设施').run();healthy()
assert len(app.selectbox(key='atlas_choice').options)==3
app.text_input(key='atlas_search').set_value('no-such-place-editorial-check').run();healthy()
assert any('没有符合条件的地点' in x.value for x in app.info)
app.text_input(key='atlas_search').set_value('').run();healthy()
app.selectbox(key='atlas_kind').set_value('全部类型').run();healthy()
app.selectbox(key='atlas_choice').set_value('sabetta').run();healthy()
assert app.session_state['atlas_focus']=='sabetta'
app.button(key='atlas_reset').click().run();healthy()
assert 'atlas_focus' not in app.session_state
checks.append('Every theme renders; external place navigation clears incompatible theme; type/search/focus/reset remain functional')
records=photo_records();ordered=diverse_photos(records)
assert len(records)==len(ordered)==167
assert {p['id'] for p in records}=={p['id'] for p in ordered}
assert {p['id']:p for p in records}=={p['id']:p for p in ordered}
assert ordered==diverse_photos(records)
assert len({p['topic'] for p in ordered[:12]})==7
assert len({p['owner_key'] for p in ordered[:12]})>=7
for topic in {p['topic'] for p in records}:
    filtered=filter_photos(records,topic=topic)
    assert all(p['topic']==topic for p in diverse_photos(filtered))
checks.append('All 167 image records and credits unchanged; first gallery page covers seven real subject labels and at least seven owners')
app.switch_page('pages/9_实景图集.py').run();healthy()
assert len(app.get('imgs'))==12
app.selectbox(key='gallery-page').set_value(2).run();healthy()
app.selectbox(key='gallery-topic').set_value('科研设施').run();healthy()
assert app.selectbox(key='gallery-page').value==1
app.selectbox(key='gallery-topic').set_value('全部视角').run()
app.selectbox(key='gallery-kind').set_value('项目影像').run()
app.selectbox(key='gallery-owner').set_value('project:mosaic').run();healthy()
assert len(app.get('imgs'))==5
app.text_input(key='gallery-query').set_value('no-such-photo-editorial-check').run();healthy()
assert not app.get('imgs') and any('没有符合条件的照片' in x.value for x in app.info)
checks.append('Gallery paging, subject filters, project image counts and empty search render correctly')
out=ROOT/'test-results/atlas-editorial';out.mkdir(parents=True,exist_ok=True)
(out/'data-report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
