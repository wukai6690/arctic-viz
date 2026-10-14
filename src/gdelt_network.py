"""Interactive, source-linked GDELT country-pair network views."""
from __future__ import annotations

import json
import math
from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
from src.presentation import ROOT, show_chart, section_title
from src.source_library import source_button

DATA_PATH = ROOT / "data/analysis/gdelt/network/network.json"


@st.cache_data(show_spinner=False)
def load_network() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _positions(countries: list[dict]) -> dict[str, tuple[float, float]]:
    # Stable positions make changes between time slices readable.
    n = len(countries)
    return {c["code"]: (math.cos(2 * math.pi * i / n - math.pi / 2), math.sin(2 * math.pi * i / n - math.pi / 2)) for i, c in enumerate(countries)}


def _edge_color(edge: dict) -> str:
    value = edge.get("goldstein_mean")
    if value is None or abs(value) < 0.8:
        return "#82968b"
    return "#4c8b73" if value > 0 else "#bd665d"


def network_figure(window: dict, countries: list[dict], min_events: int = 1) -> go.Figure:
    positions = _positions(countries)
    edges = [edge for edge in window["edges"] if edge["event_count"] >= min_events]
    edge_traces = []
    for edge in edges:
        x1, y1 = positions[edge["source"]]; x2, y2 = positions[edge["target"]]
        width = max(1.0, min(12.0, 1.3 + 2.0 * math.log1p(edge["article_count"] or edge["event_count"])))
        value = edge.get("goldstein_mean")
        polarity = "合作倾向" if value is not None and value > 0 else "冲突倾向" if value is not None and value < 0 else "中性/未定"
        text = (f"{edge['source']} ↔ {edge['target']}<br>事件 {edge['event_count']:,} 条 · 新闻文章 {edge['article_count']:,} 篇"
                f"<br>{polarity} · Goldstein 均值 {value:+.2f}" if value is not None else
                f"{edge['source']} ↔ {edge['target']}<br>事件 {edge['event_count']:,} 条 · 新闻文章 {edge['article_count']:,} 篇<br>{polarity}")
        edge_traces.append(go.Scatter(x=[x1, x2], y=[y1, y2], mode="lines", line={"width": width, "color": _edge_color(edge)},
                                      hovertemplate=text + "<extra></extra>", showlegend=False, customdata=[edge["source"] + "|" + edge["target"]]))
    country_by_code = {c["code"]: c for c in countries}
    nodes = window["nodes"]
    max_degree = max((n["event_degree"] for n in nodes), default=1)
    role_colors = {"观察国": "#b9625f", "北极国家": "#4f806d"}
    node_trace = go.Scatter(
        x=[positions[n["code"]][0] for n in nodes], y=[positions[n["code"]][1] for n in nodes],
        mode="markers+text", text=[country_by_code[n["code"]]["name"] for n in nodes], textposition="top center",
        textfont={"size": 13, "color": "#294b42"},
        marker={"size": [17 + 30 * math.sqrt(n["event_degree"] / max_degree) if max_degree else 17 for n in nodes],
                "color": [role_colors.get(n["role"], "#7d83a7") for n in nodes], "line": {"width": 1.5, "color": "#ffffff"}},
        customdata=[[n["code"], n["event_degree"], n["article_degree"]] for n in nodes],
        hovertemplate="%{text} (%{customdata[0]})<br>事件度数：%{customdata[1]:,}<br>关联新闻文章：%{customdata[2]:,}<extra></extra>",
        name="国家节点",
    )
    fig = go.Figure(edge_traces + [node_trace])
    fig.update_layout(height=600, margin={"l": 25, "r": 25, "t": 35, "b": 25}, showlegend=False,
                      xaxis={"visible": False, "range": [-1.22, 1.22]}, yaxis={"visible": False, "range": [-1.18, 1.18]},
                      plot_bgcolor="#f5f7f3", paper_bgcolor="#f5f7f3", hovermode="closest")
    return fig


def trend_figure(data: dict) -> go.Figure:
    years = [w["year"] for w in data["windows"]]
    events = [len(w["events"]) for w in data["windows"]]
    relations = [len(w["edges"]) for w in data["windows"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=events, mode="lines+markers", name="事件记录数", line={"color": "#4f806d", "width": 2.5}))
    fig.add_trace(go.Scatter(x=years, y=relations, mode="lines+markers", name="国家对数量", line={"color": "#8d7ba2", "width": 2.5}))
    fig.update_layout(height=300, margin={"l": 45, "r": 20, "t": 25, "b": 45}, xaxis={"dtick": 1, "title": "时间切片"}, yaxis={"title": "样本记录"})
    return fig


def render_network(key: str = "network") -> None:
    data = load_network()
    countries = data["countries"]
    labels = [w["label"] for w in data["windows"]]
    by_label = {w["label"]: w for w in data["windows"]}
    section_title("DYNAMIC NETWORK", "北极国家地缘事件网络", "按 GDELT 时间切片查看国家互动记录如何变化，再回到具体事件和来源。")
    st.info("网络边表示选定 GDELT 日档/窗口内的机器编码事件聚合。线条更粗表示新闻文章记录更多；颜色表示 Goldstein 均值的合作或冲突倾向。它是新闻感知网络，不是外交关系强度或因果结论。")
    a, b, c = st.columns([1.4, 1, 1])
    frame_key = key + "-frame"
    current = st.session_state.get(frame_key, labels[min(1, len(labels) - 1)])
    min_events = b.selectbox("最少事件数", [1, 2, 5, 10], index=0, key=key + "-min")
    auto = c.checkbox("自动播放时间切片", value=False, key=key + "-auto", help="每秒推进一个已准备好的时间切片。")
    if auto:
        # Streamlit 1.57 fragments allow a small, self-contained playback loop.
        st.caption("自动播放只在已整理的样本窗口之间切换；不会在浏览器端重新抓取新闻。")
        @st.fragment(run_every="1s")
        def _advance():
            now = st.session_state.get(frame_key, labels[0])
            index = labels.index(now) if now in labels else 0
            st.session_state[frame_key] = labels[(index + 1) % len(labels)]
            st.rerun(scope="app")
        _advance()
        current = st.session_state.get(frame_key, current)
    choice = a.selectbox("网络时间切片", labels, index=labels.index(current) if current in labels else 0, key=key + "-window")
    if not auto:
        st.session_state[frame_key] = choice
    window = by_label[choice]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("时间范围", window["date_start"] + (" — " + window["date_end"] if window["date_end"] != window["date_start"] else ""))
    m2.metric("事件记录", f"{len(window['events']):,}")
    m3.metric("国家对", f"{len(window['edges']):,}")
    m4.metric("数据来源", window["source"]["dataset"])
    tabs = st.tabs(["关系网络", "时间演变", "关系明细与新闻证据", "方法与边界"])
    with tabs[0]:
        st.caption("节点位置固定，便于比较不同时间切片；节点大小按事件度数缩放。红边为负向 Goldstein 均值，绿边为正向，灰边接近中性。")
        show_chart(network_figure(window, countries, min_events), key=key + "-graph", config={"displayModeBar": True})
        st.caption("节点颜色：红色为中国观察国，绿色为北极国家，紫色为其他登记节点。点击或悬停查看事件数、文章数和均值。")
    with tabs[1]:
        st.subheader("样本窗口之间的变化")
        show_chart(trend_figure(data), key=key + "-trend")
        st.caption("当前数据是 2015、2019、2020、2025 的选定日档/短窗口，曲线用于展示网络构建方法，不应解释为完整年度趋势。")
        st.dataframe([{ "时间切片": w["label"], "事件记录": len(w["events"]), "国家对": len(w["edges"]), "窗口说明": w["sample_note"] } for w in data["windows"]], hide_index=True, width="stretch")
    with tabs[2]:
        options = {f"{e['source']} ↔ {e['target']} · {e['event_count']} 条事件": e for e in window["edges"] if e["event_count"] >= min_events}
        if not options:
            st.warning("当前阈值下没有国家对，请降低最少事件数。")
        else:
            selected_label = st.selectbox("选择一条国家关系", list(options), key=key + "-edge")
            edge = options[selected_label]
            a, b, c = st.columns(3)
            a.metric("事件记录", edge["event_count"])
            b.metric("新闻文章", edge["article_count"])
            c.metric("Goldstein 均值", "未计算" if edge["goldstein_mean"] is None else f"{edge['goldstein_mean']:+.2f}")
            st.write(f"覆盖日期：{edge['first_date']} 至 {edge['last_date']}；正向事件 {edge['positive_events']} 条，负向事件 {edge['negative_events']} 条。")
            rows = []
            wanted = set(edge["event_ids"])
            for event in window["events"]:
                if event["id"] not in wanted: continue
                rows.append({"日期": event["date"], "事件类型": event["category"], "编码": event["event_code"], "地点": event["location"], "Goldstein": event["goldstein"], "来源": event["source_url"]})
            st.dataframe(rows, hide_index=True, width="stretch", column_config={"来源": st.column_config.LinkColumn("来源", display_text="打开来源")})
            for i, row in enumerate(rows[:6]):
                if row["来源"].startswith(("http://", "https://")):
                    source_button(row["来源"], f"站内查看来源 {i + 1}", key=key + "-source-" + str(i))
    with tabs[3]:
        st.markdown("#### 当前样本如何生成")
        st.write(data["scope"])
        st.write("边的宽度使用事件涉及的新闻文章数；节点大小使用事件度数；颜色使用 QuadClass 合作/冲突与 Goldstein 均值。原始事件保留日期、参与者、事件编码、地点和来源链接。")
        st.markdown("#### 数据来源与下载")
        st.download_button("下载当前网络数据 · JSON", json.dumps({"metadata": data, "window": window}, ensure_ascii=False, indent=2), "gdelt-arctic-network-current.json", "application/json", key=key + "-download", on_click="ignore")
        for citation in data["citations"]:
            st.markdown(f"- [{citation['title']}]({citation['url']})")
        st.markdown("#### 使用边界")
        for limit in data["limitations"]: st.write("- " + limit)


def render_network_page() -> None:
    render_network("network-page")
