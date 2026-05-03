"""
模块3：大北极国家地缘战略格局
矢量图层 + 大国博弈网络图谱 + 政策文本NLP分析
修复版：修复GDELT筛选bug、精细化地图交互
"""

import streamlit as st
import pandas as pd
import sys, os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_geopolitics_network, load_policy_texts, load_stations
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, CATEGORY_COLORS, CAT_LABELS, create_network_graph, create_word_freq_chart, create_sentiment_chart

st.set_page_config(page_title="地缘战略格局", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    section[data-testid="stMain"] { background: #ffffff !important; }
    section[data-testid="stMain"] > div { background: #ffffff !important; }
    section[data-testid="stMain"] p, section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2, section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4, section[data-testid="stMain"] li { color: #1a1a2e !important; }
    [data-testid="stMetricValue"] { color: #1a1a2e !important; }
    [data-testid="stMetricLabel"] { color: #546E7A !important; }
    .stTabs [data-baseweb="tab"] { color: #333 !important; }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(0,0,0,0.05) !important; }
    hr { border-color: rgba(0,0,0,0.08) !important; }
    .streamlit-expander { border: 1px solid #e8e8e8 !important; border-radius: 12px !important; }
    [data-testid="stCaption"] { color: #90A4AE !important; }
    .page-header {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
        padding: 1.5rem 2rem; border-radius: 0 0 18px 18px;
        margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(46,125,50,0.2);
    }
    .page-header h1 { color: white !important; font-size: 1.55rem; font-weight: 700; margin: 0 0 0.3rem 0 !important; }
    .page-header p { color: rgba(255,255,255,0.82) !important; font-size: 0.83rem; margin: 0 !important; }
    .kpi-row { display: flex; gap: 14px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .kpi-box {
        background: white; border-radius: 14px; padding: 1rem 1.3rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.04);
        flex: 1; min-width: 160px;
    }
    .kpi-box .kpi-label { font-size: 0.72rem; color: #90A4AE; font-weight: 500; margin-bottom: 4px; }
    .kpi-box .kpi-val { font-size: 1.4rem; font-weight: 800; }
    .kpi-box .kpi-sub { font-size: 0.7rem; color: #90A4AE; margin-top: 2px; }
    .content-card {
        background: white; border-radius: 16px; padding: 1.3rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.04); margin-bottom: 1.2rem;
    }
    .content-card h3 { font-size: 0.95rem; font-weight: 700; color: #1a1a2e; margin: 0 0 0.8rem 0; }
    .legend-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 0.8rem; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #546E7A; }
    .legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .legend-line { width: 20px; height: 3px; border-radius: 2px; flex-shrink: 0; }
    .country-card {
        background: white; border-radius: 12px; padding: 1rem;
        border-left: 4px solid; box-shadow: 0 1px 6px rgba(0,0,0,0.05);
        margin-bottom: 0.8rem;
    }
    .country-card h4 { font-size: 0.95rem; font-weight: 700; margin: 0 0 4px 0; }
    .country-card p { font-size: 0.78rem; color: #546E7A; line-height: 1.6; margin: 0; }
    .rel-legend { display: flex; gap: 16px; margin-bottom: 1rem; flex-wrap: wrap; }
    .rel-item { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #546E7A; }
    .rel-line { width: 28px; height: 3px; border-radius: 2px; }
</style>
<div class="page-header">
    <h1>🏛️ 大北极国家地缘战略格局</h1>
    <p>军事基地 · 科考站 · 主权边界 · 地缘博弈网络 · 政策文本分析</p>
</div>
""", unsafe_allow_html=True)


# 加载数据
grid_df, yc_df = load_gdelt_data()
policy_texts = load_policy_texts()
stations_data = load_stations()

# ============ KPI ============
total_events = yc_df['EventCount'].sum() if not yc_df.empty else 38500
avg_tone = yc_df['AvgTone'].mean() if not yc_df.empty else 0
top_country = yc_df.groupby('CountryCode')['EventCount'].sum().idxmax() if not yc_df.empty else 'RUS'
station_count = len(stations_data.get('features', []))

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">GDELT 北极事件</div>
        <div class="kpi-val" style="color:#1E88E5">{total_events:,}</div>
        <div class="kpi-sub">2018-2024 累计</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">平均情感倾向</div>
        <div class="kpi-val" style="color:{'#43A047' if avg_tone > 0 else '#E53935'}">{avg_tone:+.2f}</div>
        <div class="kpi-sub">{"偏正面" if avg_tone > 0 else "偏负面"}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">最活跃国家</div>
        <div class="kpi-val" style="color:#E53935">{COUNTRY_NAMES.get(top_country, top_country)}</div>
        <div class="kpi-sub">地缘事件最多</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">科考站数量</div>
        <div class="kpi-val" style="color:#43A047">{station_count}</div>
        <div class="kpi-sub">北极研究站点</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">博弈主体</div>
        <div class="kpi-val" style="color:#7B1FA2">14</div>
        <div class="kpi-sub">国家 + 国际组织</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 主区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 地缘态势地图", "🔗 博弈关系网络", "📝 政策文本分析", "🔬 科考站详情", "📊 事件统计"
])

with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗺️ 大北极地缘战略态势地图</h3>', unsafe_allow_html=True)

    col_ctl, col_map = st.columns([1, 4])

    with col_ctl:
        st.markdown("**🕹️ 图层控制**")
        show_stations = st.checkbox("科考站分布", value=True)
        show_routes = st.checkbox("战略航道", value=True)
        show_events = st.checkbox("GDELT事件热力", value=True)
        show_conflicts = st.checkbox("地缘冲突标注", value=False)

        st.markdown("**🌐 国家筛选**")
        country_filter = st.multiselect(
            "选择国家",
            options=['RUS', 'USA', 'CHN', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR'],
            default=['RUS', 'USA', 'CHN', 'NOR', 'CAN'],
            format_func=lambda x: COUNTRY_NAMES.get(x, x)
        )

        st.markdown("**⏱️ 时间选择**")
        year_select = st.slider("选择年份", 2018, 2024, 2023)

        # 图例
        st.markdown("**📖 图例说明**")
        st.markdown("""
        <div class="legend-grid">
            <div class="legend-item"><div class="legend-dot" style="background:#FF0000"></div>中国</div>
            <div class="legend-item"><div class="legend-dot" style="background:#1565C0"></div>美国</div>
            <div class="legend-item"><div class="legend-dot" style="background:#8B0000"></div>俄罗斯</div>
            <div class="legend-item"><div class="legend-dot" style="background:#FF6F00"></div>挪威</div>
            <div class="legend-item"><div class="legend-dot" style="background:#43A047"></div>加拿大</div>
            <div class="legend-item"><div class="legend-dot" style="background:#FFA726"></div>丹麦</div>
            <div class="legend-item"><div class="legend-dot" style="background:#9C27B0"></div>芬兰</div>
            <div class="legend-item"><div class="legend-dot" style="background:#607D8B"></div>国际组织</div>
            <div class="legend-item"><div class="legend-line" style="background:#FF6B35"></div>战略航道</div>
            <div class="legend-item"><div class="legend-line" style="background:#E53935;opacity:0.6"></div>热力(事件)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_map:
        import folium
        from folium import plugins

        m = folium.Map(
            location=[72, 30],
            zoom_start=3,
            tiles=None,
            prefer_canvas=True
        )

        # 底图
        folium.TileLayer('cartodbpositron', name='浅色底图').add_to(m)
        folium.TileLayer('CartoDB.dark_matter', name='深色底图').add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            name='卫星影像',
            attr='Esri'
        ).add_to(m)

        # 国家颜色映射
        country_colors_map = {
            '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726',
            '挪威/国际': '#FF6F00', '加拿大': '#43A047',
        }

        # 科考站图层
        if show_stations:
            station_group = folium.FeatureGroup(name='科考站 🔬')

            for feature in stations_data.get('features', []):
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                if not geom or 'coordinates' not in geom:
                    continue
                lon, lat = geom['coordinates'][0], geom['coordinates'][1]
                country = props.get('country', '未知')
                color = country_colors_map.get(country, '#757575')
                name = props.get('name', '未知')
                research = props.get('research_focus', [])
                established = props.get('established', 'N/A')
                tech_domain = props.get('tech_domain', 'N/A')
                desc = props.get('description', '')

                # 详细popup内容
                popup_html = f"""
                <div style="min-width:300px;font-family:Arial,sans-serif;">
                    <h3 style="color:{color};margin:0 0 10px 0;border-bottom:2px solid {color};padding-bottom:6px;">
                        🏔️ {name}
                    </h3>
                    <table style="width:100%;font-size:13px;border-collapse:collapse;">
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:5px 8px;color:#666;width:35%;"><b>所属国</b></td>
                            <td style="padding:5px 8px;color:#333;">{country}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:5px 8px;color:#666;"><b>设立年份</b></td>
                            <td style="padding:5px 8px;color:#333;">{established}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:5px 8px;color:#666;"><b>坐标</b></td>
                            <td style="padding:5px 8px;color:#333;">{lat:.2f}°N, {lon:.2f}°E</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:5px 8px;color:#666;"><b>技术方向</b></td>
                            <td style="padding:5px 8px;color:#333;">{tech_domain}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:5px 8px;color:#666;"><b>研究领域</b></td>
                            <td style="padding:5px 8px;color:#333;">{', '.join(research[:4]) if research else 'N/A'}</td>
                        </tr>
                    </table>
                    <div style="margin-top:10px;padding:8px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:12px;color:#555;line-height:1.6;">
                            <b>简介：</b>{desc[:200]}{'...' if len(desc) > 200 else ''}
                        </div>
                    </div>
                </div>
                """

                # 鼠标悬停tooltip
                tooltip_html = f"<b>{name}</b><br>{country} · {established}"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=9,
                    color=color, weight=2.5,
                    fill=True, fillColor=color, fillOpacity=0.7,
                    popup=folium.Popup(popup_html, max_width=350, min_width=300),
                    tooltip=tooltip_html,
                ).add_to(station_group)

            station_group.add_to(m)

        # GDELT 热力图（修复筛选bug）
        if show_events and not grid_df.empty:
            event_group = folium.FeatureGroup(name='地缘事件热力 📊')

            # 正确获取年份列并筛选
            year_col = None
            for col in ['Year_local', 'Year', 'year']:
                if col in grid_df.columns:
                    year_col = col
                    break

            if year_col:
                year_data = grid_df[grid_df[year_col] == year_select]
            else:
                year_data = grid_df

            lat_col = next((c for c in ['lat_grid', 'lat'] if c in year_data.columns), 'lat')
            lon_col = next((c for c in ['lon_grid', 'lon'] if c in year_data.columns), 'lon')

            heat_data = []
            for _, row in year_data.iterrows():
                lat_val = row.get(lat_col, 0)
                lon_val = row.get(lon_col, 0)
                ev_count = row.get('EventCount', 1)
                if lat_val and lon_val and -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                    heat_data.append([lat_val, lon_val, ev_count])

            if heat_data:
                plugins.HeatMap(
                    heat_data,
                    radius=18, blur=14, max_zoom=8,
                    gradient={0.4: 'blue', 0.65: 'lime', 0.85: 'orange', 1: 'red'}
                ).add_to(event_group)

            event_group.add_to(m)

        # 战略航道
        if show_routes:
            route_group = folium.FeatureGroup(name='战略航道 🚢')

            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
            if os.path.exists(routes_path):
                with open(routes_path, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)

                for feature in routes_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'LineString':
                        coords = [[c[1], c[0]] for c in coords]
                    name = props.get('name', props.get('name_en', ''))
                    color = props.get('color', '#FF6B35')
                    desc = props.get('description', '')
                    distance = props.get('distance', '')
                    duration = props.get('duration', '')
                    operator = props.get('operator', '')

                    route_popup = f"""
                    <div style="min-width:260px;font-family:Arial,sans-serif;">
                        <h3 style="color:{color};margin:0 0 8px 0;">🚢 {name}</h3>
                        <table style="width:100%;font-size:12px;">
                            <tr><td style="padding:3px 6px;color:#666;"><b>航程</b></td><td style="padding:3px 6px;">{distance}</td></tr>
                            <tr><td style="padding:3px 6px;color:#666;"><b>航行时间</b></td><td style="padding:3px 6px;">{duration}</td></tr>
                            <tr><td style="padding:3px 6px;color:#666;"><b>主导方</b></td><td style="padding:3px 6px;">{operator}</td></tr>
                        </table>
                        <div style="margin-top:8px;font-size:12px;color:#555;line-height:1.5;">{desc}</div>
                    </div>
                    """

                    folium.PolyLine(
                        locations=coords,
                        weight=4.5,
                        color=color,
                        opacity=0.85,
                        popup=folium.Popup(route_popup, max_width=280),
                        tooltip=f"{name} — {distance}"
                    ).add_to(route_group)

            route_group.add_to(m)

        # 冲突事件
        if show_conflicts:
            conf_group = folium.FeatureGroup(name='地缘冲突 ⚠️')
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            conf_path = os.path.join(geo_dir, 'conflicts.geojson')
            if os.path.exists(conf_path):
                with open(conf_path, 'r', encoding='utf-8') as f:
                    conf_data = json.load(f)
                for feature in conf_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'Point':
                        lat, lon = coords[1], coords[0]
                        cat = props.get('category', 'general')
                        color = CATEGORY_COLORS.get(cat, '#E53935')
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"<b>{props.get('name', '')}</b><br>{props.get('description', '')}",
                            tooltip=props.get('name', ''),
                            icon=folium.Icon(color='red', icon='warning', prefix='fa')
                        ).add_to(conf_group)
            conf_group.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        plugins.Fullscreen(position='topright').add_to(m)
        plugins.MousePosition().add_to(m)

        try:
            from streamlit_folium import st_folium
            st_folium(m, width=None, height=600, returned_objects=[])
        except ImportError:
            st.error("请安装 streamlit-folium: pip install streamlit-folium")
            st.info("或者取消图层控制中的Folium相关内容")

    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔗 大北极国家地缘博弈关系网络图谱</h3>', unsafe_allow_html=True)
    st.caption("节点大小=影响力 | 线条颜色=关系类型 | 线宽=关系强度 | 支持按历史阶段切换")

    period_select = st.selectbox(
        "选择历史时期",
        ["all", "2018-2021", "2022-2024"],
        format_func=lambda x: "全部时期" if x == "all" else x,
        label_visibility="collapsed"
    )
    layout_style = st.selectbox(
        "网络布局",
        ["circular", "tiered"],
        format_func=lambda x: {"circular": "圆形布局", "tiered": "分层布局"}.get(x, x)
    )

    st.markdown("""
    <div class="rel-legend">
        <div class="rel-item"><div class="rel-line" style="background:#43A047"></div>合作关系</div>
        <div class="rel-item"><div class="rel-line" style="background:#FF6B35;border-style:dashed"></div>竞争关系</div>
        <div class="rel-item"><div class="rel-line" style="background:#E53935;border-style:dotted"></div>对抗关系</div>
    </div>
    """, unsafe_allow_html=True)

    net_data = load_geopolitics_network(period_select)
    fig_net = create_network_graph(net_data, layout_style=layout_style)
    st.plotly_chart(fig_net, use_container_width=True)

    # 网络统计
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("节点数", len(net_data['nodes']))
    with stat_cols[1]:
        st.metric("关系数", len(net_data['links']))
    with stat_cols[2]:
        coop_count = sum(1 for l in net_data['links'] if l['relation'] == 'cooperation')
        st.metric("合作关系", coop_count)
    with stat_cols[3]:
        conflict_count = sum(1 for l in net_data['links'] if l['relation'] in ('competition', 'confrontation'))
        st.metric("竞争/对抗", conflict_count)

    st.markdown("#### 核心关系详情")
    rel_df = pd.DataFrame(net_data['links'])
    rel_df['source_name'] = rel_df['source'].map(lambda x: COUNTRY_NAMES.get(x, x))
    rel_df['target_name'] = rel_df['target'].map(lambda x: COUNTRY_NAMES.get(x, x))
    rel_df['relation_cn'] = rel_df['relation'].map({'cooperation': '合作', 'competition': '竞争', 'confrontation': '对抗'})
    display_df = rel_df[['source_name', 'relation_cn', 'target_name', 'strength']].rename(
        columns={'source_name': '主体A', 'relation_cn': '关系', 'target_name': '主体B', 'strength': '强度'}
    ).sort_values('强度', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📝 各国北极政策文本关键词分析</h3>', unsafe_allow_html=True)
    st.caption("基于各国北极政策白皮书文本，提取关键词并进行情感分析")

    fig_sent = create_sentiment_chart(policy_texts, height=320)
    st.plotly_chart(fig_sent, use_container_width=True)

    st.markdown("""
    **情感分析解读：** 中国的北极政策文本情感值最高，反映合作导向的治理观；
    俄罗斯近年情感值转负，体现军事对抗性增强；北欧国家普遍呈正面倾向，强调环境保护与国际合作。
    """, unsafe_allow_html=False)

    fig_wc = create_word_freq_chart(policy_texts, height=420)
    st.plotly_chart(fig_wc, use_container_width=True)

    st.markdown("#### 各国政策核心主张")
    summary_cols = st.columns(3)
    country_data = {
        'RUS': ('俄罗斯', '#E53935', '强调北极主权、安全与航道管控，通过军事部署强化存在，核动力破冰船为战略工具'),
        'USA': ('美国', '#1565C0', '坚持航行自由，将中俄定位北极挑战者，通过国防部北极战略应对竞争'),
        'CHN': ('中国', '#FF0000', '定位『近北极国家』与『利益攸关方』，倡导『人类命运共同体』理念，侧重科技合作'),
        'NOR': ('挪威', '#FF6F00', '推动巴伦支海合作与环境保护，主张以国际法框架解决争端'),
        'CAN': ('加拿大', '#43A047', '强调北极主权和西北航道管辖，注重原住民权益和环境保护'),
        'DNK': ('丹麦', '#FFA726', '通过格陵兰发挥北极影响力，推动气候科学和北极治理'),
    }
    for i, (code, (name, color, desc)) in enumerate(country_data.items()):
        with summary_cols[i]:
            st.markdown(f"""
            <div class="country-card" style="border-color:{color};">
                <h4 style="color:{color};">🏳️ {name}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔬 大北极科考站详细信息</h3>', unsafe_allow_html=True)
    st.caption("点击展开查看科考站详情，包括所属国、设立年份、研究领域和技术方向")

    features = stations_data.get('features', [])
    if not features:
        st.info("科考站数据加载中...")
    else:
        all_countries = sorted(set(f.get('properties', {}).get('country', '未知') for f in features))
        country_filter_st = st.multiselect("按国家筛选", all_countries, default=all_countries)
        filtered = [f for f in features if f.get('properties', {}).get('country', '未知') in country_filter_st]

        color_map = {
            '中国': '#E53935', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6F00', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726', '挪威/国际': '#FF6F00',
            '加拿大': '#43A047',
        }

        for feature in filtered:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            name = props.get('name', '未知')
            country = props.get('country', '未知')
            established = props.get('established', 'N/A')
            research = props.get('research_focus', [])
            tech = props.get('tech_domain', 'N/A')
            desc = props.get('description', '')
            lon, lat = geom.get('coordinates', [0, 0])[0], geom.get('coordinates', [0, 0])[1]
            color = color_map.get(country, '#757575')

            with st.expander(f"🏰 {name}  ({country} · {established})"):
                info_cols = st.columns([1, 2])
                with info_cols[0]:
                    st.markdown(f"""
                    **所属国：** {country}<br>
                    **设立年份：** {established}<br>
                    **坐标：** {lat:.2f}°N, {lon:.2f}°E<br>
                    **技术方向：** {tech}
                    """)
                with info_cols[1]:
                    st.markdown("**研究领域：**")
                    if research:
                        for r in research:
                            st.markdown(f"  • {r}")
                    st.markdown(f"**简介：** {desc}")

        st.markdown("#### 科考站统计概览")
        country_counts = {}
        for f in features:
            c = f.get('properties', {}).get('country', '未知')
            country_counts[c] = country_counts.get(c, 0) + 1
        stat_cc = st.columns(len(country_counts))
        for i, (country, count) in enumerate(sorted(country_counts.items(), key=lambda x: -x[1])):
            color = color_map.get(country, '#757575')
            with stat_cc[i]:
                st.metric(country, count)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 GDELT 事件统计分析</h3>', unsafe_allow_html=True)

    if not yc_df.empty:
        import plotly.graph_objects as go
        yearly = yc_df.groupby('year')['EventCount'].sum()

        fig_yr = go.Figure(go.Bar(
            x=yearly.index, y=yearly.values,
            marker_color='#1E88E5',
            hovertemplate='%{x}年: %{y}起事件<extra></extra>'
        ))
        fig_yr.update_layout(
            xaxis_title='年份', yaxis_title='事件总数',
            template='plotly_white', height=300,
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_yr, use_container_width=True)

        st.markdown("#### 国家事件排名")
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
            height=350, margin=dict(l=100, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        st.markdown("#### 情感倾向年度变化")
        tone_yearly = yc_df.groupby('year')['AvgTone'].mean()
        fig_tone = go.Figure()
        fig_tone.add_trace(go.Scatter(
            x=tone_yearly.index, y=tone_yearly.values,
            mode='lines+markers', name='平均情感值',
            line=dict(color='#FF6B35', width=2.5),
            marker=dict(size=6), fill='tozeroy', fillcolor='rgba(255,107,53,0.1)'
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
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("数据来源: GDELT全球事件数据库 · 北极政策白皮书 · INTERACT科考站数据库")
