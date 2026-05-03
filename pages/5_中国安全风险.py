"""
模块5：中国北极安全风险评估与策略参考
风险热力图 + SWOT分析 + 中国应对策略推演
重制版：高级UI、精细化交互
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_risk_data, get_swot_data, load_stations, get_strategy_recommendations
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, create_risk_matrix, create_swot_chart

st.set_page_config(page_title="中国安全风险", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .page-header {
        background: linear-gradient(135deg, #B71C1C 0%, #C62828 50%, #E53935 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 18px 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(198,40,40,0.2);
    }
    .page-header h1 { color: white !important; font-size: 1.55rem; font-weight: 700; margin: 0 0 0.3rem 0; }
    .page-header p { color: rgba(255,255,255,0.82) !important; font-size: 0.83rem; margin: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 18px; font-weight: 600; font-size: 0.85rem; }
    section[data-testid="stMain"] { background: #f5f7fa !important; }
    section[data-testid="stMain"] > div { background: #f5f7fa !important; }
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
    .swot-card {
        background: white; border-radius: 12px; padding: 1rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06); border: 1px solid;
    }
    .strategy-card {
        background: #FAFAFA; border-radius: 12px; padding: 1rem;
        border-left: 3px solid; margin: 0.5rem 0;
    }
    .risk-legend-item {
        display: flex; align-items: center; gap: 8px;
        background: white; border-radius: 10px; padding: 0.7rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); flex: 1;
    }
</style>
<div class="page-header">
    <h1>🛡️ 中国北极安全风险评估与策略参考</h1>
    <p>四维风险矩阵 · SWOT分析 · 中国应对策略推演沙盘</p>
</div>
""", unsafe_allow_html=True)


# 加载数据
risk_df = load_risk_data()
swot_data = get_swot_data()
stations_data = load_stations()

# ============ KPI ============
avg_risk = risk_df['risk_level'].mean()
high_risk_count = (risk_df['risk_level'] >= 7).sum()
max_risk = risk_df['risk_level'].max()
max_risk_region = risk_df[risk_df['risk_level'] == max_risk]['region'].values[0] if max_risk > 0 else 'N/A'

kpi_html = f"""
<div class="kpi-row">
    <div class="kpi-box">
        <div class="kpi-label">📊 平均风险等级</div>
        <div class="kpi-val" style="color:#FF6B35">{avg_risk:.1f}/10</div>
        <div class="kpi-sub">综合评级</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">⚠️ 高风险区域数</div>
        <div class="kpi-val" style="color:#E53935">{high_risk_count}</div>
        <div class="kpi-sub">7级以上</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🔴 最高风险</div>
        <div class="kpi-val" style="color:#B71C1C">{max_risk}/10</div>
        <div class="kpi-sub">{max_risk_region}</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">🌊 覆盖海域</div>
        <div class="kpi-val" style="color:#1E88E5">10个</div>
        <div class="kpi-sub">主要北极海域</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)


# ============ 主区域 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 四维风险热力图", "📊 SWOT分析", "🧩 应对策略推演", "📋 风险详情", "📈 风险趋势"
])


with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🗺️ 北极航行与介入风险热力图</h3>', unsafe_allow_html=True)
    st.caption("颜色越深（红）= 风险等级越高 | 数值标注在单元格内")

    risk_cat = st.selectbox("选择风险类别", ['全部', '航道通行', '科考安全', '技术壁垒', '权益冲突'])

    if risk_cat == '全部':
        pivot = risk_df.pivot_table(values='risk_level', index='region', columns='category', aggfunc='mean')
    else:
        pivot = risk_df[risk_df['category'] == risk_cat].pivot_table(
            values='risk_level', index='region', columns='category', aggfunc='mean')

    import plotly.graph_objects as go
    colorscale = [[0,'#43A047'],[0.3,'#FDD835'],[0.6,'#FF9800'],[1,'#E53935']]

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns if risk_cat == '全部' else [risk_cat],
        y=pivot.index,
        colorscale=colorscale, zmin=1, zmax=10,
        colorbar=dict(title='风险等级', tickvals=[1,3,5,7,10],
                     ticktext=['1低','3','5中','7','10高']),
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>',
        text=pivot.values, texttemplate='%{z:.0f}',
        textfont=dict(color='white', size=14)
    ))
    fig_heat.update_layout(
        margin=dict(l=140, r=40, t=40, b=60),
        height=max(400, len(pivot) * 48),
        xaxis_title='', yaxis_title='',
        template='plotly_white'
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # 图例
    st.markdown("**风险等级说明：**")
    legend_cols = st.columns(5)
    legend_data = [
        ('1-3', '低风险', '#43A047'),
        ('4-5', '中风险', '#FF9800'),
        ('6-7', '较高风险', '#FF6B35'),
        ('8-9', '高风险', '#E53935'),
        ('10', '极高风险', '#B71C1C'),
    ]
    for i, (level, label, color) in enumerate(legend_data):
        with legend_cols[i]:
            st.markdown(f"""
            <div class="risk-legend-item" style="border:1px solid {color};">
                <div style="font-size:1.2rem;font-weight:800;color:{color};">{level}</div>
                <div style="font-size:0.7rem;color:#546E7A;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # 分区域分析
    st.markdown("#### 分区域风险详情")
    region_select = st.selectbox("选择海域", risk_df['region'].unique())
    region_data = risk_df[risk_df['region'] == region_select]
    rc_cols = st.columns(len(region_data))
    for i, (_, row) in enumerate(region_data.iterrows()):
        level = row['risk_level']
        color = '#43A047' if level < 4 else '#FF9800' if level < 7 else '#E53935'
        trend_icon = '↓' if row['trend']=='下降' else '→' if row['trend']=='稳定' else '↑'
        trend_color = '#43A047' if row['trend']=='下降' else '#FF9800' if row['trend']=='稳定' else '#E53935'
        with rc_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:white;border-radius:12px;
                        box-shadow:0 1px 6px rgba(0,0,0,0.06);border-top:3px solid {color};">
                <div style="font-size:1.5rem;font-weight:800;color:{color};">{int(level)}</div>
                <div style="font-size:0.7rem;color:#546E7A;">{row['category']}</div>
                <div style="font-size:0.65rem;color:#90A4AE;margin-top:4px">{row['main_factors']}</div>
                <div style="font-size:0.65rem;color:{trend_color};margin-top:2px">{trend_icon} {row['trend']}</div>
            </div>
            """, unsafe_allow_html=True)

    region_row = risk_df[risk_df['region'] == region_select].iloc[0]
    st.info(f"**{region_select}** | 纬度: {region_row['lat']}°N | 经度: {region_row['lon']}°E | 所属区域: {region_row['belong']}")
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 中国北极战略 SWOT 分析</h3>', unsafe_allow_html=True)

    fig_swot = create_swot_chart(swot_data)
    st.plotly_chart(fig_swot, use_container_width=True)

    # 详细解读
    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #43A047;border-color:#43A047;">
            <div style="font-weight:700;color:#43A047;font-size:1rem;margin-bottom:0.5rem;">S 优势</div>
            <ul style="font-size:0.8rem;color:#546E7A;line-height:1.8;padding-left:1.2rem;margin:0;">
                <li><b>科研实力：</b>极地科考体系完善，「雪龙2」全年候航行能力</li>
                <li><b>资本优势：</b>北极能源项目投资规模领先</li>
                <li><b>技术进步：</b>极地LNG船、破冰船建造技术快速追赶</li>
                <li><b>战略视野：</b>「人类命运共同体」理念提供独特治理观</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #E53935;border-color:#E53935;margin-top:0.8rem;">
            <div style="font-weight:700;color:#E53935;font-size:1rem;margin-bottom:0.5rem;">W 劣势</div>
            <ul style="font-size:0.8rem;color:#546E7A;line-height:1.8;padding-left:1.2rem;margin:0;">
                <li><b>距离劣势：</b>非北极国家，距北极核心区数千公里</li>
                <li><b>制度缺失：</b>缺乏北极治理机制正式成员资格</li>
                <li><b>技术差距：</b>核动力破冰船等领域仍有差距</li>
                <li><b>经验不足：</b>北极航道商业运营经验积累时间较短</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with detail_cols[1]:
        st.markdown("""
        <div class="swot-card" style="border-left:4px solid #1E88E5;border-color:#1E88E5;">
            <div style="font-weight:700;color:#1E88E5;font-size:1rem;margin-bottom:0.5rem;">O 机会</div>
            <ul style="font-size:0.8rem;color:#546E7A;line-height:1.8;padding-left:1.2rem;margin:0;">
                <li><b>航道价值：</b>气候变化加速航道通航窗口扩大</li>
                <li><b>合作空间：</b>科技合作仍是大国关系「压舱石」</li>
                <li><b>规则制定：</b>北极治理规则重构期为中国参与提供窗口</li>
                <li><b>能源需求：</b>北极油气资源满足进口多元化需求</li>
            </ul>
        </div>
        <div class="swot-card" style="border-left:4px solid #FF6B35;border-color:#FF6B35;margin-top:0.8rem;">
            <div style="font-weight:700;color:#FF6B35;font-size:1rem;margin-bottom:0.5rem;">T 威胁</div>
            <ul style="font-size:0.8rem;color:#546E7A;line-height:1.8;padding-left:1.2rem;margin:0;">
                <li><b>大国对抗：</b>中美博弈向北极延伸，技术脱钩风险上升</li>
                <li><b>航道控制：</b>俄罗斯强化东北航道管辖限制</li>
                <li><b>环境约束：</b>国际环保压力限制资源开发空间</li>
                <li><b>理事受阻：</b>北极理事会功能受损，多边机制弱化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🧩 中国应对策略推演沙盘</h3>', unsafe_allow_html=True)
    st.markdown("选择风险情景，获取智能生成的对策建议，涵盖科考安全、技术攻关、航道保障、外交参与四大方向", unsafe_allow_html=False)

    scenario = st.selectbox("选择风险情景", [
        "正常运营情景",
        "航道封锁情景",
        "多边机制停摆情景",
        "大国军事对峙升级情景",
        "极端气候灾害情景"
    ])

    strategy = get_strategy_recommendations(scenario)
    risk_level_color = {'低': '#43A047', '中': '#FF9800', '中高': '#FF6B35', '高': '#E53935'}
    rc = risk_level_color.get(strategy['risk_level'], '#757575')

    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:1.2rem;
                border-left:5px solid {strategy['color']};margin-bottom:1rem;
                box-shadow:0 1px 10px rgba(0,0,0,0.07);">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <h3 style="color:{strategy['color']};margin:0;font-size:1.1rem;">{strategy['title']}</h3>
            <span style="background:{rc}22;color:{rc};padding:3px 12px;border-radius:12px;font-size:0.8rem;font-weight:600;">
                风险等级：{strategy['risk_level']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    area_colors = {
        '科考安全': '#1E88E5',
        '技术攻关': '#7B1FA2',
        '航道保障': '#FF6B35',
        '外交参与': '#43A047'
    }

    strategy_cols = st.columns(2)
    items = strategy['items']
    for i, (area, advice) in enumerate(items):
        color = area_colors.get(area, '#757575')
        with strategy_cols[i % 2]:
            st.markdown(f"""
            <div class="strategy-card" style="border-color:{color};">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.4rem;">
                    <span style="background:{color}22;color:{color};padding:3px 10px;
                               border-radius:8px;font-size:0.75rem;font-weight:600;">{area}</span>
                </div>
                <p style="font-size:0.85rem;color:#546E7A;margin:0;line-height:1.7">{advice}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
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
        marker_color='#E53935',
        hovertemplate='%{y}: %{x}个区域<extra></extra>'
    ))
    fig_factors.update_layout(
        xaxis_title='涉及区域数', yaxis_title='风险来源',
        height=300, margin=dict(l=160, r=20, t=20, b=40),
        template='plotly_white'
    )
    st.plotly_chart(fig_factors, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab5:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📈 风险趋势分析</h3>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    st.markdown("#### 风险趋势分布")
    trend_counts = risk_df['trend'].value_counts()
    fig_trend = go.Figure(go.Pie(
        labels=['上升', '稳定', '下降'],
        values=[trend_counts.get('上升', 0), trend_counts.get('稳定', 0), trend_counts.get('下降', 0)],
        hole=0.4,
        marker_colors=['#E53935', '#FF9800', '#43A047'],
        textinfo='percent+label'
    ))
    fig_trend.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("#### 各风险类别平均等级")
    cat_avg = risk_df.groupby('category')['risk_level'].mean().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(
        x=cat_avg.values, y=cat_avg.index,
        orientation='h',
        marker_color=['#E53935' if v > 6 else '#FF9800' if v > 4 else '#43A047' for v in cat_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_cat.update_layout(
        xaxis_title='平均风险等级', yaxis_title='风险类别',
        height=280, margin=dict(l=120, r=20, t=20, b=40),
        template='plotly_white'
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("#### 海域风险排名（综合四维）")
    region_avg = risk_df.groupby('region')['risk_level'].mean().sort_values(ascending=True)
    fig_rank = go.Figure(go.Bar(
        x=region_avg.values, y=region_avg.index,
        orientation='h',
        marker_color=['#E53935' if v > 6 else '#FF9800' if v > 4 else '#43A047' for v in region_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_rank.update_layout(
        xaxis_title='综合风险等级', yaxis_title='海域',
        height=350, margin=dict(l=140, r=20, t=20, b=40),
        template='plotly_white'
    )
    st.plotly_chart(fig_rank, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.markdown("""
<div style="background:#FFF8E1;padding:1rem;border-radius:12px;border-left:4px solid #FF6F00;">
<b>⚠️ 风险评估说明：</b>本模块风险评估基于公开数据和专家判断综合得出，
用于学术研究参考，不构成任何政策建议。具体决策请咨询专业机构。
风险等级会受到国际形势变化影响，本平台将持续更新数据。
</div>
""", unsafe_allow_html=True)
st.caption("数据来源: 基于公开资料综合评估 · 风险模型参考相关学术文献")
