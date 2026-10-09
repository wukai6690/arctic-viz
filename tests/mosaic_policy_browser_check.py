"""Final polar viewport/legend bounds and adjacent mobile policy readings."""
import json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/case-journey'
OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('ARCTIC_TEST_URL','http://127.0.0.1:8502');report={};errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1540,'height':1060});page=context.new_page();page.set_default_timeout(45000)
    page.on('pageerror',lambda e:errors.append(str(e)));runs={'n':0}
    def socket_watch(socket):
        if '_stcore/stream' not in socket.url:return
        def receive(payload):
            if not isinstance(payload,bytes):return
            msg=ForwardMsg();msg.ParseFromString(payload)
            if msg.WhichOneof('type')=='script_finished' and msg.script_finished in (0,3):runs['n']+=1
        socket.on('framereceived',receive)
    page.on('websocket',socket_watch);page.goto(BASE,wait_until='domcontentloaded');app=page
    if 'streamlit.app' in BASE:
        page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000);app=page.frame_locator('iframe[title="streamlitApp"]')
    app.locator('.home-intro h1').wait_for(timeout=90000)
    def settle():
        page.wait_for_timeout(300);app.locator('.stApp[data-test-script-state="notRunning"]').wait_for()
        assert not app.locator('[data-testid="stException"]').count()
    def nav(label):
        before=runs['n'];app.locator('[data-testid="stSidebar"]').get_by_role('link',name=label,exact=True).click();deadline=time.monotonic()+60
        while runs['n']<=before and time.monotonic()<deadline:page.wait_for_timeout(100)
        assert runs['n']>before;settle()
    def chart_state():
        chart=app.locator('[role="tabpanel"]:visible .js-plotly-plot')
        expect(chart.locator('.point')).to_have_count(4)
        state=chart.evaluate('''e=>{const b=e.getBoundingClientRect();const inside=s=>[...e.querySelectorAll(s)].map(n=>{const r=n.getBoundingClientRect();return {text:n.textContent,inside:r.width>0&&r.height>0&&r.left>=b.left-1&&r.right<=b.right+1&&r.top>=b.top-1&&r.bottom<=b.bottom+1}});return {projection:e.layout.geo.projection.type,points:inside('.point'),legend:inside('.legendtext'),labels:[...e.querySelectorAll('.geolayer text')].map(e=>e.textContent)}}''')
        assert state['projection']=='orthographic'
        assert len(state['points'])==4 and all(r['inside'] for r in state['points'])
        assert len(state['legend'])==3 and all(r['inside'] for r in state['legend'])
        assert '北极点' in state['labels']
        return chart,state
    nav('案例研究');chart,state=chart_state();report['desktop_polar']=state
    chart.scroll_into_view_if_needed();settle();page.screenshot(path=str(OUT/'final-polar-desktop.png'),animations='disabled')
    page.set_viewport_size({'width':390,'height':844});settle();chart,state=chart_state();report['mobile_polar']=state
    assert app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    chart.scroll_into_view_if_needed();settle();page.screenshot(path=str(OUT/'final-polar-mobile.png'),animations='disabled')
    page.set_viewport_size({'width':1540,'height':1060});settle();nav('研究发现')
    app.get_by_role('tab',name='政策对照',exact=True).click();settle()
    page.set_viewport_size({'width':390,'height':844});settle()
    panel=app.locator('[role="tabpanel"]:visible');readings=panel.locator('.policy-reading');expect(readings).to_have_count(2)
    positions=readings.evaluate_all('(es)=>es.map(e=>{const r=e.getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,text:e.innerText}})')
    assert positions[1]['top']>=positions[0]['bottom']-1
    assert positions[1]['top']-positions[0]['bottom']<90
    assert panel.get_by_text('原文短引 · 文档定位',exact=True).first.bounding_box()['y']>=positions[1]['bottom']
    assert app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    readings.first.evaluate("e=>e.scrollIntoView({block:'start'})")
    app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop-=70');settle()
    page.screenshot(path=str(OUT/'final-policy-mobile.png'),animations='disabled')
    report['mobile_policy']={'adjacent_gap_px':positions[1]['top']-positions[0]['bottom'],'readings':[p['text'] for p in positions],'original_excerpts_follow_both_readings':True}
    browser.close()
report['url']=BASE;report['page_errors']=errors
(OUT/'final-visual-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
