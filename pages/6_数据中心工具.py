"""
模块6：数据中心与工具模块
数据集下载、上传数据可视化、时空查询与对比分析
增强版：更丰富的可视化类型、Excel支持、多源对比
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_ice_data, load_gdelt_data, load_patent_data, load_risk_data, get_downloadable_datasets

st.set_page_config(page_title="数据中心", page_icon="🗄️", layout="wide")

st.markdown("""
<style>
    .page-header { background: linear-gradient(135deg, #00695C 0%, #00897B 100%);
        padding: 1.2rem 1.5rem; border-radius: 0 0 14px 14px; margin-bottom: 1.5rem; }
    .page-header h1 { color: white !important; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .page-header p { color: rgba(255,255,255,0.85) !important; font-size: 0.85rem; margin: 0.3rem 0 0 0; }
    .download-card { background:white;border-radius:12px;padding:1rem;
                    box-shadow:0 2px 8px rgba(0,0,0,0.06);margin:0.3rem 0; }
    /* 确保主内容区白色背景，文字深色 */
    section[data-testid="stMain"] > div { background: white !important; }
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li, section[data-testid="stMain"] span { color: #1a1a2e !important; }
    .stMarkdown p, .stMarkdown li { color: #1a1a2e !important; }
    .stTabs [data-baseweb="tab"] { color: #333 !important; }
</style>
<div class="page-header">
    <h1>🗄️ 数据中心与工具模块</h1>
    <p>数据集下载 · 上传数据可视化 · 时空查询 · 对比分析</p>
</div>
""", unsafe_allow_html=True)

# ============ 主区域 ============
tab1, tab2, tab3, tab4 = st.tabs([
    "📥 数据集下载", "📤 数据上传工具", "🔍 时空查询", "📊 数据对比分析"
])

with tab1:
    st.markdown("### 📥 平台数据集下载")

    st.markdown("""
    本平台提供以下可供下载的数据集（CSV/GeoJSON 格式），所有数据均经过清洗和聚合处理，
    可直接用于学术研究和二次分析。
    """)

    datasets = get_downloadable_datasets()

    for ds in datasets:
        col_info, col_dl = st.columns([4, 1])
        with col_info:
            st.markdown(f"""
            <div class="download-card">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.3rem;">
                    <span style="background:#E3F2FD;color:#1565C0;padding:2px 8px;border-radius:8px;font-size:0.75rem;">{ds['format']}</span>
                    <span style="font-weight:700;font-size:0.95rem;">{ds['name']}</span>
                </div>
                <div style="font-size:0.8rem;color:#546E7A;margin-bottom:0.3rem;">{ds['desc']}</div>
                <div style="font-size:0.72rem;color:#90A4AE;">
                    行数: {ds['rows']} · 大小: {ds['size']} · 来源: {ds['source']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_dl:
            file_path = os.path.join('data', 'processed', ds['file'])
            geo_dir = os.path.join('geojson', ds['file'])
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    st.download_button(
                        "下载", f.read(),
                        file_name=ds['file'],
                        mime='text/csv',
                        use_container_width=True
                    )
            elif os.path.exists(geo_dir):
                with open(geo_dir, 'rb') as f:
                    st.download_button(
                        "下载", f.read(),
                        file_name=ds['file'],
                        mime='application/json',
                        use_container_width=True
                    )
            else:
                st.button("暂无", disabled=True, use_container_width=True)

with tab2:
    st.markdown("### 📤 上传数据可视化工具")
    st.markdown("上传您的 CSV 数据文件，自动生成可视化图表。")

    uploaded = st.file_uploader(
        "选择 CSV 文件",
        type=['csv'],
        help="支持标准的带表头 CSV 文件"
    )

    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.success(f"成功加载 {uploaded.name}，共 {len(df)} 行 × {len(df.columns)} 列")

            # 预览
            with st.expander("📋 数据预览（前10行）"):
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            # 基本信息
            info_cols = st.columns(3)
            with info_cols[0]:
                st.metric("数据行数", len(df))
            with info_cols[1]:
                st.metric("数据列数", len(df.columns))
            with info_cols[2]:
                st.metric("缺失值", df.isnull().sum().sum())

            # 列类型
            st.markdown("#### 列信息")
            col_info_df = pd.DataFrame({
                '列名': df.columns,
                '类型': [str(dtype) for dtype in df.dtypes],
                '非空数': [df[c].notna().sum() for c in df.columns],
                '示例值': [str(df[c].iloc[0]) if len(df) > 0 else '' for c in df.columns]
            })
            st.dataframe(col_info_df, use_container_width=True, hide_index=True)

            # 可视化选择
            st.markdown("#### 生成可视化")
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            all_cols = df.columns.tolist()

            if numeric_cols:
                chart_type = st.selectbox("图表类型", ["折线图", "柱状图", "散点图", "热力图", "面积图"])
                viz_cols = st.columns(2)
                with viz_cols[0]:
                    x_col = st.selectbox("X轴（列）", all_cols, index=0)
                with viz_cols[1]:
                    y_col = st.selectbox("Y轴（数值列）", numeric_cols if numeric_cols else all_cols)

                import plotly.graph_objects as go

                if chart_type == "折线图":
                    fig = go.Figure(go.Scatter(
                        x=df[x_col], y=df[y_col],
                        mode='lines+markers',
                        line=dict(color='#1E88E5', width=2),
                        marker=dict(size=5),
                        hovertemplate=f'%{{x}}: %{{y:.2f}}<extra></extra>'
                    ))
                    fig.update_layout(
                        xaxis_title=x_col, yaxis_title=y_col,
                        template='plotly_white', height=400,
                        margin=dict(l=60, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "柱状图":
                    fig = go.Figure(go.Bar(
                        x=df[x_col], y=df[y_col],
                        marker_color='#1E88E5',
                        hovertemplate=f'%{{x}}: %{{y:.2f}}<extra></extra>'
                    ))
                    fig.update_layout(
                        xaxis_title=x_col, yaxis_title=y_col,
                        template='plotly_white', height=400,
                        margin=dict(l=60, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "散点图":
                    color_col = st.selectbox("颜色分组（可选）", [None] + all_cols)
                    if color_col:
                        import plotly.express as px
                        fig = px.scatter(df, x=x_col, y=y_col, color=color_col)
                    else:
                        fig = go.Figure(go.Scatter(
                            x=df[x_col], y=df[y_col], mode='markers',
                            marker=dict(size=8, color='#1E88E5')
                        ))
                    fig.update_layout(template='plotly_white', height=400,
                                    margin=dict(l=60, r=20, t=20, b=40))
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "面积图":
                    fig = go.Figure(go.Scatter(
                        x=df[x_col], y=df[y_col],
                        mode='lines', fill='tozeroy',
                        line=dict(color='#1E88E5', width=2),
                        fillcolor='rgba(30,136,229,0.2)'
                    ))
                    fig.update_layout(
                        xaxis_title=x_col, yaxis_title=y_col,
                        template='plotly_white', height=400,
                        margin=dict(l=60, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:  # 热力图
                    numeric_df = df[numeric_cols].head(30)
                    fig = go.Figure(data=go.Heatmap(
                        z=numeric_df.values,
                        x=numeric_df.columns,
                        y=numeric_df.index,
                        colorscale='Blues'
                    ))
                    fig.update_layout(height=400, margin=dict(l=60, r=20, t=20, b=40))
                    st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("未检测到数值列，请上传包含数值数据的 CSV 文件。")

        except Exception as e:
            st.error(f"加载文件失败: {e}")
    else:
        st.info("请上传一个 CSV 文件开始分析。推荐格式：带表头的 UTF-8 编码 CSV")

        with st.expander("📝 CSV 模板示例"):
            st.code("""年份,海冰面积,平均气温,航道事件数\n2020,10.5,1.2,125\n2021,9.8,1.5,138\n2022,9.2,1.8,152\n2023,8.9,2.0,165\n2024,8.5,2.3,178""", language="csv")

with tab3:
    st.markdown("### 🔍 时空查询工具")
    st.markdown("在海冰和 GDELT 数据中按时间和空间条件进行筛选查询。")

    # 海冰查询
    st.markdown("#### 🧊 海冰面积查询")
    ice_df, ice_summary, _ = load_ice_data()

    q_cols = st.columns(3)
    with q_cols[0]:
        query_year = st.number_input("查询年份", min_value=1979, max_value=2024, value=2020, key="q_yr")
    with q_cols[1]:
        query_month = st.selectbox("查询月份", ["全部"] + list(range(1, 13)),
                                   format_func=lambda x: "全部" if x == "全部" else f"{x}月",
                                   key="q_mo")
    with q_cols[2]:
        metric_type = st.selectbox("指标类型", ["年均值", "年最大", "年最小"], key="q_mt")

    if query_year in ice_summary.index:
        yr_data = ice_summary.loc[query_year]
        m_cols = st.columns(3)
        with m_cols[0]:
            st.metric("年均面积", f"{yr_data['mean']:.2f} M km²")
        with m_cols[1]:
            st.metric("年最大", f"{yr_data['maximum']:.2f} M km²")
        with m_cols[2]:
            st.metric("年最小", f"{yr_data['minimum']:.2f} M km²")

        if query_month != "全部":
            month_names = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
            if query_month - 1 < len(month_names):
                col_name = month_names[query_month - 1]
                if col_name in ice_df.columns:
                    val = ice_df.loc[query_year, col_name]
                    st.info(f"{query_year}年{query_month}月海冰面积: **{val:.2f} M km²**")

        # 时间范围对比
        st.markdown("#### 📊 与历史平均对比")
        compare_years = st.multiselect("对比年份", list(range(1979, 2025)),
                                      default=[query_year, 1990, 2000, 2010], key="comp_yr")
        if compare_years:
            comp_data = []
            for yr in compare_years:
                if yr in ice_summary.index:
                    comp_data.append({'年份': yr, '年均面积': ice_summary.loc[yr, 'mean']})
            comp_df = pd.DataFrame(comp_data)

            import plotly.graph_objects as go
            fig_comp = go.Figure(go.Bar(
                x=comp_df['年份'], y=comp_df['年均面积'],
                marker_color=['#E53935' if yr == query_year else '#1E88E5' for yr in comp_df['年份']],
                hovertemplate='%{x}年: %{y:.2f} M km²<extra></extra>'
            ))
            fig_comp.update_layout(
                xaxis_title='年份', yaxis_title='年均海冰面积 (M km²)',
                template='plotly_white', height=300,
                margin=dict(l=60, r=20, t=20, b=40)
            )
            st.plotly_chart(fig_comp, use_container_width=True)

    # GDELT 查询
    st.markdown("#### 🌍 GDELT 事件查询")
    grid_df, yc_df = load_gdelt_data()

    q2_cols = st.columns(3)
    with q2_cols[0]:
        q2_year = st.number_input("查询年份", min_value=2018, max_value=2024, value=2023, key="q2y")
    with q2_cols[1]:
        country_options = ["全部"] + (sorted(yc_df['CountryCode'].unique().tolist()) if not yc_df.empty else [])
        q2_country = st.selectbox("国家/地区", country_options,
                                 format_func=lambda x: x if x == "全部" else COUNTRY_NAMES.get(x, x),
                                 key="q2c")
    with q2_cols[2]:
        cat_options = ["全部"] + (list(yc_df['EventCategory'].unique()) if 'EventCategory' in yc_df.columns else [])
        q2_cat = st.selectbox("事件类型", cat_options, key="q2cat")

    if not yc_df.empty:
        q2_data = yc_df[yc_df['year'] == q2_year]
        if q2_country != "全部":
            q2_data = q2_data[q2_data['CountryCode'] == q2_country]
        if q2_cat != "全部" and 'EventCategory' in q2_data.columns:
            q2_data = q2_data[q2_data['EventCategory'] == q2_cat]

        if not q2_data.empty:
            total_events = q2_data['EventCount'].sum()
            avg_tone = q2_data['AvgTone'].mean()
            cc = st.columns(2)
            with cc[0]:
                st.metric(f"{q2_year}年事件总数", f"{total_events:,}")
            with cc[1]:
                st.metric(f"平均情感值", f"{avg_tone:.2f}",
                         delta="偏正面" if avg_tone > 0 else "偏负面")
        else:
            st.info(f"{q2_year}年在{' ' + q2_country if q2_country != '全部' else ''}暂无数据")
    else:
        st.info("GDELT 数据加载中...")

with tab4:
    st.markdown("### 📊 多源数据对比分析")

    st.markdown("""
    在同一图表中对比多个数据源的时间演变趋势。
    数据自动归一化到 0-100 范围，便于直观对比不同量纲的指标。
    """)

    compare_options = st.multiselect(
        "选择要对比的指标",
        ["海冰年均面积", "GDELT事件总数", "航道通航潜力", "专利申请量"],
        default=["海冰年均面积", "GDELT事件总数"]
    )

    if compare_options:
        _, ice_summary, _ = load_ice_data()
        _, yc_df = load_gdelt_data()
        patent_df = load_patent_data()

        years = list(range(2018, 2025))
        compare_data = {'year': years}

        if "海冰年均面积" in compare_options:
            ice_vals = [ice_summary.loc[y, 'mean'] if y in ice_summary.index else None for y in years]
            compare_data['海冰面积'] = ice_vals

        if "GDELT事件总数" in compare_options:
            gdelt_yearly = yc_df.groupby('year')['EventCount'].sum() if not yc_df.empty else pd.Series()
            compare_data['GDELT事件'] = [gdelt_yearly.get(y, 0) for y in years]

        if "航道通航潜力" in compare_options:
            ice_df, _, _ = load_ice_data()
            potential = [(15 - min(ice_df.loc[y, 'sep'], 15)) / 10 * 100
                        if y in ice_df.index else None for y in years]
            compare_data['通航潜力'] = potential

        if "专利申请量" in compare_options:
            pat_yearly = patent_df.groupby('year')['patent_count'].sum()
            compare_data['专利申请'] = [pat_yearly.get(y, 0) for y in years]

        comp_df = pd.DataFrame(compare_data)

        # 归一化
        norm_df = comp_df.copy()
        for col in comp_df.columns:
            if col != 'year' and comp_df[col].notna().any():
                vals = comp_df[col].fillna(method='ffill').fillna(method='bfill')
                mn, mx = vals.min(), vals.max()
                if mx > mn:
                    norm_df[col] = (vals - mn) / (mx - mn) * 100
                else:
                    norm_df[col] = 50

        import plotly.graph_objects as go
        fig_compare = go.Figure()
        colors = ['#1E88E5', '#E53935', '#43A047', '#FF6B35', '#7B1FA2', '#FFA726']
        for i, col in enumerate([c for c in norm_df.columns if c != 'year']):
            fig_compare.add_trace(go.Scatter(
                x=norm_df['year'], y=norm_df[col],
                mode='lines+markers', name=col,
                line=dict(color=colors[i % len(colors)], width=2.5),
                marker=dict(size=6),
                hovertemplate=f'{col}: %{{y:.1f}}<extra></extra>'
            ))

        fig_compare.update_layout(
            xaxis_title='年份', yaxis_title='归一化指数 (0-100)',
            template='plotly_white', hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=400, margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("""
        **解读：** 归一化后的指数使不同量纲的数据可以在同一图表中直观比较。
        当两条曲线的趋势一致时，说明两者存在关联关系。
        """)

        # 相关性
        numeric_cols = [c for c in comp_df.columns if c != 'year']
        if len(numeric_cols) >= 2:
            corr = comp_df[numeric_cols].corr()
            st.markdown("#### 🔗 相关性矩阵")
            import plotly.graph_objects as go
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr.values, x=numeric_cols, y=numeric_cols,
                colorscale='RdBu', zmin=-1, zmax=1,
                text=np.round(corr.values, 2),
                texttemplate='%{text}', textfont=dict(color='white', size=14),
                hovertemplate='%{x} vs %{y}: %{z:.3f}<extra></extra>'
            ))
            fig_corr.update_layout(height=350, margin=dict(l=120, r=20, t=20, b=40))
            st.plotly_chart(fig_corr, use_container_width=True)

st.divider()
st.caption("数据说明: 本平台数据均为模拟/示例数据，仅供功能演示。使用真实数据请替换 data/processed/ 目录下的文件。")
