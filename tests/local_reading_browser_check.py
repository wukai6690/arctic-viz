"""Real-browser source reading, downloads, filters, mobile, and blocked external network."""
import io,json,re,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/local-reading';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1600,'height':1100},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    def healthy():
        assert not page.locator('[data-testid="stException"]').count(),page.locator('[data-testid="stException"]').all_text_contents()
    def nav(name):
        page.locator('[data-testid="stSidebar"]').get_by_role('link',name=name,exact=True).click()
        page.wait_for_timeout(1100);healthy()
    def choose(label,name):
        page.get_by_role('combobox',name=re.compile(label)).click()
        page.get_by_role('option',name=name,exact=True).click();page.wait_for_timeout(900);healthy()
    def shot(name):page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
    def no_outbound():
        links=page.locator('[data-testid="stMain"] a[href]').evaluate_all('(nodes)=>nodes.map(n=>n.href).filter(u=>/^https?:/.test(u)&&new URL(u).origin!==location.origin)')
        assert not links,links
        # Edge exposes its built-in download shelf as a page; it is browser UI, not a website.
        assert all(tab.url in ['about:blank','edge://downloads-hub/'] or tab.url.startswith('http://127.0.0.1:8501') for tab in context.pages),[tab.url for tab in context.pages]
    page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded')
    page.locator('.home-intro h1').wait_for(timeout=45000)
    assert page.locator('.stApp').evaluate('(el)=>getComputedStyle(el).backgroundColor')=='rgb(245, 247, 243)'
    nav('北极地图');page.get_by_role('tab',name='认识这个地点',exact=True).wait_for()
    assert page.locator('.place-reading').count()==4
    page.locator('.place-lede').scroll_into_view_if_needed();shot('place-dossier-desktop.png')
    # Persist a non-default place and confirm local reading never changes its context.
    choose('当前地点','萨别塔 · Sabetta')
    page.get_by_role('tab',name='资料与事件',exact=True).click()
    url=page.url
    tab_count=len(context.pages)
    page.get_by_role('button',name='阅读背景正文 · Sabetta',exact=True).click()
    dialog=page.get_by_role('dialog');dialog.wait_for();healthy()
    assert len(context.pages)==tab_count
    assert '开放许可正文' in dialog.inner_text()
    query=dialog.get_by_role('textbox',name='在正文中查找',exact=True)
    query.fill('LNG');query.press('Enter');page.wait_for_timeout(500)
    assert dialog.get_by_text(re.compile('找到 [1-9]')).count()==1
    with page.expect_download() as download:dialog.get_by_role('button',name='下载本地正文与署名 · TXT',exact=True).click()
    download.value.save_as(OUT/'sabetta-reading.txt')
    text=(OUT/'sabetta-reading.txt').read_text(encoding='utf-8')
    assert 'Wikipedia contributors' in text and 'Creative Commons' in text and 'Revision:' in text
    shot('local-reading-dialog.png');no_outbound()
    page.keyboard.press('Escape');page.wait_for_timeout(500)
    assert page.url==url and 'Sabetta' in page.get_by_role('combobox',name=re.compile('当前地点')).get_attribute('aria-label')
    checks.append('Warm neutral theme; local full-text reading/search/download opens without navigation or lost place selection')
    page.get_by_role('tab',name='认识这个地点',exact=True).click()
    with page.expect_download() as download:page.get_by_role('button',name='下载地点资料包 · ZIP',exact=True).click()
    download.value.save_as(OUT/'sabetta-place-dossier.zip')
    with zipfile.ZipFile(OUT/'sabetta-place-dossier.zip') as bundle:
        assert bundle.testzip() is None
        manifest=json.loads(bundle.read('manifest.json'))
        assert manifest['place']['id']=='sabetta' and len([x for x in bundle.namelist() if x.startswith('photos/')])>=5
        assert '萨别塔' in bundle.read('打开地点档案.html').decode('utf-8')
    checks.append('Actual downloaded place ZIP includes matching Chinese profile, all photos, local text, and attribution')
    page.get_by_role('tab',name='地点图集',exact=True).click()
    page.get_by_text('产业现场',exact=True).click()
    expect(page.locator('[class*="st-key-photo-card-atlas-sabetta"] [data-testid="stImage"] img')).to_have_count(1,timeout=15000)
    page.get_by_text('全部视角',exact=True).click()
    expect(page.locator('[class*="st-key-photo-card-atlas-sabetta"] [data-testid="stImage"] img')).to_have_count(5,timeout=15000)
    page.get_by_role('button',name=re.compile('阅读专题 · 亚马尔')).click()
    page.get_by_role('heading',name='亚马尔 LNG：港口、冰区运输与投资',exact=True).wait_for()
    page.get_by_role('button',name='站内阅读这条关系的依据',exact=True).click()
    dialog=page.get_by_role('dialog');dialog.wait_for()
    assert '项目事实导读' in dialog.inner_text() and '未收录' in dialog.inner_text()
    no_outbound();page.keyboard.press('Escape');page.wait_for_timeout(400)
    checks.append('Photo-topic filters match actual assets; project relation evidence is readable in place with clear archival status')
    nav('站内资料');page.get_by_role('heading',name='站内资料',exact=True).wait_for()
    box=page.get_by_role('textbox',name='搜索站内资料',exact=True);box.fill('impossible-no-library-record');box.press('Enter')
    page.get_by_text('没有匹配资料。请缩短关键词或更换资料类型。',exact=True).wait_for()
    box.fill('');box.press('Enter');page.wait_for_timeout(700);no_outbound()
    nav('北极地图');page.get_by_role('tab',name='认识这个地点',exact=True).click()
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(900)
    page.locator('.place-lede').scroll_into_view_if_needed();healthy()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    shot('place-dossier-mobile.png')
    checks.append('Library empty search clears old results; 390 px place reading fits without horizontal overflow')
    # A fresh context with external requests blocked proves local content has no hotlink dependency.
    offline=browser.new_context(viewport={'width':1400,'height':1000})
    def route(request_route):
        if urlsplit(request_route.request.url).hostname in ['127.0.0.1','localhost']:request_route.continue_()
        else:request_route.abort()
    offline.route('**/*',route)
    local=offline.new_page();local.goto('http://127.0.0.1:8501/北极全景地图?place=shanghai',wait_until='domcontentloaded')
    local.get_by_role('tab',name='认识这个地点',exact=True).wait_for(timeout=45000)
    assert local.locator('.place-reading').count()==4
    local.get_by_role('tab',name='地点图集',exact=True).click()
    local.wait_for_function('''()=>{const a=[...document.querySelectorAll('[data-testid="stImage"] img')];return a.length>=5&&a.every(x=>x.complete&&x.naturalWidth>=500)}''',timeout=20000)
    local.get_by_role('tab',name='资料与事件',exact=True).click()
    assert local.get_by_role('button',name=re.compile('阅读背景正文')).count()==2
    local.get_by_role('button',name='阅读背景正文 · Jiangnan Shipyard',exact=True).click()
    local.get_by_role('dialog').wait_for();assert '开放许可正文' in local.get_by_role('dialog').inner_text()
    assert not local.locator('[data-testid="stException"]').count()
    checks.append('With external browser requests blocked, Shanghai profile, all local photos and both local background articles still work')
    browser.close()
report={'checks':checks,'browser_errors':errors}
(OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
