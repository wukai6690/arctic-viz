"""Comparable, sourced case narratives, with local downloads."""
import json
from html import escape
import streamlit as st
from src.presentation import ROOT,section_title
from src.home_views import CASES
from src.deep_case_content import load_deep_cases,get_deep_case,case_report_text
from src.source_library import source_button
from src.research_catalog import project_media,open_project
from src.evidence_views import photo_figure,place_catalog

def report_downloads(cid,text=None):
    a,b=st.columns(2)
    path=ROOT/'static/reports'/f'{cid}-case-report.pdf'
    if path.exists():a.download_button('下载案例报告 · PDF',path.read_bytes(),path.name,'application/pdf',key='case-pdf-'+cid,on_click='ignore')
    if text:b.download_button('下载报告正文与出处 · TXT',text,cid+'-case-report.txt','text/plain',key='case-txt-'+cid,on_click='ignore')

def case_sources(ids,key):
    sources={s['id']:s for s in load_deep_cases()['sources']}
    for sid in dict.fromkeys(ids):
        s=sources[sid];source_button(s['url'],s['title'],key=key+'-'+sid)
        st.caption(s['publisher']+' · '+(s.get('published_at') or '原页未标注日期')+' · '+s['locator'])

def case_gallery(cid):
    photos=list(project_media().get(cid,[]))
    if cid=='yamal':photos+=next(p['photos'] for p in place_catalog()['places'] if p['id']=='sabetta')
    if photos:
        st.caption('图像提供现场背景，不能单凭照片判断技术性能、合作强度或长期环境变化。')
        for offset in range(0,len(photos),2):
            for col,p in zip(st.columns(2,gap='large'),photos[offset:offset+2]):
                with col:photo_figure(p,download=True,key='case-photo-'+cid+'-'+p['id'])

def render_deep_case(cid):
    case=get_deep_case(cid);scope=case['scope']
    st.subheader(case['title']);st.write(case['question']);st.caption(scope['label']+' · '+scope['geography'])
    st.markdown('<div class="case-lede">'+escape(case['summary'])+'</div>',unsafe_allow_html=True)
    st.caption('观察单位：'+scope['observation_unit'])
    report_downloads(cid,case_report_text(cid))
    overview,timeline,tasks,interpret,photos,sources=st.tabs(['主要认识','历史时序','任务与能力','解释与边界','现场影像','全部依据'])
    with overview:
        for row in case['findings']:
            st.markdown('### '+row['title']);st.write(row['text']);st.caption(row['status']+' · '+row['limits'])
            with st.expander('这一判断的依据'):case_sources(row['source_ids'],cid+'-finding-'+row['id'])
        st.subheader('数字必须连同口径一起阅读')
        for offset in range(0,len(case['metrics']),2):
            for col,row in zip(st.columns(2,gap='large'),case['metrics'][offset:offset+2]):
                with col:
                    st.metric(row['label'],f"{row['value']} {row['unit']}");st.caption(row['period']+' · '+row['meaning']);st.write(row['limits'])
                    with st.expander('数据出处'):case_sources(row['source_ids'],cid+'-metric-'+row['id'])
    with timeline:
        st.caption('将计划、公告和实际事件分开登记；月份记录不补造具体日期。')
        for node in case['timeline']:
            st.markdown('<div class="timeline-row"><time>'+escape(node['date'])+'</time><div><b>'+escape(node['title'])+'</b><p>'+escape(node['text'])+'</p><small>'+escape(node['date_kind'])+'</small></div></div>',unsafe_allow_html=True)
            with st.expander('节点依据'):case_sources(node['source_ids'],cid+'-timeline-'+node['id'])
    with tasks:
        for i,row in enumerate(case['comparisons']):
            st.subheader(row['task'])
            for title,body in [('技术能力',row['capability']),('参与方','、'.join(row['actors'])),('可观察结果',row['observed_outcome']),('解释边界',row['limits'])]:
                st.markdown(f'<div class="reading-row"><strong>{escape(title)}</strong><p>{escape(body)}</p></div>',unsafe_allow_html=True)
            with st.expander('任务依据'):case_sources(row['source_ids'],cid+'-task-'+str(i))
        if case.get('historical_relations'):
            st.subheader('历史股权关系')
            for row in case['historical_relations']:st.write(f"{row['actor']}：{row['share']}{row['unit']}（{row['period']}）")
            st.caption('限于案例资料时点，不能当作当前股权或实际政治影响力。')
    with interpret:
        for i,row in enumerate(case['mechanism_evidence']):
            st.subheader(row['direction']);st.write(row['claim']);st.markdown('**已经观察到**');st.write(row['observed']);st.markdown('**尚未建立**');st.write(row['not_established'])
            with st.expander('解释依据'):case_sources(row['source_ids'],cid+'-mechanism-'+str(i))
        st.subheader('还可能有哪些解释')
        for row in case['alternatives']:st.markdown('**'+row['explanation']+'**');st.write('进一步核对：'+row['test_needed'])
        st.subheader('资料局限')
        for line in case['limits']:st.write('• '+line)
        st.subheader('中国参与的后续研究问题')
        for line in case['china_questions']:st.write('• '+line)
    with photos:case_gallery(cid)
    with sources:
        data=load_deep_cases();st.write(data['methodology']);case_sources(case['source_ids'],cid+'-all')
        bundle={'version':data['version'],'reviewed_at':data['reviewed_at'],'case':case,'sources':[s for s in data['sources'] if s['id'] in case['source_ids']]}
        st.download_button('下载案例结构化证据 · JSON',json.dumps(bundle,ensure_ascii=False,indent=2),cid+'-evidence.json','application/json',key=cid+'-json',on_click='ignore')

def render_cases():
    section_title('CASE STUDIES','案例研究','从具体任务读懂技术、环境与地缘关系。事实、解释和未解决的问题分别呈现。')
    st.caption('案例按各自注明的历史时窗阅读，不跟随侧栏的海区、年份或月份选择。')
    pending=st.session_state.pop('_case_pending',None)
    requested=st.query_params.get('case')
    if pending in CASES:
        st.session_state['case-choice']=pending
    elif requested in CASES and ('case-choice' not in st.session_state or requested!=st.session_state.get('_case_query_seen')):
        st.session_state['case-choice']=requested
    cid=st.radio('选择案例',list(CASES),format_func=lambda x:CASES[x][1].split('：')[0],horizontal=True,key='case-choice')
    st.query_params['case']=cid;st.session_state['_case_query_seen']=cid
    if cid=='mosaic':
        from src.mosaic_research import render_mosaic_research
        render_mosaic_research(key='mosaic-case');report_downloads(cid)
    else:render_deep_case(cid)
    st.divider()
    a,b=st.columns(2)
    if a.button('查看原项目关系与技术专题',key='case-original'):open_project(cid)
    b.page_link('pages/12_研究过程.py',label='查看核验与调研整理入口')
