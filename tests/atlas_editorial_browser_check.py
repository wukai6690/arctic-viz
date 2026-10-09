"""Check compact atlas, exact theme markers, photo provenance and mobile layouts."""
import json,os,re,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/atlas-editorial';OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('ARCTIC_TEST_URL','http://127.0.0.1:8502');checks=[];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1540,'height':1060},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(40000);page.on('pageerror',lambda e:errors.append(str(e)))
    runs={'finished':0}
    def watch_socket(socket):
        if '_stcore/stream' not in socket.url:return
        def received(payload):
            if not isinstance(payload,bytes):return
            message=ForwardMsg();message.ParseFromString(payload)
            if message.WhichOneof('type')=='script_finished' and message.script_finished in (0,3):runs['finished']+=1
        socket.on('framereceived',received)
    page.on('websocket',watch_socket)
    page.goto(BASE,wait_until='domcontentloaded');app=page
    if 'streamlit.app' in BASE:
        page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000)
        app=page.frame_locator('iframe[title="streamlitApp"]')
    sidebar=app.locator('[data-testid="stSidebar"]')
    sidebar.get_by_role('link',name='北极地图',exact=True).wait_for(timeout=90000)
    def settle():
        page.wait_for_timeout(250);app.locator('.stApp[data-test-script-state="notRunning"]').wait_for()
        assert not app.locator('[data-testid="stException"]').count(),app.locator('[data-testid="stException"]').all_text_contents()
    def run_action(action):
        before=runs['finished'];action();deadline=time.monotonic()+60
        while runs['finished']<=before and time.monotonic()<deadline:page.wait_for_timeout(100)
        assert runs['finished']>before,'No successful Streamlit run completed after action'
        settle()
    def click(locator):run_action(lambda:locator.click())
    def nav(label):click(sidebar.get_by_role('link',name=label,exact=True))
    def choose(label,value):
        c=app.get_by_role('combobox',name=re.compile(label));c.click();c.fill(value)
        click(app.get_by_role('option',name=value,exact=True))
    def map_frame():return app.frame_locator('iframe').first
    def marker_count(count):expect(map_frame().locator('.atlas-dot')).to_have_count(count,timeout=25000)
    def shot(name):page.screenshot(path=str(OUT/name),animations='disabled')
    def loaded():
        images=app.locator('[data-testid="stImage"] img')
        for _ in range(60):
            if images.count() and images.evaluate_all('(es)=>es.every(e=>e.complete && e.naturalWidth>0)'):return
            page.wait_for_timeout(300)
        raise AssertionError('Photographs did not finish loading')
    def mobile_fit():
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    nav('北极地图');marker_count(29)
    assert app.locator('iframe').first.bounding_box()['y']<400
    shot('atlas-desktop.png')
    choose('研究主题','通信设施');marker_count(2)
    assert map_frame().locator('[title="埃斯兰航天中心"]').count()==1
    assert map_frame().locator('[title="伊努维克"]').count()==1
    assert '尚未建立经过核对的地面站关联' in app.locator('[data-testid="stMain"]').inner_text()
    choose('研究主题','能源运输');marker_count(1)
    expect(app.get_by_role('combobox',name=re.compile('当前地点'))).to_have_attribute('aria-label',re.compile('Sabetta'))
    choose('研究主题','全部地点');marker_count(29)
    app.get_by_role('button',name='筛选与图层',exact=True).click()
    choose('地点类型','空间设施');marker_count(3)
    choose('地点类型','全部类型');page.keyboard.press('Escape');settle();marker_count(29)
    box=app.get_by_role('textbox',name='查找地点',exact=True)
    box.fill('no-such-place-visual-test');run_action(lambda:box.press('Enter'))
    expect(app.get_by_text('没有符合条件的地点，请调整地区、类型或搜索词。',exact=True)).to_be_visible()
    box.fill('');run_action(lambda:box.press('Enter'));marker_count(29)
    click(map_frame().locator('[title="萨别塔"]'))
    expect(app.get_by_role('combobox',name=re.compile('当前地点'))).to_have_attribute('aria-label',re.compile('Sabetta'))
    assert app.get_by_role('button',name=re.compile('阅读专题 · 亚马尔')).count()==1
    click(app.get_by_role('button',name='恢复北极全景',exact=True));marker_count(29)
    checks.append('Desktop map starts within first 400 px; all 29 markers, exact theme joins, layer filters, empty search and marker/detail linkage work')
    app.get_by_role('tab',name='时点影像',exact=True).click();settle()
    panel=app.locator('[role="tabpanel"]:visible');expect(panel.locator('[data-testid="stImage"] img')).to_have_count(2)
    checks.append('Existing history-image tab survives map reorganization')
    nav('实景图集');loaded();expect(app.locator('[data-testid="stImage"] img')).to_have_count(12)
    filter_y=[app.get_by_role('combobox',name=re.compile(label)).evaluate('e=>e.closest("[data-testid=stSelectbox]").getBoundingClientRect().y') for label in ['影像类别','地点或项目','拍摄内容']]
    filter_y.append(app.get_by_role('textbox',name='搜索图集',exact=True).evaluate('e=>e.closest("[data-testid=stTextInput]").getBoundingClientRect().y'))
    shot('gallery-desktop.png')
    assert max(filter_y)-min(filter_y)<4,f'Desktop gallery filter containers should share one row: {filter_y}'
    labels=app.locator('.gallery-topic-label').all_text_contents();assert len(set(labels))==7
    assert app.locator('[class*="st-key-photo-card-"] [data-testid="stImage"] img').evaluate_all('(es)=>es.every(e=>getComputedStyle(e).objectFit==="contain")')
    shot('gallery-desktop.png')
    choose('影像类别','项目影像');choose('地点或项目','MOSAiC：破冰船与跨国科研协作');loaded()
    expect(app.locator('[data-testid="stImage"] img')).to_have_count(5)
    with page.expect_download() as result:app.get_by_role('button',name='下载当前照片的来源与许可',exact=True).click()
    target=OUT/'photo-sources.json';result.value.save_as(target)
    rows=json.loads(target.read_text(encoding='utf-8'));assert len(rows)==5 and all(r['owner_id']=='mosaic' and r['license'] and r['author'] for r in rows)
    click(app.get_by_role('button',name='放大查看',exact=True).first)
    dialog=app.get_by_role('dialog');expect(dialog).to_be_visible()
    with page.expect_download() as result:dialog.get_by_role('button',name='下载这张实景照片',exact=True).click()
    target=OUT/result.value.suggested_filename;result.value.save_as(target);assert target.stat().st_size>1000
    page.keyboard.press('Escape');settle()
    checks.append('Gallery shows seven subject types on page one, preserves complete images, and downloads exact selected source records and original photo')
    nav('北极地图');page.set_viewport_size({'width':390,'height':844});settle()
    close=app.locator('[data-testid="stSidebarCollapseButton"] button')
    box=close.bounding_box() if close.count() else None
    if box and 0<=box['x']<390:close.click();settle()
    app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop=0');settle();mobile_fit()
    shot('atlas-mobile.png')
    choose('研究主题','通信设施');marker_count(2);mobile_fit()
    app.get_by_role('button',name='筛选与图层',exact=True).click();settle()
    expect(app.get_by_role('combobox',name=re.compile('地点类型'))).to_be_visible()
    mobile_fit();shot('atlas-mobile-layers.png');page.keyboard.press('Escape')
    page.set_viewport_size({'width':1540,'height':1060});settle()
    if not sidebar.get_by_role('link',name='实景图集',exact=True).is_visible():
        app.locator('[data-testid="stExpandSidebarButton"]').click();settle()
    nav('实景图集');choose('影像类别','全部影像');choose('地点或项目','所有地点与项目')
    page.set_viewport_size({'width':390,'height':844});settle();loaded();mobile_fit()
    app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop=0');shot('gallery-mobile.png')
    app.locator('[class*="st-key-photo-card-"]').first.scroll_into_view_if_needed();shot('gallery-mobile-photo.png')
    checks.append('Map theme/layer controls and complete gallery images remain usable without page overflow at 390 px')
    browser.close()
(OUT/'browser-report.json').write_text(json.dumps({'url':BASE,'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2));assert not errors
