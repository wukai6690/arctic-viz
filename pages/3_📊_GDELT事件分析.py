"""
GDELT 事件分析页面
展示北极地缘政治事件的年度趋势、国家对比、类别分布和情感分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="GDELT 事件分析", page_icon="📊", layout="wide")

st.markdown("## 📊 GDELT 北极地缘事件分析")
st.markdown("数据来源: **GDELT 全球事件数据库** (http://data.gdeltproject.org) · 2018-2024")
st.divider()

# 加载数据
@st.cache_data
def load_data():
    grid_path = 'data/processed/gdelt_arctic_by_grid.csv'
    yc_path = 'data/processed/gdelt_arctic_by_year_country.csv'

    grid_df = pd.read_csv(grid_path) if os.path.exists(grid_path) else pd.DataFrame()
    yc_df = pd.read_csv(yc_path) if os.path.exists(yc_path) else pd.DataFrame()

    # 统一列名：优先 Year_local，回退 Year
    if not grid_df.empty:
        if 'Year_local' in grid_df.columns and 'Year' not in grid_df.columns:
            grid_df = grid_df.rename(columns={'Year_local': 'Year'})
        elif 'Year' in grid_df.columns and 'Year_local' not in grid_df.columns:
            grid_df['Year_local'] = grid_df['Year'].astype(str)
        elif 'Year' in grid_df.columns and 'Year_local' in grid_df.columns:
            pass
    if not yc_df.empty:
        if 'Year_local' in yc_df.columns and 'Year' not in yc_df.columns:
            yc_df = yc_df.rename(columns={'Year_local': 'Year'})
        elif 'Year' in yc_df.columns and 'Year_local' not in yc_df.columns:
            yc_df['Year_local'] = yc_df['Year'].astype(str)
        elif 'Year' in yc_df.columns and 'Year_local' in yc_df.columns:
            pass

    # 年份列统一为整数（用于图表）
    for df, name in [(grid_df, 'grid_df'), (yc_df, 'yc_df')]:
        if not df.empty:
            for col in ['Year', 'year']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    break

    if os.path.exists('data/processed/gdelt_arctic_sample.csv'):
        sample_df = pd.read_csv('data/processed/gdelt_arctic_sample.csv')
    else:
        sample_df = pd.DataFrame()

    return grid_df, yc_df, sample_df

grid_df, yc_df, sample_df = load_data()

# 数据状态检查
data_empty = grid_df.empty and yc_df.empty
if data_empty:
    st.warning("⚠️ 未找到 GDELT 数据文件，请先前往「数据爬取工具」页面生成样本数据或抓取 GDELT 数据。")
    st.page_link("pages/5_📥_数据爬取工具.py", label="👉 前往数据爬取工具", icon="📥")
    st.stop()

# 顶部概览指标
total_events = int(yc_df['EventCount'].sum()) if not yc_df.empty and 'EventCount' in yc_df.columns else 0
avg_tone = round(yc_df['AvgTone'].mean(), 2) if not yc_df.empty and 'AvgTone' in yc_df.columns else 0
country_group = yc_df.groupby('CountryCode')['EventCount'].sum() if not yc_df.empty and 'CountryCode' in yc_df.columns else pd.Series()
top_country = country_group.idxmax() if not country_group.empty else 'N/A'
cat_group = grid_df.groupby('EventCategory')['EventCount'].sum() if not grid_df.empty and 'EventCategory' in grid_df.columns else pd.Series()
top_category = cat_group.idxmax() if not cat_group.empty else 'N/A'

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("GDELT 北极事件总数", f"{total_events:,}", delta="2018-2024 累计")
with kpi_cols[1]:
    tone_label = "偏正面" if avg_tone > 0 else "偏负面" if avg_tone < 0 else "中性"
    st.metric("平均情感倾向", f"{avg_tone:.2f}", delta=tone_label)
with kpi_cols[2]:
    st.metric("事件最多国家", top_country, delta="GDELT 国家代码")
with kpi_cols[3]:
    cat_display = top_category.replace('arctic_', '') if isinstance(top_category, str) else str(top_category)
    st.metric("最活跃事件类别", cat_display, delta="事件类型")

st.divider()

# 主图表区域
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 年度趋势", "🌐 国家对比", "📂 类别分布", "🎭 情感分析"
])

# 国家中文名映射
COUNTRY_NAMES = {
    'RUS': '俄罗斯', 'CHN': '中国', 'USA': '美国', 'NOR': '挪威',
    'CAN': '加拿大', 'DNK': '丹麦', 'FIN': '芬兰', 'SWE': '瑞典',
    'ISL': '冰岛', 'JPN': '日本', 'KOR': '韩国'
}
COUNTRY_COLORS = {
    'RUS': '#E53935', 'CHN': '#FF0000', 'USA': '#1565C0', 'NOR': '#FF6B35',
    'CAN': '#43A047', 'DNK': '#FFA726', 'FIN': '#9C27B0', 'SWE': '#00BCD4',
    'ISL': '#795548', 'JPN': '#FFFFFF', 'KOR': '#1E88E5'
}

with tab1:
    st.markdown("### 📅 年度事件数量趋势")

    if not yc_df.empty and 'CountryCode' in yc_df.columns and 'Year' in yc_df.columns:
        fig1 = go.Figure()

        countries_in_data = yc_df['CountryCode'].unique()
        for country in sorted(countries_in_data):
            c_df = yc_df[yc_df['CountryCode'] == country]
            color = COUNTRY_COLORS.get(country, '#757575')
            name = COUNTRY_NAMES.get(country, country)

            fig1.add_trace(go.Bar(
                x=c_df['Year'].values,
                y=c_df['EventCount'].values,
                name=name,
                marker_color=color,
                hovertemplate=name + ' %{x}: %{y} 事件<extra></extra>'
            ))

        fig1.update_layout(
            barmode='group',
            xaxis_title='年份',
            yaxis_title='事件数量',
            template='plotly_white',
            height=420,
            legend=dict(orientation='h', yanchor='bottom', y=1.08, xanchor='center', x=0.5),
            margin=dict(l=60, r=20, t=20, b=60)
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig1b = go.Figure()
        yearly_total = yc_df.groupby('Year')['EventCount'].sum()
        fig1b.add_trace(go.Scatter(
            x=yearly_total.index.values,
            y=yearly_total.values,
            mode='lines+markers+text',
            name='年度总事件数',
            line=dict(color='#1E88E5', width=3),
            text=yearly_total.values,
            textposition='top center',
            hovertemplate='%{x}年: %{y} 事件<extra></extra>'
        ))
        fig1b.update_layout(
            xaxis_title='年份',
            yaxis_title='事件总数',
            template='plotly_white',
            height=320,
            showlegend=False,
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig1b, use_container_width=True)

        st.markdown("""
        **趋势解读：** 2018-2024年间，北极相关 GDELT 事件总数呈持续上升趋势。
        俄罗斯（RUS）事件数量始终领先，体现其在北极地区的主导性存在；
        中国（CHN）事件数量增长显著，反映北极战略参与程度的提升；
        2022年后美国（USA）事件数量激增，与北极军事化加速相吻合。
        """)
    else:
        st.info("暂无年度-国家数据，请先在「数据爬取工具」页面生成样本数据。")


with tab2:
    st.markdown("### 🌐 国家维度分析")

    if not yc_df.empty and 'CountryCode' in yc_df.columns:
        country_totals = yc_df.groupby('CountryCode')['EventCount'].sum().sort_values(ascending=True)
        sorted_codes = country_totals.index.tolist()

        fig2a = go.Figure(go.Bar(
            x=country_totals.values,
            y=[f"{COUNTRY_NAMES.get(c, c)} ({c})" for c in sorted_codes],
            orientation='h',
            marker_color=[COUNTRY_COLORS.get(c, '#757575') for c in sorted_codes],
            hovertemplate='%{y}: %{x} 事件<extra></extra>'
        ))
        fig2a.update_layout(
            xaxis_title='事件总数',
            yaxis_title='国家',
            template='plotly_white',
            height=max(350, len(country_totals) * 50),
            margin=dict(l=100, r=20, t=20, b=40)
        )
        st.plotly_chart(fig2a, use_container_width=True)

        major_countries = ['RUS', 'CHN', 'USA']
        available_countries = [c for c in major_countries if c in yc_df['CountryCode'].values]

        if available_countries:
            fig2b = go.Figure()
            for country in available_countries:
                c_df = yc_df[yc_df['CountryCode'] == country].sort_values('Year')
                fig2b.add_trace(go.Scatter(
                    x=c_df['Year'].values,
                    y=c_df['EventCount'].values,
                    mode='lines+markers',
                    name=COUNTRY_NAMES.get(country, country),
                    line=dict(color=COUNTRY_COLORS.get(country, '#757575'), width=2.5),
                    hovertemplate=COUNTRY_NAMES.get(country, country) + ': %{y} 事件<extra></extra>'
                ))
            fig2b.update_layout(
                xaxis_title='年份',
                yaxis_title='事件数量',
                template='plotly_white',
                height=380,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=60, r=20, t=20, b=40)
            )
            st.plotly_chart(fig2b, use_container_width=True)

        st.markdown("""
        **国家格局解读：**
        - **俄罗斯**：北极事件绝对主体，涵盖航道管理、资源开发、军事部署全方位活动
        - **中国**：近五年增长近 4 倍，主要集中在航道合作、能源投资和科技合作领域
        - **美国**：2022年后事件激增，主要反映北极理事会功能受阻背景下的军事和外交活动
        """)
    else:
        st.info("暂无国家数据，请先在「数据爬取工具」页面生成样本数据。")


with tab3:
    st.markdown("### 📂 事件类别分布")

    if not grid_df.empty and 'EventCategory' in grid_df.columns:
        cat_totals = grid_df.groupby('EventCategory')['EventCount'].sum().sort_values(ascending=False)

        CAT_LABELS = {
            'arctic_resource': '北极资源开发',
            'arctic_military': '军事活动',
            'arctic_shipping': '航道航运',
            'arctic_research': '科研活动',
            'arctic_infrastructure': '基础设施',
            'arctic_technology': '技术竞争',
            'arctic_cooperation': '科技合作',
            'arctic_general': '一般事件',
            'arctic_governance': '治理规则'
        }
        CAT_COLORS = {
            'arctic_resource': '#FDD835',
            'arctic_military': '#8E24AA',
            'arctic_shipping': '#FF6B35',
            'arctic_research': '#1E88E5',
            'arctic_infrastructure': '#00BCD4',
            'arctic_technology': '#E53935',
            'arctic_cooperation': '#43A047',
            'arctic_general': '#757575',
            'arctic_governance': '#6D4C41'
        }

        fig3a = go.Figure()
        fig3a.add_trace(go.Pie(
            labels=[CAT_LABELS.get(c, c) for c in cat_totals.index],
            values=cat_totals.values,
            marker_colors=[CAT_COLORS.get(c, '#757575') for c in cat_totals.index],
            textinfo='percent+label',
            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
        ))
        fig3a.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig3a, use_container_width=True)

        year_col = 'Year' if 'Year' in grid_df.columns else 'Year_local'
        if year_col in grid_df.columns:
            fig3b = go.Figure()
            for cat in cat_totals.index:
                cat_df = grid_df[grid_df['EventCategory'] == cat]
                yearly = cat_df.groupby(year_col)['EventCount'].sum()
                fig3b.add_trace(go.Bar(
                    x=yearly.index.values,
                    y=yearly.values,
                    name=CAT_LABELS.get(cat, cat),
                    marker_color=CAT_COLORS.get(cat, '#757575'),
                    hovertemplate=f'{CAT_LABELS.get(cat, cat)}: %{{x}}年 %{{y}} 事件<extra></extra>'
                ))

            fig3b.update_layout(
                barmode='group',
                xaxis_title='年份',
                yaxis_title='事件数量',
                template='plotly_white',
                height=400,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
                           font=dict(size=10)),
                margin=dict(l=60, r=20, t=60, b=60)
            )
            st.plotly_chart(fig3b, use_container_width=True)

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("#### 类别热度排名")
            for i, (cat, count) in enumerate(cat_totals.items(), 1):
                pct = count / cat_totals.sum() * 100
                bar_len = pct * 5
                color = CAT_COLORS.get(cat, '#757575')
                st.markdown(
                    f"<div style='margin:3px 0'>"
                    f"<span style='width:30px;display:inline-block'>{i}.</span>"
                    f"<span style='width:130px;display:inline-block'>{CAT_LABELS.get(cat, cat)}</span>"
                    f"<span style='display:inline-block;width:{bar_len}px;background:{color};height:14px;border-radius:3px;'></span>"
                    f"<span style='margin-left:6px;font-size:0.8rem'>{pct:.1f}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        with col_right:
            st.markdown("#### 技术竞争重点领域")
            st.markdown("""
            **高端船舶制造：**
            - 破冰型 LNG 运输船建造
            - 核动力破冰船自主研发
            - 极地货船船队扩张

            **极地通信卫星：**
            - 极地轨道通信卫星部署
            - 北极导航增强系统
            - 卫星数据传输网络
            """)
    else:
        st.info("暂无类别数据，请先在「数据爬取工具」页面生成样本数据。")


with tab4:
    st.markdown("### 🎭 情感分析 (AvgTone)")

    if not yc_df.empty and 'AvgTone' in yc_df.columns:
        fig4a = go.Figure()
        major_countries = ['RUS', 'CHN', 'USA', 'NOR', 'CAN']
        available = [c for c in major_countries if c in yc_df['CountryCode'].values]

        for country in available:
            c_df = yc_df[yc_df['CountryCode'] == country].sort_values('Year')
            if not c_df.empty:
                fig4a.add_trace(go.Scatter(
                    x=c_df['Year'].values,
                    y=c_df['AvgTone'].values,
                    mode='lines+markers',
                    name=COUNTRY_NAMES.get(country, country),
                    line=dict(color=COUNTRY_COLORS.get(country, '#757575'), width=2),
                    hovertemplate=f'{COUNTRY_NAMES.get(country)}: %{{y:.2f}}<extra></extra>'
                ))

        fig4a.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="中性线")
        fig4a.update_layout(
            xaxis_title='年份',
            yaxis_title='平均情感倾向值',
            template='plotly_white',
            height=400,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig4a, use_container_width=True)

        if not grid_df.empty and 'EventCategory' in grid_df.columns and 'AvgTone' in grid_df.columns:
            tone_cat = grid_df.groupby('EventCategory')['AvgTone'].mean().sort_values()
            fig4b = go.Figure()
            fig4b.add_trace(go.Bar(
                y=[CAT_LABELS.get(c, c) for c in tone_cat.index],
                x=tone_cat.values,
                orientation='h',
                marker_color=['#E53935' if v < -1 else '#FDD835' if v < 0.5
                              else '#43A047' for v in tone_cat.values],
                hovertemplate='%{y}: %{x:.2f}<extra></extra>'
            ))
            fig4b.add_vline(x=0, line_dash="dash", line_color="gray")
            fig4b.update_layout(
                xaxis_title='平均情感值',
                yaxis_title='事件类别',
                template='plotly_white',
                height=350,
                margin=dict(l=130, r=20, t=20, b=40)
            )
            st.plotly_chart(fig4b, use_container_width=True)

        st.markdown("""
        **情感分析解读：**
        - **正值（绿色）**：通常表示合作、协议、援助等正面事件
        - **负值（红色）**：通常表示冲突、对抗、制裁等负面事件

        军事活动（arctic_military）平均情感值显著偏低，符合预期。
        科技合作（arctic_cooperation）呈正面倾向，体现了科技外交的缓冲作用。
        中国的情感均值持续为正，反映合作类事件占比较高。
        """)
    else:
        st.info("暂无情感数据，请先在「数据爬取工具」页面生成样本数据。")

st.divider()
st.caption("数据来源: GDELT 全球事件数据库 · http://data.gdeltproject.org")
st.caption("情感值 (AvgTone): -100(极度负面) ~ +100(极度正面)，基于新闻报道语调计算")
