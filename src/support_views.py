"""Observed climate and transparent source/download tools."""
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.source_library import source_table
from src.presentation import section_title,show_chart,ROOT
from src.evidence_views import reference_data,place_catalog,render_observations,render_candidate_events,render_verified_downloads
from src.research_catalog import research_catalog,project_media

def render_climate():
    section_title('CLIMATE OBSERVATIONS','海冰观测','用同一口径观察长期趋势和季节变化，为项目研究提供环境背景。')
    st.page_link('pages/8_区域联动研究.py',label='查看巴伦支海、喀拉海与楚科奇海的区域观测 ↗')
    obs,season,heat=st.tabs(['长期变化','季节对比','逐月分布'])
    with obs:render_observations()
    df=pd.DataFrame(reference_data()['sea_ice'])
    with season:
        st.subheader('不同年份的海冰季节周期')
        available=sorted(df.year.unique().tolist())
        chosen=st.multiselect('对比年份',available,default=available[-3:],max_selections=5,key='season_years')
        fig=go.Figure()
        palette=['#427da9','#ac775f','#879b6e','#8d7ba2','#b39859']
        for n,year in enumerate(chosen):
            values=df[df.year==year].set_index('month').reindex(range(1,13))
            fig.add_trace(go.Scatter(x=list(range(1,13)),y=values.extent,name=str(year),mode='lines+markers',line=dict(color=palette[n]),connectgaps=False))
        if chosen:
            fig.update_layout(height=430,xaxis=dict(title='月份',dtick=1),yaxis=dict(title='海冰范围 / 百万 km²',rangemode='tozero'),legend=dict(orientation='h'),margin=dict(t=30,l=50,r=20,b=45))
            show_chart(fig,key='season-real')
        else:st.info('请选择至少一个年份。')
        st.caption('未发布或缺失的月份留空；使用 NSIDC 月度观测，不推算剩余月份。')
    with heat:
        st.subheader('每一个月，放回观测序列')
        pivot=df.pivot(index='year',columns='month',values='extent').reindex(columns=range(1,13))
        fig=go.Figure(go.Heatmap(x=list(range(1,13)),y=pivot.index,z=pivot.values,colorscale=[[0,'#f0f7fc'],[.5,'#9bbfdc'],[1,'#356a94']],colorbar=dict(title='百万 km²'),hoverongaps=False,hovertemplate='%{y} 年 %{x} 月<br>%{z:.2f} 百万 km²<extra></extra>'))
        fig.update_layout(height=660,xaxis=dict(title='月份',dtick=1),yaxis_title='年份',margin=dict(l=60,r=30,t=15,b=45))
        show_chart(fig,key='monthly-real')
        st.caption('同一颜色标尺覆盖全部年份；空白表示缺失观测。')
    st.info('这些观测说明北极海冰总体变化。具体航道通航条件还需要区域冰情、船舶等级和航行资料。')

def render_events():
    section_title('EVENT SOURCES','事件线索','机器抽取的报道提供检索入口；项目专题中的事实另外对照发布方材料核验。')
    history,snapshot=st.tabs(['历史案例窗口与核验','2026 年短时快照'])
    with history:
        from src.review_views import render_history
        render_history()
    with snapshot:
        st.caption('此处为先前采集的 GDELT 2.0 短时快照，与历史 GDELT 1.0 日档分别保留，不拼接为连续十年统计。')
        render_candidate_events()

def render_data():
    research=research_catalog();places=place_catalog();data=reference_data()
    section_title('DATA & METHODS','数据与方法','记录覆盖范围、处理口径和原始出处，让图表和研究关系可以复核。')
    a,b,c=st.columns(3)
    a.metric('地点档案',len(places['places']));b.metric('项目专题',len(research['projects']));c.metric('有来源的项目关系',sum(len(p['relationships']) for p in research['projects']))
    methods,sources,downloads,tools=st.tabs(['整理方法','来源目录','资料下载','研究工具'])
    with methods:
        from src.study_data import regional_data,collection_progress
        regional=regional_data();progress=collection_progress()
        st.markdown('#### 研究时窗与区域口径')
        st.write(f'主时窗为 2016—2025，共 10 个完整日历年；2026 年观测单独保留。新增三个海区，共 {len(regional["records"]):,} 条区域月度记录，包含缺失状态；统计表与地图使用配套的 NSIDC 海区定义。')
        st.write(f'历史 GDELT 已采集 {progress["files"]} 个日档；候选先核验原文，再按现实事件归并。专利先按最早优先权日和专利族整理。两类资料当前都不作为完整年度活动统计。')
        st.page_link('pages/8_区域联动研究.py',label='查看逐年覆盖与下载复核包 ↗')
        st.markdown('#### 地点、项目与事件分别核对')
        st.dataframe(pd.DataFrame([
            {'资料':'地点位置','处理方式':'地名和目录坐标配对，保留城市、站点或区域的定位精度','展示限制':'示意点不冒充具体事件坐标'},
            {'资料':'实景照片','处理方式':'核对文件描述、拍摄地点、作者和许可；逐张保留来源','展示限制':'历史照片保留日期，项目照片与地点照片分别标注'},
            {'资料':'项目事实与关系','处理方式':'每条事实、时间节点、关系分别记录原始来源','展示限制':'项目样本不代表北极全部活动；历史股权不代表当前股权'},
            {'资料':'GDELT 记录','处理方式':'保留来源文件和行号，排除已识别的地名歧义','展示限制':'当前仅为有限窗口的候选线索，未作为已核验事件'},
            {'资料':'NSIDC 海冰','处理方式':'保留单位、缺失值和 1991—2020 同月基准','展示限制':'不把海冰总量换算成航道通航天数'},
        ]),hide_index=True,width='stretch')
        st.markdown('#### 当前覆盖与版本')
        st.write(f'海冰：{min(e["date"] for e in data["sea_ice"])}—{max(e["date"] for e in data["sea_ice"])}，共 {len(data["sea_ice"])} 个月度记录。')
        intervals=data.get('coverage',{}).get('event_ingestion_intervals',[])
        st.write('事件来源更新窗口（UTC）：'+ '；'.join(i['start']+' — '+i['end'] for i in intervals))
        st.caption(f'观测快照 {data["version"]} ｜ 地点 {places["version"]} ｜ 专题 {research["version"]}')
        st.write('当前页面读取固定资料包。新采集内容经核验后才能进入展示；页面刷新不会自动扩展观测或新闻覆盖。')
        with st.expander('已识别的地点歧义'):
            for rule in places['excluded_matches']:st.write(rule['reason'])
    with sources:
        from src.study_data import regional_data,read_json
        st.subheader('区域观测与政策材料')
        rows=[{'标题':s['title'],'原文':s['url'],'核对/采集日期':s.get('retrieved_at',s.get('accessed_at',''))} for s in [*regional_data()['sources'],*read_json('evidence_context.json')['sources']]]
        source_table(pd.DataFrame(rows),key='data-regional')
        st.subheader('项目原始材料')
        source_table(pd.DataFrame([{'标题':s['title'],'发布机构':s['publisher'],'发布日期':s['published_at'] or '未标明','核对日期':s['accessed_at'],'原文':s['url']} for s in research['sources']]),key='data-projects')
        st.subheader('照片作者与许可')
        photos=[{'归属':p['name'],**photo} for p in places['places'] for photo in p['photos']]
        project_names={p['id']:p['title'] for p in research_catalog()['projects']}
        photos += [{'归属':project_names[pid],**photo} for pid,items in project_media().items() for photo in items]
        source_table(pd.DataFrame([{'归属':p['归属'],'图注':p['caption'],'作者':p['author'],'许可':p['license'],'日期':p['date'],'来源':p['source_url']} for p in photos]),'来源','data-photos')
    with downloads:
        from src.research_extension_data import extension_data,research_bundle
        extended=extension_data()
        rows=[{'section':k,'records':v} for k,v in extended.items() if isinstance(v,list) and k!='sources']
        rows.append({'section':'shipping','records':[extended['shipping']]})
        st.download_button('政策、机制、参与条件与文献记录 · ZIP',research_bundle('research-extension',{'scope':'完整研究扩展资料'},rows),'research-extension-evidence.zip','application/zip',key='all-extension-download',on_click='ignore')
        from src.study_data import regional_data,region_geometry
        st.download_button('三个海区的完整月度观测 · JSON',json.dumps(regional_data(),ensure_ascii=False),'regional-ice-with-provenance.json','application/json',on_click='ignore')
        st.download_button('配套统计海区边界 · GeoJSON',json.dumps(region_geometry(),ensure_ascii=False),'nsidc-research-regions.geojson','application/geo+json',on_click='ignore')
        render_verified_downloads()
        st.download_button('项目事实、关系与来源 · JSON',json.dumps(research,ensure_ascii=False,indent=2),'arctic-project-evidence.json','application/json',key='download-projects',on_click='ignore')
        rows=[{'project_id':p['id'],'project':p['title'],**e} for p in research['projects'] for e in p['relationships']]
        st.download_button('项目关系表 · CSV',pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'),'arctic-project-relations.csv','text/csv',on_click='ignore')
        geo={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[p['longitude'],p['latitude']]},'properties':{k:p[k] for k in ['id','name','english','region','reference_url','location_note']}} for p in places['places']]}
        st.download_button('地点与定位说明 · GeoJSON',json.dumps(geo,ensure_ascii=False,indent=2),'arctic-places.geojson','application/geo+json',on_click='ignore')
    with tools:
        st.subheader('上传自己的表格进行初步查看')
        st.caption('文件用于当前会话中的制图，不会自动进入正式资料库或项目结论。')
        uploaded=st.file_uploader('选择 CSV 文件',type=['csv'])
        if uploaded:
            try:
                frame=pd.read_csv(uploaded)
            except Exception:
                st.info('无法读取，请检查 CSV 编码和列格式。');return
            st.dataframe(frame.head(200),hide_index=True,width='stretch')
            numeric=frame.select_dtypes(include='number').columns.tolist()
            if numeric and len(frame.columns):
                col1,col2,col3=st.columns(3)
                x=col1.selectbox('横轴',frame.columns.tolist());y=col2.selectbox('数值列',numeric)
                kind=col3.selectbox('图表类型',['折线图','散点图','柱状图'])
                trace=go.Bar(x=frame[x],y=frame[y]) if kind=='柱状图' else go.Scatter(x=frame[x],y=frame[y],mode='lines+markers' if kind=='折线图' else 'markers',connectgaps=False)
                fig=go.Figure(trace);fig.update_layout(xaxis_title=x,yaxis_title=y,height=400)
                show_chart(fig,key='uploaded-chart')
            else:st.info('未识别到数值列，暂时只展示表格。')
        st.caption('原版模拟分析代码保存在项目 legacy_pages/20261009 中；主要展示不再混入模拟排名和风险分数。')

def render_about():
    section_title('ABOUT THE RESEARCH','关于研究','北极地缘与技术双向互动机制研究 · 大学生创新创业训练计划')
    st.write('研究围绕技术活动、地理条件和参与主体的关系展开。当前平台将地点实景、官方观测、项目材料与报道线索组织为可查看来源的研究资料。')
    st.markdown('**研究问题**：极地装备和通信能力如何形成？哪些机构、项目与地理节点参与其中？这些联系能为中国的科研、交通与国际参与提供什么值得检验的问题？')
    st.markdown('**当前进展**：已建立带照片的地点档案、七个项目专题、三个海区的官方月度观测，以及事件核验和专利族整理工具。新增政策对照、双向作用证据、技术与活动档案、中国参与条件、多方表述、时点影像和文献核对记录。主研究时窗为 2016—2025；研究解释尚未通过完整活动样本和因果分析检验。')
    st.markdown('**展示结构**：研究总览、北极地图、区域联动、技术与地缘、研究发现。数据与方法集中记录来源，海冰观测与事件线索提供进一步查询。')
    st.caption('本平台不把功能完成等同于研究结论完成。')
