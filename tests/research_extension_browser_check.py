"""Exercise visible research additions, in-place readers, exact downloads and mobile layouts."""
import io,json,os,re,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/research-extension';OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('ARCTIC_TEST_URL','http://127.0.0.1:8502')
errors=[];checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1540,'height':1060},device_scale_factor=1,accept_downloads=True)
    page=context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='domcontentloaded')
    app=page
    if 'streamlit.app' in BASE:
        page.locator('iframe[title="streamlitApp"]').wait_for(timeout=90000)
        app=page.frame_locator('iframe[title="streamlitApp"]')
    app.locator('.home-intro h1').wait_for(timeout=90000)
    def settle():
        page.wait_for_timeout(700);app.locator('.stApp[data-test-script-state="notRunning"]').wait_for()
        assert not app.locator('[data-testid="stException"]').count(),app.locator('[data-testid="stException"]').all_text_contents()
    def nav(label):
        app.locator('[data-testid="stSidebar"]').get_by_role('link',name=label,exact=True).click();settle()
    def tab(label):app.get_by_role('tab',name=label,exact=True).click();settle()
    def press_label(label):app.locator('[role="tabpanel"]:visible').get_by_text(label,exact=True).click();settle()
    def choose(label,value):
        c=app.get_by_role('combobox',name=re.compile(label));c.click();c.fill(value)
        app.get_by_role('option',name=value,exact=True).click();settle()
    def shot(name,target=None):
        if target:
            target.evaluate("e=>e.scrollIntoView({block:'start'})")
            app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop-=90')
        settle();page.screenshot(path=str(OUT/(('live-' if 'streamlit.app' in BASE else '')+name+'.png')),animations='disabled')
    def download(button):
        with page.expect_download() as result:app.get_by_role('button',name=button,exact=True).click()
        d=result.value;target=OUT/d.suggested_filename;d.save_as(target)
        return target
    nav('研究发现');shot('mechanisms',app.get_by_role('tab',name='机制与证据',exact=True))
    choose('作用方向','地缘与制度 → 技术')
    assert '用户需求进入技术项目' in app.get_by_role('combobox',name=re.compile('研究问题')).get_attribute('aria-label')
    tab('政策对照')
    press_label('技术与设施')
    shot('policies',app.get_by_role('tab',name='政策对照',exact=True))
    button=app.locator('[role="tabpanel"]:visible').get_by_role('button',name='站内阅读政策导读',exact=True).first
    before=page.url;button.click();settle()
    dialog=app.get_by_role('dialog');dialog.wait_for();assert '2021' in dialog.inner_text()
    assert page.url==before and len(context.pages)==1
    path=download('下载中文导读与出处 · TXT');assert '2021-01-26' in path.read_text(encoding='utf-8')
    shot('policy-reader');page.keyboard.press('Escape');settle()
    policyzip=download('下载当前分析与出处 · ZIP')
    with zipfile.ZipFile(policyzip) as z:
        selection=json.loads(z.read('manifest.json'))['selection'];assert selection=={'left':'no2021','right':'no2025','theme':'技术与设施'}
        assert len(json.loads(z.read('records.json')))==2
        assert {s['id'] for s in json.loads(z.read('sources.json'))}=={'norway-2021','norway-2025','norway-2025-infra'}
    checks.append('Policy comparison, in-place source reading and actual TXT/ZIP downloads match selected documents and topic')
    tab('中国参与条件');choose('选择参与任务','获取通信与观测数据')
    press_label('假设某项通信服务暂不可用')
    press_label('评估其他通信路径')
    shot('participation',app.get_by_role('combobox',name=re.compile('选择参与任务')))
    scenariozip=download('下载当前条件比较 · ZIP')
    with zipfile.ZipFile(scenariozip) as z:
        selection=json.loads(z.read('manifest.json'))['selection'];assert selection['hypothesis_active'] is True and selection['selected_option']=='评估其他通信路径'
    tab('多方视角');choose('参与者类型','原住民组织');shot('perspectives',app.get_by_role('tab',name='多方视角',exact=True))
    assert 'Inuit Circumpolar Council' in app.locator('[role="tabpanel"]:visible').inner_text()
    checks.append('Task conditions and hypothetical alternatives remain distinct; community-related statements preserve attribution')
    nav('技术与地缘');choose('选择项目专题','ASBM：面向高纬地区的通信卫星')
    tab('技术与活动');shot('capability',app.get_by_role('tab',name='技术与活动',exact=True))
    assert '2024' in app.locator('[role="tabpanel"]:visible').inner_text()
    tab('双向作用');settle()
    nav('区域联动');tab('实际活动');press_label('航行距离')
    shot('activities',app.get_by_role('tab',name='实际活动',exact=True))
    shipping=download('下载航运端点与口径 · ZIP')
    with zipfile.ZipFile(shipping) as z:
        assert json.loads(z.read('manifest.json'))['selection']['metric']=='distance_million_nm'
        assert [r['year'] for r in json.loads(z.read('records.json'))]==[2013,2025]
    checks.append('Technology and actual-activity tabs work; shipping export keeps geographic scope, years and selected metric')
    nav('北极地图');choose('当前地点','萨别塔 · Sabetta');tab('时点影像')
    panel=app.locator('[role="tabpanel"]:visible');images=panel.locator('[data-testid="stImage"] img')
    assert images.count()==2
    for img in images.all():assert img.evaluate('e=>e.complete && e.naturalWidth>0')
    shot('history',app.get_by_role('tab',name='时点影像',exact=True))
    record=download('下载影像比较记录 · JSON');assert json.loads(record.read_text(encoding='utf-8'))['place_id']=='sabetta'
    nav('数据与方法');tab('资料下载');bundle=download('政策、机制、参与条件与文献记录 · ZIP')
    with zipfile.ZipFile(bundle) as z:assert z.testzip() is None and len(json.loads(z.read('records.json')))>=9
    nav('研究发现');tab('政策对照');page.set_viewport_size({'width':390,'height':844});settle()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    shot('mobile-policy',app.get_by_role('tab',name='政策对照',exact=True))
    tab('中国参与条件');settle();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    cards=app.locator('.condition-reading');assert cards.count()==3
    assert cards.evaluate_all('(es)=>es.every(e=>e.scrollWidth<=e.clientWidth+1)')
    shot('mobile-participation',app.get_by_role('tab',name='中国参与条件',exact=True))
    checks.append('History photos load and download; complete research package works; new research pages fit a 390 px viewport')
    browser.close()
(OUT/('live-report.json' if 'streamlit.app' in BASE else 'browser-report.json')).write_text(json.dumps({'url':BASE,'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2));assert not errors
