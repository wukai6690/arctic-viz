"""Two-part patent search and landscape workspace.

The data loader and evidence panel remain in ``patent_views``.  This module
only reorganises the visible experience into search and analysis workspaces so
the existing patent provenance and tests stay reusable.
"""
from __future__ import annotations

import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import section_title, show_chart
from src.patent_views import (
    _chart_year,
    _completeness_score,
    _country,
    _heatmap_figure,
    _record_panel,
    _search_text,
    _sort_records,
    _trend_figure,
    load_coverage,
    load_patents,
)


def _topic_group(record: dict) -> str:
    text = " ".join(str(record.get(key, "")) for key in ("technology", "preliminary_categories", "title", "title_zh")).casefold()
    if any(token in text for token in ("船", "破冰", "航线", "ice navigation", "水面")):
        return "船舶与破冰"
    if any(token in text for token in ("通信", "卫星", "地面站", "中继")):
        return "通信与卫星"
    if any(token in text for token in ("观测", "遥感", "海冰", "雷达", "声呐", "检测", "监测")):
        return "海冰观测与预警"
    if any(token in text for token in ("预测", "算法", "模型", "数据", "人工智能", "ai")):
        return "算法与数据"
    if any(token in text for token in ("能源", "资源", "风电", "储能", "电力")):
        return "能源与资源"
    if any(token in text for token in ("材料", "结构", "防护", "建筑", "低温")):
        return "材料与防护"
    return "其他极地技术"


def _topic_figure(records: list[dict]) -> go.Figure:
    counts = pd.Series([_topic_group(record) for record in records]).value_counts().sort_values()
    fig = go.Figure(go.Bar(x=counts.values, y=counts.index, orientation="h", text=counts.values, textposition="outside", marker_color="#2d91cc"))
    fig.update_layout(height=320, margin={"l": 110, "r": 45, "t": 18, "b": 38}, xaxis_title="公开文本数", yaxis_title="")
    return fig


def _applicant_figure(records: list[dict]) -> go.Figure:
    names = [str(record.get("assignee") or "申请人未注明").split(";")[0].strip() for record in records]
    counts = pd.Series(names).value_counts().head(10).sort_values()
    fig = go.Figure(go.Bar(x=counts.values, y=counts.index, orientation="h", text=counts.values, textposition="outside", marker_color="#61a9d8"))
    fig.update_layout(height=320, margin={"l": 145, "r": 45, "t": 18, "b": 38}, xaxis_title="公开文本数", yaxis_title="")
    return fig


def _filter_records(records: list[dict], country: str, technology: str, basis: str, year_range: tuple[int, int], query: str, text_status: str, date_only: bool) -> list[dict]:
    query = query.strip().casefold()
    result = []
    for record in records:
        year = _chart_year(record, basis)
        if country != "全部公开局／地区" and _country(record) != country:
            continue
        if technology != "全部技术类别" and record.get("technology") != technology:
            continue
        if year is None and date_only:
            continue
        if year is not None and not year_range[0] <= year <= year_range[1]:
            continue
        if query and query not in _search_text(record):
            continue
        source = record.get("abstract_zh_source") or "未提供摘要"
        if text_status == "公开中文原文" and source != "专利公开中文原文":
            continue
        if text_status == "中文译文" and source != "基于公开摘要的中文译文":
            continue
        if text_status == "未提供摘要" and source not in {"", "公开页面未提供摘要"}:
            continue
        result.append(record)
    return result


def _workbench_css() -> None:
    st.markdown("""<style>
    .patent-workbench-note{display:flex;gap:12px;background:#e7f4fc;border:1px solid #cce7f5;border-left:4px solid #328fc5;border-radius:12px;padding:12px 15px;margin:4px 0 18px;color:#5d7b91}.patent-workbench-note b{color:#176c9d;white-space:nowrap}.patent-workbench-note span{font-size:13px}
    .patent-result-row{background:#fff;border:1px solid #d9eaf4;border-radius:12px;padding:11px 13px;margin:5px 0}.patent-result-row small{color:#6e91a7}.patent-result-row strong{display:block;color:#15476e;font-size:14px;margin-top:5px}.patent-result-row p{font-size:12px;color:#7893a5;margin:4px 0 0}
    .patent-analysis-chip{display:inline-block;background:#e8f5fc;border:1px solid #cce8f5;border-radius:999px;color:#2479a8;padding:5px 10px;font-size:12px;margin-right:6px}
    </style>""", unsafe_allow_html=True)


def render_patent_workbench() -> None:
    data = load_patents()
    coverage = load_coverage()
    records = data["records"]
    _workbench_css()
    section_title("PATENT DATABASE", "北极专利检索与态势分析", "以公开文本为证据入口：先检索单条专利并核对来源，再查看公开年份、公开局和技术主题分布。")
    st.caption("公开文本数量不等于独立发明数量；公开局／文献所属国家不等同于申请人国籍。公开年份默认用于趋势，优先权年份只在字段存在时进入统计。")

    countries = sorted({_country(r) for r in records})
    technologies = sorted({r.get("technology", "未分类") for r in records})
    public_years = sorted({_chart_year(r, "公开年份") for r in records if _chart_year(r, "公开年份")})
    priority_years = sorted({_chart_year(r, "最早优先权年份") for r in records if _chart_year(r, "最早优先权年份")})
    basis = st.selectbox("统计日期口径", ["公开年份", "最早优先权年份"], key="patent-chart-date")
    available_years = public_years if basis == "公开年份" else priority_years
    min_year, max_year = min(available_years), max(available_years)
    with st.container(border=True):
        st.markdown("#### 统一筛选条件")
        q1, q2, q3 = st.columns([1.6, 1, 1])
        query = q1.text_input("关键词", placeholder="标题、申请人、公开号、摘要、分类号", key="patent-query")
        country = q2.selectbox("公开局／文献所属国家或地区", ["全部公开局／地区", *countries], key="patent-country")
        technology = q3.selectbox("技术类别", ["全部技术类别", *technologies], key="patent-technology")
        year_range = st.slider(f"{basis}范围", min_year, max_year, (min_year, max_year), key="patent-years")
        with st.expander("高级筛选与结果排序"):
            f1, f2, f3 = st.columns(3)
            text_status = f1.selectbox("摘要状态", ["全部摘要", "公开中文原文", "中文译文", "未提供摘要"], key="patent-text-status")
            date_only = f2.checkbox("只看当前日期口径已具备记录", value=False, key="patent-date-verified")
            sort_mode = f3.selectbox("结果排序", ["信息完整度（高到低）", "公开日期（新到旧）", "最早优先权（新到旧）", "标题"], key="patent-sort")

    filtered = _sort_records(_filter_records(records, country, technology, basis, year_range, query, text_status, date_only), sort_mode)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("匹配公开文本", f"{len(filtered):,}")
    m2.metric("公开局／地区", len({_country(r) for r in filtered}))
    m3.metric("技术主题", len({_topic_group(r) for r in filtered}))
    m4.metric("日期覆盖", f"{sum(_chart_year(r, basis) is not None for r in filtered):,}/{len(filtered):,}")
    tabs = st.tabs(["专利检索工作台", "专利态势分析"])

    with tabs[0]:
        st.markdown("<div class='patent-workbench-note'><b>检索工作台</b><span>左侧浏览结果，右侧阅读摘要、首项权利要求、分类号、发明人和来源。完整字段缺失会明确标注。</span></div>", unsafe_allow_html=True)
        if not filtered:
            st.warning("没有匹配记录，请放宽关键词、公开局、技术类别或日期范围。")
        else:
            page_size = 10
            page_count = max(1, (len(filtered) + page_size - 1) // page_size)
            page = st.number_input("结果页", 1, page_count, 1, key="patent-result-page", label_visibility="collapsed")
            page_records = filtered[(int(page) - 1) * page_size:int(page) * page_size]
            left, right = st.columns([1.05, 1], gap="large")
            with left:
                st.markdown(f"#### 检索结果 <small>（{len(filtered):,} 条 · 第 {int(page)}/{page_count} 页）</small>", unsafe_allow_html=True)
                labels = [f"{r['publication_number']} · {r.get('title_zh') or r.get('title') or '标题未提供'}" for r in page_records]
                selected = None
                if labels:
                    selected_label = st.radio("选择一项查看详情", labels, key="patent-result-choice", label_visibility="collapsed")
                    selected = page_records[labels.index(selected_label)]
                    st.dataframe(pd.DataFrame([{"公开号": r["publication_number"], "公开局／地区": _country(r), "公开日": r.get("publication_date") or "未提供", "技术主题": _topic_group(r), "状态": r.get("verification_status") or "未标注"} for r in page_records]), hide_index=True, width="stretch", height=400)
            with right:
                if selected:
                    _record_panel(selected, "patent-workbench-record")
        st.download_button("下载当前检索结果 · JSON", json.dumps({**data, "records": filtered}, ensure_ascii=False, indent=2), "arctic-patents-filtered.json", "application/json", key="patent-database-download", on_click="ignore")

    with tabs[1]:
        st.markdown("<div class='patent-workbench-note'><b>态势分析</b><span>所有图表使用当前筛选条件。公开年份默认覆盖较完整；切换最早优先权年份后，缺失字段会明确减少可绘制样本。</span></div>", unsafe_allow_html=True)
        st.subheader(f"按{basis}统计的年度公开文本趋势")
        show_chart(_trend_figure(filtered, basis), key="patent-trend")
        st.caption(f"当前口径可绘制 {sum(_chart_year(r, basis) is not None for r in filtered):,}/{len(filtered):,} 条；缺失日期不补值。柱状图统计公开文本，不代表专利族数量。")
        heat_left, heat_right = st.columns(2, gap="large")
        with heat_left:
            st.markdown("#### 公开局／地区 × 年份")
            show_chart(_heatmap_figure(filtered, "国家", "公开局／地区", basis), key="patent-country-heatmap")
        with heat_right:
            st.markdown("#### 技术主题 × 年份")
            topic_records = [{**r, "technology": _topic_group(r)} for r in filtered]
            show_chart(_heatmap_figure(topic_records, "技术类别", "技术主题", basis), key="patent-technology-heatmap")
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            st.markdown("#### 技术主题分布")
            show_chart(_topic_figure(filtered), key="patent-topic-distribution")
        with chart_right:
            st.markdown("#### 申请人／机构 Top 10（字段存在时）")
            with_applicant = [r for r in filtered if r.get("assignee")]
            show_chart(_applicant_figure(with_applicant), key="patent-applicant-top")
        st.markdown("#### 当前筛选下的代表性公开文本")
        representative = _sort_records(filtered, "信息完整度（高到低）")[:10]
        st.dataframe(pd.DataFrame([{"公开号": r["publication_number"], "标题": r.get("title_zh") or r.get("title", ""), "公开局／地区": _country(r), "技术主题": _topic_group(r), "公开日": r.get("publication_date") or "未提供", "来源": r["source_url"]} for r in representative]), hide_index=True, width="stretch", column_config={"来源": st.column_config.LinkColumn("来源", display_text="打开公开页")})

    with st.expander("数据库口径与限制"):
        st.write(data["source_note"])
        st.write("当前详情库由公开文本组成；优先权日期、申请人、法律状态、专利族和权利要求的完整度不同。公开局／文献所属国家用于描述文献分布，不直接代表申请人国籍或技术实力。")
        st.write(coverage.get("definition", ""))
        st.link_button("打开统计来源", coverage["source_url"])
