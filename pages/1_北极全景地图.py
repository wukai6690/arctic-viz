"""
北极战略态势全景地图 — 巅峰重构版
融合 Plotly 3D 地球 + PyDeck 极地视角 + Folium 交互地图
暗色沉浸式设计，前沿可视化技术
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_stations, load_geopolitics_network, load_risk_data
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS

st.set_page_config(
    page_title="北极全景地图",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 全局暗色沉浸式样式 — 地图专属主题
# ============================================================

st.markdown("""
<style>
    /* ---- 整体暗色沉浸背景 ---- */
    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] {
        background: #060912 !important;
        min-height: 100vh;
    }
    section[data-testid="stMain"] > div {
        background: transparent !important;
        padding: 0 1rem !important;
    }

    /* ---- 全局文字颜色修复 ---- */
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li, section[data-testid="stMain"] td,
    section[data-testid="stMain"] th { color: rgba(255,255,255,0.92) !important; }
    .stMarkdown p, .stMarkdown li { color: rgba(255,255,255,0.85) !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: white !important; }
    /* Streamlit 组件文字 */
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.55) !important; }
    .stTabs [data-baseweb="tab"] { color: rgba(255,255,255,0.6) !important; }
    .stTabs [data-baseweb="tab"]:hover { color: white !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(30,136,229,0.25) !important;
        color: white !important;
    }
    .stSelectbox [data-baseweb="select"] > div { color: white !important; }
    .stSlider label, .stSlider span { color: rgba(255,255,255,0.7) !important; }
    .stCheckbox label { color: rgba(255,255,255,0.75) !important; }
    .stMultiSelect [data-baseweb="select"] > div { color: white !important; }
    [data-testid="stCaption"] { color: rgba(255,255,255,0.35) !important; }
    [data-baseweb="select"] { background: rgba(255,255,255,0.06) !important; }
    .streamlit-expander {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
    }
    .streamlit-expander summary { color: rgba(255,255,255,0.8) !important; }
    /* Streamlit expander header */
    .streamlit-expander > div > summary { color: rgba(255,255,255,0.8) !important; }
    /* Metric 修复 */
    [data-testid="stMetricValue"] { font-weight: 700 !important; }

    /* ---- 顶部 Hero Banner ---- */
    .hero-banner {
        background: linear-gradient(135deg, #020617 0%, #0a1628 40%, #0f2744 100%);
        border-radius: 18px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.2rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -60%; right: -5%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(30,136,229,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: -40%; left: -5%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(229,57,53,0.05) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-banner .hero-title {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: white !important;
        margin: 0 0 0.5rem 0 !important;
        position: relative;
        z-index: 1;
        line-height: 1.3;
    }
    .hero-banner .hero-sub {
        color: rgba(255,255,255,0.55) !important;
        font-size: 0.85rem !important;
        margin: 0 !important;
        position: relative;
        z-index: 1;
    }
    .hero-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(30,136,229,0.15);
        border: 1px solid rgba(30,136,229,0.3);
        border-radius: 20px; padding: 4px 12px;
        font-size: 0.72rem; color: rgba(144,202,249,0.9);
        font-weight: 600;
        position: relative; z-index: 1;
    }

    /* ---- 统计卡片 ---- */
    .stat-cards-row {
        display: flex; gap: 12px; margin-bottom: 1.2rem; flex-wrap: wrap;
    }
    .stat-mini-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 1rem 1.2rem;
        flex: 1; min-width: 140px;
        backdrop-filter: blur(8px);
        transition: all 0.2s;
    }
    .stat-mini-card:hover {
        background: rgba(255,255,255,0.07);
        border-color: rgba(255,255,255,0.12);
    }
    .stat-mini-card .s-label {
        font-size: 0.68rem; color: rgba(255,255,255,0.4);
        font-weight: 600; margin-bottom: 4px;
        display: flex; align-items: center; gap: 4px;
    }
    .stat-mini-card .s-value {
        font-size: 1.35rem; font-weight: 800; color: white;
        line-height: 1; margin-bottom: 3px;
    }
    .stat-mini-card .s-sub {
        font-size: 0.65rem; color: rgba(255,255,255,0.3);
    }

    /* ---- 地图容器 ---- */
    .map-hero-container {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
        margin-bottom: 1.2rem;
        position: relative;
    }
    .map-hero-container .map-overlay-stats {
        position: absolute;
        bottom: 16px; left: 16px;
        background: rgba(6,9,18,0.88);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        z-index: 1000;
        min-width: 200px;
    }
    .map-overlay-stats .mos-title {
        font-size: 0.68rem; color: rgba(255,255,255,0.4);
        font-weight: 600; margin-bottom: 6px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .map-overlay-stats .mos-row {
        display: flex; justify-content: space-between;
        align-items: center; padding: 3px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .map-overlay-stats .mos-row:last-child { border-bottom: none; }
    .map-overlay-stats .mos-label { font-size: 0.72rem; color: rgba(255,255,255,0.5); }
    .map-overlay-stats .mos-val { font-size: 0.8rem; font-weight: 700; }

    /* ---- 控制面板 ---- */
    .control-panel-dark {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.2rem;
        color: white !important;
        backdrop-filter: blur(8px);
    }
    .control-panel-dark h3 {
        color: white !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.8rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    }
    .control-panel-dark h4 {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        margin: 0.6rem 0 0.4rem 0 !important;
    }
    .control-panel-dark p, .control-panel-dark span,
    .control-panel-dark div, .control-panel-dark label {
        color: rgba(255,255,255,0.65) !important;
    }
    .toggle-item {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .toggle-item:last-child { border-bottom: none; }
    .legend-item-dark {
        display: flex; align-items: center; gap: 8px;
        font-size: 0.72rem; color: rgba(255,255,255,0.65);
        padding: 3px 0;
    }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .legend-line { width: 22px; height: 3px; border-radius: 2px; flex-shrink: 0; }

    /* ---- Tab 栏暗色 ---- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 3px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 7px 16px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        color: rgba(255,255,255,0.5) !important;
        transition: all 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.06) !important;
        color: rgba(255,255,255,0.8) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(30,136,229,0.3) !important;
        color: white !important;
    }

    /* ---- 内容区块 ---- */
    .content-block {
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(6px);
    }
    .content-block h3 {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: white !important;
        margin: 0 0 1rem 0 !important;
        padding-bottom: 0.6rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        display: flex; align-items: center; gap: 8px;
    }
    .content-block p { font-size: 0.8rem !important; }

    /* ---- 底部信息条 ---- */
    .map-footer-bar {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-top: 1rem;
    }
    .map-footer-bar .mf-text {
        font-size: 0.72rem; color: rgba(255,255,255,0.3);
    }
    .map-footer-bar .mf-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(255,255,255,0.05);
        border-radius: 20px; padding: 3px 10px;
        font-size: 0.68rem; color: rgba(255,255,255,0.45);
    }

    /* ---- 国家排名条 ---- */
    .country-bar-item {
        display: flex; align-items: center; gap: 10px;
        padding: 5px 0;
    }
    .country-bar-item .cb-dot {
        width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
    }
    .country-bar-item .cb-name {
        font-size: 0.78rem; color: rgba(255,255,255,0.7);
        min-width: 50px;
    }
    .country-bar-item .cb-bar-bg {
        flex: 1; height: 4px;
        background: rgba(255,255,255,0.06);
        border-radius: 2px; overflow: hidden;
    }
    .country-bar-item .cb-bar-fill {
        height: 4px; border-radius: 2px;
    }
    .country-bar-item .cb-count {
        font-size: 0.75rem; font-weight: 700; color: rgba(255,255,255,0.8);
        min-width: 30px; text-align: right;
    }

    /* ---- 分隔线 ---- */
    hr {
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.06) !important;
        margin: 1.2rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 页面顶部 Banner
# ============================================================

st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">🌍 北极战略态势</div>
    <h1 class="hero-title">🗺️ 北极地缘与技术全景地图</h1>
    <p class="hero-sub">大北极国家科考站网络 · 战略航道布局 · GDELT 地缘事件热力 · 实时数据联动</p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 核心统计数据（迷你卡片）
# ============================================================

grid_df, yc_df = load_gdelt_data()
stations_data = load_stations()
net_data = load_geopolitics_network('all')

total_stations = len(stations_data.get('features', []))
total_events = int(yc_df['EventCount'].sum()) if not yc_df.empty else 0
avg_tone = yc_df['AvgTone'].mean() if not yc_df.empty else 0
tone_label = "偏正面" if avg_tone > 0 else "偏负面"
tone_color = "#43A047" if avg_tone > 0 else "#E53935"
tone_val_color = "#43A047" if avg_tone > 0 else "#E53935"

country_counts = {}
for feat in stations_data.get('features', []):
    c = feat.get('properties', {}).get('country', '未知')
    country_counts[c] = country_counts.get(c, 0) + 1

top_country_name = max(country_counts, key=country_counts.get) if country_counts else "未知"
route_count = 5
conflict_count = 3

st.markdown(f"""
<div class="stat-cards-row">
    <div class="stat-mini-card">
        <div class="s-label">🔬 科考站</div>
        <div class="s-value" style="color:#1E88E5">{total_stations}</div>
        <div class="s-sub">大北极研究网络</div>
    </div>
    <div class="stat-mini-card">
        <div class="s-label">📊 地缘事件</div>
        <div class="s-value" style="color:#E53935">{total_events:,}</div>
        <div class="s-sub">GDELT 2018-2024</div>
    </div>
    <div class="stat-mini-card">
        <div class="s-label">🚢 战略航道</div>
        <div class="s-value" style="color:#FF6B35">{route_count}</div>
        <div class="s-sub">东北/西北/跨极航道</div>
    </div>
    <div class="stat-mini-card">
        <div class="s-label">⚡ 情感指数</div>
        <div class="s-value" style="color:{tone_val_color}">{avg_tone:+.2f}</div>
        <div class="s-sub">{tone_label}</div>
    </div>
    <div class="stat-mini-card">
        <div class="s-label">🌐 最活跃国家</div>
        <div class="s-value" style="color:#FF6B35">{top_country_name}</div>
        <div class="s-sub">科考站数量最多</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 主地图区域 — 4 个标签页
# ============================================================

map_tab1, map_tab2, map_tab3, map_tab4, map_tab5 = st.tabs([
    "🌍 3D极地全景",
    "🗺️ 交互地图",
    "📈 战略统计",
    "🧊 GDELT热力时序",
    "🔗 国家关系网络"
])


# ----------------------------------------------------------------
# Tab1: 3D 极地全景 — Plotly 正射投影 + 旋转 + 丰富图层
# ----------------------------------------------------------------
with map_tab1:
    col_ctl1, col_map1 = st.columns([1, 4.5])

    with col_ctl1:
        st.markdown('<div class="control-panel-dark">', unsafe_allow_html=True)
        st.markdown("### 🕹️ 图层控制")

        show_stations = st.checkbox("🔬 科考站网络", value=True)
        show_routes = st.checkbox("🚢 战略航道", value=True)
        show_events_map = st.checkbox("📊 GDELT事件", value=True)
        show_arctic = st.checkbox("🔵 北极圈参考", value=True)
        show_bases = st.checkbox("🏰 军事基地", value=False)

        st.markdown("### 🌍 旋转视角")
        rot_lon = st.slider("经度旋转", -180, 180, -30, help="拖动改变地球视角")
        rot_lat = st.slider("纬度倾斜", 60, 90, 78, help="俯视角度（越大越俯视北极）")

        st.markdown("### 📖 图例")
        st.markdown("""
        <div class="legend-item-dark"><div class="legend-dot" style="background:#FF0000"></div>中国科考站</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#1565C0"></div>美国科考站</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#8B0000"></div>俄罗斯科考站</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#FF6F00"></div>北欧科考站</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#607D8B"></div>国际合作站</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#E53935"></div>东北航道 NSR</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#1E88E5"></div>西北航道 NWP</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#43A047"></div>跨极航道 TSR</div>
        """, unsafe_allow_html=True)

        st.markdown("### 🗺️ 地图操作提示")
        st.markdown("""
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.4);line-height:1.7;">
        • 鼠标<strong style="color:rgba(255,255,255,0.6)">按住拖动</strong>旋转地球<br>
        • 鼠标<strong style="color:rgba(255,255,255,0.6)">滚轮</strong>缩放<br>
        • <strong style="color:rgba(255,255,255,0.6)">点击标记</strong>查看详情
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_map1:
        import plotly.graph_objects as go

        fig = go.Figure()

        # 北极圈经纬网格
        for lat in [66.5, 70, 75, 80, 85]:
            lons = np.linspace(-180, 180, 90)
            lats = [lat] * len(lons)
            dash = 'dash' if lat == 66.5 else 'dot'
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats, mode='lines',
                line=dict(width=1.2 if lat == 66.5 else 0.5,
                         color=f'rgba(144,202,249,{"0.9" if lat == 66.5 else "0.25"})',
                         dash=dash),
                showlegend=False, hoverinfo='skip'
            ))
        for lon in np.arange(-180, 180, 30):
            lats = np.linspace(60, 90, 30)
            lons_l = [lon] * len(lats)
            fig.add_trace(go.Scattergeo(
                lon=lons_l, lat=lats, mode='lines',
                line=dict(width=0.5, color='rgba(144,202,249,0.15)'),
                showlegend=False, hoverinfo='skip'
            ))

        # 北极圈标注
        if show_arctic:
            arctic_lons = np.linspace(-180, 180, 180)
            arctic_lats = [66.5] * len(arctic_lons)
            fig.add_trace(go.Scattergeo(
                lon=arctic_lons, lat=arctic_lats, mode='lines',
                line=dict(width=2.5, color='rgba(144,202,249,0.9)', dash='dash'),
                name='北极圈 (66.5°N)', showlegend=True,
                hoverinfo='text', hovertext='北极圈 66.5°N'
            ))

        # 科考站
        station_colors_map = {
            '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726',
            '挪威/国际': '#FF6F00', '加拿大': '#43A047', '加拿大 ': '#43A047',
        }

        if show_stations:
            for feat in stations_data.get('features', []):
                props = feat.get('properties', {})
                geom = feat.get('geometry', {})
                if not geom or 'coordinates' not in geom:
                    continue
                lon, lat = geom['coordinates'][0], geom['coordinates'][1]
                country = props.get('country', '未知')
                name = props.get('name', '未知')
                color = station_colors_map.get(country, '#757575')
                established = props.get('established', 'N/A')
                research = props.get('research_focus', [])
                tech_domain = props.get('tech_domain', 'N/A')
                desc = props.get('description', '')

                fig.add_trace(go.Scattergeo(
                    lon=[lon], lat=[lat],
                    mode='markers+text',
                    marker=dict(
                        size=15, color=color,
                        line=dict(width=2, color='white'),
                        opacity=0.95,
                        symbol='circle'
                    ),
                    text=[name],
                    textposition='top center',
                    textfont=dict(size=9, color='white'),
                    hovertemplate=(
                        f"<b style='color:{color}'>🔬 {name}</b><br>"
                        f"<extra></extra>"
                        f"<b>国家:</b> {country}<br>"
                        f"<b>设立:</b> {established}<br>"
                        f"<b>坐标:</b> {lat:.2f}°N, {lon:.2f}°E<br>"
                        f"<b>技术方向:</b> {tech_domain}<br>"
                        f"<b>研究领域:</b> {', '.join(research[:3]) if research else 'N/A'}<br>"
                        f"<b>简介:</b> {desc[:120]}{'...' if len(desc) > 120 else ''}"
                    ),
                    name=f'🔬 {name}',
                    showlegend=False
                ))

        # 战略航道
        if show_routes:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
            if os.path.exists(routes_path):
                with open(routes_path, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                for feat in routes_data.get('features', []):
                    props = feat.get('properties', {})
                    geom = feat.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    name = props.get('name', '')
                    color = props.get('color', '#FF6B35')
                    distance = props.get('distance', '')
                    duration = props.get('duration', '')
                    operator = props.get('operator', '')
                    desc = props.get('description', '')

                    fig.add_trace(go.Scattergeo(
                        lon=[c[0] for c in coords],
                        lat=[c[1] for c in coords],
                        mode='lines',
                        line=dict(width=5, color=color, opacity=0.85),
                        hovertemplate=(
                            f"<b style='color:{color}'>🚢 {name}</b><br>"
                            f"<extra></extra>"
                            f"<b>航程:</b> {distance}<br>"
                            f"<b>航行时间:</b> {duration}<br>"
                            f"<b>主导方:</b> {operator}<br>"
                            f"<b>说明:</b> {desc[:80]}..."
                        ),
                        name=f'🚢 {name}',
                        showlegend=True
                    ))

        # GDELT 事件热力散点
        if show_events_map and not grid_df.empty:
            year_col = next((c for c in ['Year_local', 'Year'] if c in grid_df.columns), None)
            if year_col:
                latest_year = grid_df[year_col].max()
                year_data = grid_df[grid_df[year_col] == latest_year]
                lat_col = next((c for c in ['lat_grid', 'lat'] if c in year_data.columns), 'lat_grid')
                lon_col = next((c for c in ['lon_grid', 'lon'] if c in year_data.columns), 'lon_grid')

                for threshold, size, opacity in [(20, 8, 0.35), (10, 6, 0.5), (1, 4, 0.7)]:
                    ev_data = year_data[year_data['EventCount'] >= threshold]
                    if len(ev_data) > 0:
                        fig.add_trace(go.Scattergeo(
                            lon=ev_data[lon_col].tolist(),
                            lat=ev_data[lat_col].tolist(),
                            mode='markers',
                            marker=dict(
                                size=size,
                                color=ev_data['EventCount'].tolist(),
                                colorscale='Reds',
                                opacity=opacity,
                                cmin=0, cmax=50,
                                colorbar=dict(
                                    title='事件数', len=0.35, y=0.5,
                                    titlefont=dict(color='white', size=11),
                                    tickfont=dict(color='rgba(255,255,255,0.6)', size=9),
                                    bgcolor='rgba(0,0,0,0.4)',
                                    bordercolor='rgba(255,255,255,0.1)',
                                    borderwidth=1
                                )
                            ),
                            hovertemplate='📊 地缘事件: %{marker.color}起<br>坐标: %{lat:.1f}°N, %{lon:.1f}°E<extra></extra>',
                            name=f'📊 事件热力({latest_year})',
                            showlegend=False
                        ))

        # 军事基地
        if show_bases:
            military_bases = [
                (71.59, -45.54, '北极战略指挥中心', '俄罗斯', '#B71C1C'),
                (76.53, -45.42, '图勒空军基地', '美国/丹麦', '#B71C1C'),
                (82.5, -82.53, '阿勒特雷达站', '加拿大', '#B71C1C'),
                (69.97, 30.04, '希尔克内斯海军基地', '挪威', '#B71C1C'),
            ]
            for lat, lon, name, country, color in military_bases:
                fig.add_trace(go.Scattergeo(
                    lon=[lon], lat=[lat],
                    mode='markers',
                    marker=dict(size=12, color=color, symbol='diamond',
                               line=dict(width=2, color='white')),
                    hovertemplate=f"🏰 <b>{name}</b><br>所属: {country}<extra></extra>",
                    name=f'🏰 {name}', showlegend=False
                ))

        # 更新布局
        fig.update_layout(
            geo=dict(
                scope='world',
                projection_type='orthographic',
                projection_rotation=dict(lon=rot_lon, lat=rot_lat),
                center=dict(lat=rot_lat, lon=rot_lon),
                showland=True,
                landcolor='rgba(220,235,250,0.9)',
                showocean=True,
                oceancolor='rgba(140,185,235,0.65)',
                showlakes=True,
                lakecolor='rgba(140,185,235,0.75)',
                showcountries=True,
                countrycolor='rgba(150,175,210,0.5)',
                showcoastlines=True,
                coastlinecolor='rgba(130,160,195,0.6)',
                coastlinewidth=0.8,
                showframe=False,
                bgcolor='rgba(6,9,18,0)',
                lataxis_range=[55, 90],
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=30),
            height=640,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.04,
                xanchor='center',
                x=0.5,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.08)',
                borderwidth=1,
                font=dict(color='rgba(255,255,255,0.7)', size=9),
                itemsizing='constant'
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # 底部信息条
    st.markdown("""
    <div class="map-footer-bar">
        <div class="mf-text">🗺️ 北极战略态势全景地图 | 数据更新: 2024 | GDELT · INTERACT · GeoJSON | © 大创专项</div>
        <div class="mf-badge">🌍 北极圈 66.5°N</div>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# Tab2: Folium 交互地图 — 多底图切换 + 精细化图层 + 丰富 Popup
# ----------------------------------------------------------------
with map_tab2:
    col_ctl2, col_map2 = st.columns([1, 5.5])

    with col_ctl2:
        st.markdown('<div class="control-panel-dark">', unsafe_allow_html=True)

        st.markdown("### 🗺️ 交互地图控制")

        f_show_stations = st.checkbox("🔬 科考站", value=True)
        f_show_routes = st.checkbox("🚢 战略航道", value=True)
        f_show_events = st.checkbox("📊 事件热力", value=True)
        f_show_conflicts = st.checkbox("⚠️ 冲突事件", value=False)
        f_show_military = st.checkbox("🏰 军事基地", value=False)

        tile_choice = st.selectbox("底图风格", [
            "CartoDB Positron", "CartoDB Dark", "Esri Satellite",
            "OpenStreetMap", "Stamen Terrain"
        ], format_func=lambda x: x)

        f_year = st.slider("年份筛选", 2018, 2024, 2023)

        st.markdown("### 🌐 国家筛选")
        f_countries = st.multiselect(
            "选择国家",
            options=['RUS', 'USA', 'CHN', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR'],
            default=['RUS', 'USA', 'CHN', 'NOR', 'CAN'],
            format_func=lambda x: COUNTRY_NAMES.get(x, x)
        )

        st.markdown("### 📖 图例")
        st.markdown("""
        <div class="legend-item-dark"><div class="legend-dot" style="background:#FF0000"></div>中国</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#1565C0"></div>美国</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#8B0000"></div>俄罗斯</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#FF6F00"></div>挪威</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#43A047"></div>加拿大</div>
        <div class="legend-item-dark"><div class="legend-dot" style="background:#607D8B"></div>国际组织</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#E53935"></div>东北航道 NSR</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#1E88E5"></div>西北航道 NWP</div>
        <div class="legend-item-dark"><div class="legend-line" style="background:#43A047"></div>跨极航道 TSR</div>
        """, unsafe_allow_html=True)

        st.markdown("### 💡 操作提示")
        st.markdown("""
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);line-height:1.7;">
        • <b>点击</b>标记查看详情<br>
        • <b>滚轮</b>缩放地图<br>
        • <b>右下角</b>切换全屏<br>
        • <b>右上角</b>切换图层
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_map2:
        import folium
        from folium import plugins

        tile_templates = {
            "CartoDB Positron": ('cartodbpositron', 'CartoDB'),
            "CartoDB Dark": ('CartoDB.dark_matter', 'CartoDB'),
            "Esri Satellite": ('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 'Esri'),
            "OpenStreetMap": ('OpenStreetMap', 'OSM'),
            "Stamen Terrain": ('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', 'Stadia'),
        }
        tile_url, tile_attr = tile_templates.get(tile_choice, ('cartodbpositron', 'CartoDB'))

        m = folium.Map(
            location=[72, 30],
            zoom_start=3,
            tiles=None,
            prefer_canvas=True
        )

        if tile_choice == "Stamen Terrain":
            folium.TileLayer(tile_url, attr=tile_attr, name=tile_choice).add_to(m)
        elif tile_choice == "Esri Satellite":
            folium.TileLayer(tiles=tile_url, attr='Esri', name=tile_choice).add_to(m)
        else:
            folium.TileLayer(tiles=tile_url, name=tile_choice).add_to(m)
        folium.TileLayer('cartodbpositron', name='浅色底图').add_to(m)
        folium.TileLayer('CartoDB.dark_matter', name='深色底图').add_to(m)

        station_colors_map = {
            '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726',
            '挪威/国际': '#FF6F00', '加拿大': '#43A047', '加拿大 ': '#43A047',
        }

        # 科考站
        if f_show_stations:
            station_group = folium.FeatureGroup(name='🔬 科考站网络')

            for feat in stations_data.get('features', []):
                props = feat.get('properties', {})
                geom = feat.get('geometry', {})
                if not geom or 'coordinates' not in geom:
                    continue
                lon, lat = geom['coordinates'][0], geom['coordinates'][1]
                country = props.get('country', '未知')
                name = props.get('name', '未知')
                established = props.get('established', 'N/A')
                research = props.get('research_focus', [])
                tech_domain = props.get('tech_domain', 'N/A')
                desc = props.get('description', '')
                color = station_colors_map.get(country, '#757575')

                popup_html = f"""
                <div style="min-width:320px;font-family:'Segoe UI',Arial,sans-serif;">
                    <div style="background:linear-gradient(135deg,{color}22,{color}44);border-left:4px solid {color};padding:10px 14px;border-radius:8px 8px 0 0;">
                        <h3 style="color:{color};margin:0;font-size:16px;font-weight:700;">🔬 {name}</h3>
                    </div>
                    <div style="padding:12px 14px;">
                        <table style="width:100%;font-size:13px;border-collapse:collapse;">
                            <tr><td style="padding:5px 8px;color:#607D8B;width:35%;font-weight:600;">所属国</td><td style="padding:5px 8px;color:#1a1a2e;font-weight:600;">{country}</td></tr>
                            <tr style="background:#f8f9fa;"><td style="padding:5px 8px;color:#607D8B;font-weight:600;">设立年份</td><td style="padding:5px 8px;color:#1a1a2e;">{established}</td></tr>
                            <tr><td style="padding:5px 8px;color:#607D8B;font-weight:600;">地理坐标</td><td style="padding:5px 8px;color:#1a1a2e;">{lat:.2f}°N, {lon:.2f}°E</td></tr>
                            <tr style="background:#f8f9fa;"><td style="padding:5px 8px;color:#607D8B;font-weight:600;">技术方向</td><td style="padding:5px 8px;color:#1a1a2e;">{tech_domain}</td></tr>
                        </table>
                        <div style="margin-top:10px;padding:10px;background:#f0f4f8;border-radius:8px;">
                            <div style="font-size:12px;color:#37474F;line-height:1.7;">
                                <b style="color:#1565C0;">研究领域：</b>{', '.join(research[:4]) if research else 'N/A'}<br><br>
                                <b style="color:#1565C0;">站点简介：</b>{desc}
                            </div>
                        </div>
                    </div>
                </div>
                """

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=11,
                    color=color, weight=2.5,
                    fill=True, fillColor=color, fillOpacity=0.8,
                    popup=folium.Popup(popup_html, max_width=380, min_width=320),
                    tooltip=f"🔬 {name} · {country}"
                ).add_to(station_group)

            station_group.add_to(m)

        # 战略航道
        if f_show_routes:
            route_group = folium.FeatureGroup(name='🚢 战略航道')
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
            if os.path.exists(routes_path):
                with open(routes_path, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                for feat in routes_data.get('features', []):
                    props = feat.get('properties', {})
                    geom = feat.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'LineString':
                        coords = [[c[1], c[0]] for c in coords]
                    name = props.get('name', '')
                    color = props.get('color', '#FF6B35')
                    distance = props.get('distance', '')
                    duration = props.get('duration', '')
                    operator = props.get('operator', '')
                    open_months = props.get('open_months', '')
                    desc = props.get('description', '')

                    route_popup = f"""
                    <div style="min-width:280px;font-family:'Segoe UI',Arial,sans-serif;">
                        <h3 style="color:{color};margin:0 0 10px 0;font-weight:700;">🚢 {name}</h3>
                        <table style="width:100%;font-size:12px;border-collapse:collapse;">
                            <tr><td style="padding:4px 8px;color:#607D8B;font-weight:600;">航程</td><td style="padding:4px 8px;color:#1a1a2e;">{distance}</td></tr>
                            <tr><td style="padding:4px 8px;color:#607D8B;font-weight:600;">航行时间</td><td style="padding:4px 8px;color:#1a1a2e;">{duration}</td></tr>
                            <tr><td style="padding:4px 8px;color:#607D8B;font-weight:600;">主导方</td><td style="padding:4px 8px;color:#1a1a2e;">{operator}</td></tr>
                            <tr><td style="padding:4px 8px;color:#607D8B;font-weight:600;">通航期</td><td style="padding:4px 8px;color:#1a1a2e;">{open_months}</td></tr>
                        </table>
                        <div style="margin-top:8px;font-size:12px;color:#37474F;line-height:1.6;">{desc}</div>
                    </div>
                    """

                    folium.PolyLine(
                        locations=coords,
                        weight=5.5, color=color, opacity=0.9,
                        popup=folium.Popup(route_popup, max_width=300),
                        tooltip=f"🚢 {name} — {distance}"
                    ).add_to(route_group)
            route_group.add_to(m)

        # GDELT 热力
        if f_show_events and not grid_df.empty:
            event_group = folium.FeatureGroup(name='📊 地缘事件热力')
            year_col = next((c for c in ['Year_local', 'Year'] if c in grid_df.columns), None)
            if year_col:
                year_data = grid_df[grid_df[year_col] == f_year]
                lat_col = next((c for c in ['lat_grid', 'lat'] if c in year_data.columns), 'lat_grid')
                lon_col = next((c for c in ['lon_grid', 'lon'] if c in year_data.columns), 'lon_grid')

                heat_data = []
                for _, row in year_data.iterrows():
                    lat_v = row.get(lat_col, 0)
                    lon_v = row.get(lon_col, 0)
                    ev = row.get('EventCount', 1)
                    if lat_v and lon_v and -90 <= lat_v <= 90:
                        heat_data.append([lat_v, lon_v, ev])

                if heat_data:
                    plugins.HeatMap(
                        heat_data,
                        radius=18, blur=14, max_zoom=8,
                        gradient={0.3: 'blue', 0.55: 'lime', 0.75: 'orange', 1: 'red'}
                    ).add_to(event_group)
            event_group.add_to(m)

        # 冲突事件
        if f_show_conflicts:
            conf_group = folium.FeatureGroup(name='⚠️ 地缘冲突')
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            conf_path = os.path.join(geo_dir, 'conflicts.geojson')
            if os.path.exists(conf_path):
                with open(conf_path, 'r', encoding='utf-8') as f:
                    conf_data = json.load(f)
                for feat in conf_data.get('features', []):
                    props = feat.get('properties', {})
                    geom = feat.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'Point':
                        lat, lon = coords[1], coords[0]
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"<b>{props.get('name', '')}</b><br>{props.get('description', '')}",
                            tooltip=props.get('name', ''),
                            icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
                        ).add_to(conf_group)
            conf_group.add_to(m)

        # 军事基地
        if f_show_military:
            mil_group = folium.FeatureGroup(name='🏰 军事基地')
            military_bases = [
                {'name': '北极战略指挥中心', 'lon': -45.54, 'lat': 71.59, 'country': '俄罗斯'},
                {'name': '图勒空军基地', 'lon': -45.42, 'lat': 76.53, 'country': '美国/丹麦'},
                {'name': '阿勒特雷达站', 'lon': -82.53, 'lat': 82.5, 'country': '加拿大'},
                {'name': '希尔克内斯海军基地', 'lon': 30.04, 'lat': 69.97, 'country': '挪威'},
            ]
            for base in military_bases:
                folium.CircleMarker(
                    location=[base['lat'], base['lon']],
                    radius=9,
                    color='#B71C1C', weight=2,
                    fill=True, fillColor='#B71C1C', fillOpacity=0.75,
                    popup=f"<b>🏰 {base['name']}</b><br>所属: {base['country']}",
                    tooltip=f"🏰 {base['name']}"
                ).add_to(mil_group)
            mil_group.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        plugins.Fullscreen(position='topright').add_to(m)
        plugins.MousePosition(
            separator=' | ', empty_string='--',
            lng_first=True,
            number_format='.4f',
            prefix='坐标:'
        ).add_to(m)

        try:
            from streamlit_folium import st_folium
            st_folium(m, width=None, height=650, returned_objects=[])
        except ImportError:
            st.error("请安装 streamlit-folium: `pip install streamlit-folium`")

    st.markdown("""
    <div class="map-footer-bar">
        <div class="mf-text">🗺️ Folium 交互地图 | 点击标记查看详情 | 滚轮缩放 | © 大创专项</div>
        <div class="mf-badge">🔍 多底图切换 · 全屏支持</div>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------
# Tab3: 战略统计 — 科考站国家分布 + 事件趋势
# ----------------------------------------------------------------
with map_tab3:
    col_stat1, col_stat2 = st.columns(2)

    with col_stat1:
        st.markdown('<div class="content-block">', unsafe_allow_html=True)
        st.markdown("### 🏳️ 科考站国家分布")

        if country_counts:
            sorted_countries = sorted(country_counts.items(), key=lambda x: -x[1])
            total_s = sum(country_counts.values())
            country_colors = {
                '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
                '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
                '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
                '国际合作（多国）': '#607D8B', '加拿大': '#43A047',
            }

            for c_name, c_count in sorted_countries:
                color = country_colors.get(c_name, '#757575')
                pct = c_count / total_s * 100 if total_s > 0 else 0
                st.markdown(f"""
                <div class="country-bar-item">
                    <div class="cb-dot" style="background:{color}"></div>
                    <div class="cb-name">{c_name}</div>
                    <div class="cb-bar-bg">
                        <div class="cb-bar-fill" style="width:{pct:.0f}%;background:{color};"></div>
                    </div>
                    <div class="cb-count" style="color:{color}">{c_count}站</div>
                </div>
                """, unsafe_allow_html=True)

        # Plotly 条形图
        import plotly.graph_objects as go
        if country_counts:
            sorted_c = sorted(country_counts.items(), key=lambda x: -x[1])
            fig_country = go.Figure(go.Bar(
                y=[c[0] for c in sorted_c],
                x=[c[1] for c in sorted_c],
                orientation='h',
                marker_color=[country_colors.get(c[0], '#757575') for c in sorted_c],
                hovertemplate='%{y}: %{x}个科考站<extra></extra>'
            ))
            fig_country.update_layout(
                height=max(320, len(sorted_c) * 42),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=120, r=30, t=20, b=40),
                xaxis_title='科考站数量',
                yaxis_title='',
                showlegend=False,
                font=dict(color='rgba(255,255,255,0.7)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)',
                          title_font_color='rgba(255,255,255,0.5)'),
                yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
            )
            st.plotly_chart(fig_country, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_stat2:
        st.markdown('<div class="content-block">', unsafe_allow_html=True)
        st.markdown("### 📊 GDELT 地缘事件年度趋势")

        if not yc_df.empty:
            yearly = yc_df.groupby('year')['EventCount'].sum()
            tone_yearly = yc_df.groupby('year')['AvgTone'].mean()

            fig_dual = go.Figure()
            fig_dual.add_trace(go.Bar(
                x=yearly.index, y=yearly.values,
                name='地缘事件数',
                marker_color='rgba(229,57,53,0.6)',
                marker_line_color='#E53935',
                marker_line_width=1.5,
                hovertemplate='%{x}年: %{y}起事件<extra></extra>'
            ))
            fig_dual.add_trace(go.Scatter(
                x=tone_yearly.index, y=tone_yearly.values,
                name='情感指数',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=8, color='#FFD700'),
                hovertemplate='%{x}年情感: %{y:.2f}<extra></extra>'
            ))
            fig_dual.update_layout(
                xaxis_title='年份',
                yaxis=dict(title='地缘事件数', titlefont_color='rgba(255,255,255,0.6)',
                          tickfont_color='rgba(255,255,255,0.6)', gridcolor='rgba(255,255,255,0.06)'),
                yaxis2=dict(title='情感指数', titlefont_color='rgba(255,215,0,0.8)',
                           tickfont_color='rgba(255,215,0,0.8)',
                           overlaying='y', side='right', showgrid=False),
                template='plotly_dark',
                height=320,
                margin=dict(l=50, r=50, t=30, b=40),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                          font=dict(color='rgba(255,255,255,0.7)'),
                          bgcolor='rgba(0,0,0,0.3)', bordercolor='rgba(255,255,255,0.08)', borderwidth=1),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
            )
            fig_dual.update_xaxes(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)',
                                  tickfont_color='rgba(255,255,255,0.6)')
            st.plotly_chart(fig_dual, use_container_width=True)

            # 国家事件排名
            st.markdown("#### 🌐 国家事件活跃度排名")
            top5 = yc_df.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=False).head(6)
            total_ev = top5.sum()
            for code, count in top5.items():
                color = COUNTRY_COLORS.get(code, '#757575')
                pct = count / total_ev * 100 if total_ev > 0 else 0
                st.markdown(f"""
                <div class="country-bar-item">
                    <div class="cb-dot" style="background:{color}"></div>
                    <div class="cb-name">{COUNTRY_NAMES.get(code, code)}</div>
                    <div class="cb-bar-bg">
                        <div class="cb-bar-fill" style="width:{pct:.0f}%;background:{color};"></div>
                    </div>
                    <div class="cb-count" style="color:{color}">{count:,}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("GDELT 数据加载中...")

        st.markdown('</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------
# Tab4: GDELT 热力时序动画
# ----------------------------------------------------------------
with map_tab4:
    if not grid_df.empty:
        import plotly.graph_objects as go

        year_col = next((c for c in ['Year_local', 'Year'] if c in grid_df.columns), None)
        if year_col:
            years_avail = sorted(grid_df[year_col].unique())
            lat_col = next((c for c in ['lat_grid', 'lat'] if c in grid_df.columns), 'lat_grid')
            lon_col = next((c for c in ['lon_grid', 'lon'] if c in grid_df.columns), 'lon_grid')

            anim_year = st.select_slider(
                "🎬 选择年份（拖动播放）",
                options=years_avail,
                value=years_avail[-1] if years_avail else 2023
            )

            year_data_anim = grid_df[grid_df[year_col] == anim_year]
            ev_data_anim = year_data_anim[year_data_anim['EventCount'] >= 1]

            if not ev_data_anim.empty:
                year_total = int(ev_data_anim['EventCount'].sum())
                year_avg_tone = ev_data_anim['AvgTone'].mean() if 'AvgTone' in ev_data_anim.columns else 0

                stat_cols = st.columns(3)
                with stat_cols[0]:
                    st.metric(f"📊 {anim_year}年事件总数", f"{year_total:,}")
                with stat_cols[1]:
                    st.metric(f"⚡ 情感均值", f"{year_avg_tone:+.2f}",
                             delta="偏正面" if year_avg_tone > 0 else "偏负面")
                with stat_cols[2]:
                    top_code = ev_data_anim.groupby('CountryCode')['EventCount'].sum().idxmax() if not ev_data_anim.empty else 'N/A'
                    st.metric(f"🌐 最活跃国家", COUNTRY_NAMES.get(top_code, top_code))

                # 绘制热力散点
                fig_anim = go.Figure()

                # 北极参考线
                for lat in [66.5, 70, 75, 80]:
                    lons = np.linspace(-180, 180, 90)
                    lats = [lat] * len(lons)
                    fig_anim.add_trace(go.Scattergeo(
                        lon=lons, lat=lats, mode='lines',
                        line=dict(width=1, color='rgba(144,202,249,0.3)', dash='dash'),
                        showlegend=False, hoverinfo='skip'
                    ))

                # 热力散点
                for threshold, size, opacity in [(20, 10, 0.4), (10, 7, 0.5), (5, 5, 0.65), (1, 4, 0.8)]:
                    d = ev_data_anim[ev_data_anim['EventCount'] >= threshold]
                    if len(d) > 0:
                        fig_anim.add_trace(go.Scattergeo(
                            lon=d[lon_col].tolist(),
                            lat=d[lat_col].tolist(),
                            mode='markers',
                            marker=dict(
                                size=size,
                                color=d['EventCount'].tolist(),
                                colorscale='Reds',
                                opacity=opacity,
                                cmin=0, cmax=50,
                                colorbar=dict(title='事件数', len=0.3, y=0.5)
                            ),
                            hovertemplate='📊 %{marker.color}起事件<br>%{lat:.1f}°N, %{lon:.1f}°E<extra></extra>',
                            showlegend=False
                        ))

                fig_anim.update_layout(
                    geo=dict(
                        scope='world',
                        projection_type='orthographic',
                        center=dict(lat=75, lon=-30),
                        showland=True,
                        landcolor='rgba(220,235,250,0.9)',
                        showocean=True,
                        oceancolor='rgba(140,185,235,0.6)',
                        showcountries=True,
                        countrycolor='rgba(150,175,210,0.4)',
                        showcoastlines=True,
                        coastlinecolor='rgba(130,160,195,0.5)',
                        coastlinewidth=0.8,
                        showframe=False,
                        bgcolor='rgba(6,9,18,0)',
                        lataxis_range=[55, 90],
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=30),
                    height=560,
                    showlegend=False
                )
                st.plotly_chart(fig_anim, use_container_width=True)
            else:
                st.info(f"{anim_year}年暂无事件数据")

            # 年度趋势对比
            st.markdown("#### 📈 各年度事件总量对比")
            yearly_all = yc_df.groupby('year')['EventCount'].sum() if not yc_df.empty else pd.Series()
            if not yearly_all.empty:
                fig_year_comp = go.Figure(go.Bar(
                    x=yearly_all.index, y=yearly_all.values,
                    marker_color=['#E53935' if y == anim_year else '#1E88E5' for y in yearly_all.index],
                    hovertemplate='%{x}年: %{y}起事件<extra></extra>'
                ))
                fig_year_comp.update_layout(
                    height=280,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=50, r=20, t=20, b=40),
                    xaxis_title='年份',
                    yaxis_title='事件总数',
                    font=dict(color='rgba(255,255,255,0.7)'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
                )
                st.plotly_chart(fig_year_comp, use_container_width=True)
    else:
        st.info("GDELT 数据加载中...")


# ----------------------------------------------------------------
# Tab5: 国家关系网络
# ----------------------------------------------------------------
with map_tab5:
    import plotly.graph_objects as go

    st.markdown('<div class="content-block">', unsafe_allow_html=True)
    st.markdown("### 🔗 大北极国家地缘博弈关系网络")

    period_choice = st.selectbox(
        "选择时期",
        ['all', '2018-2021', '2022-2024'],
        format_func=lambda x: {
            'all': '全部时期 (2018-2024)',
            '2018-2021': '2018-2021（相对稳定期）',
            '2022-2024': '2022-2024（俄乌冲突后）'
        }.get(x, x)
    )

    net_data_period = load_geopolitics_network(period_choice)

    nodes = net_data_period.get('nodes', [])
    links = net_data_period.get('links', [])

    if nodes and links:
        n = len(nodes)
        angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
        r = 1.6

        link_colors_map = {
            'cooperation': '#43A047',
            'competition': '#FF6B35',
            'confrontation': '#E53935'
        }
        rel_names = {
            'cooperation': '合作',
            'competition': '竞争',
            'confrontation': '对抗'
        }

        fig_net = go.Figure()

        for link in links:
            src, tgt = link.get('source'), link.get('target')
            if src in angles and tgt in angles:
                lx = [r * np.cos(angles[src]), r * np.cos(angles[tgt])]
                ly = [r * np.sin(angles[src]), r * np.sin(angles[tgt])]
                color = link_colors_map.get(link.get('relation', ''), '#757575')
                fig_net.add_trace(go.Scatter(
                    x=lx, y=ly, mode='lines',
                    line=dict(width=max(link.get('strength', 1) / 12, 1),
                             color=color),
                    hoverinfo='text',
                    text=f"{COUNTRY_NAMES.get(src, src)} — {COUNTRY_NAMES.get(tgt, tgt)}: {rel_names.get(link.get('relation', ''), '')} ({link.get('strength', 0)})",
                    showlegend=False
                ))

        node_x = [r * np.cos(angles[n['id']]) for n in nodes]
        node_y = [r * np.sin(angles[n['id']]) for n in nodes]
        node_colors = [COUNTRY_COLORS.get(n.get('country', ''), '#757575') for n in nodes]
        node_sizes = [28 if n.get('type') == 'country' else 18 for n in nodes]

        fig_net.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(size=node_sizes, color=node_colors,
                       line=dict(width=2.5, color='white')),
            text=[COUNTRY_NAMES.get(n['id'], n['id']) for n in nodes],
            textposition='middle center',
            textfont=dict(size=11, color='white', family='Arial'),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))

        fig_net.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            height=580,
            xaxis=dict(visible=False, range=[-3.2, 3.2]),
            yaxis=dict(visible=False, range=[-3.2, 3.2]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_net, use_container_width=True)

        # 图例
        rel_cols = st.columns(3)
        for i, (rel, color) in enumerate(link_colors_map.items()):
            with rel_cols[i]:
                st.markdown(f"""
                <div style="text-align:center;padding:0.6rem;background:rgba(255,255,255,0.04);
                            border-radius:10px;border:1px solid rgba(255,255,255,0.06);">
                    <div style="display:inline-block;width:30px;height:3px;background:{color};border-radius:2px;vertical-align:middle;"></div>
                    <span style="font-size:0.82rem;color:rgba(255,255,255,0.75);margin-left:6px;">{rel_names[rel]}</span>
                </div>
                """, unsafe_allow_html=True)

        # 关系统计
        st.markdown("#### 📊 关系类型统计")
        rel_counts = {}
        for link in links:
            r_type = link.get('relation', 'unknown')
            rel_counts[r_type] = rel_counts.get(r_type, 0) + 1

        if rel_counts:
            fig_rel_pie = go.Figure(go.Pie(
                labels=[rel_names.get(k, k) for k in rel_counts.keys()],
                values=list(rel_counts.values()),
                hole=0.45,
                marker_colors=[link_colors_map.get(k, '#757575') for k in rel_counts.keys()],
                textinfo='percent+label',
                hovertemplate='%{label}: %{value}组 (%{percent})<extra></extra>'
            ))
            fig_rel_pie.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True,
                legend=dict(
                    orientation='h', yanchor='bottom', y=-0.1,
                    xanchor='center', x=0.5,
                    font=dict(color='rgba(255,255,255,0.6)')
                )
            )
            st.plotly_chart(fig_rel_pie, use_container_width=True)

        # 关系详情表
        st.markdown("#### 📋 关系详情表")
        link_display = []
        for link in links:
            src, tgt = link.get('source'), link.get('target')
            link_display.append({
                '国家A': COUNTRY_NAMES.get(src, src),
                '国家B': COUNTRY_NAMES.get(tgt, tgt),
                '关系': rel_names.get(link.get('relation', ''), ''),
                '强度': link.get('strength', 0)
            })
        if link_display:
            link_df = pd.DataFrame(link_display).sort_values('强度', ascending=False)
            st.dataframe(link_df, use_container_width=True, hide_index=True)
    else:
        st.info("网络数据加载中...")

    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.markdown("""
<div class="map-footer-bar">
    <div class="mf-text">🗺️ 地图数据来源: INTERACT科考站数据库 · GDELT全球事件数据库 · GeoJSON地理数据 · © 大创专项 2025-2026</div>
    <div class="mf-badge">🌍 北极圈 66.5°N · 北纬55°-90°</div>
</div>
""", unsafe_allow_html=True)
