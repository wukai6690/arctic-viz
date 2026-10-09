"""Visible end-to-end checks for the research journey, cases and preparation records."""
import csv,io,json,os,re,time,zipfile
from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright,expect
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'test-results/case-journey';OUT.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('ARCTIC_TEST_URL','http://127.0.0.1:8502');checks=[];errors=[];pdfs={};download_pages=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-angle=swiftshader'])
    context=browser.new_context(viewport={'width':1540,'height':1060},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(45000);page.on('pageerror',lambda e:errors.append(str(e)))
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
    app.locator('.home-intro h1').wait_for(timeout=90000)
    sidebar=app.locator('[data-testid="stSidebar"]')
    def settle():
        page.wait_for_timeout(250);app.locator('.stApp[data-test-script-state="notRunning"]').wait_for()
        assert not app.locator('[data-testid="stException"]').count(),app.locator('[data-testid="stException"]').all_text_contents()
    def run_action(action):
        before=runs['finished'];action();deadline=time.monotonic()+60
        while runs['finished']<=before and time.monotonic()<deadline:page.wait_for_timeout(100)
        assert runs['finished']>before,'No successful Streamlit run completed after action'
        settle()
    def click(locator):run_action(lambda:locator.click())
    def nav(label):
        link=sidebar.get_by_role('link',name=label,exact=True);box=link.bounding_box()
        if not box or box['x']<0:app.locator('[data-testid="stExpandSidebarButton"]').click();settle()
        click(link);print('Page: '+label,flush=True)
    def tab(label):app.get_by_role('tab',name=label,exact=True).click();settle()
    def shot(name,target=None):
        if target:
            target.evaluate("e=>e.scrollIntoView({block:'start'})")
            app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop-=80')
        settle();page.screenshot(path=str(OUT/name),animations='disabled')
    def loaded(panel=None):
        images=(panel or app).locator('[data-testid="stImage"] img')
        for _ in range(60):
            if images.count() and images.evaluate_all('(es)=>es.every(e=>e.complete && e.naturalWidth>0)'):return
            page.wait_for_timeout(300)
        raise AssertionError('Images did not finish loading')
    def download(label):
        with page.expect_download() as result:app.get_by_role('button',name=label,exact=True).click()
        target=OUT/result.value.suggested_filename;result.value.save_as(target);return target
    def pdf(cid):
        target=download('下载案例报告 · PDF');assert target.read_bytes().startswith(b'%PDF-')
        download_pages.append({'case':cid,'pages':[p.url for p in context.pages]})
        with pymupdf.open(target) as document:
            assert document.page_count>=2
            text=''.join(page.get_text() for page in document)
            assert ('MOSAiC' if cid=='mosaic' else 'ASBM' if cid=='asbm' else '亚马尔') in text
            pdfs[cid]={'file':target.name,'pages':document.page_count,'bytes':target.stat().st_size}
    def mobile_fit():
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    loaded();assert '技术如何改变北极活动' in app.locator('.home-intro h1').inner_text()
    assert '尚未开展访谈或实地调研' in app.locator('[data-testid="stMain"]').inner_text()
    shot('home.png');checks.append('Home leads with the research question, actual work, three cases and truthful no-fieldwork status')
    nav('研究导览')
    for index,name in enumerate(['研究问题','真实观测','案例比较','证据边界','实际工作']):
        expect(app.get_by_text(f'{index+1} / 5 · {name}',exact=True)).to_be_visible()
        if index<4:click(app.get_by_role('button',name='下一步',exact=True))
    expect(app.get_by_role('button',name='下一步',exact=True)).to_be_disabled()
    click(app.get_by_role('button',name='上一步',exact=True))
    expect(app.get_by_text('4 / 5 · 证据边界',exact=True)).to_be_visible()
    shot('guided-reading.png');checks.append('Five-step journey advances and returns correctly; final next button is disabled')
    nav('案例研究');expect(app.get_by_role('heading',name='MOSAiC：一年的观测，依赖哪些条件',exact=True)).to_be_visible()
    panel=app.locator('[role="tabpanel"]:visible');loaded(panel)
    expect(panel.locator('[data-testid="stImage"] img')).to_have_count(1)
    expect(panel.locator('.geolayer .geo')).to_have_count(1)
    panel.locator('.geolayer path').first.wait_for(state='attached')
    assert '2019-10-15' in panel.inner_text()
    shot('mosaic-track-ice.png',app.get_by_role('tab',name='航迹与同期冰情',exact=True))
    tab('证据与下载');package=download('下载当前日期证据包 · ZIP')
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        selected=json.loads(z.read('manifest.json'));assert selected['selection']['day']=='2019-10-15'
        assert selected['ice']['status']=='available' and 'ice-2019-10-15.png' in z.namelist()
        rows=list(csv.DictReader(io.StringIO(z.read('selected_day_positions.csv').decode('utf-8-sig'))))
        assert rows and all(row['timestamp'].startswith('2019-10-15') for row in rows)
    pdf('mosaic')
    tab('航迹与同期冰情')
    click(app.get_by_text('全部船位日期',exact=True))
    slider=app.locator('[role="tabpanel"]:visible').get_by_role('slider')
    slider.focus();run_action(lambda:slider.press('ArrowRight'))
    expect(app.get_by_text('该日有真实船位，尚未保存同日冰情图。切换到“已有同期冰图的日期”可查看已核对图组。',exact=True)).to_be_visible()
    panel=app.locator('[role="tabpanel"]:visible');expect(panel.locator('[data-testid="stImage"] img')).to_have_count(0)
    missing_day=re.search(r'实测船位：(\d{4}-\d{2}-\d{2})',panel.inner_text()).group(1)
    assert missing_day=='2019-10-16'
    shot('mosaic-missing-ice.png',app.get_by_role('tab',name='航迹与同期冰情',exact=True))
    tab('证据与下载');package=download('下载当前日期证据包 · ZIP')
    with zipfile.ZipFile(package) as z:
        selected=json.loads(z.read('manifest.json'));assert selected['selection']['day']==missing_day and selected['ice'] is None
        assert not any(name.endswith('.png') for name in z.namelist())
        rows=list(csv.DictReader(io.StringIO(z.read('selected_day_positions.csv').decode('utf-8-sig'))))
        assert rows and all(row['timestamp'].startswith(missing_day) for row in rows)
    tab('设备与观测成果');loaded(app.locator('[role="tabpanel"]:visible'))
    checks.append('MOSAiC measured route and dated ice load; changing date yields honest missing-image state; actual ZIPs preserve date and image availability')
    for cid,label in [('asbm','ASBM'),('yamal','亚马尔')]:
        click(app.get_by_text(label,exact=True))
        pdf(cid);txt=download('下载报告正文与出处 · TXT').read_text(encoding='utf-8')
        assert label in txt and 'http' in txt
        for name in ['主要认识','历史时序','任务与能力','解释与边界','现场影像','全部依据']:
            tab(name);panel=app.locator('[role="tabpanel"]:visible')
            assert panel.inner_text().strip()
            if name=='现场影像':loaded(panel)
        panel=app.locator('[role="tabpanel"]:visible')
        before=page.url;pages_before=len(context.pages)
        source_title=panel.get_by_role('button').first.inner_text()
        click(panel.get_by_role('button').first)
        dialog=app.get_by_role('dialog');expect(dialog).to_be_visible()
        expect(dialog.get_by_role('heading',name=source_title,exact=True)).to_be_visible()
        shot(cid+'-source-reader.png')
        diagnostic={'before':before,'after':page.url,'tabs_before':pages_before,'tabs_after':len(context.pages),'page_urls':[p.url for p in context.pages],'dialog_text':dialog.inner_text()}
        assert page.url==before and len(context.pages)==pages_before and len(diagnostic['dialog_text'])>100,diagnostic
        page.keyboard.press('Escape');settle()
        evidence=download('下载案例结构化证据 · JSON')
        evidence_data=json.loads(evidence.read_text(encoding='utf-8'))
        assert evidence_data['case']['id']==cid and evidence_data['version'] and evidence_data['reviewed_at']
        assert set(evidence_data['case']['source_ids'])=={source['id'] for source in evidence_data['sources']}
        assert all(source['url'].startswith('http') for source in evidence_data['sources'])
        tab('历史时序');shot(cid+'-timeline.png',app.get_by_role('tab',name='历史时序',exact=True))
    checks.append('ASBM and Yamal all six tabs, real photo loading, same-site source dialogs, exact JSON/TXT downloads and all three PDF reports pass')
    for _ in range(2):
        nav('研究总览');click(app.get_by_role('button',name='进入案例',exact=True).nth(1))
        expect(app.get_by_role('heading',name='ASBM：高纬通信如何形成合作分工',exact=True)).to_be_visible()
    checks.append('Repeated navigation from the home ASBM card preserves the intended case after widget cleanup')
    nav('研究过程');tab('调研记录入口')
    template=json.loads(download('下载空白记录模板 · JSON').read_text(encoding='utf-8'))
    assert template['status']=='计划' and not template['summary'] and not template['activity_date']
    app.get_by_role('textbox',name='记录编号',exact=True).fill('ui-plan-check')
    app.get_by_role('textbox',name='这次活动要回答什么问题',exact=True).fill('待开展的网站试用：读者能否找到一个研究判断的依据？')
    app.get_by_role('textbox',name='记录摘要',exact=True).fill('界面测试用计划；尚未开展，不包含受访者、引文或调查结果。')
    click(app.get_by_role('button',name='整理为可下载记录',exact=True))
    exported=json.loads(download('下载这份研究记录 · JSON').read_text(encoding='utf-8'))
    assert exported['id']=='ui-plan-check' and exported['status']=='计划'
    assert not exported['participant_code'] and not exported['activity_date'] and not exported['evidence_reference']
    assert app.get_by_role('button',name='追加保存到本地私有记录',exact=True).count()==0
    app.get_by_role('textbox',name='记录编号',exact=True).fill('bad id')
    click(app.get_by_role('button',name='整理为可下载记录',exact=True))
    expect(app.get_by_text('编号使用 3—50 位字母、数字、下划线或短横线。',exact=True)).to_be_visible()
    assert app.get_by_role('button',name='下载这份研究记录 · JSON',exact=True).count()==0
    checks.append('Public process page downloads a blank template and valid hypothetical plan; invalid replacement removes stale download; no public write button')
    page.set_viewport_size({'width':390,'height':844});settle();mobile_fit()
    app.locator('[data-testid="stMain"]').evaluate('e=>e.scrollTop=0');shot('process-mobile.png')
    form=app.locator('[data-testid="stForm"]');assert form.evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    page.set_viewport_size({'width':1540,'height':1060});settle();nav('案例研究')
    click(app.get_by_text('ASBM',exact=True));tab('任务与能力')
    page.set_viewport_size({'width':390,'height':844});settle();mobile_fit()
    shot('case-mobile.png',app.get_by_role('tab',name='任务与能力',exact=True))
    rows=app.locator('[role="tabpanel"]:visible .reading-row');assert rows.evaluate_all('(es)=>es.every(e=>e.scrollWidth<=e.clientWidth+1)')
    page.set_viewport_size({'width':1540,'height':1060});settle()
    click(app.get_by_text('MOSAiC',exact=True))
    page.set_viewport_size({'width':390,'height':844});settle();mobile_fit()
    shot('mosaic-mobile.png',app.get_by_role('tab',name='航迹与同期冰情',exact=True))
    checks.append('Case, measured-route view and research-record form fit a 390 px viewport without page or reading-row overflow')
    browser.close()
report={'url':BASE,'checks':checks,'pdfs':pdfs,'pdf_download_pages':download_pages,'page_errors':errors}
(OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
