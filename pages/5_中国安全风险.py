"""
模块5：中国北极安全风险评估与策略参考
深色沉浸主题 v6.0
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_risk_data, get_swot_data, get_strategy_recommendations
from src.viz import create_risk_matrix, create_swot_chart

st.set_page_config(page_title="中国安全风险", page_icon="🛡️", layout="wide")

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
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(239,68,68,0.2) !important; color: #fca5a5 !important; }
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
    .page-header { background: linear-gradient(135deg, #0f172a 0%, #7f1d1d 100%); padding: 1.8rem 2rem; border-radius: 0 0 18px 18px; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(239,68,68,0.15); position: relative; overflow: hidden; }
    .page-header::before { content: ''; position: absolute; top: -50%; right: -5%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(239,68,68,0.06) 0%, transparent 70%); pointer-events: none; }
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
    .swot-card { background: var(--card); border-radius: 12px; padding: 1rem; border: 1px solid; }
    .strat-card { background: #fafafa; border-radius: 12px; padding: 1rem; border-left: 3px solid; margin: 0.5rem 0; }
</style>
<div class="page-header">
    <h1>🛡️ 中国北极安全风险评估与策略参考</h1>
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
        <div class="kpi-label">📊 平均风险等级</div>
        <div class="kpi-val" style="color:#fb923c">{avg_risk:.1f}/10</div>
        <div class="kpi-sub">综合评级</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">⚠️ 高风险区域数</div>
        <div class="kpi-val" style="color:#f87171">{high_risk_count}</div>
        <div class="kpi-sub">7级以上</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🔴 最高风险</div>
        <div class="kpi-val" style="color:#ef4444">{max_risk}/10</div>
        <div class="kpi-sub">{max_risk_region}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🌊 覆盖海域</div>
        <div class="kpi-val" style="color:#60a5fa">10个</div>
        <div class="kpi-sub">主要北极海域</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 标签页 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ 四维风险热力图", "📊 SWOT分析", "🧩 应对策略推演", "📋 风险详情", "📈 风险趋势"])


with tab1:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗺️ 北极航行与介入风险热力图</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go
    colorscale = [[0,'#22c55e'],[0.3,'#eab308'],[0.6,'#f97316'],[1,'#ef4444']]

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
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("#### 风险等级说明")
    legend_cols = st.columns(5)
    legend_data = [
        ('1-3', '低风险', '#22c55e'), ('4-5', '中风险', '#eab308'),
        ('6-7', '较高风险', '#f97316'), ('8-9', '高风险', '#ef4444'), ('10', '极高风险', '#dc2626'),
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
        color = '#22c55e' if level < 4 else '#eab308' if level < 7 else '#ef4444'
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
    st.markdown('<h3>📊 中国北极战略 SWOT 分析</h3>', unsafe_allow_html=True)

    fig_swot = create_swot_chart(swot_data)
    st.plotly_chart(fig_swot, use_container_width=True)

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #22c55e;">
            <div style="font-weight:700;color:#4ade80;font-size:1rem;margin-bottom:0.5rem;">S 优势</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>科研实力：</b>极地科考体系完善，「雪龙2」全年候航行能力</li>
                <li><b>资本优势：</b>北极能源项目投资规模领先</li>
                <li><b>技术进步：</b>极地LNG船、破冰船建造技术快速追赶</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #f87171;margin-top:0.8rem;">
            <div style="font-weight:700;color:#f87171;font-size:1rem;margin-bottom:0.5rem;">W 劣势</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>距离劣势：</b>非北极国家，距北极核心区数千公里</li>
                <li><b>制度缺失：</b>缺乏北极治理机制正式成员资格</li>
                <li><b>技术差距：</b>核动力破冰船等领域仍有差距</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with detail_cols[1]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #60a5fa;">
            <div style="font-weight:700;color:#60a5fa;font-size:1rem;margin-bottom:0.5rem;">O 机会</div>
            <ul style="font-size:0.8rem;color:var(--text2);line-height:1.9;padding-left:1.2rem;margin:0;">
                <li><b>航道价值：</b>气候变化加速航道通航窗口扩大</li>
                <li><b>合作空间：</b>科技合作仍是大国关系「压舱石」</li>
                <li><b>规则制定：</b>北极治理规则重构期为中国参与提供窗口</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #fb923c;margin-top:0.8rem;">
            <div style="font-weight:700;color:#fb923c;font-size:1rem;margin-bottom:0.5rem;">T 威胁</div>
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
    st.markdown('<h3>🧩 中国应对策略推演沙盘</h3>', unsafe_allow_html=True)

    scenario = st.selectbox("选择风险情景", [
        "正常运营情景", "航道封锁情景", "多边机制停摆情景",
        "大国军事对峙升级情景", "极端气候灾害情景"
    ])

    strategy = get_strategy_recommendations(scenario)
    risk_level_color = {'低': '#22c55e', '中': '#eab308', '中高': '#fb923c', '高': '#ef4444'}
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

    area_colors = {'科考安全': '#60a5fa', '技术攻关': '#a855f7', '航道保障': '#fb923c', '外交参与': '#22c55e'}
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
    st.markdown('<h3>📋 风险详情总表</h3>', unsafe_allow_html=True)

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
        marker_color='#ef4444',
        hovertemplate='%{y}: %{x}个区域<extra></extra>'
    ))
    fig_factors.update_layout(
        xaxis_title='涉及区域数', yaxis_title='风险来源',
        height=300, margin=dict(l=160, r=20, t=20, b=40),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
        yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
    )
    st.plotly_chart(fig_factors, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="dk-card">', unsafe_allow_html=True)
    st.markdown('<h3>📈 风险趋势分析</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    trend_counts = risk_df['trend'].value_counts()
    fig_trend = go.Figure(go.Pie(
        labels=['上升', '稳定', '下降'],
        values=[trend_counts.get('上升', 0), trend_counts.get('稳定', 0), trend_counts.get('下降', 0)],
        hole=0.4,
        marker_colors=['#ef4444', '#eab308', '#22c55e'],
        textinfo='percent+label'
    ))
    fig_trend.update_layout(
        height=320, margin=dict(l=20, r=20, t=20, b=20),
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)')
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("#### 各风险类别平均等级")
    cat_avg = risk_df.groupby('category')['risk_level'].mean().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(
        x=cat_avg.values, y=cat_avg.index,
        orientation='h',
        marker_color=['#ef4444' if v > 6 else '#eab308' if v > 4 else '#22c55e' for v in cat_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_cat.update_layout(
        xaxis_title='平均风险等级', yaxis_title='风险类别',
        height=280, margin=dict(l=120, r=20, t=20, b=40),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
        yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("#### 海域风险排名（综合四维）")
    region_avg = risk_df.groupby('region')['risk_level'].mean().sort_values(ascending=True)
    fig_rank = go.Figure(go.Bar(
        x=region_avg.values, y=region_avg.index,
        orientation='h',
        marker_color=['#ef4444' if v > 6 else '#eab308' if v > 4 else '#22c55e' for v in region_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_rank.update_layout(
        xaxis_title='综合风险等级', yaxis_title='海域',
        height=350, margin=dict(l=140, r=20, t=20, b=40),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont_color='rgba(255,255,255,0.6)'),
        yaxis=dict(tickfont_color='rgba(255,255,255,0.8)'),
    )
    st.plotly_chart(fig_rank, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.markdown("""
<div style="background:rgba(249,115,22,0.06);padding:1rem;border-radius:12px;border-left:4px solid #f97316;">
<b>⚠️ 风险评估说明：</b>本模块风险评估基于公开数据和专家判断综合得出，用于学术研究参考，不构成任何政策建议。具体决策请咨询专业机构。风险等级会受到国际形势变化影响。
</div>
""", unsafe_allow_html=True)
st.caption("数据来源: 基于公开资料综合评估 · 风险模型参考相关学术文献")
