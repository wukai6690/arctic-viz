"""End-to-end acceptance checks for the atlas and evidence dossiers."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/research'
OUT.mkdir(parents=True,exist_ok=True)
errors=[];checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    context=browser.new_context(viewport={'width':1600,'height':1100},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    def healthy():
        assert not page.locator('[data-testid="stException"]').count(),page.locator('[data-testid="stException"]').all_text_contents()
    def nav(name):
        if name in ['海冰观测','事件线索','关于研究'] and not page.locator('[data-testid="stSidebar"]').get_by_role('link',name=name,exact=True).is_visible():
            page.locator('[data-testid="stSidebar"]').get_by_text('观测与研究资料',exact=True).click()
        page.locator('[data-testid="stSidebar"]').get_by_role('link',name=name,exact=True).click();page.wait_for_timeout(1100);healthy()
    def choose(label,option):
        page.get_by_role('combobox',name=re.compile(label)).click()
        page.get_by_role('option',name=option,exact=True).click();page.wait_for_timeout(900);healthy()
    def shot(name):
        page.wait_for_timeout(700)
        try:page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
        except Exception:
            page.wait_for_timeout(1200);page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
    page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded')
    page.get_by_role('heading',name=re.compile('在变化的北极')).wait_for(timeout=45000);healthy();shot('home.png')
    nav('北极地图')
    frame=page.frame_locator('iframe').first
    frame.locator('[title="新奥尔松"]').wait_for(timeout=20000)
    assert frame.locator('.atlas-dot').count()==29
    assert page.locator('[data-testid="stImage"] img').count()>=4
    page.wait_for_timeout(800);shot('atlas.png')
    # The taller scope controls put the iframe partly below the viewport. Settle
    # scrolling before the click so Playwright does not use a stale iframe offset.
    page.locator('iframe').first.scroll_into_view_if_needed();page.wait_for_timeout(800)
    frame.locator('[title="萨别塔"]').click()
    page.get_by_role('button',name=re.compile('阅读专题 · 亚马尔')).wait_for(timeout=15000)
    assert 'Sabetta' in page.get_by_role('combobox',name=re.compile('当前地点')).get_attribute('aria-label')
    checks.append('29 named markers; marker click selects Sabetta and its sourced project')
    page.get_by_role('button',name=re.compile('阅读专题 · 亚马尔')).click()
    page.get_by_role('heading',name='亚马尔 LNG：港口、冰区运输与投资',exact=True).wait_for(timeout=15000)
    healthy()
    choose('选择项目专题','Kinuvik：跨大西洋的卫星接收协作')
    page.get_by_role('tab',name='项目时间线与地点',exact=True).click();page.wait_for_timeout(500)
    page.get_by_role('button',name='在地图中查看 · 埃斯兰航天中心',exact=True).click()
    page.get_by_role('combobox',name=re.compile('当前地点')).wait_for(timeout=15000);page.wait_for_timeout(900)
    assert 'Esrange' in page.get_by_role('combobox',name=re.compile('当前地点')).get_attribute('aria-label')
    healthy();shot('atlas-esrange.png')
    checks.append('Map → project → another project → Esrange map navigation preserves selection')
    choose('地点类型','空间设施')
    page.frame_locator('iframe').first.locator('.leaflet-control-zoom-in').wait_for(timeout=15000)
    assert page.frame_locator('iframe').first.locator('.atlas-dot').count()==3
    page.get_by_role('textbox',name='查找地点',exact=True).fill('no-such-arctic-place')
    page.get_by_role('textbox',name='查找地点',exact=True).press('Enter')
    page.get_by_text('没有符合条件的地点，请调整地区、类型或搜索词。',exact=True).wait_for()
    page.get_by_role('textbox',name='查找地点',exact=True).fill('')
    page.get_by_role('textbox',name='查找地点',exact=True).press('Enter');page.wait_for_timeout(700)
    checks.append('Type filter and empty search are accurate')
    nav('技术与地缘')
    choose('研究领域','冰区船舶');choose('选择项目专题','雪龙2号：跨国设计与国内建造')
    graph=page.locator('[role="tabpanel"]:visible .scatterlayer .trace').first
    graph.wait_for(timeout=15000);page.wait_for_timeout(500);shot('project.png')
    relationship_point=page.locator('[role="tabpanel"]:visible .scatterlayer .trace').nth(4).locator('.point').nth(1)
    relationship_point.scroll_into_view_if_needed()
    point_box=relationship_point.bounding_box()
    assert point_box
    page.mouse.click(point_box['x']+point_box['width']/2,point_box['y']+point_box['height']/2)
    page.wait_for_timeout(900);healthy()
    assert '第七〇八研究所' in page.get_by_role('combobox',name=re.compile('查看关系依据')).get_attribute('aria-label')
    page.locator('[role="tabpanel"]:visible [data-testid="stPlotlyChart"]').scroll_into_view_if_needed()
    shot('project-relations.png')
    choose('查看关系依据','江南造船（中国） → 雪龙2号 · 建造')
    page.get_by_role('button',name='站内阅读这条关系的依据',exact=True).click()
    dialog=page.get_by_role('dialog');dialog.wait_for()
    dialog.get_by_text('出处、许可与保存信息',exact=True).click()
    assert 'https://dnr.gxzf.gov.cn/' in dialog.inner_text()
    page.keyboard.press('Escape');page.wait_for_timeout(500)
    checks.append('Graph click and relationship selector expose the matching primary document')
    page.get_by_role('tab',name='研究解释',exact=True).click()
    assert page.get_by_text(re.compile('交付与设计分工不能单独证明')).count()>0
    nav('研究发现');shot('findings.png')
    nav('数据与方法')
    page.get_by_role('tab',name='资料下载',exact=True).click()
    with page.expect_download() as downloaded:page.get_by_role('button',name='项目事实、关系与来源 · JSON',exact=True).click()
    downloaded.value.save_as(OUT/'downloaded-projects.json')
    assert len(json.loads((OUT/'downloaded-projects.json').read_text(encoding='utf-8'))['projects'])==7
    page.get_by_role('tab',name='研究工具',exact=True).click()
    page.locator('input[type="file"]').set_input_files({'name':'check.csv','mimeType':'text/csv','buffer':b'year,value\n2020,4\n2021,6\n2022,5\n'})
    page.get_by_role('combobox',name=re.compile('图表类型')).wait_for(timeout=15000);healthy()
    checks.append('Evidence download and CSV upload chart work')
    sidebar=page.locator('[data-testid="stSidebar"]')
    sidebar.get_by_text('观测与研究资料',exact=True).click()
    nav('海冰观测');choose('观测月份','3 月')
    assert '2026-03' in page.locator('[data-testid="stMetric"]').first.inner_text()
    page.get_by_role('tab',name='季节对比',exact=True).click();page.wait_for_timeout(700);shot('climate.png')
    nav('事件线索');healthy()
    nav('关于研究');healthy()
    checks.append('Climate controls, news candidates and research description remain available')
    nav('北极地图')
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(1200)
    healthy();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    shot('mobile-map.png');checks.append('Map page fits a 390 px mobile viewport')
    browser.close()
(OUT/'browser-report.json').write_text(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2))
assert not errors
