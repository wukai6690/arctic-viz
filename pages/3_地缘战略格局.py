"""
模块3：北极地缘战略格局
深色沉浸主题 v6.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_stations, load_geopolitics_network, load_policy_texts
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, CATEGORY_COLORS, CAT_LABELS, create_network_graph, create_word_freq_chart, create_sentiment_chart

st.set_page_config(page_title="地缘战略格局", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    :root { --bg: #0a0e1a; --bg2: #111827; --card: #1a2236; --card2: #1f2a42; --border: rgba(255,255,255,0.07); --text: rgba(255,255,255,0.92); --text2: rgba(255,255,255,0.6); --text3: rgba(255,255,255,0.35); }
    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] { background: var(--bg) !important; }
    section[data-testid="stMain"] > div { background: transparent !important; }
    [data-testid="stMainBlockContainer"] { background: transparent !important; padding-top: 0 !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e1a, #111827) !important; }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    section[data-testid="stMain"] p, section[data-testid="stMain"] span, section[data-testid="stMain"] h1, section[data-testid="stMain"] h2, section[data-testid="stMain"] h3, section[data-testid="stMain"] h4, section[data-testid="stMain"] li { color: var(--text) !important; }
    .stMarkdown p, .stMarkdown li { color: var(--text2) !important; }
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px !important; padding: 8px 18px !important; font-weight: 600 !important; font-size: 0.85rem !important; color: var(--text2) !important; background: transparent !important; }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.06) !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(34,197,94,0.2) !important; color: #86efac !important; }
    [data-testid="stMetricValue"] { color: var(--text) !important; }
    [data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: 0.8rem !important; }
    [data-testid="stCaption"] { color: var(--text3) !important; }
    .stCheckbox label { color: var(--text2) !important; }
    [data-baseweb="select"] > div { color: var(--text) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: var(--text) !important; }
    .stMultiSelect [data-baseweb="select"] > div { color: var(--text) !important; }
    .streamlit-expander { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }
    .streamlit-expander summary { color: var(--text) !important; font-weight: 600 !important; }
    .stAlert { border-radius: 12px !important; }
    hr { border: none !important; border-top: 1px solid var(--border) !important; }
    .page-header { background: linear-gradient(135deg, #0f172a 0%, #14532d 100%); padding: 1.8rem 2rem; border-radius: 0 0 18px 18px; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(34,197,94,0.15); position: relative; overflow: hidden; }
    .page-header::before { content: ''; position: absolute; top: -50%; right: -5%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(34,197,94,0.06) 0%, transparent 70%); pointer-events: none; }
    .page-header h1 { color: white !important; font-size: 1.6rem; font-weight: 700; margin: 0 0 0.3rem 0; position: relative; z-index: 1; }
    .page-header p { color: rgba(255,255,255,0.5) !important; font-size: 0.83rem; margin: 0; position: relative; z-index: 1; }
    .dk-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 1.3rem; margin-bottom: 1.2rem; }
    .dk-card:hover { background: var(--card2); }
    .dk-card h3 { font-size: 0.95rem; font-weight: 700; color: var(--text); margin: 0 0 1rem 0; padding-bottom: 0.7rem; border-bottom: 1px solid var(--border); }
    .kpi-row { display: flex; gap: 14px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .kpi-box { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.3rem; flex: 1; min-width: 160px; }
    .kpi-box .kpi-label { font-size: 0.7rem; color: var(--text3); font-weight: 600; margin-bottom: 4px; }
    .kpi-box .kpi-val { font-size: 1.4rem; font-weight: 800; }
    .kpi-box .kpi-sub { font-size: 0.68rem; color: var(--text3); margin-top: 2px; }
    .country-bar-item { display: flex; align-items: center; gap: 10px; padding: 5px 0; }
    .country-bar-item .cb-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
    .country-bar-item .cb-name { font-size: 0.78rem; color: var(--text2); min-width: 50px; }
    .country-bar-item .cb-bar-bg { flex: 1; height: 5px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
    .country-bar-item .cb-bar-fill { height: 5px; border-radius: 3px; }
    .country-bar-item .cb-count { font-size: 0.75rem; font-weight: 700; min-width: 40px; text-align: right; }
</style>
<div class="page-header">
    <h1>🏛️ 大北极国家地缘战略格局</h1>
    <p>军事基地 · 科考站 · 主权边界 · 地缘博弈网络 · 政策文本分析</p>
</div>
""", unsafe_allow_html=True)


# ============ 数据 ============
grid_df, yc_df = load_gdelt_data()
stations_data = load_stations()
net_data = load_geopolitics_network('all')
policy_texts = load_policy_texts()

total_stations = len(stations_data.get('features', []))
total_events = int(yc_df['EventCount'].sum()) if not yc_df.empty else 0
avg_tone = yc_df['AvgTone'].mean() if not yc_df.empty else 0
country_counts = {}
for feat in stations_data.get('features', []):
    c = feat.get('properties', {}).get('country', '未知')
    country_counts[c] = country_counts.get(c, 0) + 1

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">🔬 科考站总数</div>
        <div class="kpi-val" style="color:#22c55e">{total_stations}</div>
        <div class="kpi-sub">大北极研究网络</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">📊 GDELT事件</div>
        <div class="kpi-val" style="color:#ef4444">{total_events:,}</div>
        <div class="kpi-sub">2018-2024累计</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🌐 涉及国家</div>
        <div class="kpi-val" style="color:#60a5fa">{len(country_counts)}</div>
        <div class="kpi-sub">主要北极国家</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">⚡ 平均情感</div>
        <div class="kpi-val" style="color:{'#4ade80' if avg_tone > 0 else '#f87171'}">{avg_tone:+.2f}</div>
        <div class="kpi-sub">{'偏正面' if avg_tone > 0 else '偏负面'}</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 标签页 ============
tab1, tab2, tab3, tab4 = st.tabs(["🏳️ 国家概况", "🔗 博弈网络", "📝 政策分析", "🗺️ 科考站详情"])


with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🏳️ 大北极国家地缘概况</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    if country_counts:
        sorted_c = sorted(country_counts.items(), key=lambda x: -x[1])
        country_colors_map = {
            '中国': '#ef4444', '美国': '#3b82f6', '俄罗斯': '#b91c1c',
            '挪威': '#f97316', '丹麦': '#eab308', '芬兰': '#a855f7',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#22c55e',
        }
        total_s = sum(country_counts.values())
        for c_name, c_count in sorted_c:
            color = country_colors_map.get(c_name, '#6b7280')
            pct = c_count / total_s * 100
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

        fig_country = go.Figure(go.Bar(
            y=[c[0] for c in sorted_c],
            x=[c[1] for c in sorted_c],
            orientation='h',
            marker_color=[country_colors_map.get(c[0], '#6b7280') for c in sorted_c],
            hovertemplate='%{y}: %{x}个科考站<extra></extra>'
        ))
        fig_country.update_layout(
            height=max(320, len(sorted_c) * 42),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=120, r=30, t=20, b=40),
            xaxis_title='科考站数量',
            yaxis_title='',
            showlegend=False,
            font=dict(color='rgba(255,255,255,0.8)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)',
                      title_font_color='rgba(255,255,255,0.5)'),
            yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
        )
        st.plotly_chart(fig_country, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔗 大北极地缘博弈网络</h3>', unsafe_allow_html=True)

    period = st.selectbox("选择时期", ['all', '2018-2021', '2022-2024'],
                         format_func=lambda x: {'all': '全部 (2018-2024)', '2018-2021': '2018-2021 相对稳定期', '2022-2024': '2022-2024 俄乌冲突后'}.get(x, x))

    net_p = load_geopolitics_network(period)
    fig_net = create_network_graph(net_p, height=520)
    st.plotly_chart(fig_net, use_container_width=True)

    # 关系统计
    rel_colors_map = {'cooperation': '#22c55e', 'competition': '#f97316', 'confrontation': '#ef4444'}
    rel_names = {'cooperation': '合作', 'competition': '竞争', 'confrontation': '对抗'}
    rel_counts = {}
    for link in net_p.get('links', []):
        r = link.get('relation', 'unknown')
        rel_counts[r] = rel_counts.get(r, 0) + 1

    rel_cols = st.columns(3)
    for i, (rel, color) in enumerate(rel_colors_map.items()):
        with rel_cols[i]:
            count = rel_counts.get(rel, 0)
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:var(--card);border-radius:12px;border-top:3px solid {color};">
                <div style="font-size:1.4rem;font-weight:800;color:{color};">{count}</div>
                <div style="font-size:0.72rem;color:var(--text3);">{rel_names.get(rel, rel)}关系</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>📝 各国北极政策文本分析</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    if policy_texts:
        policy_country = st.selectbox("选择国家", list(policy_texts.keys()),
                                    format_func=lambda x: COUNTRY_NAMES.get(x, x))
        if policy_country in policy_texts:
            text_data = policy_texts[policy_country]
            st.markdown(f"""
            <div style="background:var(--card);border-radius:12px;padding:1rem;border-left:4px solid {COUNTRY_COLORS.get(policy_country, '#6b7280')};margin-bottom:1rem;">
                <div style="font-weight:700;color:var(--text);margin-bottom:0.4rem;">{COUNTRY_NAMES.get(policy_country, policy_country)} · {text_data.get('year', 'N/A')}年</div>
                <div style="font-size:0.8rem;color:var(--text3);margin-bottom:0.5rem;">{text_data.get('summary', '')}</div>
                <div style="font-size:0.78rem;color:var(--text2);font-style:italic;line-height:1.6;">「{text_data.get('text', '')[:200]}...」</div>
            </div>
            """, unsafe_allow_html=True)

        col_wf, col_se = st.columns(2)
        with col_wf:
            fig_wf = create_word_freq_chart(policy_texts, height=400)
            st.plotly_chart(fig_wf, use_container_width=True)
        with col_se:
            fig_se = create_sentiment_chart(policy_texts, height=400)
            st.plotly_chart(fig_se, use_container_width=True)
    else:
        st.info("政策文本数据加载中...")
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗺️ 科考站详情一览</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    # 地图展示科考站
    fig_map = go.Figure(go.Scattergeo(
        scope='world',
        projection_type='orthographic',
        center=dict(lat=75, lon=0),
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
        bgcolor='rgba(10,14,26,0)',
        lataxis_range=[55, 90],
    ))

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

        fig_map.add_trace(go.Scattergeo(
            lon=[lon], lat=[lat],
            mode='markers+text',
            marker=dict(size=14, color=color, line=dict(width=2, color='white')),
            text=[name], textposition='top center',
            textfont=dict(size=9, color='white'),
            hovertemplate=(
                f"<b style='color:{color}'>🔬 {name}</b><br>"
                f"<extra></extra>"
                f"<b>国家:</b> {country}<br>"
                f"<b>设立:</b> {props.get('established', 'N/A')}<br>"
                f"<b>坐标:</b> {lat:.2f}°N, {lon:.2f}°E<br>"
                f"<b>研究:</b> {', '.join(props.get('research_focus', [])[:3])}"
            ),
            showlegend=False
        ))

    fig_map.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=10), height=480,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # 科考站列表
    st.markdown("#### 🔬 科考站列表")
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
            '设立年份': props.get('established', ''),
            '坐标': f"{lat:.2f}°N, {lon:.2f}°E",
            '技术方向': props.get('tech_domain', ''),
            '研究领域': ', '.join(props.get('research_focus', [])[:3]),
        })
    if station_list:
        st.dataframe(pd.DataFrame(station_list), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("数据来源: GDELT 全球事件数据库 · INTERACT 科考站数据库 · 各国北极政策文件")
