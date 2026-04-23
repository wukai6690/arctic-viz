"""
北极地图概览页面
交互式 Folium 地图，支持时间滑块联动
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.narrative import get_narrative_by_year, get_all_years

st.set_page_config(page_title="北极地图概览", page_icon="🌍", layout="wide")

st.markdown("## 🌍 北极交互地图概览")
st.markdown("""
拖动下方时间滑块，地图将同步更新 GDELT 事件热力图和战略叙事文字。
""")

st.divider()

# 加载 GeoJSON 数据
@st.cache_data
def load_geojson(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

routes_geojson = load_geojson('geojson/arctic_routes.geojson')
stations_geojson = load_geojson('geojson/research_stations.geojson')
conflicts_geojson = load_geojson('geojson/conflicts.geojson')

# 加载 GDELT 网格数据
@st.cache_data
def load_gdelt_grid():
    path = 'data/processed/gdelt_arctic_by_grid.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        # 统一列名：优先 Year_local，回退 year
        if 'Year_local' in df.columns:
            df['Year'] = pd.to_numeric(df['Year_local'], errors='coerce').fillna(0).astype(int)
        elif 'year' in df.columns and 'Year' not in df.columns:
            df['Year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
        elif 'Year' in df.columns:
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame()

gdelt_df = load_gdelt_grid()

# 侧边栏控制
with st.sidebar:
    st.markdown("### 🕐 时间控制")
    selected_year = st.slider(
        "选择年份",
        min_value=2018,
        max_value=2024,
        value=2023,
        step=1,
        help="拖动滑块切换年份，地图与叙事文字同步更新"
    )

    st.divider()
    st.markdown("### 🗺️ 图层开关")
    show_routes = st.checkbox("三大航道轨迹", value=True)
    show_stations = st.checkbox("科考站分布", value=True)
    show_conflicts = st.checkbox("地缘冲突事件", value=True)
    show_gdelt_heat = st.checkbox("GDELT 事件热力图", value=True)

    st.divider()
    st.markdown("### 📌 地图设置")
    map_zoom = st.slider("初始缩放级别", 2, 8, 4)

    st.divider()
    all_years = get_all_years()
    st.markdown(f"**叙事数据覆盖年份：** `{', '.join(map(str, all_years))}`")

# 创建 Folium 地图
@st.cache_data
def create_arctic_map(year, zoom, routes_on, stations_on, conflicts_on, gdelt_on, gdelt_data):
    m = folium.Map(
        location=[80, 0],
        zoom_start=zoom,
        tiles='cartodbpositron',
        prefer_canvas=True,
        control_scale=True
    )

    # 北极圈参考线
    folium.Circle(
        location=[66.5, 0],
        radius=0,
        popup="北极圈 (66.5°N)"
    ).add_to(m)

    # 三大航道
    if routes_on:
        route_colors = {
            'Northeast Passage (NSR)': '#FF6B35',
            '西北航道': '#00B4D8',
            'Northeast Passage': '#FF6B35',
            '东北航道': '#FF6B35',
            'Northwest Passage (NWP)': '#00B4D8',
            'Transpolar Passage': '#8338EC',
            '中央航道': '#8338EC',
        }
        route_labels = {
            'Northeast Passage (NSR)': '东北航道 (NSR)',
            'Northeast Passage': '东北航道 (NSR)',
            '东北航道': '东北航道 (NSR)',
            'Northwest Passage (NWP)': '西北航道 (NWP)',
            '西北航道': '西北航道 (NWP)',
            'Transpolar Passage': '中央航道 (公海)',
            '中央航道': '中央航道 (公海)',
        }

        for feature in routes_geojson['features']:
            name = feature['properties'].get('name', feature['properties'].get('name_en', ''))
            color = route_colors.get(name, '#FF6B35')
            label = route_labels.get(name, name)

            coords = feature['geometry']['coordinates']
            if feature['geometry']['type'] == 'LineString':
                coords = [[c[1], c[0]] for c in coords]

            route_group = folium.FeatureGroup(name=label)

            folium.PolyLine(
                locations=coords,
                weight=4,
                color=color,
                opacity=0.85,
                popup=folium.Popup(
                    f"<b>{label}</b><br>"
                    f"<b>英文名:</b> {feature['properties'].get('name_en', 'N/A')}<br>"
                    f"<b>描述:</b> {feature['properties'].get('description', 'N/A')}<br>"
                    f"<b>通航期:</b> {feature['properties'].get('ice_free_months', 'N/A')}<br>"
                    f"<b>2023年货运量:</b> {feature['properties'].get('cargo_volume_2023', 'N/A')}<br>"
                    f"<b>涉及国家:</b> {', '.join(feature['properties'].get('countries', []))}",
                    max_width=350
                )
            ).add_to(route_group)

            for i, coord in enumerate(coords[::5]):
                folium.CircleMarker(
                    location=coord,
                    radius=3,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.8,
                    popup=f"{label} 航点 {i+1}"
                ).add_to(route_group)

            route_group.add_to(m)

    # GDELT 热力图（按年份过滤）
    if gdelt_on and not gdelt_data.empty:
        year_col = 'Year' if 'Year' in gdelt_data.columns else 'Year_local'
        year_data = gdelt_data[gdelt_data[year_col] == year]
        if not year_data.empty:
            heat_data = [
                [row['lat_grid'], row['lon_grid'], row['EventCount']]
                for _, row in year_data.iterrows()
                if pd.notna(row['lat_grid']) and pd.notna(row['lon_grid'])
            ]
            if heat_data:
                plugins.HeatMap(heat_data, radius=25, blur=15, max_zoom=6,
                                gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
                               ).add_to(m)

    # 科考站
    if stations_on:
        station_group = folium.FeatureGroup(name='科考站')
        country_colors = {
            '中国': '#FF0000',
            '美国': '#0000FF',
            '俄罗斯': '#8B0000',
            '挪威': '#FFA500',
            '丹麦': '#FF4500',
            '国际合作（多国）': '#800080',
        }

        for feature in stations_geojson['features']:
            props = feature.get('properties', {})
            name = props.get('name', '未知')
            country = props.get('country', '未知')
            geom = feature.get('geometry')
            if not geom or 'coordinates' not in geom:
                continue
            lat, lon = geom['coordinates'][1], geom['coordinates'][0]
            color = country_colors.get(country, '#555555')

            research = '<br>'.join([f"• {r}" for r in props.get('research_focus', [])])

            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                color=color,
                weight=2,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                popup=folium.Popup(
                    f"<b style='font-size:14px'>{name}</b><br>"
                    f"<b>所属国:</b> {country}<br>"
                    f"<b>设立年份:</b> {props.get('established', 'N/A')}<br>"
                    f"<b>研究领域:</b><br>{research}<br>"
                    f"<b>技术方向:</b> {props.get('tech_domain', 'N/A')}<br>"
                    f"<b>简介:</b> {props.get('description', '')}",
                    max_width=400
                ),
                tooltip=f"{name} ({country})"
            ).add_to(station_group)

        station_group.add_to(m)

    # 地缘冲突事件
    if conflicts_on:
        conflict_group = folium.FeatureGroup(name='地缘冲突事件')
        category_colors = {
            'tech_competition': '#E53935',
            'arctic_shipping': '#FF6B35',
            'arctic_resource': '#FDD835',
            'arctic_military': '#8E24AA',
            'arctic_cooperation': '#43A047',
            'arctic_infrastructure': '#00BCD4',
            'arctic_research': '#1E88E5',
            'arctic_governance': '#6D4C41',
        }
        category_labels = {
            'tech_competition': '技术竞争',
            'arctic_shipping': '航道事件',
            'arctic_resource': '资源开发',
            'arctic_military': '军事活动',
            'arctic_cooperation': '科技合作',
            'arctic_infrastructure': '基础设施',
            'arctic_research': '科研活动',
            'arctic_governance': '治理规则',
        }

        for feature in conflicts_geojson['features']:
            props = feature.get('properties', {})
            if props.get('year') != year:
                continue

            category = props.get('category', 'unknown')
            geom = feature.get('geometry')
            if not geom or 'coordinates' not in geom:
                continue
            lat, lon = geom['coordinates'][1], geom['coordinates'][0]
            color = category_colors.get(category, '#757575')
            label = category_labels.get(category, category)
            severity = props.get('severity', 5)

            folium.CircleMarker(
                location=[lat, lon],
                radius=severity,
                color=color,
                weight=2,
                fill=True,
                fillColor=color,
                fillOpacity=0.5,
                popup=folium.Popup(
                    f"<b>{props.get('title', '')}</b><br>"
                    f"<b>类型:</b> {label}<br>"
                    f"<b>年份:</b> {props.get('year', '')}<br>"
                    f"<b>涉及国家:</b> {', '.join(props.get('countries', []))}<br>"
                    f"<b>严重程度:</b> {'⚠️' * severity}<br>"
                    f"<b>描述:</b> {props.get('description', '')}",
                    max_width=350
                ),
                tooltip=f"{label}: {props.get('title', '')}"
            ).add_to(conflict_group)

        conflict_group.add_to(m)

    # 图层控制
    folium.LayerControl(collapsed=False, autoToggleChecked=False).add_to(m)

    # 导航控件
    plugins.Fullscreen(position='topright').add_to(m)
    plugins.MousePosition().add_to(m)

    return m

# 生成地图
arctic_map = create_arctic_map(
    selected_year, map_zoom,
    show_routes, show_stations, show_conflicts, show_gdelt_heat,
    gdelt_df
)

# 布局：地图 + 叙事文字
col_map, col_narrative = st.columns([7, 3])

with col_map:
    st.markdown(f"### 📍 {selected_year}年 北极地缘态势图")
    st.caption("点击地图元素查看详情 | 使用右下角控件切换图层")

    if gdelt_df.empty:
        st.info("""
        🗺️ 地图基础功能正常（航道/科考站/冲突点）。

        📊 如需在地图上叠加 GDELT 事件热力图：
        1. 点击左侧菜单「GDELT 数据获取」
        2. 点击「🎲 生成模拟数据」
        3. 返回本页面即可看到热力图
        """)
    else:
        try:
            from streamlit_folium import st_folium
            st_folium(arctic_map, width=None, height=600, returned_objects=[])
        except ImportError:
            st.error("请安装 streamlit-folium: pip install streamlit-folium")

with col_narrative:
    st.markdown(f"### 📖 {selected_year}年战略叙事")
    narrative = get_narrative_by_year(int(selected_year))

    st.markdown(f"**{narrative['title']}**")
    st.caption(f"📅 {narrative['period']}")
    st.markdown(narrative['summary'])

    with st.expander("🔑 关键事件", expanded=True):
        for event in narrative['key_events']:
            st.markdown(f"- {event}")

    st.markdown("---")
    st.markdown("**🇨🇳 中国视角**")
    st.markdown(narrative['chinese_angle'])

    if 'tech_competition' in narrative:
        st.markdown("---")
        st.markdown("**⚙️ 技术竞争焦点**")
        st.markdown(narrative['tech_competition'])

    if 'policy_recommendation' in narrative:
        st.markdown("---")
        st.markdown("**🛡️ 政策建议**")
        st.markdown(narrative['policy_recommendation'])

# 底部图例
st.divider()
legend_cols = st.columns([1, 1, 1, 1, 1])

categories = [
    ("技术竞争", "#E53935"),
    ("航道事件", "#FF6B35"),
    ("资源开发", "#FDD835"),
    ("军事活动", "#8E24AA"),
    ("科技合作", "#43A047"),
]
for i, (label, color) in enumerate(categories):
    with legend_cols[i]:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;'>"
            f"<div style='width:16px;height:16px;border-radius:50%;background:{color};'></div>"
            f"<span style='font-size:0.85rem'>{label}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

st.divider()
st.caption("数据来源: GDELT 全球事件数据库 | GeoJSON: 航道/NGA, 科考站/INTERACT")
