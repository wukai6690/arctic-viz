"""
模块3：北极地缘战略格局
浅色研究主题 · 原版功能保留
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_gdelt_data, load_stations, load_geopolitics_network, load_policy_texts
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, CATEGORY_COLORS, CAT_LABELS, create_network_graph, create_word_freq_chart, create_sentiment_chart

st.set_page_config(page_title="地缘战略格局", page_icon="◎", layout="wide")

from src.presentation import apply_presentation, show_chart
apply_presentation('geopolitics')


st.markdown("""

<div class="page-header">
    <h1> 大北极国家地缘战略格局</h1>
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
        <div class="kpi-label"> 科考站总数</div>
        <div class="kpi-val" style="color:#5d8770">{total_stations}</div>
        <div class="kpi-sub">大北极研究网络</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> GDELT事件</div>
        <div class="kpi-val" style="color:#ac665a">{total_events:,}</div>
        <div class="kpi-sub">2018-2024累计</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 涉及国家</div>
        <div class="kpi-val" style="color:#4b7883">{len(country_counts)}</div>
        <div class="kpi-sub">主要北极国家</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 平均情感</div>
        <div class="kpi-val" style="color:{'#5d8770' if avg_tone > 0 else '#b37564'}">{avg_tone:+.2f}</div>
        <div class="kpi-sub">{'偏正面' if avg_tone > 0 else '偏负面'}</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 标签页 ============
from src.evidence_views import render_candidate_events

source_tab, tab1, tab2, tab3, tab4 = st.tabs(["已采集事件线索"," 国家概况", " 博弈网络", " 政策分析", " 科考站详情"])


with source_tab:
    render_candidate_events()

with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 大北极国家地缘概况</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    if country_counts:
        sorted_c = sorted(country_counts.items(), key=lambda x: -x[1])
        country_colors_map = {
            '中国': '#ac665a', '美国': '#4b7883', '俄罗斯': '#b91c1c',
            '挪威': '#b19059', '丹麦': '#b69855', '芬兰': '#867697',
            '瑞典': '#06b6d4', '冰岛': '#78716c', '日本': '#d6d3d1',
            '国际合作（多国）': '#6b7280', '加拿大': '#5d8770',
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
            font=dict(color='rgba(54,80,65,0.8)'),
            xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)',
                      title_font_color='rgba(54,80,65,0.5)'),
            yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
        )
        show_chart(fig_country, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 大北极地缘博弈网络</h3>', unsafe_allow_html=True)

    period = st.selectbox("选择时期", ['all', '2018-2021', '2022-2024'],
                         format_func=lambda x: {'all': '全部 (2018-2024)', '2018-2021': '2018-2021 相对稳定期', '2022-2024': '2022-2024 俄乌冲突后'}.get(x, x))

    net_p = load_geopolitics_network(period)
    fig_net = create_network_graph(net_p, height=520)
    show_chart(fig_net, use_container_width=True)

    # 关系统计
    rel_colors_map = {'cooperation': '#5d8770', 'competition': '#b19059', 'confrontation': '#ac665a'}
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
    st.markdown('<h3> 各国北极政策文本分析</h3>', unsafe_allow_html=True)

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
            show_chart(fig_wf, use_container_width=True)
        with col_se:
            fig_se = create_sentiment_chart(policy_texts, height=400)
            show_chart(fig_se, use_container_width=True)
    else:
        st.info("政策文本数据加载中...")
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 科考站详情一览</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    # 地图展示科考站
    fig_map = go.Figure(go.Scattergeo())
    fig_map.update_layout(
        geo=dict(
            scope='world',
            projection_type='orthographic',
            center=dict(lat=75, lon=0),
            lataxis_range=[55, 90],
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
            bgcolor='#f5f7f3'
        ),
        paper_bgcolor='#f5f7f3',
        margin=dict(l=0, r=0, t=10, b=10), height=480,
    )

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

        fig_map.add_trace(go.Scattergeo(
            lon=[lon], lat=[lat],
            mode='markers+text',
            marker=dict(size=14, color=color, line=dict(width=2, color='white')),
            text=[name], textposition='top center',
            textfont=dict(size=9, color='white'),
            hovertemplate=(
                f"<b style='color:{color}'> {name}</b><br>"
                f"<extra></extra>"
                f"<b>国家:</b> {country}<br>"
                f"<b>设立:</b> {props.get('established', 'N/A')}<br>"
                f"<b>坐标:</b> {lat:.2f}°N, {lon:.2f}°E<br>"
                f"<b>研究:</b> {', '.join(props.get('research_focus', [])[:3])}"
            ),
            showlegend=False
        ))

    show_chart(fig_map, use_container_width=True)

    # 科考站列表
    st.markdown("####  科考站列表")
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
st.caption("已采集事件线索来自 GDELT 原始记录，尚待逐条核验。原版国家关系、政策词频与科考站资料保留为示例或待核验线索。")
