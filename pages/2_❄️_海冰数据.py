"""
海冰数据面板页面
展示北极海冰面积历年变化趋势、季节性分析、趋势预测与航道通航关联
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.ice_data import (
    load_ice_data, compute_trend, get_seasonal_stats,
    MONTH_NAMES_CN, MONTH_ABBR
)

st.set_page_config(page_title="海冰数据", page_icon="❄️", layout="wide")

st.markdown("## ❄️ 北极海冰数据面板")
st.markdown("数据来源: **NSIDC** (美国国家冰雪数据中心) · 1979-2024 逐月海冰范围数据")
st.divider()

# 加载数据
df_monthly, df_summary, long_df = load_ice_data()
trend = compute_trend(df_summary)
seasons = get_seasonal_stats(long_df)

# 顶部指标
kpi_cols = st.columns(4)
latest_year = int(df_summary.index[-1])
prev_year = int(df_summary.index[-2])
latest_mean = df_summary['mean'].iloc[-1]
prev_mean = df_summary['mean'].iloc[-2]
change = latest_mean - prev_mean

with kpi_cols[0]:
    st.metric(
        f"{latest_year}年均海冰面积",
        f"{latest_mean:.2f} M km²",
        delta=f"{change:+.2f} vs {prev_year}"
    )

with kpi_cols[1]:
    first_mean = df_summary['mean'].iloc[0]
    total_change = latest_mean - first_mean
    pct = (total_change / first_mean) * 100
    st.metric(
        "1979-2024累计变化",
        f"{total_change:.2f} M km²",
        delta=f"{pct:.1f}%"
    )

with kpi_cols[2]:
    st.metric(
        "每十年下降速率",
        f"{trend['decline_per_decade']:.2f} M km²/十年",
        delta=f"趋势显著 (R²={trend['r_squared']:.3f})"
    )

with kpi_cols[3]:
    min_record = df_summary['minimum'].min()
    min_year = int(df_summary['minimum'].idxmin())
    st.metric(
        f"{min_year}年历史最低",
        f"{min_record:.2f} M km²",
        delta="⚠️ 夏季最小值"
    )

st.divider()

# 图表标签页
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 年度趋势", "🗓️ 月度变化", "🌍 季节对比", "🔗 航道关联", "🔮 趋势预测"
])

with tab1:
    st.markdown("### 📈 历年海冰年均面积变化趋势")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_summary.index,
        y=df_summary['mean'],
        mode='lines+markers',
        name='年均面积',
        line=dict(color='#1E88E5', width=2.5),
        marker=dict(size=6, color='#1E88E5'),
        hovertemplate='<b>%{x}</b><br>海冰面积: %{y:.2f} M km²<extra></extra>'
    ))

    x = df_summary.index.values
    y_fit = trend['slope'] * x + trend['intercept']
    fig.add_trace(go.Scatter(
        x=x, y=y_fit,
        mode='lines',
        name=f'线性趋势 (斜率={trend["slope"]:.4f})',
        line=dict(color='#E53935', width=2, dash='dash'),
        hovertemplate='趋势线: %{y:.2f} M km²<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df_summary.index,
        y=df_summary['maximum'],
        mode='lines',
        name='最大值（冬季）',
        line=dict(color='#90CAF9', width=1, dash='dot'),
        hovertemplate='%{x}: 最大 %{y:.2f} M km²<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df_summary.index,
        y=df_summary['minimum'],
        mode='lines',
        name='最小值（夏季）',
        line=dict(color='#BBDEFB', width=1, dash='dot'),
        hovertemplate='%{x}: 最小 %{y:.2f} M km²<extra></extra>'
    ))

    fig.update_layout(
        xaxis_title='年份',
        yaxis_title='海冰面积 (百万平方公里)',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450,
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div style="background:#f0f4f8;padding:1rem;border-radius:8px;border-left:4px solid #1E88E5;margin-top:0.5rem">
    <b>趋势解读：</b>1979-2024年间，北极年均海冰面积呈<strong>显著下降趋势</strong>，
    每十年减少约 <strong>{trend['decline_per_decade']:.2f} 百万平方公里</strong>。
    线性拟合的 R² = {trend['r_squared']:.3f}，说明模型解释力较强。
    这一趋势直接驱动了北极航道通航窗口的延长，为「冰上丝绸之路」提供了物理基础。
    </div>
    """, unsafe_allow_html=True)


with tab2:
    st.markdown("### 🗓️ 月度海冰面积热力图")

    pivot = long_df.pivot_table(values='ice_extent', index='year', columns='month_num', aggfunc='mean')
    valid_cols = [c for c in pivot.columns if c in range(1, 13)]
    pivot = pivot[valid_cols]
    pivot.columns = [MONTH_NAMES_CN[c-1] for c in pivot.columns]

    fig2 = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='Blues',
        colorbar=dict(title='M km²'),
        hovertemplate='%{y}年 %{x}<br>海冰面积: %{z:.2f} M km²<extra></extra>'
    ))

    fig2.update_layout(
        xaxis_title='月份',
        yaxis_title='年份',
        height=550,
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **解读：** 9月（秋季）海冰面积最低，是航道通航的黄金窗口期。
    夏季（6-8月）海冰退缩程度直接决定当年航道通航能力。
    颜色越深（蓝色）代表海冰覆盖面积越大。
    """)


with tab3:
    st.markdown("### 🌍 四季海冰变化趋势对比")

    fig3 = go.Figure()
    season_colors = {
        '春季(3-5月)': '#66BB6A',
        '夏季(6-8月)': '#FF7043',
        '秋季(9-11月)': '#FFA726',
        '冬季(12-2月)': '#42A5F5'
    }

    for season in seasons.columns:
        fig3.add_trace(go.Scatter(
            x=seasons.index,
            y=seasons[season],
            mode='lines+markers',
            name=season,
            line=dict(color=season_colors[season], width=2),
            marker=dict(size=5),
            hovertemplate=f'{season}: %{{y:.2f}} M km²<extra></extra>'
        ))

    fig3.update_layout(
        xaxis_title='年份',
        yaxis_title='海冰面积 (百万平方公里)',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420,
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig3, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        season_changes = {}
        for season in seasons.columns:
            first = seasons[season].iloc[0]
            last = seasons[season].iloc[-1]
            season_changes[season] = ((last - first) / first) * 100

        st.markdown("#### 各季节变化率 (1979→2024)")
        for season, pct in sorted(season_changes.items(), key=lambda x: x[1]):
            color = '#E53935' if pct < -10 else '#FDD835' if pct < -5 else '#43A047'
            bar_width = min(abs(pct) * 5, 100)
            st.markdown(
                f"<div style='margin:4px 0'>"
                f"<span style='width:100px;display:inline-block'>{season.split('(')[0]}</span>"
                f"<span style='display:inline-block;width:{bar_width}px;background:{color};height:16px;border-radius:3px;'></span>"
                f"<span style='margin-left:8px;color:{color};font-weight:600'>{pct:.1f}%</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("#### 季节性特征")
        st.markdown("""
        - **冬季（12-2月）**：海冰面积最大，覆盖范围接近全年峰值
        - **春季（3-5月）**：快速融化期，冰-水边界向北退缩
        - **夏季（6-8月）**：融化加速，9月达年度最低点
        - **秋季（9-11月）**：冻结初期，是东北航道通航的黄金期
        """)


with tab4:
    st.markdown("### 🔗 海冰变化与航道通航能力关联分析")

    fig4 = go.Figure()

    fig4.add_trace(go.Scatter(
        x=df_summary.index,
        y=df_summary['mean'],
        mode='lines+markers',
        name='年均海冰面积 (M km²)',
        yaxis='y1',
        line=dict(color='#1E88E5', width=2.5),
        hovertemplate='%{x}年: %{y:.2f} M km²<extra></extra>'
    ))

    # 航道通航潜力指数（基于9月海冰面积）
    sep_data = df_monthly['sep'].values
    shipping_potential = [(15 - min(s, 15)) / 10 * 100 for s in sep_data]
    fig4.add_trace(go.Scatter(
        x=df_summary.index,
        y=shipping_potential,
        mode='lines+markers',
        name='航道通航潜力指数 (0-100)',
        yaxis='y2',
        line=dict(color='#FF6B35', width=2),
        marker=dict(symbol='diamond'),
        hovertemplate='%{x}年通航潜力: %{y:.0f}<extra></extra>'
    ))

    fig4.update_layout(
        xaxis=dict(title='年份'),
        yaxis=dict(title='海冰面积 (M km²)', side='left', showgrid=True),
        yaxis2=dict(title='通航潜力指数', side='right', overlaying='y', showgrid=False),
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=420,
        margin=dict(l=60, r=60, t=20, b=40)
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("""
    **关联分析：**
    航道通航潜力指数基于每年9月海冰面积计算，反映夏季融化后的通航条件。
    指数越高表示通航窗口越大、航道条件越好。

    1979-2024年间，9月平均海冰面积从约 7.1 M km² 下降至约 4.4 M km²，
    东北航道通航窗口从约 2 个月延长至 3-4 个月。
    这是「冰上丝绸之路」从概念走向现实的物理基础。
    """)

    st.markdown("#### 航道通航窗口估算")
    shipping_df = pd.DataFrame({
        '年份': df_summary.index,
        '9月海冰面积 (M km²)': [round(s, 2) for s in sep_data],
        '通航潜力指数': [round(s, 1) for s in shipping_potential],
        '通航等级': ['极好' if s > 70 else '良好' if s > 50 else '一般' if s > 30 else '受限'
                    for s in shipping_potential]
    })
    st.dataframe(shipping_df.tail(15), use_container_width=True, hide_index=True)


with tab5:
    st.markdown("### 🔮 海冰面积趋势预测（线性外推）")

    # 线性回归预测
    years_arr = df_summary.index.values.astype(float)
    mean_arr = df_summary['mean'].values

    # 计算趋势参数
    x_mean = years_arr.mean()
    y_mean = mean_arr.mean()
    slope = np.sum((years_arr - x_mean) * (mean_arr - y_mean)) / np.sum((years_arr - x_mean) ** 2)
    intercept = y_mean - slope * x_mean

    # 未来10年预测
    forecast_years = np.arange(2025, 2035)
    forecast_values = slope * forecast_years + intercept

    # 置信区间（简单估计）
    residuals = mean_arr - (slope * years_arr + intercept)
    std_resid = np.std(residuals)

    fig5 = go.Figure()

    # 历史数据
    fig5.add_trace(go.Scatter(
        x=years_arr,
        y=mean_arr,
        mode='lines+markers',
        name='历史数据 (NSIDC)',
        line=dict(color='#1E88E5', width=2),
        marker=dict(size=5),
        hovertemplate='%{x}年: %{y:.2f} M km²<extra></extra>'
    ))

    # 趋势线（延伸至2024）
    extended_x = np.arange(1979, 2025)
    extended_y = slope * extended_x + intercept
    fig5.add_trace(go.Scatter(
        x=extended_x,
        y=extended_y,
        mode='lines',
        name='线性趋势线',
        line=dict(color='#E53935', width=2, dash='dash'),
        hovertemplate='趋势: %{x}年 %{y:.2f} M km²<extra></extra>'
    ))

    # 预测
    fig5.add_trace(go.Scatter(
        x=forecast_years,
        y=forecast_values,
        mode='lines+markers',
        name='线性预测 (2025-2034)',
        line=dict(color='#FF6B35', width=2, dash='dot'),
        marker=dict(size=7, symbol='diamond'),
        hovertemplate='预测: %{x}年 %{y:.2f} M km²<extra></extra>'
    ))

    # 置信带
    ci_upper = forecast_values + 1.96 * std_resid
    ci_lower = forecast_values - 1.96 * std_resid
    fig5.add_trace(go.Scatter(
        x=list(forecast_years) + list(forecast_years)[::-1],
        y=list(ci_upper) + list(ci_lower)[::-1],
        fill='toself',
        fillcolor='rgba(255,107,53,0.1)',
        line=dict(color='rgba(255,107,53,0)'),
        name='95%置信区间',
        hovertemplate='95%置信区间<extra></extra>'
    ))

    fig5.update_layout(
        xaxis_title='年份',
        yaxis_title='年均海冰面积 (M km²)',
        template='plotly_white',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig5, use_container_width=True)

    # 预测数据表
    forecast_df = pd.DataFrame({
        '预测年份': forecast_years,
        '预测面积 (M km²)': [round(v, 2) for v in forecast_values],
        '95%下限': [round(v - 1.96*std_resid, 2) for v in forecast_values],
        '95%上限': [round(v + 1.96*std_resid, 2) for v in forecast_values],
        '相对1979年变化': [f"{((v - mean_arr[0])/mean_arr[0]*100):.1f}%" for v in forecast_values]
    })
    st.markdown("#### 预测数据表 (2030年前)")
    st.dataframe(forecast_df[forecast_df['预测年份'] <= 2030], use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div style="background:#fff3e0;padding:1rem;border-radius:8px;border-left:4px solid #FF6B35;margin-top:0.5rem">
    <b>⚠️ 预测说明：</b>以上预测基于 <b>1979-2024 年线性回归模型</b>（R² = {trend['r_squared']:.3f}），
    假设气候变化趋势持续。按此模型，到 <b>2030 年</b>北极年均海冰面积预计降至约
    <b>{forecast_values[5]:.2f} M km²</b>，航道通航窗口将显著延长。
    实际变化还受厄尔尼诺/拉尼娜、黑碳沉积等非线性因素影响。
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 NSIDC 数据获取说明", expanded=False):
        st.markdown("""
        **官方数据获取方式**：
        1. 访问 NSIDC 官网：https://nsidc.org/data/g02135
        2. 下载 Monthly Sea Ice Extent 表格（CSV 格式）
        3. 替换 `data/processed/ice_area_monthly.csv` 文件

        **NSIDC 数据字段说明**：
        - `Year`, `Month`：年月
        - `Extent`：海冰范围（百万平方公里）
        - `Area`：海冰面积（百万平方公里）

        **数据更新频率**：每月更新一次，通常在次月初发布
        """)

st.divider()
st.caption("数据来源: NSIDC Sea Ice Index (G02135) · 美国国家冰雪数据中心 · https://nsidc.org/data/g02135")
