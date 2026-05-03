"""
模块1：北极气候环境时空监测
深色沉浸主题 v6.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_ice_data, load_cmip6_forecast, compute_trend, get_seasonal_stats, mk_test, load_climate_data, load_route_data
from src.viz import create_forecast_chart, create_seasonal_heatmap

st.set_page_config(page_title="气候时空监测", page_icon="🌡️", layout="wide")

# 深色主题 CSS
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
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(59,130,246,0.2) !important; color: #93c5fd !important; }
    [data-testid="stMetricValue"] { color: var(--text) !important; }
    [data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: 0.8rem !important; }
    [data-testid="stCaption"] { color: var(--text3) !important; }
    .stCheckbox label { color: var(--text2) !important; }
    [data-baseweb="select"] > div { color: var(--text) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: var(--text) !important; }
    .streamlit-expander { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }
    .streamlit-expander summary { color: var(--text) !important; font-weight: 600 !important; }
    .stAlert { border-radius: 12px !important; }
    hr { border: none !important; border-top: 1px solid var(--border) !important; }
    /* 页面头部 */
    .page-header { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); padding: 1.8rem 2rem; border-radius: 0 0 18px 18px; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(59,130,246,0.15); position: relative; overflow: hidden; }
    .page-header::before { content: ''; position: absolute; top: -50%; right: -5%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%); pointer-events: none; }
    .page-header h1 { color: white !important; font-size: 1.6rem; font-weight: 700; margin: 0 0 0.3rem 0; position: relative; z-index: 1; }
    .page-header p { color: rgba(255,255,255,0.5) !important; font-size: 0.83rem; margin: 0; position: relative; z-index: 1; }
    /* 通用深色卡片 */
    .dk-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 1.3rem; margin-bottom: 1.2rem; }
    .dk-card:hover { background: var(--card2); }
    .dk-card h3 { font-size: 0.95rem; font-weight: 700; color: var(--text); margin: 0 0 1rem 0; padding-bottom: 0.7rem; border-bottom: 1px solid var(--border); }
    .kpi-row { display: flex; gap: 14px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .kpi-box { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.3rem; flex: 1; min-width: 160px; }
    .kpi-box .kpi-label { font-size: 0.7rem; color: var(--text3); font-weight: 600; margin-bottom: 4px; }
    .kpi-box .kpi-val { font-size: 1.4rem; font-weight: 800; }
    .kpi-box .kpi-sub { font-size: 0.68rem; color: var(--text3); margin-top: 2px; }
    .info-card { background: rgba(59,130,246,0.08); border-radius: 12px; padding: 1rem; border-left: 4px solid #3b82f6; }
    .warn-card { background: rgba(239,68,68,0.08); border-radius: 12px; padding: 1rem; border-left: 4px solid #ef4444; }
    .dk-card p, .dk-card span { color: var(--text2) !important; }
    .dk-card h4 { color: var(--text) !important; }
</style>
<div class="page-header">
    <h1>🌡️ 北极气候环境时空监测</h1>
    <p>气温 · 海冰密集度 · CMIP6情景预测 · 航道通航潜力评估 · M-K突变检验</p>
</div>
""", unsafe_allow_html=True)


# ============ 数据加载 ============
df, df_summary, long_df = load_ice_data()
cmip6_df = load_cmip6_forecast()
trend = compute_trend(df_summary)
seasons = get_seasonal_stats(long_df)
climate_df = load_climate_data()

# ============ KPI ============
latest = df_summary['mean'].iloc[-1]
prev = df_summary['mean'].iloc[-2]
first = df_summary['mean'].iloc[0]
total_change = latest - first
pct = total_change / first * 100
min_val = df_summary['minimum'].min()
min_yr = df_summary['minimum'].idxmin()

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">📊 2024年均海冰面积</div>
        <div class="kpi-val" style="color:#60a5fa">{latest:.2f} M km²</div>
        <div class="kpi-sub">较2023年 {latest-prev:+.2f} M km²</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">📉 1979-2024累计变化</div>
        <div class="kpi-val" style="color:#f87171">{total_change:+.2f} M km²</div>
        <div class="kpi-sub">累计变化 {pct:+.1f}%</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">📐 每十年下降速率</div>
        <div class="kpi-val" style="color:#fb923c">{trend['decline_per_decade']:.2f} M km²</div>
        <div class="kpi-sub">R²={trend['r_squared']:.3f}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">⚠️ {min_yr}年历史最低</div>
        <div class="kpi-val" style="color:#ef4444">{min_val:.2f} M km²</div>
        <div class="kpi-sub">夏季最小值</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 主图表区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 趋势与预测", "🗓️ 月度热力图", "🌍 季节对比", "🛳️ 航道评估", "📊 统计分析"
])


with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>📈 海冰面积变化趋势与CMIP6情景预测</h3>', unsafe_allow_html=True)

    ssp126_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP1-2.6'].values[0]
    ssp126_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP1-2.6'].values[0]
    ssp585_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP5-8.5'].values[0]
    ssp585_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP5-8.5'].values[0]

    col_pred1, col_pred2 = st.columns(2)
    with col_pred1:
        st.markdown(f"""
        <div class="info-card">
            <b>🌱 SSP1-2.6 低碳情景</b><br>
            2050年: <b>{ssp126_2050:.2f} M km²</b><br>
            2100年: <b>{ssp126_2100:.2f} M km²</b>
        </div>
        """, unsafe_allow_html=True)
    with col_pred2:
        st.markdown(f"""
        <div class="warn-card">
            <b>🔥 SSP5-8.5 高排放情景</b><br>
            2050年: <b>{ssp585_2050:.2f} M km²</b><br>
            2100年: <b>{ssp585_2100:.2f} M km²</b>
        </div>
        """, unsafe_allow_html=True)

    fig = create_forecast_chart(df_summary, cmip6_df)
    st.plotly_chart(fig, use_container_width=True)

    # M-K 突变检验
    mk_result = mk_test(df_summary['mean'].values)
    mk_cols = st.columns(3)
    with mk_cols[0]:
        st.metric("Z值", f"{mk_result['z_value']:.4f}")
    with mk_cols[1]:
        st.metric("P值", f"{mk_result['p_value']:.6f}")
    with mk_cols[2]:
        st.metric("趋势判定", mk_result['trend'], delta="通过显著性检验" if abs(mk_result['z_value']) > 1.96 else "未通过")

    st.markdown("""
    <div class="dk-card" style="margin-top:1rem;">
    <h4>M-K 突变检验结果解读</h4>
    <p>1979-2024年间，北极年均海冰面积呈显著下降趋势（每十年约减少 0.65 M km²），M-K检验和线性拟合R²=0.89共同确认趋势可信度高。两种CMIP6情景均显示21世纪海冰将持续减少，高排放情景下2100年夏季北极近乎无冰，为「冰上丝绸之路」提供了物理基础。</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗓️ 月度海冰面积热力图（1980-2024）</h3>', unsafe_allow_html=True)

    year_range = st.slider("年份范围", 1980, 2024, (1990, 2024))
    color_scheme = st.selectbox("配色方案", ["Ice", "YlOrRd", "Viridis"],
                                format_func=lambda x: {"Ice": "冰蓝色", "YlOrRd": "红黄渐变", "Viridis": "科学紫绿"}.get(x, x))

    fig2 = create_seasonal_heatmap(long_df, year_range=year_range, color_scheme=color_scheme)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    <p><b>解读指南：</b>颜色越深（蓝）代表海冰覆盖面积越大。9月（秋季）颜色最浅，是年度最低点，也是航道通航的黄金窗口期。</p>
    """, unsafe_allow_html=False)

    st.markdown("#### 🕐 关键年份对比")
    key_years = st.multiselect("选择年份对比", sorted(df.index.tolist()), default=[1980, 2000, 2012, 2024])
    if key_years:
        import plotly.graph_objects as go
        fig_compare = go.Figure()
        colors_yr = ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#a855f7']
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        for i, yr in enumerate(sorted(key_years)):
            if yr in df.index:
                fig_compare.add_trace(go.Scatter(
                    x=month_labels, y=df.loc[yr].values,
                    mode='lines+markers', name=str(yr),
                    line=dict(color=colors_yr[i % len(colors_yr)], width=2.5),
                    marker=dict(size=6)
                ))
        fig_compare.update_layout(
            xaxis_title='月份', yaxis_title='海冰面积 (M km²)',
            template='plotly_dark', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=380, margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.8)')
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🌍 四季海冰变化趋势对比</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    fig3 = go.Figure()
    season_colors = {
        '春季(3-5月)': '#22c55e', '夏季(6-8月)': '#f97316',
        '秋季(9-11月)': '#fb923c', '冬季(12-2月)': '#60a5fa'
    }
    for season in seasons.columns:
        fig3.add_trace(go.Scatter(
            x=seasons.index, y=seasons[season],
            mode='lines+markers', name=season,
            line=dict(color=season_colors[season], width=2),
            marker=dict(size=4),
            hovertemplate=f'{season}: %{{y:.2f}} M km²<extra></extra>'
        ))
    fig3.update_layout(
        xaxis_title='年份', yaxis_title='海冰面积 (M km²)',
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)')
    )
    st.plotly_chart(fig3, use_container_width=True)

    season_changes = {}
    for season in seasons.columns:
        first_s = seasons[season].iloc[0]
        last_s = seasons[season].iloc[-1]
        season_changes[season] = ((last_s - first_s) / first_s) * 100

    change_cols = st.columns(4)
    sorted_seasons = sorted(season_changes.items(), key=lambda x: x[1])
    for i, (season, pct) in enumerate(sorted_seasons):
        color = '#f87171' if pct < -15 else '#fb923c' if pct < -10 else '#4ade80'
        with change_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:var(--card);border-radius:12px;border-top:3px solid {color};">
                <div style="font-size:1.3rem;font-weight:800;color:{color};">{pct:.1f}%</div>
                <div style="font-size:0.72rem;color:var(--text3);">{season.split('(')[0]}</div>
            </div>
            """, unsafe_allow_html=True)

    if not climate_df.empty:
        st.markdown("#### 🌡️ 北极气温与冻土变化趋势")
        climate_cols = st.columns(2)
        with climate_cols[0]:
            fig_temp = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['arctic_temp_anomaly'],
                mode='lines+markers', name='气温距平',
                line=dict(color='#ef4444', width=2),
                marker=dict(size=4), fill='tozeroy', fillcolor='rgba(239,57,53,0.12)'
            ))
            fig_temp.update_layout(
                xaxis_title='年份', yaxis_title='气温距平 (°C)',
                template='plotly_dark', height=300,
                margin=dict(l=60, r=20, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)')
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        with climate_cols[1]:
            fig_perm = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['permafrost_thickness'],
                mode='lines+markers', name='冻土厚度',
                line=dict(color='#3b82f6', width=2),
                marker=dict(size=4), fill='tozeroy', fillcolor='rgba(59,130,246,0.12)'
            ))
            fig_perm.update_layout(
                xaxis_title='年份', yaxis_title='活动层厚度 (cm)',
                template='plotly_dark', height=300,
                margin=dict(l=60, r=20, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)')
            )
            st.plotly_chart(fig_perm, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🛳️ 航道通航潜力评估</h3>', unsafe_allow_html=True)

    sep_data = df['sep'].values
    years = df.index.tolist()
    shipping_potential = [(15 - min(s, 15)) / 10 * 100 for s in sep_data]

    import plotly.graph_objects as go
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=years, y=sep_data, mode='lines+markers',
        name='9月海冰面积 (M km²)',
        yaxis='y1', line=dict(color='#60a5fa', width=2.5),
        hovertemplate='%{x}年9月: %{y:.2f} M km²<extra></extra>'
    ))
    fig4.add_trace(go.Scatter(
        x=years, y=shipping_potential, mode='lines+markers',
        name='通航潜力指数 (0-100)',
        yaxis='y2', line=dict(color='#f97316', width=2),
        marker=dict(symbol='diamond'), fill='tozeroy',
        fillcolor='rgba(249,115,22,0.08)',
        hovertemplate='%{x}年通航潜力: %{y:.0f}<extra></extra>'
    ))
    fig4.update_layout(
        xaxis=dict(title='年份'),
        yaxis=dict(title='9月海冰面积 (M km²)', side='left'),
        yaxis2=dict(title='通航潜力指数', side='right', overlaying='y', showgrid=False),
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=60, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)')
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### 🚢 三大北极航道概览")
    routes = load_route_data()
    route_cols = st.columns(3)
    colors_route = ['#60a5fa', '#f87171', '#4ade80']
    for i, (route_name, info) in enumerate(routes.items()):
        color = colors_route[i]
        with route_cols[i]:
            st.markdown(f"""
            <div style="background:var(--card);border-radius:14px;padding:1.1rem;border-top:4px solid {color};">
                <h4 style="color:{color};margin:0 0 0.5rem 0;font-size:0.95rem;">🚢 {route_name}</h4>
                <table style="width:100%;font-size:0.76rem;color:var(--text2);">
                    <tr><td><b>起点</b></td><td>{info['start']}</td></tr>
                    <tr><td><b>终点</b></td><td>{info['end']}</td></tr>
                    <tr><td><b>航程</b></td><td>{info['distance']}</td></tr>
                    <tr><td><b>航行时间</b></td><td>{info['duration']}</td></tr>
                    <tr><td><b>主导方</b></td><td>{info['operator']}</td></tr>
                    <tr><td><b>通航期</b></td><td>{info['open_months']}</td></tr>
                </table>
                <p style="font-size:0.7rem;color:var(--text3);margin-top:0.5rem;">{info['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 📋 航道通航窗口年度估算（近15年）")
    shipping_df = pd.DataFrame({
        '年份': years,
        '9月海冰面积 (M km²)': [round(s, 2) for s in sep_data],
        '通航潜力指数': [round(s, 1) for s in shipping_potential],
        '通航等级': ['极好' if s > 70 else '良好' if s > 50 else '一般' if s > 30 else '受限'
                    for s in shipping_potential]
    })
    st.dataframe(shipping_df.tail(15), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 统计分析工具</h3>', unsafe_allow_html=True)

    analysis_type = st.selectbox("分析维度", ["按月份", "按年代", "按季节"])
    import plotly.graph_objects as go

    if analysis_type == "按月份":
        month_means = df.mean()
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        fig5 = go.Figure(go.Bar(
            x=month_labels,
            y=month_means.values,
            marker_color=['#60a5fa' if i in [0,1,11] else '#4ade80' if i in [2,3,4] else '#f97316' if i in [5,6,7] else '#fb923c' for i in range(12)],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='月份', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_dark',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(255,255,255,0.8)'))
        st.plotly_chart(fig5, use_container_width=True)
    elif analysis_type == "按年代":
        long_df_copy = long_df.copy()
        long_df_copy['decade'] = (long_df_copy['year'] // 10) * 10
        decade_means = long_df_copy.groupby('decade')['ice_extent'].mean().reset_index()
        fig5 = go.Figure(go.Bar(
            x=[f"{int(d)}s" for d in decade_means['decade']],
            y=decade_means['ice_extent'],
            marker_color='#60a5fa',
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='年代', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_dark',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(255,255,255,0.8)'))
        st.plotly_chart(fig5, use_container_width=True)
    else:
        seas_means = seasons.mean()
        fig5 = go.Figure(go.Bar(
            x=seas_means.index, y=seas_means.values,
            marker_color=['#4ade80','#f97316','#fb923c','#60a5fa'],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='季节', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_dark',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(255,255,255,0.8)'))
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown("#### 描述性统计")
    stats = pd.DataFrame({
        '指标': ['均值', '标准差', '最小值', '最大值', '中位数'],
        '海冰面积 (M km²)': [
            round(df_summary['mean'].mean(), 2),
            round(df_summary['mean'].std(), 2),
            round(df_summary['minimum'].min(), 2),
            round(df_summary['maximum'].max(), 2),
            round(df_summary['mean'].median(), 2)
        ]
    })
    st.dataframe(stats, use_container_width=True, hide_index=True)

    st.markdown("#### 📐 线性趋势拟合详情")
    trend_cols = st.columns(2)
    with trend_cols[0]:
        fig_fit = go.Figure()
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=df_summary['mean'],
            mode='markers', name='实际值',
            marker=dict(size=5, color='#60a5fa')
        ))
        fitted = trend['intercept'] + trend['slope'] * df_summary.index.astype(float)
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=fitted,
            mode='lines', name='拟合线',
            line=dict(color='#ef4444', width=2.5, dash='dash')
        ))
        fig_fit.update_layout(
            xaxis_title='年份', yaxis_title='年均海冰面积 (M km²)',
            template='plotly_dark', height=320,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.8)')
        )
        st.plotly_chart(fig_fit, use_container_width=True)
    with trend_cols[1]:
        st.markdown(f"""
        **趋势拟合方程：**
        ```
        Y = {trend['slope']:.4f} × 年份 + {trend['intercept']:.2f}
        ```
        - **斜率：** {trend['slope']:.4f} M km²/年
        - **每十年下降：** {trend['decline_per_decade']:.2f} M km²
        - **R²（决定系数）：** {trend['r_squared']:.4f}
        - **趋势判定：** {'显著下降' if abs(trend['slope']) > 0.03 else '缓慢变化'}
        """)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("数据来源: NSIDC Sea Ice Index (G02135) · CMIP6模型预测数据")
