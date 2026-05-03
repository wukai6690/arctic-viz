"""
模块5：中国北极安全风险评估与策略参考
风险热力图 + SWOT分析 + 中国应对策略推演
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_risk_data, get_swot_data, load_stations
from src.viz import COUNTRY_NAMES, COUNTRY_COLORS, create_risk_matrix, create_swot_chart

st.set_page_config(page_title="中国安全风险", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .page-header { background: linear-gradient(135deg, #C62828 0%, #E53935 100%);
        padding: 1.2rem 1.5rem; border-radius: 0 0 14px 14px; margin-bottom: 1.5rem; }
    .page-header h1 { color: white; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .page-header p { color: rgba(255,255,255,0.85); font-size: 0.85rem; margin: 0.3rem 0 0 0; }
    .risk-low { background:#E8F5E9;border:1px solid #A5D6A7;border-radius:8px;padding:0.8rem;text-align:center; }
    .risk-medium { background:#FFF3E0;border:1px solid #FFCC80;border-radius:8px;padding:0.8rem;text-align:center; }
    .risk-high { background:#FFEBEE;border:1px solid #EF9A9A;border-radius:8px;padding:0.8rem;text-align:center; }
</style>
<div class="page-header">
    <h1>🛡️ 中国北极安全风险评估与策略参考模块</h1>
    <p>四维风险矩阵 · SWOT分析 · 中国应对策略推演沙盘</p>
</div>
""", unsafe_allow_html=True)

# 加载数据
risk_df = load_risk_data()
swot_data = get_swot_data()
stations_data = load_stations()

# ============ KPI ============
kpi_cols = st.columns(4)
avg_risk = risk_df['risk_level'].mean()
high_risk_count = (risk_df['risk_level'] >= 7).sum()
max_risk = risk_df['risk_level'].max()
max_risk_region = risk_df[risk_df['risk_level'] == max_risk]['region'].values[0] if max_risk > 0 else 'N/A'

with kpi_cols[0]:
    st.metric("平均风险等级", f"{avg_risk:.1f}/10", delta="综合评级")
with kpi_cols[1]:
    st.metric("高风险区域数", f"{high_risk_count}", delta="7级以上")
with kpi_cols[2]:
    st.metric("最高风险", f"{max_risk}/10", delta=max_risk_region)
with kpi_cols[3]:
    st.metric("覆盖海域", "10个", delta="主要北极海域")

st.divider()

# ============ 主区域 ============
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ 四维风险热力图", "📊 SWOT分析", "🧩 应对策略推演", "📋 风险详情"
])

with tab1:
    st.markdown("### 🗺️ 北极航行与介入风险热力图")
    st.caption("颜色越深（红）= 风险等级越高 | 点击单元格查看风险来源和影响因素")

    # 风险类别筛选
    risk_cat = st.selectbox("选择风险类别", ['全部', '航道通行', '科考安全', '技术壁垒', '权益冲突'])

    import plotly.graph_objects as go

    if risk_cat == '全部':
        pivot = risk_df.pivot_table(values='risk_level', index='region', columns='category', aggfunc='mean')
    else:
        pivot = risk_df[risk_df['category'] == risk_cat].pivot_table(
            values='risk_level', index='region', columns='category', aggfunc='mean')

    colorscale = [[0,'#43A047'],[0.3,'#FDD835'],[0.6,'#FF9800'],[1,'#E53935']]

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns if risk_cat == '全部' else [risk_cat],
        y=pivot.index,
        colorscale=colorscale, zmin=1, zmax=10,
        colorbar=dict(title='风险等级', tickvals=[1,3,5,7,10],
                     ticktext=['1低','3','5中','7','10高']),
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>',
        text=pivot.values, texttemplate='%{z:.0f}', textfont=dict(color='white', size=14)
    ))
    fig_heat.update_layout(
        margin=dict(l=140, r=40, t=40, b=60),
        height=max(400, len(pivot) * 45),
        xaxis_title='', yaxis_title=''
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # 图例说明
    st.markdown("""
    **风险等级说明：**
    """)
    legend_cols = st.columns(5)
    with legend_cols[0]:
        st.markdown("<div class='risk-low'><div style='font-size:1.2rem'>1-3</div><div style='font-size:0.7rem;color:#2E7D32'>低风险</div></div>", unsafe_allow_html=True)
    with legend_cols[1]:
        st.markdown("<div class='risk-medium'><div style='font-size:1.2rem'>4-5</div><div style='font-size:0.7rem;color:#E65100'>中风险</div></div>", unsafe_allow_html=True)
    with legend_cols[2]:
        st.markdown("<div class='risk-high'><div style='font-size:1.2rem'>6-7</div><div style='font-size:0.7rem;color:#C62828'>较高风险</div></div>", unsafe_allow_html=True)
    with legend_cols[3]:
        st.markdown("<div style='background:#FFCDD2;border:1px solid #EF9A9A;border-radius:8px;padding:0.8rem;text-align:center;'><div style='font-size:1.2rem'>8-9</div><div style='font-size:0.7rem;color:#B71C1C'>高风险</div></div>", unsafe_allow_html=True)
    with legend_cols[4]:
        st.markdown("<div style='background:#B71C1C;border:1px solid #7f0000;border-radius:8px;padding:0.8rem;text-align:center;'><div style='font-size:1.2rem'>10</div><div style='font-size:0.7rem;color:white'>极高风险</div></div>", unsafe_allow_html=True)

    # 分区域风险分析
    st.markdown("#### 分区域风险深度分析")
    region_select = st.selectbox("选择海域", risk_df['region'].unique())

    region_data = risk_df[risk_df['region'] == region_select]
    rc_cols = st.columns(len(region_data))
    for i, (_, row) in enumerate(region_data.iterrows()):
        level = row['risk_level']
        color = '#43A047' if level < 4 else '#FF9800' if level < 7 else '#E53935'
        with rc_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:0.8rem;background:white;border-radius:12px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);border-top:3px solid {color};">
                <div style="font-size:1.5rem;font-weight:800;color:{color};">{int(level)}</div>
                <div style="font-size:0.7rem;color:#546E7A;">{row['category']}</div>
                <div style="font-size:0.65rem;color:#90A4AE;margin-top:4px">{row['main_factors']}</div>
                <div style="font-size:0.65rem;color:{'#43A047' if row['trend']=='下降' else '#FF6B35' if row['trend']=='稳定' else '#E53935'};margin-top:2px">
                    {'↓' if row['trend']=='下降' else '→' if row['trend']=='稳定' else '↑'} {row['trend']}
                </div>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 📊 中国北极战略 SWOT 分析")

    # SWOT 图表
    fig_swot = create_swot_chart(swot_data)
    st.plotly_chart(fig_swot, use_container_width=True)

    # 详细解读
    st.markdown("#### SWOT 详细解读")

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("""
        <div style="border-left:4px solid #43A047;padding-left:12px;margin-bottom:1rem;">
            <b style="color:#43A047;font-size:1rem">优势 S</b>
            <ul style="font-size:0.82rem;color:#546E7A;line-height:1.8;margin-top:6px">
                <li><b>科研实力：</b>极地科考体系完善，『雪龙2』全年候航行能力</li>
                <li><b>资本优势：</b>北极能源项目投资规模领先</li>
                <li><b>技术进步：</b>极地LNG船、破冰船建造技术快速追赶</li>
                <li><b>战略视野：</b>『人类命运共同体』理念提供独特治理观</li>
            </ul>
        </div>
        <div style="border-left:4px solid #E53935;padding-left:12px;margin-bottom:1rem;">
            <b style="color:#E53935;font-size:1rem">劣势 W</b>
            <ul style="font-size:0.82rem;color:#546E7A;line-height:1.8;margin-top:6px">
                <li><b>距离劣势：</b>非北极国家，距北极核心区数千公里</li>
                <li><b>制度缺失：</b>缺乏北极治理机制正式成员资格</li>
                <li><b>技术差距：</b>核动力破冰船等领域仍有差距</li>
                <li><b>经验不足：</b>北极航道商业运营经验积累时间较短</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with detail_cols[1]:
        st.markdown("""
        <div style="border-left:4px solid #1E88E5;padding-left:12px;margin-bottom:1rem;">
            <b style="color:#1E88E5;font-size:1rem">机会 O</b>
            <ul style="font-size:0.82rem;color:#546E7A;line-height:1.8;margin-top:6px">
                <li><b>航道价值：</b>气候变化加速航道通航窗口扩大</li>
                <li><b>合作空间：</b>科技合作仍是大国关系『压舱石』</li>
                <li><b>规则制定：</b>北极治理规则重构期为中国参与提供窗口</li>
                <li><b>能源需求：</b>北极油气资源满足进口多元化需求</li>
            </ul>
        </div>
        <div style="border-left:4px solid #FF6B35;padding-left:12px;margin-bottom:1rem;">
            <b style="color:#FF6B35;font-size:1rem">威胁 T</b>
            <ul style="font-size:0.82rem;color:#546E7A;line-height:1.8;margin-top:6px">
                <li><b>大国对抗：</b>中美博弈向北极延伸，技术脱钩风险上升</li>
                <li><b>航道控制：</b>俄罗斯强化东北航道管辖限制</li>
                <li><b>环境约束：</b>国际环保压力限制资源开发空间</li>
                <li><b>理事受阻：</b>北极理事会功能受损，多边机制弱化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🧩 中国应对策略推演沙盘")
    st.markdown("选择风险情景，获取智能生成的对策建议")

    # 情景选择
    scenario = st.selectbox("选择风险情景", [
        "正常运营情景",
        "航道封锁情景",
        "多边机制停摆情景",
        "大国军事对峙升级情景",
        "极端气候灾害情景"
    ])

    strategies = {
        "正常运营情景": {
            "title": "常规推进策略",
            "color": "#43A047",
            "items": [
                ("科考安全", "深化极地科考合作，扩大『雪龙2』航线覆盖范围，与北欧国家共享科考数据"),
                ("技术攻关", "加快核动力破冰船国产化论证，推进极地通信卫星星座规划"),
                ("航道保障", "深化与俄罗斯能源合作，确保『冰上丝绸之路』物流畅通"),
                ("外交参与", "积极争取北极理事会正式观察员地位，提升制度性话语权"),
            ]
        },
        "航道封锁情景": {
            "title": "多元通道策略",
            "color": "#FF6B35",
            "items": [
                ("科考安全", "加强国内极地模拟训练能力建设，减少对单一海域依赖"),
                ("技术攻关", "突破极地无人航行技术，发展自主导航与应急通信能力"),
                ("航道保障", "开拓西北航道替代方案，加强与加拿大的沟通协调"),
                ("外交参与", "通过『一带一路』多边平台争取航道通行权益国际法支持"),
            ]
        },
        "多边机制停摆情景": {
            "title": "双边替代策略",
            "color": "#1565C0",
            "items": [
                ("科考安全", "通过双边科考协议替代多边框架，确保科研连续性"),
                ("技术攻关", "加大自主技术研发投入，降低外部技术依赖"),
                ("航道保障", "探索与域内国家签署双边航道合作协议的可能性"),
                ("外交参与", "利用上海合作组织等平台，构建替代性合作框架"),
            ]
        },
        "大国军事对峙升级情景": {
            "title": "风险管控策略",
            "color": "#E53935",
            "items": [
                ("科考安全", "暂时回避敏感区域科考，优先保障人员安全"),
                ("技术攻关", "加速极地军民两用技术自主化，降低『卡脖子』风险"),
                ("航道保障", "暂停高风险航段商业运营，等待局势缓和"),
                ("外交参与", "通过非官方渠道传递缓和信号，避免直接对抗"),
            ]
        },
        "极端气候灾害情景": {
            "title": "应急响应策略",
            "color": "#7B1FA2",
            "items": [
                ("科考安全", "建立极地气象预警联动机制，提升应急响应速度"),
                ("技术攻关", "发展极端环境作业装备，提升船舶抗风险能力"),
                ("航道保障", "制定极端气候应急预案，建立航运保险机制"),
                ("外交参与", "推动建立北极气候灾害联合应对机制"),
            ]
        }
    }

    s = strategies[scenario]
    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:1.2rem;
                border-left:5px solid {s['color']};margin-bottom:1rem;
                box-shadow:0 2px 12px rgba(0,0,0,0.06);">
        <h3 style="color:{s['color']};margin:0 0 0.5rem 0">{s['title']}</h3>
    </div>
    """, unsafe_allow_html=True)

    for area, advice in s['items']:
        area_colors = {'科考安全': '#1E88E5', '技术攻关': '#7B1FA2', '航道保障': '#FF6B35', '外交参与': '#43A047'}
        st.markdown(f"""
        <div style="background:#FAFAFA;border-radius:12px;padding:1rem;margin:0.5rem 0;
                    border-left:3px solid {area_colors.get(area, '#757575')};">
            <b style="color:{area_colors.get(area, '#757575')};">{area}</b>
            <p style="font-size:0.88rem;color:#546E7A;margin:0.4rem 0 0 0;line-height:1.6">{advice}</p>
        </div>
        """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📋 风险详情总表")

    # 完整风险表
    st.dataframe(
        risk_df[['region', 'lat', 'lon', 'category', 'risk_level', 'trend', 'main_factors']].rename(
            columns={'region': '海域', 'lat': '纬度', 'lon': '经度', 'category': '风险类别',
                    'risk_level': '风险等级', 'trend': '趋势', 'main_factors': '主要因素'}
        ).sort_values('风险等级', ascending=False),
        use_container_width=True, hide_index=True
    )

    # 风险来源分析
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
        height=300, margin=dict(l=160, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_factors, use_container_width=True)

    # 趋势分析
    st.markdown("#### 风险趋势分布")
    trend_counts = risk_df['trend'].value_counts()
    fig_trend = go.Figure(go.Pie(
        labels=['上升', '稳定', '下降'],
        values=[trend_counts.get('上升', 0), trend_counts.get('稳定', 0), trend_counts.get('下降', 0)],
        hole=0.4,
        marker_colors=['#E53935', '#FF9800', '#43A047'],
        textinfo='percent+label'
    ))
    fig_trend.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()
st.markdown("""
<div style="background:#FFF8E1;padding:1rem;border-radius:12px;border-left:4px solid #FF6F00;">
<b>⚠️ 风险评估说明：</b>本模块风险评估基于公开数据和专家判断综合得出，
用于学术研究参考，不构成任何政策建议。具体决策请咨询专业机构。
风险等级会受到国际形势变化影响，本平台将持续更新数据。
</div>
""", unsafe_allow_html=True)

st.caption("数据来源: 基于公开资料综合评估 · 风险模型参考相关学术文献")
