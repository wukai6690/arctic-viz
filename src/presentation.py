"""Shared presentation for the original Streamlit research modules."""
from pathlib import Path
import re
from urllib.parse import quote
import streamlit as st
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ('研究总览','app.py'),('北极地图','pages/1_北极全景地图.py'),
    ('海冰与航线','pages/17_海冰与航线.py'),
    ('动态关系网络','pages/14_动态关系网络.py'),('事件检索','pages/15_事件检索.py'),('专利数据库','pages/16_patents.py'),
    ('数据与方法','pages/6_数据中心工具.py'),
]
NOTES = {
    'map':'实景照片附原始来源；原版科考站、航道与关系网络作为研究线索保留，位置和关系仍需逐项核验。统计与热力演示使用原版示例数据。',
    'climate':'“真实海冰观测”来自 NSIDC 官方文件。其余原版分析工具保留为示例，情景曲线、气温、冻土与通航指数尚未接入正式研究资料。',
    'geopolitics':'原版国家关系、事件汇总与政策词频为示例资料，用于展示分析方法。关系连线不代表已经证实的合作或冲突强度。',
    'technology':'专利记录来自公开官方页面的可复核样本，支持按国家、技术类别与优先权年份筛选；样本不代表全球专利总量，也不直接等同于国家技术实力。',
    'risk':'风险等级、趋势与策略情景沿用原版示例设定，用于讨论研究框架，不构成已经完成的风险测算。',
    'data':'真实观测、候选事件和原版示例分别下载；上传数据只在当前会话中使用。',
}

def apply_presentation(page='home'):
    base_css = (ROOT/'src'/'research.css').read_text(encoding='utf-8')
    arctic_css = (ROOT/'src'/'arctic_v2.css').read_text(encoding='utf-8')
    premium_css = (ROOT/'src'/'arctic_v3.css').read_text(encoding='utf-8')
    st.markdown('<style>'+base_css+arctic_css+premium_css+'</style>',unsafe_allow_html=True)
    st.markdown(f'<div class="arctic-page arctic-page-{quote(str(page))}"></div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="research-brand"><span class="brand-mark">◉</span><div><b>北极观察</b><small>ARCTIC RESEARCH · VISUAL EVIDENCE</small></div></div>',unsafe_allow_html=True)
        st.markdown('<div class="sidebar-context">地理大创 · 北极地缘与技术双向互动研究</div>',unsafe_allow_html=True)
        for label,path in PAGES:
            page_link(path,label=label,use_container_width=True)
        from src.study_scope import sidebar_scope
        sidebar_scope()
        st.markdown('<div class="sidebar-foot">地点 · 项目 · 证据<br>每一条研究联系，都可以回到来源。</div>',unsafe_allow_html=True)
    if page in NOTES:
        st.markdown(f'<div class="data-note"><b>资料说明</b><span>{NOTES[page]}</span></div>',unsafe_allow_html=True)

def page_link(path, label, **kwargs):
    """Render a page link, with a URL fallback for cloud page-registry lag."""
    try:
        return st.page_link(path, label=label, **kwargs)
    except Exception as exc:
        # Streamlit Cloud can briefly expose a new page through its URL before
        # its page registry accepts the relative filesystem path. Keep the
        # navigation usable during that window.
        if str(path).endswith('pages/16_patents.py'):
            href = 'patents'
        else:
            stem = Path(str(path)).stem
            href = quote(re.sub(r'^\d+_', '', stem))
        st.markdown(f'<a class="fallback-page-link" href="/{href}">{label}</a>', unsafe_allow_html=True)
        return None

def light_figure(figure):
    fig=go.Figure(figure)
    fig.update_layout(template='plotly_white',paper_bgcolor='#ffffff',plot_bgcolor='#ffffff',
        font=dict(family='Arial, Microsoft YaHei, sans-serif',color='#163a5d',size=12),
        hoverlabel=dict(bgcolor='#ffffff',font_color='#163a5d',bordercolor='#cfe1ed'),
        legend=dict(bgcolor='rgba(255,255,255,0)',font=dict(color='#55718a',size=11)),
        title_font=dict(color='#163a5d',size=16))
    fig.update_xaxes(gridcolor='#e1edf5',zerolinecolor='#cfe1ed',tickfont_color='#6b879e',title_font_color='#55718a',linecolor='#d8e8f3')
    fig.update_yaxes(gridcolor='#e1edf5',zerolinecolor='#cfe1ed',tickfont_color='#6b879e',title_font_color='#55718a',linecolor='#d8e8f3')
    fig.update_geos(bgcolor='#eef6fc',landcolor='#f8fcff',oceancolor='#dceef8',lakecolor='#dceef8',countrycolor='#bcd7e7',coastlinecolor='#9ec8df')
    fig.update_polars(bgcolor='#ffffff',radialaxis=dict(gridcolor='#e1edf5',linecolor='#cfe1ed',tickfont_color='#6b879e'),angularaxis=dict(gridcolor='#e1edf5',linecolor='#cfe1ed',tickfont_color='#55718a'))
    for trace in fig.data:
        if hasattr(trace,'textfont') and trace.type!='heatmap':trace.textfont.color='#163a5d'
        if hasattr(trace,'line') and trace.line.color in ['white','#fff','#ffffff']:
            trace.line.color='#9ec8df'
    for annotation in fig.layout.annotations:
        if annotation.font.color in ['white','#fff','#ffffff'] or '255,255,255' in str(annotation.font.color):annotation.font.color='#2a668e'
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
