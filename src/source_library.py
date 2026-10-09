"""Local, provenance-preserving reading. No network requests during browsing."""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
import pandas as pd
import streamlit as st
from src.presentation import ROOT, section_title

LIBRARY = ROOT/'data/library'

def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def canonical_url(url):
    return unquote(str(url or '')).rstrip('/')

def source_id(url):
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:20]

def source_href(url):
    return '/站内资料?source='+source_id(url)

def local_file(path, root=ROOT):
    """Metadata is local, but still reject traversal and symlinks outside its root."""
    candidate=(root/path).resolve()
    if not candidate.is_relative_to(root.resolve()):raise ValueError('Invalid local document path')
    return candidate

def source_records():
    records={}
    def add(record, aliases=()):
        record={**record,'id':source_id(record['url'])}
        for url in [record['url'],*aliases]:records[source_id(url)]=record
        return record
    for article in read_json(LIBRARY/'articles.json',{}).values():
        add(article, [article['requested_url']])
    research=read_json(ROOT/'data/reference/research.json',{})
    for source in research.get('sources',[]):
        facts=list(dict.fromkeys(f['text'] for p in research['projects'] for f in p['facts'] if f['source_id']==source['id']))
        nodes=[f"{n['date']} · {n['label']}" for p in research['projects'] for n in p['timeline'] if n['source_id']==source['id']]
        relations=[f"{r['from']} → {r['to']}：{r['label']}" for p in research['projects'] for r in p['relationships'] if r['source_id']==source['id']]
        add({**source,'kind':'项目事实导读','summary':facts,'nodes':nodes,'relations':relations,
             'notice':'下文是本站依据发布方材料整理的事实导读，未收录该网页全文。历史信息保留材料日期。'})
    context=read_json(ROOT/'data/analysis/evidence_context.json',{})
    for source in context.get('sources',[]):
        add({**source,'kind':'政策资料导读','summary':[n['description'] for n in context['policy_nodes'] if n['source_id']==source['id']],
             'nodes':[n['date']+' · '+n['label'] for n in context['policy_nodes'] if n['source_id']==source['id']],
             'notice':'本站整理的历史政策导读；未收录发布页全文。'})
    for source in read_json(LIBRARY/'guides.json',[]):add(source)
    for source in read_json(ROOT/'data/reference/research_extensions.json',{}).get('sources',[]):
        previous=records.get(source_id(source['url']),{})
        add({**previous,**source,'research_id':source['id']})
    # Register the actual downloaded raw files, rather than remote substitutes.
    for sidecar in (ROOT/'data/analysis/raw').glob('*.source.json'):
        metadata=read_json(sidecar,{})
        path=sidecar.with_name(sidecar.name.removesuffix('.source.json'))
        url=metadata.get('url') or metadata.get('source_url')
        if url and path.exists():
            add({'url':url,'title':path.name,'publisher':'NSIDC','kind':'原始数据文件','file_path':str(path.relative_to(ROOT)),
                 'summary':['下载本地保存的官方原始文件；本站区域统计与边界分别由对应工作簿和掩膜整理。'], 'metadata':metadata})
    places=read_json(ROOT/'data/reference/places.json',{})
    media=read_json(ROOT/'data/reference/project_media.json',{})
    photos=[photo for p in places.get('places',[]) for photo in p['photos']]+[photo for items in media.values() for photo in items]
    for photo in photos:
        add({'url':photo['source_url'],'title':photo['caption'],'publisher':photo['author'],'kind':'实景照片','photo':photo})
    for place in places.get('places',[]):
        for field in ['reference_url','coordinate_source']:
            url=place.get(field)
            if url and source_id(url) not in records:
                add({'url':url,'title':place['name']+' · '+('位置与坐标' if field=='coordinate_source' else '地点资料记录'),
                     'publisher':urlsplit(url).netloc,'kind':'地点资料导读','place_id':place['id'],
                     'summary':[place['description'],place['location_note']],
                     'notice':'地点目录的本地资料卡。更多背景正文见本地点的开放许可阅读材料；未收录此来源页全文。'})
    return records

def resolve_source(url):
    record=source_records().get(source_id(url))
    if record:return record
    # Unknown / unarchived articles remain machine records, never fabricated prose.
    from src.study_data import candidates
    matches=[r for r in candidates() if canonical_url(r.get('source_url'))==canonical_url(url)]
    if not matches:
        matches=[r for r in read_json(ROOT/'data/reference/published.json',{}).get('events',[]) if canonical_url(r.get('source_url'))==canonical_url(url)]
    return {'id':source_id(url),'url':url,'title':'报道候选记录' if matches else '来源登记',
        'publisher':urlsplit(url).netloc,'kind':'候选报道记录' if matches else '资料索引',
        'records':matches,'summary':[],
        'notice':'尚未收录此网页的正文。以下仅保留本地候选记录与出处，不能据此完成原文核验。' if matches else '本站保留了出处，尚未收录这份材料的正文。'}

def article_text(record):
    if not record.get('text_path'):return ''
    path=local_file(record['text_path'],LIBRARY)
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Local article checksum differs from recorded revision')
    return raw.decode('utf-8').replace('\r\n','\n')

def render_source(record, key='reader'):
    st.subheader(record['title'])
    st.caption(record['kind']+' · '+record.get('publisher','来源未注明'))
    if record.get('notice'):st.info(record['notice'])
    dates=[label+' '+str(record[field])[:10] for label,field in [('发布日期','published_at'),('来源更新','revised_at'),('本站收录','retrieved_at')] if record.get(field)]
    if dates:st.caption(' · '.join(dates))
    for paragraph in record.get('summary',[]):st.write(paragraph)
    if record.get('excerpt'):
        st.markdown('**原文短引**');st.text(record['excerpt'])
    if record.get('locator'):st.caption('原文定位：'+record['locator'])
    if record.get('research_id'):
        guide='\n'.join([record['title'],record.get('publisher',''),record.get('published_at') or '原页未注明发布日期',
                          record.get('notice',''),*record.get('summary',[]),'原文短引：'+record.get('excerpt','无'),
                          '原文定位：'+record.get('locator',''),record['url'],'本站核对：'+record.get('retrieved_at','')])
        st.download_button('下载中文导读与出处 · TXT',guide,record['research_id']+'-guide.txt','text/plain',key=key+'-guide',on_click='ignore')
    if record.get('observation_records'):
        st.dataframe(pd.DataFrame(record['observation_records']),hide_index=True,width='stretch',height=300)
        st.download_button('下载本地解析观测 · CSV',pd.DataFrame(record['observation_records']).to_csv(index=False).encode('utf-8-sig'),'observations.csv','text/csv',key=key+'-observations',on_click='ignore')
    if record.get('nodes'):
        st.markdown('**材料中的时间节点**')
        for node in dict.fromkeys(record['nodes']):st.write('• '+node)
    if record.get('relations'):
        st.markdown('**这份材料支持的关系**')
        for relation in dict.fromkeys(record['relations']):st.write('• '+relation)
    if record.get('photo'):
        from src.evidence_views import photo_figure
        photo_figure(record['photo'],download=True,key=key+'-photo')
    body=article_text(record)
    if body:
        profile=read_json(ROOT/'data/reference/place_profiles.json',{}).get(record.get('place_id'))
        if profile:
            st.write(profile['lede'])
            with st.expander('展开中文地点导读'):
                st.write(profile['lede'])
                for section in profile['sections']:st.write('**'+section['title']+'**');st.write(section['body'])
                st.caption(profile['credit']+' '+profile['license'])
        st.caption('已保存英文正文，不含原网页的图片、脚注链接和排版。上方可展开中文导读；项目事实另有一手资料。')
        query=st.text_input('在正文中查找',key=key+'-query').strip()
        paragraphs=body.split('\n\n')
        selected=[p for p in paragraphs if query.casefold() in p.casefold()] if query else paragraphs
        if query:st.caption(f'找到 {len(selected)} 个段落')
        if not selected:st.info('正文中没有这个词，请尝试英文地名或关键词。')
        with st.container(height=440,border=True):
            for paragraph in selected:st.text(paragraph)
        credit=f"{record['title']}\n{record['publisher']}\n{record['license']}\n{record['license_url']}\nRevision: {record['revision']}\n{record['revision_url']}\nContributor history: {record['history_url']}\n{record['changes']}\n\n"
        st.download_button('下载本地正文与署名 · TXT',credit+body,record['text_path'].split('/')[-1],'text/plain',key=key+'-text',on_click='ignore')
        st.caption(record['publisher']+' · '+record['license'])
    if record.get('records'):
        st.dataframe(pd.DataFrame([{k:r.get(k,'') for k in ['date','location','actor1','actor2','category','source_line']} for r in record['records']]),hide_index=True,width='stretch')
        st.caption('上述地点、行为体和分类由 GDELT 自动抽取，未据此补写新闻内容。')
    if record.get('file_path'):
        path=local_file(record['file_path'])
        st.download_button('下载已保存的原始文件',path.read_bytes(),path.name,key=key+'-raw',on_click='ignore')
    with st.expander('出处、许可与保存信息'):
        # Plain code makes the original address copyable without outbound navigation.
        st.caption('原始地址（供复制核对）');st.code(record['url'],language=None,wrap_lines=True)
        for label,field in [('文字许可','license_url'),('固定版本','revision_url'),('作者历史','history_url')]:
            if record.get(field):st.caption(label);st.code(record[field],language=None,wrap_lines=True)
        if record.get('sha256'):st.caption('本地文件 SHA-256');st.code(record['sha256'],language=None,wrap_lines=True)
    st.download_button('下载这份资料的记录 · JSON',json.dumps(record,ensure_ascii=False,indent=2),record['id']+'.json','application/json',key=key+'-record',on_click='ignore')

@st.dialog('站内资料阅读',width='large')
def source_dialog(url):
    render_source(resolve_source(url),'dialog-'+source_id(url))

def source_button(url,label='站内阅读',key=None):
    if url and st.button(label,key=key or 'source-'+source_id(url)):
        source_dialog(url)

def source_table(frame,column='原文',key='sources',**kwargs):
    """Tables display local reading labels, with one accessible in-place selector."""
    urls=list(dict.fromkeys(str(u) for u in frame[column] if pd.notna(u) and str(u)))
    records=source_records()
    labels={u:records.get(source_id(u),{}).get('title') or urlsplit(u).netloc for u in urls}
    shown=frame.copy();shown[column]=shown[column].map(labels).fillna('未登记')
    st.dataframe(shown.rename(columns={column:'站内资料'}),hide_index=True,width='stretch',**kwargs)
    if urls:
        if st.session_state.get(key+'-choice') not in urls:st.session_state[key+'-choice']=urls[0]
        selected=st.selectbox('选择资料后站内阅读',urls,format_func=lambda u:labels[u]+' · '+urlsplit(u).netloc,key=key+'-choice')
        source_button(selected,'阅读所选资料',key=key+'-open')

def render_library():
    section_title('LOCAL READING ROOM','站内资料','在这里阅读地点背景、项目事实和影像出处。正文、导读与候选记录分别标明收录状态。')
    records={r['id']:r for r in source_records().values()}
    requested=st.query_params.get('source')
    if requested:
        record=source_records().get(requested)
        if record:render_source(record,'page-'+requested)
        else:st.info('这个资料编号未收录，请从下面的目录查找。')
        st.divider()
    c1,c2=st.columns([1,2])
    kind=c1.selectbox('资料类型',['全部资料',*sorted({r['kind'] for r in records.values()})],key='library-kind')
    query=c2.text_input('搜索站内资料',placeholder='地点、项目、机构、图注',key='library-search').strip().casefold()
    chosen=[r for r in records.values() if (kind=='全部资料' or r['kind']==kind) and query in json.dumps({k:r.get(k) for k in ['title','publisher','summary']},ensure_ascii=False).casefold()]
    st.caption(f'找到 {len(chosen)} 份本地资料；候选新闻在“事件线索”中单独查询。')
    if chosen:source_table(pd.DataFrame([{'标题':r['title'],'收录状态':r['kind'],'来源机构/作者':r.get('publisher',''),'原文':r['url']} for r in chosen]),key='library-results',height=400)
    else:st.info('没有匹配资料。请缩短关键词或更换资料类型。')
