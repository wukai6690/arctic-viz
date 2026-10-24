"""Interactive, source-linked GDELT country-pair network views."""
from __future__ import annotations

import json
import math
import re
import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import plotly.graph_objects as go
import requests
import streamlit as st
from bs4 import BeautifulSoup
from src.presentation import ROOT, show_chart, section_title
from src.source_library import source_button

DATA_PATH = ROOT / "data/analysis/gdelt/network/network.json"
GRID_PATH = ROOT / "data/processed/gdelt_arctic_by_grid.csv"

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
COUNTRY_FLAGS = {
    "CHN": "🇨🇳", "USA": "🇺🇸", "RUS": "🇷🇺", "CAN": "🇨🇦", "NOR": "🇳🇴",
    "DNK": "🇩🇰", "FIN": "🇫🇮", "SWE": "🇸🇪", "ISL": "🇮🇸",
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


@st.cache_data(show_spinner=False)
def _processed_grid_events() -> list[dict]:
    """Load the archived GDELT grid snapshot as country-pair event evidence.

    The snapshot is kept separate from the curated network JSON.  It adds
    dated 2023–2025 months to the selector while retaining the original event
    identifiers, coordinates and source URLs.
    """
    if not GRID_PATH.exists():
        return []
    arctic = set(COUNTRY_LABELS) - {"ALL"}
    rows: list[dict] = []
    with GRID_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            actor1 = str(raw.get("Actor1CountryCode") or "").strip().upper()
            actor2 = str(raw.get("Actor2CountryCode") or "").strip().upper()
            if actor1 not in arctic or actor2 not in arctic or actor1 == actor2:
                continue
            stamp = str(raw.get("SQLDATE") or "").strip()
            if len(stamp) != 8 or not stamp.isdigit():
                continue
            try:
                event_day = date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))
            except ValueError:
                continue
            try:
                goldstein = float(raw.get("GoldsteinScale"))
            except (TypeError, ValueError):
                goldstein = None
            try:
                articles = int(float(raw.get("NumArticles") or 0))
            except (TypeError, ValueError):
                articles = 0
            try:
                mentions = int(float(raw.get("NumMentions") or 0))
            except (TypeError, ValueError):
                mentions = 0
            try:
                tone = float(raw.get("AvgTone"))
            except (TypeError, ValueError):
                tone = None
            event_code = str(raw.get("EventCode") or "")
            rows.append({
                "id": "grid:" + str(raw.get("GlobalEventID") or f"{stamp}:{len(rows)}"),
                "date": event_day.isoformat(), "actor1": actor1, "actor2": actor2,
                "actor1_name": raw.get("Actor1Name") or actor1, "actor2_name": raw.get("Actor2Name") or actor2,
                "event_code": event_code, "category": f"CAMEO {event_code}" if event_code else "GDELT 事件",
                "goldstein": goldstein, "avg_tone": tone,
                "quad_class": 1 if goldstein is not None and goldstein > 0 else 3 if goldstein is not None and goldstein < 0 else 0,
                "num_articles": articles, "num_mentions": mentions, "num_sources": 1,
                "location": raw.get("ActionGeo_FullName") or "未标注地点",
                "source_url": raw.get("SOURCEURL") or "",
                "latitude": raw.get("ActionGeo_Lat"), "longitude": raw.get("ActionGeo_Long"),
            })
    return rows


def _network_events(data: dict) -> list[dict]:
    unique = {event.get("id"): event for event in all_events(data)}
    for event in _processed_grid_events():
        unique.setdefault(event.get("id"), event)
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
    # Transparent bilateral relation indices inspired by the BLR approach:
    # cooperation/conflict share within a pair multiplied by that pair's
    # average contribution to the two countries' observed event activity.
    # The result is a descriptive 0–100 sample index, not a diplomatic score.
    for edge in edges:
        total = edge["event_count"] or 1
        pair_contribution = 0.5 * (
            edge["event_count"] / max(1, degree[edge["source"]])
            + edge["event_count"] / max(1, degree[edge["target"]])
        )
        edge["blr_cooperation"] = round(100 * (edge["positive_events"] / total) * pair_contribution, 2)
        edge["blr_conflict"] = round(100 * (edge["negative_events"] / total) * pair_contribution, 2)
        edge["blr_net"] = round(edge["blr_cooperation"] - edge["blr_conflict"], 2)
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
    """Return a fixed, presentation-friendly nine-country layout.

    A fixed layout is deliberately used instead of a force-directed graph: the
    same country stays in the same place in every month, while the relation
    lines carry the changing signal.  The arrangement also leaves enough white
    space around the central US/Russia/China cluster for curved links to remain
    readable.
    """
    reference = {
        "USA": (0.00, 0.25), "RUS": (0.34, 0.58), "CHN": (0.42, 0.05),
        "CAN": (-0.38, 0.58), "NOR": (0.82, 0.47), "DNK": (0.86, -0.34),
        "FIN": (0.34, -0.72), "SWE": (-0.28, -0.72), "ISL": (-0.87, -0.22),
    }
    codes = [c["code"] for c in countries]
    positions = {code: reference[code] for code in codes if code in reference}
    missing = [code for code in codes if code not in positions]
    for i, code in enumerate(missing):
        angle = 2 * math.pi * i / max(1, len(missing))
        positions[code] = (0.95 * math.cos(angle), 0.82 * math.sin(angle))
    return positions


def _quadratic_curve(x1: float, y1: float, x2: float, y2: float, offset: float, steps: int = 28) -> tuple[list[float], list[float]]:
    """Create a short quadratic Bezier arc between two country nodes."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    cx, cy = (x1 + x2) / 2 + nx * offset, (y1 + y2) / 2 + ny * offset
    xs, ys = [], []
    for step in range(steps + 1):
        t = step / steps
        omt = 1 - t
        xs.append(omt * omt * x1 + 2 * omt * t * cx + t * t * x2)
        ys.append(omt * omt * y1 + 2 * omt * t * cy + t * t * y2)
    return xs, ys


def network_figure(window: dict, countries: list[dict], min_events: int = 1, focus: str = "ALL") -> go.Figure:
    positions = _positions(countries, window.get("nodes"))
    edges = sorted((edge for edge in window["edges"] if edge["event_count"] >= min_events),
                   key=lambda row: (-row["event_count"], row["source"], row["target"]))
    edge_traces = []
    for index, edge in enumerate(edges):
        source, target = edge["source"], edge["target"]
        if source not in positions or target not in positions:
            continue
        x1, y1 = positions[source]; x2, y2 = positions[target]
        total = edge["event_count"] or 1
        width = max(1.5, min(9.5, 1.4 + 1.45 * math.log1p(edge["article_count"] or total)))
        opacity = 0.95 if focus == "ALL" or focus in (source, target) else 0.16
        name = f"{COUNTRY_LABELS.get(source, source)} ↔ {COUNTRY_LABELS.get(target, target)}"
        value = edge.get("goldstein_mean")
        hover = (f"{COUNTRY_FLAGS.get(source, '')} {name}<br>事件 {total:,} 条 · 新闻文章 {edge['article_count']:,} 篇"
                 f"<br>合作 {edge.get('positive_events', 0):,} · 竞争/冲突 {edge.get('negative_events', 0):,}"
                 f"<br>双边合作指数 {edge.get('blr_cooperation', 0):.2f} · 双边冲突指数 {edge.get('blr_conflict', 0):.2f}"
                 + (f"<br>Goldstein 均值 {value:+.2f}" if value is not None else ""))
        # A pair with both positive and negative events gets two slightly
        # separated arcs; this makes mixed relationships legible rather than
        # collapsing them into one misleading average colour.
        positive = int(edge.get("positive_events", 0) or 0)
        negative = int(edge.get("negative_events", 0) or 0)
        base_offset = 0.035 + 0.012 * (index % 3)
        parts = [(positive, "#2d8fc9", "合作事件", base_offset),
                 (negative, "#e47b72", "竞争/冲突事件", -base_offset)]
        if positive == 0 and negative == 0:
            parts = [(total, "#aebfca", "中性/未定事件", 0.0)]
        for count, color, legend, offset in parts:
            if count <= 0:
                continue
            xs, ys = _quadratic_curve(x1, y1, x2, y2, offset)
            edge_traces.append(go.Scatter(x=xs, y=ys, mode="lines",
                line={"width": width * (0.68 if legend.startswith("竞争") else 0.8), "color": f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},{opacity})"},
                hovertemplate=hover + f"<br>该层事件 {count:,} 条<extra></extra>",
                showlegend=False, customdata=[source + "|" + target]))
    country_by_code = {c["code"]: c for c in countries}
    nodes = window["nodes"]
    max_degree = max((n["event_degree"] for n in nodes), default=1)
    ranked_nodes = sorted(nodes, key=lambda node: (-node.get("event_degree", 0), -node.get("article_degree", 0), node["code"]))
    active_codes = [node["code"] for node in ranked_nodes if node.get("event_degree", 0) > 0]
    core_codes = set(active_codes[:3])
    secondary_codes = set(active_codes[3:6])
    role_colors = {code: "#c87357" if code in core_codes else "#d8aa52" if code in secondary_codes else "#7d96b0" if code in active_codes else "#d6dee4" for code in positions}
    node_text = [f"{COUNTRY_FLAGS.get(n['code'], '•')} {COUNTRY_LABELS.get(n['code'], country_by_code.get(n['code'], {}).get('name', n['code']))}" for n in nodes]
    node_trace = go.Scatter(
        x=[positions[n["code"]][0] for n in nodes], y=[positions[n["code"]][1] for n in nodes],
        mode="markers+text", text=node_text, textposition="top center",
        textfont={"size": 13, "color": "#173f63", "family": "Microsoft YaHei, Arial"},
        marker={"size": [12 if not n["event_degree"] else 18 + 34 * math.sqrt(n["event_degree"] / max_degree) if max_degree else 18 for n in nodes],
                "color": [role_colors.get(n["code"], "#d6dee4") for n in nodes], "line": {"width": 2, "color": "#ffffff"},
                "opacity": 0.96},
        customdata=[[n["code"], n["event_degree"], n["article_degree"]] for n in nodes],
        hovertemplate="%{text} (%{customdata[0]})<br>事件度数：%{customdata[1]:,}<br>关联新闻文章：%{customdata[2]:,}<extra></extra>",
        name="国家节点",
    )
    legend_traces = [
        go.Scatter(x=[None], y=[None], mode="lines", line={"width": 4, "color": "#2d8fc9"}, name="合作事件"),
        go.Scatter(x=[None], y=[None], mode="lines", line={"width": 4, "color": "#e47b72"}, name="竞争 / 冲突"),
        go.Scatter(x=[None], y=[None], mode="lines", line={"width": 3, "color": "#aebfca"}, name="中性 / 未定"),
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 12, "color": "#c87357"}, name="动态核心节点"),
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 10, "color": "#d8aa52"}, name="动态次核心节点"),
        go.Scatter(x=[None], y=[None], mode="markers", marker={"size": 8, "color": "#7d96b0"}, name="动态边缘节点"),
    ]
    fig = go.Figure(edge_traces + [node_trace] + legend_traces)
    fig.update_layout(height=640, margin={"l": 25, "r": 25, "t": 20, "b": 48}, showlegend=True,
                      legend={"orientation": "h", "y": -0.02, "x": 0.5, "xanchor": "center", "font": {"size": 11}},
                      xaxis={"visible": False, "range": [-1.18, 1.12]}, yaxis={"visible": False, "range": [-1.02, 0.95]},
                      plot_bgcolor="#fbfdff", paper_bgcolor="#ffffff", hovermode="closest")
    return fig


def matrix_figure(window: dict, countries: list[dict]) -> go.Figure:
    """Show a compact country-pair matrix with signed cooperation balance."""
    codes = [c["code"] for c in countries]
    labels = [f"{COUNTRY_FLAGS.get(code, '')} {COUNTRY_LABELS.get(code, code)}" for code in codes]
    lookup = {tuple(sorted((edge["source"], edge["target"]))): edge for edge in window.get("edges", [])}
    z, text, custom = [], [], []
    max_abs = 1
    for source in codes:
        z_row, text_row, custom_row = [], [], []
        for target in codes:
            if source == target:
                z_row.append(None); text_row.append("—"); custom_row.append([0, 0, 0])
                continue
            edge = lookup.get(tuple(sorted((source, target))))
            if not edge:
                z_row.append(0); text_row.append("0"); custom_row.append([0, 0, 0]); continue
            positive = int(edge.get("positive_events", 0) or 0)
            negative = int(edge.get("negative_events", 0) or 0)
            total = int(edge.get("event_count", 0) or 0)
            balance = positive - negative
            max_abs = max(max_abs, abs(balance))
            z_row.append(balance); text_row.append(str(total)); custom_row.append([total, positive, negative])
        z.append(z_row); text.append(text_row); custom.append(custom_row)
    fig = go.Figure(go.Heatmap(z=z, x=labels, y=labels, text=text, texttemplate="%{text}",
        customdata=custom, colorscale=[[0, "#e47b72"], [0.5, "#f4f8fb"], [1, "#3b91c7"]],
        zmin=-max_abs, zmax=max_abs, xgap=2, ygap=2,
        hovertemplate="%{y} × %{x}<br>事件记录：%{customdata[0]:,}<br>合作：%{customdata[1]:,} · 竞争/冲突：%{customdata[2]:,}<extra></extra>",
        colorbar={"title": "合作−竞争", "thickness": 12, "len": 0.75}))
    fig.update_layout(height=470, margin={"l": 95, "r": 35, "t": 20, "b": 75},
                      xaxis={"side": "bottom", "tickangle": -25, "tickfont": {"size": 11}},
                      yaxis={"autorange": "reversed", "tickfont": {"size": 11}},
                      plot_bgcolor="#ffffff", paper_bgcolor="#ffffff")
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


def monthly_windows(data: dict) -> list[dict]:
    """Build every month from 2014-01 through 2026-09.

    Observed events are grouped into their actual month. Empty months receive a
    clearly labelled nearest-history window so every selectable month has a
    usable network while the page still distinguishes direct from backfilled
    coverage.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in _network_events(data):
        month = str(event.get("date", ""))[:7]
        if len(month) == 7 and month[4] == "-":
            grouped[month].append(event)
    windows = []
    months = []
    year, month_num = 2014, 1
    while (year, month_num) <= (2026, 9):
        months.append(f"{year:04d}-{month_num:02d}")
        month_num += 1
        if month_num == 13:
            year, month_num = year + 1, 1
    for month in months:
        direct_rows = grouped[month]
        rows = list(direct_rows)
        fallback_months: list[str] = []
        if not rows:
            # Gather the nearest observed months until the fallback has enough
            # relation diversity. This uses real earlier/later events and never
            # changes their dates; it only supplies a context window for an
            # otherwise empty month selector position.
            candidates = []
            for distance in range(1, 37):
                for direction in (-1, 1):
                    candidate = _month_offset(month, direction * distance)
                    if grouped.get(candidate):
                        candidates.append((distance, candidate))
                if len(candidates) >= 4:
                    break
            candidates.sort()
            for _, candidate in candidates:
                rows.extend(grouped[candidate])
                fallback_months.append(candidate)
                pairs = {tuple(sorted((event.get("actor1", ""), event.get("actor2", "")))) for event in rows}
                if len(rows) >= 60 and len(pairs) >= 6:
                    break
        edges, nodes = aggregate_events(rows, data["countries"])
        observed = bool(direct_rows)
        windows.append({
            "id": "month-" + month,
            "label": month,
            "year": int(month[:4]),
            "date_start": min((e.get("date", "") for e in rows), default=month + "-01"),
            "date_end": max((e.get("date", "") for e in rows), default=month + "-01"),
            "events": rows,
            "direct_events": direct_rows,
            "fallback_months": fallback_months,
            "edges": edges,
            "nodes": nodes,
            "source": {"dataset": "GDELT 已整理月度样本" if observed else "最近可用月份历史回溯样本"},
            "sample_note": "当前为该月已整理日期窗口，不代表完整月份活动量。" if observed else f"该月没有直接记录；网络使用最近可用月份回溯样本：{', '.join(fallback_months)}。",
        })
    return windows


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_web_article(url: str) -> dict:
    """Read a page only after the user asks for its text.

    Many news sites block automated readers or publish only a short page shell;
    the result therefore keeps the original URL and reports the access state.
    """
    if not str(url).startswith(("http://", "https://")):
        return {"status": "invalid", "title": "没有可访问的网页地址", "text": ""}
    try:
        response = requests.get(url, headers={"User-Agent": "ArcticResearch/1.0 (source review)"}, timeout=8)
        if response.status_code >= 400:
            return {"status": "http_error", "title": "网页返回错误", "text": "", "code": response.status_code}
        soup = BeautifulSoup(response.content, "lxml")
        for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
            node.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else "网页正文"
        candidates = soup.select("article, main, [role='main'], .article-body, .story-body, .entry-content")
        target = max(candidates, key=lambda node: len(node.get_text(" ", strip=True)), default=soup.body or soup)
        paragraphs = []
        for node in target.select("p, h1, h2, h3, li"):
            text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
            if len(text) >= 35 and text not in paragraphs:
                paragraphs.append(text)
        text = "\n\n".join(paragraphs)[:16000]
        if len(text) < 120:
            return {"status": "no_text", "title": title, "text": ""}
        return {"status": "ok", "title": title, "text": text, "code": response.status_code}
    except requests.RequestException as exc:
        return {"status": "request_error", "title": "网页暂时无法读取", "text": "", "error": type(exc).__name__}


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
        st.caption("按日期、国家对、CAMEO 事件类型和关键词筛选 GDELT 事件，并查看对应的来源链接。")
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


@st.dialog("来源网页正文", width="large")
def show_article_dialog(article: dict, event: dict) -> None:
    """Display fetched source text in a compact modal instead of a page-length block."""
    st.caption(f"{event.get('date', '')} · {event.get('location', '')} · {event_type_label(event)}")
    if article.get("status") == "ok":
        st.subheader(article.get("title") or "网页正文")
        st.caption("正文由来源网页即时读取，用于辅助核对；事件字段和原文链接仍是记录依据。")
        st.text_area("正文", article.get("text", ""), height=430, label_visibility="collapsed")
    elif article.get("status") == "no_text":
        st.warning("网页可访问，但没有提取到足够正文。请使用下方原文链接查看页面。")
    else:
        st.warning("网页暂时无法读取。请使用下方原文链接直接查看。")
    if event.get("source_url"):
        st.link_button("打开原文", event["source_url"], use_container_width=True)


def render_search_results(result: dict, countries: list[dict], key: str) -> None:
    """Show compact search results with source reading in a modal."""
    st.subheader("事件检索结果")
    st.caption("结果保留日期、行为体、地点、事件类型和原文链接；选择一条记录后，可在弹窗中读取网页正文。")
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
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        height=360,
        column_config={"来源": st.column_config.LinkColumn("相关链接", display_text="打开原文")},
    )
    choices = result["events"][:300]
    selected = st.selectbox(
        "选择一条事件查看正文",
        choices,
        format_func=lambda event: f"{event.get('date', '')} · {event.get('actor1', '')} → {event.get('actor2', '')} · {event_type_label(event)} · {event.get('location', '')}",
        key=key + "-article-choice",
    )
    url = str(selected.get("source_url", ""))
    left, right = st.columns(2)
    if url.startswith(("http://", "https://")):
        left.link_button("打开相关原文链接", url, use_container_width=True)
    else:
        left.caption("这条事件没有可用的原文 URL。")
    if right.button("检索网页正文", key=key + "-read-article", use_container_width=True, disabled=not bool(url)):
        show_article_dialog(fetch_web_article(url), selected)


def _edge_sources(window: dict, edge: dict, limit: int = 2) -> list[str]:
    wanted = set(edge.get("event_ids", []))
    urls = []
    for event in window.get("events", []):
        if event.get("id") not in wanted:
            continue
        url = str(event.get("source_url") or "")
        if url.startswith(("http://", "https://")) and url not in urls:
            urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def render_evidence_panel(window: dict, countries: list[dict], min_events: int, key: str) -> None:
    """Render the right-hand evidence rail from the same edge rows as the graph."""
    ranked = sorted((edge for edge in window.get("edges", []) if edge["event_count"] >= min_events),
                    key=lambda edge: (-edge["event_count"], -edge.get("article_count", 0)))[:7]
    st.markdown("<div class='network-evidence-panel'><div class='network-panel-kicker'>BILATERAL EVIDENCE</div><h3>双边关系强度与关键证据</h3><p>按事件记录数排序；颜色拆分合作与竞争/冲突，点击来源可回到新闻原文。</p>", unsafe_allow_html=True)
    if not ranked:
        st.warning("当前窗口没有达到阈值的国家对。")
    for index, edge in enumerate(ranked, start=1):
        source, target = edge["source"], edge["target"]
        total = int(edge.get("event_count", 0) or 0)
        positive = int(edge.get("positive_events", 0) or 0)
        negative = int(edge.get("negative_events", 0) or 0)
        max_total = max(1, int(ranked[0].get("event_count", 1) or 1))
        width = max(10, round(total / max_total * 100))
        tone = "合作偏多" if positive > negative else "竞争偏多" if negative > positive else "混合关系"
        source_html = ""
        for source_url in _edge_sources(window, edge, limit=1):
            source_html = f"<a class='network-source-link' href='{source_url}' target='_blank' rel='noreferrer'>查看证据 ↗</a>"
        st.markdown(
            f"<div class='network-rank-row'><div class='network-rank-top'><span class='network-rank-no'>{index:02d}</span><b>{COUNTRY_FLAGS.get(source, '')} {COUNTRY_LABELS.get(source, source)} × {COUNTRY_FLAGS.get(target, '')} {COUNTRY_LABELS.get(target, target)}</b><strong>{total:,}</strong></div>"
            f"<div class='network-rank-bar'><span style='width:{width}%;'></span></div><div class='network-rank-meta'><span>{tone}</span><span class='network-positive'>合作 {positive}</span><span class='network-negative'>竞争/冲突 {negative}</span><span>{source_html}</span></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_network_insights(window: dict, min_events: int) -> None:
    ranked = sorted((edge for edge in window.get("edges", []) if edge["event_count"] >= min_events),
                    key=lambda edge: -edge["event_count"])
    top = ranked[0] if ranked else None
    total_positive = sum(int(edge.get("positive_events", 0) or 0) for edge in ranked)
    total_negative = sum(int(edge.get("negative_events", 0) or 0) for edge in ranked)
    top_text = f"{COUNTRY_LABELS.get(top['source'], top['source'])} × {COUNTRY_LABELS.get(top['target'], top['target'])}（{top['event_count']} 条）" if top else "暂无"
    st.markdown(
        f"<div class='network-insight-strip'><div><small>关键发现</small><b>{window['label']}</b><span>保留 {len(ranked)} 对达到当前阈值的国家关系。</span></div><div><small>最密集关系</small><b>{top_text}</b><span>以 GDELT 事件记录数衡量。</span></div><div><small>关系倾向</small><b class='network-positive'>合作 {total_positive:,}</b><b class='network-negative'>竞争/冲突 {total_negative:,}</b><span>仅用于描述新闻事件编码分布。</span></div></div>",
        unsafe_allow_html=True,
    )


def render_search_page() -> None:
    data = load_network()
    section_title("EVENT SEARCH", "按条件查找北极国家互动记录", "日期、国家角色和 CAMEO 事件类型先筛选事件，再回到来源网页核对。")
    result = render_search_panel(data, data["countries"], "event-search")
    if result is not None:
        render_search_results(result, data["countries"], "event-search-result")


def _month_offset(month: str, offset: int) -> str:
    total = int(month[:4]) * 12 + int(month[5:7]) - 1 + offset
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _event_evidence_rows(events: list[dict], month: str, related_pairs: set[tuple[str, str]], history_months: int = 12, limit: int = 80) -> list[dict]:
    start = _month_offset(month, -history_months)
    rows = []
    for event in events:
        event_month = str(event.get("date", ""))[:7]
        if not (start <= event_month <= month):
            continue
        pair = tuple(sorted((event.get("actor1", ""), event.get("actor2", ""))))
        if related_pairs and pair not in related_pairs:
            continue
        rows.append({
            "证据月份": event_month,
            "日期": event.get("date", ""),
            "国家对": f"{COUNTRY_FLAGS.get(pair[0], '')} {COUNTRY_LABELS.get(pair[0], pair[0])} ↔ {COUNTRY_FLAGS.get(pair[1], '')} {COUNTRY_LABELS.get(pair[1], pair[1])}",
            "事件类型": event_type_label(event),
            "地点": event.get("location", ""),
            "Goldstein": event.get("goldstein"),
            "来源": event.get("source_url", ""),
        })
    return sorted(rows, key=lambda row: (row["日期"], row["证据月份"]), reverse=True)[:limit]


def _render_evidence_table(events: list[dict], month: str, related_pairs: set[tuple[str, str]], key: str, title: str, history_months: int = 12) -> None:
    note = "全样本时间范围内" if history_months > 100 else "当前月份及此前 12 个月内"
    st.markdown(f"<div class='network-section-heading'><span>EVIDENCE TRACE</span><b>{title}</b><small>显示{note}、与当前国家对相关的事件证据。</small></div>", unsafe_allow_html=True)
    rows = _event_evidence_rows(events, month, related_pairs, history_months=history_months)
    if not rows:
        st.info("当前资料包没有匹配的事件证据。空白表示覆盖边界，不表示国家关系不存在。")
        return
    st.dataframe(rows, hide_index=True, width="stretch", height=390, column_config={"来源": st.column_config.LinkColumn("来源", display_text="打开原文")})


def _render_bilateral_index(edges: list[dict], key: str, title: str) -> None:
    ranked = sorted(edges, key=lambda edge: (-abs(edge.get("blr_net", 0)), -edge.get("event_count", 0)))[:12]
    st.markdown(f"<div class='network-section-heading'><span>BILATERAL RELATION INDEX</span><b>{title}</b><small>合作/冲突占比 × 该国家对对双方观测活动的平均贡献；数值只描述当前资料样本。</small></div>", unsafe_allow_html=True)
    if not ranked:
        st.info("当前窗口没有可计算的双边关系指数。")
        return
    rows = [{
        "国家对": f"{COUNTRY_FLAGS.get(edge['source'], '')} {COUNTRY_LABELS.get(edge['source'], edge['source'])} ↔ {COUNTRY_FLAGS.get(edge['target'], '')} {COUNTRY_LABELS.get(edge['target'], edge['target'])}",
        "事件记录": edge.get("event_count", 0),
        "合作事件": edge.get("positive_events", 0),
        "竞争/冲突": edge.get("negative_events", 0),
        "双边合作指数": edge.get("blr_cooperation", 0),
        "双边冲突指数": edge.get("blr_conflict", 0),
        "净关系": edge.get("blr_net", 0),
    } for edge in ranked]
    st.dataframe(rows, hide_index=True, width="stretch", height=310)
    st.caption("公式：BLR 合作 = 合作事件占比 × 双方平均贡献 × 100；BLR 冲突同理；净关系 = 合作 − 冲突。该指数不代表外交关系强度。")


def render_network(key: str = "network") -> None:
    data = load_network()
    countries = data["countries"]
    windows = monthly_windows(data)
    month_by_label = {window["label"]: window for window in windows}
    events = _network_events(data)
    overall_edges, overall_nodes = aggregate_events(events, countries)
    overall = {"id": "all-sample", "label": "全样本汇总", "year": None,
               "date_start": min((e.get("date", "") for e in events), default=""),
               "date_end": max((e.get("date", "") for e in events), default=""),
               "events": events, "edges": overall_edges, "nodes": overall_nodes}
    section_title("RELATIONSHIP NETWORK", "北极国家关系网络", "整体关系看全样本，月度关系看 2014—2026 的每一个月份；事件证据跟随国家对回溯。")
    st.markdown("<div class='network-hero-note'><b>动态网络阅读方式</b><span>节点大小按该窗口事件度数变化，连线按该窗口国家对变化；同一国家在不同月份的节点大小和连线都会重新计算。</span><span class='network-hero-source'>GDELT 新闻感知层 · 不等同于外交关系结论</span></div>", unsafe_allow_html=True)
    observed = sum(bool(window.get("direct_events")) for window in windows)
    fallback_count = len(windows) - observed
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("月度选择器", f"{len(windows)} 个月", "2014-01—2026-09")
    c2.metric("直接有事件月份", f"{observed} 个月", f"{fallback_count} 个月使用历史回溯")
    c3.metric("全样本事件", f"{len(events):,}", "去重后")
    c4.metric("全样本国家对", f"{len(overall_edges):,}", "9 个北极国家")
    tabs = st.tabs(["整体关系网络", "月度关系网络"])
    with tabs[0]:
        st.markdown("<div class='network-panel-heading'><span>ALL OBSERVED EVIDENCE</span><b>全样本国家关系网络</b><small>合并已整理网络样本与 GDELT 网格归档事件；线条越粗表示该国家对的事件文章量越大。</small></div>", unsafe_allow_html=True)
        show_chart(network_figure(overall, countries, 1, "ALL"), key=key + "-overall", config={"displayModeBar": True, "displaylogo": False})
        _render_bilateral_index(overall_edges, key + "-overall-index", "全样本双边关系指数")
        related = {tuple(sorted((edge["source"], edge["target"]))) for edge in overall_edges}
        _render_evidence_table(events, max((window["label"] for window in windows if window["events"]), default="2025-09"), related, key + "-overall-evidence", "整体网络事件证据", history_months=200)
    with tabs[1]:
        labels = [window["label"] for window in windows]
        densest = max(windows, key=lambda window: len(window["events"]))["label"] if windows else labels[0]
        choice = st.selectbox("选择月份", labels, index=labels.index(densest) if densest in labels else 0, key=key + "-month-choice")
        window = month_by_label[choice]
        m1, m2, m3 = st.columns(3)
        m1.metric("当前月份", choice)
        m2.metric("关系样本事件", f"{len(window['events']):,}", f"直接记录 {len(window.get('direct_events', [])):,}")
        m3.metric("国家对", f"{len(window['edges']):,}")
        if not window.get("direct_events"):
            st.info(f"该月份没有直接事件记录；当前网络使用历史回溯样本（{', '.join(window.get('fallback_months', []))}），因此连线仍反映真实的近期国家互动。")
        st.markdown("<div class='network-panel-heading'><span>MONTHLY RELATIONSHIP</span><b>该月份的国家关系网络</b><small>拖动月份选择器后，节点、连线、颜色和下方证据都会同步更新。</small></div>", unsafe_allow_html=True)
        show_chart(network_figure(window, countries, 1, "ALL"), key=key + "-monthly", config={"displayModeBar": True, "displaylogo": False})
        _render_bilateral_index(window["edges"], key + "-monthly-index", f"{choice} 双边关系指数")
        related = {tuple(sorted((edge["source"], edge["target"]))) for edge in window["edges"]}
        evidence_month = choice if window.get("direct_events") else max(window.get("fallback_months", [choice]))
        evidence_title = "当前月份及历史关联事件证据" if window.get("direct_events") else f"{choice} 网络的历史回溯证据"
        _render_evidence_table(events, evidence_month, related, key + "-monthly-evidence", evidence_title)

def render_network_page() -> None:
    render_network("network-page")
