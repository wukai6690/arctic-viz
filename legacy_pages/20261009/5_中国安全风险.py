"""
模块5：中国北极安全风险评估与策略参考
浅色研究主题 · 原版功能保留
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_risk_data, get_swot_data, get_strategy_recommendations
from src.viz import create_risk_matrix, create_swot_chart

st.set_page_config(page_title="中国安全风险", page_icon="◎", layout="wide")

from src.presentation import apply_presentation, show_chart
apply_presentation('risk')


st.markdown("""

<div class="page-header">
    <h1> 中国北极安全风险评估与策略参考</h1>
    <p>四维风险矩阵 · SWOT分析 · 中国应对策略推演沙盘</p>
</div>
""", unsafe_allow_html=True)


# ============ 数据 ============
risk_df = load_risk_data()
swot_data = get_swot_data()

avg_risk = risk_df['risk_level'].mean()
high_risk_count = (risk_df['risk_level'] >= 7).sum()
max_risk = risk_df['risk_level'].max()
max_risk_region = risk_df[risk_df['risk_level'] == max_risk]['region'].values[0] if max_risk > 0 else 'N/A'

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label"> 平均风险等级</div>
        <div class="kpi-val" style="color:#b19059">{avg_risk:.1f}/10</div>
        <div class="kpi-sub">综合评级</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 高风险区域数</div>
        <div class="kpi-val" style="color:#b37564">{high_risk_count}</div>
        <div class="kpi-sub">7级以上</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 最高风险</div>
        <div class="kpi-val" style="color:#ac665a">{max_risk}/10</div>
        <div class="kpi-sub">{max_risk_region}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label"> 覆盖海域</div>
        <div class="kpi-val" style="color:#4b7883">10个</div>
        <div class="kpi-sub">主要北极海域</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 标签页 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([" 四维风险热力图", " SWOT分析", " 应对策略推演", " 风险详情", " 风险趋势"])


with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 北极航行与介入风险热力图</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    colorscale = [[0,'#5d8770'],[0.3,'#b69855'],[0.6,'#b19059'],[1,'#ac665a']]

    risk_cat = st.selectbox("选择风险类别", ['全部', '航道通行', '科考安全', '技术壁垒', '权益冲突'])

    if risk_cat == '全部':
        pivot = risk_df.pivot_table(values='risk_level', index='region', columns='category', aggfunc='mean')
    else:
        pivot = risk_df[risk_df['category'] == risk_cat].pivot_table(
            values='risk_level', index='region', columns='category', aggfunc='mean')

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns if risk_cat == '全部' else [risk_cat],
        y=pivot.index,
        colorscale=colorscale, zmin=1, zmax=10,
        colorbar=dict(title='风险等级', len=0.35, y=0.5),
        text=pivot.values, texttemplate='%{z:.0f}',
        textfont=dict(color='white', size=14),
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>'
    ))
    fig_heat.update_layout(
        margin=dict(l=160, r=40, t=40, b=60),
        height=max(420, len(pivot) * 50),
        xaxis_title='', yaxis_title='',
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    show_chart(fig_heat, use_container_width=True)

    st.markdown("#### 风险等级说明")
    legend_cols = st.columns(5)
    legend_data = [
        ('1-3', '低风险', '#5d8770'), ('4-5', '中风险', '#b69855'),
        ('6-7', '较高风险', '#b19059'), ('8-9', '高风险', '#ac665a'), ('10', '极高风险', '#dc2626'),
    ]
    for i, (level, label, color) in enumerate(legend_data):
        with legend_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.7rem;background:var(--card);border-radius:10px;border:1px solid {color};">
                <div style="font-size:1.2rem;font-weight:800;color:{color};">{level}</div>
                <div style="font-size:0.68rem;color:var(--text3);">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 分区域风险详情")
    region_select = st.selectbox("选择海域", risk_df['region'].unique())
    region_data = risk_df[risk_df['region'] == region_select]
    rc_cols = st.columns(len(region_data))
    for i, (_, row) in enumerate(region_data.iterrows()):
        level = row['risk_level']
        color = '#5d8770' if level < 4 else '#b69855' if level < 7 else '#ac665a'
        with rc_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:var(--card);border-radius:12px;border-top:3px solid {color};">
                <div style="font-size:1.5rem;font-weight:800;color:{color};">{int(level)}</div>
                <div style="font-size:0.68rem;color:var(--text2);">{row['category']}</div>
                <div style="font-size:0.62rem;color:var(--text3);margin-top:3px;">{row['main_factors']}</div>
            </div>
            """, unsafe_allow_html=True)

    region_row = risk_df[risk_df['region'] == region_select].iloc[0]
    st.info(f"**{region_select}** | 纬度: {region_row['lat']}°N | 经度: {region_row['lon']}°E | 所属区域: {region_row['belong']}")
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 中国北极战略 SWOT 分析</h3>', unsafe_allow_html=True)

    fig_swot = create_swot_chart(swot_data)
    show_chart(fig_swot, use_container_width=True)

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #5d8770;">
            <div style="font-weight:700;color:#5d8770;font-size:1rem;margin-bottom:0.5rem;">S 优势</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>科研实力：</b>极地科考体系完善，「雪龙2」全年候航行能力</li>
                <li><b>资本优势：</b>北极能源项目投资规模领先</li>
                <li><b>技术进步：</b>极地LNG船、破冰船建造技术快速追赶</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #b37564;margin-top:0.8rem;">
            <div style="font-weight:700;color:#b37564;font-size:1rem;margin-bottom:0.5rem;">W 劣势</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>距离劣势：</b>非北极国家，距北极核心区数千公里</li>
                <li><b>制度缺失：</b>缺乏北极治理机制正式成员资格</li>
                <li><b>技术差距：</b>核动力破冰船等领域仍有差距</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with detail_cols[1]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #4b7883;">
            <div style="font-weight:700;color:#4b7883;font-size:1rem;margin-bottom:0.5rem;">O 机会</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>航道价值：</b>气候变化加速航道通航窗口扩大</li>
                <li><b>合作空间：</b>科技合作仍是大国关系「压舱石」</li>
                <li><b>规则制定：</b>北极治理规则重构期为中国参与提供窗口</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #b19059;margin-top:0.8rem;">
            <div style="font-weight:700;color:#b19059;font-size:1rem;margin-bottom:0.5rem;">T 威胁</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>大国对抗：</b>中美博弈向北极延伸，技术脱钩风险上升</li>
                <li><b>航道控制：</b>俄罗斯强化东北航道管辖限制</li>
                <li><b>理事受阻：</b>北极理事会功能受损，多边机制弱化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 中国应对策略推演沙盘</h3>', unsafe_allow_html=True)

    scenario = st.selectbox("选择风险情景", [
        "正常运营情景", "航道封锁情景", "多边机制停摆情景",
        "大国军事对峙升级情景", "极端气候灾害情景"
    ])

    strategy = get_strategy_recommendations(scenario)
    risk_level_color = {'低': '#5d8770', '中': '#b69855', '中高': '#b19059', '高': '#ac665a'}
    rc = risk_level_color.get(strategy['risk_level'], '#6b7280')

    st.markdown(f"""
    <div style="background:var(--card);border-radius:16px;padding:1.2rem;border-left:5px solid {strategy['color']};margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <h3 style="color:{strategy['color']};margin:0;font-size:1.1rem;">{strategy['title']}</h3>
            <span style="background:{rc}22;color:{rc};padding:3px 12px;border-radius:12px;font-size:0.8rem;font-weight:600;">
                风险等级：{strategy['risk_level']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    area_colors = {'科考安全': '#4b7883', '技术攻关': '#867697', '航道保障': '#b19059', '外交参与': '#5d8770'}
    strategy_cols = st.columns(2)
    items = strategy['items']
    for i, (area, advice) in enumerate(items):
        color = area_colors.get(area, '#6b7280')
        with strategy_cols[i % 2]:
            st.markdown(f"""
            <div class="strat-card" style="border-color:{color};">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.4rem;">
                    <span style="background:{color}22;color:{color};padding:3px 10px;border-radius:8px;font-size:0.75rem;font-weight:600;">{area}</span>
                </div>
                <p style="font-size:0.85rem;color:#1a1a2e;margin:0;line-height:1.7;">{advice}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 风险详情总表</h3>', unsafe_allow_html=True)

    display_df = risk_df[['region', 'lat', 'lon', 'belong', 'category', 'risk_level', 'trend', 'main_factors']].rename(
        columns={'region': '海域', 'lat': '纬度', 'lon': '经度', 'belong': '所属区域',
                'category': '风险类别', 'risk_level': '风险等级', 'trend': '趋势', 'main_factors': '主要因素'}
    ).sort_values('风险等级', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("#### 主要风险来源")
    factor_counts = risk_df['main_factors'].value_counts()
    import plotly.graph_objects as go
    fig_factors = go.Figure(go.Bar(
        x=factor_counts.values, y=factor_counts.index,
        orientation='h',
        marker_color='#ac665a',
        hovertemplate='%{y}: %{x}个区域<extra></extra>'
    ))
    fig_factors.update_layout(
        xaxis_title='涉及区域数', yaxis_title='风险来源',
        height=300, margin=dict(l=160, r=20, t=20, b=40),
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)'),
        xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
    )
    show_chart(fig_factors, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3> 风险趋势分析</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    trend_counts = risk_df['trend'].value_counts()
    fig_trend = go.Figure(go.Pie(
        labels=['上升', '稳定', '下降'],
        values=[trend_counts.get('上升', 0), trend_counts.get('稳定', 0), trend_counts.get('下降', 0)],
        hole=0.4,
        marker_colors=['#ac665a', '#b69855', '#5d8770'],
        textinfo='percent+label'
    ))
    fig_trend.update_layout(
        height=320, margin=dict(l=20, r=20, t=20, b=20),
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)')
    )
    show_chart(fig_trend, use_container_width=True)

    st.markdown("#### 各风险类别平均等级")
    cat_avg = risk_df.groupby('category')['risk_level'].mean().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(
        x=cat_avg.values, y=cat_avg.index,
        orientation='h',
        marker_color=['#ac665a' if v > 6 else '#b69855' if v > 4 else '#5d8770' for v in cat_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_cat.update_layout(
        xaxis_title='平均风险等级', yaxis_title='风险类别',
        height=280, margin=dict(l=120, r=20, t=20, b=40),
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)'),
        xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
    )
    show_chart(fig_cat, use_container_width=True)

    st.markdown("#### 海域风险排名（综合四维）")
    region_avg = risk_df.groupby('region')['risk_level'].mean().sort_values(ascending=True)
    fig_rank = go.Figure(go.Bar(
        x=region_avg.values, y=region_avg.index,
        orientation='h',
        marker_color=['#ac665a' if v > 6 else '#b69855' if v > 4 else '#5d8770' for v in region_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_rank.update_layout(
        xaxis_title='综合风险等级', yaxis_title='海域',
        height=350, margin=dict(l=140, r=20, t=20, b=40),
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(54,80,65,0.8)'),
        xaxis=dict(gridcolor='rgba(54,80,65,0.16)', tickfont_color='rgba(54,80,65,0.6)'),
        yaxis=dict(tickfont_color='rgba(54,80,65,0.8)'),
    )
    show_chart(fig_rank, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.markdown("""
<div style="background:rgba(249,115,22,0.06);padding:1rem;border-radius:12px;border-left:4px solid #b19059;">
<b> 风险评估说明：</b>本模块保留原版风险分数、SWOT 条目和情景策略，当前为研究框架示例。尚未建立可核验的指标资料、权重依据和检验结果，不能作为已经完成的风险评估。
</div>
""", unsafe_allow_html=True)
st.caption("数据状态：原版示例设定。后续需逐项补充指标来源、计算方法与验证依据。")
