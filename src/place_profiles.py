"""Multifaceted place reading and a self-contained, attributed offline package."""
import io,json,zipfile
from html import escape
from pathlib import Path
import streamlit as st
from src.presentation import ROOT
from src.source_library import LIBRARY,article_text,source_button

def profiles():
    return json.loads((ROOT/'data/reference/place_profiles.json').read_text(encoding='utf-8'))

def place_articles(pid):
    return [r for r in json.loads((LIBRARY/'articles.json').read_text(encoding='utf-8')).values() if r['place_id']==pid]

def photo_topic(photo):
    return photo.get('topic','其他视角')

@st.cache_data(show_spinner=False,max_entries=6)
def place_bundle(place_json,profile_json,articles_json):
    place=json.loads(place_json);profile=json.loads(profile_json);articles=json.loads(articles_json)
    memory=io.BytesIO()
    def paragraph(text):return '<p>'+escape(text)+'</p>'
    body='<h1>'+escape(place['name'])+'</h1>'+paragraph(profile['lede'])
    body+=paragraph(place['location_note'])
    for section in profile['sections']:body+='<h2>'+escape(section['title'])+'</h2>'+paragraph(section['body'])
    body+='<h2>研究入口 · 待检验问题</h2>'+paragraph(profile['research_question'])
    body+='<h2>真实影像</h2>'
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as bundle:
        for photo in place['photos']:
            filename=Path(photo['src']).name
            bundle.write(ROOT/'static/places'/filename,'photos/'+filename)
            body+='<figure><img src="photos/'+escape(filename)+'" alt="'+escape(photo['caption'])+'"><figcaption>'+escape(photo['caption'])+'<br>'+escape(photo['author']+' · '+photo['date']+' · '+photo['license'])+'</figcaption><pre>'+escape(photo['source_url']+'\n'+photo['license_url'])+'</pre></figure>'
        for article in articles:
            text=article_text(article)
            credit='\n'.join([article['title'],article['publisher'],article['license'],article['license_url'],article['revision_url'],article['history_url'],article['changes']])
            bundle.writestr('readings/'+Path(article['text_path']).name,credit+'\n\n'+text)
        body+='<h2>导读出处</h2>'+paragraph(profile['credit']+' '+profile['license'])
        body+='<pre>'+escape('\n'.join(profile['reading_urls']))+'</pre>'
        html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(place['name'])+' · 地点档案</title><style>body{max-width:900px;margin:40px auto;padding:0 22px;background:#f5f7f3;color:#304d43;font:17px/1.9 system-ui,sans-serif}h1,h2{line-height:1.4}h2{margin-top:2em}img{max-width:100%;max-height:600px;object-fit:contain}figure{margin:2em 0;background:white;padding:18px}figcaption,pre{font-size:13px;overflow-wrap:anywhere;white-space:pre-wrap;color:#64786e}</style><body>'+body+'</body></html>'
        bundle.writestr('打开地点档案.html',html)
        bundle.writestr('manifest.json',json.dumps({'place':place,'profile':profile,'articles':articles},ensure_ascii=False,indent=2))
        bundle.writestr('阅读说明.txt','解压后打开“打开地点档案.html”，可离线阅读中文介绍与全部地点照片。\nreadings 文件夹保存开放许可英文正文，manifest.json 保存来源、许可、版本和校验信息。\n项目导读与候选报道不冒充原网页全文。图片保留作者与许可，历史影像不代表当前状态。')
    return memory.getvalue()

def render_profile(place):
    profile=profiles()[place['id']]
    st.markdown('<div class="place-lede">'+escape(profile['lede'])+'</div>',unsafe_allow_html=True)
    for offset in range(0,len(profile['sections']),2):
        for col,section in zip(st.columns(2,gap='large'),profile['sections'][offset:offset+2]):
            with col:
                number=profile['sections'].index(section)+1
                st.markdown(f'<section class="place-reading"><small>0{number}</small><h3>{escape(section["title"])}</h3><p>{escape(section["body"])}</p></section>',unsafe_allow_html=True)
    st.markdown('<div class="place-question"><small>研究入口 · 待检验问题</small><p>'+escape(profile['research_question'])+'</p></div>',unsafe_allow_html=True)
    a,b=st.columns([1,1],gap='large')
    with a:
        st.markdown('**继续认识这个区域**');st.write(profile['compare_reason'])
        from src.evidence_views import place_catalog
        from src.research_catalog import open_place
        other=next(p for p in place_catalog()['places'] if p['id']==profile['compare_id'])
        if st.button('查看地点 · '+other['name'],key='profile-compare-'+place['id']):open_place(other['id'])
        st.caption('这里是阅读与比较入口；地图上的项目联系仍以专题来源为依据。')
    with b:
        st.markdown('**带走这份地点档案**')
        st.caption('中文导读、全部地点照片、英文背景正文和完整署名。解压后可离线浏览。')
        articles=place_articles(place['id'])
        data=place_bundle(json.dumps(place,ensure_ascii=False),json.dumps(profile,ensure_ascii=False),json.dumps(articles,ensure_ascii=False))
        st.download_button('下载地点资料包 · ZIP',data,place['id']+'-place-dossier.zip','application/zip',key='place-package-'+place['id'],on_click='ignore')
        st.caption(f'{len(place["photos"])} 张本地照片 · {len(articles)} 篇开放许可正文 · {len(data)/1024/1024:.1f} MB')
    with st.expander('导读来源与版本'):
        st.caption(profile['credit']);st.caption(profile['license']+' · 整理日期 '+profile['edited_at'])
        for i,article in enumerate(place_articles(place['id'])):source_button(article['url'],'阅读本地背景正文 · '+article['title'],key='profile-reading-'+place['id']+'-'+str(i))
        st.caption('项目事实与照片分别保留在“资料与事件”和图注中；百科背景不替代一手项目证据。')
