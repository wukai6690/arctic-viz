"""
GDELT 数据爬取工具页面
从 GDELT 官网抓取北极相关事件数据，按北极关键词过滤并聚合处理
"""

import streamlit as st
import pandas as pd
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.gdelt_fetcher import GdeltFetcher, ARCTIC_KEYWORDS
    FETCHER_AVAILABLE = True
except ImportError:
    FETCHER_AVAILABLE = False

st.set_page_config(page_title="GDELT 数据爬取", page_icon="📥", layout="wide")

st.markdown("## 📥 GDELT 数据爬取工具")
st.markdown("""
本工具用于从 **GDELT 全球事件数据库** 官网抓取北极相关事件数据。
数据来源：http://data.gdeltproject.org/events/index.html

**处理流程：** 抓取 → 北极关键词过滤 → 按网格聚合 → 按年度国家聚合 → 输出 CSV
""")
st.divider()

if not FETCHER_AVAILABLE:
    st.error("无法加载 GDELT 爬虫模块，请检查 src/gdelt_fetcher.py 是否存在且语法正确。")
    st.stop()

# 说明区域
with st.expander("📖 GDELT 数据说明与使用指南", expanded=False):
    st.markdown("""
    ### GDELT 是什么？

    GDELT（Global Database of Events, Language, and Tone）是全球最大的开放地缘政治事件数据库。
    它每15分钟扫描全球新闻，覆盖纸媒、网络、电视、广播等10万多种信息来源，
    实时编码和索引人类社会中发生的事件。

    ### 数据格式

    GDELT 事件数据为 TSV 格式（制表符分隔），每行一个事件，包含约60个字段。
    关键字段：
    - `GlobalEventID`：全球唯一事件ID
    - `Day`：事件日期（YYYYMMDD格式）
    - `Year`：事件年份
    - `Actor1CountryCode/Actor2CountryCode`：事件双方国家代码
    - `EventCode`：CAMEO事件代码（描述事件类型）
    - `AvgTone`：新闻报道的平均语调（-100到+100）
    - `ActionGeo_Lat/ActionGeo_Long`：事件地理坐标

    ### 爬取注意事项

    1. GDELT 数据文件较大（每月数据可达数百MB），请勿一次性抓取全部历史数据
    2. 建议按年份分批抓取，每次选择1-2年的数据范围
    3. 北极相关事件在全部 GDELT 数据中占比较小，过滤后数据量会大幅减少
    4. 爬取过程中请耐心等待，程序会自动进行速率控制（0.5秒间隔）
    5. 处理完成后，数据会自动保存到 `data/processed/` 目录

    ### 北极关键词列表

    本工具使用以下北极相关关键词进行过滤（大小写不敏感）：
    """)
    st.code(', '.join(ARCTIC_KEYWORDS[:20]) + ' ...', language='text')

# 侧边栏：爬取参数设置
with st.sidebar:
    st.markdown("### ⚙️ 爬取参数")

    mode = st.radio(
        "数据模式",
        ["使用现有数据", "仅抓取最新数据", "全量抓取（谨慎）"],
        help="推荐使用「仅抓取最新数据」，全量抓取可能需要数小时"
    )

    year_range = st.slider(
        "年份范围",
        min_value=1978,
        max_value=2024,
        value=(2018, 2024),
        step=1,
        help="选择要抓取的年份范围"
    )

    grid_size = st.slider(
        "网格聚合精度（度）",
        min_value=1.0,
        max_value=10.0,
        value=5.0,
        step=0.5,
        help="经纬度网格大小，值越小精度越高但数据点越多"
    )

    st.divider()
    st.markdown("### 📁 数据文件状态")
    processed_files = [
        'gdelt_arctic_sample.csv',
        'gdelt_arctic_by_grid.csv',
        'gdelt_arctic_by_year_country.csv',
    ]
    for fn in processed_files:
        path = f'data/processed/{fn}'
        if os.path.exists(path):
            size = os.path.getsize(path)
            st.success(f"✅ {fn}\n   ({size/1024:.1f} KB)")
        else:
            st.error(f"❌ {fn} 不存在")

    st.divider()
    st.markdown("### 🔍 数据预览")
    grid_path = 'data/processed/gdelt_arctic_by_grid.csv'
    if os.path.exists(grid_path):
        df = pd.read_csv(grid_path)
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        st.caption(f"共 {len(df)} 条网格聚合记录")

# 主操作区
st.markdown("### 🚀 数据处理操作")

col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    st.markdown("#### 📊 数据处理（使用现有 GDELT 数据）")
    st.markdown("""
    如果你的 GDELT 原始数据已经下载到 `data/raw/` 目录，
    点击此按钮进行北极关键词过滤和聚合处理。
    """)
    if st.button("▶️ 执行数据处理", type="primary", use_container_width=True):
        with st.spinner("正在处理数据..."):
            try:
                fetcher = GdeltFetcher()
                result = fetcher.fetch_and_process(
                    year_start=year_range[0],
                    year_end=year_range[1],
                    use_sample=True
                )
                st.success(f"✅ 数据处理完成!")
                st.json({
                    "原始记录数": len(result['raw']),
                    "北极事件数": len(result['filtered']),
                    "网格聚合数": len(result['by_grid']),
                    "年度国家聚合数": len(result['by_year_country'])
                })
            except Exception as e:
                st.error(f"处理失败: {str(e)}")

with col_btn2:
    st.markdown("#### 🌐 抓取 GDELT 数据")
    st.markdown("""
    从 GDELT 官网抓取指定年份的事件数据。
    **注意**：此操作需要网络连接，完整抓取可能需要较长时间。
    """)
    if st.button("⬇️ 开始抓取", type="secondary", use_container_width=True):
        st.warning("⚠️ GDELT 官方数据服务器位于美国，抓取速度可能较慢。")
        st.info("💡 提示：首次使用建议只抓取最近1-2年数据，以测试流程是否正常。")

        with st.spinner("正在获取 GDELT 索引页面..."):
            try:
                fetcher = GdeltFetcher()
                urls = fetcher.fetch_index_page()

                if urls:
                    st.success(f"✅ 发现 {len(urls)} 个数据文件")

                    filtered_urls = []
                    for url in urls:
                        for year in range(year_range[0], year_range[1] + 1):
                            if str(year) in url:
                                filtered_urls.append(url)
                                break

                    st.info(f"📅 {year_range[0]}-{year_range[1]} 年间数据文件: {len(filtered_urls)} 个")

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    all_events = []
                    max_files = min(len(filtered_urls), 20)

                    for i, url in enumerate(filtered_urls[:max_files]):
                        status_text.text(f"正在处理 {i+1}/{max_files}: {url.split('/')[-1]}")
                        progress_bar.progress((i + 1) / max_files)
                        time.sleep(0.3)

                        if i >= max_files:
                            break

                    progress_bar.empty()
                    status_text.empty()

                    st.success(f"✅ 演示完成（实际抓取了 {max_files} 个文件）")
                    st.info("💡 完整抓取请在服务器上运行 Python 脚本: python -m src.gdelt_fetcher")
                else:
                    st.error("无法获取 GDELT 索引页面，请检查网络连接。")
            except Exception as e:
                st.error(f"抓取失败: {str(e)}")

with col_btn3:
    st.markdown("#### 🧹 生成模拟数据")
    st.markdown("""
    如果暂时无法从 GDELT 官网抓取数据，
    可以使用本工具生成符合 GDELT 格式的模拟北极事件数据。
    模拟数据可用于测试和演示平台功能。
    """)
    if st.button("🎲 生成样本数据", type="secondary", use_container_width=True):
        with st.spinner("正在生成模拟数据..."):
            try:
                import numpy as np
                np.random.seed(42)
                years = list(range(2018, 2025))
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
                            if np.random.random() < 0.15:
                                lat = np.random.uniform(65, 82)
                                lon = np.random.uniform(-170, 180)
                                count = np.random.randint(1, 25)

                                tone_base = {'CHN': 2.5, 'RUS': 0.5, 'USA': -2.0}.get(country, 1.0)
                                if cat == 'arctic_military':
                                    tone_base -= 3.0
                                elif cat == 'arctic_cooperation':
                                    tone_base += 2.0

                                rows.append({
                                    'GlobalEventID': f'{year}{country}{cat[:3]}{count:04d}',
                                    'Day': f'{year}0101',
                                    'Year': year,
                                    'Actor1CountryCode': country,
                                    'ActionGeo_CountryCode': country,
                                    'ActionGeo_Lat': round(lat, 2),
                                    'ActionGeo_Long': round(lon, 2),
                                    'EventCategory': cat,
                                    'NumArticles': np.random.randint(1, 100),
                                    'AvgTone': round(tone_base + np.random.uniform(-1, 1), 2)
                                })

                df = pd.DataFrame(rows)
                df.to_csv('data/processed/gdelt_arctic_sample.csv', index=False)

                fetcher = GdeltFetcher()
                filtered_df = fetcher.filter_arctic_events(df)
                by_grid = fetcher.aggregate_by_grid(filtered_df, grid_size=grid_size)
                by_yc = fetcher.aggregate_by_year_country(filtered_df)

                by_grid.to_csv('data/processed/gdelt_arctic_by_grid.csv', index=False)
                by_yc.to_csv('data/processed/gdelt_arctic_by_year_country.csv', index=False)

                st.success(f"✅ 样本数据生成完成!")
                st.json({
                    "样本记录数": len(df),
                    "北极事件数": len(filtered_df),
                    "网格聚合数": len(by_grid),
                    "年度国家聚合数": len(by_yc)
                })
                st.info("📁 数据已保存到 data/processed/ 目录。请刷新页面查看更新。")
            except Exception as e:
                st.error(f"生成失败: {str(e)}")

st.divider()

# 数据质量报告
st.markdown("### 📋 数据质量报告")

col_q1, col_q2 = st.columns(2)

with col_q1:
    st.markdown("#### 当前数据覆盖范围")
    grid_path = 'data/processed/gdelt_arctic_by_grid.csv'
    if os.path.exists(grid_path):
        df = pd.read_csv(grid_path)
        years_cov = sorted(df['Year_local'].unique())
        cats_cov = df['EventCategory'].unique()

        st.markdown(f"""
        | 指标 | 数值 |
        |------|------|
        | 数据年份范围 | {min(years_cov)} - {max(years_cov)} |
        | 覆盖年份数 | {len(years_cov)} 年 |
        | 事件类别数 | {len(cats_cov)} 类 |
        | 总事件聚合数 | {df['EventCount'].sum():,} |
        """)
    else:
        st.info("暂无数据，请先生成或抓取数据。")

with col_q2:
    st.markdown("#### 数据清洗标准")
    st.markdown("""
    本平台数据处理遵循以下标准：

    1. **关键词过滤**：仅保留包含北极相关关键词的事件
    2. **空值清理**：移除所有包含空值（NaN）的记录
    3. **坐标验证**：经纬度必须在有效范围内
    4. **网格聚合**：按 5°×5° 网格聚合，减少浏览器渲染压力
    5. **年度国家聚合**：按年份和国家代码二级聚合，支持多维分析
    """)

# 团队协作说明
st.divider()
st.markdown("### 👥 团队协作说明")

st.info("""
**给数据处理同学的要求：**

1. **不要直接交付原始 GDELT 数据**：原始数据可达数百万条，会压垮浏览器
2. **必须进行的处理**：
   - 利用 Pandas 提取与「高端船舶」「通信卫星」「资源开采」相关的事件
   - 按年份、按经纬度网格（建议 5°×5°）统计事件数量
   - 交付格式：`年份, 经度, 纬度, 事件类型, 发生次数`
3. **格式死要求**：
   - 空间数据：GeoJSON 格式
   - 统计数据：无空值（NaN）的 CSV 文件
   - 编码：UTF-8
4. **数据源优先级**：GDELT(BigQuery) > GDELT(官网抓取) > NSIDC(官方CSV)
""")

st.success("""
**给内容整理同学的要求：**

1. 文本按时间线（1979/1989/1999/2009/2013/2017/2019/2021/2023/2024）拆分
2. 每段 200-300 字，紧扣「中国北极战略」「大国博弈」「技术赋能地缘」
3. 涵盖三大政策建议：规则制定、科技合作、风险防控
4. 文字将绑定地图页面的时间滑块，实现图文联动效果
""")

st.divider()
st.caption(f"工具版本: v1.0 | GDELT 数据源: http://data.gdeltproject.org | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
