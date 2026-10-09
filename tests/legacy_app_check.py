"""Exercise original pages and key controls using Streamlit's own test runner."""
import json
import logging
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
OUT=ROOT/'test-results'/'original'
OUT.mkdir(parents=True,exist_ok=True)
for name in ['streamlit','streamlit.runtime.scriptrunner_utils.script_run_context']:
    logging.getLogger(name).setLevel(logging.ERROR)
report=[]
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=40)
pages=[ROOT/'app.py',*sorted((ROOT/'pages').glob('*.py'))]
for page in pages:
    try:
        if page.name=='app.py':app.run()
        else:app.switch_page('pages/'+page.name).run()
        errors=[e.message for e in app.exception]
        record={'page':page.name,'errors':errors,'tabs':[t.label for t in app.tabs]}
        if not errors and page.name.startswith('2_'):
            before=[m.value for m in app.metric]
            app.selectbox(key='observed_month').set_value(3).run()
            record['month_filter_changes_values']=before!=[m.value for m in app.metric]
            record['errors'] += [e.message for e in app.exception]
        if not errors and page.name.startswith('3_'):
            app.text_input(key='verified_events_query').set_value('zz-no-such-entity').run()
            record['empty_search_is_explicit']=any('没有匹配记录' in x.value for x in app.info)
            record['errors'] += [e.message for e in app.exception]
        report.append(record)
    except Exception as e:
        report.append({'page':page.name,'errors':[str(e)]})
    (OUT/'app-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert len(report)==11 and not any(r['errors'] for r in report)
assert all(r.get('month_filter_changes_values',True) and r.get('empty_search_is_explicit',True) for r in report)
