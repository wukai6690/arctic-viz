"""Evidence-driven additions inside the existing research, project and atlas pages."""
import json
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.presentation import show_chart
from src.source_library import source_button
from src.research_catalog import research_catalog,open_project,open_place
from src.research_extension_data import (extension_data,extension_sources,policy_comparison,mechanism_rows,
                                         filtered_activities,research_bundle,history_records)

def reading_row(label,text):
    st.markdown('<div class="reading-row"><strong>'+escape(label)+'</strong><p>'+escape(text)+'</p></div>',unsafe_allow_html=True)

def source_buttons(ids,key):
    sources=extension_sources()
    with st.expander('阅读依据与资料时点'):
        for sid in dict.fromkeys(ids):
            s=sources[sid]
            source_button(s['url'],s['title'],key=key+'-source-'+sid)
            st.caption(s.get('publisher','')+' · '+(s.get('published_at') or '发布日未标明')+' · '+s.get('locator','项目来源目录'))

def download_selection(kind,selection,rows,key,label='下载当前分析与出处 · ZIP'):
    st.download_button(label,research_bundle(kind,selection,rows),kind+'-evidence.zip','application/zip',key=key,on_click='ignore')

def render_policy_comparison():
    data=extension_data();policies={p['id']:p for p in data['policies']}
    st.subheader('同一个问题，放进不同政策中阅读')
    st.write('选择两份材料，对照科研、技术、社区或参与条件。中文为人工核对导读，短引文保留原文；不同文档类型不作机械词频排名。')
    topic=st.radio('政策比较主题',list(next(iter(policies.values()))['themes']),horizontal=True,key='policy-theme')
    a,b=st.columns(2,gap='large')
    left=a.selectbox('左侧政策',list(policies),index=1,format_func=lambda k:policies[k]['name'],key='policy-left')
    right_options=[k for k in policies if k!=left]
    if st.session_state.get('policy-right') not in right_options:st.session_state['policy-right']='no2025' if 'no2025' in right_options else right_options[0]
    right=b.selectbox('右侧政策',right_options,format_func=lambda k:policies[k]['name'],key='policy-right')
    sources=extension_sources()
    for col,pid in zip(st.columns(2,gap='large'),[left,right]):
        p=policies[pid];s=sources[p['source_id']]
        with col:
            st.markdown('<article class="policy-reading"><small>'+escape(p['date']+' / '+p['genre'])+'</small><h3>'+escape(p['name'])+'</h3><p class="policy-focus">'+escape(p['themes'][topic])+'</p></article>',unsafe_allow_html=True)
    st.caption('上方相邻阅读同一主题；原文短引、体裁与来源放在下方逐份核对。')
    for col,pid in zip(st.columns(2,gap='large'),[left,right]):
        p=policies[pid];s=sources[p['source_id']]
        with col:
            if s.get('excerpt'):
                st.markdown('**原文短引 · 文档定位**');st.text(s['excerpt']);st.caption(s['locator'])
            st.caption(p['scope'])
            source_button(s['url'],'站内阅读政策导读',key='policy-open-'+pid)
            for extra in p.get('extra_source_ids',[]):source_button(sources[extra]['url'],'阅读相关章节导读',key='policy-extra-'+extra)
    st.markdown('**比较时先问三件事**')
    st.write('提出了什么目标？安排了什么行动？有没有对应的实施记录？两份材料出现相似词语，并不表示执行方式相同。')
    if {left,right}=={'no2021','no2025'}:
        st.info('这组比较可以讨论表述与重点的变化。2021 年为英文摘要、2025 年为战略；不能把篇幅和体裁差异直接当作立场变化。2025 年政策也不能倒过来解释 2024 年项目启动。')
    ids=list(dict.fromkeys(pid for k in [left,right] for pid in policies[k]['project_ids']))
    names={p['id']:p['title'] for p in research_catalog()['projects']}
    with st.expander('关联专题 · 作为研究入口'):
        st.caption('主题相关不等于政策直接造成了项目变化。')
        for pid in ids:
            if st.button(names[pid],key='policy-project-'+pid):open_project(pid)
    rows=policy_comparison(left,right,topic)
    for row,pid in zip(rows,[left,right]):row['extra_source_ids']=policies[pid].get('extra_source_ids',[])
    download_selection('policy-comparison',dict(left=left,right=right,theme=topic),rows,'policy-download')

def render_mechanisms(project_id=None,key='mechanisms'):
    st.subheader('技术与地缘怎样相互作用')
    st.caption('先看方向，再看事实与时序。证据状态说明材料能支持什么，不是可信度分数。')
    data=extension_data();a,b=st.columns(2)
    direction=a.selectbox('作用方向',['全部方向','技术 → 活动与关系','地缘与制度 → 技术'],key=key+'-direction')
    statuses=list(dict.fromkeys(r['status'] for r in mechanism_rows(project_id)))
    status=b.selectbox('证据状态',['全部证据状态',*statuses],key=key+'-status')
    rows=mechanism_rows(project_id,direction,status)
    if not rows:
        st.info('当前选择没有对应材料，可调整方向或证据状态。');return
    ids=[r['id'] for r in rows]
    if st.session_state.get(key+'-choice') not in ids:st.session_state[key+'-choice']=ids[0]
    chosen=st.selectbox('研究问题',ids,format_func=lambda k:next(r['title'] for r in rows if r['id']==k),key=key+'-choice')
    row=next(r for r in rows if r['id']==chosen)
    st.markdown('<div class="mechanism-intro"><span>'+escape(row['direction'])+'</span><h3>'+escape(row['title'])+'</h3><p>'+escape(row['claim'])+'</p><small>'+escape(row['status'])+'</small></div>',unsafe_allow_html=True)
    for col,(label,value) in zip(st.columns(3,gap='large'),row['layers'].items()):
        with col:st.markdown('<div class="research-layer"><small>'+escape(label)+'</small><p>'+escape(value)+'</p></div>',unsafe_allow_html=True)
    st.markdown('**支持判断的时间节点**')
    for i,node in enumerate(row['sequence']):
        st.markdown('<div class="timeline-row"><time>'+escape(node['date'])+'</time><div>'+escape(node['description'])+'</div></div>',unsafe_allow_html=True)
    reading_row('其他可能解释',row['alternatives']);reading_row('继续检验需要',row['missing'])
    source_buttons(row['source_ids'],key+'-'+chosen)
    download_selection('mechanism',dict(project=project_id,direction=direction,status=status,question=chosen),[row],key+'-download','下载这个问题的证据表 · ZIP')

def render_capability(project_id):
    data=extension_data();row=next(r for r in data['capabilities'] if r['project_id']==project_id)
    st.subheader('技术解决什么任务')
    st.write(row['need'])
    for title,field in [('设计与规格','design'),('部署与交付','deployment'),('实际使用','operation')]:reading_row(title,row[field])
    st.caption(row['limits'])
    source_buttons(row['source_ids'],'capability-'+project_id)
    activities=filtered_activities(project_id)
    if activities:
        st.markdown('**已整理的活动记录**')
        st.dataframe(pd.DataFrame([{'日期':r['date'],'类型':r['stage'],'记录':r['event']} for r in activities]),hide_index=True,width='stretch')
        st.caption('只显示已有材料的节点。公告日期、实际发生日及成果发表日按记录说明区分。')
    reading_row('资料缺口',row['missing'])
    download_selection('capability',{'project':project_id},[row,*activities],'capability-download-'+project_id)

def render_security():
    st.subheader('中国参与北极，需要哪些具体条件')
    st.write('本项目将“功能性安全”暂作为研究框架：围绕一项任务，检查能力、参与条件、连续性与反馈。以下为分析问题及现有证据，尚未形成风险评分或经过验证的指数。')
    tasks={r['id']:r for r in extension_data()['tasks']}
    tid=st.selectbox('选择参与任务',list(tasks),format_func=lambda k:tasks[k]['name'],key='security-task');r=tasks[tid]
    st.markdown('<div class="place-question"><small>任务中的关键问题</small><p>'+escape(r['question'])+'</p></div>',unsafe_allow_html=True)
    for col,item in zip(st.columns(len(r['conditions']),gap='large'),r['conditions']):
        with col:
            st.markdown('<article class="condition-reading"><h3>'+escape(item[0])+'</h3><span>'+escape(item[1])+'</span><p>'+escape(item[2])+'</p></article>',unsafe_allow_html=True)
    reading_row('可以开展的工作',r['action']);reading_row('尚缺的直接依据',r['missing'])
    ids=list(dict.fromkeys(x[3] for x in r['conditions']));source_buttons(ids,'security-'+tid)
    record={**r,'source_ids':ids}
    download_selection('participation-conditions',{'task':tid},[record],'security-download')
    st.divider();render_scenarios()

def render_scenarios():
    st.subheader('一个条件改变后，需要重新核对什么')
    st.caption('条件比较练习。下方是假设，不表示发生过相应中断，也不输出概率、损失或未经验证的替代方案排名。')
    rows={r['id']:r for r in extension_data()['scenarios']}
    sid=st.selectbox('条件比较主题',list(rows),format_func=lambda k:rows[k]['name'],key='scenario-choice');r=rows[sid]
    reading_row('已有材料',r['baseline'])
    changed=st.checkbox(r['changed'],key='scenario-changed-'+sid)
    if changed:
        reading_row('需要检查的影响',r['affected'])
        selected=st.radio('待评估的安排',[o['name'] for o in r['options']],key='scenario-option-'+sid)
        option=next(o for o in r['options'] if o['name']==selected)
        reading_row('成立所需条件',option['conditions']);reading_row('尚不能回答',option['limits'])
    else:
        selected=None;st.info('当前显示已有材料。勾选上方假设后，可逐项检查需要补充的条件。')
    source_buttons(r['source_ids'],'scenario-'+sid)
    record={**r,'hypothesis_active':changed,'selected_option':selected}
    download_selection('conditional-comparison',{'scenario':sid,'hypothesis_active':changed,'selected_option':selected},[record],'scenario-download','下载当前条件比较 · ZIP')

def render_perspectives():
    st.subheader('同一片北极，不同参与者的关切')
    st.caption('分别记录谁在什么时间、什么材料中表达了什么。这里没有自动推断立场，也没有将机构发言当作全部居民的意见。')
    rows=extension_data()['perspectives'];roles=list(dict.fromkeys(r['role'] for r in rows))
    role=st.selectbox('参与者类型',['全部参与者',*roles],key='perspective-role')
    chosen=[r for r in rows if role=='全部参与者' or r['role']==role]
    for r in chosen:
        st.markdown('<article class="perspective-reading"><small>'+escape(r['role']+' · '+r['date'])+'</small><h3>'+escape(r['actor'])+'</h3><p>'+escape(r['position'])+'</p></article>',unsafe_allow_html=True)
        st.caption(r['limit']);source_button(extension_sources()[r['source_id']]['url'],'阅读这项表述的出处',key='perspective-'+r['id'])
    download_selection('perspectives',{'role':role},chosen,'perspective-download')

def render_activities():
    st.subheader('实际活动，与环境观测分别核对')
    st.write('先区分全北极航运汇总与单个项目的活动节点。它们的地区范围、时间粒度和统计对象不同。')
    shipping=extension_data()['shipping'];metric=st.radio('航运对照指标',['独立船舶数','航行距离'],horizontal=True,key='shipping-metric')
    key='unique_ships' if metric=='独立船舶数' else 'distance_million_nm';unit='艘' if key=='unique_ships' else '百万海里（约数）'
    obs=shipping['observations']
    fig=go.Figure(go.Bar(x=[str(r['year']) for r in obs],y=[r[key] for r in obs],marker_color=['#afc3b3','#497b6a'],text=[f'{r[key]:,}' for r in obs],textposition='outside',cliponaxis=False))
    fig.update_layout(height=325,xaxis_title='年份',yaxis=dict(title=unit,rangemode='tozero'),margin=dict(l=50,r=15,t=32,b=40))
    show_chart(fig,key='activity-shipping-chart')
    st.caption(shipping['geography']+' · '+shipping['precision'])
    st.info(shipping['note'])
    source_buttons([shipping['source_id'],'pame-access'],'shipping')
    download_selection('shipping-endpoints',{'metric':key,'geography':shipping['geography']},[{**r,'source_id':shipping['source_id'],'geography':shipping['geography'],'precision':shipping['precision']} for r in obs],'shipping-download','下载航运端点与口径 · ZIP')
    st.markdown('**项目实施与成果记录**')
    names={p['id']:p['title'] for p in research_catalog()['projects']}
    options=list(dict.fromkeys(r['project_id'] for r in extension_data()['activities']))
    pid=st.selectbox('活动记录项目',['all',*options],format_func=lambda k:'全部已有记录' if k=='all' else names[k],key='activities-project')
    rows=filtered_activities(None if pid=='all' else pid)
    for r in rows:
        st.markdown('<div class="timeline-row"><time>'+escape(r['date'])+'</time><div><b>'+escape(r['stage'])+'</b><p>'+escape(r['event'])+'</p></div></div>',unsafe_allow_html=True)
        source_button(extension_sources()[r['source_id']]['url'],'阅读活动依据',key='activity-'+r['id'])
    download_selection('activities',{'project':pid},rows,'activities-download')

def render_literature():
    st.subheader('研究主张如何得到文献支持')
    st.caption('这是首批核对记录，不是完成的系统文献综述。已找到相关研究的方向，不再笼统表述为研究空白。')
    for r in extension_data()['literature']:
        with st.expander(r['claim'],expanded=False):
            st.write('**当前判断：**'+r['status']);reading_row('已有研究或材料',r['finding']);reading_row('本项目可做的工作',r['contribution']);reading_row('继续核对',r['next'])
            for sid in r['source_ids']:source_button(extension_sources()[sid]['url'],'阅读文献或材料 · '+extension_sources()[sid]['title'],key='literature-'+r['id']+'-'+sid)
    download_selection('literature-claims',{'scope':'首批文献与研究主张对照'},extension_data()['literature'],'literature-download')

def render_place_history(place):
    record=history_records(place['id'])
    st.subheader(place['name']+' · 时点影像')
    if not record:
        st.info('这个地点尚未整理可用于时间比较的影像组。现有实景可在“地点图集”查看。')
        for pid,name in [('sabetta','萨别塔'),('kiruna','基律纳'),('nyalesund','新奥尔松')]:
            if st.button('查看 '+name+' 的时点影像',key='history-other-'+pid):open_place(pid)
        return
    st.write(record['introduction']);st.caption(record['comparison_limit'])
    photos={p['id']:p for p in place['photos']};items=record['items'];ids=[i['photo_id'] for i in items]
    def label(k):
        item=next(i for i in items if i['photo_id']==k)
        return item['date_label']+' · '+photos[k]['caption']
    a,b=st.columns(2,gap='large')
    left=a.selectbox('左侧影像',ids,format_func=label,key='history-left-'+place['id'])
    right_options=[k for k in ids if k!=left]
    state='history-right-'+place['id']
    if st.session_state.get(state) not in right_options:st.session_state[state]=right_options[-1]
    right=b.selectbox('右侧影像',right_options,format_func=label,key=state)
    from src.evidence_views import photo_figure
    for col,pid in zip([a,b],[left,right]):
        with col:
            item=next(i for i in items if i['photo_id']==pid)
            photo_figure(photos[pid],download=True,key='history-'+place['id']+'-'+pid)
            st.write(item['observation'])
    reading_row('可以继续追查',record['question'])
    st.download_button('下载影像比较记录 · JSON',json.dumps(dict(place_id=place['id'],comparison_limit=record['comparison_limit'],selected=[photos[left],photos[right]],items=[i for i in items if i['photo_id'] in [left,right]]),ensure_ascii=False,indent=2),place['id']+'-history-comparison.json','application/json',key='history-export-'+place['id'],on_click='ignore')
