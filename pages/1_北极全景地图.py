"""
模块1：北极全景地图 — 巅峰之作
深色沉浸主题 v6.0 — 前沿3D + 交互地图
"""

import streamlit as st
import sys, os, json, folium, streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_stations, load_gdelt_data, load_geopolitics_network
from src.viz import ARCTIC_THEME, COUNTRY_NAMES, COUNTRY_COLORS, create_3d_globe_annotate

st.set_page_config(
    page_title="北极全景地图",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============ 全局 CSS ============
st.markdown("""
<style>
    :root {
        --bg: #060912;
        --bg2: #0a0e1a;
        --bg-card: #0f1729;
        --bg-card2: #151e30;
        --border: rgba(255,255,255,0.06);
        --text: rgba(255,255,255,0.92);
        --text2: rgba(255,255,255,0.62);
        --text3: rgba(255,255,255,0.32);
        --accent: #3b82f6;
        --accent2: #f97316;
    }
    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] {
        background: var(--bg) !important;
        padding: 0 !important;
    }
    section[data-testid="stMain"] > div {
        background: transparent !important;
        padding: 0 1rem !important;
        max-width: 100% !important;
    }
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
    }
    /* 全局文字 */
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li,
    section[data-testid="stMain"] td,
    section[data-testid="stMain"] th { color: var(--text) !important; }
    .stMarkdown p, .stMarkdown li { color: var(--text2) !important; }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important; padding: 10px 20px !important;
        font-weight: 700 !important; font-size: 0.9rem !important;
        color: var(--text2) !important; background: rgba(255,255,255,0.04) !important;
        border: 1px solid transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.08) !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(249,115,22,0.18) !important;
        color: #fb923c !important;
        border-color: rgba(249,115,22,0.4) !important;
    }
    [data-testid="stMetricValue"] { color: var(--text) !important; }
    [data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: 0.78rem !important; }
    [data-testid="stCaption"] { color: var(--text3) !important; }
    .stCheckbox label { color: var(--text2) !important; }
    [data-baseweb="select"] > div { color: var(--text) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: var(--text) !important; }
    .stMultiSelect [data-baseweb="select"] > div { color: var(--text) !important; }
    hr { border: none !important; border-top: 1px solid var(--border) !important; }
    .stAlert { border-radius: 12px !important; }
    .streamlit-expander { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }
    .streamlit-expander summary { color: var(--text) !important; font-weight: 600 !important; }
    [data-testid="stSlider"] label { color: var(--text2) !important; }
    /* 自定义滚动条 */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }
</style>
""", unsafe_allow_html=True)


# ============ 页面头部 Hero ============
st.markdown("""
<div style="
    background: linear-gradient(135deg, #060912 0%, #0c1a35 40%, #1a0a10 100%);
    padding: 2rem 2rem 1.5rem 2rem;
    position: relative; overflow: hidden;
    border-bottom: 1px solid rgba(249,115,22,0.12);
    margin: 0 -1rem 1.5rem -1rem;
">
    <div style="position:absolute;top:-30%;right:0%;width:600px;height:600px;background:radial-gradient(circle,rgba(249,115,22,0.06) 0%,transparent 65%);pointer-events:none;"></div>
    <div style="position:absolute;bottom:-20%;left:5%;width:400px;height:400px;background:radial-gradient(circle,rgba(59,130,246,0.05) 0%,transparent 65%);pointer-events:none;"></div>
    <div style="position:relative;z-index:1;">
        <div style="display:inline-flex;align-items:center;gap:6px;background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.2);border-radius:20px;padding:5px 14px;font-size:0.72rem;color:rgba(251,146,60,0.9);font-weight:600;margin-bottom:0.8rem;">
            🗺️ 北极地缘与技术多要素联动可视化平台 · 旗舰模块
        </div>
        <h1 style="color:white !important;font-size:1.85rem;font-weight:800;margin:0 0 0.5rem 0;line-height:1.25;">
            🌍 北极全景地图
        </h1>
        <p style="color:rgba(255,255,255,0.5) !important;font-size:0.85rem;margin:0;">
            3D地球仪 · 交互地图 · GDELT热力叠加 · 国家关系网络 · 科考站详情 · 航道信息
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============ 核心指标卡 ============
try:
    stations_data = load_stations()
    station_count = len(stations_data.get('features', []))
    grid_df, yc_df = load_gdelt_data()
    total_events = int(yc_df['EventCount'].sum()) if not yc_df.empty else 0
    net_all = load_geopolitics_network('all')
    link_count = len(net_all.get('links', []))
    node_count = len(net_all.get('nodes', []))
except:
    station_count = 11; total_events = 0; link_count = 0; node_count = 0

stat_html = f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:1.5rem;">
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #3b82f6;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;">🔬</div>
        <div style="font-size:1.5rem;font-weight:800;color:#60a5fa;line-height:1;">{station_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">科考站</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #ef4444;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;">📊</div>
        <div style="font-size:1.5rem;font-weight:800;color:#f87171;line-height:1;">{total_events:,}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">地缘事件</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #a855f7;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;">🔗</div>
        <div style="font-size:1.5rem;font-weight:800;color:#c084fc;line-height:1;">{link_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">关系连线</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #22c55e;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;">🌐</div>
        <div style="font-size:1.5rem;font-weight:800;color:#4ade80;line-height:1;">{node_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">国家节点</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #f97316;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;">🛳️</div>
        <div style="font-size:1.5rem;font-weight:800;color:#fb923c;line-height:1;">3</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">核心航道</div>
    </div>
</div>
"""
st.markdown(stat_html, unsafe_allow_html=True)


# ============ 主标签页 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 3D极地全景",
    "🗺️ 交互地图",
    "📈 战略统计",
    "🧊 GDELT热力时序",
    "🔗 国家关系网络",
])


# =============================================
# Tab 1: 3D极地全景
# =============================================
with tab1:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.2rem;margin-bottom:1.2rem;">
    """, unsafe_allow_html=True)

    globe_controls = st.columns(3)
    with globe_controls[0]:
        highlight_arctic = st.checkbox("突出北极圈", value=True, key="globe_arctic")
    with globe_controls[1]:
        show_stations = st.checkbox("显示科考站", value=True, key="globe_stations")
    with globe_controls[2]:
        show_routes = st.checkbox("显示航道", value=True, key="globe_routes")

    # 3D Globe
    geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
    routes_data = None
    routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
    if os.path.exists(routes_path):
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_data = json.load(f)

    fig_globe = create_3d_globe_annotate(
        stations_data=stations_data if show_stations else None,
        routes_data=routes_data if show_routes else None,
        height=560
    )
    st.plotly_chart(fig_globe, use_container_width=True)

    st.markdown("""
    <div style="display:flex;gap:12px;margin-top:0.8rem;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#ef4444;border-radius:50%;display:inline-block;"></span>中国
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#3b82f6;border-radius:50%;display:inline-block;"></span>美国
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#b91c1c;border-radius:50%;display:inline-block;"></span>俄罗斯
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#f97316;border-radius:50%;display:inline-block;"></span>挪威
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#22c55e;border-radius:50%;display:inline-block;"></span>加拿大
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:3px;height:10px;background:#fb923c;display:inline-block;"></span>航道
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================
# Tab 2: 交互地图
# =============================================
with tab2:
    tile_options = {
        "深色卫星图 (CartoDB Dark)": "cartodbpositron",
        "浅色地图 (CartoDB Light)": "cartodbpositronnolabels",
        "深色地形 (Carto Dark Matter)": "CartoDB.dark_matter",
        "开放街道图 (OSM)": "OpenStreetMap",
        "深色地形 (Stamen Toner)": "Stamen Toner",
    }

    map_ctrl_cols = st.columns([1, 1, 1, 1])
    with map_ctrl_cols[0]:
        selected_tile = st.selectbox("底图", list(tile_options.keys()), index=2)
    with map_ctrl_cols[1]:
        center_lat = st.number_input("中心纬度", value=75.0, min_value=60.0, max_value=90.0, step=0.5, format="%.1f")
    with map_ctrl_cols[2]:
        center_lon = st.number_input("中心经度", value=0.0, min_value=-180.0, max_value=180.0, step=5.0, format="%.1f")
    with map_ctrl_cols[3]:
        zoom_level = st.slider("缩放级别", 2, 10, 3)

    try:
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles=tile_options[selected_tile],
            attr='深色北极地图'
        )

        # 添加科考站标记
        station_colors_map = {
            '中国': '#ef4444', '美国': '#3b82f6', '俄罗斯': '#b91c1c',
            '挪威': '#f97316', '丹麦': '#eab308', '芬兰': '#a855f7',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#22c55e',
        }

        for feat in stations_data.get('features', []):
            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            if not geom or 'coordinates' not in geom:
                continue
            lon, lat = geom['coordinates'][0], geom['coordinates'][1]
            country = props.get('country', '未知')
            name = props.get('name', '未知')
            color = station_colors_map.get(country, '#6b7280')

            popup_html = f"""
            <div style="width:280px;font-family:'Segoe UI',Arial,sans-serif;">
                <div style="background:{color};color:white;padding:8px 12px;font-weight:700;font-size:14px;border-radius:6px 6px 0 0;">
                    🔬 {name}
                </div>
                <div style="padding:12px;background:#f8fafc;font-size:12px;line-height:1.8;">
                    <table style="width:100%;border-collapse:collapse;">
                        <tr><td style="font-weight:600;color:#374151;padding:3px 0;width:70px;">国家</td><td style="color:#1f2937;">{country}</td></tr>
                        <tr><td style="font-weight:600;color:#374151;padding:3px 0;">坐标</td><td style="color:#1f2937;">{lat:.2f}°N, {lon:.2f}°E</td></tr>
                        <tr><td style="font-weight:600;color:#374151;padding:3px 0;">设立</td><td style="color:#1f2937;">{props.get('established', 'N/A')}</td></tr>
                        <tr><td style="font-weight:600;color:#374151;padding:3px 0;">技术</td><td style="color:#1f2937;">{props.get('tech_domain', 'N/A')}</td></tr>
                        <tr><td style="font-weight:600;color:#374151;padding:3px 0;">研究</td><td style="color:#1f2937;">{', '.join(props.get('research_focus', [])[:3])}</td></tr>
                    </table>
                    <div style="margin-top:8px;padding:8px;background:#e2e8f0;border-radius:4px;font-size:11px;color:#475569;">
                        {props.get('description', '暂无描述')}
                    </div>
                </div>
            </div>
            """

            folium.CircleMarker(
                location=[lat, lon],
                radius=9,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                weight=2,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{name} ({country})"
            ).add_to(m)

        # 添加航道线
        if routes_data:
            route_colors_map = {
                '东北航道': '#f97316', '西北航道': '#3b82f6', '跨北极航道': '#ef4444'
            }
            for feat in routes_data.get('features', []):
                props = feat.get('properties', {})
                geom = feat.get('geometry', {})
                if geom and 'coordinates' in geom:
                    coords = geom['coordinates']
                    route_name = props.get('name', '未知航道')
                    color = route_colors_map.get(route_name, '#6b7280')

                    popup_html = f"""
                    <div style="width:260px;font-family:'Segoe UI',Arial,sans-serif;">
                        <div style="background:{color};color:white;padding:8px 12px;font-weight:700;font-size:13px;border-radius:6px 6px 0 0;">
                            🚢 {route_name}
                        </div>
                        <div style="padding:12px;background:#f8fafc;font-size:12px;line-height:1.8;">
                            <table style="width:100%;">
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;width:65px;">起点</td><td style="color:#1f2937;">{props.get('start', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;">终点</td><td style="color:#1f2937;">{props.get('end', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;">航程</td><td style="color:#1f2937;">{props.get('distance', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;">航行时间</td><td style="color:#1f2937;">{props.get('duration', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;">主导方</td><td style="color:#1f2937;">{props.get('operator', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:#374151;padding:3px 0;">通航期</td><td style="color:#1f2937;">{props.get('open_months', 'N/A')}</td></tr>
                            </table>
                            <div style="margin-top:8px;padding:8px;background:#e2e8f0;border-radius:4px;font-size:11px;color:#475569;">
                                {props.get('description', '')}
                            </div>
                        </div>
                    </div>
                    """

                    folium.PolyLine(
                        locations=[[c[1], c[0]] for c in coords],
                        color=color,
                        weight=3,
                        opacity=0.8,
                        popup=folium.Popup(popup_html, max_width=280),
                        tooltip=route_name
                    ).add_to(m)

        # 添加北极圈
        arctic_circle_coords = []
        for i in range(361):
            import math
            lat_c = 66.5
            lon_c = i
            arctic_circle_coords.append([lat_c, lon_c])
        folium.PolyLine(
            locations=arctic_circle_coords,
            color='rgba(255,255,255,0.25)',
            weight=1.2,
            dash_array='6,4',
            tooltip='北极圈 (66.5°N)'
        ).add_to(m)

        m.get_root().html.add_child(folium.Element("""
        <style>
            .leaflet-popup-content-wrapper { border-radius: 10px !important; padding: 0 !important; overflow: hidden !important; box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important; }
            .leaflet-popup-content { margin: 0 !important; width: auto !important; }
            .leaflet-tooltip { background: rgba(10,14,26,0.9) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: white !important; border-radius: 8px !important; font-size: 12px !important; }
        </style>
        """))

        with st.container():
            components.html(
                m._repr_html_(),
                height=580,
                scrolling=False
            )
    except Exception as e:
        st.error(f"地图渲染出错: {e}")

    st.markdown("""
    <div style="display:flex;gap:16px;margin-top:0.8rem;flex-wrap:wrap;">
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#ef4444;border-radius:50%;display:inline-block;margin-right:4px;"></span>中国</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#3b82f6;border-radius:50%;display:inline-block;margin-right:4px;"></span>美国</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#b91c1c;border-radius:50%;display:inline-block;margin-right:4px;"></span>俄罗斯</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#f97316;border-radius:50%;display:inline-block;margin-right:4px;"></span>挪威</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#22c55e;border-radius:50%;display:inline-block;margin-right:4px;"></span>加拿大</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:20px;height:3px;background:#f97316;display:inline-block;margin-right:4px;"></span>东北航道</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:20px;height:3px;background:#3b82f6;display:inline-block;margin-right:4px;"></span>西北航道</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================
# Tab 3: 战略统计
# =============================================
with tab3:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.2rem;">
    """, unsafe_allow_html=True)

    import plotly.graph_objects as go

    # 国家科考站数量
    country_counts = {}
    for feat in stations_data.get('features', []):
        c = feat.get('properties', {}).get('country', '未知')
        country_counts[c] = country_counts.get(c, 0) + 1

    if country_counts:
        sorted_c = sorted(country_counts.items(), key=lambda x: -x[1])
        colors_c = {
            '中国': '#ef4444', '美国': '#3b82f6', '俄罗斯': '#b91c1c',
            '挪威': '#f97316', '丹麦': '#eab308', '芬兰': '#a855f7',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#22c55e',
        }

        stat_cols = st.columns(2)
        with stat_cols[0]:
            fig_c = go.Figure(go.Bar(
                y=[c[0] for c in sorted_c],
                x=[c[1] for c in sorted_c],
                orientation='h',
                marker_color=[colors_c.get(c[0], '#6b7280') for c in sorted_c],
                text=[c[1] for c in sorted_c],
                textposition='outside',
                hovertemplate='%{y}: %{x}个科考站<extra></extra>'
            ))
            fig_c.update_layout(
                title=dict(text='🇬🇸 各国北极科考站数量', font=dict(color='var(--text)', size=14)),
                height=max(350, len(sorted_c) * 48),
                margin=dict(l=140, r=50, t=40, b=40),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)',
                          title_font_color='rgba(255,255,255,0.5)'),
                yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
            )
            st.plotly_chart(fig_c, use_container_width=True)

        with stat_cols[1]:
            fig_pie = go.Figure(go.Pie(
                labels=[c[0] for c in sorted_c],
                values=[c[1] for c in sorted_c],
                hole=0.45,
                marker_colors=[colors_c.get(c[0], '#6b7280') for c in sorted_c],
                textinfo='percent+label',
                hovertemplate='%{label}: %{value}个 (%{percent})<extra></extra>'
            ))
            fig_pie.update_layout(
                title=dict(text='📊 科考站国家分布', font=dict(color='var(--text)', size=14)),
                height=350, margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)')
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # 科考站详细信息表
    st.markdown("#### 🔬 科考站详情列表")
    station_list = []
    for feat in stations_data.get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if not geom or 'coordinates' not in geom:
            continue
        lon, lat = geom['coordinates'][0], geom['coordinates'][1]
        station_list.append({
            '名称': props.get('name', ''),
            '国家': props.get('country', ''),
            '设立': props.get('established', ''),
            '坐标': f"{lat:.2f}°N, {lon:.2f}°E",
            '技术方向': props.get('tech_domain', ''),
            '研究领域': ', '.join(props.get('research_focus', [])[:2]),
        })
    if station_list:
        st.dataframe(pd.DataFrame(station_list), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================
# Tab 4: GDELT 热力时序
# =============================================
with tab4:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.2rem;">
    """, unsafe_allow_html=True)

    grid_df, yc_df = load_gdelt_data()

    # 年份滑块
    min_yr = int(yc_df['year'].min()) if not yc_df.empty and 'year' in yc_df.columns else 2018
    max_yr = int(yc_df['year'].max()) if not yc_df.empty and 'year' in yc_df.columns else 2024
    sel_years = st.slider("选择年份范围", min_yr, max_yr, (max(min_yr, 2020), max_yr), key="gdelt_slider")

    filtered = yc_df[
        (yc_df['year'] >= sel_years[0]) &
        (yc_df['year'] <= sel_years[1])
    ]

    import plotly.graph_objects as go

    stat_cols = st.columns(3)
    if not filtered.empty:
        with stat_cols[0]:
            st.metric("事件总数", f"{filtered['EventCount'].sum():,}")
        with stat_cols[1]:
            st.metric("平均情感值", f"{filtered['AvgTone'].mean():+.2f}")
        with stat_cols[2]:
            st.metric("涉及国家", filtered['CountryCode'].nunique())

    # 热力图
    if not filtered.empty and 'EventCategory' in filtered.columns:
        heat_data = filtered.pivot_table(
            values='EventCount', index='CountryCode',
            columns='year', aggfunc='sum'
        ).fillna(0)

        fig_heat = go.Figure(data=go.Heatmap(
            z=heat_data.values,
            x=[str(int(c)) for c in heat_data.columns],
            y=[COUNTRY_NAMES.get(c, c) for c in heat_data.index],
            colorscale='Reds', zmid=heat_data.values.mean(),
            text=np.round(heat_data.values, 0),
            texttemplate='%{text:.0f}', textfont=dict(color='white', size=10),
            hovertemplate='%{y} %{x}: %{z:.0f}起事件<extra></extra>'
        ))
        fig_heat.update_layout(
            height=max(350, len(heat_data) * 40),
            margin=dict(l=120, r=20, t=20, b=60),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.8)'),
            xaxis=dict(title='', tickfont_color='rgba(255,255,255,0.6)'),
            yaxis=dict(title='', tickfont_color='rgba(255,255,255,0.8)', ticks='outside'),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # 年度趋势
    if not filtered.empty:
        yearly = filtered.groupby('year')['EventCount'].sum()
        yearly_tone = filtered.groupby('year')['AvgTone'].mean()

        fig_yearly = go.Figure()
        fig_yearly.add_trace(go.Bar(
            x=yearly.index, y=yearly.values,
            name='事件数量', yaxis='y1',
            marker_color='#ef4444', opacity=0.8,
            hovertemplate='%{x}年: %{y}起事件<extra></extra>'
        ))
        fig_yearly.add_trace(go.Scatter(
            x=yearly_tone.index, y=yearly_tone.values,
            name='情感值', yaxis='y2',
            mode='lines+markers',
            line=dict(color='#fb923c', width=2.5),
            marker=dict(size=7),
            hovertemplate='%{x}年情感: %{y:.2f}<extra></extra>'
        ))
        fig_yearly.update_layout(
            xaxis_title='年份', yaxis_title='事件数量', yaxis2=dict(title='情感值', side='right', overlaying='y', showgrid=False),
            template='plotly_dark', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=380, margin=dict(l=60, r=60, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.8)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
        )
        st.plotly_chart(fig_yearly, use_container_width=True)

        # 国家事件排名
        st.markdown("#### 🏆 GDELT事件国家排名")
        country_events = filtered.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=False)
        fig_rank = go.Figure(go.Bar(
            x=[COUNTRY_NAMES.get(c, c) for c in country_events.index[:10]],
            y=country_events.values[:10],
            marker_color='#f87171',
            hovertemplate='%{x}: %{y}起<extra></extra>'
        ))
        fig_rank.update_layout(
            xaxis_title='国家', yaxis_title='事件数量',
            height=320, margin=dict(l=60, r=20, t=20, b=60),
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.8)'),
            xaxis=dict(tickfont_color='rgba(255,255,255,0.8)', tickangle=30),
            yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
        )
        st.plotly_chart(fig_rank, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================
# Tab 5: 国家关系网络
# =============================================
with tab5:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:16px;padding:1.2rem;">
    """, unsafe_allow_html=True)

    period_net = st.selectbox("选择时期", [
        ('all', '全部 (2018-2024)'),
        ('2018-2021', '2018-2021 相对稳定期'),
        ('2022-2024', '2022-2024 俄乌冲突后'),
    ], format_func=lambda x: x[1], index=0, key="net_period")

    net_data_p = load_geopolitics_network(period_net[0])

    import plotly.graph_objects as go
    import numpy as np

    nodes = net_data_p.get('nodes', [])
    links = net_data_p.get('links', [])
    n = len(nodes)

    if n > 0:
        angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
        r = 2.2

        rel_colors = {
            'cooperation': '#22c55e',
            'competition': '#f97316',
            'confrontation': '#ef4444',
        }

        for link in links:
            if link['source'] in angles and link['target'] in angles:
                lx = [r * np.cos(angles[link['source']]), r * np.cos(angles[link['target']])]
                ly = [r * np.sin(angles[link['source']]), r * np.sin(angles[link['target']])]
                fig_net.add_trace(go.Scatter(
                    x=lx, y=ly, mode='lines',
                    line=dict(width=link.get('strength', 1) / 8, color=rel_colors.get(link.get('relation', 'competition'), '#6b7280')),
                    hoverinfo='text',
                    text=f"{link['source']} — {link['target']}: {link.get('relation', 'unknown')}",
                    showlegend=False
                ))

        node_x = [r * np.cos(angles[n['id']]) for n in nodes]
        node_y = [r * np.sin(angles[n['id']]) for n in nodes]
        node_colors = [COUNTRY_COLORS.get(n.get('country', ''), '#6b7280') for n in nodes]
        node_sizes = [26 if n.get('type') == 'research' else 16 for n in nodes]

        # 构建 hover text
        node_texts = []
        for n in nodes:
            txt = f"<b>{n.get('name', n['id'])}</b>"
            txt += f"<br>国家: {n.get('country', 'N/A')}"
            txt += f"<br>类型: {n.get('type', 'N/A')}"
            if n.get('influence'):
                txt += f"<br>影响力: {n.get('influence')}"
            node_texts.append(txt)

        fig_net = go.Figure()
        for link in links:
            if link['source'] in angles and link['target'] in angles:
                lx = [r * np.cos(angles[link['source']]), r * np.cos(angles[link['target']])]
                ly = [r * np.sin(angles[link['source']]), r * np.sin(angles[link['target']])]
                fig_net.add_trace(go.Scatter(
                    x=lx, y=ly, mode='lines',
                    line=dict(width=link.get('strength', 1) / 8,
                             color=rel_colors.get(link.get('relation', 'competition'), '#6b7280')),
                    hoverinfo='text',
                    text=f"{link['source']} — {link['target']}: {link.get('relation', 'unknown')}",
                    showlegend=False
                ))

        fig_net.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(size=node_sizes, color=node_colors, line=dict(width=2.5, color='white')),
            text=[n.get('name', n['id']) for n in nodes],
            textposition='top center', textfont=dict(size=9, color='white'),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))

        fig_net.update_layout(
            margin=dict(l=20, r=20, t=20, b=20), height=520,
            xaxis=dict(visible=False, range=[-3.5, 3.5]),
            yaxis=dict(visible=False, range=[-3.5, 3.5]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_net, use_container_width=True)

        # 关系统计
        rel_stats = {}
        for link in links:
            r = link.get('relation', 'unknown')
            rel_stats[r] = rel_stats.get(r, 0) + 1

        rel_cn = {'cooperation': '🤝 合作', 'competition': '⚔️ 竞争', 'confrontation': '🚨 对抗'}
        rc_stat_cols = st.columns(3)
        for i, (rel, color) in enumerate(rel_colors.items()):
            with rc_stat_cols[i]:
                count = rel_stats.get(rel, 0)
                st.markdown(f"""
                <div style="text-align:center;padding:0.9rem;background:var(--bg-card2);border-radius:14px;border-top:3px solid {color};">
                    <div style="font-size:1.6rem;font-weight:800;color:{color};">{count}</div>
                    <div style="font-size:0.72rem;color:var(--text3);">{rel_cn.get(rel, rel)}关系</div>
                </div>
                """, unsafe_allow_html=True)

        # 关系详情表
        if links:
            st.markdown("#### 国家关系详情")
            rel_df = pd.DataFrame(links)
            rel_df_display = rel_df.copy()
            rel_df_display['relation_cn'] = rel_df_display['relation'].map(rel_cn)
            rel_df_display = rel_df_display[['source', 'target', 'relation_cn', 'strength']].rename(
                columns={'source': '国家A', 'target': '国家B', 'relation_cn': '关系类型', 'strength': '强度'}
            )
            st.dataframe(rel_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("暂无关系网络数据")
    st.markdown("</div>", unsafe_allow_html=True)


st.divider()
st.caption("🗺️ 北极全景地图 · v6.0 · 数据来源: GDELT / INTERACT / 各国公开资料")
