"""
模块6：数据中心与工具模块
数据集下载、上传数据可视化、时空查询与对比分析
重制版：高级UI、精细化功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.data_core import load_ice_data, load_gdelt_data, load_patent_data, load_risk_data, get_downloadable_datasets
from src.viz import COUNTRY_NAMES

st.set_page_config(page_title="数据中心", page_icon="🗄️", layout="wide")

st.markdown("""
<style>
    .page-header {
        background: linear-gradient(135deg, #004D40 0%, #00695C 50%, #00897B 100%);
        padding: 1.5rem 2rem;
        border-radius: 0 0 18px 18px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,105,92,0.2);
    }
    .page-header h1 { color: white !important; font-size: 1.55rem; font-weight: 700; margin: 0 0 0.3rem 0; }
    .page-header p { color: rgba(255,255,255,0.82) !important; font-size: 0.83rem; margin: 0; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 8px 18px; font-weight: 600; font-size: 0.85rem; }
    section[data-testid="stMain"] { background: #ffffff !important; }
    section[data-testid="stMain"] > div { background: #ffffff !important; }
    section[data-testid="stMain"] p, section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2, section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4, section[data-testid="stMain"] li { color: #1a1a2e !important; }
    [data-testid="stMetricValue"] { color: #1a1a2e !important; }
    [data-testid="stMetricLabel"] { color: #546E7A !important; }
    .stTabs [data-baseweb="tab"] { color: #333 !important; }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(0,0,0,0.05) !important; }
    hr { border-color: rgba(0,0,0,0.08) !important; }
    .streamlit-expander { border: 1px solid #e8e8e8 !important; border-radius: 12px !important; }
    [data-testid="stCaption"] { color: #90A4AE !important; }
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
    .download-card {
        background: white; border-radius: 12px; padding: 1rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin: 0.4rem 0;
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
    }
    .download-card .dl-info { flex: 1; }
    .download-card .dl-format {
        display: inline-block; background: #E3F2FD; color: #1565C0;
        padding: 2px 8px; border-radius: 8px; font-size: 0.72rem; font-weight: 600;
    }
    .upload-zone {
        border: 2px dashed #B0BEC5; border-radius: 14px; padding: 2rem;
        text-align: center; transition: all 0.2s;
    }
    .upload-zone:hover { border-color: #1565C0; background: #F5F9FF; }
</style>
<div class="page-header">
    <h1>🗄️ 数据中心与工具</h1>
    <p>数据集下载 · 上传数据可视化 · 时空查询 · 对比分析</p>
</div>
""", unsafe_allow_html=True)


# ============ 主区域 ============
tab1, tab2, tab3, tab4 = st.tabs([
    "📥 数据集下载", "📤 数据上传", "🔍 时空查询", "📊 数据对比"
])


with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📥 平台数据集下载</h3>', unsafe_allow_html=True)
    st.markdown("本平台提供以下可供下载的数据集（CSV/GeoJSON 格式），所有数据均经过清洗和聚合处理，可直接用于学术研究和二次分析。", unsafe_allow_html=False)

    datasets = get_downloadable_datasets()

    for ds in datasets:
        col_info, col_dl = st.columns([4, 1])
        with col_info:
            st.markdown(f"""
            <div class="download-card">
                <div class="dl-info">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.3rem;">
                        <span class="dl-format">{ds['format']}</span>
                        <span style="font-weight:700;font-size:0.95rem;">{ds['name']}</span>
                    </div>
                    <div style="font-size:0.78rem;color:#546E7A;margin-bottom:0.3rem;">{ds['desc']}</div>
                    <div style="font-size:0.72rem;color:#90A4AE;">
                        行数: {ds['rows']} · 大小: {ds['size']} · 来源: {ds['source']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_dl:
            file_path = os.path.join('data', 'processed', ds['file'])
            geo_dir = os.path.join('geojson', ds['file'])
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    mime = 'text/csv' if ds['file'].endswith('.csv') else 'application/json'
                    st.download_button(
                        "下载", f.read(),
                        file_name=ds['file'],
                        mime=mime,
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
                st.button("暂无数据", disabled=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📤 上传数据可视化工具</h3>', unsafe_allow_html=True)
    st.markdown("上传您的 CSV 数据文件，自动生成可视化图表。支持标准带表头 UTF-8 编码 CSV 文件。", unsafe_allow_html=False)

    uploaded = st.file_uploader(
        "选择 CSV 文件",
        type=['csv'],
        help="支持标准的带表头 UTF-8 编码 CSV 文件"
    )

    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.success(f"✅ 成功加载 {uploaded.name}，共 {len(df)} 行 × {len(df.columns)} 列")

            with st.expander("📋 数据预览（前10行）"):
                st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            info_cols = st.columns(3)
            with info_cols[0]:
                st.metric("数据行数", len(df))
            with info_cols[1]:
                st.metric("数据列数", len(df.columns))
            with info_cols[2]:
                st.metric("缺失值", df.isnull().sum().sum())

            st.markdown("#### 列信息")
            col_info_df = pd.DataFrame({
                '列名': df.columns,
                '类型': [str(dtype) for dtype in df.dtypes],
                '非空数': [df[c].notna().sum() for c in df.columns],
                '示例值': [str(df[c].iloc[0]) if len(df) > 0 else '' for c in df.columns]
            })
            st.dataframe(col_info_df, use_container_width=True, hide_index=True)

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
                        template='plotly_white', height=420,
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
                        template='plotly_white', height=420,
                        margin=dict(l=60, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "散点图":
                    color_col = st.selectbox("颜色分组（可选）", [None] + all_cols)
                    import plotly.express as px
                    if color_col:
                        fig = px.scatter(df, x=x_col, y=y_col, color=color_col)
                    else:
                        fig = go.Figure(go.Scatter(
                            x=df[x_col], y=df[y_col], mode='markers',
                            marker=dict(size=8, color='#1E88E5')
                        ))
                    fig.update_layout(template='plotly_white', height=420,
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
                        template='plotly_white', height=420,
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
                    fig.update_layout(height=420, margin=dict(l=60, r=20, t=20, b=40))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("未检测到数值列，请上传包含数值数据的 CSV 文件。")

        except Exception as e:
            st.error(f"❌ 加载文件失败: {e}")
    else:
        st.info("请上传一个 CSV 文件开始分析。推荐格式：带表头的 UTF-8 编码 CSV")
        with st.expander("📝 CSV 模板示例"):
            st.code("年份,海冰面积,平均气温,航道事件数\n2020,10.5,1.2,125\n2021,9.8,1.5,138\n2022,9.2,1.8,152", language="csv")
    st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔍 时空查询工具</h3>', unsafe_allow_html=True)
    st.markdown("在海冰和 GDELT 数据中按时间和空间条件进行筛选查询。", unsafe_allow_html=False)

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
    st.markdown('</div>', unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 多源数据对比分析</h3>', unsafe_allow_html=True)
    st.markdown("在同一图表中对比多个数据源的时间演变趋势。数据自动归一化到 0-100 范围，便于直观对比不同量纲的指标。", unsafe_allow_html=False)

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
            height=420, margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("""
        **解读：** 归一化后的指数使不同量纲的数据可以在同一图表中直观比较。
        当两条曲线的趋势一致时，说明两者存在关联关系。
        """, unsafe_allow_html=False)

        # 相关性
        numeric_cols = [c for c in comp_df.columns if c != 'year']
        if len(numeric_cols) >= 2:
            corr = comp_df[numeric_cols].corr()
            st.markdown("#### 🔗 相关性矩阵")
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr.values, x=numeric_cols, y=numeric_cols,
                colorscale='RdBu', zmin=-1, zmax=1,
                text=np.round(corr.values, 2),
                texttemplate='%{text}', textfont=dict(color='white', size=14),
                hovertemplate='%{x} vs %{y}: %{z:.3f}<extra></extra>'
            ))
            fig_corr.update_layout(height=380, margin=dict(l=120, r=20, t=20, b=40))
            st.plotly_chart(fig_corr, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.caption("数据说明: 本平台数据均为模拟/示例数据，仅供功能演示。使用真实数据请替换 data/processed/ 目录下的文件。")
