"""
北极地缘与技术多要素联动3D可视化平台
主入口文件 — 深色沉浸主题 v6.0
"""

import streamlit as st
import sys, os, json

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="北极战略可视化平台",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "北极地缘与技术多要素联动3D可视化平台 v6.0"}
)

# 全局深色主题 CSS
st.markdown("""
<style>
    /* === 全局深色背景 === */
    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-card: #1a2236;
        --bg-card-hover: #1f2a42;
        --border: rgba(255,255,255,0.07);
        --text-primary: rgba(255,255,255,0.92);
        --text-secondary: rgba(255,255,255,0.6);
        --text-muted: rgba(255,255,255,0.35);
        --accent-blue: #3b82f6;
        --accent-red: #ef4444;
        --accent-orange: #f97316;
        --accent-green: #22c55e;
        --accent-purple: #a855f7;
    }

    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] { background: #0a0e1a !important; }
    section[data-testid="stMain"] > div { background: transparent !important; }
    [data-testid="stMainBlockContainer"] { background: transparent !important; padding-top: 0 !important; }

    /* === 侧边栏 === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a 0%, #111827 50%, #1a2236 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
        color: white !important;
    }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }

    /* 侧边栏 Logo */
    .sidebar-logo { text-align: center; padding: 1.5rem 0.5rem 1rem 0; }
    .sidebar-logo .logo-icon { font-size: 3rem; display: block; margin-bottom: 0.4rem; }
    .sidebar-logo h2 { font-size: 1.1rem !important; font-weight: 700 !important; color: white !important; margin: 0; line-height: 1.3; }
    .sidebar-logo p { font-size: 0.7rem !important; color: rgba(255,255,255,0.5) !important; margin: 0.2rem 0 0 0; }

    /* 导航链接 */
    .nav-item {
        display: flex; align-items: center; gap: 10px;
        padding: 0.7rem 1rem; border-radius: 10px;
        margin: 3px 0; text-decoration: none; font-size: 0.88rem;
        font-weight: 500; color: rgba(255,255,255,0.7) !important;
        transition: all 0.2s ease; border: 1px solid transparent;
    }
    .nav-item:hover {
        background: rgba(59,130,246,0.15) !important;
        color: #60a5fa !important;
        transform: translateX(3px);
        border-color: rgba(59,130,246,0.3);
    }
    .nav-icon { font-size: 1.15rem; width: 28px; text-align: center; flex-shrink: 0; }
    .nav-label { flex: 1; }
    .nav-divider { border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 0.6rem 0; }

    /* === 全局文字颜色 === */
    section[data-testid="stMain"] p, section[data-testid="stMain"] span,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li, section[data-testid="stMain"] td,
    section[data-testid="stMain"] th { color: var(--text-primary) !important; }
    .stMarkdown p, .stMarkdown li,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--text-primary) !important; }

    /* === 通用深色卡片 === */
    .dark-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        transition: all 0.2s;
    }
    .dark-card:hover { background: var(--bg-card-hover); }

    /* === Hero Banner === */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c2340 100%);
        border-radius: 20px;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        margin-bottom: 1.5rem;
        position: relative; overflow: hidden;
        border: 1px solid rgba(59,130,246,0.15);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 60px rgba(59,130,246,0.05);
    }
    .hero-banner::before {
        content: ''; position: absolute;
        top: -30%; right: -5%; width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-banner::after {
        content: ''; position: absolute;
        bottom: -20%; left: -5%; width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 1.9rem !important; font-weight: 800 !important;
        color: white !important; margin: 0 0 0.5rem 0 !important;
        position: relative; z-index: 1; line-height: 1.3;
    }
    .hero-sub {
        color: rgba(255,255,255,0.55) !important;
        font-size: 0.88rem !important; margin: 0 !important;
        position: relative; z-index: 1;
    }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.25);
        border-radius: 20px; padding: 4px 12px; font-size: 0.7rem;
        color: rgba(147,197,253,0.9); font-weight: 600;
        position: relative; z-index: 1; margin-bottom: 0.8rem;
    }

    /* === KPI 指标卡 === */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px; margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: var(--bg-card);
        border-radius: 14px; padding: 1.1rem 1rem;
        border: 1px solid var(--border);
        transition: all 0.25s; position: relative; overflow: hidden;
    }
    .kpi-card::before {
        content: ''; position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
    }
    .kpi-card.blue::before { background: #3b82f6; }
    .kpi-card.red::before { background: #ef4444; }
    .kpi-card.orange::before { background: #f97316; }
    .kpi-card.purple::before { background: #a855f7; }
    .kpi-card.green::before { background: #22c55e; }
    .kpi-card:hover {
        background: var(--bg-card-hover);
        border-color: rgba(255,255,255,0.12);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .kpi-label {
        font-size: 0.7rem; color: var(--text-muted);
        font-weight: 600; margin-bottom: 0.5rem;
        display: flex; align-items: center; gap: 5px;
    }
    .kpi-value {
        font-size: 1.55rem; font-weight: 800; line-height: 1;
    }
    .kpi-value.blue { color: #60a5fa; }
    .kpi-value.red { color: #f87171; }
    .kpi-value.orange { color: #fb923c; }
    .kpi-value.purple { color: #c084fc; }
    .kpi-value.green { color: #4ade80; }

    /* === 功能模块网格 === */
    .section-title {
        font-size: 1rem; font-weight: 700; color: var(--text-primary);
        margin: 0 0 1rem 0; display: flex; align-items: center; gap: 8px;
    }
    .module-grid {
        display: grid; grid-template-columns: repeat(2, 1fr);
        gap: 16px; margin-bottom: 1.5rem;
    }
    .module-card {
        background: var(--bg-card); border-radius: 16px;
        padding: 1.5rem; border: 1px solid var(--border);
        border-top: 3px solid #3b82f6;
        transition: all 0.25s ease; cursor: pointer;
        display: flex; flex-direction: column; gap: 0.7rem;
        text-decoration: none; color: inherit !important;
        min-height: 165px;
    }
    .module-card:hover {
        background: var(--bg-card-hover);
        border-color: rgba(59,130,246,0.4);
        transform: translateY(-3px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.35);
    }
    .module-card.map-card { border-top-color: #f97316; }
    .module-icon { font-size: 2.2rem; line-height: 1; }
    .module-title { font-weight: 700; font-size: 1rem; color: #93c5fd; margin: 0; }
    .module-desc { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.7; margin: 0; flex: 1; }
    .module-tag {
        display: inline-flex; align-items: center; gap: 4px;
        background: rgba(59,130,246,0.1); color: #93c5fd;
        border-radius: 20px; padding: 0.2rem 0.7rem;
        font-size: 0.68rem; font-weight: 600; width: fit-content; margin-top: auto;
    }

    /* === 框架说明卡片 === */
    .framework-box {
        background: rgba(59,130,246,0.06);
        border-radius: 14px; padding: 1.2rem;
        border-left: 4px solid #3b82f6;
    }
    .framework-box h4 {
        font-size: 0.95rem; font-weight: 700; color: #93c5fd; margin: 0 0 0.6rem 0;
    }
    .framework-box p {
        font-size: 0.8rem !important; color: var(--text-secondary) !important;
        line-height: 1.7 !important; margin: 0 0 0.5rem 0 !important;
    }
    .framework-box strong { color: #93c5fd !important; }

    /* === 底部信息栏 === */
    .footer-bar {
        background: var(--bg-card); border-radius: 12px;
        padding: 1rem 1.5rem; text-align: center;
        color: var(--text-muted); font-size: 0.75rem;
        line-height: 1.6; border: 1px solid var(--border);
    }

    /* === Streamlit 组件覆盖 === */
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important; padding: 8px 18px !important;
        font-weight: 600 !important; font-size: 0.85rem !important;
        color: var(--text-secondary) !important; background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.06) !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(59,130,246,0.2) !important; color: #93c5fd !important;
    }
    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid var(--border) !important;
    }
    hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.2rem 0 !important; }
    .streamlit-expander {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    .streamlit-expander summary { color: var(--text-primary) !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.8rem !important; }
    [data-testid="stCaption"] { color: var(--text-muted) !important; }
    [data-testid="stAlert"] { border-radius: 12px !important; }
    .stCheckbox label { color: var(--text-secondary) !important; }
    [data-baseweb="select"] { color: var(--text-primary) !important; }
    [data-testid="stSlider"] label { color: var(--text-secondary) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: var(--text-primary) !important; }
    .stMultiSelect [data-baseweb="select"] > div { color: var(--text-primary) !important; }
    .stNumberInput label { color: var(--text-secondary) !important; }
    .stNumberInput input { color: var(--text-primary) !important; }
</style>
""", unsafe_allow_html=True)


# ============ 数据加载 ============
try:
    from src.data_core import (
        load_ice_data, load_gdelt_data, compute_trend,
        load_cmip6_forecast, load_risk_data, get_swot_data,
        load_patent_data, load_policy_texts, load_geopolitics_network,
        load_stations, get_seasonal_stats
    )
    from src.viz import (
        ARCTIC_THEME, COUNTRY_NAMES, COUNTRY_COLORS,
        CATEGORY_COLORS, CAT_LABELS, create_3d_globe,
        create_metric_trend_chart, create_forecast_chart,
        create_risk_matrix, create_swot_chart, create_network_graph,
        create_word_freq_chart, create_patent_bubble, create_radar_chart,
        create_3d_globe_annotate, create_sentiment_chart
    )
    DATA_OK = True
except ImportError:
    DATA_OK = False


# ============ 侧边栏 ============
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span class="logo-icon">🌍</span>
            <h2>北极战略平台</h2>
            <p>大创专项 · v6.0</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        nav_items = [
            ("🏠", "首页概览", "app"),
            ("🗺️", "北极全景地图", "1_北极全景地图"),
            ("🌡️", "气候时空监测", "2_气候时空监测"),
            ("🏛️", "地缘战略格局", "3_地缘战略格局"),
            ("⚙️", "技术竞争与合作", "4_极地核心技术"),
            ("🛡️", "安全风险评估", "5_中国安全风险"),
            ("🗄️", "数据中心工具", "6_数据中心工具"),
            ("ℹ️", "关于本项目", "7_关于本项目"),
        ]

        for icon, label, page in nav_items:
            st.markdown(
                f'<a class="nav-item" href="./?page={page}">'
                f'<span class="nav-icon">{icon}</span>'
                f'<span class="nav-label">{label}</span>'
                f'</a>',
                unsafe_allow_html=True
            )

        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        st.markdown("""
        <div style="padding: 0 0.2rem;">
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);font-weight:600;margin-bottom:0.4rem;">📊 项目信息</div>
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);line-height:1.9;">
        课题：北极地缘与技术双向互动<br>
        框架：Python + Streamlit<br>
        数据：GDELT / NSIDC / 专利
        </div>
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.4);font-weight:600;margin:0.8rem 0 0.4rem 0;">🔑 核心研究</div>
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);line-height:1.7;">
        技术进步赋能地缘权力延伸<br>
        中国北极安全应对策略
        </div>
        <div style="margin-top:1rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.07);">
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.3);">© 2025-2026 大创专项</div>
        </div>
        </div>
        """)


render_sidebar()


# ============ Hero Banner ============
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">🌍 北极地缘与技术多要素联动3D可视化平台</div>
    <h1 class="hero-title">基于「大北极」格局下地缘与技术双向互动机制研究</h1>
    <p class="hero-sub">大学生创新创业训练计划专项 · Python + Streamlit + Plotly · 集成 GDELT / NSIDC / 专利多源数据</p>
</div>
""", unsafe_allow_html=True)


# ============ KPI 指标 ============
kpi_data = [
    ("+3.7°C", "北极近十年升温速率", "⚠️", "red"),
    ("-13.2%", "海冰面积累计下降", "📉", "blue"),
    ("+45天", "航道通航窗口延长", "📈", "orange"),
    ("11", "覆盖国家/地区", "🌐", "purple"),
    ("6", "平台核心模块", "🔧", "green"),
]

kpi_html = '<div class="kpi-grid">'
for value, label, icon, color in kpi_data:
    kpi_html += f'''
    <div class="kpi-card {color}">
        <div class="kpi-label">{icon} {label}</div>
        <div class="kpi-value {color}">{value}</div>
    </div>'''
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 功能模块 ============
st.markdown('<div class="section-title">🎯 功能模块</div>', unsafe_allow_html=True)

modules = [
    ("🗺️", "北极全景地图", "融合Plotly 3D地球仪 + Folium交互地图 + GDELT热力叠加，点击标记查看科考站/航道详情，支持多底图切换", "地图模块", "1_北极全景地图", True),
    ("🌡️", "气候时空监测", "1980-2025年气温/海冰时空演变，CMIP6情景预测，航道通航评估，M-K突变检验", "气候监测", "2_气候时空监测", False),
    ("🏛️", "地缘战略格局", "大国博弈网络图谱、政策文本词云与情感分析、科考站详情、GDELT事件统计", "地缘格局", "3_地缘战略格局", False),
    ("⚙️", "技术竞争与合作", "专利气泡图、热力图、技术合作网络、五国竞争力雷达图、「技术-地缘」双轴联动看板", "技术竞争", "4_极地核心技术", False),
    ("🛡️", "安全风险评估", "四维风险热力图、SWOT可视化、中国应对策略推演沙盘（5种情景）", "安全风险", "5_中国安全风险", False),
    ("🗄️", "数据中心工具", "数据集下载（CSV/GeoJSON）、CSV上传可视化（5种图表）、时空查询、多指标归一化对比分析", "数据中心", "6_数据中心工具", False),
    ("ℹ️", "关于本项目", "项目介绍、研究框架、技术架构、团队信息、项目大事记", "关于项目", "7_关于本项目", False),
]

module_html = '<div class="module-grid">'
for icon, title, desc, tag, page, is_map in modules:
    card_style = 'border-top:3px solid #f97316;' if is_map else ''
    tag_text = f'⭐ {tag} · 点击进入' if is_map else tag
    module_html += f'''
    <a class="module-card{" map-card" if is_map else ""}" href="./{page}" style="{card_style}">
        <div class="module-icon">{icon}</div>
        <div class="module-title">{title}</div>
        <div class="module-desc">{desc}</div>
        <div class="module-tag">{tag_text}</div>
    </a>'''
module_html += '</div>'
st.markdown(module_html, unsafe_allow_html=True)


# ============ 核心研究框架 ============
st.markdown('<div class="section-title">📐 核心研究框架</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    with st.container():
        if DATA_OK:
            try:
                stations_data = load_stations()
                geo_dir = os.path.join(os.path.dirname(__file__), 'geojson')
                routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
                routes_data = None
                if os.path.exists(routes_path):
                    with open(routes_path, 'r', encoding='utf-8') as f:
                        routes_data = json.load(f)

                fig_globe = create_3d_globe_annotate(
                    stations_data=stations_data,
                    routes_data=routes_data,
                    height=520
                )
                st.plotly_chart(fig_globe, use_container_width=True)
            except Exception:
                fig_globe = create_3d_globe(height=520)
                st.plotly_chart(fig_globe, use_container_width=True)
        else:
            st.info("数据模块未就绪，请确保已安装依赖并正确配置数据文件。")

with col_right:
    st.markdown("""
    <div class="framework-box">
        <h4>🔬「技术-地缘」双向互动分析框架</h4>
        <p>本平台突破传统地缘政治单向分析视角，引入「技术-地缘」互动框架：</p>
        <p><strong>路径一：技术进步 → 地缘扩展</strong><br>
        极地破冰船技术、核动力推进、极地通信卫星等突破，拓展了国家在北极的存在边界和影响范围</p>
        <p><strong>路径二：地缘需求 → 技术投入</strong><br>
        航道竞争和资源开发的战略需求，反向驱动高端船舶制造和极地基础设施投资</p>
        <p><strong>路径三：技术合作 → 信任构建</strong><br>
        在大国博弈加剧的背景下，科技合作成为维持北极对话的『压舱石』</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="dark-card" style="margin-top:1rem;">
        <div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);margin-bottom:0.6rem;">🎯 研究核心问题</div>
        <ol style="font-size:0.8rem;color:var(--text-secondary);line-height:2;margin:0;padding-left:1.2rem;">
            <li>北极海冰快速融化如何从物理层面催生新航道？</li>
            <li>大国在高端船舶与极地卫星领域博弈格局如何演变？</li>
            <li>中国如何在三条路径上构建北极战略？</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


st.divider()


# ============ 最新动态数据 ============
if DATA_OK:
    tab_latest1, tab_latest2, tab_latest3 = st.tabs(["📈 海冰趋势", "🌐 地缘事件", "⚙️ 技术专利"])

    with tab_latest1:
        try:
            _, df_summary, _ = load_ice_data()
            trend = compute_trend(df_summary)
            recent = df_summary.tail(10)['mean'].tolist()
            fig_trend = create_metric_trend_chart(recent, color="#3b82f6", height=100)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.caption(f"近10年海冰面积均值趋势 | 每十年下降 {trend['decline_per_decade']:.2f} M km² | R²={trend['r_squared']:.3f}")
        except Exception:
            st.info("海冰数据加载中...")

    with tab_latest2:
        try:
            _, yc_df = load_gdelt_data()
            if not yc_df.empty:
                yearly = yc_df.groupby('year')['EventCount'].sum()
                recent_events = yearly.tail(7).tolist()
                fig_evt = create_metric_trend_chart(recent_events, color="#ef4444", height=100)
                st.plotly_chart(fig_evt, use_container_width=True)
                st.caption(f"GDELT北极地缘事件年度趋势 | 2024年共计 {yearly.get(2024, 0):,} 起")
        except Exception:
            st.info("GDELT数据加载中...")

    with tab_latest3:
        try:
            patent_df = load_patent_data()
            recent_pat = patent_df.groupby('year')['patent_count'].sum().tail(10).tolist()
            fig_pat = create_metric_trend_chart(recent_pat, color="#a855f7", height=100)
            st.plotly_chart(fig_pat, use_container_width=True)
            total = patent_df['patent_count'].sum()
            st.caption(f"极地技术专利年度趋势 | 累计 {total:,} 项专利申请")
        except Exception:
            st.info("专利数据加载中...")


st.divider()


# ============ 底部信息 ============
st.markdown("""
<div class="footer-bar">
    数据来源: GDELT 全球事件数据库 · NSIDC 海冰监测 · 专利数据库 · 各国北极政策文件<br>
    技术栈: Python + Streamlit + Plotly · 部署: Streamlit Community Cloud<br>
    © 2025-2026 北极地缘与技术双向互动机制研究 · 大创专项
</div>
""", unsafe_allow_html=True)
