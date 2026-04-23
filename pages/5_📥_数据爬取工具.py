"""
GDELT 数据爬取与清洗页面
提供交互式 GDELT 数据获取、清洗和北极事件过滤功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import time
import traceback
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.gdelt_fetcher import GdeltFetcher, ARCTIC_KEYWORDS
    FETCHER_AVAILABLE = True
except ImportError:
    FETCHER_AVAILABLE = False

st.set_page_config(page_title="GDELT 数据获取", page_icon="📥", layout="wide")

st.markdown("## 📥 GDELT 数据获取与北极事件过滤")
st.markdown("""
从 **GDELT 全球事件数据库**官网抓取北极相关事件数据，支持实时过滤、分类与可视化预览。
""")
st.divider()

if not FETCHER_AVAILABLE:
    st.error("❌ 无法加载 GDELT 爬虫模块，请检查 src/gdelt_fetcher.py 是否存在且语法正确。")
    st.page_link("pages/6_数据管理中心.py", label="👉 前往数据管理中心", icon="🗄️")
    st.stop()

# GDELT 说明
with st.expander("📖 GDELT 数据说明", expanded=False):
    st.markdown("""
    ### GDELT 是什么？

    GDELT（Global Database of Events, Language, and Tone）是全球最大的开放地缘政治事件数据库。
    它每15分钟扫描全球新闻，覆盖纸媒、网络、电视、广播等10万多种信息来源，
    实时编码和索引人类社会中发生的事件。

    ### 数据格式
    GDELT 事件数据为 TSV 格式（制表符分隔），每行一个事件，包含约60个字段。

    ### 北极关键词列表
    本工具使用以下北极相关关键词进行过滤（大小写不敏感）：
    """)
    st.code(', '.join(ARCTIC_KEYWORDS[:25]), language='text')

st.info("💡 **推荐**：完整的数据获取与清洗请使用 [数据管理中心](pages/6_数据管理中心.py)，本页面提供快速预览功能。")

# 侧边栏
with st.sidebar:
    st.markdown("### ⚙️ 参数设置")
    mode = st.radio(
        "运行模式",
        ["🎲 生成模拟数据（推荐首次使用）", "🌐 从 GDELT 官网抓取"],
        help="模拟数据用于快速测试；正式分析请从官网抓取"
    )
    year_range = st.slider(
        "年份范围",
        min_value=2015, max_value=2024,
        value=(2018, 2024), step=1
    )
    grid_size = st.slider(
        "网格精度（度）",
        min_value=1.0, max_value=10.0, value=5.0, step=0.5
    )

    st.divider()
    st.markdown("### 📁 输出文件")
    out_files = [
        ('data/processed/gdelt_arctic_by_grid.csv', '网格聚合数据'),
        ('data/processed/gdelt_arctic_by_year_country.csv', '年度国家聚合'),
        ('data/processed/gdelt_arctic_sample.csv', '样本原始数据'),
    ]
    for path, desc in out_files:
        full = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full):
            size = os.path.getsize(full) / 1024
            st.success(f"✅ {desc} ({size:.1f} KB)")
        else:
            st.error(f"❌ {desc} 不存在")

# 操作区
st.markdown("### 🚀 数据获取操作")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🎲 生成北极事件模拟数据")
    st.markdown("""
    使用概率模型生成符合 GDELT 格式的北极事件数据，
    包含真实的国家分布、事件类别和情感倾向。
    """)
    if st.button("▶️ 生成模拟数据", type="primary", use_container_width=True):
        with st.spinner("正在生成模拟数据..."):
            try:
                fetcher = GdeltFetcher()

                # 生成模拟数据
                np.random.seed(42)
                years = list(range(year_range[0], year_range[1] + 1))
                countries = ['RUS', 'CHN', 'USA', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR']
                categories = [
                    'arctic_shipping', 'arctic_resource', 'arctic_technology',
                    'arctic_military', 'arctic_cooperation', 'arctic_research',
                    'arctic_infrastructure', 'arctic_governance'
                ]

                rows = []
                for year in years:
                    for country in countries:
                        for cat in categories:
                            if np.random.random() < 0.12:
                                lat = np.random.uniform(65, 82)
                                lon = np.random.uniform(-170, 180)
                                count = np.random.randint(1, 30)

                                tone_base = {
                                    'CHN': 2.5, 'RUS': 0.5, 'USA': -1.5,
                                    'NOR': 3.0, 'CAN': 1.0
                                }.get(country, 1.0)
                                if cat == 'arctic_military':
                                    tone_base -= 3.5
                                elif cat == 'arctic_cooperation':
                                    tone_base += 2.5
                                elif cat == 'arctic_shipping':
                                    tone_base += 0.5

                                rows.append({
                                    'GlobalEventID': f'{year}{country}{cat[:3]}{count:04d}',
                                    'Day': f'{year}0101',
                                    'Year': year,
                                    'Year_local': str(year),
                                    'Actor1CountryCode': country,
                                    'ActionGeo_CountryCode': country,
                                    'ActionGeo_Lat': round(lat, 2),
                                    'ActionGeo_Long': round(lon, 2),
                                    'EventCategory': cat,
                                    'NumArticles': np.random.randint(1, 200),
                                    'AvgTone': round(tone_base + np.random.uniform(-1.5, 1.5), 2)
                                })

                df = pd.DataFrame(rows)
                os.makedirs('data/processed', exist_ok=True)
                df.to_csv('data/processed/gdelt_arctic_sample.csv', index=False)

                # 过滤和聚合
                filtered_df = fetcher.filter_arctic_events(df)
                by_grid = fetcher.aggregate_by_grid(filtered_df, grid_size=grid_size)
                by_yc = fetcher.aggregate_by_year_country(filtered_df)

                # 修复聚合后的年份列
                if 'Year' in by_grid.columns and 'Year_local' not in by_grid.columns:
                    by_grid['Year_local'] = by_grid['Year'].astype(str)
                if 'Year' in by_yc.columns and 'Year_local' not in by_yc.columns:
                    by_yc['Year_local'] = by_yc['Year'].astype(str)

                by_grid.to_csv('data/processed/gdelt_arctic_by_grid.csv', index=False)
                by_yc.to_csv('data/processed/gdelt_arctic_by_year_country.csv', index=False)

                st.success(f"✅ 模拟数据生成完成！")
                col_ev, col_gr, col_yr = st.columns(3)
                with col_ev:
                    st.metric("生成事件", len(df))
                with col_gr:
                    st.metric("网格数", len(by_grid))
                with col_yr:
                    st.metric("年国组合", len(by_yc))
                st.info("📁 数据已保存到 data/processed/ 目录。请刷新页面查看更新。")

            except Exception as e:
                st.error(f"❌ 生成失败：{str(e)}")
                st.code(traceback.format_exc())

with col2:
    st.markdown("#### 🌐 抓取 GDELT 数据（需网络）")
    st.markdown("""
    从 GDELT 官网抓取指定年份的北极相关事件。
    **注意**：需要稳定的网络连接，完整抓取可能需要较长时间。
    """)
    st.warning("⚠️ GDELT 服务器位于美国，建议每次只抓取 1 年数据")

    col_fetch1, col_fetch2 = st.columns(2)
    with col_fetch1:
        fetch_year = st.selectbox(
            "抓取年份",
            list(range(2018, 2025)),
            index=5,
            help="建议从近一年开始测试"
        )
    with col_fetch2:
        max_urls = st.slider("最多文件数", 1, 50, 10)

    if st.button("⬇️ 开始抓取", type="secondary", use_container_width=True):
        with st.spinner(f"正在获取 {fetch_year} 年 GDELT 数据..."):
            try:
                fetcher = GdeltFetcher()
                all_urls = fetcher.fetch_index_page()

                # 筛选当年 URL
                year_urls = [u for u in all_urls if str(fetch_year) in u]
                year_urls = year_urls[:max_urls]

                if not year_urls:
                    st.error(f"❌ 未找到 {fetch_year} 年的 GDELT 数据文件")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    all_events = []

                    for i, url in enumerate(year_urls):
                        status_text.text(f"处理 [{i+1}/{len(year_urls)}]: {url.split('/')[-1]}")
                        progress_bar.progress((i + 1) / len(year_urls))

                        try:
                            resp = fetcher.session.get(url, timeout=60)
                            resp.raise_for_status()

                            import zipfile, io
                            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                                for name in z.namelist():
                                    if name.endswith('.csv'):
                                        with z.open(name) as f:
                                            text = f.read().decode('utf-8', errors='ignore')
                                            for line in text.splitlines():
                                                if line.startswith('GLOBALEVENTID'):
                                                    continue
                                                row = fetcher.parse_gdelt_row(line)
                                                if row:
                                                    all_events.append(row)
                        except Exception as e:
                            st.warning(f"处理 {url.split('/')[-1]} 失败: {e}")

                        time.sleep(0.5)

                    progress_bar.empty()
                    status_text.empty()

                    if all_events:
                        raw_df = pd.DataFrame(all_events)
                        filtered = fetcher.filter_arctic_events(raw_df)
                        by_grid = fetcher.aggregate_by_grid(filtered, grid_size=grid_size)
                        by_yc = fetcher.aggregate_by_year_country(filtered)

                        if 'Year' in by_grid.columns and 'Year_local' not in by_grid.columns:
                            by_grid['Year_local'] = by_grid['Year'].astype(str)
                        if 'Year' in by_yc.columns and 'Year_local' not in by_yc.columns:
                            by_yc['Year_local'] = by_yc['Year'].astype(str)

                        os.makedirs('data/raw', exist_ok=True)
                        os.makedirs('data/processed', exist_ok=True)
                        raw_df.to_csv('data/raw/gdelt_raw.csv', index=False)
                        by_grid.to_csv('data/processed/gdelt_arctic_by_grid.csv', index=False)
                        by_yc.to_csv('data/processed/gdelt_arctic_by_year_country.csv', index=False)

                        st.success(
                            f"✅ 抓取完成！原始 {len(raw_df):,} 条 → 北极过滤 {len(filtered):,} 条 "
                            f"→ 网格聚合 {len(by_grid):,} 条"
                        )
                    else:
                        st.warning("⚠️ 未获取到任何事件数据")

            except Exception as e:
                st.error(f"❌ 抓取失败：{str(e)}")
                st.code(traceback.format_exc())

st.divider()

# 数据质量报告
st.markdown("### 📋 当前数据覆盖范围")

grid_path = 'data/processed/gdelt_arctic_by_grid.csv'
yc_path = 'data/processed/gdelt_arctic_by_year_country.csv'

col_rep1, col_rep2 = st.columns(2)

with col_rep1:
    if os.path.exists(grid_path):
        df = pd.read_csv(grid_path)
        st.markdown(f"**网格聚合数据**：{len(df)} 条记录")
        if 'Year' in df.columns:
            years = sorted(df['Year'].unique())
        elif 'Year_local' in df.columns:
            years = sorted([int(y) for y in df['Year_local'].unique() if str(y).isdigit()])
        else:
            years = []
        cats = df['EventCategory'].unique().tolist() if 'EventCategory' in df.columns else []

        st.markdown(f"| 指标 | 数值 |")
        st.markdown(f"|------|------|")
        st.markdown(f"| 年份范围 | {min(years)} - {max(years)} |" if years else "| 年份范围 | 暂无数据 |")
        st.markdown(f"| 覆盖年份数 | {len(years)} 年 |" if years else "| 覆盖年份数 | 0 |")
        st.markdown(f"| 事件类别数 | {len(cats)} 类 |")
        st.markdown(f"| 总事件数 | {df['EventCount'].sum():,} |" if 'EventCount' in df.columns else "| 总事件数 | N/A |")
    else:
        st.info("暂无网格数据")

with col_rep2:
    if os.path.exists(yc_path):
        df_yc = pd.read_csv(yc_path)
        st.markdown(f"**年度国家聚合数据**：{len(df_yc)} 条记录")
        countries = df_yc['CountryCode'].unique().tolist() if 'CountryCode' in df_yc.columns else []
        st.markdown(f"**涉及国家**：`{', '.join(sorted(countries))}`")
        if 'AvgTone' in df_yc.columns:
            avg_tone = df_yc['AvgTone'].mean()
            st.markdown(f"**平均情感值**：{avg_tone:.2f}")
    else:
        st.info("暂无年度国家数据")

# 团队说明
st.divider()
st.markdown("""
### 👥 数据处理说明

**GDELT 数据处理流程**：

1. **下载原始 TSV**：从 GDELT 官网按日期范围下载每日 ZIP 文件
2. **北极关键词过滤**：使用 30+ 个北极相关关键词（Arctic, icebreaker, Northern Sea Route...）
3. **事件分类**：将事件分为航道航运/资源开发/技术竞争/军事活动/科技合作等8类
4. **网格聚合**：按 5°×5° 经纬度网格聚合，生成热力图数据
5. **年度国家聚合**：按年份×国家二级聚合，生成趋势分析数据

**噪音过滤**：排除包含 Antarctic, penguin, cruise 等明显非北极内容的事件
""")

st.caption(f"工具版本: v2.0 · GDELT 数据源: http://data.gdeltproject.org · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
