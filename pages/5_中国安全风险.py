"""
模块5：中国北极安全风险评估与策略参考
风险热力图 + SWOT分析 + 中国应对策略推演
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_risk_data, get_swot_data, load_stations, get_strategy_recommendations

st.set_page_config(page_title="中国安全风险", page_icon="🛡️", layout="wide")


# =========================================================================
# 全局样式
# =========================================================================
st.markdown("""
<style>
    .stApp [data-testid="stMainBlockContainer"] { background: #ffffff; }
    section[data-testid="stMain"] { background: #ffffff; }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown li, section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4 {
        color: #1e293b !important;
    }
    .page-hero {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 50%, #b91c1c 100%);
        border-radius: 14px;
        padding: 36px 32px;
        margin-bottom: 28px;
    }
    .page-hero h1 { color: white !important; font-size: 1.6rem; font-weight: 800; margin: 0 0 6px 0; }
    .page-hero p { color: rgba(255,255,255,0.8) !important; font-size: 0.88rem; margin: 0; }
    .section-title {
        font-size: 1rem; font-weight: 700; color: #0f172a;
        margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0;
    }
    .kpi-card {
        background: white; border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.04);
        text-align: center;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 800; line-height: 1; margin-bottom: 4px; }
    .kpi-label { font-size: 0.75rem; color: #64748b; font-weight: 500; }
    .risk-box { background:#fef2f2;border-radius:12px;padding:16px;border-left:4px solid #dc2626; }
    .swot-card { background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# 侧边栏
# =========================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 12px 0 20px 0;">
            <div style="font-size:2.5rem;">🛡️</div>
            <div style="font-size:1.05rem; font-weight:700; color:white !important; margin-top:6px;">中国安全风险</div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.55);">模块 5 · v5.0</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        pages_map = [
            ("🏠", "首页概览", "app.py"),
            ("🌡️", "气候时空监测", "pages/2_气候时空监测.py"),
            ("🏛️", "地缘战略格局", "pages/3_地缘战略格局.py"),
            ("⚙️", "技术竞争与合作", "pages/4_极地核心技术.py"),
            ("🛡️", "中国安全风险", "pages/5_中国安全风险.py"),
            ("🗄️", "数据中心工具", "pages/6_数据中心工具.py"),
            ("ℹ️", "关于本项目", "pages/7_关于本项目.py"),
        ]
        for icon, label, path in pages_map:
            st.page_link(path, label=label, icon=icon)
        st.divider()
        st.caption("© 2025-2026 大创专项")


render_sidebar()


# =========================================================================
# 页面头部
# =========================================================================
st.markdown("""
<div class="page-hero">
    <h1>🛡️ 中国北极安全风险评估与策略参考</h1>
    <p>四维风险矩阵 · SWOT分析 · 中国应对策略推演沙盘</p>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# 数据加载
# =========================================================================
try:
    risk_df = load_risk_data()
    swot_data = get_swot_data()
    stations_data = load_stations()
except Exception:
    st.error("数据加载失败")
    st.stop()

avg_risk = float(risk_df['risk_level'].mean())
high_risk_count = int((risk_df['risk_level'] >= 7).sum())
max_risk = float(risk_df['risk_level'].max())
max_risk_region = risk_df[risk_df['risk_level'] == max_risk]['region'].values[0] if max_risk > 0 else 'N/A'

# =========================================================================
# KPI
# =========================================================================
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#991b1b;">{avg_risk:.1f}</div>
    <div class="kpi-label">平均风险等级 /10</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#dc2626;">{high_risk_count}</div>
    <div class="kpi-label">高风险区域数（7级以上）</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#dc2626;">{max_risk}/10</div>
    <div class="kpi-label">最高风险（{max_risk_region}）</div></div>
    """, unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-value" style="color:#16a34a;">10</div>
    <div class="kpi-label">覆盖海域数量</div></div>
    """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 主区域
# =========================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 四维风险热力图", "📊 SWOT分析", "🧩 应对策略推演", "📋 风险详情", "📈 风险趋势"
])


# -------------------------------------------------------------------------
# Tab 1: 风险热力图
# -------------------------------------------------------------------------
with tab1:
    st.markdown('<div class="section-title">🗺️ 北极航行与介入风险热力图</div>', unsafe_allow_html=True)
    st.caption("颜色越深（红）= 风险等级越高 | 数值标注在单元格内")

    import plotly.graph_objects as go

    risk_cat = st.selectbox(
        "选择风险类别",
        ['全部', '航道通行', '科考安全', '技术壁垒', '权益冲突'],
        key="risk_cat_select"
    )

    if risk_cat == '全部':
        pivot = risk_df.pivot_table(values='risk_level', index='region', columns='category', aggfunc='mean')
    else:
        pivot = risk_df[risk_df['category'] == risk_cat].pivot_table(
            values='risk_level', index='region', columns='category', aggfunc='mean')

    colorscale = [[0,'#16a34a'],[0.3,'#fde047'],[0.6,'#f97316'],[1,'#dc2626']]

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
        margin=dict(l=160, r=40, t=40, b=60),
        height=max(400, len(pivot) * 50),
        xaxis_title='', yaxis_title=''
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # 风险等级说明
    st.markdown("##### 风险等级说明")
    legend_cols = st.columns(5)
    legend_data = [
        ('1-3', '低风险', '#16a34a'),
        ('4-5', '中风险', '#f97316'),
        ('6-7', '较高风险', '#ea580c'),
        ('8-9', '高风险', '#dc2626'),
        ('10', '极高风险', '#7f1d1d'),
    ]
    for i, (level, label, color) in enumerate(legend_data):
        with legend_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:12px;border-radius:8px;
                        background:{color}18;border:1px solid {color};">
                <div style="font-size:1.1rem;font-weight:800;color:{color};">{level}</div>
                <div style="font-size:0.72rem;color:#64748b;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # 分区域分析
    st.markdown("#### 分区域风险详情")
    region_select = st.selectbox("选择海域", risk_df['region'].unique(), key="region_select_risk")
    region_data = risk_df[risk_df['region'] == region_select]
    rc_cols = st.columns(len(region_data))
    for i, (_, row) in enumerate(region_data.iterrows()):
        level = float(row['risk_level'])
        color = '#16a34a' if level < 4 else '#f97316' if level < 7 else '#dc2626'
        trend_icon = '↓' if row['trend']=='下降' else '→' if row['trend']=='稳定' else '↑'
        trend_color = '#16a34a' if row['trend']=='下降' else '#f97316' if row['trend']=='稳定' else '#dc2626'
        with rc_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:12px;background:white;border-radius:12px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:3px solid {color};">
                <div style="font-size:1.5rem;font-weight:800;color:{color};">{int(level)}</div>
                <div style="font-size:0.72rem;color:#64748b;">{row['category']}</div>
                <div style="font-size:0.68rem;color:#94a3b8;margin-top:4px">{row['main_factors']}</div>
                <div style="font-size:0.68rem;color:{trend_color};margin-top:2px">{trend_icon} {row['trend']}</div>
            </div>
            """, unsafe_allow_html=True)

    region_row = risk_df[risk_df['region'] == region_select].iloc[0]
    st.info(f"**{region_select}** | 纬度: {region_row['lat']}°N | 经度: {region_row['lon']}°E | 所属区域: {region_row['belong']}")


# -------------------------------------------------------------------------
# Tab 2: SWOT分析
# -------------------------------------------------------------------------
with tab2:
    st.markdown('<div class="section-title">📊 中国北极战略 SWOT 分析</div>', unsafe_allow_html=True)

    try:
        from src.viz import create_swot_chart
        fig_swot = create_swot_chart(swot_data)
        st.plotly_chart(fig_swot, use_container_width=True)
    except Exception:
        st.info("SWOT图表加载中...")

    # SWOT详细解读
    st.markdown("#### SWOT 详细解读")
    detail_cols = st.columns(2)

    with detail_cols[0]:
        st.markdown("""
        <div style="border-left:4px solid #16a34a;padding-left:12px;margin-bottom:16px;background:#f0fdf4;padding:16px;border-radius:0 12px 12px 0;">
            <b style="color:#16a34a;font-size:1rem">优势 S</b>
            <ul style="font-size:0.82rem;color:#475569;line-height:1.9;margin-top:8px">
                <li><b>科研实力：</b>极地科考体系完善，「雪龙2」全年候航行能力</li>
                <li><b>资本优势：</b>北极能源项目投资规模领先</li>
                <li><b>技术进步：</b>极地LNG船、破冰船建造技术快速追赶</li>
                <li><b>战略视野：</b>「人类命运共同体」理念提供独特治理观</li>
            </ul>
        </div>
        <div style="border-left:4px solid #dc2626;padding-left:12px;background:#fef2f2;padding:16px;border-radius:0 12px 12px 0;">
            <b style="color:#dc2626;font-size:1rem">劣势 W</b>
            <ul style="font-size:0.82rem;color:#475569;line-height:1.9;margin-top:8px">
                <li><b>距离劣势：</b>非北极国家，距北极核心区数千公里</li>
                <li><b>制度缺失：</b>缺乏北极治理机制正式成员资格</li>
                <li><b>技术差距：</b>核动力破冰船等领域仍有差距</li>
                <li><b>经验不足：</b>北极航道商业运营经验积累时间较短</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with detail_cols[1]:
        st.markdown("""
        <div style="border-left:4px solid #1565C0;padding-left:12px;margin-bottom:16px;background:#eff6ff;padding:16px;border-radius:0 12px 12px 0;">
            <b style="color:#1565C0;font-size:1rem">机会 O</b>
            <ul style="font-size:0.82rem;color:#475569;line-height:1.9;margin-top:8px">
                <li><b>航道价值：</b>气候变化加速航道通航窗口扩大</li>
                <li><b>合作空间：</b>科技合作仍是大国关系「压舱石」</li>
                <li><b>规则制定：</b>北极治理规则重构期为中国参与提供窗口</li>
                <li><b>能源需求：</b>北极油气资源满足进口多元化需求</li>
            </ul>
        </div>
        <div style="border-left:4px solid #ea580c;padding-left:12px;background:#fff7ed;padding:16px;border-radius:0 12px 12px 0;">
            <b style="color:#ea580c;font-size:1rem">威胁 T</b>
            <ul style="font-size:0.82rem;color:#475569;line-height:1.9;margin-top:8px">
                <li><b>大国对抗：</b>中美博弈向北极延伸，技术脱钩风险上升</li>
                <li><b>航道控制：</b>俄罗斯强化东北航道管辖限制</li>
                <li><b>环境约束：</b>国际环保压力限制资源开发空间</li>
                <li><b>理事受阻：</b>北极理事会功能受损，多边机制弱化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# -------------------------------------------------------------------------
# Tab 3: 应对策略推演
# -------------------------------------------------------------------------
with tab3:
    st.markdown('<div class="section-title">🧩 中国应对策略推演沙盘</div>', unsafe_allow_html=True)
    st.caption("选择风险情景，获取智能生成的对策建议，涵盖科考安全、技术攻关、航道保障、外交参与四大方向")

    scenario = st.selectbox(
        "选择风险情景",
        [
            "正常运营情景",
            "航道封锁情景",
            "多边机制停摆情景",
            "大国军事对峙升级情景",
            "极端气候灾害情景"
        ],
        key="scenario_select"
    )

    strategy = get_strategy_recommendations(scenario)

    risk_level_color = {'低': '#16a34a', '中': '#f97316', '中高': '#ea580c', '高': '#dc2626'}
    rc = risk_level_color.get(strategy['risk_level'], '#757575')

    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:20px;
                border-left:5px solid {strategy['color']};margin-bottom:20px;
                box-shadow:0 2px 12px rgba(0,0,0,0.06);">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <h3 style="color:{strategy['color']};margin:0;font-size:1.2rem;">{strategy['title']}</h3>
            <span style="background:{rc}22;color:{rc};padding:3px 12px;border-radius:12px;font-size:0.8rem;font-weight:600;">
                风险等级：{strategy['risk_level']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    area_colors = {
        '科考安全': '#1565C0',
        '技术攻关': '#7c3aed',
        '航道保障': '#ea580c',
        '外交参与': '#16a34a'
    }

    items = strategy['items']
    col1, col2 = st.columns(2)
    for i, (area, advice) in enumerate(items):
        color = area_colors.get(area, '#757575')
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div style="background:#f8fafc;border-radius:12px;padding:16px;margin-bottom:12px;
                        border-left:4px solid {color};box-shadow:0 1px 4px rgba(0,0,0,0.04);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    <span style="background:{color}22;color:{color};padding:3px 10px;
                               border-radius:8px;font-size:0.75rem;font-weight:600;">{area}</span>
                </div>
                <p style="font-size:0.88rem;color:#475569;margin:0;line-height:1.6;">{advice}</p>
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------------------
# Tab 4: 风险详情
# -------------------------------------------------------------------------
with tab4:
    st.markdown('<div class="section-title">📋 风险详情总表</div>', unsafe_allow_html=True)

    display_df = risk_df[['region', 'lat', 'lon', 'belong', 'category', 'risk_level', 'trend', 'main_factors']].rename(
        columns={'region': '海域', 'lat': '纬度', 'lon': '经度', 'belong': '所属区域',
                'category': '风险类别', 'risk_level': '风险等级', 'trend': '趋势', 'main_factors': '主要因素'}
    ).sort_values('风险等级', ascending=False)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 风险来源
    st.markdown("#### 主要风险来源")
    factor_counts = risk_df['main_factors'].value_counts()
    import plotly.graph_objects as go
    fig_factors = go.Figure(go.Bar(
        x=factor_counts.values, y=factor_counts.index,
        orientation='h',
        marker_color='#dc2626',
        hovertemplate='%{y}: %{x}个区域<extra></extra>'
    ))
    fig_factors.update_layout(
        xaxis_title='涉及区域数', yaxis_title='风险来源',
        height=300, margin=dict(l=160, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_factors, use_container_width=True)


# -------------------------------------------------------------------------
# Tab 5: 风险趋势
# -------------------------------------------------------------------------
with tab5:
    st.markdown('<div class="section-title">📈 风险趋势分析</div>', unsafe_allow_html=True)

    import plotly.graph_objects as go

    st.markdown("##### 风险趋势分布")
    trend_counts = risk_df['trend'].value_counts()
    fig_trend = go.Figure(go.Pie(
        labels=['上升', '稳定', '下降'],
        values=[trend_counts.get('上升', 0), trend_counts.get('稳定', 0), trend_counts.get('下降', 0)],
        hole=0.4,
        marker_colors=['#dc2626', '#f97316', '#16a34a'],
        textinfo='percent+label'
    ))
    fig_trend.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("##### 各风险类别平均等级")
    cat_avg = risk_df.groupby('category')['risk_level'].mean().sort_values(ascending=True)
    fig_cat = go.Figure(go.Bar(
        x=cat_avg.values, y=cat_avg.index,
        orientation='h',
        marker_color=['#dc2626' if v > 6 else '#f97316' if v > 4 else '#16a34a' for v in cat_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_cat.update_layout(
        xaxis_title='平均风险等级', yaxis_title='风险类别',
        height=280, margin=dict(l=120, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("##### 海域风险排名")
    region_avg = risk_df.groupby('region')['risk_level'].mean().sort_values(ascending=True)
    fig_rank = go.Figure(go.Bar(
        x=region_avg.values, y=region_avg.index,
        orientation='h',
        marker_color=['#dc2626' if v > 6 else '#f97316' if v > 4 else '#16a34a' for v in region_avg.values],
        hovertemplate='%{y}: 平均 %{x:.1f}<extra></extra>'
    ))
    fig_rank.update_layout(
        xaxis_title='综合风险等级', yaxis_title='海域',
        height=350, margin=dict(l=140, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_rank, use_container_width=True)


st.divider()
st.markdown("""
<div style="background:#fef3c7;padding:16px;border-radius:12px;border-left:4px solid #d97706;">
<b>⚠️ 风险评估说明：</b>本模块风险评估基于公开数据和专家判断综合得出，
用于学术研究参考，不构成任何政策建议。具体决策请咨询专业机构。
</div>
""", unsafe_allow_html=True)
st.caption("数据来源: 基于公开资料综合评估 · 风险模型参考相关学术文献")
