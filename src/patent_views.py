"""Standalone, source-linked Arctic technology patent database."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import ROOT, section_title, show_chart

DATA_PATH = ROOT / "data/analysis/patents/patents.json"
COVERAGE_PATH = ROOT / "data/analysis/patents/coverage.json"
COUNTRY_NAMES = {
    "China": "中国",
    "United States": "美国",
    "South Korea": "韩国",
    "Finland": "芬兰",
    "France": "法国",
    "Germany": "德国",
    "Japan": "日本",
    "Russia": "俄罗斯",
    "Sweden": "瑞典",
    "Norway": "挪威",
    "Australia": "澳大利亚",
    "India": "印度",
    "United Kingdom": "英国",
    "WIPO": "世界知识产权组织",
}


@st.cache_data(show_spinner=False)
def load_patents() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_coverage() -> dict:
    return json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))


def _country(record: dict) -> str:
    return COUNTRY_NAMES.get(record.get("country", ""), record.get("country", "未注明国家"))


def _year(record: dict) -> int | None:
    try:
        return int(str(record.get("priority_date", ""))[:4])
    except (TypeError, ValueError):
        return None


def _chart_year(record: dict, basis: str) -> int | None:
    field = "publication_date" if basis == "公开年份" else "priority_date"
    try:
        return int(str(record.get(field, ""))[:4])
    except (TypeError, ValueError):
        return None


def _search_text(record: dict) -> str:
    return " ".join(str(record.get(k, "")) for k in ("publication_number", "title", "title_zh", "technology", "country", "assignee", "abstract", "abstract_original", "abstract_zh", "claim_1", "classifications")).casefold()


def _sort_records(records: list[dict], mode: str) -> list[dict]:
    if mode == "信息完整度（高到低）":
        return sorted(records, key=lambda r: (_completeness_score(r), r.get("publication_number", "")), reverse=True)
    if mode == "标题":
        return sorted(records, key=lambda r: (r.get("title_zh") or r.get("title") or "").casefold())
    field = "publication_date" if mode == "公开日期（新到旧）" else "priority_date"
    return sorted(records, key=lambda r: (r.get(field) or "0000-00-00", r.get("publication_number", "")), reverse=True)


def _completeness_score(record: dict) -> int:
    """Score only fields actually present on the public page; never infer missing facts."""
    score = 0
    score += 1 if record.get("title_zh") or record.get("title") else 0
    score += 3 if record.get("abstract_zh_source") in {"专利公开中文原文", "基于公开摘要的中文译文"} else 0
    score += 1 if record.get("priority_date") else 0
    score += 1 if record.get("publication_date") else 0
    score += 1 if record.get("assignee") else 0
    score += 1 if record.get("inventors") else 0
    score += 1 if record.get("claim_1") else 0
    score += 1 if record.get("classifications") else 0
    score += 1 if record.get("status") else 0
    return score


def _trend_figure(records: list[dict], basis: str) -> go.Figure:
    frame = pd.DataFrame([{"年份": _chart_year(r, basis), "国家": _country(r), "公开文本数": 1} for r in records if _chart_year(r, basis)])
    fig = go.Figure()
    if not frame.empty:
        grouped = frame.groupby(["年份", "国家"], as_index=False)["公开文本数"].sum()
        for country, rows in grouped.groupby("国家"):
            fig.add_trace(go.Bar(x=rows["年份"], y=rows["公开文本数"], name=country, hovertemplate=f"{country}<br>%{{x}}：%{{y}} 条<extra></extra>"))
    fig.update_layout(height=360, barmode="stack", margin={"l": 45, "r": 20, "t": 25, "b": 45}, xaxis_title=basis, yaxis_title="公开文本数", hovermode="x unified", legend={"orientation": "h", "y": 1.12})
    return fig


def _heatmap_figure(records: list[dict], row_key: str, row_label: str, basis: str) -> go.Figure:
    rows = [{"国家": _country(r), "技术类别": r.get("technology", "未分类"), "年份": _chart_year(r, basis)} for r in records if _chart_year(r, basis)]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return go.Figure()
    if row_key == "国家":
        pivot = frame.pivot_table(index="国家", columns="年份", values="技术类别", aggfunc="size", fill_value=0)
    else:
        pivot = frame.pivot_table(index="技术类别", columns="年份", values="国家", aggfunc="size", fill_value=0)
    # A restrained light-blue scale keeps zero cells quiet and high counts legible.
    text = pivot.astype(int).astype(str).values
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 11, "color": "#244e5b"},
        x=[str(x) for x in pivot.columns],
        y=list(pivot.index),
        zmin=0,
        colorscale=[[0.0, "#f3f8fb"], [0.25, "#d9edf2"], [0.5, "#a8ced4"], [0.75, "#6ca3ad"], [1.0, "#397786"]],
        colorbar={"title": "记录数", "tickformat": "d"},
        hovertemplate="%{y}<br>%{x}：%{z} 条<extra></extra>",
        xgap=1,
        ygap=1,
    ))
    fig.update_layout(height=max(300, 34 * len(pivot.index) + 100), margin={"l": 125, "r": 25, "t": 30, "b": 55}, xaxis_title=basis, yaxis_title=row_label)
    return fig


def _record_panel(record: dict, key: str) -> None:
    year = _year(record)
    st.markdown(f"### {record.get('title_zh') or record.get('title') or record.get('publication_number')}")
    st.caption(f"{record['publication_number']} · {_country(record)} · {record.get('technology', '未分类')} · 最早优先权 {record.get('priority_date') or '未核实'}")
    m1, m2, m3 = st.columns(3)
    m1.metric("申请人", record.get("assignee") or "官方页未提取")
    m2.metric("公开日期", record.get("publication_date") or "官方页未提取")
    m3.metric("法律状态字段", record.get("status") or "官方页未提取")
    st.link_button("打开官方专利页面", record["source_url"])
    source_label = record.get("abstract_zh_source") or ("公开英文摘要（原文）" if record.get("abstract_original") else "公开页面未提供摘要")
    st.markdown(f"**摘要（{source_label}）**")
    st.write(record.get("abstract_zh") or record.get("abstract_original") or "该公开页面未提供可提取摘要。")
    if not record.get("abstract_zh") and record.get("abstract_original"):
        st.info("该补充记录保留了公开页面的原始摘要；尚未额外生成中文译文。")
    if record.get("abstract_original") and record.get("abstract_original") != record.get("abstract_zh"):
        with st.expander("查看原始摘要文本（核对用）"):
            st.write(record["abstract_original"])
    with st.expander("查看首项权利要求"):
        st.write(record.get("claim_1") or "该页面未提取到首项权利要求。")
    with st.expander("查看分类号与发明人"):
        st.write("分类号：" + ("、".join(record.get("classifications", [])) or "页面未注明"))
        st.write("发明人：" + ("、".join(record.get("inventors", [])) or "页面未注明"))
    st.caption("中文摘要优先采用专利公开页面的中文原文；其他记录标注为中文译文，并保留原始摘要供核对。本站没有据此判断技术已经在北极项目中部署。")


def render_patent_database() -> None:
    data = load_patents()
    coverage = load_coverage()
    records = data["records"]
    section_title("专利数据库", "北极技术专利与公开文本", "先看广义关联专利覆盖量，再检索已经整理为可阅读详情的公开文本。")
    st.caption("广义覆盖量来自公开研究报告的引用统计；详情库只纳入已保留公开号、来源页和中文摘要的公开文本。两者口径不同，不用于直接比较国家技术实力。")
    c0, c1, c2 = st.columns(3)
    c0.metric("广义关联专利文献", f"{coverage.get('total_documents', 0):,}")
    c1.metric("当前可检索详情", f"{len(records):,}")
    c2.metric("2015 年广义新增", f"{coverage.get('year_2015_documents', 0):,}")
    with st.expander("总量口径与详情库边界", expanded=False):
        st.write(coverage.get("definition", ""))
        st.write(coverage.get("scope_note", ""))
        st.link_button("打开统计来源", coverage["source_url"])
        st.dataframe(pd.DataFrame([{"登记机构": k, "文献数": v} for k, v in coverage.get("office_breakdown", {}).items()]), hide_index=True, width="stretch")
    countries = sorted({_country(r) for r in records})
    technologies = sorted({r.get("technology", "未分类") for r in records})
    years = sorted({_year(r) for r in records if _year(r)})
    c1, c2, c3 = st.columns(3)
    country = c1.selectbox("国家", ["全部国家", *countries], key="patent-country")
    technology = c2.selectbox("技术类别", ["全部类别", *technologies], key="patent-technology")
    year_range = c3.slider("最早优先权年份", min(years), max(years), (min(years), max(years)), key="patent-years")
    query = st.text_input("检索专利", placeholder="标题、申请人、专利号、摘要关键词或分类号", key="patent-query").strip().casefold()
    chart_basis = st.selectbox("图表日期口径", ["最早优先权年份", "公开年份"], key="patent-chart-date")
    filtered = [r for r in records if (country == "全部国家" or _country(r) == country) and (technology == "全部类别" or r.get("technology") == technology) and (_year(r) is None or year_range[0] <= _year(r) <= year_range[1]) and (not query or query in _search_text(r))]
    with st.expander("检索口径", expanded=False):
        st.write("关键词会同时检索公开号、中文/原文标题、申请人、摘要、首项权利要求和分类号。年份筛选使用最早优先权日；未核实日期的记录仍保留在结果中，但不进入趋势图和热力图。")
        st.write("详情库当前尚未为全部记录补齐专利族编号，因此趋势图和热力图统计的是公开文本数，不把同族文本冒充为独立发明数量。")
    f1, f2, f3 = st.columns(3)
    text_status = f1.selectbox("摘要状态", ["全部摘要", "公开中文原文", "中文译文", "未提供摘要"], key="patent-text-status")
    date_only = f2.checkbox("只看已核实优先权日", key="patent-date-verified")
    sort_mode = f3.selectbox("结果排序", ["信息完整度（高到低）", "最早优先权（新到旧）", "公开日期（新到旧）", "标题"], key="patent-sort")
    if text_status == "公开中文原文":
        filtered = [r for r in filtered if r.get("abstract_zh_source") == "专利公开中文原文"]
    elif text_status == "中文译文":
        filtered = [r for r in filtered if r.get("abstract_zh_source") == "基于公开摘要的中文译文"]
    elif text_status == "未提供摘要":
        filtered = [r for r in filtered if r.get("abstract_zh_source") == "公开页面未提供摘要"]
    if date_only:
        filtered = [r for r in filtered if _year(r) is not None]
    filtered = _sort_records(filtered, sort_mode)
    m1, m2, m3 = st.columns(3)
    m1.metric("匹配公开文本", len(filtered))
    m2.metric("覆盖国家", len({_country(r) for r in filtered}))
    m3.metric("技术类别", len({r.get("technology") for r in filtered}))
    st.markdown(f'<div class="patent-focus"><div><small>PATENT ANALYSIS WORKSPACE</small><b>国家与年份趋势</b><span>看公开文本如何随年份和国家分布</span></div><div><b>热力图</b><span>看国家 × 技术方向的集中区域</span></div><div><b>专利记录</b><span>直接打开公开号、摘要与官方页面</span></div><strong>{len(filtered):,}<em> 条当前结果</em></strong></div>', unsafe_allow_html=True)
    q1, q2, q3, q4, q5, q6 = st.columns(6)
    q1.metric("中文公开原文", sum(r.get("abstract_zh_source") == "专利公开中文原文" for r in filtered))
    q2.metric("中文译文", sum(r.get("abstract_zh_source") == "基于公开摘要的中文译文" for r in filtered))
    q3.metric("优先权日已核实", sum(_year(r) is not None for r in filtered))
    q4.metric("公开日已核实", sum(bool(r.get("publication_date")) for r in filtered))
    q5.metric("申请人/状态", sum(bool(r.get("assignee")) and bool(r.get("status")) for r in filtered))
    q6.metric("含首项权利要求", sum(bool(r.get("claim_1")) for r in filtered))
    chart_count = sum(_chart_year(r, chart_basis) is not None for r in filtered)
    st.caption(f"完整度排序按公开页实际字段计算；当前最高分 {max((_completeness_score(r) for r in filtered), default=0)}/11。图表可用 {chart_count}/{len(filtered)} 条记录，缺失日期不补值。")
    if not filtered:
        st.warning("没有匹配记录，请放宽国家、年份、摘要状态或关键词。")
        return
    tabs = st.tabs(["国家与年份趋势", "热力图", "专利记录"])
    with tabs[0]:
        st.subheader(f"按{chart_basis}统计的公开文本趋势")
        show_chart(_trend_figure(filtered, chart_basis), key="patent-trend")
        st.caption("柱高表示该年度纳入详情库的公开文本数；不同国家堆叠显示。该图不等于完整国家专利申请量，也不等于去重后的专利族数量。")
        trend_rows = [{"国家": _country(r), "年份": _chart_year(r, chart_basis), "公开文本数": 1} for r in filtered if _chart_year(r, chart_basis)]
        if trend_rows:
            st.dataframe(pd.DataFrame(trend_rows).groupby(["国家", "年份"], as_index=False).sum(), hide_index=True, width="stretch")
        else:
            st.info("当前日期口径没有可绘制的记录，请切换日期口径或放宽筛选条件。")
    with tabs[1]:
        st.subheader("国家—年份热力图")
        show_chart(_heatmap_figure(filtered, "国家", "国家", chart_basis), key="patent-country-heatmap")
        st.caption("每个格子已直接标出记录数；浅蓝色表示记录较少，深蓝色表示记录较多。缺失日期的记录不会进入热力图。")
        st.subheader("技术类别—年份热力图")
        show_chart(_heatmap_figure(filtered, "技术类别", "技术类别", chart_basis), key="patent-technology-heatmap")
    with tabs[2]:
        rows = [{"公开号": r["publication_number"], "国家": _country(r), "最早优先权": r.get("priority_date", "") or "官方页未提取", "公开日": r.get("publication_date", "") or "官方页未提取", "技术类别": r.get("technology", ""), "申请人": r.get("assignee", "") or "官方页未提取", "摘要来源": r.get("abstract_zh_source", ""), "完整度": f"{_completeness_score(r)}/11", "标题": r.get("title_zh") or r.get("title", ""), "官方页面": r["source_url"]} for r in filtered]
        st.dataframe(rows, hide_index=True, width="stretch", column_config={"官方页面": st.column_config.LinkColumn("官方页面", display_text="打开专利页")})
        labels = [f"{r['publication_number']} · {r.get('title_zh') or r.get('title', '')}" for r in filtered]
        selected_label = st.selectbox("选择一项查看官方摘要与权利要求", labels, key="patent-record-choice")
        _record_panel(filtered[labels.index(selected_label)], "patent-record")
    with st.expander("数据库口径与限制"):
        st.write(data["source_note"])
        st.write("纳入方向：冰区船舶与破冰、北极航线规划、海冰风险、浮冰预测、极区卫星地面站和数据中继。后续可按 CPC 分类号、关键词和申请人继续扩充，并记录排除理由。")
        st.download_button("下载当前专利数据库 · JSON", json.dumps({**data, "records": filtered}, ensure_ascii=False, indent=2), "arctic-patents-filtered.json", "application/json", key="patent-database-download", on_click="ignore")
