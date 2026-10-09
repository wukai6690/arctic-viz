"""Project dossiers and evidence-bounded research interpretations."""
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.presentation import section_title,show_chart
from src.evidence_views import place_catalog,photo_figure,photo_grid
from src.research_catalog import research_catalog,project_media,open_place,open_project
from src.source_library import source_button,source_href

def source_link(source,label='原始资料'):
    return f'[{label} · {source["publisher"]}]({source_href(source["url"])})'

def relationship_figure(project):
    edges=project['relationships'];fig=go.Figure()
    left=list(dict.fromkeys(e['from'] for e in edges));right=list(dict.fromkeys(e['to'] for e in edges))
    pos={name:(0,(len(left)-1)/2-i) for i,name in enumerate(left)}
    pos.update({name:(1.5,(len(right)-1)/2-i) for i,name in enumerate(right)})
    mx=[];my=[];labels=[];custom=[]
    for e in edges:
        x1,y1=pos[e['from']];x2,y2=pos[e['to']]
        fig.add_trace(go.Scatter(x=[x1,x2],y=[y1,y2],mode='lines',line=dict(color='#b6cddd',width=2),hoverinfo='skip',showlegend=False))
        mx.append((x1+x2)/2);my.append((y1+y2)/2);labels.append(e['label']);custom.append(e['id'])
    fig.add_trace(go.Scatter(x=mx,y=my,customdata=custom,text=labels,mode='markers+text',textposition='top center',marker=dict(size=10,color='#8a7897',symbol='diamond'),hovertemplate='%{text}<br>点击查看依据<extra></extra>',showlegend=False))
    for names,color,xanchor in [(left,'#638fb2','middle left'),(right,'#3e6f97','middle right')]:
        fig.add_trace(go.Scatter(x=[pos[n][0] for n in names],y=[pos[n][1] for n in names],text=names,mode='markers+text',textposition=xanchor,cliponaxis=False,marker=dict(size=15,color=color,line=dict(color='#fff',width=2)),hovertemplate='%{text}<extra></extra>',showlegend=False))
    fig.update_traces(selected=dict(marker=dict(opacity=1)),unselected=dict(marker=dict(opacity=1),textfont=dict(color='#304e68')))
    fig.update_layout(height=max(280,len(left)*70),margin=dict(l=190,r=200,t=35,b=30),xaxis=dict(visible=False,range=[-.15,1.65]),yaxis=dict(visible=False,range=[-max(1,len(left)/2),max(1,len(left)/2)]),clickmode='event+select',dragmode=False)
    return fig

def render_project():
    catalog=research_catalog();projects=catalog['projects'];sources={s['id']:s for s in catalog['sources']}
    places={p['id']:p for p in place_catalog()['places']}
    section_title('TECHNOLOGY & GEOGRAPHY','技术与地缘','从具体项目出发，查看技术分工、参与机构与地理节点之间的联系。')
    pending=st.session_state.pop('_project_pending',None)
    if not st.session_state.get('project_initialized'):
        pending=pending or st.query_params.get('project');st.session_state['project_initialized']=True
    if pending in [p['id'] for p in projects]:
        st.session_state['project_choice']=pending;st.session_state['project_domain']='全部领域'
    a,b=st.columns([1,2])
    domain=a.selectbox('研究领域',['全部领域',*dict.fromkeys(p['domain'] for p in projects)],key='project_domain')
    subset=[p for p in projects if domain=='全部领域' or p['domain']==domain];by_id={p['id']:p for p in subset}
    if st.session_state.get('project_choice') not in by_id:st.session_state['project_choice']=subset[0]['id']
    pid=b.selectbox('选择项目专题',list(by_id),format_func=lambda x:by_id[x]['title'],key='project_choice')
    project=by_id[pid];st.query_params['project']=pid
    if pid in ['mosaic','asbm','yamal']:
        from src.home_views import open_case
        if st.button('阅读完整案例：观测、时序与研究边界',key='project-deep-case'):open_case(pid)
    from src.study_scope import scope,scope_label
    from src.study_data import PROJECT_REGIONS,read_json
    study=scope()
    if st.session_state.get('_study_active'):
        related=study['region']=='all' or study['region'] in PROJECT_REGIONS.get(pid,[])
        st.caption('当前研究范围：'+scope_label()+(' ｜ 本专题有区域关联或服务背景。' if related else ' ｜ 本专题作为扩展案例阅读，不计入当前海区项目节点。'))
    left,right=st.columns([1.1,1],gap='large')
    with left:
        st.markdown(f'<div class="eyebrow">{escape(project["domain"])} / {escape(project["years"])}</div>',unsafe_allow_html=True)
        st.subheader(project['title']);st.write(project['question']);st.caption(project['summary'])
        st.markdown('**已核对的事实**')
        for i,f in enumerate(project['facts']):
            st.write(f['text'])
            source_button(sources[f['source_id']]['url'],'阅读依据 · '+sources[f['source_id']]['publisher'],key=f'fact-{pid}-{i}')
    photos=project_media().get(project.get('media_key',pid),[])
    if not photos and project.get('media_place') in places:photos=places[project['media_place']]['photos']
    with right:
        if photos:photo_figure(photos[0])
        else:
            st.markdown('<div class="project-text-cover"><small>ARCTIC SATELLITE BROADBAND MISSION</small><h2>高纬地区的通信条件</h2><p>本专题核对发射公告与参与方角色。轨道卫星不作为地面设施标记。</p></div>',unsafe_allow_html=True)
            source_button(sources['asbm-launch']['url'],'阅读 Space Norway 发射公告导读',key='asbm-source')
    st.divider()
    relation_tab,time_tab,capability_tab,mechanism_tab,interpretation_tab=st.tabs(['参与关系与依据','项目时间线与地点','技术与活动','双向作用','研究解释'])
    from src.research_extensions import render_capability,render_mechanisms
    with capability_tab:render_capability(pid)
    with mechanism_tab:render_mechanisms(pid,key='project-mechanisms-'+pid)
    with relation_tab:
        st.caption('每条线对应一种具体关系，线宽不表示强度；点击菱形标记或使用下方菜单查看依据。')
        event=show_chart(relationship_figure(project),key='relations-'+pid,on_select='rerun',selection_mode='points')
        relations={e['id']:e for e in project['relationships']};state_key='relation-choice-'+pid
        selected=event.get('selection',{}).get('points',[]) if event else []
        if selected and selected[-1].get('customdata') in relations:
            selected_id=selected[-1]['customdata']
            if st.session_state.get('relation-point-'+pid)!=selected_id:
                st.session_state[state_key]=selected_id;st.session_state['relation-point-'+pid]=selected_id
        rid=st.selectbox('查看关系依据',list(relations),format_func=lambda x:relations[x]['from']+' → '+relations[x]['to']+' · '+relations[x]['label'],key=state_key)
        relation=relations[rid];source=sources[relation['source_id']]
        st.markdown(f'<div class="evidence-card"><small>关系依据</small><h3>{escape(relation["from"])} → {escape(relation["to"])}</h3><p>{escape(relation["label"])}</p></div>',unsafe_allow_html=True)
        source_button(source['url'],'站内阅读这条关系的依据',key='relation-source-'+pid)
        st.caption('资料发布日期：'+(source['published_at'] or '原页未列明确发布日期')+' ｜ 核对日期：'+source['accessed_at'])
    with time_tab:
        st.subheader('项目时间线')
        scoped=st.session_state.get('_study_active',False)
        visible=[n for n in project['timeline'] if not scoped or study['years'][0]<=int(n['date'][:4])<=study['years'][1]]
        if not visible:st.info('当前时窗内尚无已整理的项目节点；下方可展开历史背景。')
        for item in visible:
            s=sources[item['source_id']]
            st.markdown(f'<div class="timeline-row"><time>{escape(item["date"])}</time><div><b>{escape(item["label"])}</b><br>{escape(s["publisher"])}</div></div>',unsafe_allow_html=True)
            source_button(s['url'],'阅读节点资料',key='timeline-'+pid+'-'+str(project['timeline'].index(item)))
        st.caption('仅展示有材料支持的节点；年度记录保留年度精度，不补造具体日期。')
        background=[n for n in project['timeline'] if n not in visible]
        if background:
            with st.expander('研究时窗之外的项目背景'):
                for item in background:
                    st.write(f"**{item['date']} · {item['label']}**")
                    source_button(sources[item['source_id']]['url'],'阅读背景资料',key='background-'+pid+'-'+str(project['timeline'].index(item)))
        st.markdown('#### 关联地点')
        if project['place_ids']:
            for col,place_id in zip(st.columns(len(project['place_ids'])),project['place_ids']):
                with col:
                    place=places[place_id]
                    st.markdown('**'+place['name']+'**');st.caption(place['description'])
                    if st.button('在地图中查看 · '+place['name'],key='project-map-'+place_id):open_place(place_id)
        else:st.caption('本专题为轨道卫星项目，目前未建立经过核对的北极地面站关联。')
        if len(photos)>1:
            st.markdown('#### 更多实景')
            photo_grid(photos,'project-'+pid)
            st.page_link('pages/9_实景图集.py',label='浏览全部实景照片 ↗')
    with interpretation_tab:
        role=read_json('evidence_context.json')['project_roles'][pid]
        st.markdown('#### 技术在这个案例中起什么作用')
        for label,field in [('地理与任务条件','condition'),('技术能力','capability'),('实际活动','activity'),
                ('参与关系','relationship'),('其他可能解释','alternatives'),('进一步验证','next_evidence')]:
            st.markdown(f'<div class="reading-row"><strong>{label}</strong><p>{escape(role[field])}</p></div>',unsafe_allow_html=True)
        st.caption('这是组织证据的研究框架；各环节之间的因果关系仍需检验。依据为上方已核对事实与对应原文。')
        st.markdown('#### 可以据此讨论什么')
        st.write(project['interpretation'])
        st.markdown('#### 证据的边界')
        st.write(project['limits'])
        st.markdown('#### 与中国相关的后续问题')
        st.write(project['china'])
        st.write(role['china_action'])
        st.caption('此处为基于材料的研究解释，不是完成因果识别后的结论。')
    st.divider()
    with st.expander(f'浏览全部 {len(projects)} 个专题'):
        for p in projects:
            c1,c2=st.columns([3,1]);c1.write('**'+p['title']+'**');c1.caption(p['summary'])
            if c2.button('打开专题',key='browse-'+p['id']):open_project(p['id'])
    with st.expander('技术检索与专利样本'):
        from src.review_views import render_patents
        render_patents()

def render_findings():
    from src.research_extensions import render_mechanisms,render_policy_comparison,render_security,render_perspectives,render_literature
    section_title('RESEARCH FINDINGS','研究发现','从政策、技术与实际活动出发，逐项检查关系怎样形成、条件怎样变化。')
    mechanism,policy,security,perspectives,existing,literature=st.tabs(['机制与证据','政策对照','中国参与条件','多方视角','案例概览','文献与研究主张'])
    with mechanism:render_mechanisms()
    with policy:render_policy_comparison()
    with security:render_security()
    with perspectives:render_perspectives()
    with existing:render_existing_findings()
    with literature:render_literature()


def render_existing_findings():
    catalog=research_catalog();by_id={p['id']:p for p in catalog['projects']}
    st.caption(catalog['scope'])
    from src.study_scope import scope,scope_label,indicator
    from src.study_views import comparison_rows
    from src.study_data import read_json
    st.subheader('先从可复核的区域观测开始')
    st.caption(scope_label()+' ｜ 改变研究范围后，此表同步更新。')
    st.dataframe(comparison_rows(scope(),indicator())[['海区','有效年份','同月均值 / km²','最低值年份','最低值 / km²']],hide_index=True,width='stretch')
    st.page_link('pages/8_区域联动研究.py',label='查看曲线、筛选规则与资料覆盖 ↗')
    st.caption('以上为真实'+('海冰范围' if indicator()=='extent' else '海冰面积')+'的描述性统计。项目与政策资料用于形成解释；尚未建立完整活动序列来检验海冰与地缘变化的因果关系。')
    themes=[
        ('极地技术能力涉及跨机构分工',['xuelong2','mosaic'],'设计、制造、科研组织和港口后勤分别出现在项目材料中。','这些案例可以支持研究分工关系；尚不足以判断合作一定改善国家间关系。'),
        ('高纬地理条件进入技术网络的组织方式',['kinuvik','asbm'],'地面站配对与卫星轨道服务，分别提供认识极地通信条件的切入点。','需要补充实际覆盖、运行和服务资料，才能评估具体能力和依赖。'),
        ('北极参与还包括资本、设施与社区',['yamal','awipev','chars'],'历史股权、联合科研基地和社区中的研究设施，呈现不同类型的参与。','不能把不同年份、不同关系类型相加成一个未经定义的国家实力分数。'),
    ]
    for title,ids,reading,limit in themes:
        st.subheader(title);st.write(reading)
        for pid in ids:
            p=by_id[pid]
            if st.button(p['title']+' ↗',key='finding-'+pid):open_project(pid)
        st.caption('解释边界：'+limit);st.divider()
    st.subheader('对中国的讨论，从具体条件开始')
    st.dataframe(pd.DataFrame([
        {'关注问题':'科考装备与合作','已有材料':'雪龙2号的设计与建造分工','下一步资料':'关键部件、运行记录、联合成果'},
        {'关注问题':'极地通信与数据','已有材料':'地面站配对与通信卫星项目','下一步资料':'服务覆盖、访问规则、可用性记录'},
        {'关注问题':'能源与交通参与','已有材料':'亚马尔 LNG 的历史股权与港口节点','下一步资料':'按同一时点整理运输、经营和政策材料'},
    ]),hide_index=True,width='stretch')
    st.caption('后续研究需要在同一时间范围内补充资料，并分别讨论技术、运营和政策条件。')
    roles=read_json('evidence_context.json')['project_roles']
    with st.expander('把中国相关问题落实到证据与行动',expanded=True):
        for pid in ['xuelong2','mosaic','yamal','asbm','chars']:
            st.markdown('**'+by_id[pid]['title']+'**')
            st.write(roles[pid]['china_action'])
            st.caption('待补充的依据：'+roles[pid]['next_evidence'])
        st.caption('这里提供研究与材料收集方向，不将尚未核验的情景写成确定性安全结论。')
