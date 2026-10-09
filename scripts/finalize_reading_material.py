"""Build local guide entries from already verified source records."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
articles=load('data/library/articles.json')
if articles['shanghai']['title']=='Jiangnan Shipyard':
    city,shipyard=articles['jiangnan'],articles['shanghai']
    citytext=(ROOT/'data/library'/city['text_path']).read_text(encoding='utf-8')
    yardtext=(ROOT/'data/library'/shipyard['text_path']).read_text(encoding='utf-8')
    for key,record,text in [('shanghai',city,citytext),('jiangnan',shipyard,yardtext)]:
        record.update(id='wiki-'+key,text_path='texts/'+key+'.txt',place_id='shanghai')
        (ROOT/'data/library'/record['text_path']).write_text(text,encoding='utf-8');articles[key]=record
    (ROOT/'data/library/articles.json').write_text(json.dumps(articles,ensure_ascii=False,indent=2),encoding='utf-8')
guides=[
 {'url':'https://www.ksat.no/news/news-archive/2023/spectacular-drone-footage-from-svalsat-the-ksat-svalbard-ground-station/','title':'SvalSat · 山地站区与卫星数据服务','publisher':'KSAT','published_at':'2023-04-02','accessed_at':'2026-10-09','kind':'项目事实导读','summary':['KSAT 的这份介绍将 SvalSat 定位在朗伊尔城附近山地，说明高纬位置有利于接收太阳同步轨道航天器过境信号。','该材料把站点与全球气象数据服务联系起来。页面是 2023 年发布的设施介绍，不用其中的历史设备数量推定当前规模。'],'notice':'依据 KSAT 官方站点介绍整理的简短导读，未收录发布页全文或视频。'},
 {'url':'https://nsidc.org/data/g02135/versions/4','title':'NSIDC Sea Ice Index · 怎样阅读海冰观测','publisher':'NSIDC / 本站整理','kind':'数据方法导读','summary':['海冰范围（extent）汇总达到冰浓度阈值的海域；海冰面积（area）按网格冰浓度加权，两项指标不能混用。','本站长期图读取官方月度观测，保留缺失值，采用 1991—2020 同月基准。区域表与全北极表分别记录，不用总体海冰量推算某条航道的通航天数。','在“数据与方法”可以下载本地观测；区域联动页可下载与当前筛选完全一致的复核包。'],'notice':'本站方法导读，未收录 NSIDC 产品网页全文。'},
 {'url':'https://data.gdeltproject.org/events/index.html','title':'GDELT 日档 · 从机器编码到核验事件','publisher':'GDELT / 本站整理','kind':'数据方法导读','summary':['历史案例使用 GDELT 1.0 日档。保留原始压缩文件、日期、行号、下载校验和候选条件。候选条目并不是经过原文核验的现实事件。','来源报道、事件发生日期、地点和参与方需分别核对。相同报道可以产生多条编码，不同报道也可能讨论同一件事，不能直接把条目数当作事件数。','本站已保存有限案例窗口，不是完整十年全量数据；2026 年短时快照属于 GDELT 2.0，单独展示。'],'notice':'这是站内采集口径说明，未收录外部新闻全文。'},
 {'url':'https://www.wipo.int/web-publications/world-intellectual-property-indicators-2024-highlights/en/patents-highlights.html','title':'专利样本 · 日期与专利族口径','publisher':'WIPO / 本站整理','kind':'数据方法导读','summary':['本站样本按同族最早优先权日组织时间，保留公开号与提供方专利族编号。A/B 文本和不同国家公开文本不能简单重复计为多项发明。','三个公开文本归并为两个专利族，仅用于展示整理方法；这些样本未被认定已部署于地图项目。'],'notice':'本站采用的整理方法与样本说明，未收录 WIPO 页面全文。'},
 {'url':'https://www.usgs.gov/media/images/diomede-islands','title':'代奥米德群岛 · 地理位置导读','publisher':'USGS','kind':'地点资料导读','summary':['大小代奥米德岛位于白令海峡，西侧大岛属俄罗斯，东侧小岛属美国，国际日期变更线从两岛之间经过。USGS 该页面展示遥感影像。'],'notice':'根据 USGS 图像说明整理的简短导读，非整页存档。'},
]
published=load('data/reference/published.json')
for s in published['sources']:
    if s['source']=='nsidc':
        records=[r for r in published['sea_ice'] if r.get('source_id')==s['id']]
        guides.append({**s,'publisher':'NSIDC','kind':'本地观测记录','summary':['已保存并解析官方月度文件。海冰范围、面积、缺失和基准口径见“海冰观测”。'],'observation_records':records,'notice':'这是本站保存的来源记录与解析结果，不是产品网页全文。'})
sample=list(csv.DictReader((ROOT/'data/analysis/patent_sample.csv').open(encoding='utf-8-sig')))
for url in dict.fromkeys(r['source_url'] for r in sample):
    rows=[r for r in sample if r['source_url']==url]
    guides.append({'url':url,'title':rows[0]['title']+' · 专利样本记录','publisher':rows[0]['applicant'],'kind':'专利事实导读','summary':[f"{r['publication_id']}；优先权日 {r['priority_date']}；公开日 {r['publication_date']}。{r['relevance_note']}" for r in rows],'patent_records':rows,'notice':'这是经核对的专利著录样本，未收录完整说明书、权利要求和附图。'})
(ROOT/'data/library/guides.json').write_text(json.dumps(guides,ensure_ascii=False,indent=2),encoding='utf-8')
sys.path.insert(0,str(ROOT/'scripts'))
from build_place_profiles import build
build()
print('GUIDES',len(guides))
