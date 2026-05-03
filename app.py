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

# =========================================================================
# 全局样式 - 简洁专业
# =========================================================================

st.markdown("""
<style>
    /* 主背景白色 */
    .stApp > header { background: transparent; }
    .stApp [data-testid="stMainBlockContainer"] { background: #ffffff; padding: 0 1rem; }
    section[data-testid="stMain"] { background: #ffffff; }

    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #0d2149 50%, #0f3060 100%) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] a { color: rgba(255,255,255,0.95) !important; }

    /* 侧边栏导航链接 */
    .nav-link {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        margin: 4px 0;
        border-radius: 8px;
        color: rgba(255,255,255,0.8) !important;
        text-decoration: none;
        font-size: 0.9rem;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    .nav-link:hover {
        background: rgba(255,255,255,0.12);
        color: white !important;
        border-color: rgba(255,255,255,0.2);
    }
    .nav-link.active {
        background: rgba(255,255,255,0.18);
        color: white !important;
        border-color: rgba(255,255,255,0.35);
    }
    .nav-icon { font-size: 1.1rem; width: 24px; text-align: center; }
    .nav-divider { border-color: rgba(255,255,255,0.1) !important; margin: 8px 0; }

    /* KPI卡片 */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.05);
        text-align: center;
        transition: all 0.2s;
    }
    .kpi-card:hover {
        box-shadow: 0 6px 24px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .kpi-value { font-size: 2rem; font-weight: 800; line-height: 1; margin-bottom: 6px; }
    .kpi-label { font-size: 0.78rem; color: #64748b; font-weight: 500; }

    /* 模块卡片 */
    .module-card {
        background: white;
        border-radius: 16px;
        padding: 28px 24px;
        box-shadow: 0 2px 16px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.05);
        height: 100%;
        transition: all 0.25s;
        cursor: pointer;
    }
    .module-card:hover {
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        transform: translateY(-4px);
        border-color: rgba(13,71,161,0.25);
    }
    .module-icon { font-size: 2.2rem; margin-bottom: 12px; }
    .module-title { font-weight: 700; font-size: 1.05rem; color: #0f172a; margin-bottom: 8px; }
    .module-desc { font-size: 0.82rem; color: #64748b; line-height: 1.6; }
    .module-tag {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.72rem;
        margin-top: 12px;
        font-weight: 500;
    }

    /* 标题区域 */
    .hero-section {
        background: linear-gradient(135deg, #0a1628 0%, #0d2149 40%, #1565C0 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title { color: white; font-size: 1.9rem; font-weight: 800; margin: 0 0 10px 0; line-height: 1.3; }
    .hero-subtitle { color: rgba(255,255,255,0.75); font-size: 0.95rem; margin: 0; }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.9);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.72rem;
        margin-bottom: 10px;
        font-weight: 500;
    }

    /* 图表区样式 */
    .chart-section {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border: 1px solid rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
    }

    /* 全局文字颜色 */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown li, section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4 {
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# 侧边栏导航 - 使用 Streamlit 原生 page_link
# =========================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 12px 0 20px 0;">
            <div style="font-size:2.8rem; margin-bottom:6px;">🌍</div>
            <div style="font-size:1.15rem; font-weight:700; color:white !important; line-height:1.2;">
                北极战略平台
            </div>
            <div style="font-size:0.72rem; color:rgba(255,255,255,0.6); margin-top:4px;">
                大创专项 · v5.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        # 使用 st.page_link 实现原生多页面导航
        pages_map = {
            "🏠 首页概览": "app.py",
            "🌡️ 气候时空监测": "pages/2_气候时空监测.py",
            "🏛️ 地缘战略格局": "pages/3_地缘战略格局.py",
            "⚙️ 技术竞争与合作": "pages/4_极地核心技术.py",
            "🛡️ 中国安全风险": "pages/5_中国安全风险.py",
            "🗄️ 数据中心工具": "pages/6_数据中心工具.py",
            "ℹ️ 关于本项目": "pages/7_关于本项目.py",
        }

        for label, path in pages_map.items():
            icon = label.split()[0]
            st.page_link(path, label=label, icon=icon)

        st.markdown('<hr class="nav-divider">', unsafe_allow_html=True)

        st.markdown("""
        <div style="padding: 0 4px; font-size:0.78rem; color:rgba(255,255,255,0.6);">
            <div style="font-weight:600; margin-bottom:8px; color:rgba(255,255,255,0.75);">📊 项目信息</div>
            <div style="line-height:1.8;">
            课题：北极地缘与技术双向互动<br>
            框架：Python + Streamlit<br>
            数据：GDELT / NSIDC / 专利
            </div>
            <div style="margin-top:12px; line-height:1.8;">
            <div style="font-weight:600; margin-bottom:4px; color:rgba(255,255,255,0.75);">🔑 核心研究</div>
            技术进步赋能地缘权力延伸<br>
            中国北极安全应对策略
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.caption("© 2025-2026 大创专项")


render_sidebar()


# =========================================================================
# 首页内容
# =========================================================================

# Hero 区域
st.markdown("""
<div class="hero-section">
    <div class="hero-badge">🌍 大学生创新创业训练计划专项</div>
    <h1 class="hero-title">北极地缘与技术多要素联动<br>3D可视化平台</h1>
    <p class="hero-subtitle">基于「大北极」格局下地缘与技术双向互动机制研究 · 数据驱动的极地战略决策参考系统</p>
</div>
""", unsafe_allow_html=True)


# ============ KPI 指标 ============
st.markdown('<div class="section-title">📈 关键指标总览</div>', unsafe_allow_html=True)

kpi_cols = st.columns(5)
kpi_data = [
    ("+3.7°C", "北极近十年升温速率", "#dc2626"),
    ("-13.2%", "海冰面积累计下降", "#1565C0"),
    ("+45天", "航道通航窗口延长", "#ea580c"),
    ("11", "覆盖国家/地区", "#7c3aed"),
    ("6", "平台核心模块", "#059669"),
]
for i, (value, label, color) in enumerate(kpi_data):
    with kpi_cols[i]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value" style="color:{color};">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# ============ 核心研究框架 ============
st.markdown('<div class="section-title">📐 核心研究框架：「技术-地缘」双向互动分析</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1])

with col_left:
    if True:
        try:
            from src.viz import create_3d_globe
            fig_globe = create_3d_globe(highlight_arctic=True, height=400)
            st.plotly_chart(fig_globe, use_container_width=True)
        except Exception:
            st.info("🗺️ 3D地球可视化加载中...")

with col_right:
    st.markdown("""
    <div style="padding:8px 0;">
        <div style="background:#f8fafc;border-radius:10px;padding:16px;margin-bottom:12px;border-left:4px solid #1565C0;">
            <div style="font-weight:700;color:#1565C0;margin-bottom:6px;font-size:0.9rem;">路径一：技术进步 → 地缘扩展</div>
            <div style="font-size:0.82rem;color:#475569;line-height:1.6;">
                极地破冰船技术、核动力推进、极地通信卫星等突破，
                拓展了国家在北极的存在边界和影响范围
            </div>
        </div>
        <div style="background:#f8fafc;border-radius:10px;padding:16px;margin-bottom:12px;border-left:4px solid #7c3aed;">
            <div style="font-weight:700;color:#7c3aed;margin-bottom:6px;font-size:0.9rem;">路径二：地缘需求 → 技术投入</div>
            <div style="font-size:0.82rem;color:#475569;line-height:1.6;">
                航道竞争和资源开发的战略需求，反向驱动高端船舶制造
                和极地基础设施投资
            </div>
        </div>
        <div style="background:#f8fafc;border-radius:10px;padding:16px;border-left:4px solid #059669;">
            <div style="font-weight:700;color:#059669;margin-bottom:6px;font-size:0.9rem;">路径三：技术合作 → 信任构建</div>
            <div style="font-size:0.82rem;color:#475569;line-height:1.6;">
                在大国博弈加剧的背景下，科技合作成为维持北极对话的『压舱石』
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# ============ 功能模块 ============
st.markdown('<div class="section-title">🧭 平台核心模块</div>', unsafe_allow_html=True)

module_cols = st.columns(3)
modules = [
    ("🌡️", "气候时空监测", "1980-2025年气温/海冰时空演变，CMIP6情景预测，航道通航评估", "气候监测", "#eff6ff", "#1565C0"),
    ("🏛️", "地缘战略格局", "大国博弈网络图谱、政策文本词云与情感分析、科考站详情", "地缘格局", "#f0fdf4", "#166534"),
    ("⚙️", "技术竞争与合作", "专利气泡图、技术合作网络、「技术-地缘」双轴联动看板", "技术竞争", "#faf5ff", "#7e22ce"),
    ("🛡️", "安全风险评估", "四维风险热力图、SWOT可视化、中国应对策略推演沙盘", "安全风险", "#fff7ed", "#c2410c"),
    ("🗄️", "数据中心", "数据集下载、上传数据可视化、时空查询与对比分析", "数据中心", "#f0fdfa", "#0d9488"),
    ("ℹ️", "关于项目", "项目介绍、研究框架、技术架构与团队信息", "关于项目", "#f8fafc", "#475569"),
]

for i, (icon, title, desc, tag, bg, border) in enumerate(modules):
    page_file = f"pages/2_气候时空监测.py"
    if tag == "气候监测": page_file = "pages/2_气候时空监测.py"
    elif tag == "地缘格局": page_file = "pages/3_地缘战略格局.py"
    elif tag == "技术竞争": page_file = "pages/4_极地核心技术.py"
    elif tag == "安全风险": page_file = "pages/5_中国安全风险.py"
    elif tag == "数据中心": page_file = "pages/6_数据中心工具.py"
    elif tag == "关于项目": page_file = "pages/7_关于本项目.py"

    with module_cols[i % 3]:
        with st.container():
            st.markdown(f"""
            <div class="module-card" onclick="window.location.href='?page={tag}'" style="background:{bg};border-color:{border}20;">
                <div class="module-icon">{icon}</div>
                <div class="module-title">{title}</div>
                <div class="module-desc">{desc}</div>
                <span class="module-tag" style="background:{border}15;color:{border};">{tag}</span>
            </div>
            """, unsafe_allow_html=True)

st.divider()


# ============ 最新动态数据 ============
try:
    from src.data_core import load_ice_data, load_gdelt_data, load_patent_data, compute_trend

    tab_latest1, tab_latest2, tab_latest3 = st.tabs(["📈 海冰趋势", "🌐 地缘事件", "⚙️ 技术专利"])

    with tab_latest1:
        try:
            _, df_summary, _ = load_ice_data()
            trend = compute_trend(df_summary)
            from src.viz import create_metric_trend_chart
            recent = df_summary.tail(10)['mean'].tolist()
            fig_trend = create_metric_trend_chart(recent, color="#1565C0", height=90)
            st.plotly_chart(fig_trend, use_container_width=True)
            st.caption(f"📊 近10年海冰面积均值趋势 | 每十年下降 {trend['decline_per_decade']:.2f} M km² | R²={trend['r_squared']:.3f}")
        except Exception:
            st.info("海冰数据加载中...")

    with tab_latest2:
        try:
            _, yc_df = load_gdelt_data()
            if not yc_df.empty:
                yearly = yc_df.groupby('year')['EventCount'].sum()
                recent_events = yearly.tail(7).tolist()
                from src.viz import create_metric_trend_chart
                fig_evt = create_metric_trend_chart(recent_events, color="#dc2626", height=90)
                st.plotly_chart(fig_evt, use_container_width=True)
                st.caption(f"🌐 GDELT北极地缘事件年度趋势 | 2024年共计 {yearly.get(2024, 0):,} 起")
            else:
                st.info("GDELT数据加载中...")
        except Exception:
            st.info("GDELT数据加载中...")

    with tab_latest3:
        try:
            patent_df = load_patent_data()
            recent_pat = patent_df.groupby('year')['patent_count'].sum().tail(10).tolist()
            from src.viz import create_metric_trend_chart
            fig_pat = create_metric_trend_chart(recent_pat, color="#7c3aed", height=90)
            st.plotly_chart(fig_pat, use_container_width=True)
            total = patent_df['patent_count'].sum()
            st.caption(f"⚙️ 极地技术专利年度趋势 | 累计 {total:,} 项专利申请")
        except Exception:
            st.info("专利数据加载中...")

except Exception:
    st.info("📊 数据模块加载中，请稍候...")

st.divider()


# ============ 底部信息 ============
st.markdown("""
<div style="background:#f8fafc;border-radius:12px;padding:20px;text-align:center;">
    <div style="font-size:0.82rem;color:#64748b;line-height:2;">
        数据来源: GDELT 全球事件数据库 · NSIDC 海冰监测 · 专利数据库 · 各国北极政策文件<br>
        技术栈: Python + Streamlit + Plotly · 部署: Streamlit Community Cloud<br>
        <span style="color:#94a3b8;">© 2025-2026 北极地缘与技术双向互动机制研究 · 大创专项</span>
    </div>
</div>
""", unsafe_allow_html=True)
