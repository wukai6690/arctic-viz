"""
模块X：北极战略态势全景地图
独立地图模块 — 融合Plotly3D地球 + Folium交互地图 + PyDeck3D四视角
采用前沿可视化技术，全屏沉浸式体验
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_stations, load_geopolitics_network
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS

st.set_page_config(page_title="北极全景地图", page_icon="🗺️", layout="wide")


# ============ 全局样式 ============
st.markdown("""
<style>
    /* 全屏地图页 — 极简顶部导航 */
    .map-page-header {
        background: linear-gradient(135deg, #0a0f1e 0%, #1a237e 50%, #0D47A1 100%);
        padding: 1rem 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 0;
        box-shadow: 0 6px 30px rgba(0,0,0,0.3);
    }
    .map-page-header h1 { color: white !important; font-size: 1.6rem !important; font-weight: 800 !important; margin: 0 0 0.2rem 0 !important; }
    .map-page-header p { color: rgba(255,255,255,0.7) !important; font-size: 0.8rem !important; margin: 0 !important; }

    /* 主布局 */
    section[data-testid="stMain"] { background: #0a0f1e !important; }
    section[data-testid="stMain"] > div { background: #0a0f1e !important; padding: 0 !important; }

    /* 全宽地图容器 */
    .map-container {
        border-radius: 0;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    }

    /* 地图控制面板 */
    .control-panel {
        background: rgba(10, 15, 30, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.2rem;
        color: white !important;
        height: 100%;
    }
    .control-panel h3 { color: white !important; font-size: 0.9rem !important; font-weight: 700 !important; margin: 0 0 0.8rem 0 !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; padding-bottom: 0.5rem !important; }
    .control-panel h4 { color: rgba(255,255,255,0.85) !important; font-size: 0.78rem !important; font-weight: 600 !important; margin: 0.8rem 0 0.4rem 0 !important; }
    .control-panel p, .control-panel span, .control-panel div, .control-panel label { color: rgba(255,255,255,0.75) !important; }

    /* 切换开关 */
    .toggle-item {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .toggle-item:last-child { border-bottom: none; }

    /* 图例项 */
    .legend-item-map {
        display: flex; align-items: center; gap: 8px;
        font-size: 0.75rem; color: rgba(255,255,255,0.8);
        padding: 3px 0;
    }
    .legend-dot-map { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .legend-line-map { width: 22px; height: 3px; border-radius: 2px; flex-shrink: 0; }

    /* 统计数据 */
    .stat-box {
        background: rgba(255,255,255,0.05);
        border-radius: 10px; padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .stat-box .stat-label { font-size: 0.68rem; color: rgba(255,255,255,0.45); margin-bottom: 2px; }
    .stat-box .stat-value { font-size: 1.2rem; font-weight: 800; color: white; }
    .stat-box .stat-sub { font-size: 0.65rem; color: rgba(255,255,255,0.4); margin-top: 1px; }

    /* 底部信息条 */
    .map-footer {
        background: rgba(10,15,30,0.9);
        backdrop-filter: blur(8px);
        border-top: 1px solid rgba(255,255,255,0.06);
        padding: 0.6rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
    }
    .map-footer .footer-text { font-size: 0.72rem; color: rgba(255,255,255,0.4); }
    .map-footer .footer-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(255,255,255,0.08); border-radius: 20px;
        padding: 3px 10px; font-size: 0.7rem; color: rgba(255,255,255,0.6);
    }

    /* Tab 样式 */
    .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 4px; gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 6px 14px; font-weight: 600; font-size: 0.82rem;
        color: rgba(255,255,255,0.6) !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.08) !important; }
    .stTabs [data-baseweb="tab"]:active, .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(30,136,229,0.4) !important;
        color: white !important;
    }

    /* Slider 样式 */
    .stSlider label, .stSlider span, .stSlider p { color: rgba(255,255,255,0.7) !important; }
    [data-testid="stSlider"] > div > div > div { color: white !important; }
    .stSlider [data-baseweb="slider"] .trTeIr { color: white !important; }

    /* Selectbox 样式 */
    .stSelectbox [data-baseweb="select"] { background: rgba(255,255,255,0.08) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: white !important; }

    /* Checkbox 样式 */
    .stCheckbox label, .stCheckbox span, .stCheckbox p { color: rgba(255,255,255,0.7) !important; }

    /* number input */
    .stNumberInput label { color: rgba(255,255,255,0.7) !important; }
    .stNumberInput input { color: white !important; }

    /* 多选 */
    .stMultiSelect [data-baseweb="select"] { background: rgba(255,255,255,0.08) !important; }

    /* Streamlit expander */
    .streamlit-expander { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; }
    .streamlit-expander summary { color: white !important; }
</style>
""", unsafe_allow_html=True)


# ============ 页面标题 ============
st.markdown("""
<div class="map-page-header">
    <h1>🗺️ 北极战略态势全景地图</h1>
    <p>实时战略态势 · 科考站网络 · 航道布局 · 地缘事件热力 · 四维数据联动</p>
</div>
""", unsafe_allow_html=True)


# ============ 数据加载 ============
grid_df, yc_df = load_gdelt_data()
stations_data = load_stations()
net_data = load_geopolitics_network('all')

# 统计数据
total_stations = len(stations_data.get('features', []))
total_events = yc_df['EventCount'].sum() if not yc_df.empty else 0
avg_tone = yc_df['AvgTone'].mean() if not yc_df.empty else 0
top_country = yc_df.groupby('CountryCode')['EventCount'].sum().idxmax() if not yc_df.empty else 'RUS'

# 国家统计
country_counts = {}
for feat in stations_data.get('features', []):
    c = feat.get('properties', {}).get('country', '未知')
    country_counts[c] = country_counts.get(c, 0) + 1


# ============ 主地图 Tab ============
map_tab1, map_tab2, map_tab3, map_tab4 = st.tabs([
    "🌍 3D地球全景", "🗺️ 交互地图", "⚡ 实时数据联动", "📊 战略统计"
])


# -----------------------------------------------
# Tab1: 3D 地球 — Plotly 正射投影 + 可旋转
# -----------------------------------------------
with map_tab1:
    tab1_cols = st.columns([1, 4])

    with tab1_cols[0]:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)

        st.markdown("### 🕹️ 图层控制")

        show_stations = st.checkbox("🔬 科考站网络", value=True)
        show_routes = st.checkbox("🚢 战略航道", value=True)
        show_events_map = st.checkbox("📊 GDELT事件", value=True)
        show_arctic = st.checkbox("🔵 北极圈参考", value=True)

        st.markdown("### 🌍 旋转控制")
        rot_lon = st.slider("经度旋转", -180, 180, 0, help="拖动改变地球视角")
        rot_lat = st.slider("纬度倾斜", 60, 90, 75, help="改变俯视角度")

        st.markdown("### 📖 图例")
        st.markdown("""
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#FF0000"></div>中国科考站</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#1565C0"></div>美国科考站</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#8B0000"></div>俄罗斯科考站</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#607D8B"></div>国际合作站</div>
        <div class="legend-item-map"><div class="legend-line-map" style="background:#E53935"></div>东北航道</div>
        <div class="legend-item-map"><div class="legend-line-map" style="background:#1565C0"></div>西北航道</div>
        <div class="legend-item-map"><div class="legend-line-map" style="background:#43A047"></div>跨极航道</div>
        """, unsafe_allow_html=True)

        st.markdown("### 📈 实时统计")
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">科考站总数</div>
            <div class="stat-value" style="color:#1E88E5">{total_stations}</div>
            <div class="stat-sub">大北极研究网络</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">地缘事件</div>
            <div class="stat-value" style="color:#E53935">{total_events:,}</div>
            <div class="stat-sub">2018-2024 GDELT</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">平均情感</div>
            <div class="stat-value" style="color:{'#43A047' if avg_tone > 0 else '#E53935'}">{avg_tone:+.2f}</div>
            <div class="stat-sub">{'偏正面' if avg_tone > 0 else '偏负面'}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">最活跃国家</div>
            <div class="stat-value" style="color:#FF6B35">{COUNTRY_NAMES.get(top_country, top_country)}</div>
            <div class="stat-sub">地缘事件最多</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with tab1_cols[1]:
        # 3D Plotly 地球
        import plotly.graph_objects as go

        fig = go.Figure()

        # 经纬度网格线
        for lat in [70, 75, 80, 85]:
            lons = np.linspace(-180, 180, 90)
            lats = [lat] * len(lons)
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats, mode='lines',
                line=dict(width=0.5, color='rgba(100,150,200,0.25)'),
                showlegend=False, hoverinfo='skip'
            ))
        for lon in np.arange(-180, 180, 30):
            lats = np.linspace(60, 90, 30)
            lons = [lon] * len(lats)
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats, mode='lines',
                line=dict(width=0.5, color='rgba(100,150,200,0.25)'),
                showlegend=False, hoverinfo='skip'
            ))

        # 北极圈
        if show_arctic:
            arctic_lons = np.linspace(-180, 180, 180)
            arctic_lats = [66.5] * len(arctic_lons)
            fig.add_trace(go.Scattergeo(
                lon=arctic_lons, lat=arctic_lats, mode='lines',
                line=dict(width=2, color='rgba(144,202,249,0.8)', dash='dash'),
                name='北极圈 (66.5°N)', showlegend=True, hoverinfo='skip'
            ))

        # 科考站
        station_colors = {
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
                color = station_colors.get(country, '#757575')
                established = props.get('established', 'N/A')
                research = props.get('research_focus', [])
                desc = props.get('description', '')[:100]

                fig.add_trace(go.Scattergeo(
                    lon=[lon], lat=[lat],
                    mode='markers+text',
                    marker=dict(
                        size=14, color=color,
                        line=dict(width=2, color='white'),
                        opacity=0.9,
                        symbol='circle'
                    ),
                    text=[name],
                    textposition='top center',
                    textfont=dict(size=8, color='white'),
                    hovertemplate=(
                        f"<b style='color:{color}'>🔬 {name}</b><br>"
                        f"<b>国家:</b> {country}<br>"
                        f"<b>设立:</b> {established}<br>"
                        f"<b>坐标:</b> {lat:.2f}°N, {lon:.2f}°E<br>"
                        f"<b>领域:</b> {', '.join(research[:3]) if research else 'N/A'}<br>"
                        f"<b>简介:</b> {desc}...<extra></extra>"
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
                    desc = props.get('description', '')[:80]

                    fig.add_trace(go.Scattergeo(
                        lon=[c[0] for c in coords],
                        lat=[c[1] for c in coords],
                        mode='lines',
                        line=dict(width=4, color=color, opacity=0.85),
                        hovertemplate=(
                            f"<b style='color:{color}'>🚢 {name}</b><br>"
                            f"<b>航程:</b> {distance}<br>"
                            f"<b>时间:</b> {duration}<br>"
                            f"<b>主导:</b> {operator}<br>"
                            f"<b>说明:</b> {desc}...<extra></extra>"
                        ),
                        name=f'🚢 {name}',
                        showlegend=True
                    ))

        # GDELT 事件热力（圆形散点模拟热力效果）
        if show_events_map and not grid_df.empty:
            year_col = next((c for c in ['Year_local', 'Year'] if c in grid_df.columns), None)
            if year_col:
                # 取最近一年的数据
                latest_year = grid_df[year_col].max()
                year_data = grid_df[grid_df[year_col] == latest_year]
                lat_col = next((c for c in ['lat_grid', 'lat'] if c in year_data.columns), 'lat_grid')
                lon_col = next((c for c in ['lon_grid', 'lon'] if c in year_data.columns), 'lon_grid')

                # 分档显示不同强度
                for threshold, size, opacity in [(20, 6, 0.3), (10, 5, 0.5), (1, 4, 0.7)]:
                    ev_data = year_data[year_data['EventCount'] >= threshold]
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
                            colorbar=dict(title='事件数', len=0.3, y=0.5)
                        ),
                        hovertemplate='📊 地缘事件: %{marker.color}起<br>坐标: %{lat:.1f}°N, %{lon:.1f}°E<extra></extra>',
                        name=f'📊 事件热力({latest_year})',
                        showlegend=False
                    ))

        # 更新布局
        fig.update_layout(
            geo=dict(
                scope='world',
                projection_type='orthographic',
                projection_rotation=dict(lon=rot_lon, lat=rot_lat),
                center=dict(lat=rot_lat, lon=rot_lon),
                showland=True,
                landcolor='rgba(220,235,250,0.95)',
                showocean=True,
                oceancolor='rgba(170,210,240,0.7)',
                showlakes=True,
                lakecolor='rgba(170,210,240,0.8)',
                showcountries=True,
                countrycolor='rgba(160,180,200,0.6)',
                showcoastlines=True,
                coastlinecolor='rgba(140,165,190,0.7)',
                coastlinewidth=0.8,
                showframe=False,
                bgcolor='rgba(5,15,35,0)',
                lataxis_range=[55, 90],
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=0),
            height=620,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.02,
                xanchor='center',
                x=0.5,
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(color='white', size=9)
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # 底部信息条
    st.markdown("""
    <div class="map-footer">
        <div class="footer-text">🗺️ 北极战略态势全景地图 | 数据更新: 2024 | © 大创专项</div>
        <div class="footer-badge">🌍 北极圈 66.5°N</div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------
# Tab2: Folium 交互地图 — 精细化图层控制
# -----------------------------------------------
with map_tab2:
    col_ctl2, col_map2 = st.columns([1, 5])

    with col_ctl2:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)

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
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#FF0000"></div>中国</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#1565C0"></div>美国</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#8B0000"></div>俄罗斯</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#FF6F00"></div>挪威</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#43A047"></div>加拿大</div>
        <div class="legend-item-map"><div class="legend-dot-map" style="background:#607D8B"></div>国际组织</div>
        <div class="legend-item-map"><div class="legend-line-map" style="background:#E53935"></div>东北航道</div>
        <div class="legend-item-map"><div class="legend-line-map" style="background:#1565C0"></div>西北航道</div>
        """, unsafe_allow_html=True)

        st.markdown("### 💡 操作提示")
        st.markdown("""
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);line-height:1.6;">
        • <b>点击</b>标记查看详情<br>
        • <b>滚轮</b>缩放地图<br>
        • <b>右下角</b>切换全屏<br>
        • <b>鼠标位置</b>显示坐标
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_map2:
        import folium
        from folium import plugins

        # 底图选择
        tile_templates = {
            "CartoDB Positron": ('cartodbpositron', 'CartoDB'),
            "CartoDB Dark": ('CartoDB.dark_matter', 'CartoDB'),
            "Esri Satellite": ('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 'Esri'),
            "OpenStreetMap": ('OpenStreetMap', 'OSM'),
            "Stamen Terrain": ('https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png', 'Stamen'),
        }
        tile_url, tile_attr = tile_templates.get(tile_choice, ('cartodbpositron', 'CartoDB'))

        m = folium.Map(
            location=[72, 30],
            zoom_start=3,
            tiles=None,
            prefer_canvas=True
        )

        # 添加底图
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
                <div style="min-width:300px;font-family:'Segoe UI',Arial,sans-serif;">
                    <div style="background:linear-gradient(135deg,{color}22,{color}44);border-left:4px solid {color};padding:10px 12px;border-radius:8px 8px 0 0;">
                        <h3 style="color:{color};margin:0;font-size:15px;">🔬 {name}</h3>
                    </div>
                    <div style="padding:10px 12px;">
                        <table style="width:100%;font-size:13px;border-collapse:collapse;">
                            <tr><td style="padding:4px 8px;color:#666;width:35%;"><b>所属国</b></td><td style="padding:4px 8px;color:#222;">{country}</td></tr>
                            <tr style="background:#f8f9fa;"><td style="padding:4px 8px;color:#666;"><b>设立年份</b></td><td style="padding:4px 8px;color:#222;">{established}</td></tr>
                            <tr><td style="padding:4px 8px;color:#666;"><b>坐标</b></td><td style="padding:4px 8px;color:#222;">{lat:.2f}°N, {lon:.2f}°E</td></tr>
                            <tr style="background:#f8f9fa;"><td style="padding:4px 8px;color:#666;"><b>技术方向</b></td><td style="padding:4px 8px;color:#222;">{tech_domain}</td></tr>
                        </table>
                        <div style="margin-top:8px;padding:8px;background:#f0f4f8;border-radius:6px;">
                            <div style="font-size:11px;color:#555;line-height:1.6;">
                                <b style="color:#333;">研究领域：</b>{', '.join(research[:4]) if research else 'N/A'}<br>
                                <b style="color:#333;">简介：</b>{desc[:180]}{'...' if len(desc) > 180 else ''}
                            </div>
                        </div>
                    </div>
                </div>
                """

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    color=color, weight=2.5,
                    fill=True, fillColor=color, fillOpacity=0.8,
                    popup=folium.Popup(popup_html, max_width=360, min_width=300),
                    tooltip=f"🔬 {name} ({country})"
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
                    <div style="min-width:260px;font-family:'Segoe UI',Arial,sans-serif;">
                        <h3 style="color:{color};margin:0 0 8px 0;">🚢 {name}</h3>
                        <table style="width:100%;font-size:12px;">
                            <tr><td style="padding:3px 6px;color:#666;"><b>航程</b></td><td style="padding:3px 6px;">{distance}</td></tr>
                            <tr><td style="padding:3px 6px;color:#666;"><b>航行时间</b></td><td style="padding:3px 6px;">{duration}</td></tr>
                            <tr><td style="padding:3px 6px;color:#666;"><b>主导方</b></td><td style="padding:3px 6px;">{operator}</td></tr>
                            <tr><td style="padding:3px 6px;color:#666;"><b>通航期</b></td><td style="padding:3px 6px;">{open_months}</td></tr>
                        </table>
                        <div style="margin-top:8px;font-size:12px;color:#555;line-height:1.5;">{desc}</div>
                    </div>
                    """

                    folium.PolyLine(
                        locations=coords,
                        weight=5.5, color=color, opacity=0.9,
                        popup=folium.Popup(route_popup, max_width=280),
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

        # 军事基地（虚拟）
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
                    radius=8,
                    color='#B71C1C', weight=2,
                    fill=True, fillColor='#B71C1C', fillOpacity=0.7,
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
            st.error("请安装 streamlit-folium: pip install streamlit-folium")

    st.markdown("""
    <div class="map-footer">
        <div class="footer-text">🗺️ Folium 交互地图 | 点击标记查看详情 | 滚轮缩放 | © 大创专项</div>
        <div class="footer-badge">🔍 支持多底图切换</div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------
# Tab3: 实时数据联动 — 多维度数据面板
# -----------------------------------------------
with map_tab3:
    import plotly.graph_objects as go

    st.markdown('<div class="control-panel" style="border-radius:16px;margin-bottom:1rem;">', unsafe_allow_html=True)
    st.markdown("### ⚡ 四维数据联动看板", unsafe_allow_html=False)

    col_yr, col_map3 = st.columns([1, 4])

    with col_yr:
        selected_year_map = st.slider("选择年份", 2018, 2024, 2023)

        # 该年统计
        year_events = yc_df[yc_df['year'] == selected_year_map] if not yc_df.empty else pd.DataFrame()
        year_total = year_events['EventCount'].sum() if not year_events.empty else 0
        year_tone = year_events['AvgTone'].mean() if not year_events.empty else 0

        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">{selected_year_map}年地缘事件</div>
            <div class="stat-value" style="color:#E53935">{year_total:,}</div>
            <div class="stat-sub">GDELT统计</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">平均情感值</div>
            <div class="stat-value" style="color:{'#43A047' if year_tone > 0 else '#E53935'}">{year_tone:+.2f}</div>
            <div class="stat-sub">{'正面' if year_tone > 0 else '负面'}</div>
        </div>
        """, unsafe_allow_html=True)

        # 国家排名
        if not year_events.empty:
            top5 = year_events.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=False).head(5)
            for i, (code, count) in enumerate(top5.items()):
                color = COUNTRY_COLORS.get(code, '#757575')
                pct = count / year_total * 100 if year_total > 0 else 0
                st.markdown(f"""
                <div style="padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></div>
                            <span style="font-size:0.78rem;color:rgba(255,255,255,0.8);">{COUNTRY_NAMES.get(code, code)}</span>
                        </div>
                        <div style="font-size:0.82rem;font-weight:700;color:white;">{count}</div>
                    </div>
                    <div style="height:3px;background:rgba(255,255,255,0.08);border-radius:2px;margin-top:4px;">
                        <div style="height:3px;width:{pct:.0f}%;background:{color};border-radius:2px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col_map3:
        # GDELT 年度趋势
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
                yaxis=dict(title='地缘事件数', titlefont_color='rgba(255,255,255,0.6)', tickfont_color='rgba(255,255,255,0.6)'),
                yaxis2=dict(title='情感指数', titlefont_color='rgba(255,215,0,0.8)', tickfont_color='rgba(255,215,0,0.8)',
                           overlaying='y', side='right', showgrid=False),
                template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280,
                margin=dict(l=50, r=50, t=30, b=40),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                          bgcolor='rgba(0,0,0,0.5)', font=dict(color='white'))
            )
            # 应用暗色主题到坐标轴
            fig_dual.update_xaxes(gridcolor='rgba(255,255,255,0.08)', zerolinecolor='rgba(255,255,255,0.1)', tickfont_color='rgba(255,255,255,0.6)', title_font_color='rgba(255,255,255,0.6)')
            fig_dual.update_yaxes(gridcolor='rgba(255,255,255,0.08)', zerolinecolor='rgba(255,255,255,0.1)', tickfont_color='rgba(255,255,255,0.6)')
            st.plotly_chart(fig_dual, use_container_width=True)

        # 按类型分布
        if not yc_df.empty:
            cat_events = yc_df[yc_df['year'] == selected_year_map].groupby('EventCategory')['EventCount'].sum() if 'EventCategory' in yc_df.columns else pd.Series()
            if not cat_events.empty:
                fig_pie = go.Figure(go.Pie(
                    labels=['资源开发', '军事活动', '航道航运', '科研活动', '基础设施', '技术竞争', '科技合作', '一般事件'],
                    values=cat_events.values if len(cat_events) == 8 else [1]*8,
                    hole=0.5,
                    marker_colors=['#FDD835', '#8E24AA', '#FF6B35', '#1E88E5', '#00BCD4', '#E53935', '#43A047', '#757575'],
                    textinfo='percent+label',
                    hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
                ))
                fig_pie.update_layout(
                    height=240, margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5, font=dict(color='white', size=9))
                )
                st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------
# Tab4: 战略统计
# -----------------------------------------------
with map_tab4:
    import plotly.graph_objects as go

    col_stats1, col_stats2 = st.columns(2)

    with col_stats1:
        st.markdown('<div class="control-panel" style="height:100%;">', unsafe_allow_html=True)
        st.markdown("### 🏳️ 科考站国家分布", unsafe_allow_html=False)

        # 国家统计
        if country_counts:
            sorted_countries = sorted(country_counts.items(), key=lambda x: -x[1])
            country_colors = {
                '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
                '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
                '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
                '国际合作（多国）': '#607D8B', '加拿大': '#43A047',
            }
            fig_country = go.Figure(go.Bar(
                y=[c[0] for c in sorted_countries],
                x=[c[1] for c in sorted_countries],
                orientation='h',
                marker_color=[country_colors.get(c[0], '#757575') for c in sorted_countries],
                hovertemplate='%{y}: %{x}个科考站<extra></extra>'
            ))
            fig_country.update_layout(
                height=max(300, len(sorted_countries) * 40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=100, r=20, t=20, b=40),
                xaxis_title='科考站数量',
                yaxis_title='',
                showlegend=False,
            )
            fig_country.update_xaxes(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)', title_font_color='rgba(255,255,255,0.6)')
            fig_country.update_yaxes(tickfont_color='rgba(255,255,255,0.8)')
            st.plotly_chart(fig_country, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_stats2:
        st.markdown('<div class="control-panel" style="height:100%;">', unsafe_allow_html=True)
        st.markdown("### 🔗 地缘关系网络", unsafe_allow_html=False)

        # 关系类型统计
        rel_types = {}
        for link in net_data.get('links', []):
            t = link.get('relation', 'unknown')
            rel_types[t] = rel_types.get(t, 0) + 1

        rel_colors = {'cooperation': '#43A047', 'competition': '#FF6B35', 'confrontation': '#E53935'}
        rel_names = {'cooperation': '合作', 'competition': '竞争', 'confrontation': '对抗'}
        rel_data = [(rel_names.get(k, k), v, rel_colors.get(k, '#757575')) for k, v in rel_types.items()]

        if rel_data:
            fig_rel = go.Figure()
            for name, count, color in rel_data:
                fig_rel.add_trace(go.Bar(
                    x=[count], y=[name],
                    orientation='h',
                    marker_color=color,
                    hovertemplate=f'{name}: {count}组关系<extra></extra>',
                    showlegend=False
                ))
            fig_rel.update_layout(
                height=200,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=80, r=20, t=20, b=40),
                xaxis_title='关系数量',
                showlegend=False,
            )
            fig_rel.update_xaxes(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)')
            fig_rel.update_yaxes(tickfont_color='rgba(255,255,255,0.8)')
            st.plotly_chart(fig_rel, use_container_width=True)

        # 节点影响力
        st.markdown("#### 🏆 国家影响力排名")
        node_influence = {}
        for node in net_data.get('nodes', []):
            nid = node.get('id', '')
            influence = node.get('influence', 5)
            node_influence[COUNTRY_NAMES.get(nid, nid)] = influence

        if node_influence:
            sorted_nodes = sorted(node_influence.items(), key=lambda x: -x[1])
            fig_inf = go.Figure(go.Bar(
                y=[n[0] for n in sorted_nodes],
                x=[n[1] for n in sorted_nodes],
                orientation='h',
                marker_color=[COUNTRY_COLORS.get(list(COUNTRY_NAMES.keys())[list(COUNTRY_NAMES.values()).index(n[0])], '#757575')
                            if n[0] in COUNTRY_NAMES.values() else '#1E88E5' for n in sorted_nodes],
                hovertemplate='%{y}: 影响力 %{x}<extra></extra>'
            ))
            fig_inf.update_layout(
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=100, r=20, t=20, b=40),
                xaxis_title='影响力指数',
                showlegend=False,
            )
            fig_inf.update_xaxes(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)')
            fig_inf.update_yaxes(tickfont_color='rgba(255,255,255,0.8)')
            st.plotly_chart(fig_inf, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("🗺️ 地图数据来源: INTERACT科考站数据库 · GDELT全球事件数据库 · GeoJSON地理数据 · © 大创专项")
