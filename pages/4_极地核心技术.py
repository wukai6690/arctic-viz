"""
模块4：极地核心技术竞争与合作
专利气泡图 + 技术合作网络 + 技术-地缘联动看板
重制版：高级UI、精细化图表
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_patent_data, load_tech_network, load_gdelt_data
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, create_patent_bubble, create_patent_heatmap, create_tech_geopolitics_chart

st.set_page_config(page_title="技术竞争", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    .page-header {
        background: linear-gradient(135deg, #4A148C 0%, #7B1FA2 50%, #9C27B0 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 18px 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(123,31,162,0.2);
    }
    .page-header h1 { color: white !important; font-size: 1.55rem; font-weight: 700; margin: 0 0 0.3rem 0; }
    .page-header p { color: rgba(255,255,255,0.82) !important; font-size: 0.83rem; margin: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 18px; font-weight: 600; font-size: 0.85rem; }
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
    .milestone-card {
        background: white; border-radius: 12px; padding: 0.9rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06); border-top: 3px solid;
        text-align: center;
    }
    .milestone-card .ms-year { font-size: 1.3rem; font-weight: 800; }
    .milestone-card .ms-event { font-size: 0.75rem; color: #546E7A; margin-top: 4px; line-height: 1.4; }
</style>
<div class="page-header">
    <h1>⚙️ 极地核心技术竞争与合作</h1>
    <p>专利时空分布 · 技术合作网络 · 「技术-地缘」双轴联动看板</p>
</div>
""", unsafe_allow_html=True)


# 加载数据
patent_df = load_patent_data()
tech_net = load_tech_network()
grid_df, yc_df = load_gdelt_data()

# ============ KPI ============
total_patents = patent_df['patent_count'].sum()
top_cat = patent_df.groupby('category')['patent_count'].sum().idxmax()
top_country_pat = patent_df.groupby('country')['patent_count'].sum().idxmax()

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">📊 专利申请总数</div>
        <div class="kpi-val" style="color:#7B1FA2">{total_patents:,}</div>
        <div class="kpi-sub">2000-2024 累计</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🏆 最活跃领域</div>
        <div class="kpi-val" style="color:#1E88E5">{top_cat}</div>
        <div class="kpi-sub">专利最多</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🌐 专利大国</div>
        <div class="kpi-val" style="color:#E53935">{COUNTRY_NAMES.get(top_country_pat, top_country_pat)}</div>
        <div class="kpi-sub">累计专利最多</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">⚙️ 技术类别</div>
        <div class="kpi-val" style="color:#43A047">5</div>
        <div class="kpi-sub">核心领域</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 主区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 专利分布", "🔗 技术合作网络", "⚡ 技术-地缘联动", "📈 趋势分析", "🗺️ 国家排名"
])


with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 极地核心技术专利时空分布</h3>', unsafe_allow_html=True)

    filter_cols = st.columns(3)
    with filter_cols[0]:
        selected_years = st.slider("年份范围", 2000, 2024, (2010, 2024))
    with filter_cols[1]:
        all_cats = patent_df['category'].unique().tolist()
        selected_cats = st.multiselect("技术类别", all_cats, default=all_cats)
    with filter_cols[2]:
        all_countries = patent_df['country'].unique().tolist()
        selected_countries = st.multiselect("国家/地区", all_countries,
                                           default=['RUS', 'CHN', 'USA', 'NOR'])

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

        # 气泡图
        st.markdown("#### 专利气泡图（尺寸=数量，颜色=国家）")
        fig_bubble = px.scatter(
            filtered, x='year', y='patent_count',
            size='avg_quality', color='country',
            hover_name='country', hover_data={'avg_quality': True},
            color_discrete_map={k: COUNTRY_COLORS.get(k, '#757575') for k in filtered['country'].unique()},
            labels={'patent_count': '专利数量', 'avg_quality': '平均质量分'}
        )
        fig_bubble.update_layout(
            height=420, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            margin=dict(l=60, r=20, t=40, b=60),
            template='plotly_white'
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

        # 热力图
        st.markdown("#### 专利热力图（按国家×技术类别）")
        fig_heat = create_patent_heatmap(filtered, height=380)
        st.plotly_chart(fig_heat, use_container_width=True)

        # 排名
        st.markdown("#### 国家专利排名")
        country_summary = filtered.groupby('country').agg(
            专利总数=('patent_count', 'sum'), 平均质量=('avg_quality', 'mean')
        ).sort_values('专利总数', ascending=False)
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
            template='plotly_white'
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # 技术类别饼图
        st.markdown("#### 技术类别结构")
        cat_summary = filtered.groupby('category').agg(
            专利数=('patent_count', 'sum'), 平均质量=('avg_quality', 'mean')
        ).sort_values('专利数', ascending=False)
        fig_cat = go.Figure(go.Pie(
            labels=cat_summary.index, values=cat_summary['专利数'],
            hole=0.4, textinfo='percent+label',
            marker_colors=['#1E88E5', '#E53935', '#43A047', '#FF6B35', '#9C27B0'],
            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
        ))
        fig_cat.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_cat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔗 极地技术合作网络图谱</h3>', unsafe_allow_html=True)
    st.caption("节点=科研/产业机构 | 连线强度=合作紧密程度 | 颜色=国家")

    import plotly.graph_objects as go
    fig_tech_net = go.Figure()
    nodes = tech_net['nodes']
    links = tech_net['links']
    n = len(nodes)
    angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
    r = 1.4

    link_colors = {
        'joint_research': '#43A047', 'satellite_data': '#1E88E5',
        'climate_monitoring': '#66BB6A', 'climate_modeling': '#9CCC65',
        'research': '#90A4AE', 'internal': '#8B0000',
        'oil_gas_dev': '#FF6B35', 'shipbuilding': '#FFA726',
        'academic': '#9C27B0', 'arctic_research': '#607D8B'
    }

    for link in links:
        if link['source'] in angles and link['target'] in angles:
            lx = [r * np.cos(angles[link['source']]), r * np.cos(angles[link['target']])]
            ly = [r * np.sin(angles[link['source']]), r * np.sin(angles[link['target']])]
            fig_tech_net.add_trace(go.Scatter(
                x=lx, y=ly, mode='lines',
                line=dict(width=link['strength'] / 12,
                         color=link_colors.get(link['type'], '#B0BEC5')),
                hoverinfo='text',
                text=f"{link['source']}-{link['target']}: {link['type']} ({link['strength']})",
                showlegend=False
            ))

    node_x = [r * np.cos(angles[n['id']]) for n in nodes]
    node_y = [r * np.sin(angles[n['id']]) for n in nodes]
    node_colors = [COUNTRY_COLORS.get(n['country'], '#757575') for n in nodes]
    node_sizes = [22 if n['type'] == 'research' else 15 for n in nodes]

    fig_tech_net.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color='white')),
        text=[n['name'] for n in nodes],
        textposition='outside', textfont=dict(size=9),
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
    st.plotly_chart(fig_tech_net, use_container_width=True)

    # 合作详情
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
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>⚡「技术-地缘」双轴联动看板</h3>', unsafe_allow_html=True)
    st.markdown("专利趋势与地缘活动时间线同步展示，反映技术演进如何赋能地缘权力延伸", unsafe_allow_html=False)

    fig_link = create_tech_geopolitics_chart(patent_df, yc_df if not yc_df.empty else None, height=420)
    st.plotly_chart(fig_link, use_container_width=True)

    # 关键时间节点
    st.markdown("#### 关键时间节点")
    milestones = [
        (2009, "俄罗斯北极点海底插旗", "#E53935"),
        (2013, "中国成为北极理事会观察员", "#FF0000"),
        (2017, "「冰上丝绸之路」提出", "#FF6B35"),
        (2022, "俄乌冲突重塑北极格局", "#8B0000"),
    ]
    ms_cols = st.columns(4)
    for i, (yr, event, color) in enumerate(milestones):
        with ms_cols[i]:
            st.markdown(f"""
            <div class="milestone-card" style="border-color:{color};">
                <div class="ms-year" style="color:{color};">{yr}</div>
                <div class="ms-event">{event}</div>
            </div>
            """, unsafe_allow_html=True)

    year_range_t = st.slider("年份范围", 2000, 2024, (2010, 2024))
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
            corr_color = "#43A047" if corr > 0.5 else "#FF6B35" if corr > 0 else "#E53935"
            st.markdown(f"""
            <div style="background:#F3E5F5;padding:1rem;border-radius:12px;border-left:4px solid #7B1FA2;margin-top:1rem;">
            <b>相关性分析：</b>专利申请量与GDELT地缘事件数的皮尔逊相关系数为 <b style="color:{corr_color}">{corr:.3f}</b>。
            {'技术进步与地缘扩张呈现显著正相关，验证了「技术赋能地缘」假说。' if corr > 0.5 else '两者相关性较弱，可能存在滞后效应或受其他因素影响。'}
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📈 技术竞争趋势深度分析</h3>', unsafe_allow_html=True)

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
            line=dict(color=COUNTRY_COLORS.get(country, '#757575'), width=2.5),
            marker=dict(size=5),
            hovertemplate=f'{COUNTRY_NAMES.get(country, country)}: %{{y}}项<extra></extra>'
        ))
    fig_trend.update_layout(
        xaxis_title='年份', yaxis_title='专利申请量',
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # 雷达图
    st.markdown("#### 五国极地技术竞争力对比（雷达图）")
    radar_categories = ['遥感探测', '冰区船舶', '油气开采', '冻土工程', '气候模拟']
    radar_data = {
        '中国': [85, 90, 70, 65, 75],
        '美国': [95, 75, 60, 80, 95],
        '俄罗斯': [60, 95, 95, 90, 55],
        '挪威': [75, 70, 50, 70, 85],
        '加拿大': [70, 65, 55, 75, 80],
    }
    radar_colors = {
        '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
        '挪威': '#FF6F00', '加拿大': '#43A047'
    }

    fig_radar = go.Figure()
    for country, values in radar_data.items():
        r_c = int(radar_colors[country][1:3], 16)
        g_c = int(radar_colors[country][3:5], 16)
        b_c = int(radar_colors[country][5:7], 16)
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=radar_categories + [radar_categories[0]],
            fill='toself', fillcolor=f'rgba({r_c},{g_c},{b_c},0.12)',
            line=dict(color=radar_colors[country], width=2),
            name=country,
            hovertemplate='%{theta}: %{r}<extra></extra>'
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=450, margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("""
    **技术竞争格局解读：**
    - **中国**：冰区船舶和遥感探测领域优势明显，整体快速追赶
    - **美国**：遥感探测与气候模拟领先，综合技术实力最强
    - **俄罗斯**：冰区船舶和油气开采绝对领先，但遥感领域相对薄弱
    - **北欧国家**：气候模拟和环境监测见长，侧重环保和科研
    """, unsafe_allow_html=False)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗺️ 各国技术布局详情</h3>', unsafe_allow_html=True)

    country_detail = st.selectbox("选择国家", ['CHN', 'USA', 'RUS', 'NOR', 'CAN'],
                                 format_func=lambda x: COUNTRY_NAMES.get(x, x))

    country_data = patent_df[patent_df['country'] == country_detail]
    if not country_data.empty:
        cat_yearly = country_data.groupby(['year', 'category'])['patent_count'].sum().reset_index()
        cat_pivot = cat_yearly.pivot(index='year', columns='category', values='patent_count').fillna(0)

        import plotly.graph_objects as go
        fig_detail = go.Figure()
        colors_cat = ['#1E88E5', '#E53935', '#43A047', '#FF6B35', '#9C27B0']
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
            height=420, margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_detail, use_container_width=True)

        total = country_data['patent_count'].sum()
        avg_quality = country_data['avg_quality'].mean()
        cat_count = country_data.groupby('category')['patent_count'].sum().idxmax()
        st.markdown(f"""
        **{COUNTRY_NAMES.get(country_detail, country_detail)} 技术布局概况：**
        - 累计专利：{total:,} 项
        - 平均质量：{avg_quality:.1f}
        - 最强领域：{cat_count}（专利最多）
        """)
    else:
        st.info("该国家暂无数据")
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("数据来源: Patent database simulation · 技术合作数据基于公开报道整理")
