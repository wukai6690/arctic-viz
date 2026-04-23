"""
数据管理中心页面
集成 GDELT 1.0 + 2.0 爬取/清洗流水线，提供交互式参数配置、实时进度、结果预览和数据质量报告
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
import time
import traceback
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="数据管理中心", page_icon="🗄️", layout="wide")

st.markdown("## 🗄️ 北极多源数据管理中心")
st.markdown("""
一站式管理 GDELT 1.0 事件流式清洗、GDELT 2.0 DOC API 文章抓取、数据质量报告与多源数据清单。
数据来源：GDELT 全球事件数据库 · NSIDC 海冰数据中心 · GeoJSON 手工标注
""")
st.divider()

# -------------------- 工具函数 --------------------
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_RAW = os.path.join(PROJ_ROOT, 'data', 'raw')
DATA_PROCESSED = os.path.join(PROJ_ROOT, 'data', 'processed')
GDELT_OUTPUT = os.path.join(DATA_PROCESSED, 'gdelt2')
os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(GDELT_OUTPUT, exist_ok=True)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def get_file_size_mb(path):
    if os.path.exists(path):
        return os.path.getsize(path) / 1024 / 1024
    return 0

def list_data_files():
    files = []
    for root, _, fnames in os.walk(DATA_PROCESSED):
        for f in fnames:
            fp = os.path.join(root, f)
            files.append({
                'file': f,
                'path': fp,
                'size_mb': get_file_size_mb(fp),
                'modified': datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%Y-%m-%d %H:%M')
            })
    return sorted(files, key=lambda x: x['size_mb'], reverse=True)


# -------------------- 侧边栏：数据概览 --------------------
with st.sidebar:
    st.markdown("### 📂 数据文件状态")

    data_files = list_data_files()
    if data_files:
        total_mb = sum(f['size_mb'] for f in data_files)
        st.markdown(f"**共 {len(data_files)} 个文件 · {total_mb:.2f} MB**")
        for f in data_files[:12]:
            size_str = f"{f['size_mb']:.1f}MB" if f['size_mb'] >= 1 else f"{f['size_mb']*1024:.0f}KB"
            label = f['file']
            if f['size_mb'] > 0.5:
                st.success(f"✅ {label} ({size_str})")
            else:
                st.info(f"📄 {label} ({size_str})")
    else:
        st.warning("暂无数据文件")

    st.divider()
    st.markdown("### 📊 数据源清单")
    st.markdown("""
    | 数据源 | 覆盖范围 | 说明 |
    |--------|---------|------|
    | GDELT 1.0 | 1979-至今 | 每日事件 TSV 流式处理 |
    | GDELT 2.0 | 近12个月 | 文章 + 时间线 API |
    | NSIDC | 1979-2024 | 月度海冰面积 CSV |
    | GeoJSON | 手动标注 | 航道/科考站/冲突 |
    """)

    st.divider()
    st.markdown("### 🗺️ 北极研究问题对应数据")
    st.markdown("""
    - 🌡️ **气候驱动** → NSIDC 海冰 + GDELT 气候事件
    - ⚔️ **技术竞争** → GDELT 技术关键词过滤
    - 🇨🇳 **中国路径** → GDELT 中国+北极关键词
    - 🛢️ **资源博弈** → GDELT 能源/航道事件
    """)


# -------------------- Tab 1: GDELT 1.0 清洗流水线 --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧹 GDELT 1.0 清洗", "📰 GDELT 2.0 抓取",
    "🔍 数据质量报告", "🗃️ 数据预览/导出", "📡 多源数据说明"
])

with tab1:
    st.markdown("### 🧹 GDELT 1.0 事件数据流式清洗流水线")
    st.markdown("""
    **功能**：从 GDELT 官网按日期范围下载每日 ZIP 文件，按块（chunksize）流式处理，
    按北极关键词+利益攸关方过滤，写出清洗后事件与月度面板。
    """)
    st.caption("💡 默认只写出 recommended_keep=1 的推荐记录，显著节省磁盘空间")

    with st.expander("📖 流水线工作原理说明", expanded=False):
        st.markdown("""
        **处理流程：**
        1. 从 GDELT index.html 获取所有文件 URL，按日期范围筛选
        2. 逐文件下载 ZIP → 解压 → 按 chunksize 分块读取 TSV
        3. 对每块执行：关键词匹配 → 利益攸关方检测 → 噪音过滤 → 标记 recommended_keep
        4. 累加月度面板（年份×国家×事件根类别的聚合统计）
        5. 输出：清洗后事件 CSV + 月度面板 CSV + 处理报告 JSON

        **关键词分组**（来自 keywords.csv）：
        - space（北极地区）、actor（利益国）、technology（技术）、
          geopolitics（地缘政治）、climate（气候）、resource（资源）
        - noise（噪音排除，如 Antarctic, penguin）
        """)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### ⚙️ 清洗参数配置")
        start_date = st.text_input(
            "开始日期 (YYYY-MM-DD)",
            value="2023-01-01",
            help="格式: 2023-01-01"
        )
        end_date = st.text_input(
            "结束日期 (YYYY-MM-DD)",
            value="2023-12-31",
            help="格式: 2023-12-31"
        )
        chunksize = st.slider(
            "每块行数 (chunksize)",
            min_value=5000, max_value=100000, value=20000, step=5000,
            help="值越大内存占用越高，值越小写入次数越多"
        )
        keep_all = st.checkbox(
            "保留全部清洗记录（含噪音）",
            value=False,
            help="默认只保留 recommended_keep=1 的记录"
        )
        cache_dir = st.text_input(
            "ZIP 缓存目录",
            value="data/raw",
            help="留空则使用系统临时目录（处理后自动删除）"
        )

    with col_right:
        st.markdown("#### 🗂️ 关键词管理")
        kw_path = os.path.join(PROJ_ROOT, 'keywords.csv')
        kw_df = pd.read_csv(kw_path) if os.path.exists(kw_path) else pd.DataFrame()

        if not kw_df.empty:
            st.markdown(f"**keywords.csv**: {len(kw_df)} 条关键词")
            grp_cnt = kw_df.groupby('group').size()
            for grp, cnt in grp_cnt.items():
                color = "#E53935" if grp == 'noise' else "#43A047" if grp == 'space' else "#1E88E5"
                st.markdown(f"- <span style='color:{color}'>**{grp}**</span>: {cnt} 条", unsafe_allow_html=True)
        else:
            st.warning("keywords.csv 不存在")

        st.markdown("---")
        st.markdown("**运行模式**")
        run_mode = st.radio(
            "数据来源",
            ["🌐 从 GDELT 官网抓取", "💾 使用本地 ZIP 文件"],
            help="本地模式需将 .zip 文件放在 data/raw/ 目录"
        )
        max_files = st.number_input(
            "最多处理文件数（0=不限）",
            min_value=0, max_value=1000, value=20, step=1,
            help="设为 0 则处理全部匹配文件"
        )

    st.divider()

    # 预览将要处理的日期范围
    if start_date and end_date:
        try:
            from datetime import datetime as dt
            sd = dt.strptime(start_date, "%Y-%m-%d")
            ed = dt.strptime(end_date, "%Y-%m-%d")
            days = (ed - sd).days + 1
            st.info(f"📅 日期范围：{start_date} ~ {end_date}，共 **{days} 天**，约 **{days // 30 + 1} 个月**")
        except:
            st.warning("日期格式有误，请使用 YYYY-MM-DD 格式")

    # 执行按钮
    col_b1, col_b2 = st.columns([1, 3])
    with col_b1:
        run_gdelt1 = st.button("🚀 启动 GDELT 1.0 流水线", type="primary", use_container_width=True)

    with col_b2:
        st.markdown("""
        **建议流程**：
        1. 先设置日期范围（如 2023-01-01 ~ 2023-06-30）
        2. 最多文件数设为 6（月度数据约每 2-3 天一个文件）
        3. 点击启动，观察进度条
        4. 完成后切换到「数据质量报告」检查结果
        """)

    if run_gdelt1:
        status_area = st.empty()
        progress_bar = st.progress(0)
        log_area = st.empty()

        def log(msg):
            log_area.code(msg, language=None)

        try:
            from gdelt_pipeline import (
                run_gdelt1_pipeline, fetch_gdelt1_index_urls,
                filter_gdelt1_urls_by_date
            )

            status_area.info("🔄 正在获取 GDELT 文件索引...")
            log("获取 GDELT index.html...")

            if run_mode.startswith("💾"):
                status_area.info("💾 本地模式：扫描 data/raw/*.zip")
                import glob
                local_files = sorted(glob.glob(os.path.join(DATA_RAW, "*.zip")))
                sources = [f for f in local_files if start_date[:4] in f or start_date[2:4] in f]
                log(f"找到 {len(sources)} 个本地 ZIP 文件")
                sources = sources[:max_files] if max_files > 0 else sources
            else:
                all_urls = fetch_gdelt1_index_urls()
                sources = filter_gdelt1_urls_by_date(all_urls, start_date, end_date)
                sources = sources[:max_files] if max_files > 0 else sources

            if not sources:
                st.error("❌ 未找到匹配的文件，请检查日期范围")
            else:
                status_area.info(f"🔄 找到 {len(sources)} 个文件，开始流式处理...")
                log(f"将处理 {len(sources)} 个文件\n")

                start_time = time.time()

                with st.spinner(f"正在处理 {len(sources)} 个 GDELT 文件，请耐心等待..."):
                    run_gdelt1_pipeline(
                        keyword_csv=kw_path,
                        output_dir=DATA_PROCESSED,
                        events_file_pattern=None,
                        start_date=start_date,
                        end_date=end_date,
                        max_files=max_files if max_files > 0 else None,
                        chunksize=chunksize,
                        keep_all_cleaned=keep_all,
                        cache_dir=cache_dir if cache_dir else None,
                    )

                elapsed = time.time() - start_time

                progress_bar.progress(1.0)
                status_area.success(
                    f"✅ GDELT 1.0 清洗完成！耗时 {elapsed:.1f} 秒，"
                    f"输出文件：{DATA_PROCESSED}/"
                )
                log(f"✅ 完成！耗时 {elapsed:.1f} 秒")

                # 展示输出文件
                out_files = list_data_files()
                st.markdown("#### 📁 本次输出文件")
                for f in out_files:
                    if f['size_mb'] > 0.0001:
                        st.success(f"✅ {f['file']} ({f['size_mb']:.2f} MB)")

        except FileNotFoundError as e:
            st.error(f"❌ 文件未找到：{e}")
            st.info("💡 请确保 keywords.csv 存在于项目根目录")
        except Exception as e:
            st.error(f"❌ 处理出错：{e}")
            st.code(traceback.format_exc())


# -------------------- Tab 2: GDELT 2.0 抓取 --------------------
with tab2:
    st.markdown("### 📰 GDELT 2.0 DOC API 文章抓取流水线")
    st.markdown("""
    **功能**：通过 GDELT 2.0 Document API 抓取近 12 个月的北极相关新闻文章与时间线数据。
    支持按主题（航天技术/极地科考/地缘政治等）分组查询。
    """)
    st.caption("⚠️ 注意：GDELT DOC API 有频率限制，每次查询后自动暂停 2 秒，完整运行约需 10-15 分钟")

    with st.expander("📖 GDELT 2.0 API 模式说明", expanded=False):
        st.markdown("""
        GDELT 2.0 Document API 提供多种数据模式：

        | 模式 | 说明 | 用途 |
        |------|------|------|
        | artlist | 文章列表 | 获取北极相关新闻标题/摘要/来源 |
        | timelinevol | 音量时间线 | 各主题新闻报道量随时间变化 |
        | timelinetone | 语调时间线 | 各主题情感值随时间变化 |
        | timelinesourcecountry | 来源国家 | 各新闻来源国的报道量时间线 |

        **查询策略**：从 keywords.csv 选取 high/medium 优先级词条，
        按北极地区 + 主题关键词组合成复合查询，减少噪音。
        """)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### ⚙️ API 参数配置")
        timespan = st.select_slider(
            "时间跨度",
            options=["1month", "3months", "6months", "12months", "24months"],
            value="6months",
            help="API 返回数据的时间范围"
        )
        maxrecords = st.slider(
            "每查询最大记录数",
            min_value=50, max_value=500, value=250, step=50
        )
        min_priority = st.selectbox(
            "最低关键词优先级",
            ["low", "medium", "high"],
            index=1,
            help="只使用 keywords.csv 中 priority >= 此值的关键词"
        )
        top_n = st.slider(
            "每组最多关键词数（API限制）",
            min_value=2, max_value=10, value=6,
            help="每组查询最多发送的关键词数量（GDELT API 限制每查询最多约 10 个词）"
        )

    with col_r:
        st.markdown("#### 🔍 查询主题预览")
        kw_path = os.path.join(PROJ_ROOT, 'keywords.csv')
        kw_df = pd.read_csv(kw_path) if os.path.exists(kw_path) else pd.DataFrame()
        if not kw_df.empty:
            from gdelt_pipeline import KeywordTable
            kw = KeywordTable.from_csv(kw_path)
            for grp in ['space', 'actor', 'technology', 'geopolitics', 'climate', 'resource']:
                terms = kw.terms(grp, min_priority=min_priority, top_n=top_n)
                if terms:
                    st.markdown(f"**{grp.upper()}**：`{'` · `'.join(terms[:4])}` ...")
        else:
            st.warning("keywords.csv 不存在")

        st.markdown("---")
        st.markdown("#### 📋 将执行的查询")
        from gdelt_pipeline import build_doc_queries, KeywordTable
        try:
            kw = KeywordTable.from_csv(kw_path)
            queries = build_doc_queries(kw, min_priority=min_priority, top_n_per_group=top_n)
            for name, q in queries:
                st.code(f"[{name}]\n{q[:80]}..." if len(q) > 80 else f"[{name}]\n{q}", language=None)
        except Exception as e:
            st.warning(f"无法预览查询：{e}")

    st.divider()
    st.warning("⚠️ **重要提示**：API 查询会向 GDELT 服务器发送约 5×4=20 个请求，每次暂停 2 秒，完整运行约需 10-20 分钟。中途刷新页面会导致任务中断。")

    run_gdelt2 = st.button("🚀 启动 GDELT 2.0 抓取（耗时较长）", type="primary")

    if run_gdelt2:
        status2 = st.empty()
        progress2 = st.progress(0)
        log2 = st.empty()

        try:
            from gdelt_pipeline import run_gdelt2_doc_pipeline, build_doc_queries, KeywordTable

            kw = KeywordTable.from_csv(kw_path)
            queries = build_doc_queries(kw, min_priority=min_priority, top_n_per_group=top_n)

            total_steps = len(queries) * 4  # 4 种模式
            step = 0

            status2.info(f"🔄 开始 GDELT 2.0 抓取，共 {len(queries)} 个查询 × 4 种模式 = {total_steps} 个 API 请求")

            start_time = time.time()

            with st.spinner("正在向 GDELT API 发送请求，请耐心等待..."):
                run_gdelt2_doc_pipeline(
                    keyword_csv=kw_path,
                    output_dir=GDELT_OUTPUT,
                    timespan=timespan,
                    maxrecords=maxrecords,
                    min_priority=min_priority,
                    top_n_per_group=top_n,
                )

            elapsed = time.time() - start_time
            progress2.progress(1.0)
            status2.success(f"✅ GDELT 2.0 抓取完成！耗时 {elapsed:.1f} 秒")

            # 展示结果
            st.markdown("#### 📁 输出文件")
            out2 = [f for f in os.listdir(GDELT_OUTPUT) if f.endswith('.csv') or f.endswith('.json')]
            for fname in out2:
                fp = os.path.join(GDELT_OUTPUT, fname)
                size = get_file_size_mb(fp)
                st.success(f"✅ {fname} ({size:.2f} MB)")

            # 预览文章数据
            art_csv = os.path.join(GDELT_OUTPUT, 'doc_articles_cleaned.csv')
            if os.path.exists(art_csv):
                df_art = pd.read_csv(art_csv, nrows=5)
                st.markdown("#### 👁️ 文章数据预览（前5条）")
                cols_show = [c for c in df_art.columns if c not in ['_match_text', 'SOURCEURL', 'url']]
                st.dataframe(df_art[cols_show], use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"❌ GDELT 2.0 抓取出错：{e}")
            st.code(traceback.format_exc())


# -------------------- Tab 3: 数据质量报告 --------------------
with tab3:
    st.markdown("### 🔍 数据质量报告")

    # GDELT 1.0 报告
    summary_json = os.path.join(DATA_PROCESSED, 'gdelt1_summary.json')
    if os.path.exists(summary_json):
        with open(summary_json, encoding='utf-8') as f:
            summary = json.load(f)

        st.markdown("#### 🧹 GDELT 1.0 清洗流水线报告")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("请求文件数", summary.get('files_requested', 0))
        with c2:
            st.metric("失败文件数", summary.get('files_failed', 0), delta="⚠️" if summary.get('files_failed', 0) > 0 else "✅")
        with c3:
            st.metric("读取总行数", f"{summary.get('rows_read_total', 0):,}")
        with c4:
            st.metric("推荐保留行数", f"{summary.get('rows_recommended_keep_total', 0):,}")

        keep_rate = 0
        if summary.get('rows_read_total', 0) > 0:
            keep_rate = summary.get('rows_recommended_keep_total', 0) / summary.get('rows_read_total', 0) * 100

        c5, c6 = st.columns(2)
        with c5:
            st.metric("清洗后行数（全部）", f"{summary.get('rows_cleaned_total', 0):,}")
        with c6:
            st.metric("推荐保留率", f"{keep_rate:.2f}%")

        if summary.get('files_failed', 0) > 0:
            failed_json = os.path.join(DATA_PROCESSED, 'gdelt1_failed_files.json')
            if os.path.exists(failed_json):
                with open(failed_json, encoding='utf-8') as f:
                    failed = json.load(f)
                st.warning(f"⚠️ 有 {len(failed)} 个文件处理失败：")
                for item in failed[:10]:
                    st.code(f"文件: {item.get('source', 'N/A')}\n错误: {item.get('error', 'N/A')}")
    else:
        st.info("📋 GDELT 1.0 清洗报告暂不存在，请先运行清洗流水线")

    st.divider()

    # 数据完整性检查
    st.markdown("#### 🗂️ 数据完整性检查")

    checks = []

    # GDELT 数据
    for fname, col_check in [
        ('data/processed/gdelt_arctic_by_grid.csv', ['EventCategory', 'EventCount']),
        ('data/processed/gdelt_arctic_by_year_country.csv', ['CountryCode', 'EventCount', 'Year']),
        ('data/processed/gdelt1_events_cleaned.csv', ['Actor1Name', 'EventCode', 'AvgTone']),
        ('data/processed/gdelt1_events_monthly_panel.csv', ['year_month', 'event_count']),
    ]:
        path = os.path.join(PROJ_ROOT, fname)
        if os.path.exists(path):
            df = pd.read_csv(path, nrows=5)
            missing = [c for c in col_check if c not in df.columns]
            if missing:
                checks.append((fname, "⚠️ 缺少列: " + ", ".join(missing), "warning"))
            else:
                checks.append((fname, "✅ 列完整", "success"))
        else:
            checks.append((fname, "❌ 文件不存在", "error"))

    # 海冰数据
    for fname, col_check in [
        ('data/processed/ice_area_monthly.csv', ['jan', 'feb', 'mar']),
        ('data/processed/ice_area_summary.csv', ['mean', 'minimum', 'maximum']),
    ]:
        path = os.path.join(PROJ_ROOT, fname)
        if os.path.exists(path):
            df = pd.read_csv(path, nrows=5)
            missing = [c for c in col_check if c not in df.columns]
            if missing:
                checks.append((fname, "⚠️ 缺少列: " + ", ".join(missing), "warning"))
            else:
                checks.append((fname, "✅ 列完整", "success"))
        else:
            checks.append((fname, "❌ 文件不存在", "error"))

    for fname, msg, level in checks:
        if level == "success":
            st.success(f"✅ `{fname}` — {msg}")
        elif level == "warning":
            st.warning(f"⚠️ `{fname}` — {msg}")
        else:
            st.error(f"❌ `{fname}` — {msg}")

    st.divider()

    # GDELT 2.0 报告
    st.markdown("#### 📰 GDELT 2.0 抓取报告")
    query_log = os.path.join(GDELT_OUTPUT, 'query_log.csv')
    art_csv = os.path.join(GDELT_OUTPUT, 'doc_articles_cleaned.csv')

    if os.path.exists(query_log):
        qdf = pd.read_csv(query_log)
        st.success(f"✅ 已执行 {len(qdf)} 个查询")
        st.dataframe(qdf, use_container_width=True, hide_index=True)
    else:
        st.info("📋 GDELT 2.0 查询记录暂不存在")

    if os.path.exists(art_csv):
        adf = pd.read_csv(art_csv)
        st.markdown(f"**文章统计**：共 {len(adf)} 条，关键词匹配分布：")
        match_cols = [c for c in adf.columns if c.startswith('has_')]
        if match_cols:
            match_stats = adf[match_cols].sum()
            st.bar_chart(match_stats)
    else:
        st.info("📋 GDELT 2.0 文章数据暂不存在")


# -------------------- Tab 4: 数据预览与导出 --------------------
with tab4:
    st.markdown("### 🗃️ 数据预览与导出")

    all_csvs = []
    for root, _, fnames in os.walk(DATA_PROCESSED):
        for f in fnames:
            if f.endswith('.csv'):
                all_csvs.append(os.path.join(root, f))
    for root, _, fnames in os.walk(GDELT_OUTPUT):
        for f in fnames:
            if f.endswith('.csv'):
                all_csvs.append(os.path.join(root, f))

    if not all_csvs:
        st.info("暂无 CSV 文件，请先运行数据流水线")
    else:
        file_options = {os.path.relpath(f, PROJ_ROOT): f for f in sorted(all_csvs)}
        selected_file = st.selectbox("选择要预览的文件", list(file_options.keys()))

        if selected_file:
            fp = file_options[selected_file]
            size = get_file_size_mb(fp)
            st.markdown(f"**文件信息**：{size:.2f} MB · {os.path.basename(fp)}")

            nrows = st.slider("预览行数", min_value=5, max_value=100, value=20, step=5)

            try:
                df = pd.read_csv(fp, nrows=nrows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.markdown("#### 📊 列信息")
                col_info = pd.DataFrame({
                    '列名': df.columns,
                    '类型': [str(dt) for dt in df.dtypes.values],
                    '非空数': [df[c].notna().sum() for c in df.columns],
                    '示例': [str(df[c].dropna().iloc[0]) if df[c].notna().any() else 'N/A' for c in df.columns]
                })
                st.dataframe(col_info, use_container_width=True, hide_index=True)

                col_down1, col_down2 = st.columns(2)
                with col_down1:
                    st.download_button(
                        "📥 下载当前文件 (CSV)",
                        data=open(fp, 'rb').read(),
                        file_name=os.path.basename(fp),
                        mime='text/csv',
                        use_container_width=True
                    )
                with col_down2:
                    st.info(f"文件路径: `{fp}`")
            except Exception as e:
                st.error(f"无法读取文件：{e}")


# -------------------- Tab 5: 多源数据说明 --------------------
with tab5:
    st.markdown("### 📡 北极多源数据清单与获取指南")

    st.markdown("""
    本平台整合了以下多源数据，构建北极地缘气候研究数据生态：
    """)

    # GDELT 数据
    with st.expander("🌐 GDELT 全球事件数据库（核心数据源）", expanded=True):
        st.markdown("""
        **数据地址**：
        - 索引页：http://data.gdeltproject.org/events/index.html
        - API 文档：https://blog.gdeltproject.org/the-gdelt-project-api/
        - GDELT 2.0 分析平台：https://analysis.gdeltproject.org/

        **数据格式**：
        - GDELT 1.0：每日 TSV（Tab分隔），约60个字段，1979年至今
        - GDELT 2.0：JSON 格式文章列表、时间线数据

        **关键字段**：
        - `GlobalEventID`：全球唯一事件ID
        - `SQLDATE`：事件日期（YYYYMMDD）
        - `Actor1CountryCode/Actor2CountryCode`：事件双方国家
        - `EventRootCode`：事件根类别（CAME0编码体系）
        - `AvgTone`：情感值（-100 ~ +100）
        - `ActionGeo_Lat/Long`：事件地理坐标

        **本平台使用方式**：
        1. GDELT 1.0 流水线：按北极关键词过滤，按 chunksize 流式处理，输出清洗后事件
        2. GDELT 2.0 DOC API：抓取近12个月新闻文章与时间线

        **北极关键词策略**：
        - 地区词：Arctic, High North, Northern Sea Route, Northwest Passage...
        - 技术词：icebreaker, LNG, satellite communication, navigation...
        - 噪音过滤：Antarctic, penguin, Arctic Monkeys（乐队名）, cruise...
        """)

    # NSIDC 数据
    with st.expander("❄️ NSIDC 海冰数据"):
        st.markdown("""
        **数据地址**：https://nsidc.org/data/g02135
        - 月度海冰范围数据（Sea Ice Index）
        - 历史数据可追溯到 1979年
        - 格式：ASCII / CSV / NetCDF

        **获取方式**：
        ```python
        # 直接从 NSIDC 下载
        import pandas as pd
        url = "https://noaa-gsdr.s3.amazonaws.com/data/g02135/m Sea Ice Index/"
        # 或使用 nsidc 官方 Python 客户端
        ```

        **本平台处理**：在 `src/ice_data.py` 中通过确定性算法生成 1979-2024 年月度数据，
        供「海冰数据面板」页面可视化使用。

        **替代数据源**：
        - OSI SAF 海冰数据：https://osisaf-hl.met.no/
        - EUMETSAT 海洋与冰冻圈：https://www.eumetsat.int/
        """)

    # 政策文档
    with st.expander("📜 北极政策与治理数据"):
        st.markdown("""
        **官方政策文件**：
        - 中国外交部北极政策：http://www.gov.cn/
        - 美国北极战略：https://www.whitehouse.gov/
        - 俄罗斯北极政策：俄联邦政府官方文件
        - 北极理事会：https://www.arctic-council.org/

        **航运数据**：
        - 北极航道管理局（NSR）：https://www.nsra.ru/
        - Lloyd's List 航运数据库
        - 联合国贸易和发展会议（UNCTAD）海运数据

        **资源数据**：
        - USGS 极地资源评估
        - 俄罗斯自然资源部数据

        **气象/气候数据**：
        - ECMWF 再分析数据（ERA5）
        - NOAA 极地预报数据
        - Copernicus 气候变化服务（C3S）
        """)

    # GeoJSON 数据
    with st.expander("🗺️ 地理空间数据"):
        st.markdown("""
        **本平台手工标注 GeoJSON**：
        - `geojson/arctic_routes.geojson`：三大航道（东北航道/西北航道/中央航道）
        - `geojson/research_stations.geojson`：北极科考站（含中国黄河站等）
        - `geojson/conflicts.geojson`：地缘冲突事件热力点

        **北极权威地理数据源**：
        - NGA Arctic Geospatial Data：https://nga.mil/
        - Natural Earth Data（开源）：https://naturalearthdata.com/
        - INTERACT 科考站目录：https://eu-interact.org/
        - PSMSL 潮位数据（海平面）：https://www.psmsl.org/
        """)

    st.divider()
    st.markdown("""
    ### 🔗 北极研究数据生态图谱

    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                    北极多源数据生态                          │
    │                                                              │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │  GDELT 1.0/2.0 │   │   NSIDC 海冰   │   │   政策/治理    │   │
    │  │  地缘事件数据  │   │   气候监测     │   │   官方文件    │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │            │
    │         ▼                  ▼                   ▼            │
    │  ┌───────────────────────────────────────────────────┐     │
    │  │              数据清洗与标准化处理                    │     │
    │  │  北极关键词过滤 → 网格聚合 → 月度面板 → 可视化输出   │     │
    │  └───────────────────────┬───────────────────────────┘     │
    │                          │                                  │
    │         ┌────────────────┼────────────────┐               │
    │         ▼                ▼                ▼                │
    │  ┌────────────┐   ┌────────────┐   ┌────────────┐        │
    │  │  交互地图   │   │  图表面板   │   │  战略叙事   │        │
    │  │  Folium   │   │  Plotly   │   │  时间线    │        │
    │  └────────────┘   └────────────┘   └────────────┘        │
    └─────────────────────────────────────────────────────────────┘
    ```
    """)

st.divider()
st.caption(
    f"数据管理中心 · 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
    f"项目根目录: {PROJ_ROOT}"
)
