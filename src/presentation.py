"""Shared presentation for the original Streamlit research modules."""
from pathlib import Path
import re
import streamlit as st
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ('研究总览','app.py'),('研究导览','pages/13_研究导览.py'),('北极地图','pages/1_北极全景地图.py'),
    ('案例研究','pages/11_案例研究.py'),('研究发现','pages/5_中国安全风险.py'),
    ('研究过程','pages/12_研究过程.py'),('数据与方法','pages/6_数据中心工具.py'),
]
NOTES = {
    'map':'实景照片附原始来源；原版科考站、航道与关系网络作为研究线索保留，位置和关系仍需逐项核验。统计与热力演示使用原版示例数据。',
    'climate':'“真实海冰观测”来自 NSIDC 官方文件。其余原版分析工具保留为示例，情景曲线、气温、冻土与通航指数尚未接入正式研究资料。',
    'geopolitics':'原版国家关系、事件汇总与政策词频为示例资料，用于展示分析方法。关系连线不代表已经证实的合作或冲突强度。',
    'technology':'专利数量、技术关系与竞争力分数沿用原版示例。真实专利检索结果尚未接入，这些图不用于判断国家技术实力。',
    'risk':'风险等级、趋势与策略情景沿用原版示例设定，用于讨论研究框架，不构成已经完成的风险测算。',
    'data':'真实观测、候选事件和原版示例分别下载；上传数据只在当前会话中使用。',
}

def apply_presentation(page='home'):
    st.markdown('<style>'+ (ROOT/'src'/'research.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="research-brand"><span>◎</span><div>北极观察<small>ARCTIC RESEARCH</small></div></div>',unsafe_allow_html=True)
        st.caption('地理大创 · 研究工作区')
        for label,path in PAGES:
            st.page_link(path,label=label,use_container_width=True)
        with st.expander('观测与研究资料',expanded=True):
            st.page_link('pages/9_实景图集.py',label='实景图集')
            st.page_link('pages/8_区域联动研究.py',label='区域联动')
            st.page_link('pages/4_极地核心技术.py',label='技术与地缘')
            st.page_link('pages/10_站内资料.py',label='站内资料')
            st.page_link('pages/2_气候时空监测.py',label='海冰观测')
            st.page_link('pages/3_地缘战略格局.py',label='事件线索')
            st.page_link('pages/7_关于本项目.py',label='关于研究')
        from src.study_scope import sidebar_scope
        sidebar_scope()
        st.markdown('<div class="sidebar-foot">地点 · 项目 · 证据<br>每一条研究联系，都可以回到来源。</div>',unsafe_allow_html=True)
    if page in NOTES:
        st.markdown(f'<div class="data-note"><b>资料说明</b><span>{NOTES[page]}</span></div>',unsafe_allow_html=True)

def light_figure(figure):
    fig=go.Figure(figure)
    fig.update_layout(template='plotly_white',paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
        font=dict(family='Arial, Microsoft YaHei, sans-serif',color='#304d43',size=12),
        hoverlabel=dict(bgcolor='#ffffff',font_color='#304d43',bordercolor='#cad9d4'),
        legend=dict(bgcolor='rgba(255,255,255,0)',font=dict(color='#64786e',size=11)),
        title_font=dict(color='#304d43',size=16))
    fig.update_xaxes(gridcolor='#e7ece4',zerolinecolor='#cad9d4',tickfont_color='#78897d',title_font_color='#64786e',linecolor='#dbe4d9')
    fig.update_yaxes(gridcolor='#e7ece4',zerolinecolor='#cad9d4',tickfont_color='#78897d',title_font_color='#64786e',linecolor='#dbe4d9')
    fig.update_geos(bgcolor='#f5f7f3',landcolor='#f7f7ef',oceancolor='#dfe9e9',lakecolor='#dfe9e9',countrycolor='#cad5c8',coastlinecolor='#b3c4b8')
    fig.update_polars(bgcolor='#ffffff',radialaxis=dict(gridcolor='#e2e9de',linecolor='#cad9d4',tickfont_color='#78897d'),angularaxis=dict(gridcolor='#e2e9de',linecolor='#cad9d4',tickfont_color='#64786e'))
    for trace in fig.data:
        if hasattr(trace,'textfont') and trace.type!='heatmap':trace.textfont.color='#304d43'
        if hasattr(trace,'line') and trace.line.color in ['white','#fff','#ffffff']:
            trace.line.color='#b3c4b8'
    for annotation in fig.layout.annotations:
        if annotation.font.color in ['white','#fff','#ffffff'] or '255,255,255' in str(annotation.font.color):annotation.font.color='#426886'
    return fig

def show_chart(figure,**kwargs):
    # Keep the cloud app's /~/+/ mount prefix when resolving local resources.
    config={'displaylogo':False,'scrollZoom':False,'topojsonURL':'app/static/maps/','toImageButtonOptions':{'format':'png','scale':2}}
    config.update(kwargs.pop('config',{}) or {})
    kwargs.pop('use_container_width',None)
    kwargs.setdefault('width','stretch')
    kwargs.setdefault('theme',None)
    return st.plotly_chart(light_figure(figure),config=config,**kwargs)

def section_title(kicker,title,description=''):
    from html import escape
    st.markdown(f'<div class="editorial-heading"><small>{escape(kicker)}</small><h1>{escape(title)}</h1><p>{escape(description)}</p></div>',unsafe_allow_html=True)
