"""
模块3：大北极国家地缘战略格局
精细化矢量地图 + 大国博弈网络图谱 + 政策文本NLP分析
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_geopolitics_network, load_policy_texts, load_stations
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, CATEGORY_COLORS, CAT_LABELS

st.set_page_config(page_title="地缘战略格局", page_icon="🏛️", layout="wide")


# =========================================================================
# 全局样式
# =========================================================================
st.markdown("""
<style>
    .stApp [data-testid="stMainBlockContainer"] { background: #ffffff; }
    section[data-testid="stMain"] { background: #ffffff; }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown li, section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4 {
        color: #1e293b !important;
    }
    .page-hero {
        background: linear-gradient(135deg, #14532d 0%, #166534 50%, #15803d 100%);
        border-radius: 14px;
        padding: 36px 32px;
        margin-bottom: 28px;
    }
    .page-hero h1 { color: white !important; font-size: 1.6rem; font-weight: 800; margin: 0 0 6px 0; }
    .page-hero p { color: rgba(255,255,255,0.8) !important; font-size: 0.88rem; margin: 0; }
    .section-title {
        font-size: 1rem; font-weight: 700; color: #0f172a;
        margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0;
    }
    .kpi-card {
        background: white; border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.04);
        text-align: center;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .kpi-label { font-size: 0.75rem; color: #64748b; font-weight: 500; }
    .country-card {
        background: white; border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.04);
        border-left: 4px solid;
    }
    .country-card h4 { margin: 0 0 6px 0; font-size: 0.95rem; }
    .country-card p { margin: 0; font-size: 0.8rem; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# 侧边栏
# =========================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 12px 0 20px 0;">
            <div style="font-size:2.5rem;">🏛️</div>
            <div style="font-size:1.05rem; font-weight:700; color:white !important; margin-top:6px;">地缘战略格局</div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.55);">模块 3 · v5.0</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(255,255,255,0.1);">', unsafe_allow_html=True)

        pages_map = [
            ("🏠", "首页概览", "app.py"),
            ("🌡️", "气候时空监测", "pages/2_气候时空监测.py"),
            ("🏛️", "地缘战略格局", "pages/3_地缘战略格局.py"),
            ("⚙️", "技术竞争与合作", "pages/4_极地核心技术.py"),
            ("🛡️", "中国安全风险", "pages/5_中国安全风险.py"),
            ("🗄️", "数据中心工具", "pages/6_数据中心工具.py"),
            ("ℹ️", "关于本项目", "pages/7_关于本项目.py"),
        ]
        for icon, label, path in pages_map:
            st.page_link(path, label=label, icon=icon)

        st.divider()
        st.caption("© 2025-2026 大创专项")


render_sidebar()


# =========================================================================
# 页面头部
# =========================================================================
st.markdown("""
<div class="page-hero">
    <h1>🏛️ 大北极国家地缘战略格局</h1>
    <p>科考站 · 战略航道 · 地缘博弈网络 · 政策文本分析 · GDELT事件统计</p>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# KPI 指标
# =========================================================================
grid_df, yc_df = load_gdelt_data()
total_events = int(yc_df['EventCount'].sum()) if not yc_df.empty else 38500
avg_tone = float(yc_df['AvgTone'].mean()) if not yc_df.empty else 0

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#166534;">{total_events:,}</div>
    <div class="kpi-label">GDELT 北极事件（2018-2024）</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[1]:
    tone_label = "偏正面" if avg_tone > 0 else "偏负面"
    tone_color = "#059669" if avg_tone > 0 else "#dc2626"
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:{tone_color};">{avg_tone:.2f}</div>
    <div class="kpi-label">平均情感倾向（{tone_label}）</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[2]:
    top_country = "俄罗斯"
    if not yc_df.empty:
        top = yc_df.groupby('CountryCode')['EventCount'].sum().idxmax()
        top_country = COUNTRY_NAMES.get(top, top)
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#1565C0;">{top_country}</div>
    <div class="kpi-label">最活跃国家</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown("""
    <div class="kpi-card"><div class="kpi-value" style="color:#7c3aed;">14</div>
    <div class="kpi-label">博弈主体（国家+国际组织）</div></div>
    """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 主区域
# =========================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 地缘态势地图", "🔗 博弈关系网络", "📝 政策文本分析", "🔬 科考站详情", "📊 事件统计"
])


# -------------------------------------------------------------------------
# Tab 1: 精细化地图
# -------------------------------------------------------------------------
with tab1:
    st.markdown('<div class="section-title">🗺️ 大北极地缘战略态势地图</div>', unsafe_allow_html=True)
    st.caption("点击地图上的任意图标（科考站/冲突事件/航道）可查看详细信息，支持图层切换")

    col_ctl, col_map = st.columns([280, 1])

    with col_ctl:
        st.markdown("##### 🕹️ 图层控制")

        layer_all = st.checkbox("全部显示", value=True, key="lyr_all")
        show_stations = st.checkbox("科考站分布", value=True, key="lyr_stations")
        show_routes = st.checkbox("战略航道", value=True, key="lyr_routes")
        show_events = st.checkbox("地缘冲突事件", value=True, key="lyr_events")
        show_heat = st.checkbox("GDELT事件热力", value=True, key="lyr_heat")

        if layer_all:
            show_stations = show_routes = show_events = show_heat = True

        st.markdown("##### 🌐 国家筛选")
        country_filter = st.multiselect(
            "选择国家",
            options=['RUS', 'USA', 'CHN', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL'],
            default=['RUS', 'USA', 'CHN', 'NOR', 'CAN'],
            format_func=lambda x: COUNTRY_NAMES.get(x, x),
            key="country_filter"
        )

        st.markdown("##### 📅 时间选择")
        year_select = st.slider("选择年份", 2018, 2024, 2023, key="year_slider")

        st.markdown("##### 📖 图例说明")
        st.markdown("""
        | 颜色 | 含义 |
        |------|------|
        | 🔴 中国 | 黄河站等 |
        | 🔵 美国 | Utqiagvik站等 |
        | 🟠 挪威 | 斯瓦尔巴站等 |
        | 🟤 俄罗斯 | 极点站、进步站等 |
        | 🟢 加拿大 | 巴尼奥站 |
        | 🟡 航道线 | 三大北极航道 |
        """)

    with col_map:
        import folium
        from folium import plugins
        import json

        m = folium.Map(
            location=[75, 30],
            zoom_start=3,
            tiles=None,
            prefer_canvas=True
        )

        # 底图选项
        folium.TileLayer('cartodbpositron', name='卫星图').add_to(m)
        folium.TileLayer('OpenStreetMap', name='街道图').add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='卫星影像'
        ).add_to(m)

        # ---- 科考站 ----
        if show_stations:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            stations_path = os.path.join(geo_dir, 'research_stations.geojson')
            if os.path.exists(stations_path):
                with open(stations_path, 'r', encoding='utf-8') as f:
                    stations_data = json.load(f)

                station_group = folium.FeatureGroup(name='🏔️ 科考站')

                for feature in stations_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue

                    lon, lat = geom['coordinates'][0], geom['coordinates'][1]
                    country = props.get('country', '未知')
                    if country_filter:
                        country_code = props.get('country_code', '')
                        name_map = {'CHN': '中国', 'RUS': '俄罗斯', 'USA': '美国',
                                   'NOR': '挪威', 'CAN': '加拿大', 'DNK': '丹麦',
                                   'FIN': '芬兰', 'SWE': '瑞典', 'ISL': '冰岛'}
                        cname = name_map.get(country_code, country)
                        if cname not in [COUNTRY_NAMES.get(c, c) for c in country_filter]:
                            continue

                    color_map = {
                        '中国': '#dc2626', '美国': '#1565C0', '俄罗斯': '#991b1b',
                        '挪威': '#ea580c', '丹麦': '#d97706', '芬兰': '#7c3aed',
                        '瑞典': '#0891b2', '冰岛': '#78716c', '日本': '#92400e',
                        '国际合作（多国）': '#475569', '丹麦/美国': '#d97706',
                        '挪威/国际': '#ea580c', '加拿大': '#16a34a'
                    }
                    color = color_map.get(country, '#757575')
                    name = props.get('name', '未知')
                    established = props.get('established', 'N/A')
                    research = props.get('research_focus', [])
                    tech_domain = props.get('tech_domain', '未知')
                    desc = props.get('description', '')

                    # 精细化popup
                    popup_html = f"""
                    <div style="width:320px; font-family:'Segoe UI',sans-serif;">
                        <div style="background:{color};color:white;padding:12px 16px;border-radius:8px 8px 0 0;margin:-10px -10px 10px -10px;">
                            <div style="font-size:1.1rem;font-weight:700;">{name}</div>
                            <div style="font-size:0.75rem;opacity:0.9;margin-top:2px;">{name}</div>
                        </div>
                        <table style="width:100%;border-collapse:collapse;font-size:12px;">
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:5px 0;color:#64748b;width:80px;"><b>所属国</b></td>
                                <td style="padding:5px 0;color:#1e293b;font-weight:600;">{country}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:5px 0;color:#64748b;"><b>设立年份</b></td>
                                <td style="padding:5px 0;color:#1e293b;">{established}年</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:5px 0;color:#64748b;"><b>坐标</b></td>
                                <td style="padding:5px 0;color:#1e293b;">{lat:.2f}°N, {lon:.2f}°E</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:5px 0;color:#64748b;"><b>研究类型</b></td>
                                <td style="padding:5px 0;color:#1e293b;">{props.get('type', '科考站')}</td>
                            </tr>
                            <tr>
                                <td style="padding:5px 0;color:#64748b;vertical-align:top;"><b>研究领域</b></td>
                                <td style="padding:5px 0;color:#1e293b;">
                                    {''.join([f'<span style="background:#f1f5f9;color:#475569;padding:2px 6px;border-radius:4px;font-size:11px;margin-right:4px;display:inline-block;">{r}</span>' for r in research[:4]])}
                                </td>
                            </tr>
                        </table>
                        <div style="margin-top:10px;padding:10px;background:#f8fafc;border-radius:6px;font-size:11px;color:#475569;line-height:1.6;">
                            <b style="color:#1e293b;">技术方向：</b>{tech_domain}<br><br>
                            <b style="color:#1e293b;">简介：</b>{desc}
                        </div>
                    </div>
                    """

                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=10,
                        color=color,
                        weight=2.5,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7,
                        popup=folium.Popup(popup_html, max_width=350, min_width=300),
                        tooltip=f"🏔️ {name} ({country})"
                    ).add_to(station_group)

                station_group.add_to(m)

        # ---- 战略航道 ----
        if show_routes:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
            if os.path.exists(routes_path):
                with open(routes_path, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                route_group = folium.FeatureGroup(name='🚢 战略航道')

                for feature in routes_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'LineString':
                        coords = [[c[1], c[0]] for c in coords]
                    name = props.get('name', '')
                    name_en = props.get('name_en', '')
                    color = props.get('color', '#FF6B35')
                    desc = props.get('description', '')
                    distance = props.get('distance', 'N/A')
                    duration = props.get('duration', 'N/A')
                    operator = props.get('operator', 'N/A')
                    open_months = props.get('open_months', 'N/A')

                    popup_html = f"""
                    <div style="width:300px;font-family:'Segoe UI',sans-serif;">
                        <div style="background:{color};color:white;padding:12px 16px;border-radius:8px 8px 0 0;margin:-10px -10px 10px -10px;">
                            <div style="font-size:1.05rem;font-weight:700;">🚢 {name}</div>
                            <div style="font-size:0.75rem;opacity:0.85;">{name_en}</div>
                        </div>
                        <table style="width:100%;border-collapse:collapse;font-size:12px;">
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;width:80px;"><b>起点-终点</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{props.get('start','')} → {props.get('end','')}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;"><b>航程</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{distance}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;"><b>航行时间</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{duration}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;"><b>主导方</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{operator}</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#64748b;"><b>通航期</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{open_months}</td>
                            </tr>
                        </table>
                        <div style="margin-top:10px;padding:10px;background:#f8fafc;border-radius:6px;font-size:11px;color:#475569;line-height:1.6;">
                            {desc}
                        </div>
                    </div>
                    """

                    folium.PolyLine(
                        locations=coords,
                        weight=4.5,
                        color=color,
                        opacity=0.85,
                        popup=folium.Popup(popup_html, max_width=320),
                        tooltip=f"🚢 {name}"
                    ).add_to(route_group)
                route_group.add_to(m)

        # ---- 地缘冲突事件 ----
        if show_events:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            conf_path = os.path.join(geo_dir, 'conflicts.geojson')
            if os.path.exists(conf_path):
                with open(conf_path, 'r', encoding='utf-8') as f:
                    conf_data = json.load(f)
                event_group = folium.FeatureGroup(name='⚡ 地缘冲突事件')

                cat_colors = {
                    'tech_competition': '#7c3aed',
                    'arctic_shipping': '#ea580c',
                    'arctic_resource': '#ca8a04',
                    'arctic_military': '#dc2626',
                    'arctic_cooperation': '#16a34a',
                    'arctic_infrastructure': '#0891b2',
                    'arctic_governance': '#64748b',
                    'arctic_research': '#1565C0',
                }
                cat_labels = {
                    'tech_competition': '技术竞争',
                    'arctic_shipping': '航道航运',
                    'arctic_resource': '资源开发',
                    'arctic_military': '军事活动',
                    'arctic_cooperation': '科技合作',
                    'arctic_infrastructure': '基础设施',
                    'arctic_governance': '治理规则',
                    'arctic_research': '极地科考',
                }

                for feature in conf_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    lat, lon = coords[1], coords[0]
                    cat = props.get('category', 'general')
                    color = cat_colors.get(cat, '#757575')
                    title = props.get('title', '')
                    year = props.get('year', 'N/A')
                    severity = props.get('severity', 5)
                    countries = props.get('countries', [])
                    country_names = [COUNTRY_NAMES.get(c, c) for c in countries]
                    desc = props.get('description', '')

                    # 严重程度圆圈大小
                    radius = 6 + severity * 0.8

                    popup_html = f"""
                    <div style="width:300px;font-family:'Segoe UI',sans-serif;">
                        <div style="background:{color};color:white;padding:12px 16px;border-radius:8px 8px 0 0;margin:-10px -10px 10px -10px;">
                            <div style="font-size:1rem;font-weight:700;">⚡ {title}</div>
                            <div style="font-size:0.72rem;opacity:0.85;margin-top:2px;">{year}年 · {cat_labels.get(cat, cat)}</div>
                        </div>
                        <table style="width:100%;border-collapse:collapse;font-size:12px;">
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;width:70px;"><b>事件类型</b></td>
                                <td style="padding:6px 0;">
                                    <span style="background:{color}22;color:{color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">
                                        {cat_labels.get(cat, cat)}
                                    </span>
                                </td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;"><b>严重程度</b></td>
                                <td style="padding:6px 0;">
                                    <span style="font-weight:700;color:{'#dc2626' if severity >= 7 else '#ea580c' if severity >= 5 else '#16a34a'};">{severity}/10</span>
                                    <span style="color:#94a3b8;">（{'高' if severity >= 7 else '中' if severity >= 5 else '低'}风险）</span>
                                </td>
                            </tr>
                            <tr style="border-bottom:1px solid #eee;">
                                <td style="padding:6px 0;color:#64748b;"><b>涉及国家</b></td>
                                <td style="padding:6px 0;color:#1e293b;">{', '.join(country_names)}</td>
                            </tr>
                        </table>
                        <div style="margin-top:10px;padding:10px;background:#f8fafc;border-radius:6px;font-size:11px;color:#475569;line-height:1.6;">
                            {desc}
                        </div>
                    </div>
                    """

                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=radius,
                        color=color,
                        weight=2,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.5,
                        popup=folium.Popup(popup_html, max_width=320),
                        tooltip=f"⚡ {title}"
                    ).add_to(event_group)
                event_group.add_to(m)

        # ---- GDELT事件热力图 ----
        if show_heat and not grid_df.empty:
            try:
                year_col = 'Year_local' if 'Year_local' in grid_df.columns else 'year'
                year_data = grid_df[grid_df[year_col] == year_select]
                if not year_data.empty:
                    lat_col = 'lat_grid' if 'lat_grid' in year_data.columns else 'lat'
                    lon_col = 'lon_grid' if 'lon_grid' in year_data.columns else 'lon'
                    heat_data = [
                        [float(row.get(lat_col, 0)), float(row.get(lon_col, 0)), float(row.get('EventCount', 1))]
                        for _, row in year_data.iterrows()
                    ]
                    heat_group = folium.FeatureGroup(name='🌡️ GDELT事件热力')
                    plugins.HeatMap(
                        heat_data, radius=22, blur=15,
                        gradient={0.3: 'blue', 0.55: 'lime', 0.8: 'orange', 1: 'red'}
                    ).add_to(heat_group)
                    heat_group.add_to(m)
            except Exception:
                pass

        # 图层控制
        folium.LayerControl(collapsed=False, position='topright').add_to(m)
        plugins.Fullscreen(position='topleft').add_to(m)
        plugins.MousePosition(
            position='bottomright',
            separator=" | ",
            prefix="坐标: ",
            num_digits=2
        ).add_to(m)

        try:
            from streamlit_folium import st_folium
            st_folium(m, width=None, height=580, returned_objects=[])
        except ImportError:
            st.error("请安装 streamlit-folium: pip install streamlit-folium")


# -------------------------------------------------------------------------
# Tab 2: 博弈关系网络
# -------------------------------------------------------------------------
with tab2:
    st.markdown('<div class="section-title">🔗 大北极国家地缘博弈关系网络图谱</div>', unsafe_allow_html=True)
    st.caption("节点大小=影响力 | 线条颜色=关系类型 | 线宽=关系强度")

    period_select = st.selectbox(
        "选择历史时期",
        ["all", "2018-2021", "2022-2024"],
        format_func=lambda x: "全部时期" if x == "all" else x,
        key="period_select"
    )
    layout_style = st.selectbox(
        "网络布局",
        ["circular", "tiered"],
        format_func=lambda x: {"circular": "圆形布局", "tiered": "分层布局"}.get(x, x),
        key="layout_style"
    )

    # 图例
    leg_cols = st.columns(3)
    with leg_cols[0]:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;font-size:0.82rem;">
            <div style="width:32px;height:3px;background:#16a34a;border-radius:2px;"></div>
            <span>合作关系</span>
        </div>""", unsafe_allow_html=True)
    with leg_cols[1]:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;font-size:0.82rem;">
            <div style="width:32px;height:3px;background:#ea580c;border-radius:2px;border-style:dashed;"></div>
            <span>竞争关系</span>
        </div>""", unsafe_allow_html=True)
    with leg_cols[2]:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;font-size:0.82rem;">
            <div style="width:32px;height:3px;background:#dc2626;border-radius:2px;border-style:dotted;"></div>
            <span>对抗关系</span>
        </div>""", unsafe_allow_html=True)

    try:
        from src.viz import create_network_graph
        net_data = load_geopolitics_network(period_select)
        fig_net = create_network_graph(net_data, layout_style=layout_style)
        st.plotly_chart(fig_net, use_container_width=True)
    except Exception as e:
        st.error(f"网络图加载失败: {e}")

    # 网络统计
    st.markdown("#### 网络结构统计")
    stat_cols = st.columns(4)
    try:
        net_data = load_geopolitics_network(period_select)
        coop_count = sum(1 for l in net_data['links'] if l['relation'] == 'cooperation')
        conflict_count = sum(1 for l in net_data['links'] if l['relation'] in ('competition', 'confrontation'))
        with stat_cols[0]:
            st.metric("节点数", len(net_data['nodes']))
        with stat_cols[1]:
            st.metric("关系数", len(net_data['links']))
        with stat_cols[2]:
            st.metric("合作关系", coop_count)
        with stat_cols[3]:
            st.metric("竞争/对抗", conflict_count)
    except Exception:
        st.info("网络数据加载中...")

    # 详细关系表
    st.markdown("#### 核心关系详情")
    try:
        net_data = load_geopolitics_network(period_select)
        rel_df = pd.DataFrame(net_data['links'])
        rel_df['source_name'] = rel_df['source'].map(lambda x: COUNTRY_NAMES.get(x, x))
        rel_df['target_name'] = rel_df['target'].map(lambda x: COUNTRY_NAMES.get(x, x))
        rel_df['relation_cn'] = rel_df['relation'].map({'cooperation': '合作', 'competition': '竞争', 'confrontation': '对抗'})
        display_df = rel_df[['source_name', 'relation_cn', 'target_name', 'strength']].rename(
            columns={'source_name': '主体A', 'relation_cn': '关系', 'target_name': '主体B', 'strength': '强度'}
        ).sort_values('强度', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    except Exception:
        st.info("关系数据加载中...")


# -------------------------------------------------------------------------
# Tab 3: 政策文本分析
# -------------------------------------------------------------------------
with tab3:
    st.markdown('<div class="section-title">📝 各国北极政策文本关键词分析</div>', unsafe_allow_html=True)
    st.caption("基于各国北极政策白皮书文本，提取高频关键词并进行情感分析")

    try:
        from src.viz import create_sentiment_chart, create_word_freq_chart
        policy_texts = load_policy_texts()
        fig_sent = create_sentiment_chart(policy_texts, height=320)
        st.plotly_chart(fig_sent, use_container_width=True)

        st.markdown("""
        **情感分析解读：**
        中国的北极政策文本情感值最高，反映合作导向的治理观；俄罗斯近年情感值转负，体现军事对抗性增强；
        北欧国家普遍呈正面倾向，强调环境保护与国际合作。
        """)

        st.markdown("#### 政策关键词词频对比")
        fig_wc = create_word_freq_chart(policy_texts, height=380)
        st.plotly_chart(fig_wc, use_container_width=True)
    except Exception:
        st.info("政策文本数据加载中...")

    # 各国政策核心主张
    st.markdown("#### 各国政策核心主张")
    country_data = {
        'RUS': ('俄罗斯', '#dc2626', '强调北极主权、安全与航道管控，通过军事部署强化存在，核动力破冰船为战略工具'),
        'USA': ('美国', '#1565C0', '坚持航行自由，将中俄定位北极挑战者，通过国防部北极战略应对竞争'),
        'CHN': ('中国', '#dc2626', '定位『近北极国家』与『利益攸关方』，倡导『人类命运共同体』理念，侧重科技合作'),
        'NOR': ('挪威', '#ea580c', '推动巴伦支海合作与环境保护，主张以国际法框架解决争端'),
        'CAN': ('加拿大', '#16a34a', '强调北极主权和西北航道管辖，注重原住民权益和环境保护'),
        'DNK': ('丹麦', '#d97706', '通过格陵兰发挥北极影响力，推动气候科学和北极治理'),
    }
    for i, (code, (name, color, desc)) in enumerate(country_data.items()):
        col = st.columns(3)[i % 3]
        with col:
            st.markdown(f"""
            <div class="country-card" style="border-left-color:{color};">
                <h4 style="color:{color};">{name}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------------------
# Tab 4: 科考站详情
# -------------------------------------------------------------------------
with tab4:
    st.markdown('<div class="section-title">🔬 大北极科考站详细信息</div>', unsafe_allow_html=True)
    st.caption("点击展开科考站名称可查看详细信息，包括所属国、设立年份、研究领域和技术方向")

    geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
    stations_path = os.path.join(geo_dir, 'research_stations.geojson')
    if os.path.exists(stations_path):
        with open(stations_path, 'r', encoding='utf-8') as f:
            stations_data = json.load(f)
    else:
        stations_data = load_stations()

    features = stations_data.get('features', [])
    if not features:
        st.info("科考站数据加载中...")
    else:
        all_countries = sorted(set(f.get('properties', {}).get('country', '未知') for f in features))
        country_filter_st = st.multiselect(
            "按国家筛选",
            all_countries,
            default=all_countries,
            key="station_country_filter"
        )
        filtered_features = [f for f in features
                           if f.get('properties', {}).get('country', '未知') in country_filter_st]

        color_map = {
            '中国': '#dc2626', '美国': '#1565C0', '俄罗斯': '#991b1b',
            '挪威': '#ea580c', '丹麦': '#d97706', '芬兰': '#7c3aed',
            '瑞典': '#0891b2', '冰岛': '#78716c', '日本': '#92400e',
            '国际合作（多国）': '#475569', '丹麦/美国': '#d97706',
            '挪威/国际': '#ea580c', '加拿大': '#16a34a'
        }

        for feature in filtered_features:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            name = props.get('name', '未知')
            country = props.get('country', '未知')
            established = props.get('established', 'N/A')
            research = props.get('research_focus', [])
            tech = props.get('tech_domain', '未知')
            desc = props.get('description', '')
            lon, lat = geom.get('coordinates', [0, 0])[0], geom.get('coordinates', [0, 0])[1]
            color = color_map.get(country, '#757575')

            with st.expander(f"🏔️ **{name}**  ({country})"):
                info_cols = st.columns([1, 2])
                with info_cols[0]:
                    st.markdown(f"""
                    **所属国：** {country}<br>
                    **设立年份：** {established}年<br>
                    **坐标：** {lat:.2f}°N, {lon:.2f}°E<br>
                    **技术方向：** {tech}
                    """)
                with info_cols[1]:
                    st.markdown(f"**研究领域：**")
                    if research:
                        for r in research:
                            st.markdown(f"  • {r}")
                    st.markdown(f"**简介：** {desc}")

        # 统计
        st.markdown("#### 科考站统计概览")
        if features:
            country_counts = {}
            for f in features:
                c = f.get('properties', {}).get('country', '未知')
                country_counts[c] = country_counts.get(c, 0) + 1
            stat_cc = st.columns(len(country_counts))
            for i, (country, count) in enumerate(sorted(country_counts.items(), key=lambda x: -x[1])):
                color = color_map.get(country, '#757575')
                with stat_cc[i]:
                    st.metric(country, count)


# -------------------------------------------------------------------------
# Tab 5: GDELT 事件统计
# -------------------------------------------------------------------------
with tab5:
    st.markdown('<div class="section-title">📊 GDELT 事件统计分析</div>', unsafe_allow_html=True)

    if not yc_df.empty:
        import plotly.graph_objects as go

        # 年度趋势
        st.markdown("##### 年度趋势")
        yearly = yc_df.groupby('year')['EventCount'].sum()
        fig_yr = go.Figure(go.Bar(
            x=yearly.index, y=yearly.values,
            marker_color='#166534',
            hovertemplate='%{x}年: %{y}起事件<extra></extra>'
        ))
        fig_yr.update_layout(
            xaxis_title='年份', yaxis_title='事件总数',
            template='plotly_white', height=300,
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_yr, use_container_width=True)

        # 国家排名
        st.markdown("##### 国家事件排名")
        country_events = yc_df.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=True)
        fig_rank = go.Figure(go.Bar(
            x=country_events.values,
            y=[COUNTRY_NAMES.get(c, c) for c in country_events.index],
            orientation='h',
            marker_color=[COUNTRY_COLORS.get(c, '#757575') for c in country_events.index],
            hovertemplate='%{y}: %{x}起<extra></extra>'
        ))
        fig_rank.update_layout(
            xaxis_title='事件总数', yaxis_title='国家',
            height=300, margin=dict(l=100, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # 情感趋势
        st.markdown("##### 情感倾向年度变化")
        tone_yearly = yc_df.groupby('year')['AvgTone'].mean()
        fig_tone = go.Figure()
        fig_tone.add_trace(go.Scatter(
            x=tone_yearly.index, y=tone_yearly.values,
            mode='lines+markers', name='平均情感值',
            line=dict(color='#ea580c', width=2.5),
            marker=dict(size=6), fill='tozeroy', fillcolor='rgba(234,88,12,0.1)'
        ))
        fig_tone.add_hline(y=0, line_dash='dash', line_color='gray')
        fig_tone.update_layout(
            xaxis_title='年份', yaxis_title='平均情感值',
            template='plotly_white', height=300,
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_tone, use_container_width=True)
    else:
        st.info("GDELT 数据加载中...")


st.divider()
st.caption("数据来源: GDELT全球事件数据库 · 北极政策白皮书 · INTERACT科考站数据库")
