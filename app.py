"""
北极地缘与技术多要素联动3D可视化平台
主入口文件 - v5.0 重构版
基于「大北极」格局下地缘与技术双向互动机制研究
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="北极战略可视化平台",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 全局样式 ============

st.markdown("""
<style>
    /* === 主题变量 === */
    :root {
        --arctic-blue: #1565C0;
        --arctic-light: #B3E5FC;
        --arctic-dark: #0D47A1;
        --arctic-ice: #E3F2FD;
        --arctic-red: #E53935;
        --arctic-green: #43A047;
        --arctic-orange: #FF6B35;
        --text-primary: #1a1a2e;
        --text-secondary: #546E7A;
        --text-muted: #90A4AE;
        --card-bg: #ffffff;
        --border-light: #e8e8e8;
    }

    /* === 侧边栏 === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D47A1 0%, #1565C0 50%, #1976D2 100%) !important;
        color: white;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
    }

    /* === 侧边栏Logo === */
    .sidebar-logo {
        text-align: center;
        padding: 1.2rem 0.5rem 0.8rem 0;
    }
    .sidebar-logo .logo-icon {
        font-size: 2.8rem;
        display: block;
        margin-bottom: 0.4rem;
    }
    .sidebar-logo h2 {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: white !important;
        margin: 0;
        line-height: 1.3;
    }
    .sidebar-logo p {
        font-size: 0.72rem !important;
        color: rgba(255,255,255,0.65) !important;
        margin: 0.2rem 0 0 0;
    }

    /* === 导航链接 === */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.65rem 0.9rem;
        border-radius: 10px;
        margin: 3px 0;
        text-decoration: none;
        font-size: 0.88rem;
        font-weight: 500;
        color: rgba(255,255,255,0.85) !important;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    .nav-item:hover {
        background: rgba(255,255,255,0.15) !important;
        color: white !important;
        transform: translateX(3px);
        border-color: rgba(255,255,255,0.2);
    }
    .nav-item .nav-icon {
        font-size: 1.1rem;
        width: 28px;
        text-align: center;
        flex-shrink: 0;
    }
    .nav-item .nav-label {
        flex: 1;
    }
    .nav-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.12);
        margin: 0.6rem 0;
    }

    /* === 主内容区 === */
    section[data-testid="stMain"] {
        background: #f5f7fa !important;
    }
    section[data-testid="stMain"] > div {
        background: #f5f7fa !important;
        padding-top: 0 !important;
    }

    /* === 页面顶部Banner === */
    .main-banner {
        background: linear-gradient(135deg, #0D47A1 0%, #1565C0 50%, #1976D2 100%);
        border-radius: 16px;
        padding: 1.8rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 24px rgba(13,71,161,0.2);
        position: relative;
        overflow: hidden;
    }
    .main-banner::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -5%;
        width: 200px;
        height: 200px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    }
    .main-banner h1 {
        color: white !important;
        font-size: 1.7rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        line-height: 1.3;
        position: relative;
        z-index: 1;
    }
    .main-banner p {
        color: rgba(255,255,255,0.82) !important;
        font-size: 0.88rem;
        margin: 0;
        position: relative;
        z-index: 1;
    }

    /* === KPI指标卡 === */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 1.1rem 1rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .kpi-card.blue::before { background: #1E88E5; }
    .kpi-card.red::before { background: #E53935; }
    .kpi-card.orange::before { background: #FF6B35; }
    .kpi-card.purple::before { background: #7B1FA2; }
    .kpi-card.green::before { background: #43A047; }

    .kpi-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .kpi-card .kpi-label {
        font-size: 0.72rem;
        color: #90A4AE;
        font-weight: 500;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .kpi-card .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1;
    }
    .kpi-card .kpi-value.blue { color: #1E88E5; }
    .kpi-card .kpi-value.red { color: #E53935; }
    .kpi-card .kpi-value.orange { color: #FF6B35; }
    .kpi-card .kpi-value.purple { color: #7B1FA2; }
    .kpi-card .kpi-value.green { color: #43A047; }

    /* === 功能模块网格 === */
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .module-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 1.5rem;
    }
    .module-card {
        background: white;
        border-radius: 16px;
        padding: 1.4rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.25s ease;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        text-decoration: none;
        color: inherit !important;
    }
    .module-card:hover {
        box-shadow: 0 8px 28px rgba(0,0,0,0.12);
        transform: translateY(-3px);
        border-color: var(--arctic-blue);
    }
    .module-card .module-icon {
        font-size: 2.2rem;
        line-height: 1;
    }
    .module-card .module-title {
        font-weight: 700;
        font-size: 1rem;
        color: #0D47A1;
        margin: 0;
    }
    .module-card .module-desc {
        font-size: 0.78rem;
        color: #546E7A;
        line-height: 1.6;
        margin: 0;
        flex: 1;
    }
    .module-card .module-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #E3F2FD;
        color: #1565C0;
        border-radius: 20px;
        padding: 0.2rem 0.7rem;
        font-size: 0.7rem;
        font-weight: 600;
        width: fit-content;
        margin-top: auto;
    }

    /* === 内容区分栏 === */
    .content-section {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }
    .content-section .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .content-section .section-header h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }

    /* === 框架说明卡片 === */
    .framework-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 14px;
        padding: 1.2rem;
        border-left: 4px solid #1565C0;
    }
    .framework-box h4 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0D47A1;
        margin: 0 0 0.6rem 0;
    }
    .framework-box p {
        font-size: 0.8rem !important;
        color: #37474F !important;
        line-height: 1.7 !important;
        margin: 0 0 0.5rem 0 !important;
    }
    .framework-box strong {
        color: #0D47A1 !important;
    }

    /* === 底部信息栏 === */
    .footer-bar {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        text-align: center;
        color: #90A4AE;
        font-size: 0.78rem;
        line-height: 1.6;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    }

    /* === Streamlit 元素覆盖 === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
    hr {
        border: none;
        border-top: 1px solid rgba(0,0,0,0.06);
        margin: 1.2rem 0;
    }
    /* 修复 Streamlit expander 边框 */
    .streamlit-expander {
        border: 1px solid #e8e8e8 !important;
        border-radius: 12px !important;
    }
    /* Streamlit metric 数字颜色 */
    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ============ 读取数据 ============

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
except ImportError as e:
    DATA_OK = False


# ============ 侧边栏导航 ============

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <span class="logo-icon">🌍</span>
            <h2>北极战略平台</h2>
            <p>大创专项 · v5.0</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        nav_items = [
            ("🏠", "首页概览", "app"),
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
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.55);font-weight:600;margin-bottom:0.4rem;">📊 项目信息</div>
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.65);line-height:1.8;">
        课题：北极地缘与技术双向互动<br>
        框架：Python + Streamlit<br>
        数据：GDELT / NSIDC / 专利
        </div>
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.55);font-weight:600;margin:0.8rem 0 0.4rem 0;">🔑 核心研究</div>
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.65);line-height:1.6;">
        技术进步赋能地缘权力延伸<br>
        中国北极安全应对策略
        </div>
        <div style="margin-top:1rem;padding-top:0.8rem;border-top:1px solid rgba(255,255,255,0.1);">
        <div style="font-size:0.68rem;color:rgba(255,255,255,0.4);">© 2025-2026 大创专项</div>
        </div>
        </div>
        """)


render_sidebar()


# ============ 首页内容 ============

st.markdown("""
<div class="main-banner">
    <h1>🌍 北极地缘与技术多要素联动3D可视化平台</h1>
    <p>基于「大北极」格局下地缘与技术双向互动机制研究 · 大学生创新创业训练计划专项</p>
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
    ("🌡️", "气候时空监测", "1980-2025年气温/海冰时空演变，CMIP6情景预测，航道通航评估", "气候监测", "2_气候时空监测"),
    ("🏛️", "地缘战略格局", "大国博弈网络图谱、政策文本词云与情感分析、科考站详情", "地缘格局", "3_地缘战略格局"),
    ("⚙️", "技术竞争与合作", "专利气泡图、技术合作网络、「技术-地缘」双轴联动看板", "技术竞争", "4_极地核心技术"),
    ("🛡️", "安全风险评估", "四维风险热力图、SWOT可视化、中国应对策略推演沙盘", "安全风险", "5_中国安全风险"),
    ("🗄️", "数据中心工具", "数据集下载、上传数据可视化、时空查询与对比分析", "数据中心", "6_数据中心工具"),
    ("ℹ️", "关于本项目", "项目介绍、研究框架、技术架构与团队信息", "关于项目", "7_关于本项目"),
]

module_html = '<div class="module-grid">'
for icon, title, desc, tag, page in modules:
    module_html += f'''
    <a class="module-card" href="./{page}">
        <div class="module-icon">{icon}</div>
        <div class="module-title">{title}</div>
        <div class="module-desc">{desc}</div>
        <div class="module-tag">📂 {tag}</div>
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
                import json
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
    <div style="margin-top:1rem;padding:1rem;background:#f8f9fa;border-radius:12px;">
        <div style="font-size:0.85rem;font-weight:700;color:#1a1a2e;margin-bottom:0.6rem;">🎯 研究核心问题</div>
        <ol style="font-size:0.8rem;color:#546E7A;line-height:2;margin:0;padding-left:1.2rem;">
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
            fig_trend = create_metric_trend_chart(recent, color="#1E88E5", height=100)
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
                fig_evt = create_metric_trend_chart(recent_events, color="#E53935", height=100)
                st.plotly_chart(fig_evt, use_container_width=True)
                st.caption(f"GDELT北极地缘事件年度趋势 | 2024年共计 {yearly.get(2024, 0):,} 起")
        except Exception:
            st.info("GDELT数据加载中...")

    with tab_latest3:
        try:
            patent_df = load_patent_data()
            recent_pat = patent_df.groupby('year')['patent_count'].sum().tail(10).tolist()
            fig_pat = create_metric_trend_chart(recent_pat, color="#9C27B0", height=100)
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
