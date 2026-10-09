"""
模块1：北极气候环境时空监测
浅色研究主题 · 原版功能保留
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_ice_data, load_cmip6_forecast, compute_trend, get_seasonal_stats, mk_test, load_climate_data, load_route_data
from src.viz import create_forecast_chart, create_seasonal_heatmap

st.set_page_config(page_title="气候时空监测", page_icon="◎", layout="wide")

from src.presentation import apply_presentation, show_chart
apply_presentation('climate')


# 深色主题 CSS
st.markdown("""

<div class="page-header">
    <h1> 北极气候环境时空监测</h1>
    <p>真实海冰观测 · 原版情景演示 · 季节对比 · 航道指标 · 趋势检验</p>
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
        <div class="kpi-label"> 2024年均海冰面积</div>
        <div class="kpi-val" style="color:#4b7883">{latest:.2f} M km²</div>
        <div class="kpi-sub">较2023年 {latest-prev:+.2f} M km²</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 1979-2024累计变化</div>
        <div class="kpi-val" style="color:#b37564">{total_change:+.2f} M km²</div>
        <div class="kpi-sub">累计变化 {pct:+.1f}%</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 每十年下降速率</div>
        <div class="kpi-val" style="color:#b19059">{trend['decline_per_decade']:.2f} M km²</div>
        <div class="kpi-sub">R²={trend['r_squared']:.3f}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> {min_yr}年历史最低</div>
        <div class="kpi-val" style="color:#ac665a">{min_val:.2f} M km²</div>
        <div class="kpi-sub">夏季最小值</div>
    </div>
</div>
"""



# ============ 主图表区域 ============
from src.evidence_views import render_observations

observed_tab, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "真实海冰观测",
    " 趋势与预测", " 月度热力图", " 季节对比", " 航道评估", " 统计分析"
])


with observed_tab:
    render_observations()

with tab1:
    st.markdown('<span class="status-demo">原版示例数据 · 方法演示</span>',unsafe_allow_html=True)
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 原版海冰趋势与情景曲线（示例）</h3>', unsafe_allow_html=True)

    ssp126_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP1-2.6'].values[0]
    ssp126_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP1-2.6'].values[0]
    ssp585_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP5-8.5'].values[0]
    ssp585_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP5-8.5'].values[0]

    col_pred1, col_pred2 = st.columns(2)
    with col_pred1:
        st.markdown(f"""
        <div class="info-card">
            <b> SSP1-2.6 低碳情景</b><br>
            2050年: <b>{ssp126_2050:.2f} M km²</b><br>
            2100年: <b>{ssp126_2100:.2f} M km²</b>
        </div>
        """, unsafe_allow_html=True)
    with col_pred2:
        st.markdown(f"""
        <div class="warn-card">
            <b> SSP5-8.5 高排放情景</b><br>
            2050年: <b>{ssp585_2050:.2f} M km²</b><br>
            2100年: <b>{ssp585_2100:.2f} M km²</b>
        </div>
        """, unsafe_allow_html=True)

    fig = create_forecast_chart(df_summary, cmip6_df)
    show_chart(fig, use_container_width=True)

    # M-K 趋势检验
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
    <h4>M-K 趋势检验结果解读</h4>
    <p>以下结果来自原版示例序列，仅演示趋势检验和绘图流程。情景曲线由程序生成，并非从 CMIP6 下载的模型结果，不能据此推断未来海冰或航道开放时间。</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 月度海冰面积热力图（1980-2024）</h3>', unsafe_allow_html=True)

    year_range = st.slider("年份范围", 1980, 2024, (1990, 2024))
    color_scheme = st.selectbox("配色方案", ["Ice", "YlOrRd", "Viridis"],
                                format_func=lambda x: {"Ice": "冰蓝色", "YlOrRd": "红黄渐变", "Viridis": "科学紫绿"}.get(x, x))

    fig2 = create_seasonal_heatmap(long_df, year_range=year_range, color_scheme=color_scheme)
    show_chart(fig2, use_container_width=True)

    st.markdown("""
    <p><b>解读指南：</b>颜色越深（蓝）代表海冰覆盖面积越大。该热力图使用原版示例；实际航行条件需结合区域冰情、天气和船舶能力判断。</p>
    """, unsafe_allow_html=False)

    st.markdown("####  关键年份对比")
    key_years = st.multiselect("选择年份对比", sorted(df.index.tolist()), default=[1980, 2000, 2012, 2024])
    if key_years:
        import plotly.graph_objects as go
        fig_compare = go.Figure()
        colors_yr = ['#4b7883', '#ac665a', '#5d8770', '#b19059', '#867697']
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
            template='plotly_white', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=380, margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(54,80,65,0.8)')
        )
        show_chart(fig_compare, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 四季海冰变化趋势对比</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    fig3 = go.Figure()
    season_colors = {
        '春季(3-5月)': '#5d8770', '夏季(6-8月)': '#b19059',
        '秋季(9-11月)': '#b19059', '冬季(12-2月)': '#4b7883'
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
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)')
    )
    show_chart(fig3, use_container_width=True)

    season_changes = {}
    for season in seasons.columns:
        first_s = seasons[season].iloc[0]
        last_s = seasons[season].iloc[-1]
        season_changes[season] = ((last_s - first_s) / first_s) * 100

    change_cols = st.columns(4)
    sorted_seasons = sorted(season_changes.items(), key=lambda x: x[1])
    for i, (season, pct) in enumerate(sorted_seasons):
        color = '#b37564' if pct < -15 else '#b19059' if pct < -10 else '#5d8770'
        with change_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:var(--card);border-radius:12px;border-top:3px solid {color};">
                <div style="font-size:1.3rem;font-weight:800;color:{color};">{pct:.1f}%</div>
                <div style="font-size:0.72rem;color:var(--text3);">{season.split('(')[0]}</div>
            </div>
            """, unsafe_allow_html=True)

    if not climate_df.empty:
        st.markdown("####  北极气温与冻土变化趋势")
        climate_cols = st.columns(2)
        with climate_cols[0]:
            fig_temp = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['arctic_temp_anomaly'],
                mode='lines+markers', name='气温距平',
                line=dict(color='#ac665a', width=2),
                marker=dict(size=4), fill='tozeroy', fillcolor='rgba(239,57,53,0.12)'
            ))
            fig_temp.update_layout(
                xaxis_title='年份', yaxis_title='气温距平 (°C)',
                template='plotly_white', height=300,
                margin=dict(l=60, r=20, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(54,80,65,0.8)')
            )
            show_chart(fig_temp, use_container_width=True)
        with climate_cols[1]:
            fig_perm = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['permafrost_thickness'],
                mode='lines+markers', name='冻土厚度',
                line=dict(color='#4b7883', width=2),
                marker=dict(size=4), fill='tozeroy', fillcolor='rgba(59,130,246,0.12)'
            ))
            fig_perm.update_layout(
                xaxis_title='年份', yaxis_title='活动层厚度 (cm)',
                template='plotly_white', height=300,
                margin=dict(l=60, r=20, t=20, b=40),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(54,80,65,0.8)')
            )
            show_chart(fig_perm, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 航道通航潜力评估</h3>', unsafe_allow_html=True)

    sep_data = df['sep'].values
    years = df.index.tolist()
    shipping_potential = [max(0, min(100, (15 - min(s, 15)) / 10 * 100)) for s in sep_data]
    st.caption('此指数沿用原版经验公式并限制在 0–100，仅作交互演示，尚未经过通航资料验证。')

    import plotly.graph_objects as go
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=years, y=sep_data, mode='lines+markers',
        name='9月海冰面积 (M km²)',
        yaxis='y1', line=dict(color='#4b7883', width=2.5),
        hovertemplate='%{x}年9月: %{y:.2f} M km²<extra></extra>'
    ))
    fig4.add_trace(go.Scatter(
        x=years, y=shipping_potential, mode='lines+markers',
        name='通航潜力指数 (0-100)',
        yaxis='y2', line=dict(color='#b19059', width=2),
        marker=dict(symbol='diamond'), fill='tozeroy',
        fillcolor='rgba(249,115,22,0.08)',
        hovertemplate='%{x}年通航潜力: %{y:.0f}<extra></extra>'
    ))
    fig4.update_layout(
        xaxis=dict(title='年份'),
        yaxis=dict(title='9月海冰面积 (M km²)', side='left'),
        yaxis2=dict(title='通航潜力指数', side='right', overlaying='y', showgrid=False),
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=60, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)')
    )
    show_chart(fig4, use_container_width=True)

    st.markdown("####  三大北极航道概览")
    routes = load_route_data()
    route_cols = st.columns(3)
    colors_route = ['#4b7883', '#b37564', '#5d8770']
    for i, (route_name, info) in enumerate(routes.items()):
        color = colors_route[i]
        with route_cols[i]:
            st.markdown(f"""
            <div style="background:var(--card);border-radius:14px;padding:1.1rem;border-top:4px solid {color};">
                <h4 style="color:{color};margin:0 0 0.5rem 0;font-size:0.95rem;"> {route_name}</h4>
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

    st.markdown("####  原版通航指数示例（近15年）")
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
    st.markdown('<h3> 统计分析工具</h3>', unsafe_allow_html=True)

    analysis_type = st.selectbox("分析维度", ["按月份", "按年代", "按季节"])
    import plotly.graph_objects as go

    if analysis_type == "按月份":
        month_means = df.mean()
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        fig5 = go.Figure(go.Bar(
            x=month_labels,
            y=month_means.values,
            marker_color=['#4b7883' if i in [0,1,11] else '#5d8770' if i in [2,3,4] else '#b19059' if i in [5,6,7] else '#b19059' for i in range(12)],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='月份', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_white',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(54,80,65,0.8)'))
        show_chart(fig5, use_container_width=True)
    elif analysis_type == "按年代":
        long_df_copy = long_df.copy()
        long_df_copy['decade'] = (long_df_copy['year'] // 10) * 10
        decade_means = long_df_copy.groupby('decade')['ice_extent'].mean().reset_index()
        fig5 = go.Figure(go.Bar(
            x=[f"{int(d)}s" for d in decade_means['decade']],
            y=decade_means['ice_extent'],
            marker_color='#4b7883',
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='年代', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_white',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(54,80,65,0.8)'))
        show_chart(fig5, use_container_width=True)
    else:
        seas_means = seasons.mean()
        fig5 = go.Figure(go.Bar(
            x=seas_means.index, y=seas_means.values,
            marker_color=['#5d8770','#b19059','#b19059','#4b7883'],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='季节', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40),
                          template='plotly_white',
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          font=dict(color='rgba(54,80,65,0.8)'))
        show_chart(fig5, use_container_width=True)

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

    st.markdown("####  线性趋势拟合详情")
    trend_cols = st.columns(2)
    with trend_cols[0]:
        fig_fit = go.Figure()
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=df_summary['mean'],
            mode='markers', name='实际值',
            marker=dict(size=5, color='#4b7883')
        ))
        fitted = trend['intercept'] + trend['slope'] * df_summary.index.astype(float)
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=fitted,
            mode='lines', name='拟合线',
            line=dict(color='#ac665a', width=2.5, dash='dash')
        ))
        fig_fit.update_layout(
            xaxis_title='年份', yaxis_title='年均海冰面积 (M km²)',
            template='plotly_white', height=320,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=60, r=20, t=20, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(54,80,65,0.8)')
        )
        show_chart(fig_fit, use_container_width=True)
    with trend_cols[1]:
        st.markdown(f"""
        **趋势拟合方程：**
        ```
        Y = {trend['slope']:.4f} × 年份 + {trend['intercept']:.2f}
        ```
        - **斜率：** {trend['slope']:.4f} M km²/年
        - **每十年下降：** {trend['decline_per_decade']:.2f} M km²
        - **R²（决定系数）：** {trend['r_squared']:.4f}
        - **趋势判定：** {'样例序列下降' if trend['slope'] < 0 else '样例序列上升'}
        """)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("真实观测：NSIDC Sea Ice Index V4；原版分析页签：示例数据与程序生成的情景曲线。")
