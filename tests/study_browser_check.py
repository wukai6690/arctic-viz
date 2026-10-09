"""Regional choices, atlas/project joins, downloads and preparation tools in Edge."""
import io,json,re,sys,zipfile
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.study_data import monthly_summary
OUT=ROOT/'test-results/study';OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[]
review_file=ROOT/'data/analysis/event_reviews.jsonl';initial_reviews=review_file.read_bytes() if review_file.exists() else None
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
    context=browser.new_context(viewport={'width':1540,'height':1050},accept_downloads=True)
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    def healthy():
        assert not page.locator('[data-testid="stException"]').count(),page.locator('[data-testid="stException"]').all_text_contents()
    def nav(label):
        link=page.locator('[data-testid="stSidebar"]').get_by_role('link',name=label,exact=True)
        if not link.is_visible():page.locator('[data-testid="stSidebar"]').get_by_text('观测与研究资料',exact=True).click()
        link.click();page.wait_for_timeout(1300);healthy()
    def choose(label,value):
        page.get_by_role('combobox',name=re.compile(label)).click()
        page.get_by_role('option',name=value,exact=True).click();page.wait_for_timeout(1000);healthy()
    def shot(name):
        page.wait_for_timeout(500);page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
    page.goto('http://127.0.0.1:8501',wait_until='domcontentloaded')
    page.get_by_role('heading',name=re.compile('在变化的北极')).wait_for(timeout=45000)
    nav('区域联动');page.get_by_role('combobox',name=re.compile('研究海区')).wait_for(timeout=20000)
    page.frame_locator('iframe').first.locator('.leaflet-container').wait_for(timeout=20000)
    shot('regional-overview.png')
    choose('研究海区','喀拉海');choose('比较月份','3 月')
    chart=page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first
    chart.wait_for();extent=chart.evaluate('(el)=>el.data[0].y')
    page.get_by_text('海冰面积（Area）',exact=True).click()
    page.wait_for_function("()=>document.querySelector('[data-testid=stPlotlyChart] .js-plotly-plot')?.layout?.yaxis?.title?.text?.includes('海冰面积')",timeout=20000);healthy()
    area=page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first.evaluate('(el)=>el.data[0].y')
    assert extent!=area
    page.get_by_text('海冰范围（Extent）',exact=True).click()
    page.wait_for_function("()=>document.querySelector('[data-testid=stPlotlyChart] .js-plotly-plot')?.layout?.yaxis?.title?.text?.includes('海冰范围')",timeout=20000)
    page.get_by_text('相对同月基准的变化',exact=True).click()
    page.wait_for_function("()=>document.querySelector('[data-testid=stPlotlyChart] .js-plotly-plot')?.layout?.yaxis?.title?.text?.includes('距平')",timeout=20000)
    anomaly=page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first.evaluate('(el)=>el.data[0].y')
    assert anomaly!=extent
    page.get_by_text('实际观测',exact=True).click();page.wait_for_timeout(700)
    checks.append('Region/month controls and extent/area switch change the actual plotted data')
    page.get_by_role('tab',name='低冰年份对照',exact=True).click();page.wait_for_timeout(400)
    expected='、'.join(map(str,monthly_summary('kara',3,2016,2025)['low_years']))
    assert expected in page.locator('[data-testid="stMetric"]').first.inner_text()
    shot('low-ice-year.png');checks.append('Low year is computed from the selected region, month and window')
    page.get_by_role('tab',name='资料覆盖与导出',exact=True).click()
    with page.expect_download() as downloaded:page.get_by_role('link',name='下载当前研究范围的复核包 · ZIP',exact=True).click()
    try:downloaded.value.save_as(OUT/'scope-download.zip')
    except Exception:
        response=context.request.get(downloaded.value.url)
        diagnostic={'url':downloaded.value.url,'filename':downloaded.value.suggested_filename,'failure':downloaded.value.failure(),'status':response.status,'headers':response.headers}
        (OUT/'download-error.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(diagnostic,ensure_ascii=False),flush=True)
        raise
    with zipfile.ZipFile(OUT/'scope-download.zip') as z:
        manifest=json.loads(z.read('manifest.json'));rows=pd.read_csv(io.BytesIO(z.read('observations.csv')))
        assert manifest['scope']=={'region':'kara','years':[2016,2025],'month':3}
        assert len(rows)==10 and set(rows.region_id)=={'kara'} and set(rows.month)=={3}
        assert rows.extent_km2.notna().all()
    checks.append('Export contains exactly the chosen observations and a source/method manifest')
    page.get_by_role('tab',name='海区与同月观测',exact=True).click()
    page.get_by_role('button',name='在北极地图查看这个地点',exact=True).click();page.wait_for_timeout(1400)
    page.frame_locator('iframe').first.locator('[title="萨别塔"]').wait_for(timeout=20000)
    assert page.frame_locator('iframe').first.locator('.atlas-dot').count()==1
    page.get_by_role('button',name=re.compile('阅读专题 · 亚马尔')).click()
    page.get_by_role('heading',name='亚马尔 LNG：港口、冰区运输与投资',exact=True).wait_for(timeout=20000)
    page.get_by_role('tab',name='研究解释',exact=True).click();healthy()
    page.get_by_role('heading',name='技术在这个案例中起什么作用',exact=True).wait_for(timeout=20000)
    checks.append('Selected region links to the matching place/photo dossier and project evidence')
    choose('选择项目专题','Kinuvik：跨大西洋的卫星接收协作')
    page.get_by_role('tab',name='项目时间线与地点',exact=True).click()
    assert page.get_by_text('当前时窗内尚无已整理的项目节点；下方可展开历史背景。',exact=True).count()
    page.get_by_role('button',name='在地图中查看 · 埃斯兰航天中心',exact=True).click();page.wait_for_timeout(1200)
    page.frame_locator('iframe').first.locator('[title="埃斯兰航天中心"]').wait_for(timeout=20000)
    assert 'Esrange' in page.get_by_role('combobox',name=re.compile('当前地点')).get_attribute('aria-label')
    nav('区域联动')
    assert '喀拉海' in page.get_by_role('combobox',name=re.compile('研究海区')).get_attribute('aria-label')
    assert '3 月' in page.get_by_role('combobox',name=re.compile('比较月份')).get_attribute('aria-label')
    shot('regional-kara.png');checks.append('Research scope survives project/map navigation; out-of-scope case remains readable')
    nav('技术与地缘');page.get_by_text('技术检索与专利样本',exact=True).click();page.wait_for_timeout(500)
    page.get_by_text('导入检索结果，检查并按族归并',exact=True).click()
    page.locator('input[type="file"]').set_input_files(str(ROOT/'data/analysis/patent_sample.csv'))
    page.get_by_text('3 个公开文本，归并为 2 个专利族。格式检查通过，相关性仍需人工确认。',exact=True).wait_for(timeout=15000)
    shot('patent-families.png');checks.append('Real patent CSV import deduplicates publication stages into two families')
    nav('事件线索');page.get_by_role('tab',name='原文核验与归并',exact=True).click()
    assert page.get_by_role('button',name='保存核验记录',exact=True).is_enabled()
    page.get_by_role('button',name='保存核验记录',exact=True).click()
    page.get_by_text('请填写核验人和至少 8 字的核验说明。',exact=True).wait_for(timeout=15000)
    assert (review_file.read_bytes() if review_file.exists() else None)==initial_reviews
    page.get_by_role('tab',name='候选检索',exact=True).click()
    box=page.get_by_role('textbox',name='检索历史报道',exact=True);box.fill('zz-no-history-match');box.press('Enter')
    page.get_by_text('没有符合检索条件的候选记录。',exact=True).wait_for(timeout=15000)
    box.fill('mosaic');box.press('Enter');page.wait_for_timeout(700);healthy();shot('history-candidates.png')
    checks.append('Historical candidate search and local review validation work without fabricating review records')
    nav('区域联动');page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(1300);healthy()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    shot('mobile-regional.png');checks.append('Regional page fits a 390 px mobile viewport')
    browser.close()
(OUT/'browser-report.json').write_text(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2))
assert not errors
