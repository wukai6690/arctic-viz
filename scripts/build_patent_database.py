import json,re,requests
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('.')
IDS=[
 ('KR102629446B1','冰区船舶/破冰技术'),
 ('US9929796B2','极区卫星数据中继'),
 ('US20200208979A1','冰区航线规划'),
 ('CN106327610A','智能极地船'),
 ('CN118168551A','北极航线规划'),
 ('CN116481534B','海冰风险航线'),
 ('CN119642828A','可视化海冰风险'),
 ('CN118364265A','浮冰运动预测'),
 ('CN110319839A','极地智能导航'),
 ('CN106203721A','自适应破冰航线'),
 ('FI125961B','破冰船船型设计'),
 ('CN121384045A','AIS 航速反馈极地航线'),
]
headers={'User-Agent':'ArcticResearch/1.0 (academic data curation)'}
def clean(x): return re.sub(r'\s+',' ',x or '').strip()
def first(s,prop):
 x=s.select_one('[itemprop="'+prop+'"]'); return clean(x.get_text(' ',strip=True)) if x else ''
def many(s,prop): return [clean(x.get_text(' ',strip=True)) for x in s.select('[itemprop="'+prop+'"]') if clean(x.get_text(' ',strip=True))]
rows=[]
for pub,tech in IDS:
 u=f'https://patents.google.com/patent/{pub}/en'
 try:
  response=requests.get(u,headers=headers,timeout=30)
  s=BeautifulSoup(response.content,'lxml')
  abstract=s.select_one('div.abstract') or s.select_one('section[itemprop="abstract"]')
  if abstract is None:
   meta=s.select_one('meta[name="DC.description"]')
   abstract_text=clean(meta.get('content','') if meta else '')
  else:
   abstract_text=clean(abstract.get_text(' ',strip=True))
   abstract_text=re.sub(r'^Abstract(?:\s+Translated from [^ ]+)?\s*','',abstract_text,flags=re.I)
  claims=s.select('div.claim') or s.select('section[itemprop="claims"] div.claim')
  codes=[]
  for x in s.select('[itemprop="code"]'):
   code=clean(x.get_text(' ',strip=True))
   if code and code not in codes: codes.append(code)
  row={
   'publication_number':pub,'technology':tech,'source_url':u,
   'title':first(s,'title'),'country':first(s,'countryName'),'assignee':first(s,'assigneeCurrent') or first(s,'assigneeOriginal'),
   'inventors':many(s,'inventor')[:8],'priority_date':first(s,'priorityDate'),'filing_date':first(s,'filingDate'),
   'publication_date':first(s,'publicationDate'),'application_number':first(s,'applicationNumber'),'status':first(s,'status'),
   'classifications':codes[:8],'abstract':abstract_text,
   'claim_1':clean(claims[0].get_text(' ',strip=True)) if claims else '',
  }
  if not row['title'] or not row['abstract']:
   print('incomplete',pub,row['title'],len(row['abstract']))
  rows.append(row)
  # Keep rebuild logs safe on Windows consoles whose code page cannot encode every assignee.
  print(pub,row['priority_date'],row['publication_date'],len(row['abstract']),ascii(row['assignee']))
 except Exception as e: print('ERROR',pub,e)
meta={'version':'arctic-patent-database-20261017-v1','generated_at':'2026-10-17','source_note':'公开专利元数据和摘要来自 Google Patents 页面；法律状态未独立核验。专利与北极项目部署关系需要人工核对。','records':rows,'fields':['publication_number','technology','title','country','assignee','priority_date','publication_date','status','classifications','abstract','claim_1','source_url']}
Path('data/analysis/patents/patents.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print('written',len(rows))
