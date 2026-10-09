"""Image delivery, actual dialogs, pagination, downloads, and mobile layout."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/photo-expansion';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1600,'height':1100},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    def healthy():
        assert not page.locator('[data-testid="stException"]').count()
    def choose(label,value):
        page.get_by_role('combobox',name=re.compile(label)).click()
        page.get_by_role('option',name=value,exact=True).click();page.wait_for_timeout(900);healthy()
    def nav(label):
        page.locator('[data-testid="stSidebar"]').get_by_role('link',name=label,exact=True).click()
        page.wait_for_timeout(1200);healthy()
    def photos_loaded():
        page.wait_for_function('''() => {
          const photos=[...document.querySelectorAll('[data-testid="stImage"] img')];
          return photos.length>0 && photos.every(i=>i.complete && i.naturalWidth>=500);
        }''',timeout=20000)
    def shot(name):
        page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
    page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded')
    page.get_by_role('heading',name=re.compile('在变化的北极')).wait_for(timeout=45000)
    nav('实景图集');page.get_by_role('heading',name='实景图集',exact=True).wait_for()
    photos_loaded();assert page.locator('[data-testid="stImage"] img').count()==12
    diagnostics=page.get_by_text(re.compile('^影像按地点和拍摄内容检索')).evaluate('(el)=>({color:getComputedStyle(el).color,opacity:getComputedStyle(el).opacity,parent:el.parentElement.outerHTML.slice(0,500)})')
    (OUT/'caption-style.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding='utf-8')
    shot('gallery-desktop.png');checks.append('Initial page delivers 12 complete local photographs')
    combo=page.get_by_role('combobox',name=re.compile('图集页码'));combo.click()
    page.get_by_role('option',name=re.compile('^第 2 ')).click();page.wait_for_timeout(900)
    photos_loaded();checks.append('Pagination displays the next photographs')
    choose('影像类别','项目影像');choose('地点或项目','MOSAiC：破冰船与跨国科研协作')
    # Match the source caption rather than relying on internal filenames.
    photos_loaded();assert page.locator('[data-testid="stImage"] img').count()==5
    page.locator('[data-testid="stImage"]').first.scroll_into_view_if_needed();shot('mosaic-gallery.png')
    page.get_by_role('button',name='放大查看',exact=True).first.click()
    dialog=page.get_by_role('dialog');dialog.wait_for();photos_loaded()
    dialog.get_by_text('照片出处与许可',exact=True).click()
    assert 'https://commons.wikimedia.org/' in dialog.inner_text()
    assert dialog.get_by_role('button',name='下载这张实景照片',exact=True).count()==1
    shot('photo-enlarged.png');page.keyboard.press('Escape');page.wait_for_timeout(500)
    checks.append('Full image dialog retains local downloads and copyable source/license records')
    with page.expect_download() as downloaded:page.get_by_role('button',name='下载当前照片的来源与许可',exact=True).click()
    downloaded.value.save_as(OUT/'downloaded-photo-sources.json')
    downloaded_rows=json.loads((OUT/'downloaded-photo-sources.json').read_text(encoding='utf-8'))
    assert len(downloaded_rows)==5 and all(p['owner_id']=='mosaic' for p in downloaded_rows)
    checks.append('Downloaded attribution manifest matches the filtered image set')
    box=page.get_by_role('textbox',name='搜索图集',exact=True);box.fill('no-such-photo-994');box.press('Enter')
    page.get_by_text('没有符合条件的照片，请更换关键词或筛选范围。',exact=True).wait_for()
    assert not page.locator('[data-testid="stImage"]').count()
    box.fill('');box.press('Enter');page.wait_for_timeout(800)
    page.get_by_role('button',name='阅读项目',exact=True).first.click()
    page.get_by_role('heading',name='MOSAiC：破冰船与跨国科研协作',exact=True).wait_for();healthy()
    checks.append('Empty search clears old images; photograph opens the corresponding project')
    page.get_by_role('tab',name='项目时间线与地点',exact=True).click();photos_loaded()
    assert page.locator('[data-testid="stImage"] img').count()==6
    page.get_by_text('更多实景',exact=True).scroll_into_view_if_needed();shot('project-fieldwork.png')
    nav('实景图集');choose('影像类别','地点实景');choose('地点或项目','格陵兰')
    page.get_by_role('button',name='在地图中查看',exact=True).first.click();page.wait_for_timeout(1200)
    assert 'Greenland' in page.get_by_role('combobox',name=re.compile('当前地点')).get_attribute('aria-label')
    page.get_by_role('tab',name='地点图集',exact=True).click();photos_loaded()
    expect(page.locator('[class*="st-key-photo-card-atlas-greenland"] [data-testid="stImage"] img')).to_have_count(5,timeout=15000)
    checks.append('Atlas shows all five selected-place photos, including photos beyond the original three')
    nav('区域联动');page.locator('.region-summary').first.wait_for();assert page.locator('.region-summary').count()==3
    shot('regional-summary-desktop.png')
    nav('实景图集');page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(900)
    photos_loaded();healthy()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    shot('gallery-mobile.png')
    page.locator('[data-testid="stImage"]').first.scroll_into_view_if_needed();shot('gallery-mobile-photo.png')
    checks.append('Photographs and controls fit a 390 px mobile viewport')
    browser.close()
report={'checks':checks,'browser_errors':errors}
(OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
