"""
北极地缘与技术多要素联动3D可视化平台
主入口文件 - v4.0
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
    :root {
        --arctic-blue: #1565C0;
        --arctic-light: #B3E5FC;
        --arctic-dark: #0D47A1;
        --arctic-ice: #E3F2FD;
        --arctic-red: #E53935;
        --arctic-green: #43A047;
        --arctic-orange: #FF6B35;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D47A1 0%, #1565C0 40%, #1976D2 100%);
        color: white;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] a {
        color: white !important;
    }
    section[data-testid="stSidebar"] a:hover {
        color: white !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2);
    }
    .sidebar-logo {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .sidebar-logo h2 {
        font-size: 1.2rem;
        font-weight: 700;
        color: white !important;
        margin: 0;
    }
    .sidebar-logo p {
        font-size: 0.75rem;
        opacity: 0.7;
        margin: 0.2rem 0 0 0;
    }
    .nav-card {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        transition: all 0.2s;
        cursor: pointer;
        text-decoration: none;
        display: block;
    }
    .nav-card:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.5);
        transform: translateX(4px);
    }
    .nav-card.active {
        background: rgba(255,255,255,0.25);
        border-color: #FFD700;
    }
    .nav-card-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: white !important;
    }
    .nav-card-desc {
        font-size: 0.7rem;
        opacity: 0.7;
        color: white !important;
    }
    .main-header-bar {
        background: linear-gradient(135deg, #0D47A1 0%, #1565C0 50%, #1976D2 100%);
        padding: 1.2rem 2rem;
        border-radius: 0 0 16px 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(13,71,161,0.25);
    }
    .main-header-bar h1 {
        color: white;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
    }
    .main-header-bar p {
        color: rgba(255,255,255,0.85);
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
    }
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.2s;
    }
    .metric-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .metric-card-blue { border-top: 4px solid #1E88E5; }
    .metric-card-red { border-top: 4px solid #E53935; }
    .metric-card-green { border-top: 4px solid #43A047; }
    .metric-card-orange { border-top: 4px solid #FF6B35; }
    .metric-card-purple { border-top: 4px solid #7B1FA2; }
    .module-card {
        background: white;
        border-radius: 16px;
        padding: 1.4rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        transition: all 0.25s;
        height: 100%;
        cursor: pointer;
    }
    .module-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        transform: translateY(-3px);
        border-color: #1565C0;
    }
    .module-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .module-title {
        font-weight: 700;
        font-size: 1rem;
        color: #0D47A1;
        margin-bottom: 0.3rem;
    }
    .module-desc {
        font-size: 0.8rem;
        color: #546E7A;
        line-height: 1.5;
    }
    .module-tag {
        display: inline-block;
        background: #E3F2FD;
        color: #1565C0;
        border-radius: 20px;
        padding: 0.15rem 0.6rem;
        font-size: 0.7rem;
        margin-top: 0.5rem;
    }
    hr {
        border: none;
        border-top: 1px solid rgba(0,0,0,0.06);
        margin: 1.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
    .info-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #1565C0;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 4px 0;
        font-size: 0.82rem;
    }
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .legend-line {
        width: 20px;
        height: 3px;
        border-radius: 2px;
        flex-shrink: 0;
    }
    /* ============ 全局白色背景修复 ============ */
    /* 确保主内容区为白色背景，文字清晰可见 */
    .stApp > header[data-testid="stHeader"],
    .stApp [data-testid="stMainBlockContainer"],
    section[data-testid="stMain"] {
        background: white !important;
    }
    section[data-testid="stMain"] > div,
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li {
        color: #1a1a2e !important;
    }
    /* 确保markdown文字始终深色 */
    .stMarkdown p,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
        color: #1a1a2e !important;
    }
    /* 白色背景的卡片内容 */
    section[data-testid="stMain"] .stMarkdown .info-box,
    section[data-testid="stMain"] .warning-card {
        color: #1a1a2e !important;
    }
    /* tab颜色修复 */
    .stTabs [data-baseweb="tab"] {
        color: #333 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)


# ============ 侧边栏导航 ============

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <div style="font-size:2.5rem;margin-bottom:0.3rem;">🌍</div>
            <h2>北极战略平台</h2>
            <p>大创专项 · v4.0</p>
        </div>
        <hr>
        """, unsafe_allow_html=True)

        pages = [
            ("🏠", "首页概览", "app"),
            ("🌡️", "气候监测", "2-气候时空监测"),
            ("🏛️", "地缘格局", "3-地缘战略格局"),
            ("⚙️", "技术竞争", "4-极地核心技术"),
            ("🛡️", "安全风险", "5-中国安全风险"),
            ("🗄️", "数据中心", "6-数据中心工具"),
            ("ℹ️", "关于项目", "7-关于本项目"),
        ]

        current_page = st.query_params.get("page", "app")
        for icon, title, path in pages:
            is_active = (path == current_page) or (path == "app" and current_page == "app")
            cls = "nav-card active" if is_active else "nav-card"
            st.markdown(
                f'<a href="/?page={path}" class="{cls}">'
                f'<div class="nav-card-title">{icon} {title}</div></a>',
                unsafe_allow_html=True
            )

        st.divider()

        st.markdown("""
        **📊 项目信息**
        - 课题：北极地缘与技术双向互动
        - 框架：Python + Streamlit
        - 数据：GDELT / NSIDC / 专利

        **🔑 核心研究**
        技术进步赋能地缘权力延伸 +
        中国北极安全应对策略
        """)
        st.divider()
        st.caption("© 2025-2026 北极战略研究项目")
        st.caption("大创专项")


render_sidebar()

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
    st.error(f"数据模块加载失败: {e}")


# ============ 首页内容 ============

st.markdown("""
<div class="main-header-bar">
    <h1>🌍 北极地缘与技术多要素联动3D可视化平台</h1>
    <p>基于「大北极」格局下地缘与技术双向互动机制研究 · 大创专项</p>
</div>
""", unsafe_allow_html=True)

# ============ KPI 指标卡（增强：带趋势迷你图） ============
kpi_cols = st.columns(5)

kpi_data = [
    ("+3.7°C", "北极近十年升温速率", "#E53935", "⚠️"),
    ("-13.2%", "海冰面积累计下降", "#1565C0", "📉"),
    ("+45天", "航道通航窗口延长", "#FF6B35", "📈"),
    ("11", "覆盖国家/地区", "#7B1FA2", "🌐"),
    ("5", "平台核心模块", "#43A047", "🔧"),
]

for i, (value, label, color, icon) in enumerate(kpi_data):
    with kpi_cols[i]:
        st.markdown(f"""
        <div class="metric-card metric-card-{"blue red green orange purple".split()[i]}">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:0.5rem;">
                <span style="font-size:1.1rem;">{icon}</span>
                <span style="font-size:0.75rem;color:#90A4AE;font-weight:500;">{label}</span>
            </div>
            <div style="font-size:1.6rem;font-weight:800;color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============ 3D 地球 + 研究框架 ============
st.markdown("### 🎯 功能模块")
module_cols = st.columns(3)

modules = [
    ("🌡️", "气候时空监测", "1980-2025年气温/海冰时空演变，CMIP6情景预测，航道通航评估", "气候监测", "#B3E5FC"),
    ("🏛️", "地缘战略格局", "大国博弈网络图谱、政策文本词云与情感分析、科考站详情", "地缘格局", "#E8F5E9"),
    ("⚙️", "技术竞争与合作", "专利气泡图、技术合作网络、「技术-地缘」双轴联动看板", "技术竞争", "#F3E5F5"),
    ("🛡️", "安全风险评估", "四维风险热力图、SWOT可视化、中国应对策略推演沙盘", "安全风险", "#FFF3E0"),
    ("🗄️", "数据中心", "数据集下载、上传数据可视化、时空查询与对比分析", "数据中心", "#E0F7FA"),
    ("ℹ️", "关于项目", "项目介绍、研究框架、技术架构与团队信息", "关于项目", "#F5F5F5"),
]

for i, (icon, title, desc, tag, bg) in enumerate(modules):
    with module_cols[i % 3]:
        page_key = tag.lower().replace(" ", "")
        st.markdown(f"""
        <div class="module-card" onclick="window.location.href='/?page={page_key}'">
            <div class="module-icon">{icon}</div>
            <div class="module-title">{title}</div>
            <div class="module-desc" style="margin-top:0.5rem;">{desc}</div>
            <span class="module-tag">{tag}</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============ 核心研究框架 ============
st.markdown("### 📐 核心研究框架")

col_left, col_right = st.columns([1, 1])

with col_left:
    if DATA_OK:
        try:
            # 加载标注数据
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
                height=480
            )
            st.plotly_chart(fig_globe, use_container_width=True)
        except Exception:
            fig_globe = create_3d_globe(height=480)
            st.plotly_chart(fig_globe, use_container_width=True)
    else:
        st.info("数据模块未就绪")

with col_right:
    st.markdown("""
    **🔬「技术-地缘」双向互动分析框架**

    本平台突破传统地缘政治单向分析视角，引入「技术-地缘」互动框架：

    **路径一：技术进步 → 地缘扩展**
    极地破冰船技术、核动力推进、极地通信卫星等突破，
    拓展了国家在北极的存在边界和影响范围

    **路径二：地缘需求 → 技术投入**
    航道竞争和资源开发的战略需求，反向驱动高端船舶制造
    和极地基础设施投资

    **路径三：技术合作 → 信任构建**
    在大国博弈加剧的背景下，科技合作成为维持北极对话的
    『压舱石』

    ---

    **🎯 研究核心问题**

    1. 北极海冰快速融化如何从物理层面催生新航道？
    2. 大国在高端船舶与极地卫星领域博弈格局如何演变？
    3. 中国如何在三条路径上构建北极战略？
    """)

st.divider()

# ============ 最新动态数据展示 ============
if DATA_OK:
    tab_latest1, tab_latest2, tab_latest3 = st.tabs(["📈 海冰趋势", "🌐 地缘事件", "⚙️ 技术专利"])

    with tab_latest1:
        try:
            _, df_summary, _ = load_ice_data()
            trend = compute_trend(df_summary)
            recent = df_summary.tail(10)['mean'].tolist()
            fig_trend = create_metric_trend_chart(recent, color="#1E88E5", height=90)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.caption(f"近10年海冰面积均值趋势 | 每十年下降{trend['decline_per_decade']:.2f} M km² | R²={trend['r_squared']:.3f}")
        except Exception:
            st.info("海冰数据加载中...")

    with tab_latest2:
        try:
            _, yc_df = load_gdelt_data()
            if not yc_df.empty:
                yearly = yc_df.groupby('year')['EventCount'].sum()
                recent_events = yearly.tail(7).tolist()
                fig_evt = create_metric_trend_chart(recent_events, color="#E53935", height=90)
                st.plotly_chart(fig_evt, use_container_width=True)
                st.caption(f"GDELT北极地缘事件年度趋势 | 2024年共计{yearly.get(2024, 0):,}起")
        except Exception:
            st.info("GDELT数据加载中...")

    with tab_latest3:
        try:
            patent_df = load_patent_data()
            recent_pat = patent_df.groupby('year')['patent_count'].sum().tail(10).tolist()
            fig_pat = create_metric_trend_chart(recent_pat, color="#9C27B0", height=90)
            st.plotly_chart(fig_pat, use_container_width=True)
            total = patent_df['patent_count'].sum()
            st.caption(f"极地技术专利年度趋势 | 累计{total:,}项专利申请")
        except Exception:
            st.info("专利数据加载中...")

st.divider()

# ============ 底部信息 ============
st.markdown("""
<div style="background:#f8f9fa;padding:1rem;border-radius:12px;text-align:center;color:#90A4AE;font-size:0.8rem;">
    数据来源: GDELT 全球事件数据库 · NSIDC 海冰监测 · 专利数据库 · 各国北极政策文件<br>
    技术栈: Python + Streamlit + Plotly · 部署: Streamlit Community Cloud<br>
    © 2025-2026 北极地缘与技术双向互动机制研究 · 大创专项
</div>
""", unsafe_allow_html=True)
