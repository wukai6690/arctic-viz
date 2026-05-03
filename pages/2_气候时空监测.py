"""
模块1：北极气候环境时空监测
支持1980-2025历史数据 + CMIP6未来预测
增强版：时间滑块、情景切换、航道评估看板、MK突变检验
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_ice_data, load_cmip6_forecast, compute_trend, get_seasonal_stats, mk_test, load_climate_data, load_route_data
from src.viz import ARCTIC_THEME, COUNTRY_COLORS, create_forecast_chart, create_seasonal_heatmap

st.set_page_config(page_title="气候时空监测", page_icon="🌡️", layout="wide")

# ============ 样式 ============
st.markdown("""
<style>
    .page-header { background: linear-gradient(135deg, #0277BD 0%, #0288D1 100%);
        padding: 1.2rem 1.5rem; border-radius: 0 0 14px 14px; margin-bottom: 1.5rem; }
    .page-header h1 { color: white !important; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .page-header p { color: rgba(255,255,255,0.85) !important; font-size: 0.85rem; margin: 0.3rem 0 0 0; }
    .info-card { background: #E3F2FD; border-radius: 12px; padding: 1rem; border-left: 4px solid #0288D1; }
    .warning-card { background: #FFEBEE; border-radius: 12px; padding: 1rem; border-left: 4px solid #E53935; }
    /* 确保主内容区白色背景，文字深色 */
    section[data-testid="stMain"] > div { background: white !important; }
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li, section[data-testid="stMain"] span {
        color: #1a1a2e !important;
    }
    .stMarkdown p, .stMarkdown li { color: #1a1a2e !important; }
    .stTabs [data-baseweb="tab"] { color: #333 !important; }
</style>
<div class="page-header">
    <h1>🌡️ 北极气候环境时空监测模块</h1>
    <p>气温 · 海冰密集度 · CMIP6情景预测 · 航道通航潜力评估 · M-K突变检验</p>
</div>
""", unsafe_allow_html=True)

# ============ 数据加载 ============
df, df_summary, long_df = load_ice_data()
cmip6_df = load_cmip6_forecast()
trend = compute_trend(df_summary)
seasons = get_seasonal_stats(long_df)
climate_df = load_climate_data()

# ============ KPI 指标 ============
kpi_cols = st.columns(4)
with kpi_cols[0]:
    latest = df_summary['mean'].iloc[-1]
    prev = df_summary['mean'].iloc[-2]
    st.metric("2024年均海冰面积", f"{latest:.2f} M km²", delta=f"{latest-prev:.2f} vs 2023")
with kpi_cols[1]:
    first = df_summary['mean'].iloc[0]
    total = latest - first
    pct = total / first * 100
    st.metric("1979-2024累计变化", f"{total:.2f} M km²", delta=f"{pct:.1f}%")
with kpi_cols[2]:
    st.metric("每十年下降速率", f"{trend['decline_per_decade']:.2f} M km²/十年",
              delta=f"R²={trend['r_squared']:.3f}")
with kpi_cols[3]:
    min_val = df_summary['minimum'].min()
    min_yr = df_summary['minimum'].idxmin()
    st.metric(f"{min_yr}年历史最低", f"{min_val:.2f} M km²", delta="夏季最小值")

st.divider()

# ============ 主图表区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 趋势与预测", "🗓️ 月度热力图", "🌍 季节对比", "🛳️ 航道通航评估", "📊 统计分析"
])

with tab1:
    st.markdown("### 📈 海冰面积变化趋势与CMIP6情景预测")
    st.caption("蓝线：历史数据 | 绿线：SSP1-2.6低碳情景 | 红线：SSP5-8.5高排放情景")

    # 预测说明
    st.info("""
    **CMIP6情景说明**：SSP1-2.6（低碳路径）假设全球积极减排，2100年海冰面积约3-5M km²；
    SSP5-8.5（高排放路径）假设化石燃料持续依赖，2100年夏季北极近乎无冰（<1M km²）。
    """)

    fig = create_forecast_chart(df_summary, cmip6_df)
    st.plotly_chart(fig, use_container_width=True)

    col_pred1, col_pred2 = st.columns(2)
    with col_pred1:
        ssp126_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP1-2.6'].values[0]
        ssp126_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP1-2.6'].values[0]
        st.markdown(f"""
        <div class="info-card">
        <b>🌱 SSP1-2.6 低碳情景</b><br>
        2050年预测: <b>{ssp126_2050:.2f} M km²</b>（较2024年下降约{(9.5-ssp126_2050):.1f} M km²）<br>
        2100年预测: <b>{ssp126_2100:.2f} M km²</b>（接近历史最低水平）
        </div>
        """, unsafe_allow_html=True)
    with col_pred2:
        ssp585_2050 = cmip6_df[cmip6_df['year'] == 2050]['SSP5-8.5'].values[0]
        ssp585_2100 = cmip6_df[cmip6_df['year'] == 2100]['SSP5-8.5'].values[0]
        st.markdown(f"""
        <div class="warning-card">
        <b>🔥 SSP5-8.5 高排放情景</b><br>
        2050年预测: <b>{ssp585_2050:.2f} M km²</b>（较2024年下降约{(9.5-ssp585_2050):.1f} M km²）<br>
        2100年预测: <b>{ssp585_2100:.2f} M km²</b>（近乎无冰状态）
        </div>
        """, unsafe_allow_html=True)

    # M-K突变检验
    mk_result = mk_test(df_summary['mean'].values)
    mk_cols = st.columns(3)
    with mk_cols[0]:
        st.markdown(f"**M-K 检验 Z值**: `{mk_result['z_value']}`")
    with mk_cols[1]:
        st.markdown(f"**P值**: `{mk_result['p_value']}`")
    with mk_cols[2]:
        color = "#43A047" if mk_result['trend'] == '显著下降' else "#E53935"
        st.markdown(f"**趋势判定**: <span style='color:{color};font-weight:bold'>{mk_result['trend']}</span>",
                   unsafe_allow_html=True)

    st.markdown("""
    **趋势解读：** 1979-2024年间，北极年均海冰面积呈显著下降趋势（每十年约减少 0.65 M km²），
    M-K检验和线性拟合R²=0.89共同确认趋势可信度高。两种CMIP6情景均显示21世纪海冰将持续减少，
    高排放情景下2100年夏季北极近乎无冰，为「冰上丝绸之路」提供了物理基础。
    """)

with tab2:
    st.markdown("### 🗓️ 月度海冰面积热力图（1980-2024）")

    year_range = st.slider("选择年份范围", 1980, 2024, (1990, 2024))
    color_scheme = st.selectbox("配色方案", ["Ice", "YlOrRd", "Viridis"], format_func=lambda x: {"Ice": "冰蓝色", "YlOrRd": "红黄渐变", "Viridis": "科学紫绿"}.get(x, x))

    fig2 = create_seasonal_heatmap(long_df, year_range=year_range, color_scheme=color_scheme)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **解读指南：** 颜色越深（蓝）代表海冰覆盖面积越大。9月（秋季）颜色最浅，
    是年度最低点，也是航道通航的黄金窗口期。颜色趋势从深到浅逐渐演变，
    直观反映海冰消退速度。近年来夏季（7-9月）颜色明显变浅，消退期提前、延长。
    """)

    # 时间轴播放（用关键年份对比替代）
    st.markdown("#### 🕐 关键年份对比")
    key_years = st.multiselect("选择年份对比", sorted(df.index.tolist()),
                               default=[1980, 2000, 2012, 2024])
    if key_years:
        import plotly.graph_objects as go
        fig_compare = go.Figure()
        colors_yr = ['#1E88E5', '#E53935', '#43A047', '#FF6B35', '#9C27B0']
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        for i, yr in enumerate(sorted(key_years)):
            if yr in df.index:
                fig_compare.add_trace(go.Scatter(
                    x=month_labels, y=df.loc[yr].values,
                    mode='lines+markers', name=str(yr),
                    line=dict(color=colors_yr[i % len(colors_yr)], width=2),
                    marker=dict(size=5)
                ))
        fig_compare.update_layout(
            xaxis_title='月份', yaxis_title='海冰面积 (M km²)',
            template='plotly_white', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=350, margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

with tab3:
    st.markdown("### 🌍 四季海冰变化趋势对比")

    import plotly.graph_objects as go
    fig3 = go.Figure()
    season_colors = {
        '春季(3-5月)': '#66BB6A', '夏季(6-8月)': '#FF7043',
        '秋季(9-11月)': '#FFA726', '冬季(12-2月)': '#42A5F5'
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
        height=420, margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig3, use_container_width=True)

    # 各季节变化率
    season_changes = {}
    for season in seasons.columns:
        first = seasons[season].iloc[0]
        last = seasons[season].iloc[-1]
        season_changes[season] = ((last - first) / first) * 100

    st.markdown("#### 各季节变化率 (1979→2024)")
    change_cols = st.columns(4)
    sorted_seasons = sorted(season_changes.items(), key=lambda x: x[1])
    for i, (season, pct) in enumerate(sorted_seasons):
        color = '#E53935' if pct < -15 else '#FF6B35' if pct < -10 else '#43A047'
        with change_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <div style="font-size:1.3rem;font-weight:800;color:{color};">{pct:.1f}%</div>
                <div style="font-size:0.75rem;color:#90A4AE;">{season.split('(')[0]}</div>
            </div>
            """, unsafe_allow_html=True)

    # 气候辅助数据
    st.markdown("#### 🌡️ 北极气温与冻土变化趋势")
    if not climate_df.empty:
        climate_cols = st.columns(2)
        with climate_cols[0]:
            fig_temp = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['arctic_temp_anomaly'],
                mode='lines+markers', name='气温距平',
                line=dict(color='#E53935', width=2),
                marker=dict(size=4),
                fill='tozeroy', fillcolor='rgba(229,57,53,0.1)'
            ))
            fig_temp.update_layout(
                xaxis_title='年份', yaxis_title='气温距平 (°C)',
                template='plotly_white', height=300,
                margin=dict(l=60, r=20, t=20, b=40)
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        with climate_cols[1]:
            fig_perm = go.Figure(go.Scatter(
                x=climate_df['year'], y=climate_df['permafrost_thickness'],
                mode='lines+markers', name='冻土厚度',
                line=dict(color='#1565C0', width=2),
                marker=dict(size=4),
                fill='tozeroy', fillcolor='rgba(21,101,192,0.1)'
            ))
            fig_perm.update_layout(
                xaxis_title='年份', yaxis_title='活动层厚度 (cm)',
                template='plotly_white', height=300,
                margin=dict(l=60, r=20, t=20, b=40)
            )
            st.plotly_chart(fig_perm, use_container_width=True)

with tab4:
    st.markdown("### 🛳️ 航道通航潜力评估")

    sep_data = df['sep'].values
    years = df.index.tolist()
    shipping_potential = [(15 - min(s, 15)) / 10 * 100 for s in sep_data]

    import plotly.graph_objects as go
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=years, y=sep_data, mode='lines+markers',
        name='9月海冰面积 (M km²)',
        yaxis='y1', line=dict(color='#1E88E5', width=2.5),
        hovertemplate='%{x}年9月: %{y:.2f} M km²<extra></extra>'
    ))
    fig4.add_trace(go.Scatter(
        x=years, y=shipping_potential, mode='lines+markers',
        name='通航潜力指数 (0-100)',
        yaxis='y2', line=dict(color='#FF6B35', width=2),
        marker=dict(symbol='diamond'), fill='tozeroy',
        fillcolor='rgba(255,107,53,0.08)',
        hovertemplate='%{x}年通航潜力: %{y:.0f}<extra></extra>'
    ))
    fig4.update_layout(
        xaxis=dict(title='年份'),
        yaxis=dict(title='9月海冰面积 (M km²)', side='left'),
        yaxis2=dict(title='通航潜力指数', side='right', overlaying='y', showgrid=False),
        template='plotly_white', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420, margin=dict(l=60, r=60, t=20, b=40)
    )
    st.plotly_chart(fig4, use_container_width=True)

    # 三大航道信息
    st.markdown("#### 🚢 三大北极航道概览")
    routes = load_route_data()
    route_cols = st.columns(3)
    for i, (route_name, info) in enumerate(routes.items()):
        with route_cols[i]:
            color = ['#E53935', '#1565C0', '#43A047'][i]
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:1rem;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:4px solid {color};">
                <h4 style="color:{color};margin:0 0 0.5rem 0">{route_name}</h4>
                <table style="width:100%;font-size:0.8rem;color:#546E7A;">
                    <tr><td><b>起点</b></td><td>{info['start']}</td></tr>
                    <tr><td><b>终点</b></td><td>{info['end']}</td></tr>
                    <tr><td><b>航程</b></td><td>{info['distance']}</td></tr>
                    <tr><td><b>航行时间</b></td><td>{info['duration']}</td></tr>
                    <tr><td><b>主导方</b></td><td>{info['operator']}</td></tr>
                    <tr><td><b>通航期</b></td><td>{info['open_months']}</td></tr>
                </table>
                <p style="font-size:0.75rem;color:#90A4AE;margin-top:0.5rem">{info['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    # 通航窗口估算表
    st.markdown("#### 📋 航道通航窗口年度估算（近15年）")
    shipping_df = pd.DataFrame({
        '年份': years,
        '9月海冰面积 (M km²)': [round(s, 2) for s in sep_data],
        '通航潜力指数': [round(s, 1) for s in shipping_potential],
        '通航等级': ['极好' if s > 70 else '良好' if s > 50 else '一般' if s > 30 else '受限'
                    for s in shipping_potential]
    })
    st.dataframe(shipping_df.tail(15), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### 📊 统计分析工具")

    analysis_type = st.selectbox("分析维度", ["按月份", "按年代", "按季节"])
    import plotly.graph_objects as go

    if analysis_type == "按月份":
        month_means = df.mean()
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        fig5 = go.Figure(go.Bar(
            x=month_labels,
            y=month_means.values,
            marker_color=['#42A5F5' if i in [0,1,11] else '#66BB6A' if i in [2,3,4] else '#FF7043' if i in [5,6,7] else '#FFA726' for i in range(12)],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='月份', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40))
        st.plotly_chart(fig5, use_container_width=True)

    elif analysis_type == "按年代":
        long_df['decade'] = (long_df['year'] // 10) * 10
        decade_means = long_df.groupby('decade')['ice_extent'].mean().reset_index()
        fig5 = go.Figure(go.Bar(
            x=[f"{int(d)}s" for d in decade_means['decade']],
            y=decade_means['ice_extent'],
            marker_color='#1E88E5',
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='年代', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40))
        st.plotly_chart(fig5, use_container_width=True)

    else:
        seas_means = seasons.mean()
        fig5 = go.Figure(go.Bar(
            x=seas_means.index, y=seas_means.values,
            marker_color=['#66BB6A','#FF7043','#FFA726','#42A5F5'],
            hovertemplate='%{x}: %{y:.2f} M km²<extra></extra>'
        ))
        fig5.update_layout(xaxis_title='季节', yaxis_title='平均海冰面积 (M km²)',
                          height=350, margin=dict(l=60, r=20, t=20, b=40))
        st.plotly_chart(fig5, use_container_width=True)

    # 描述性统计
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

    # 线性趋势详细信息
    st.markdown("#### 📐 线性趋势拟合详情")
    trend_cols = st.columns(2)
    with trend_cols[0]:
        import plotly.graph_objects as go
        fig_fit = go.Figure()
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=df_summary['mean'],
            mode='markers', name='实际值',
            marker=dict(size=5, color='#1E88E5')
        ))
        fitted = trend['intercept'] + trend['slope'] * df_summary.index.astype(float)
        fig_fit.add_trace(go.Scatter(
            x=df_summary.index, y=fitted,
            mode='lines', name=f'拟合线 (斜率={trend["slope"]:.4f})',
            line=dict(color='#E53935', width=2, dash='dash')
        ))
        fig_fit.update_layout(
            xaxis_title='年份', yaxis_title='年均海冰面积 (M km²)',
            template='plotly_white', height=300,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_fit, use_container_width=True)
    with trend_cols[1]:
        st.markdown(f"""
        **趋势拟合方程**：
        ```
        Y = {trend['slope']:.4f} × 年份 + {trend['intercept']:.2f}
        ```
        - **斜率**：{trend['slope']:.4f} M km²/年
        - **每十年下降**：{trend['decline_per_decade']:.2f} M km²
        - **R²（决定系数）**：{trend['r_squared']:.4f}
        - **趋势判定**：{'显著下降' if abs(trend['slope']) > 0.03 else '缓慢变化'}
        """)

st.divider()
st.caption("数据来源: NSIDC Sea Ice Index (G02135) · CMIP6模型预测数据")
