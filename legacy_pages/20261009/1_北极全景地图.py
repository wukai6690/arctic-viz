"""
模块1：北极全景地图 — 原版功能与实景资料
浅色研究主题 · 原版功能保留 — 前沿3D + 交互地图
"""

import streamlit as st
import sys, os, json, folium, streamlit.components.v1 as components
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_stations, load_gdelt_data, load_geopolitics_network
from src.viz import ARCTIC_THEME, COUNTRY_NAMES, COUNTRY_COLORS, create_3d_globe_annotate

st.set_page_config(
    page_title="北极全景地图",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.presentation import apply_presentation, show_chart
apply_presentation('map')


# ============ 全局 CSS ============
st.markdown("""

""", unsafe_allow_html=True)


from src.presentation import section_title
section_title('ARCTIC ATLAS', '北极全景地图', '沿用全景地图、热力时序与关系网络，加入可追溯的地点实景。')

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
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #4b7883;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;"></div>
        <div style="font-size:1.5rem;font-weight:800;color:#4b7883;line-height:1;">{station_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">科考站</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #ac665a;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;"></div>
        <div style="font-size:1.5rem;font-weight:800;color:#b37564;line-height:1;">{total_events:,}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">示例事件记录</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #867697;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;"></div>
        <div style="font-size:1.5rem;font-weight:800;color:#867697;line-height:1;">{link_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">示例关系连线</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #5d8770;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;"></div>
        <div style="font-size:1.5rem;font-weight:800;color:#5d8770;line-height:1;">{node_count}</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">国家节点</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:14px;padding:0.9rem 1rem;text-align:center;border-top:3px solid #b19059;">
        <div style="font-size:0.68rem;color:var(--text3);font-weight:600;margin-bottom:4px;"></div>
        <div style="font-size:1.5rem;font-weight:800;color:#b19059;line-height:1;">3</div>
        <div style="font-size:0.68rem;color:var(--text3);margin-top:3px;">核心航道</div>
    </div>
</div>
"""



# ============ 主标签页 ============
from src.evidence_views import render_place_gallery, create_local_map

photo_tab, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "地点实景",
    " 3D极地全景",
    " 交互地图",
    " 战略统计",
    " GDELT热力时序",
    " 国家关系网络",
])


# =============================================
with photo_tab:
    render_place_gallery()

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
    show_chart(fig_globe, use_container_width=True)

    st.markdown("""
    <div style="display:flex;gap:12px;margin-top:0.8rem;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#ac665a;border-radius:50%;display:inline-block;"></span>中国
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#4b7883;border-radius:50%;display:inline-block;"></span>美国
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#b91c1c;border-radius:50%;display:inline-block;"></span>俄罗斯
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#b19059;border-radius:50%;display:inline-block;"></span>挪威
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:10px;height:10px;background:#5d8770;border-radius:50%;display:inline-block;"></span>加拿大
        </div>
        <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:var(--text3);">
            <span style="width:3px;height:10px;background:#b19059;display:inline-block;"></span>航道
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================
# Tab 2: 交互地图
# =============================================
with tab2:
    tile_options = {
        "浅色地理轮廓 · 本地": None,
        "开放街道图 · OpenStreetMap": "OpenStreetMap",
    }

    map_ctrl_cols = st.columns([1, 1, 1, 1])
    with map_ctrl_cols[0]:
        selected_tile = st.selectbox("底图", list(tile_options.keys()), index=0)
    with map_ctrl_cols[1]:
        center_lat = st.number_input("中心纬度", value=75.0, min_value=60.0, max_value=90.0, step=0.5, format="%.1f")
    with map_ctrl_cols[2]:
        center_lon = st.number_input("中心经度", value=0.0, min_value=-180.0, max_value=180.0, step=5.0, format="%.1f")
    with map_ctrl_cols[3]:
        zoom_level = st.slider("缩放级别", 2, 10, 3)

    try:
        if tile_options[selected_tile] is None:
            m = create_local_map([center_lat, center_lon],zoom_level)
        else:
            m = folium.Map(location=[center_lat,center_lon],zoom_start=zoom_level,tiles=tile_options[selected_tile])

        # 添加科考站标记
        station_colors_map = {
            '中国': '#ac665a', '美国': '#4b7883', '俄罗斯': '#b91c1c',
            '挪威': '#b19059', '丹麦': '#b69855', '芬兰': '#867697',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#5d8770',
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
            <div style="width:280px;font-family:'Segoe UI',Arial,sans-serif;background:#f5f7f3;border-radius:10px;overflow:hidden;border:1px solid rgba(54,80,65,0.16);">
                <div style="background:{color};color:#3c594c;padding:10px 14px;font-weight:700;font-size:14px;">
                     {name}
                </div>
                <div style="padding:12px;font-size:12px;line-height:1.9;color:rgba(54,80,65,0.85);">
                    <table style="width:100%;border-collapse:collapse;">
                        <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;width:60px;">国家</td><td style="color:#3c594c;">{country}</td></tr>
                        <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">坐标</td><td style="color:#3c594c;">{lat:.2f}°N, {lon:.2f}°E</td></tr>
                        <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">设立</td><td style="color:#3c594c;">{props.get('established', 'N/A')}</td></tr>
                        <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">技术</td><td style="color:#3c594c;">{props.get('tech_domain', 'N/A')}</td></tr>
                        <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">研究</td><td style="color:#3c594c;">{', '.join(props.get('research_focus', [])[:3])}</td></tr>
                    </table>
                    <div style="margin-top:10px;padding:8px 10px;background:rgba(54,80,65,0.16);border-radius:6px;font-size:11px;color:rgba(54,80,65,0.6);line-height:1.5;">
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
                tooltip=folium.Tooltip(f"{name} ({country}) · 原版待核验地点", permanent=True, direction='top')
            ).add_to(m)

        # 添加航道线
        if routes_data:
            route_colors_map = {
                '东北航道': '#b19059', '西北航道': '#4b7883', '跨北极航道': '#ac665a'
            }
            for feat in routes_data.get('features', []):
                props = feat.get('properties', {})
                geom = feat.get('geometry', {})
                if geom and 'coordinates' in geom:
                    coords = geom['coordinates']
                    route_name = props.get('name', '未知航道')
                    color = route_colors_map.get(route_name, '#6b7280')

                    popup_html = f"""
                    <div style="width:260px;font-family:'Segoe UI',Arial,sans-serif;background:#f5f7f3;border-radius:10px;overflow:hidden;border:1px solid rgba(54,80,65,0.16);">
                        <div style="background:{color};color:#3c594c;padding:10px 14px;font-weight:700;font-size:13px;">
                             {route_name}
                        </div>
                        <div style="padding:12px;font-size:12px;line-height:1.9;color:rgba(54,80,65,0.85);">
                            <table style="width:100%;">
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;width:60px;">起点</td><td style="color:#3c594c;">{props.get('start', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">终点</td><td style="color:#3c594c;">{props.get('end', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">航程</td><td style="color:#3c594c;">{props.get('distance', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">航行时间</td><td style="color:#3c594c;">{props.get('duration', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">主导方</td><td style="color:#3c594c;">{props.get('operator', 'N/A')}</td></tr>
                                <tr><td style="font-weight:600;color:rgba(54,80,65,0.5);padding:3px 0;">通航期</td><td style="color:#3c594c;">{props.get('open_months', 'N/A')}</td></tr>
                            </table>
                            <div style="margin-top:10px;padding:8px 10px;background:rgba(54,80,65,0.16);border-radius:6px;font-size:11px;color:rgba(54,80,65,0.6);line-height:1.5;">
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
        import math
        arctic_circle_coords = []
        for i in range(361):
            lat_c = 66.5
            lon_c = i
            arctic_circle_coords.append([lat_c, lon_c])
        folium.PolyLine(
            locations=arctic_circle_coords,
            color='rgba(54,80,65,0.25)',
            weight=1.2,
            dash_array='6,4',
            tooltip='北极圈 (66.5°N)'
        ).add_to(m)

        # Embed through the local component bundle and redraw on tab changes.
        from streamlit_folium import st_folium
        st_folium(m, height=580, use_container_width=True,
                  key='original_interactive_map', returned_objects=[])
    except Exception as e:
        st.error(f"地图渲染出错: {e}")

    st.markdown("""
    <div style="display:flex;gap:16px;margin-top:0.8rem;flex-wrap:wrap;">
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#ac665a;border-radius:50%;display:inline-block;margin-right:4px;"></span>中国</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#4b7883;border-radius:50%;display:inline-block;margin-right:4px;"></span>美国</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#b91c1c;border-radius:50%;display:inline-block;margin-right:4px;"></span>俄罗斯</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#b19059;border-radius:50%;display:inline-block;margin-right:4px;"></span>挪威</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:12px;height:12px;background:#5d8770;border-radius:50%;display:inline-block;margin-right:4px;"></span>加拿大</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:20px;height:3px;background:#b19059;display:inline-block;margin-right:4px;"></span>东北航道</div>
        <div style="font-size:0.75rem;color:var(--text3);"><span style="width:20px;height:3px;background:#4b7883;display:inline-block;margin-right:4px;"></span>西北航道</div>
    </div>
    """, unsafe_allow_html=True)


# =============================================
# Tab 3: 战略统计
# =============================================
with tab3:
    st.markdown(stat_html, unsafe_allow_html=True)
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
            '中国': '#ac665a', '美国': '#4b7883', '俄罗斯': '#b91c1c',
            '挪威': '#b19059', '丹麦': '#b69855', '芬兰': '#867697',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#5d8770',
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
                height=max(350, len(sorted_c) * 48),
                margin=dict(l=140, r=50, t=40, b=40),
                paper_bgcolor='#f5f7f3', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(54,80,65,0.85)'),
                xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.7)',
                          title_font_color='rgba(54,80,65,0.5)'),
                yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
                title=dict(text='🇬🇸 各国北极科考站数量', font=dict(color='white', size=14)),
            )
            show_chart(fig_c, use_container_width=True)

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
                title=dict(text=' 科考站国家分布', font=dict(color='white', size=14)),
                height=350, margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='#f5f7f3',
                font=dict(color='rgba(54,80,65,0.8)')
            )
            show_chart(fig_pie, use_container_width=True)

    # 科考站详细信息表
    st.markdown("####  科考站详情列表")
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
            paper_bgcolor='#f5f7f3', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(54,80,65,0.8)'),
            xaxis=dict(title='', tickfont_color='rgba(54,80,65,0.7)'),
            yaxis=dict(title='', tickfont_color='rgba(54,80,65,0.8)', ticks='outside'),
        )
        show_chart(fig_heat, use_container_width=True)

    # 年度趋势
    if not filtered.empty:
        yearly = filtered.groupby('year')['EventCount'].sum()
        yearly_tone = filtered.groupby('year')['AvgTone'].mean()

        fig_yearly = go.Figure()
        fig_yearly.add_trace(go.Bar(
            x=yearly.index, y=yearly.values,
            name='事件数量', yaxis='y1',
            marker_color='#ac665a', opacity=0.8,
            hovertemplate='%{x}年: %{y}起事件<extra></extra>'
        ))
        fig_yearly.add_trace(go.Scatter(
            x=yearly_tone.index, y=yearly_tone.values,
            name='情感值', yaxis='y2',
            mode='lines+markers',
            line=dict(color='#b19059', width=2.5),
            marker=dict(size=7),
            hovertemplate='%{x}年情感: %{y:.2f}<extra></extra>'
        ))
        fig_yearly.update_layout(
            xaxis_title='年份', yaxis_title='事件数量', yaxis2=dict(title='情感值', side='right', overlaying='y', showgrid=False),
            template='plotly_white', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=380, margin=dict(l=60, r=60, t=20, b=40),
            paper_bgcolor='#f5f7f3',
            font=dict(color='rgba(54,80,65,0.8)'),
            xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.7)'),
            yaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.7)'),
        )
        show_chart(fig_yearly, use_container_width=True)

        # 国家事件排名
        st.markdown("####  GDELT事件国家排名")
        country_events = filtered.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=False)
        fig_rank = go.Figure(go.Bar(
            x=[COUNTRY_NAMES.get(c, c) for c in country_events.index[:10]],
            y=country_events.values[:10],
            marker_color='#b37564',
            hovertemplate='%{x}: %{y}起<extra></extra>'
        ))
        fig_rank.update_layout(
            xaxis_title='国家', yaxis_title='事件数量',
            height=320, margin=dict(l=60, r=20, t=20, b=60),
            template='plotly_white',
            paper_bgcolor='#f5f7f3',
            font=dict(color='rgba(54,80,65,0.8)'),
            xaxis=dict(tickfont_color='rgba(54,80,65,0.8)', tickangle=30),
            yaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        )
        show_chart(fig_rank, use_container_width=True)
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
            'cooperation': '#5d8770',
            'competition': '#b19059',
            'confrontation': '#ac665a',
        }

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

        node_x = [r * np.cos(angles[n['id']]) for n in nodes]
        node_y = [r * np.sin(angles[n['id']]) for n in nodes]
        node_colors = [COUNTRY_COLORS.get(n.get('country', ''), '#6b7280') for n in nodes]
        node_sizes = [26 if n.get('type') == 'research' else 16 for n in nodes]

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
            paper_bgcolor='#f5f7f3',
        )
        show_chart(fig_net, use_container_width=True)

        # 关系统计
        rel_stats = {}
        for link in links:
            r = link.get('relation', 'unknown')
            rel_stats[r] = rel_stats.get(r, 0) + 1

        rel_cn = {'cooperation': ' 合作', 'competition': ' 竞争', 'confrontation': ' 对抗'}
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
st.caption("地点照片的作者、许可和来源见各图片下方。实景关联事件来自已保存的 GDELT 候选记录；其余原版图层与统计为待核验资料或示例。")
