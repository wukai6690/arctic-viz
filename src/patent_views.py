"""Standalone, source-linked Arctic technology patent database."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import ROOT, section_title, show_chart

DATA_PATH = ROOT / "data/analysis/patents/patents.json"
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
}


@st.cache_data(show_spinner=False)
def load_patents() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _country(record: dict) -> str:
    return COUNTRY_NAMES.get(record.get("country", ""), record.get("country", "未注明国家"))


def _year(record: dict) -> int | None:
    try:
        return int(str(record.get("priority_date", ""))[:4])
    except (TypeError, ValueError):
        return None


def _search_text(record: dict) -> str:
    return " ".join(str(record.get(k, "")) for k in ("publication_number", "title", "technology", "country", "assignee", "abstract", "claim_1", "classifications")).casefold()


def _trend_figure(records: list[dict]) -> go.Figure:
    frame = pd.DataFrame([{"年份": _year(r), "国家": _country(r), "专利族/公开文本": 1} for r in records if _year(r)])
    fig = go.Figure()
    if not frame.empty:
        grouped = frame.groupby(["年份", "国家"], as_index=False)["专利族/公开文本"].sum()
        for country, rows in grouped.groupby("国家"):
            fig.add_trace(go.Scatter(x=rows["年份"], y=rows["专利族/公开文本"], mode="lines+markers", name=country))
    fig.update_layout(height=360, margin={"l": 45, "r": 20, "t": 25, "b": 45}, xaxis_title="最早优先权年份", yaxis_title="记录数", hovermode="x unified")
    return fig


def _heatmap_figure(records: list[dict], row_key: str, row_label: str) -> go.Figure:
    rows = [{"国家": _country(r), "技术类别": r.get("technology", "未分类"), "年份": _year(r)} for r in records if _year(r)]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return go.Figure()
    if row_key == "国家":
        pivot = frame.pivot_table(index="国家", columns="年份", values="技术类别", aggfunc="size", fill_value=0)
    else:
        pivot = frame.pivot_table(index="技术类别", columns="年份", values="国家", aggfunc="size", fill_value=0)
    fig = go.Figure(go.Heatmap(z=pivot.values, x=[str(x) for x in pivot.columns], y=list(pivot.index), colorscale=[[0, "#f1f4ef"], [0.45, "#9db7a5"], [1, "#3f745d"]], colorbar={"title": "记录数"}, hovertemplate="%{y}<br>%{x}：%{z} 条<extra></extra>"))
    fig.update_layout(height=max(300, 34 * len(pivot.index) + 100), margin={"l": 125, "r": 25, "t": 30, "b": 55}, xaxis_title="最早优先权年份", yaxis_title=row_label)
    return fig


def _record_panel(record: dict, key: str) -> None:
    year = _year(record)
    st.markdown(f"### {record.get('title') or record.get('publication_number')}")
    st.caption(f"{record['publication_number']} · {_country(record)} · {record.get('technology', '未分类')} · 最早优先权 {record.get('priority_date', '未注明')}")
    m1, m2, m3 = st.columns(3)
    m1.metric("申请人", record.get("assignee") or "未注明")
    m2.metric("公开日期", record.get("publication_date") or "未注明")
    m3.metric("法律状态字段", record.get("status") or "页面未注明")
    st.link_button("打开官方专利页面", record["source_url"])
    st.markdown("**官方摘要（公开页面原文）**")
    st.write(record.get("abstract") or "该页面未提供可提取摘要。")
    with st.expander("查看首项权利要求"):
        st.write(record.get("claim_1") or "该页面未提取到首项权利要求。")
    with st.expander("查看分类号与发明人"):
        st.write("分类号：" + ("、".join(record.get("classifications", [])) or "页面未注明"))
        st.write("发明人：" + ("、".join(record.get("inventors", [])) or "页面未注明"))
    st.caption("摘要和权利要求来自公开专利页面；本站没有据此判断技术已经在北极项目中部署。")


def render_patent_database() -> None:
    data = load_patents()
    records = data["records"]
    section_title("专利数据库", "北极技术专利与公开文本", "按国家、技术类别和优先权年份查看样本趋势；每条记录保留官方摘要、首项权利要求和来源页面。")
    st.caption("当前数据库是人工筛选的北极技术相关公开专利样本，不代表完整专利总量或国家技术实力排名。")
    countries = sorted({_country(r) for r in records})
    technologies = sorted({r.get("technology", "未分类") for r in records})
    years = sorted({_year(r) for r in records if _year(r)})
    c1, c2, c3 = st.columns(3)
    country = c1.selectbox("国家", ["全部国家", *countries], key="patent-country")
    technology = c2.selectbox("技术类别", ["全部类别", *technologies], key="patent-technology")
    year_range = c3.slider("最早优先权年份", min(years), max(years), (min(years), max(years)), key="patent-years")
    query = st.text_input("检索专利", placeholder="标题、申请人、专利号、摘要关键词或分类号", key="patent-query").strip().casefold()
    filtered = [r for r in records if (country == "全部国家" or _country(r) == country) and (technology == "全部类别" or r.get("technology") == technology) and (_year(r) is not None and year_range[0] <= _year(r) <= year_range[1]) and (not query or query in _search_text(r))]
    m1, m2, m3 = st.columns(3)
    m1.metric("匹配公开文本", len(filtered))
    m2.metric("覆盖国家", len({_country(r) for r in filtered}))
    m3.metric("技术类别", len({r.get("technology") for r in filtered}))
    if not filtered:
        st.warning("没有匹配记录，请放宽国家、年份或关键词。")
        return
    tabs = st.tabs(["国家与年份趋势", "热力图", "专利记录"])
    with tabs[0]:
        st.subheader("不同国家的优先权年份趋势")
        show_chart(_trend_figure(filtered), key="patent-trend")
        st.caption("这里统计的是纳入数据库的公开文本记录，不是完整专利申请量。优先权年份用于避免把同族后续公开日误当成新发明。")
        st.dataframe(pd.DataFrame([{"国家": _country(r), "最早优先权年份": _year(r), "记录数": 1} for r in filtered]).groupby(["国家", "最早优先权年份"], as_index=False).sum(), hide_index=True, width="stretch")
    with tabs[1]:
        st.subheader("国家—年份热力图")
        show_chart(_heatmap_figure(filtered, "国家", "国家"), key="patent-country-heatmap")
        st.subheader("技术类别—年份热力图")
        show_chart(_heatmap_figure(filtered, "技术类别", "技术类别"), key="patent-technology-heatmap")
    with tabs[2]:
        rows = [{"公开号": r["publication_number"], "国家": _country(r), "最早优先权": r.get("priority_date", ""), "公开日": r.get("publication_date", ""), "技术类别": r.get("technology", ""), "申请人": r.get("assignee", ""), "标题": r.get("title", ""), "官方页面": r["source_url"]} for r in filtered]
        st.dataframe(rows, hide_index=True, width="stretch", column_config={"官方页面": st.column_config.LinkColumn("官方页面", display_text="打开专利页")})
        labels = [f"{r['publication_number']} · {r.get('title', '')}" for r in filtered]
        selected_label = st.selectbox("选择一项查看官方摘要与权利要求", labels, key="patent-record-choice")
        _record_panel(filtered[labels.index(selected_label)], "patent-record")
    with st.expander("数据库口径与限制"):
        st.write(data["source_note"])
        st.write("纳入方向：冰区船舶与破冰、北极航线规划、海冰风险、浮冰预测、极区卫星地面站和数据中继。后续可按 CPC 分类号、关键词和申请人继续扩充，并记录排除理由。")
        st.download_button("下载当前专利数据库 · JSON", json.dumps({**data, "records": filtered}, ensure_ascii=False, indent=2), "arctic-patents-filtered.json", "application/json", key="patent-database-download", on_click="ignore")
