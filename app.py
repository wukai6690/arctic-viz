"""Original Streamlit platform, refreshed presentation and sourced materials."""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import plotly.graph_objects as go
import pandas as pd
from src.presentation import apply_presentation, show_chart
from src.evidence_views import reference_data, place_catalog, photo_figure
from src.research_catalog import research_catalog,open_project,project_media

st.set_page_config(page_title='北极观察 · 研究总览',page_icon='◎',layout='wide',initial_sidebar_state='expanded')
apply_presentation('home')
data=reference_data()
research=research_catalog()
places=place_catalog()['places']
by_id={p['id']:p for p in places}
ice=pd.DataFrame(data['sea_ice'])
september=ice[(ice.month==9)&ice.extent.notna()].sort_values('year')
latest=september.iloc[-1]

left,right=st.columns([1,1.1],gap='large')
with left:
    st.markdown('<div class="home-intro"><div class="eyebrow">北极地缘与技术双向互动研究</div><h1>在变化的北极，<br>理解环境与人。</h1><p>从海冰、航道与聚落出发，观察国家关系和技术活动。把地图上的线索与原始资料放在一起，逐步形成有依据的研究判断。</p></div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    a.page_link('pages/1_北极全景地图.py',label='探索北极地图 ↗',use_container_width=True)
    b.page_link('pages/4_极地核心技术.py',label='阅读技术专题 ↗',use_container_width=True)
    st.markdown('<div class="home-footnote">地点、项目与证据相互连接<br>每一个判断，都能回到原始材料</div>',unsafe_allow_html=True)
with right:
    photo_figure(by_id['greenland']['photos'][0])

st.write('')
cols=st.columns(4)
cols[0].metric(f'{latest.date} 海冰范围',f'{latest.extent:.2f} 百万 km²')
cols[1].metric('实景照片',f'{sum(len(p["photos"]) for p in places)+sum(len(p) for p in project_media().values())} 张')
cols[2].metric('有来源的项目专题',f'{len(research["projects"])} 个')
cols[3].metric('有依据的项目关系',f'{sum(len(p["relationships"]) for p in research["projects"])} 条')
st.caption(f'海冰来自 NSIDC；{len(places)} 个地点包括北极相关产业城市。项目资料逐条标明机构与时点，照片保留原始来源与拍摄日期。')

st.write('')
st.subheader('从地图进入项目，从项目回到证据')
st.page_link('pages/8_区域联动研究.py',label='区域联动：用同一时窗对照海冰、项目与政策 ↗',use_container_width=True)
st.caption('三个试点海区 · 2016—2025 年研究主时窗 · 同月观测、低冰年份、逐条证据与覆盖检查。2026 年观测另作未结束年度处理。')
modules=[
    ('01','北极地图','查找港口、科研聚落与空间设施，查看实景、相关专题与来源。','pages/1_北极全景地图.py'),
    ('02','技术与地缘','围绕破冰船、卫星通信、科研设施与能源运输，查看机构分工和时间节点。','pages/4_极地核心技术.py'),
    ('03','研究发现','比较政策、追溯双向作用、检查中国参与条件，并阅读不同主体的公开表述。','pages/5_中国安全风险.py'),
    ('04','数据与方法','查看资料覆盖、核验口径和来源，下载地点、关系与观测数据。','pages/6_数据中心工具.py'),
]
for offset in range(0,4,2):
    cols=st.columns(2,gap='large')
    for col,(number,title,description,path) in zip(cols,modules[offset:offset+2]):
        with col:
            st.markdown(f'<div class="module-number">{number}</div>',unsafe_allow_html=True)
            st.page_link(path,label=title+' ↗',use_container_width=True)
            st.markdown(f'<div class="module-description">{description}</div>',unsafe_allow_html=True)
            st.divider()

chart,context=st.columns([1.7,1],gap='large')
with chart:
    st.markdown('<div class="feature-title">CLIMATE / 长期观测</div>',unsafe_allow_html=True)
    st.subheader('九月海冰，放在更长的时间里看')
    fig=go.Figure(go.Scatter(x=september.year,y=september.extent,mode='lines',line=dict(color='#427da9',width=2.5),name='9 月海冰范围',connectgaps=False))
    fig.update_layout(height=280,margin=dict(l=45,r=15,t=15,b=40),yaxis=dict(title='百万 km²',rangemode='tozero'),xaxis_title='年份',showlegend=False)
    show_chart(fig,key='home_real_ice')
    st.caption(f'NSIDC Sea Ice Index V4 · {int(september.year.min())}—{int(september.year.max())} 年 · 来源与计算方法见气候板块。')
with context:
    st.markdown('<div class="feature-title">RESEARCH / 研究问题</div>',unsafe_allow_html=True)
    st.subheader('环境、技术与地缘关系')
    st.markdown('**环境条件如何变化？**\n\n从海冰变化识别研究问题，再补充区域冰情与航行资料。\n\n**技术活动如何连接国家？**\n\n用专利、项目和政策原文核对关系，区分合作线索与已证实联系。\n\n**中国如何回应这些变化？**\n\n在具体情景中讨论通航、科研、技术与权益。')

st.divider()
st.subheader('值得先看的三个地点')
for col,key in zip(st.columns(3,gap='large'),['nyalesund','svalsat','sabetta']):
    with col:
        st.markdown('**'+by_id[key]['name']+'**')
        photo_figure(by_id[key]['photos'][0])
st.caption('每个地点至少配有五张实景照片，以及地理、历史、生活或设施介绍。地点档案与背景材料可站内阅读，也可打包下载。')
st.page_link('pages/9_实景图集.py',label='浏览实景图集：科考现场、港口与北极社区 ↗')
st.markdown('<div class="data-note"><b>研究进度</b><span>目前是有来源的项目案例集。资料支持具体事实，机制解释仍待完整样本和进一步检验；GDELT 候选记录单独保留在“事件线索”。</span></div>',unsafe_allow_html=True)
st.markdown('<div class="footer-bar">北极观察 · 地理大创研究项目<br>观察环境，追溯项目，解释关系。</div>',unsafe_allow_html=True)
