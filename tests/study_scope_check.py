"""Scope persists independently of page widgets; partial years remain incomplete."""
import json,logging,sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.study_data import monthly_summary
for name in ['streamlit','streamlit.runtime.scriptrunner_utils.script_run_context']:logging.getLogger(name).setLevel(logging.ERROR)
checks=[]
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
app.switch_page('pages/8_区域联动研究.py').run()
app.selectbox(key='study-region').set_value('kara').run()
app.selectbox(key='study-month').set_value(3).run()
app.radio(key='study-metric').set_value('area').run()
assert not app.exception,[e.message for e in app.exception]
assert app.session_state['_study_region']=='kara' and app.session_state['_study_month']==3
assert app.selectbox(key='study-place').value=='sabetta'
assert app.selectbox(key='low-region').value=='kara'
app.switch_page('pages/4_极地核心技术.py').run()
app.switch_page('pages/8_区域联动研究.py').run()
assert app.selectbox(key='study-region').value=='kara' and app.selectbox(key='study-month').value==3
assert app.radio(key='study-metric').value=='area'
checks.append('Research region/month persist across widget destruction and project navigation')
app.slider(key='study-years').set_value((2024,2026)).run()
app.selectbox(key='study-month').set_value(12).run()
summary=app.dataframe[0].value
assert summary.iloc[0]['有效年份']==2 and summary.iloc[0]['缺失年份']==1
assert app.session_state['_study_years']==(2024,2026)
checks.append('Unpublished December 2026 is missing, not zero or a complete third year')
app.selectbox(key='study-region').set_value('chukchi').run()
assert app.selectbox(key='low-region').value=='chukchi'
assert app.selectbox(key='study-place').value in ['utqiagvik','bering','nome','pevek']
assert not app.exception,[e.message for e in app.exception]
app.button(key='reset-study').click().run()
assert app.session_state['_study_region']=='all' and not app.session_state['_study_active']
checks.append('Dependent place/low-year selections reset when necessary; global reset restores defaults')
(ROOT/'test-results/study').mkdir(parents=True,exist_ok=True)
(ROOT/'test-results/study/scope-report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
