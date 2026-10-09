"""Descriptive regional study; every displayed number keeps its coverage and source."""
from html import escape
import io,json,zipfile
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.source_library import source_button,source_table
from streamlit_folium import st_folium
from src.presentation import section_title,show_chart,ROOT
from src.evidence_views import create_local_map,finish_local_map,place_catalog
from src.research_catalog import open_place,open_project
from src.study_scope import controls,scope,scope_label,indicator,copy_indicator
from src.study_data import (ASSOCIATIONS,regional_data,region_definitions,region_geometry,
    ice_frame,monthly_summary,project_nodes,coverage_table,read_json,collection_progress,verified_events)

COLORS={'barents':'#427da9','kara':'#6c968e','chukchi':'#9781a5'}
PRECISION={'day':'日','month':'月','year':'年'}

def observation_cards(s,metric):
    """Readable values, with the same scope/units as the plot and raw export."""
    from html import escape
    regions=region_definitions();ids=list(regions) if s['region']=='all' else [s['region']]
    for col,rid in zip(st.columns(len(ids),gap='large'),ids):
        summary=monthly_summary(rid,s['month'],*s['years'],metric)
        if not summary['n']:
            with col:st.info(regions[rid]['name']+'：这个时窗没有有效观测。')
            continue
        mean=summary['mean_km2']/10000;baseline=summary['baseline_km2']
        delta='同月基准资料不足' if baseline is None else f'比同月基准{ "高" if summary["mean_km2"]>=baseline else "低" } {abs(summary["mean_km2"]-baseline)/10000:.2f} 万 km²'
        years='、'.join(map(str,summary['low_years']))
        with col:
            st.markdown(f'<div class="region-summary" style="--region-color:{COLORS[rid]}"><h3>{escape(regions[rid]["name"])}</h3><small>所选时窗 · {s["month"]} 月平均'+('范围' if metric=='extent' else '面积')+f'</small><div class="value">{mean:.2f} <small>万 km²</small></div><p>{delta}<br>窗口最低：{years} 年 · {summary["min_km2"]/10000:.2f} 万 km²<br>有效观测：{summary["n"]}/{summary["expected"]} 年</p></div>',unsafe_allow_html=True)
    st.caption('摘要与曲线统一使用万 km²；基准为 1991—2020 年同月均值。最低年份只在当前时窗中寻找。')

def context_nodes(start,end):
    context=read_json('evidence_context.json');sources={s['id']:s for s in context['sources']}
    return [{**n,'source_url':sources[n['source_id']]['url']} for n in context['policy_nodes'] if start<=int(n['date'][:4])<=end]

def scoped_events(s):
    return [r for r in verified_events() if s['years'][0]<=int(r['date'][:4])<=s['years'][1] and (s['region']=='all' or r['region_id'] in [s['region'],'pan_arctic'])]

def comparison_rows(s,metric='extent'):
    rows=[];regions=region_definitions();ids=list(regions) if s['region']=='all' else [s['region']]
    for rid in ids:
        summary=monthly_summary(rid,s['month'],*s['years'],metric)
        rows.append({'海区':regions[rid]['name'],'有效年份':summary['n'],'应有年份':summary['expected'],
            '缺失年份':summary['missing'],'同月均值 / km²':summary['mean_km2'],'最低值 / km²':summary['min_km2'],
            '最低值年份':'、'.join(map(str,summary['low_years'])) or '暂无观测',
            '1991—2020 同月基准 / km²':summary['baseline_km2'],
            '描述性斜率 / km²每十年':summary['slope_per_decade_km2']})
    return pd.DataFrame(rows)

def study_map(selected='all',key='study-map'):
    from src.map_geometry import geometry_near_longitude,near_longitude
    definitions=region_definitions();geo=region_geometry();places={p['id']:p for p in place_catalog()['places']}
    center=[72,20] if selected=='all' else definitions[selected]['center']
    m=create_local_map(center,1.5 if selected=='all' else 3)
    ids=list(definitions) if selected=='all' else [selected]
    for feature in geo['features']:
        rid=feature['properties']['id']
        if rid not in ids:continue
        if abs(center[1])>120:feature=geometry_near_longitude(feature,center[1])
        color=COLORS[rid]
        folium.GeoJson(feature,name=definitions[rid]['name'],style_function=lambda f,c=color:dict(fillColor=c,color=c,weight=1,fillOpacity=.25),tooltip=folium.GeoJsonTooltip(fields=['name'],aliases=['NSIDC 统计海区'])).add_to(m)
        folium.Marker(definitions[rid]['center'],icon=folium.DivIcon(html=f'<div style="white-space:nowrap;color:#244761;font-weight:600;background:#ffffffd9;padding:4px 7px;border-radius:4px">{definitions[rid]["name"]}</div>',icon_size=(80,24))).add_to(m)
        for pid in ASSOCIATIONS[rid]:
            if pid not in places:continue
            p=places[pid]
            longitude=near_longitude(p['longitude'],center[1]) if abs(center[1])>120 else p['longitude']
            folium.CircleMarker([p['latitude'],longitude],radius=4,color=color,fill=True,fill_opacity=1,tooltip=p['name']+' · 沿岸/服务关联地点').add_to(m)
    finish_local_map(m)
    st_folium(m,height=365,use_container_width=True,key=key+'-'+selected,returned_objects=[])
    st.caption('着色轮廓为 NSIDC 2007 版海区掩膜（25 km 网格），不是国界或航道。点为沿岸及服务关联地点，不要求位于海区内；不据此计算站点密度。')

def evidence_timeline(s,key='study'):
    start,end=s['years'];nodes=project_nodes(s['region'],start,end);policies=context_nodes(start,end);events=scoped_events(s)
    st.subheader('把项目节点和政策背景放回时间线')
    st.caption('项目按材料日期筛选；政策为全北极背景，不定位到某个港口。年度或月度节点保留原有精度。')
    table=[{'日期':n['date'],'精度':PRECISION[n['precision']],'类型':'项目','事项':n['label'],'关联':n['scope'],'原文':n['source_url']} for n in nodes]
    table += [{'日期':n['date'],'精度':PRECISION[n['precision']],'类型':'政策','事项':n['label'],'关联':'全北极历史背景','原文':n['source_url']} for n in policies]
    names={'pan_arctic':'全北极背景',**{k:v['name'] for k,v in region_definitions().items()}}
    table += [{'日期':n['date'],'精度':'日','类型':'核验事件','事项':n['claim'],'关联':names[n['region_id']],'原文':n['evidence_urls'][0]} for n in events]
    if table:
        source_table(pd.DataFrame(table).sort_values('日期'),key=key+'-timeline')
    else:st.info('这个时窗内尚无已整理的相关节点；不代表没有活动。')
    if not events:st.caption('当前范围尚无完成原文核验并归并的 GDELT 现实事件。待核验候选保留在“事件线索”，不混入这张时间线。')
    for pid in dict.fromkeys(n['project_id'] for n in nodes):
        n=next(x for x in nodes if x['project_id']==pid)
        if st.button('阅读项目 · '+n['project'],key=key+'-project-'+pid):open_project(pid)
    with st.expander('政策原文的具体含义'):
        for i,n in enumerate(policies):
            st.write(f"**{n['date']} · {n['label']}**\n\n{n['description']}")
            source_button(n['source_url'],'阅读政策导读',key=key+'-policy-'+str(i))
    if s['region']!='all':
        from src.research_catalog import research_catalog
        from src.study_data import PROJECT_REGIONS
        background=[p for p in research_catalog()['projects'] if s['region'] in PROJECT_REGIONS.get(p['id'],[]) and p['id'] not in {n['project_id'] for n in nodes}]
        if background:
            with st.expander('其他关联项目与时窗之前的背景'):
                st.caption('以下项目没有已整理且落在当前时窗内的节点；不会计入当前窗口的项目节点数。')
                for p in background:
                    if st.button(p['title'],key=key+'-background-'+p['id']):open_project(p['id'])

def export_bundle(s,metric):
    data=regional_data();frame=ice_frame();start,end=s['years']
    selected=frame[frame.year.between(start,end)&(frame.month==s['month'])]
    if s['region']!='all':selected=selected[selected.region_id==s['region']]
    manifest={'scope':s,'metric':metric,'unit':'km²','data_version':data['version'],'baseline':[1991,2020],
        'sources':data['sources'],'methods':data['methods'],'selection':'固定海区、月份与年份；最低年份为观测最小值，保留并列。',
        'limits':['描述性比较，不构成因果识别或航行建议。','日档采集覆盖不是事件发生覆盖。','项目、专利为核验样本，未形成完整年度活动计数。']}
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as bundle:
        def write(name,data):
            # Identical inputs must keep the same bytes/media URL across widget reruns.
            # Source/review dates remain in the manifest; ZIP wall-clock time is irrelevant.
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(entry,data)
        write('observations.csv',selected.to_csv(index=False).encode('utf-8-sig'))
        write('summary.csv',comparison_rows(s,metric).to_csv(index=False).encode('utf-8-sig'))
        write('coverage.csv',coverage_table(start,end).to_csv(index=False).encode('utf-8-sig'))
        write('project_nodes.json',json.dumps(project_nodes(s['region'],start,end),ensure_ascii=False,indent=2))
        write('policy_nodes.json',json.dumps(context_nodes(start,end),ensure_ascii=False,indent=2))
        write('reviewed_events.json',json.dumps(scoped_events(s),ensure_ascii=False,indent=2))
        write('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        write('regions.geojson',json.dumps(region_geometry(),ensure_ascii=False))
    return memory.getvalue()

def persisted_study_export(s,metric):
    """Keep public evidence packages on disk so UI reruns cannot expire their URLs.

    Only this curated, already downloadable dataset uses the public static path.
    Uploaded/private research tables must continue to use session downloads.
    """
    import hashlib,os,tempfile
    payload=export_bundle(s,metric)
    filename='study-'+hashlib.sha256(payload).hexdigest()+'.zip'
    folder=ROOT/'static/exports';folder.mkdir(exist_ok=True)
    target=folder/filename
    if not target.exists():
        with tempfile.NamedTemporaryFile(dir=folder,suffix='.tmp',delete=False) as temporary:
            temporary.write(payload);pending=temporary.name
        try:os.replace(pending,target)
        finally:
            if os.path.exists(pending):os.unlink(pending)
    return 'app/static/exports/'+filename

def render_coverage(s,key='coverage'):
    start,end=s['years'];coverage=coverage_table(start,end)
    if s['region']!='all':coverage=coverage[coverage['海区']==region_definitions()[s['region']]['name']]
    pivot=coverage.pivot(index='海区',columns='年份',values='海冰有效月份')
    fig=go.Figure(go.Heatmap(x=[str(x) for x in pivot.columns],y=pivot.index,z=pivot.values,zmin=0,zmax=12,
        colorscale=[[0,'#eef3f7'],[1,'#427da9']],colorbar=dict(title='有效月份'),text=pivot.values,texttemplate='%{text}/12',hovertemplate='%{y} · %{x}<br>%{z} 个有效月份<extra></extra>'))
    fig.update_layout(height=230,margin=dict(l=75,r=20,t=15,b=35),xaxis_title='年份')
    show_chart(fig,key=key+'-ice')
    st.dataframe(coverage,hide_index=True,width='stretch')
    p=collection_progress()
    st.caption(f'历史 GDELT 共采集 {p["files"]} 个日档。表中日档覆盖是全北极检索的共享采集窗口，不是各海区事件覆盖。专利仍是检索样本。')
    st.info('未采集、缺失、尚未核验分别记录。海冰有十年观测，不表示事件和专利也有同等完整的十年序列。2026 年单独作为未结束的观测年。')
    with st.expander('进入定量关联分析之前，需要满足什么'):
        st.write('先形成相同海区、相同时间尺度的完整记录，定义活动分母，按现实事件和专利族去重，再检查缺失、共同趋势和自相关。当前项目节点不连续，事件只覆盖案例窗口，因此不输出滞后相关系数、显著性或综合风险分数。')
        st.write('即使补齐 2016—2025 年，也只有 10 个年度观测。描述性斜率可以展示，复杂因果模型仍需更长序列、对照设计及替代解释检验。')

def render_study():
    section_title('REGIONAL STUDY','区域联动','在同一海区与时间范围内，对照海冰观测、技术项目和政策材料。')
    st.caption('研究主时窗：2016—2025，共 10 个完整日历年。长期序列用于背景；2026 年观测单列，未发布月份保持空白。')
    s=controls();definitions=region_definitions();start,end=s['years'];ids=list(definitions) if s['region']=='all' else [s['region']]
    st.caption('当前比较：'+scope_label()+'。月份用于海冰同月对比，项目与政策按年份范围筛选；选择会跨页面保留。')
    st.session_state['study-metric']=indicator()
    metric=st.radio('海冰指标',['extent','area'],format_func=lambda m:'海冰范围（Extent）' if m=='extent' else '海冰面积（Area）',horizontal=True,key='study-metric',on_change=copy_indicator)
    label='海冰范围' if metric=='extent' else '海冰面积'
    compare,low,timeline,coverage=st.tabs(['海区与同月观测','低冰年份对照','项目与政策','资料覆盖与导出'])
    with compare:
        st.subheader(f'{s["month"]} 月的{label}，逐年比较')
        observation_cards(s,metric)
        display=st.radio('曲线显示',['实际观测','相对同月基准的变化'],horizontal=True,key='study-display')
        anomaly=display!='实际观测'
        fig=go.Figure()
        for rid in ids:
            summary=monthly_summary(rid,s['month'],start,end,metric);series=summary['series'];color=COLORS[rid]
            field=metric+('_anomaly_km2' if anomaly else '_km2')
            fig.add_trace(go.Scatter(x=series.year,y=series[field]/10000,name=definitions[rid]['name'],mode='lines+markers',line=dict(color=color,width=2.5),connectgaps=False,hovertemplate='%{x} 年<br>%{y:.3f} 万 km²<extra>%{fullData.name}</extra>'))
            if not anomaly and len(ids)==1 and summary['baseline_km2'] is not None:
                fig.add_hline(y=summary['baseline_km2']/10000,line_dash='dot',line_color='#a48662',annotation_text='1991—2020 同月均值')
        if anomaly:fig.add_hline(y=0,line_dash='dot',line_color='#a48662')
        fig.update_layout(height=390,xaxis=dict(title='年份',dtick=1 if end-start<=15 else 5),yaxis=dict(title=label+('距平' if anomaly else '')+' / 万 km²',rangemode='tozero'),legend=dict(orientation='h'),margin=dict(l=60,r=20,t=25,b=40))
        show_chart(fig,key='study-monthly')
        if anomaly:st.caption('距平 = 当年该月观测 − 1991—2020 年同月均值。负值表示低于基准，不表示海冰面积为负；各海区使用自己的同月基准。')
        with st.expander('查看精确数值、缺失与描述性斜率'):
            st.dataframe(comparison_rows(s,metric),hide_index=True,width='stretch',column_config={c:st.column_config.NumberColumn(c,format='%.2f') for c in ['同月均值 / km²','最低值 / km²','1991—2020 同月基准 / km²','描述性斜率 / km²每十年']})
            st.caption('表格保留 km²。斜率只描述当前窗口的线性变化，不作显著性或因果解释；更换时窗会改变结果。基准须有 30 个同月有效值。')
        if 'barents' in ids and s['month']==9:st.caption('巴伦支海 9 月海冰可能接近零，绝对量和百分比的解释容易受低值影响；可切换 3 月查看冬季条件。')
        study_map(s['region'])
        places={p['id']:p for p in place_catalog()['places']}
        linked=list(dict.fromkeys(p for rid in ids for p in ASSOCIATIONS[rid] if p in places))
        if st.session_state.get('study-place') not in linked:st.session_state['study-place']=linked[0]
        choice=st.selectbox('关联地点与实景',linked,format_func=lambda p:places[p]['name'],key='study-place')
        if st.button('在北极地图查看这个地点',key='study-open-place'):open_place(choice)
    with low:
        st.subheader('先确定规则，再识别低冰年份')
        st.write(f'在 {start}—{end} 年中，分别寻找各海区 {s["month"]} 月的最小观测值。保留全部并列年份，不按项目发生年份倒推筛选。')
        if st.session_state.get('low-region') not in ids:st.session_state['low-region']=ids[0]
        rid=st.selectbox('低冰年份分析海区',ids,format_func=lambda x:definitions[x]['name'],key='low-region')
        summary=monthly_summary(rid,s['month'],start,end,metric)
        if not summary['n']:st.info('当前范围没有可用于筛选的同月观测。')
        else:
            st.metric('当前窗口的最低值年份','、'.join(map(str,summary['low_years'])))
            df=ice_frame();region=df[df.region_id==rid];fig=go.Figure()
            baseline=region.groupby('month')[metric+'_baseline_km2'].first().reindex(range(1,13))
            fig.add_trace(go.Scatter(x=list(range(1,13)),y=baseline/10000,name='1991—2020 逐月均值',mode='lines',line=dict(color='#a48662',dash='dot'),connectgaps=False))
            for year in summary['low_years']:
                values=region[region.year==year].set_index('month').reindex(range(1,13))
                fig.add_trace(go.Scatter(x=list(range(1,13)),y=values[metric+'_km2']/10000,name=str(year),mode='lines+markers',connectgaps=False))
            fig.add_vline(x=s['month'],line_width=1,line_dash='dot',line_color='#afbfcc')
            fig.update_layout(height=360,xaxis=dict(title='月份',dtick=1),yaxis=dict(title=label+' / 万 km²',rangemode='tozero'),legend=dict(orientation='h'),margin=dict(t=25,b=40,l=60,r=20))
            show_chart(fig,key='study-low-year')
            st.caption('整年曲线用于观察季节背景，筛选只使用上方指定月份；缺失或尚未发布的月份断开显示。')
            nodes=[n for n in project_nodes(rid,start,end) if int(n['date'][:4]) in summary['low_years']]
            if nodes:source_table(pd.DataFrame(nodes)[['date','project','label','scope','source_url']].rename(columns={'date':'日期','project':'项目','label':'节点','scope':'关联口径','source_url':'原文'}),key='low-year-sources')
            else:st.info('这些年份尚无已整理的相关项目节点；这不是“没有项目”的结论。')
            st.caption('同年出现仅表示时间上的并置。要解释机制，还需要实际航迹、冰级、投资或科研计划等材料。')
    with timeline:evidence_timeline(s)
    with coverage:
        render_coverage(s)
        url=persisted_study_export(s,metric)
        st.html(f'<a class="local-download" href="{url}" download="arctic-study-evidence.zip">下载当前研究范围的复核包 · ZIP</a>')
        st.caption('包含原始精度的观测、汇总、覆盖表、项目与政策节点、海区轮廓及方法和来源清单。')
        for i,source in enumerate(regional_data()['sources']):source_button(source['url'],source['title'],key='study-raw-'+str(i))
        st.caption(regional_data()['methods']['credit'])
