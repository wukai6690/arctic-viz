"""Acceptance of readable captions and correct state after real page navigation."""
import json,os,re,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/acceptance';OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('ARCTIC_TEST_URL','http://127.0.0.1:8502');report={'url':BASE};errors=[]

def luminance(rgb):
    c=[v/255 for v in rgb]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(a*b for a,b in zip(c,[.2126,.7152,.0722]))

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':960},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(45000);runs={'n':0}
    page.on('pageerror',lambda e:errors.append(str(e)))
    def socket_watch(socket):
        if '_stcore/stream' not in socket.url:return
        def received(payload):
            if not isinstance(payload,bytes):return
            msg=ForwardMsg();msg.ParseFromString(payload)
            if msg.WhichOneof('type')=='script_finished' and msg.script_finished in (0,3):runs['n']+=1
        socket.on('framereceived',received)
    page.on('websocket',socket_watch);page.goto(BASE,wait_until='domcontentloaded');app=page
    if 'streamlit.app' in BASE:
        page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000);app=page.frame_locator('iframe[title="streamlitApp"]')
    app.locator('.home-intro h1').wait_for(timeout=90000)
    def settle():
        page.wait_for_timeout(300);app.locator('.stApp[data-test-script-state="notRunning"]').wait_for()
        assert not app.locator('[data-testid="stException"]').count()
    def action(call):
        n=runs['n'];call();end=time.monotonic()+60
        while runs['n']<=n and time.monotonic()<end:page.wait_for_timeout(100)
        assert runs['n']>n;settle()
    def nav(label):action(lambda:app.locator('[data-testid="stSidebar"]').get_by_role('link',name=label,exact=True).click())
    def shot(name):page.screenshot(path=str(OUT/(('public-' if 'streamlit.app' in BASE else '')+name)),animations='disabled')
    settle()
    caption=app.locator('[data-testid="stMain"] [data-testid="stCaptionContainer"]').filter(has_text='阶段成果').first
    style=caption.evaluate('''e=>{const c=getComputedStyle(e),bg=getComputedStyle(document.querySelector('[data-testid="stMain"]'));return {color:c.color,opacity:parseFloat(c.opacity),background:bg.backgroundColor}}''')
    fg=list(map(float,re.findall(r'[\d.]+',style['color'])[:3]));bg=list(map(float,re.findall(r'[\d.]+',style['background'])[:3]))
    actual=[v*style['opacity']+b*(1-style['opacity']) for v,b in zip(fg,bg)]
    contrast=(luminance(bg)+.05)/(luminance(actual)+.05)
    assert contrast>=4.5 and style['opacity']==1,(contrast,style)
    report['caption_contrast']=round(contrast,2);shot('home-desktop-after.png')
    for width in [1024,768,390,320]:
        page.set_viewport_size({'width':width,'height':844});settle()
        assert app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
        if width in [390,320]:
            lines=app.locator('.home-intro h1').evaluate('''e=>{const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),lines={};let n;while(n=walker.nextNode()){for(let i=0;i<n.length;i++){if(!n.textContent[i].trim())continue;const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+1);const y=Math.round(r.getBoundingClientRect().top);lines[y]=(lines[y]||'')+n.textContent[i]}}return Object.values(lines)}''')
            assert all(len(line)>=6 for line in lines),lines
            report.setdefault('mobile_headline_lines',{})[width]=lines
            shot(f'home-{width}-after.png')
    report['tested_widths']=[1440,1024,768,390,320]
    page.set_viewport_size({'width':1440,'height':960});settle();nav('北极地图')
    combo=app.get_by_role('combobox',name=re.compile('当前地点'));combo.click();combo.fill('Sabetta')
    action(lambda:app.get_by_role('option',name='萨别塔 · Sabetta',exact=True).click())
    nav('技术与地缘');nav('北极地图')
    expect(app.get_by_role('combobox',name=re.compile('当前地点'))).to_have_attribute('aria-label',re.compile('Sabetta'))
    frame=app.frame_locator('iframe').first;expect(frame.locator('.atlas-dot')).to_have_count(29)
    center=frame.locator('body').evaluate("()=>{const k=Object.keys(window).find(k=>k.startsWith('map_')&&window[k]&&typeof window[k].getCenter==='function');const c=window[k].getCenter();return {lat:c.lat,lng:c.lng}}")
    place=next(p for p in json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'))['places'] if p['id']=='sabetta')
    assert abs(center['lat']-place['latitude'])<.02 and abs(center['lng']-place['longitude'])<.02,center
    report['returned_map_place']={'id':'sabetta','center':center};shot('map-return.png')
    nav('研究过程');app.get_by_role('tab',name='调研记录入口',exact=True).click();settle()
    app.get_by_role('textbox',name='记录编号',exact=True).fill('acceptance-plan-only')
    app.get_by_role('textbox',name='这次活动要回答什么问题',exact=True).fill('仅检验页面往返，不代表已开展的调研。')
    action(lambda:app.get_by_role('button',name='整理为可下载记录',exact=True).click())
    nav('案例研究');nav('研究过程');app.get_by_role('tab',name='调研记录入口',exact=True).click();settle()
    expect(app.get_by_role('textbox',name='记录编号',exact=True)).to_have_value('acceptance-plan-only')
    expect(app.get_by_role('textbox',name='这次活动要回答什么问题',exact=True)).to_have_value('仅检验页面往返，不代表已开展的调研。')
    app.get_by_role('textbox',name='记录摘要',exact=True).fill('返回页面后修改的计划；无真实受访者和调查结果。')
    action(lambda:app.get_by_role('button',name='整理为可下载记录',exact=True).click())
    with page.expect_download() as d:app.get_by_role('button',name='下载这份研究记录 · JSON',exact=True).click()
    target=OUT/d.value.suggested_filename;d.value.save_as(target);row=json.loads(target.read_text(encoding='utf-8'))
    assert row['id']=='acceptance-plan-only' and row['status']=='计划' and '返回页面后修改' in row['summary']
    assert app.get_by_role('button',name='追加保存到本地私有记录',exact=True).count()==0
    page.set_viewport_size({'width':390,'height':844});settle();shot('record-mobile-after.png')
    assert app.locator('[data-testid="stForm"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    action(lambda:app.get_by_role('button',name='开始新记录',exact=True).click())
    expect(app.get_by_role('textbox',name='记录编号',exact=True)).to_have_value('')
    assert app.get_by_role('button',name='下载这份研究记录 · JSON',exact=True).count()==0
    report['draft_return_edit_download_and_new_record']='passed without persistent writes'
    report['page_errors']=errors;assert not errors;browser.close()
(OUT/('public-report.json' if 'streamlit.app' in BASE else 'local-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
