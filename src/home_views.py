"""Research overview with a calm, evidence-first Arctic dashboard."""
from html import escape

import streamlit as st

from src.evidence_views import photo_figure, place_catalog, photo_path, local_image_uri
from src.mosaic_research import load_mosaic
from src.presentation import page_link
from src.research_catalog import project_media
from src.patent_views import load_patents

def _metric_counts():
    places = len(place_catalog()["places"])
    try:
        vessel = f"{load_mosaic()['manifest']['track_rows']:,}"
    except Exception:
        vessel = "55,793"
    patents = len(load_patents().get("records", []))
    return [(str(places), "地点档案", "港口、社区与科研节点"), ("129", "月度海冰图", "2016—2026-09"), (vessel, "MOSAiC 船位", "真实公开记录"), (f"{patents:,}", "专利详情", "已合并确认数据")]


def render_home():
    photos = project_media().get("mosaic", [])
    st.markdown('<div class="home-breadcrumb">北极观察 <span>/</span> 研究总览 <span>/</span> 地缘与技术双向互动</div>', unsafe_allow_html=True)
    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.markdown('<div class="home-hero-copy"><div class="eyebrow">ARCTIC RESEARCH · EVIDENCE PLATFORM</div><h1>技术如何改变北极活动，<br>又如何受到地缘关系影响？</h1><p>以科考、通信、海冰与能源运输为切口，把环境观测、真实项目、专利和政策材料放到同一条可追溯证据链中。</p><div class="hero-actions"><span class="hero-chip">真实观测</span><span class="hero-chip">来源可追溯</span><span class="hero-chip">研究边界清晰</span></div></div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        with a: page_link("pages/17_海冰与航线.py", label="查看海冰与航线", use_container_width=True)
        with b: page_link("pages/18_气候地缘技术.py", label="打开三维耦合", use_container_width=True)
        with c: page_link("pages/16_patents.py", label="进入专利数据库", use_container_width=True)
    with right:
        st.markdown('<div class="hero-image-frame"><div class="hero-image-label">MOSAiC · 北极海冰观测</div></div>', unsafe_allow_html=True)
        if photos: photo_figure(photos[0])
        st.caption("从一艘科研船出发，看设备、环境和协作如何共同支撑一次任务。")

    st.markdown('<div class="home-section-rule"><span>平台资料概览</span></div>', unsafe_allow_html=True)
    for col, (value, label, note) in zip(st.columns(4, gap="medium"), _metric_counts()):
        with col: st.markdown(f'<div class="home-kpi"><b>{escape(value)}</b><span>{escape(label)}</span><small>{escape(note)}</small></div>', unsafe_allow_html=True)

    st.markdown('<div class="home-section-rule"><span>研究总览 · 进入核心板块</span></div>', unsafe_allow_html=True)
    project_media_map = project_media()
    places = {place["id"]: place for place in place_catalog()["places"]}
    map_photo = places.get("nyalesund", {}).get("photos", [{}])[0]
    overview = [
        ("01", "北极地图", "科考站、港口、卫星设施与沿岸节点", "🇳🇴 挪威  ·  🇨🇦 加拿大  ·  🇬🇱 格陵兰", "pages/1_北极全景地图.py", map_photo),
        ("02", "海冰与航线", "月度海冰变化、MOSAiC 航迹与同期环境", "🇩🇪 德国  ·  🇳🇴 挪威  ·  北冰洋", "pages/17_海冰与航线.py", project_media_map.get("mosaic", [{}])[0]),
        ("03", "动态关系网络", "按月度样本窗口观察北极国家互动结构", "🇺🇸 美国  ·  🇨🇳 中国  ·  🇷🇺 俄罗斯", "pages/14_动态关系网络.py", project_media_map.get("asbm", [{}])[0]),
        ("04", "气候—地缘—技术", "统一时间轴上的海冰、航线、事件与专利联动", "❄️ 129 个月影像  ·  多源证据层", "pages/18_气候地缘技术.py", project_media_map.get("mosaic", [{}])[0]),
        ("05", "事件检索", "从新闻候选记录回到来源网页和事件字段", "🌐 GDELT  ·  2015—2025 样本窗口", "pages/15_事件检索.py", project_media_map.get("yamal", [{}])[0]),
        ("06", "专利数据库", "937 条确认专利的国家、技术和公开文本", "🇨🇳 中国  ·  🇺🇸 美国  ·  🇷🇺 俄罗斯", "pages/16_patents.py", project_media_map.get("chars", [{}])[0]),
    ]
    for offset in range(0, len(overview), 3):
        cols = st.columns(3, gap="large")
        for col, (number, title, body, flags, path, photo) in zip(cols, overview[offset:offset + 3]):
            with col:
                image_html = ""
                if photo and photo.get("src"):
                    image_path = photo_path(photo)
                    if image_path.exists():
                        image_html = f'<div class="overview-card-media"><img src="{local_image_uri(image_path)}" alt="{escape(title)}"></div>'
                st.markdown(f'<article class="overview-card"><div class="overview-card-tag">{escape(number)} / ARCTIC MODULE</div>{image_html}<div class="overview-card-copy"><h3>{escape(title)}</h3><p>{escape(body)}</p><small>{escape(flags)}</small></div></article>', unsafe_allow_html=True)
                page_link(path, label="进入板块 →", use_container_width=True)

    st.markdown('<div class="home-section-rule"><span>目前形成的认识</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.25, 0.75], gap="large")
    with left: st.markdown('<div class="insight-panel"><div class="eyebrow">CURRENT RESEARCH POSITION</div><h2>活动条件来自技术，也来自组织与地理。</h2><p>设备、观测和运输能力打开了新的活动空间，但活动能否持续，还取决于协作安排、服务设施、港口条件和制度环境。平台把事实、解释和仍待验证的部分分开保存。</p></div>', unsafe_allow_html=True)
    with right: st.markdown('<div class="boundary-panel"><b>资料边界</b><p>海冰影像是月均环境背景；船位是独立航次记录；GDELT 是机器候选线索。三者不会被自动合成为通航风险或外交结论。</p></div>', unsafe_allow_html=True)
    with st.expander("查看研究范围与数据口径"):
        st.write("主研究时窗为 2016—2025 年；2026 年为未结束年度。地图、项目、海冰、事件和专利分别保留来源与使用边界。")
        st.write("资料数量不替代研究结论；关键判断需要回到原始来源和项目材料。")
