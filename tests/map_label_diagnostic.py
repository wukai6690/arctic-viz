import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1100})
    page.goto('http://127.0.0.1:8501/北极全景地图')
    page.get_by_role('heading',name='北极地图',exact=True).wait_for(timeout=40000)
    frame=page.frame_locator('iframe').first
    frame.locator('.atlas-dot').first.wait_for(timeout=15000)
    page.wait_for_timeout(1800)
    target=next(f for f in page.frames if f.locator('.atlas-dot').count())
    details=target.evaluate('''() => {
      const names=Object.keys(window).filter(k=>k.startsWith('map_'));
      const map=window[names.find(k=>window[k]&&window[k].eachLayer)];
      const entries=[];
      map.eachLayer(l=>{if(l.options&&l.options.title){const t=l.getTooltip();entries.push({title:l.options.title,lat:l.getLatLng(),tooltip:t.getContent(),tooltipLat:t.getLatLng(),markerBox:l.getElement().getBoundingClientRect().toJSON(),tooltipBox:t.getElement().getBoundingClientRect().toJSON(),visibility:t.getElement().style.visibility});}});
      return {names,entries};
    }''')
    (ROOT/'test-results/research/map-labels.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
    visible=[e for e in details['entries'] if e['visibility']=='visible']
    for e in visible:
        assert abs(e['tooltipBox']['x']+e['tooltipBox']['width']/2-e['markerBox']['x']-e['markerBox']['width']/2)<15,e['title']
    print(json.dumps({'markers':len(details['entries']),'visible_labels':len(visible),'label_positions':'passed'},ensure_ascii=False))
    page.get_by_role('combobox',name='底图').click()
    page.get_by_role('option',name='街道地图',exact=True).click()
    street=page.frame_locator('iframe').first
    street.locator('.leaflet-tile-loaded').first.wait_for(timeout=25000)
    tiles=street.locator('.leaflet-tile-loaded').evaluate_all('(tiles)=>tiles.filter(t=>t.complete&&t.naturalWidth>0).length')
    assert tiles>0
    page.get_by_role('tab',name='球面视图',exact=True).click()
    chart=page.locator('[role="tabpanel"]:visible .js-plotly-plot')
    chart.locator('.geolayer path').first.wait_for(timeout=20000)
    page.wait_for_timeout(500)
    globe=chart.evaluate('(el)=>({points:el._fullData[0].lat.length,paths:el.querySelectorAll(".geolayer path").length})')
    assert globe['points']==29 and globe['paths']>4,globe
    chart.screenshot(path=str(ROOT/'test-results/research/globe.png'))
    (ROOT/'test-results/research/map-views-report.json').write_text(json.dumps({'visible_labels':len(visible),'aligned':True,'street_tiles_loaded':tiles,'globe':globe},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'street_tiles_loaded':tiles,'globe':globe}))
    browser.close()
