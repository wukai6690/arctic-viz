"""Research overview with a calm, evidence-first Arctic dashboard."""
from html import escape

import streamlit as st

from src.evidence_views import photo_figure, place_catalog
from src.mosaic_research import load_mosaic
from src.presentation import page_link
from src.research_catalog import project_media

CASES = {
    "mosaic": ("01 / 科研协作", "MOSAiC：怎样在浮冰上持续观测？", "沿真实航迹对照同期冰情，理解船舶、设备与国际协作怎样共同支撑一次任务。"),
    "asbm": ("02 / 高纬通信", "ASBM：需求怎样进入技术设计？", "按立项、发射、交付组织证据，区分覆盖设计与实际服务表现。"),
    "yamal": ("03 / 能源运输", "亚马尔：一艘船的航行说明什么？", "追踪东向运输与港口条件，区分航行事实、净航行时间和全年通航能力。"),
}


def open_case(case):
    st.session_state["_case_pending"] = case
    st.switch_page("pages/11_案例研究.py")


def _metric_counts():
    places = len(place_catalog()["places"])
    try:
        vessel = f"{load_mosaic()['manifest']['track_rows']:,}"
    except Exception:
        vessel = "55,793"
    return [(str(places), "地点档案", "港口、社区与科研节点"), ("129", "月度海冰图", "2016—2026-09"), (vessel, "MOSAiC 船位", "真实公开记录"), ("66", "专利详情", "中文摘要与来源")]


def render_home():
    photos = project_media().get("mosaic", [])
    st.markdown('<div class="home-breadcrumb">北极观察 <span>/</span> 研究总览 <span>/</span> 地缘与技术双向互动</div>', unsafe_allow_html=True)
    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown('<div class="home-hero-copy"><div class="eyebrow">ARCTIC RESEARCH · EVIDENCE PLATFORM</div><h1>技术如何改变北极活动，<br>又如何受到地缘关系影响？</h1><p>以科考、通信、海冰与能源运输为切口，把环境观测、真实项目、专利和政策材料放到同一条可追溯证据链中。</p><div class="hero-actions"><span class="hero-chip">真实观测</span><span class="hero-chip">来源可追溯</span><span class="hero-chip">研究边界清晰</span></div></div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        with a: page_link("pages/17_海冰与航线.py", label="查看海冰与航线", use_container_width=True)
        with b: page_link("pages/11_案例研究.py", label="阅读三个案例", use_container_width=True)
    with right:
        st.markdown('<div class="hero-image-frame"><div class="hero-image-label">MOSAiC · 北极海冰观测</div></div>', unsafe_allow_html=True)
        if photos: photo_figure(photos[0])
        st.caption("从一艘科研船出发，看设备、环境和协作如何共同支撑一次任务。")

    st.markdown('<div class="home-section-rule"><span>平台资料概览</span></div>', unsafe_allow_html=True)
    for col, (value, label, note) in zip(st.columns(4, gap="medium"), _metric_counts()):
        with col: st.markdown(f'<div class="home-kpi"><b>{escape(value)}</b><span>{escape(label)}</span><small>{escape(note)}</small></div>', unsafe_allow_html=True)

    st.markdown('<div class="home-section-rule"><span>从三个入口开始研究</span></div>', unsafe_allow_html=True)
    modules = [("01", "海冰与航线", "把 129 张月度海冰影像和 MOSAiC 真实船位放在同一条时间轴上。", "pages/17_海冰与航线.py"), ("02", "案例证据", "从真实项目、设备任务和发布方材料中梳理可核验的作用链。", "pages/11_案例研究.py"), ("03", "专利与地缘", "检索 66 条详情记录，查看国家、技术方向和公开文本。", "pages/16_patents.py")]
    for col, (number, title, body, path) in zip(st.columns(3, gap="large"), modules):
        with col:
            st.markdown(f'<article class="module-card"><small>{escape(number)}</small><h3>{escape(title)}</h3><p>{escape(body)}</p></article>', unsafe_allow_html=True)
            page_link(path, label="进入模块 →", use_container_width=True)

    st.markdown('<div class="home-section-rule"><span>三个案例，三种观察角度</span></div>', unsafe_allow_html=True)
    for col, (cid, (kicker, title, desc)) in zip(st.columns(3, gap="large"), CASES.items()):
        with col:
            st.markdown(f'<article class="case-card"><small>{escape(kicker)}</small><h3>{escape(title)}</h3><p>{escape(desc)}</p></article>', unsafe_allow_html=True)
            if st.button("进入案例", key="home-case-" + cid, use_container_width=True): open_case(cid)

    st.markdown('<div class="home-section-rule"><span>目前形成的认识</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 0.75], gap="large")
    with left: st.markdown('<div class="insight-panel"><div class="eyebrow">CURRENT RESEARCH POSITION</div><h2>活动条件来自技术，也来自组织与地理。</h2><p>设备、观测和运输能力打开了新的活动空间，但活动能否持续，还取决于协作安排、服务设施、港口条件和制度环境。平台把事实、解释和仍待验证的部分分开保存。</p></div>', unsafe_allow_html=True)
    with right: st.markdown('<div class="boundary-panel"><b>资料边界</b><p>海冰影像是月均环境背景；船位是独立航次记录；GDELT 是机器候选线索。三者不会被自动合成为通航风险或外交结论。</p></div>', unsafe_allow_html=True)
    with st.expander("查看研究范围与数据口径"):
        st.write("主研究时窗为 2016—2025 年；2026 年为未结束年度。地图、项目、海冰、事件和专利分别保留来源与使用边界。")
        st.write("资料数量不替代研究结论；关键判断需要回到原始来源和项目材料。")
