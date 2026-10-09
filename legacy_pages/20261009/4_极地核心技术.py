"""
模块4：极地核心技术竞争与合作
浅色研究主题 · 原版功能保留
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_patent_data, load_tech_network, load_gdelt_data
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, create_patent_bubble, create_patent_heatmap, create_tech_geopolitics_chart

st.set_page_config(page_title="技术竞争", page_icon="◎", layout="wide")

from src.presentation import apply_presentation, show_chart
apply_presentation('technology')


st.markdown("""

<div class="page-header">
    <h1> 极地核心技术竞争与合作</h1>
    <p>专利时空分布 · 技术合作网络 · 「技术-地缘」双轴联动看板</p>
</div>
""", unsafe_allow_html=True)


# ============ 数据 ============
patent_df = load_patent_data()
tech_net = load_tech_network()
grid_df, yc_df = load_gdelt_data()

total_patents = patent_df['patent_count'].sum()
top_cat = patent_df.groupby('category')['patent_count'].sum().idxmax()
top_country_pat = patent_df.groupby('country')['patent_count'].sum().idxmax()

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label"> 专利申请总数</div>
        <div class="kpi-val" style="color:#867697">{total_patents:,}</div>
        <div class="kpi-sub">2000-2024 累计</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 最活跃领域</div>
        <div class="kpi-val" style="color:#4b7883">{top_cat}</div>
        <div class="kpi-sub">专利最多</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 专利大国</div>
        <div class="kpi-val" style="color:#b37564">{COUNTRY_NAMES.get(top_country_pat, top_country_pat)}</div>
        <div class="kpi-sub">累计专利最多</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 技术类别</div>
        <div class="kpi-val" style="color:#5d8770">5</div>
        <div class="kpi-sub">核心领域</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 标签页 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([" 专利分布", " 合作网络", " 技术-地缘联动", " 趋势分析", " 国家排名"])


with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 极地核心技术专利时空分布</h3>', unsafe_allow_html=True)

    filter_cols = st.columns(3)
    with filter_cols[0]:
        selected_years = st.slider("年份范围", 2000, 2024, (2010, 2024), key="patent_filter_years")
    with filter_cols[1]:
        all_cats = patent_df['category'].unique().tolist()
        selected_cats = st.multiselect("技术类别", all_cats, default=all_cats)
    with filter_cols[2]:
        all_countries = patent_df['country'].unique().tolist()
        selected_countries = st.multiselect("国家/地区", all_countries, default=['RUS', 'CHN', 'USA', 'NOR'])

    filtered = patent_df[
        (patent_df['year'] >= selected_years[0]) &
        (patent_df['year'] <= selected_years[1]) &
        (patent_df['category'].isin(selected_cats)) &
        (patent_df['country'].isin(selected_countries))
    ]

    if filtered.empty:
        st.info("当前筛选条件下无数据，请调整筛选条件")
    else:
        import plotly.express as px
        import plotly.graph_objects as go

        st.markdown("#### 专利气泡图（尺寸=数量，颜色=国家）")
        fig_bubble = px.scatter(
            filtered, x='year', y='patent_count',
            size='avg_quality', color='country',
            hover_name='country',
            color_discrete_map={k: COUNTRY_COLORS.get(k, '#757575') for k in filtered['country'].unique()},
        )
        fig_bubble.update_layout(
            height=420, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            margin=dict(l=60, r=20, t=40, b=60),
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(54,80,65,0.8)')
        )
        show_chart(fig_bubble, use_container_width=True)

        st.markdown("#### 专利热力图（按国家×技术类别）")
        fig_heat = create_patent_heatmap(filtered, height=380)
        show_chart(fig_heat, use_container_width=True)

        col_rank, col_cat = st.columns(2)
        with col_rank:
            st.markdown("#### 国家专利排名")
            country_summary = filtered.groupby('country').agg(专利总数=('patent_count', 'sum'), 平均质量=('avg_quality', 'mean')).sort_values('专利总数', ascending=False)
            fig_rank = go.Figure(go.Bar(
                x=country_summary['专利总数'],
                y=[COUNTRY_NAMES.get(c, c) for c in country_summary.index],
                orientation='h',
                marker_color=[COUNTRY_COLORS.get(c, '#757575') for c in country_summary.index],
                hovertemplate='%{y}: %{x} 项专利<extra></extra>'
            ))
            fig_rank.update_layout(
                xaxis_title='专利总数', yaxis_title='国家',
                height=300, margin=dict(l=100, r=20, t=20, b=40),
                template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(54,80,65,0.8)'),
                xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
                yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
            )
            show_chart(fig_rank, use_container_width=True)
        with col_cat:
            st.markdown("#### 技术类别结构")
            cat_summary = filtered.groupby('category').agg(专利数=('patent_count', 'sum')).sort_values('专利数', ascending=False)
            fig_cat = go.Figure(go.Pie(
                labels=cat_summary.index, values=cat_summary['专利数'],
                hole=0.4, textinfo='percent+label',
                marker_colors=['#4b7883', '#b37564', '#5d8770', '#b19059', '#867697'],
                hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
            ))
            fig_cat.update_layout(
                height=380, margin=dict(l=20, r=20, t=20, b=20),
                template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(54,80,65,0.8)')
            )
            show_chart(fig_cat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 极地技术合作网络图谱</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    fig_tech_net = go.Figure()
    nodes = tech_net['nodes']
    links = tech_net['links']
    n = len(nodes)
    angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
    r = 1.4

    link_colors = {
        'joint_research': '#5d8770', 'satellite_data': '#4b7883',
        'climate_monitoring': '#5d8770', 'climate_modeling': '#86efac',
        'research': '#9ca3af', 'internal': '#b91c1c',
        'oil_gas_dev': '#b19059', 'shipbuilding': '#b69855',
        'academic': '#867697', 'arctic_research': '#6b7280'
    }

    for link in links:
        if link['source'] in angles and link['target'] in angles:
            lx = [r * np.cos(angles[link['source']]), r * np.cos(angles[link['target']])]
            ly = [r * np.sin(angles[link['source']]), r * np.sin(angles[link['target']])]
            fig_tech_net.add_trace(go.Scatter(
                x=lx, y=ly, mode='lines',
                line=dict(width=link['strength'] / 12, color=link_colors.get(link['type'], '#9ca3af')),
                hoverinfo='text',
                text=f"{link['source']}-{link['target']}: {link['type']} ({link['strength']})",
                showlegend=False
            ))

    node_x = [r * np.cos(angles[n['id']]) for n in nodes]
    node_y = [r * np.sin(angles[n['id']]) for n in nodes]
    node_colors = [COUNTRY_COLORS.get(n['country'], '#6b7280') for n in nodes]
    node_sizes = [22 if n['type'] == 'research' else 15 for n in nodes]

    fig_tech_net.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color='white')),
        text=[n['name'] for n in nodes],
        textposition='top center', textfont=dict(size=9),
        hovertemplate='%{text}<extra></extra>',
        showlegend=False
    ))

    fig_tech_net.update_layout(
        margin=dict(l=20, r=20, t=40, b=20), height=560,
        xaxis=dict(visible=False, range=[-2.8, 2.8]),
        yaxis=dict(visible=False, range=[-2.8, 2.8]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    show_chart(fig_tech_net, use_container_width=True)

    st.markdown("#### 核心技术合作关系详情")
    link_df = pd.DataFrame(links)
    link_df['type_cn'] = link_df['type'].map({
        'joint_research': '联合研究', 'satellite_data': '卫星数据共享',
        'climate_monitoring': '气候监测', 'climate_modeling': '气候模拟',
        'research': '学术合作', 'internal': '内部协作',
        'oil_gas_dev': '油气开发', 'shipbuilding': '造船合作',
        'academic': '学术交流', 'arctic_research': '极地研究'
    })
    display_links = link_df[['source', 'target', 'type_cn', 'strength']].rename(
        columns={'source': '机构A', 'target': '机构B', 'type_cn': '合作类型', 'strength': '强度'}
    ).sort_values('强度', ascending=False)
    st.dataframe(display_links, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>「技术-地缘」双轴联动看板</h3>', unsafe_allow_html=True)

    fig_link = create_tech_geopolitics_chart(patent_df, yc_df if not yc_df.empty else None, height=420)
    show_chart(fig_link, use_container_width=True)

    st.markdown("#### 关键时间节点")
    milestones = [
        (2009, "俄罗斯北极点海底插旗", "#b37564"),
        (2013, "中国成为北极理事会观察员", "#ac665a"),
        (2017, "「冰上丝绸之路」提出", "#b19059"),
        (2022, "俄乌冲突重塑北极格局", "#b91c1c"),
    ]
    ms_cols = st.columns(4)
    for i, (yr, event, color) in enumerate(milestones):
        with ms_cols[i]:
            st.markdown(f"""
            <div class="ms-card" style="border-color:{color};">
                <div class="ms-year" style="color:{color};">{yr}</div>
                <div class="ms-event">{event}</div>
            </div>
            """, unsafe_allow_html=True)

    year_range_t = st.slider("年份范围", 2000, 2024, (2010, 2024), key="patent_trend_years")
    pat_trend = patent_df[
        (patent_df['year'] >= year_range_t[0]) &
        (patent_df['year'] <= year_range_t[1])
    ].groupby('year')['patent_count'].sum()

    if not yc_df.empty:
        gdelt_trend = yc_df[
            (yc_df['year'] >= year_range_t[0]) &
            (yc_df['year'] <= year_range_t[1])
        ].groupby('year')['EventCount'].sum()

        merged = pd.merge(
            pat_trend.reset_index().rename(columns={'patent_count': 'patents'}),
            gdelt_trend.reset_index().rename(columns={'EventCount': 'events'}),
            on='year', how='inner'
        )
        if len(merged) > 2:
            corr = merged['patents'].corr(merged['events'])
            corr_color = "#5d8770" if corr > 0.5 else "#b19059" if corr > 0 else "#b37564"
            st.markdown(f"""
            <div style="background:rgba(168,85,247,0.06);padding:1rem;border-radius:12px;border-left:4px solid #867697;margin-top:1rem;">
            <b>相关性分析：</b>专利申请量与GDELT地缘事件数的皮尔逊相关系数为 <b style="color:{corr_color}">{corr:.3f}</b>。
            {'样例序列呈正相关；这不能验证真实世界中的因果关系或研究假说。' if corr > 0.5 else '样例序列相关性较弱；真实关系仍需检索、标注与模型检验。'}
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 技术竞争趋势深度分析</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    trend_years = range(2000, 2025)
    top_countries = ['CHN', 'USA', 'RUS', 'NOR', 'CAN']

    fig_trend = go.Figure()
    for country in top_countries:
        c_data = patent_df[patent_df['country'] == country]
        yearly = c_data.groupby('year')['patent_count'].sum().reindex(trend_years, fill_value=0)
        fig_trend.add_trace(go.Scatter(
            x=list(trend_years), y=yearly.values,
            mode='lines+markers', name=COUNTRY_NAMES.get(country, country),
            line=dict(color=COUNTRY_COLORS.get(country, '#6b7280'), width=2.5),
            marker=dict(size=5),
            hovertemplate=f'{COUNTRY_NAMES.get(country, country)}: %{{y}}项<extra></extra>'
        ))
    fig_trend.update_layout(
        xaxis_title='年份', yaxis_title='专利申请量',
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)'),
        xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        yaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
    )
    show_chart(fig_trend, use_container_width=True)

    st.markdown("#### 五国技术指标雷达图 · 原版示例")
    radar_categories = ['遥感探测', '冰区船舶', '油气开采', '冻土工程', '气候模拟']
    radar_data = {
        '中国': [85, 90, 70, 65, 75],
        '美国': [95, 75, 60, 80, 95],
        '俄罗斯': [60, 95, 95, 90, 55],
        '挪威': [75, 70, 50, 70, 85],
        '加拿大': [70, 65, 55, 75, 80],
    }
    radar_colors_map = {
        '中国': '#ac665a', '美国': '#4b7883', '俄罗斯': '#b91c1c',
        '挪威': '#b19059', '加拿大': '#5d8770'
    }

    fig_radar = go.Figure()
    for country, values in radar_data.items():
        r_c = int(radar_colors_map[country][1:3], 16)
        g_c = int(radar_colors_map[country][3:5], 16)
        b_c = int(radar_colors_map[country][5:7], 16)
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=radar_categories + [radar_categories[0]],
            fill='toself', fillcolor=f'rgba({r_c},{g_c},{b_c},0.12)',
            line=dict(color=radar_colors_map[country], width=2),
            name=country,
            hovertemplate='%{theta}: %{r}<extra></extra>'
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=450, margin=dict(l=20, r=20, t=40, b=40),
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)')
    )
    show_chart(fig_radar, use_container_width=True)

    st.markdown("""
    雷达分数为原版手工设定，用于演示多指标比较。正式分析需要统一指标口径、补充数据来源并说明评分方法；目前不能据此判断各国优势或排名。
    """)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 各国技术布局详情</h3>', unsafe_allow_html=True)

    country_detail = st.selectbox("选择国家", ['CHN', 'USA', 'RUS', 'NOR', 'CAN'],
                                 format_func=lambda x: COUNTRY_NAMES.get(x, x))

    country_data = patent_df[patent_df['country'] == country_detail]
    if not country_data.empty:
        cat_yearly = country_data.groupby(['year', 'category'])['patent_count'].sum().reset_index()
        cat_pivot = cat_yearly.pivot(index='year', columns='category', values='patent_count').fillna(0)

        import plotly.graph_objects as go
        fig_detail = go.Figure()
        colors_cat = ['#4b7883', '#b37564', '#5d8770', '#b19059', '#867697']
        for i, col in enumerate(cat_pivot.columns):
            fig_detail.add_trace(go.Scatter(
                x=cat_pivot.index, y=cat_pivot[col],
                mode='lines+markers', name=col,
                line=dict(color=colors_cat[i % len(colors_cat)], width=2),
                marker=dict(size=4)
            ))
        fig_detail.update_layout(
            xaxis_title='年份', yaxis_title='专利申请量',
            template='plotly_white', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=420, margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(54,80,65,0.8)'),
            xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
            yaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        )
        show_chart(fig_detail, use_container_width=True)

        total = country_data['patent_count'].sum()
        avg_quality = country_data['avg_quality'].mean()
        cat_count = country_data.groupby('category')['patent_count'].sum().idxmax()
        st.markdown(f"""
        **{COUNTRY_NAMES.get(country_detail, country_detail)} 技术布局概况：**
        - 累计专利：{total:,} 项
        - 平均质量：{avg_quality:.1f}
        - 最强领域：{cat_count}
        """)
    else:
        st.info("该国家暂无数据")
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("专利数量为原版模拟数据；技术合作关系与雷达分数为演示设定。正式专利记录与关系证据尚未接入。")
