"""Interactive, source-linked GDELT country-pair network views."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
from src.presentation import ROOT, show_chart, section_title
from src.source_library import source_button

DATA_PATH = ROOT / "data/analysis/gdelt/network/network.json"

COUNTRY_LABELS = {
    "ALL": "全部国家",
    "CHN": "中国",
    "USA": "美国",
    "RUS": "俄罗斯",
    "CAN": "加拿大",
    "NOR": "挪威",
    "DNK": "丹麦",
    "FIN": "芬兰",
    "SWE": "瑞典",
    "ISL": "冰岛",
}

# CAMEO root event categories. The application keeps the code visible so that
# a search can be traced back to the GDELT codebook and to the evidence rows.
EVENT_TYPES = {
    "01": "公开声明",
    "02": "呼吁、求助",
    "03": "表达合作意向",
    "04": "协商、商议",
    "05": "开展外交合作",
    "06": "开展实质性合作",
    "07": "提供支持或援助",
    "08": "妥协",
    "09": "调查、查证",
    "10": "要求、请求",
    "11": "不赞成、不同意",
    "12": "拒绝",
    "13": "威胁、恐吓",
    "14": "抗议",
    "15": "展示武力",
    "16": "减少关系",
    "17": "胁迫",
    "18": "攻击",
    "19": "战斗或军事行动",
    "20": "大规模暴力",
}


@st.cache_data(show_spinner=False)
def load_network() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def event_type_code(event: dict) -> str:
    """Return the two-digit CAMEO root code used by the search panel."""
    code = str(event.get("event_code") or "")
    return code[:2] if len(code) >= 2 and code[:2].isdigit() else ""


def event_type_label(event: dict) -> str:
    code = event_type_code(event)
    return f"{code} · {EVENT_TYPES.get(code, event.get('category') or '未分类')}" if code else (event.get("category") or "未分类")


def all_events(data: dict) -> list[dict]:
    """Flatten the prepared windows while avoiding duplicate event IDs."""
    unique: dict[str, dict] = {}
    for window in data.get("windows", []):
        for event in window.get("events", []):
            unique.setdefault(event.get("id", f"{window['id']}:{len(unique)}"), event)
    return sorted(unique.values(), key=lambda row: (row.get("date", ""), row.get("id", "")))


def aggregate_events(events: list[dict], countries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Aggregate filtered event rows into the same edge/node schema as a window."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for event in events:
        a, b = event.get("actor1"), event.get("actor2")
        if not a or not b or a == b:
            continue
        groups[tuple(sorted((a, b)))].append(event)
    edges = []
    for (source, target), rows in sorted(groups.items()):
        gold = [r["goldstein"] for r in rows if r.get("goldstein") is not None]
        tones = [r["avg_tone"] for r in rows if r.get("avg_tone") is not None]
        edges.append({
            "source": source,
            "target": target,
            "event_count": len(rows),
            "article_count": sum(r.get("num_articles", 0) or 0 for r in rows),
            "mention_count": sum(r.get("num_mentions", 0) or 0 for r in rows),
            "source_count": sum(r.get("num_sources", 0) or 0 for r in rows),
            "positive_events": sum((r.get("quad_class") or 0) in (1, 2) for r in rows),
            "negative_events": sum((r.get("quad_class") or 0) in (3, 4) for r in rows),
            "goldstein_mean": round(sum(gold) / len(gold), 3) if gold else None,
            "tone_mean": round(sum(tones) / len(tones), 3) if tones else None,
            "first_date": min(r.get("date", "") for r in rows),
            "last_date": max(r.get("date", "") for r in rows),
            "categories": dict(Counter(event_type_label(r) for r in rows)),
            "event_ids": [r.get("id") for r in rows[:80]],
        })
    degree = Counter()
    articles = Counter()
    for edge in edges:
        degree[edge["source"]] += edge["event_count"]
        degree[edge["target"]] += edge["event_count"]
        articles[edge["source"]] += edge["article_count"]
        articles[edge["target"]] += edge["article_count"]
    nodes = [{"code": c["code"], "name": c.get("name", COUNTRY_LABELS.get(c["code"], c["code"])),
              "english": c.get("english", c["code"]), "role": c.get("role", "北极国家"),
              "event_degree": degree[c["code"]], "article_degree": articles[c["code"]]} for c in countries]
    return edges, nodes


def _parse_day(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def search_events(data: dict, start: date, end: date, country1: str, country2: str,
                  selected_types: list[str], keyword: str = "", ignore_direction: bool = False) -> list[dict]:
    """Apply the visible search filters to the prepared, auditable event sample."""
    needle = keyword.strip().casefold()
    wanted = set(selected_types)
    rows = []
    for event in all_events(data):
        try:
            event_day = _parse_day(event.get("date"))
        except (TypeError, ValueError):
            continue
        if event_day < start or event_day > end:
            continue
        a, b = event.get("actor1"), event.get("actor2")
        if country1 != "ALL" and a != country1 and (not ignore_direction or b != country1):
            continue
        if country2 != "ALL":
            if ignore_direction:
                if not ((a == country1 or country1 == "ALL") and b == country2) and not (a == country2 and (country1 == "ALL" or b == country1)):
                    continue
            elif b != country2:
                continue
        if wanted and event_type_code(event) not in wanted:
            continue
        if needle:
            haystack = " ".join(str(event.get(k, "")) for k in ("actor1", "actor2", "actor1_name", "actor2_name", "location", "source_url", "category")).casefold()
            if needle not in haystack:
                continue
        rows.append(event)
    return rows


def _positions(countries: list[dict], nodes: list[dict] | None = None) -> dict[str, tuple[float, float]]:
    """Place the core in the middle and the remaining countries in rings.

    The layout follows the comparison figures used in the reference study:
    positions stay fixed between slices, while node size and edge width carry
    the changing values. This makes the result read as a network analysis
    figure rather than a force-directed animation.
    """
    codes = [c["code"] for c in countries]
    core = [code for code in ("USA", "CHN", "RUS") if code in codes]
    semiperiphery = [code for code in ("CAN", "NOR", "DNK") if code in codes and code not in core]
    outer = [code for code in codes if code not in core and code not in semiperiphery]
    positions: dict[str, tuple[float, float]] = {}
    for i, code in enumerate(core):
        angle = 2 * math.pi * i / max(1, len(core)) - math.pi / 2
        positions[code] = (0.28 * math.cos(angle), 0.28 * math.sin(angle))
    for group, radius in ((semiperiphery, 0.72), (outer, 1.06)):
        for i, code in enumerate(group):
            angle = 2 * math.pi * i / max(1, len(group)) - math.pi / 2
            positions[code] = (radius * math.cos(angle), radius * math.sin(angle))
    return positions


def _edge_color(edge: dict) -> str:
    value = edge.get("goldstein_mean")
    if value is None or abs(value) < 0.8:
        return "#82968b"
    return "#4c8b73" if value > 0 else "#bd665d"


def network_figure(window: dict, countries: list[dict], min_events: int = 1) -> go.Figure:
    positions = _positions(countries, window.get("nodes"))
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
    group_colors = {"USA": "#c95f5a", "CHN": "#c95f5a", "RUS": "#c95f5a",
                    "CAN": "#4f9b61", "NOR": "#4f9b61", "DNK": "#4f9b61"}
    node_trace = go.Scatter(
        x=[positions[n["code"]][0] for n in nodes], y=[positions[n["code"]][1] for n in nodes],
        mode="markers+text", text=[country_by_code[n["code"]]["name"] for n in nodes], textposition="top center",
        textfont={"size": 13, "color": "#294b42"},
        marker={"size": [19 + 34 * math.sqrt(n["event_degree"] / max_degree) if max_degree else 19 for n in nodes],
                "color": [group_colors.get(n["code"], "#7773a8") for n in nodes], "line": {"width": 1.5, "color": "#ffffff"},
                "opacity": 0.88},
        customdata=[[n["code"], n["event_degree"], n["article_degree"]] for n in nodes],
        hovertemplate="%{text} (%{customdata[0]})<br>事件度数：%{customdata[1]:,}<br>关联新闻文章：%{customdata[2]:,}<extra></extra>",
        name="国家节点",
    )
    legend_traces = [
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 12, "color": "#c95f5a"}, name="核心国家"),
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 12, "color": "#4f9b61"}, name="半边缘国家"),
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 12, "color": "#7773a8"}, name="边缘登记节点"),
    ]
    fig = go.Figure(edge_traces + [node_trace] + legend_traces)
    fig.update_layout(height=620, margin={"l": 35, "r": 35, "t": 25, "b": 45}, showlegend=True,
                      legend={"orientation": "h", "y": -0.02, "x": 0.5, "xanchor": "center", "font": {"size": 12}},
                      xaxis={"visible": False, "range": [-1.25, 1.25]}, yaxis={"visible": False, "range": [-1.25, 1.25]},
                      plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", hovermode="closest")
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


def _search_result_window(data: dict, events: list[dict]) -> dict:
    edges, nodes = aggregate_events(events, data["countries"])
    return {
        "id": "search",
        "label": "条件检索结果",
        "year": None,
        "date_start": min((e.get("date", "") for e in events), default=""),
        "date_end": max((e.get("date", "") for e in events), default=""),
        "events": events,
        "edges": edges,
        "nodes": nodes,
        "source": {"dataset": "GDELT 1.0 / 2.0 准备样本"},
        "sample_note": "由页面检索条件从已整理的事件样本中过滤得到。",
    }


def render_search_panel(data: dict, countries: list[dict], key: str) -> dict | None:
    """Render a screenshot-like filter panel and return the submitted result."""
    events = all_events(data)
    dates = []
    for event in events:
        try:
            dates.append(_parse_day(event.get("date")))
        except (TypeError, ValueError):
            pass
    if not dates:
        st.error("当前网络样本没有可检索的日期记录。")
        return None
    min_day, max_day = min(dates), max(dates)
    state_key = key + "-search-result"
    with st.container(border=True):
        st.subheader("事件检索")
        st.caption("按日期、国家对、CAMEO 事件类型和关键词筛选已整理的 GDELT 事件。检索结果会同步生成下方网络图；当前不是实时抓取。")
        st.info(f"可检索事件日期：{min_day.isoformat()} 至 {max_day.isoformat()} · 去重后 {len(events):,} 条。2015 年起为 GDELT 2.0，2019 窗口沿用 GDELT 1.0 整理数据。")
        with st.form(key + "-search-form", clear_on_submit=False):
            d1, d2 = st.columns(2)
            start = d1.date_input("开始日期", value=min_day, min_value=min_day, max_value=max_day, key=key + "-start")
            end = d2.date_input("结束日期", value=max_day, min_value=min_day, max_value=max_day, key=key + "-end")
            c1, c2 = st.columns(2)
            choices = [("ALL", "全部国家")] + [(c["code"], COUNTRY_LABELS.get(c["code"], c.get("name", c["code"]))) for c in countries]
            country1 = c1.selectbox("国家或地区一（角色1）", choices, format_func=lambda x: x[1], key=key + "-country1")[0]
            country2 = c2.selectbox("国家或地区二（角色2）", choices, format_func=lambda x: x[1], key=key + "-country2")[0]
            selected = st.multiselect(
                "事件类型（CAMEO 根类别）",
                options=list(EVENT_TYPES),
                default=list(EVENT_TYPES),
                format_func=lambda code: f"{code} · {EVENT_TYPES[code]}",
                key=key + "-event-types",
                help="根类别对应 GDELT Event Codebook 的前两位；取消全选可缩小结果。",
            )
            q1, q2 = st.columns([2, 1])
            keyword = q1.text_input("关键词（地点、参与者或来源标题）", placeholder="例如 Arctic、Greenland、Svalbard", key=key + "-keyword")
            ignore_direction = q2.checkbox("忽略角色方向", value=False, key=key + "-direction", help="勾选后，中国—美国和美国—中国按同一国家对匹配。")
            submitted = st.form_submit_button("检索", type="primary", use_container_width=True)
        if submitted:
            if start > end:
                st.session_state[state_key] = {"error": "开始日期不能晚于结束日期。"}
            else:
                result = search_events(data, start, end, country1, country2, selected, keyword, ignore_direction)
                st.session_state[state_key] = {"events": result, "filters": {"start": start.isoformat(), "end": end.isoformat(), "country1": country1, "country2": country2}}
        result_state = st.session_state.get(state_key)
        if not result_state:
            st.caption("设置条件后点击“检索”。默认日期范围覆盖当前已经整理的全部事件样本。")
            return None
        if result_state.get("error"):
            st.warning(result_state["error"])
            return None
        result_events = result_state.get("events", [])
        if not result_events:
            st.warning("没有匹配记录。可以放宽日期、国家对或事件类型；日期范围只覆盖当前已整理的样本窗口。")
            return None
        filtered = _search_result_window(data, result_events)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("检索结果", f"{len(result_events):,} 条")
        s2.metric("国家对", f"{len(filtered['edges']):,} 对")
        s3.metric("新闻文章", f"{sum(e.get('num_articles', 0) or 0 for e in result_events):,} 篇")
        s4.metric("日期跨度", f"{filtered['date_start']}—{filtered['date_end']}")
        st.caption("结果表只显示事件证据字段；事件类型代码可回查 GDELT Codebook。网络图线宽按文章数缩放，颜色按 Goldstein 均值。")
        return filtered


def render_search_results(result: dict, countries: list[dict], key: str) -> None:
    """Show the network and evidence table produced by the standalone search."""
    st.subheader("检索结果网络")
    st.caption("这是当前条件对应的子网络。节点和边都来自筛选后的事件记录，下面保留可回查的事件字段。")
    show_chart(network_figure(result, countries), key=key + "-graph", config={"displayModeBar": True})
    rows = [{
        "日期": e.get("date", ""),
        "事件类型": event_type_label(e),
        "Goldstein": e.get("goldstein"),
        "AvgTone": e.get("avg_tone"),
        "角色1": f"{COUNTRY_LABELS.get(e.get('actor1'), e.get('actor1', ''))} · {e.get('actor1_name', '')}",
        "角色2": f"{COUNTRY_LABELS.get(e.get('actor2'), e.get('actor2', ''))} · {e.get('actor2_name', '')}",
        "地点": e.get("location", ""),
        "来源": e.get("source_url", ""),
    } for e in result["events"][:300]]
    st.dataframe(rows, hide_index=True, width="stretch", height=420)
    for i, row in enumerate(result["events"][:6]):
        if str(row.get("source_url", "")).startswith(("http://", "https://")):
            source_button(row["source_url"], f"站内查看检索证据 {i + 1}", key=key + "-source-" + str(i))


def render_search_page() -> None:
    data = load_network()
    section_title("事件检索", "按条件查找北极国家互动记录", "日期、国家角色和 CAMEO 事件类型先筛选记录，再生成国家关系网络。这里是独立检索功能，不和时间切片页面混在一起。")
    st.info("当前检索使用已经整理的 GDELT 日档与短窗口，不会在浏览器端实时抓取新闻。每条结果都保留事件日期、参与者、编码、地点和来源。")
    result = render_search_panel(data, data["countries"], "event-search")
    if result is not None:
        render_search_results(result, data["countries"], "event-search-result")


def render_network(key: str = "network") -> None:
    data = load_network()
    countries = data["countries"]
    labels = [w["label"] for w in data["windows"]]
    by_label = {w["label"]: w for w in data["windows"]}
    section_title("时间切片 · 社会网络分析", "北极国家地缘事件网络", "固定节点位置，对照不同时间窗口的核心—半边缘—边缘结构，再回到事件证据。")
    st.info("网络边表示选定 GDELT 日档/窗口内的机器编码事件聚合。线条更粗表示新闻文章记录更多；颜色表示 Goldstein 均值的合作或冲突倾向。它是新闻感知网络，不是外交关系强度或因果结论。")
    st.caption("需要按日期、国家和事件类型筛选时，请从左侧打开“事件检索”。")
    a, b, c = st.columns([1.4, 1, 1])
    frame_key = key + "-frame"
    current = st.session_state.get(frame_key, labels[min(1, len(labels) - 1)])
    min_events = b.selectbox("最少事件数", [1, 2, 5, 10], index=0, key=key + "-min")
    auto = c.checkbox("自动播放时间切片", value=False, key=key + "-auto", help="每秒推进一个已准备好的时间切片。")
    if auto:
        from streamlit_autorefresh import st_autorefresh
        ticks = st_autorefresh(interval=1000, key=key + "-autorefresh")
        current = labels[(int(ticks) + 1) % len(labels)]
        st.session_state[frame_key] = current
        st.caption("自动播放只在已整理的样本窗口之间切换；不会在浏览器端重新抓取新闻。")
    choice = a.selectbox("网络时间切片", labels, index=labels.index(current) if current in labels else 0)
    if not auto:
        st.session_state[frame_key] = choice
    window = by_label[choice]
    m1, m2, m3, m4 = st.columns(4)
    date_label = window["date_start"] if window["date_end"] == window["date_start"] else f"{window['date_start']}—{window['date_end'][-2:]}"
    m1.metric("时间范围", date_label)
    m2.metric("事件记录", f"{len(window['events']):,}")
    m3.metric("国家对", f"{len(window['edges']):,}")
    m4.metric("数据来源", window["source"]["dataset"])
    tabs = st.tabs(["关系网络", "多时间片对照", "时间演变", "关系明细与新闻证据", "方法与边界"])
    with tabs[0]:
        st.caption("节点位置固定，便于比较不同时间切片；节点大小按事件度数缩放。红边为负向 Goldstein 均值，绿边为正向，灰边接近中性。颜色分组沿用核心—半边缘—边缘的比较框架。")
        show_chart(network_figure(window, countries, min_events), key=key + "-graph", config={"displayModeBar": True})
        st.caption("节点颜色：红色为核心国家，绿色为半边缘国家，紫色为边缘登记节点。点击或悬停查看事件数、文章数和均值。")
    with tabs[1]:
        st.subheader("不同时间窗口的网络结构")
        st.caption("固定同一组国家位置，把四个已整理窗口并排放在一起；节点大小、边宽和颜色随窗口变化。它对应论文中多面板网络图的读法。")
        for offset in range(0, len(data["windows"]), 2):
            cols = st.columns(2, gap="large")
            for col, panel in zip(cols, data["windows"][offset:offset + 2]):
                with col:
                    st.markdown(f"**{panel['label']}**")
                    panel_fig = network_figure(panel, countries, min_events)
                    panel_fig.update_layout(height=430, margin={"l": 15, "r": 15, "t": 10, "b": 40}, legend={"orientation": "h", "y": -0.06, "font": {"size": 10}})
                    show_chart(panel_fig, key=key + "-panel-" + panel["id"], config={"displayModeBar": False})
        st.dataframe([{ "时间切片": w["label"], "事件记录": len(w["events"]), "国家对": len(w["edges"]), "网络密度": round(len(w["edges"]) / 36, 3), "样本说明": w["sample_note"] } for w in data["windows"]], hide_index=True, width="stretch")
    with tabs[2]:
        st.subheader("样本窗口之间的变化")
        show_chart(trend_figure(data), key=key + "-trend")
        st.caption("当前数据是 2015、2019、2020、2025 的选定日档/短窗口，曲线用于展示网络构建方法，不应解释为完整年度趋势。")
        st.dataframe([{ "时间切片": w["label"], "事件记录": len(w["events"]), "国家对": len(w["edges"]), "窗口说明": w["sample_note"] } for w in data["windows"]], hide_index=True, width="stretch")
    with tabs[3]:
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
            # Keep the evidence table on-site; source buttons below open the
            # existing in-place reader instead of forcing an external tab.
            st.dataframe(rows, hide_index=True, width="stretch")
            for i, row in enumerate(rows[:6]):
                if row["来源"].startswith(("http://", "https://")):
                    source_button(row["来源"], f"站内查看来源 {i + 1}", key=key + "-source-" + str(i))
    with tabs[4]:
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
