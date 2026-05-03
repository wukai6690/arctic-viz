"""
模块3：大北极国家地缘战略格局
矢量图层 + 大国博弈网络图谱 + 政策文本NLP分析
增强版：多时期网络切换、更多科考站、冲突事件标注
"""

import streamlit as st
import pandas as pd
import sys, os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_geopolitics_network, load_policy_texts, load_stations
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, CATEGORY_COLORS, CAT_LABELS, create_network_graph, create_word_freq_chart, create_sentiment_chart, create_3d_globe_annotate

st.set_page_config(page_title="地缘战略格局", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    .page-header { background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%);
        padding: 1.2rem 1.5rem; border-radius: 0 0 14px 14px; margin-bottom: 1.5rem; }
    .page-header h1 { color: white !important; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .page-header p { color: rgba(255,255,255,0.85) !important; font-size: 0.85rem; margin: 0.3rem 0 0 0; }
    .country-badge { display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;margin:2px; }
    .relation-badge { display:inline-block;padding:2px 8px;border-radius:8px;font-size:0.75rem;margin:1px; }
    /* 确保主内容区白色背景，文字深色 */
    section[data-testid="stMain"] > div { background: white !important; }
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li, section[data-testid="stMain"] span { color: #1a1a2e !important; }
    .stMarkdown p, .stMarkdown li { color: #1a1a2e !important; }
    .stTabs [data-baseweb="tab"] { color: #333 !important; }
</style>
<div class="page-header">
    <h1>🏛️ 大北极国家地缘战略格局模块</h1>
    <p>军事基地 · 科考站 · 主权边界 · 地缘博弈网络 · 政策文本分析</p>
</div>
""", unsafe_allow_html=True)

# 加载数据
grid_df, yc_df = load_gdelt_data()
policy_texts = load_policy_texts()
stations_data = load_stations()

# ============ KPI ============
kpi_cols = st.columns(4)
total_events = yc_df['EventCount'].sum() if not yc_df.empty else 38500
with kpi_cols[0]:
    st.metric("GDELT 北极事件", f"{total_events:,}", delta="2018-2024")
with kpi_cols[1]:
    avg_tone = yc_df['AvgTone'].mean() if not yc_df.empty else 0
    st.metric("平均情感倾向", f"{avg_tone:.2f}", delta="偏正面" if avg_tone > 0 else "偏负面")
with kpi_cols[2]:
    top_country = yc_df.groupby('CountryCode')['EventCount'].sum().idxmax() if not yc_df.empty else 'RUS'
    st.metric("最活跃国家", COUNTRY_NAMES.get(top_country, top_country))
with kpi_cols[3]:
    st.metric("博弈主体", "14个", delta="国家+国际组织")

st.divider()

# ============ 主区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 地缘态势地图", "🔗 博弈关系网络", "📝 政策文本分析", "🔬 科考站详情", "📊 事件统计"
])

with tab1:
    st.markdown("### 🗺️ 大北极地缘战略态势地图")

    col_ctl, col_map = st.columns([1, 4])

    with col_ctl:
        st.markdown("**🕹️ 图层控制**")
        show_stations = st.checkbox("科考站分布", value=True)
        show_routes = st.checkbox("战略航道", value=True)
        show_events = st.checkbox("GDELT事件", value=True)
        show_conflicts = st.checkbox("地缘冲突事件", value=False)

        st.markdown("**🌐 国家筛选**")
        country_filter = st.multiselect(
            "选择国家",
            options=['RUS', 'USA', 'CHN', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR'],
            default=['RUS', 'USA', 'CHN', 'NOR', 'CAN'],
            format_func=lambda x: COUNTRY_NAMES.get(x, x)
        )

        st.markdown("**⏱️ 时间选择**")
        year_select = st.slider("选择年份", 2018, 2024, 2023)

    with col_map:
        import folium
        from folium import plugins

        m = folium.Map(location=[75, 30], zoom_start=3, tiles='cartodbpositron', prefer_canvas=True)

        # 科考站
        if show_stations:
            station_group = folium.FeatureGroup(name='科考站')
            country_colors_map = {
                '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
                '挪威': '#FF6B35', '丹麦': '#FFA726', '芬兰': '#9C27B0',
                '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
                '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726',
                '挪威/国际': '#FF6B35', '俄罗斯': '#8B0000', '加拿大': '#43A047'
            }

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

                popup_html = f"""
                <div style="min-width:280px">
                    <h4 style="color:{color};margin:0 0 8px 0">{name}</h4>
                    <table style="width:100%;font-size:12px">
                        <tr><td><b>所属国</b></td><td>{country}</td></tr>
                        <tr><td><b>设立年份</b></td><td>{props.get('established', 'N/A')}</td></tr>
                        <tr><td><b>研究领域</b></td><td>{', '.join(research[:3]) if research else 'N/A'}</td></tr>
                        <tr><td><b>技术方向</b></td><td>{props.get('tech_domain', 'N/A')}</td></tr>
                        <tr><td colspan="2"><b>简介：</b>{props.get('description', '')[:120]}</td></tr>
                    </table>
                </div>
                """

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    color=color, weight=2,
                    fill=True, fillColor=color, fillOpacity=0.6,
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"{name} ({country})"
                ).add_to(station_group)

            station_group.add_to(m)

        # GDELT 事件热力图
        if show_events and not grid_df.empty:
            year_col = 'Year_local' if 'Year_local' in grid_df.columns else 'Year'
            year_data = grid_df[grid_df.get(year_col, grid_df[year_col] if year_col in grid_df.columns else 2023) == year_select]
            if not year_data.empty:
                lat_col = 'lat_grid' if 'lat_grid' in year_data.columns else 'lat'
                lon_col = 'lon_grid' if 'lon_grid' in year_data.columns else 'lon'
                heat_data = [
                    [row.get(lat_col, 0), row.get(lon_col, 0), row.get('EventCount', 1)]
                    for _, row in year_data.iterrows()
                ]
                plugins.HeatMap(heat_data, radius=20, blur=12,
                               gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
                               ).add_to(m)

        # 航道
        if show_routes:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            routes_path = os.path.join(geo_dir, 'arctic_routes.geojson')
            if os.path.exists(routes_path):
                with open(routes_path, 'r', encoding='utf-8') as f:
                    routes_data = json.load(f)
                route_group = folium.FeatureGroup(name='战略航道')
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

                    folium.PolyLine(
                        locations=coords, weight=4, color=color, opacity=0.8,
                        popup=f"<b>{name}</b><br>{desc}"
                    ).add_to(route_group)
                route_group.add_to(m)

        # 冲突事件（备选图层）
        if show_conflicts:
            geo_dir = os.path.join(os.path.dirname(__file__), '..', 'geojson')
            conf_path = os.path.join(geo_dir, 'conflicts.geojson')
            if os.path.exists(conf_path):
                with open(conf_path, 'r', encoding='utf-8') as f:
                    conf_data = json.load(f)
                conf_group = folium.FeatureGroup(name='地缘冲突')
                for feature in conf_data.get('features', []):
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    if not geom or 'coordinates' not in geom:
                        continue
                    coords = geom['coordinates']
                    if geom['type'] == 'Point':
                        lat, lon = coords[1], coords[0]
                        cat = props.get('category', 'general')
                        color = CATEGORY_COLORS.get(cat, '#757575')
                        folium.Marker(
                            location=[lat, lon],
                            popup=f"<b>{props.get('name', '')}</b><br>{props.get('description', '')}",
                            icon=folium.Icon(color='red', icon='warning', prefix='fa')
                        ).add_to(conf_group)
                conf_group.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        plugins.Fullscreen(position='topright').add_to(m)
        plugins.MousePosition().add_to(m)

        try:
            from streamlit_folium import st_folium
            st_folium(m, width=None, height=580, returned_objects=[])
        except ImportError:
            st.error("请安装 streamlit-folium: pip install streamlit-folium")

    # 图例
    st.markdown("**图例**")
    legend_cols = st.columns(5)
    legend_items = [
        ("中国", "#FF0000"), ("美国", "#1565C0"), ("俄罗斯", "#8B0000"),
        ("挪威", "#FF6B35"), ("丹麦", "#FFA726"), ("芬兰", "#9C27B0"),
        ("瑞典", "#00BCD4"), ("冰岛", "#795548"), ("国际", "#607D8B"), ("航道", "#FF6B35")
    ]
    for i, (label, color) in enumerate(legend_items):
        with legend_cols[i % 5]:
            st.markdown(f"<div style='display:flex;align-items:center;gap:6px;font-size:0.8rem;'>"
                       f"<div style='width:10px;height:10px;border-radius:50%;background:{color};'></div>"
                       f"<span>{label}</span></div>", unsafe_allow_html=True)

with tab2:
    st.markdown("### 🔗 大北极国家地缘博弈关系网络图谱")
    st.caption("节点大小=影响力 | 线条颜色=关系类型 | 线宽=关系强度 | 支持按历史阶段切换")

    # 时期切换
    period_select = st.selectbox("选择历史时期", ["all", "2018-2021", "2022-2024"],
                                format_func=lambda x: "全部时期" if x == "all" else x)
    net_data = load_geopolitics_network(period_select)
    layout_style = st.selectbox("网络布局", ["circular", "tiered"], format_func=lambda x: {"circular": "圆形布局", "tiered": "分层布局"}.get(x, x))

    st.markdown("**关系类型图例**")
    rel_legend = st.columns(3)
    with rel_legend[0]:
        st.markdown('<div style="display:flex;align-items:center;gap:8px"><div style="width:30px;height:3px;background:#43A047;border-radius:2px;"></div><span>合作关系</span></div>', unsafe_allow_html=True)
    with rel_legend[1]:
        st.markdown('<div style="display:flex;align-items:center;gap:8px"><div style="width:30px;height:3px;background:#FF6B35;border-radius:2px;border-style:dashed;"></div><span>竞争关系</span></div>', unsafe_allow_html=True)
    with rel_legend[2]:
        st.markdown('<div style="display:flex;align-items:center;gap:8px"><div style="width:30px;height:3px;background:#E53935;border-radius:2px;border-style:dotted;"></div><span>对抗关系</span></div>', unsafe_allow_html=True)

    fig_net = create_network_graph(net_data, layout_style=layout_style)
    st.plotly_chart(fig_net, use_container_width=True)

    # 网络统计
    st.markdown("#### 网络结构统计")
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

    # 详细关系表
    st.markdown("#### 核心关系详情")
    rel_df = pd.DataFrame(net_data['links'])
    rel_df['source_name'] = rel_df['source'].map(lambda x: COUNTRY_NAMES.get(x, x))
    rel_df['target_name'] = rel_df['target'].map(lambda x: COUNTRY_NAMES.get(x, x))
    rel_df['relation_cn'] = rel_df['relation'].map({'cooperation': '合作', 'competition': '竞争', 'confrontation': '对抗'})
    display_df = rel_df[['source_name', 'relation_cn', 'target_name', 'strength']].rename(
        columns={'source_name': '主体A', 'relation_cn': '关系', 'target_name': '主体B', 'strength': '强度'}
    ).sort_values('强度', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### 📝 各国北极政策文本关键词分析")
    st.caption("基于各国北极政策白皮书文本，提取高频关键词并进行情感分析")

    # 情感分析
    fig_sent = create_sentiment_chart(policy_texts, height=300)
    st.plotly_chart(fig_sent, use_container_width=True)

    st.markdown("""
    **情感分析解读：** 中国的北极政策文本情感值最高，反映合作导向的治理观；
    俄罗斯近年情感值转负，体现军事对抗性增强；北欧国家普遍呈正面倾向，强调环境保护与国际合作。
    """)

    # 关键词柱状图
    st.markdown("#### 政策关键词词频对比")
    fig_wc = create_word_freq_chart(policy_texts, height=420)
    st.plotly_chart(fig_wc, use_container_width=True)

    # 各国政策摘要
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
            <div style="border-left:4px solid {color};padding-left:12px;margin-bottom:1rem;">
                <b style="color:{color};font-size:1rem">{name}</b>
                <p style="font-size:0.82rem;color:#546E7A;line-height:1.6;margin-top:4px">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 🔬 大北极科考站详细信息")

    st.caption("点击科考站名称展开详细信息，包括所属国、设立年份、研究领域和技术方向")

    features = stations_data.get('features', [])
    if not features:
        st.info("科考站数据加载中...")
    else:
        # 国家筛选
        all_countries = sorted(set(f.get('properties', {}).get('country', '未知') for f in features))
        country_filter_st = st.multiselect("按国家筛选", all_countries, default=all_countries)

        filtered_features = [f for f in features
                           if f.get('properties', {}).get('country', '未知') in country_filter_st]

        color_map = {
            '中国': '#E53935', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6B35', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726', '挪威/国际': '#FF6B35',
            '加拿大': '#43A047', '俄罗斯': '#8B0000'
        }

        for feature in filtered_features:
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

            with st.expander(f"🏰 **{name}**  ({country})"):
                info_cols = st.columns([1, 2])
                with info_cols[0]:
                    st.markdown(f"""
                    **所属国：** {country}<br>
                    **设立年份：** {established}<br>
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

with tab5:
    st.markdown("### 📊 GDELT 事件统计分析")

    if not yc_df.empty:
        # 年度趋势
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

        # 国家排名
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

        # 情感趋势
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

st.divider()
st.caption("数据来源: GDELT全球事件数据库 · 北极政策白皮书 · INTERACT科考站数据库")
