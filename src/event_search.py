"""Unified Arctic event search, candidate review and source reading view.

This module owns the standalone event-search page only.  The time-slice country
network remains in ``src.gdelt_network`` so the two workstreams can evolve
independently.
"""
from __future__ import annotations

import json
import html
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.gdelt_network import (
    COUNTRY_LABELS,
    EVENT_TYPES,
    all_events,
    event_type_code,
    event_type_label,
    fetch_web_article,
    load_network,
)
from src.presentation import ROOT, section_title, show_chart
from src.source_library import source_button


KIND_LABELS = {
    "prepared_event": "已整理事件",
    "machine_candidate": "机器候选",
    "verified_event": "独立核验",
}
STATUS_LABELS = {
    "prepared": "已整理样本",
    "pending": "待核验",
    "source_reviewed": "来源已阅读",
    "verified": "独立证据核验",
}
RELATION_CLASSES = ["言语合作", "物质合作", "言语冲突", "物质冲突"]
RELATION_COLOR = {
    "言语合作": "#2f87d3",
    "物质合作": "#55a896",
    "言语冲突": "#e49a54",
    "物质冲突": "#d76767",
}

COUNTRY_ALIASES = {
    "中国": ["中国", "china", "chinese", "chn"],
    "美国": ["美国", "united states", "us", "usa", "american"],
    "俄罗斯": ["俄罗斯", "russia", "russian", "rus"],
    "加拿大": ["加拿大", "canada", "canadian", "can"],
    "挪威": ["挪威", "norway", "norwegian", "nor"],
    "丹麦": ["丹麦", "denmark", "danish", "dnk"],
    "芬兰": ["芬兰", "finland", "finnish", "fin"],
    "瑞典": ["瑞典", "sweden", "swedish", "swe"],
    "冰岛": ["冰岛", "iceland", "icelandic", "isl"],
}


def _text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _escape(value) -> str:
    return html.escape(_text(value), quote=True)


def _valid_url(value: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", _text(value), flags=re.I))


def _parse_date(value) -> str:
    raw = re.sub(r"[^0-9]", "", _text(value))
    if len(raw) == 8:
        try:
            return datetime.strptime(raw, "%Y%m%d").date().isoformat()
        except ValueError:
            return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", _text(value)):
        try:
            return date.fromisoformat(_text(value)).isoformat()
        except ValueError:
            return ""
    return ""


def _number(value):
    raw = _text(value)
    if not raw:
        return None
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _country_name(code: str, name: str = "") -> str:
    code = _text(code).upper()
    if code in COUNTRY_LABELS and code != "ALL":
        return COUNTRY_LABELS[code]
    return _text(name) or code or "未标注参与方"


def _event_category(event_code: str, fallback: str = "") -> str:
    code = _text(event_code)[:2]
    return f"{code} · {EVENT_TYPES.get(code, fallback or '未分类')}" if code else (fallback or "未分类")


def _relation_class(event: dict) -> str:
    category = _text(event.get("category"))
    if category in RELATION_CLASSES:
        return category
    quad = _text(event.get("quad_class"))
    return {"1": "言语合作", "2": "物质合作", "3": "言语冲突", "4": "物质冲突"}.get(quad, "")


def _neutral_title(record: dict) -> str:
    original = _text(record.get("original_title"))
    if original:
        return original
    left = record.get("actor1_name") or record.get("actor1") or "未知主体"
    right = record.get("actor2_name") or record.get("actor2") or "未知主体"
    category = record.get("category") or "机器编码事件"
    return f"{left}与{right} · {category}"


def _normalise(event: dict, *, kind: str, source_archive: str = "", source_file: str = "") -> dict:
    event_code = _text(event.get("event_code") or event.get("EventCode"))
    actor1 = _text(event.get("actor1_country") or event.get("Actor1CountryCode") or event.get("actor1"))
    actor2 = _text(event.get("actor2_country") or event.get("Actor2CountryCode") or event.get("actor2"))
    actor1_name = _text(event.get("actor1_name") or event.get("Actor1Name"))
    actor2_name = _text(event.get("actor2_name") or event.get("Actor2Name"))
    category = _text(event.get("category")) or _event_category(event_code).split(" · ", 1)[-1]
    record = {
        "record_id": _text(event.get("record_id") or event.get("id") or event.get("GlobalEventID")),
        "record_kind": kind,
        "record_kind_label": KIND_LABELS[kind],
        "verification_status": _text(event.get("verification_status")) or ("已核验" if kind == "verified_event" else STATUS_LABELS["prepared"] if kind == "prepared_event" else STATUS_LABELS["pending"]),
        "event_date": _parse_date(event.get("event_date") or event.get("date") or event.get("SQLDATE")),
        "archive_date": _parse_date(event.get("archive_date") or event.get("source_archive_date")),
        "dataset": _text(event.get("dataset")) or "GDELT",
        "source_archive": source_archive or _text(event.get("source_archive")),
        "source_file": source_file or _text(event.get("source_file")),
        "actor1": actor1,
        "actor2": actor2,
        "actor1_name": actor1_name,
        "actor2_name": actor2_name,
        "actor1_label": _country_name(actor1, actor1_name),
        "actor2_label": _country_name(actor2, actor2_name),
        "event_code": event_code,
        "event_category": _event_category(event_code, category),
        "category": category,
        "relation_class": _relation_class({**event, "category": category}),
        "location": _text(event.get("location") or event.get("ActionGeo_FullName")),
        "latitude": _number(event.get("latitude") or event.get("ActionGeo_Lat")),
        "longitude": _number(event.get("longitude") or event.get("ActionGeo_Long")),
        "source_url": _text(event.get("source_url") or event.get("SOURCEURL")),
        "source_url_valid": _valid_url(event.get("source_url") or event.get("SOURCEURL")),
        "source_line": _text(event.get("source_line")),
        "num_articles": _number(event.get("num_articles") or event.get("NumArticles")) or 0,
        "num_mentions": _number(event.get("num_mentions") or event.get("NumMentions")) or 0,
        "num_sources": _number(event.get("num_sources")),
        "goldstein": _number(event.get("goldstein") or event.get("GoldsteinScale")),
        "avg_tone": _number(event.get("avg_tone") or event.get("AvgTone")),
        "original_title": _text(event.get("original_title") or event.get("title")),
        "review_note": _text(event.get("review_note") or event.get("note")),
        "relevance_reasons": event.get("relevance_reasons") or event.get("filter_reasons") or [],
    }
    record["display_title"] = _neutral_title(record)
    record["display_description"] = (
        f"{record['actor1_label']} → {record['actor2_label']}，"
        f"{record['location'] or '行动地点未提供'}。"
        f"这是一条 {record['record_kind_label']}，机器编码与来源链接保留在详情中。"
    )
    return record


def _processed_candidates() -> Iterable[dict]:
    path = ROOT / "data/processed/gdelt_arctic_by_grid.csv"
    if not path.exists():
        return []
    frame = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
    rows = []
    for row in frame.to_dict("records"):
        rows.append({
            "record_id": f"candidate:{row.get('GlobalEventID', '')}",
            "GlobalEventID": row.get("GlobalEventID"),
            "SQLDATE": row.get("SQLDATE"),
            "EventCode": row.get("EventCode"),
            "Actor1CountryCode": row.get("Actor1CountryCode"),
            "Actor2CountryCode": row.get("Actor2CountryCode"),
            "Actor1Name": row.get("Actor1Name"),
            "Actor2Name": row.get("Actor2Name"),
            "ActionGeo_FullName": row.get("ActionGeo_FullName"),
            "ActionGeo_Lat": row.get("ActionGeo_Lat"),
            "ActionGeo_Long": row.get("ActionGeo_Long"),
            "SOURCEURL": row.get("SOURCEURL"),
            "NumArticles": row.get("NumArticles"),
            "NumMentions": row.get("NumMentions"),
            "GoldsteinScale": row.get("GoldsteinScale"),
            "AvgTone": row.get("AvgTone"),
            "dataset": "GDELT 2.0",
            "source_file": path.name,
        })
    return rows


def _bulk_candidates() -> Iterable[dict]:
    """Read the published 22,815-row candidate layer when available."""
    path = ROOT / "data/analysis/gdelt/bulk/gdelt_geopolitics_22815.csv"
    if not path.exists():
        return []
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    relation_labels = {
        "gdelt_verbal_cooperation": "言语合作",
        "gdelt_material_cooperation": "物质合作",
        "gdelt_verbal_conflict": "言语冲突",
        "gdelt_material_conflict": "物质冲突",
    }
    rows = []
    for row in frame.to_dict("records"):
        participants = _text(row.get("participants_or_leads"))
        codes = re.findall(r"\[([A-Z]{3})\]", participants)
        relation = relation_labels.get(_text(row.get("relation_type")), _text(row.get("relation_type")))
        working_groups = _text(row.get("working_groups"))
        code_match = re.search(r"CAMEO\s+(\d{3})", working_groups)
        rows.append({
            "record_id": row.get("record_id"),
            "event_date": row.get("date"),
            "archive_date": row.get("date"),
            "actor1": codes[0] if codes else "",
            "actor2": codes[1] if len(codes) > 1 else "",
            "actor1_name": participants,
            "actor2_name": "",
            "event_code": code_match.group(1) if code_match else "",
            "category": relation,
            "relation_type": relation,
            "location": row.get("location"),
            "source_url": row.get("source_url"),
            "original_title": "",
            "review_note": row.get("summary"),
            "relevance_reasons": [row.get("evidence_level", "机器候选")],
            "dataset": "GDELT 1.0 · 2019 七日日档",
            "source_file": path.name,
        })
    return rows


def _daily_candidates() -> Iterable[dict]:
    rows = []
    folder = ROOT / "data/analysis/gdelt/daily"
    for path in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for event in payload.get("records", []):
            rows.append({**event, "record_id": event.get("id"), "source_file": path.name, "source_archive": event.get("archive_date", "")})
    return rows


def _verified_records() -> Iterable[dict]:
    path = ROOT / "data/analysis/event_reviews.jsonl"
    if not path.exists():
        return []
    grouped = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("status") == "verified":
            grouped[row.get("event_key") or row.get("id")] = row
    records = []
    for key, row in grouped.items():
        records.append({
            "record_id": f"verified:{key}",
            "event_date": row.get("event_date"),
            "actor1_name": "已核验事实",
            "actor2_name": "研究事件",
            "category": "独立证据核验",
            "source_url": row.get("evidence_url"),
            "review_note": row.get("claim") or row.get("note"),
            "verification_status": STATUS_LABELS["verified"],
            "dataset": "本站事件核验记录",
        })
    return records


@st.cache_data(show_spinner=False)
def load_unified_records() -> list[dict]:
    """Load both prepared network rows and larger candidate files once.

    Records sharing an ID with the prepared network sample keep the prepared
    version.  Counts therefore describe the published union rather than a raw
    sum of source files.
    """
    prepared = [_normalise(e, kind="prepared_event", source_archive=e.get("archive_date", "")) for e in all_events(load_network())]
    prepared_ids = {r["record_id"] for r in prepared}
    records = list(prepared)
    seen = set(prepared_ids)
    candidate_rows = list(_bulk_candidates())
    if not candidate_rows:
        candidate_rows = [*_daily_candidates(), *_processed_candidates()]
    for raw in candidate_rows:
        record = _normalise(raw, kind="machine_candidate", source_archive=raw.get("archive_date", ""), source_file=raw.get("source_file", ""))
        if not record["record_id"] or record["record_id"] in seen:
            continue
        seen.add(record["record_id"])
        records.append(record)
    for raw in _verified_records():
        record = _normalise(raw, kind="verified_event")
        if record["record_id"] and record["record_id"] not in seen:
            seen.add(record["record_id"])
            records.append(record)
    return sorted(records, key=lambda row: (row.get("event_date", ""), row.get("record_id", "")), reverse=True)


def _query_groups(query: str) -> list[list[str]]:
    normalized = query.casefold()
    groups = []
    for label, values in COUNTRY_ALIASES.items():
        label_cf = label.casefold()
        if label_cf in normalized:
            groups.append(list(dict.fromkeys([label_cf, *(value.casefold() for value in values)])))
            normalized = normalized.replace(label_cf, " ")
    tokens = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]+", normalized)
    for token in tokens:
        aliases = []
        for label, values in COUNTRY_ALIASES.items():
            if token == label.casefold() or token in {v.casefold() for v in values}:
                aliases.extend([label.casefold(), *(v.casefold() for v in values)])
        groups.append(list(dict.fromkeys([token, *aliases])))
    return groups


def _matches_query(record: dict, query: str) -> bool:
    groups = _query_groups(query)
    if not groups:
        return True
    haystack = " ".join([
        _text(record.get("display_title")),
        _text(record.get("original_title")),
        _text(record.get("actor1_label")),
        _text(record.get("actor2_label")),
        _text(record.get("actor1_name")),
        _text(record.get("actor2_name")),
        _text(record.get("actor1")),
        _text(record.get("actor2")),
        _text(record.get("event_category")),
        _text(record.get("category")),
        _text(record.get("location")),
        _text(record.get("source_url")),
        _text(record.get("record_id")),
        " ".join(map(str, record.get("relevance_reasons") or [])),
    ]).casefold()
    return all(any(term in haystack for term in group) for group in groups)


def _country_match(record: dict, code: str, role: int) -> bool:
    if code == "ALL":
        return True
    return record.get("actor1" if role == 1 else "actor2") == code


def filter_records(records: list[dict], filters: dict) -> list[dict]:
    start, end = filters["start"], filters["end"]
    selected_kinds = set(filters.get("kinds") or [])
    selected_relations = set(filters.get("relations") or [])
    selected_types = set(filters.get("event_types") or [])
    ignore_direction = bool(filters.get("ignore_direction"))
    result = []
    for record in records:
        event_date = record.get("event_date", "")
        if not event_date or event_date < start.isoformat() or event_date > end.isoformat():
            continue
        if selected_kinds and record.get("record_kind") not in selected_kinds:
            continue
        if selected_relations and record.get("relation_class") not in selected_relations:
            continue
        if selected_types and event_type_code(record) not in selected_types:
            continue
        c1, c2 = filters.get("country1", "ALL"), filters.get("country2", "ALL")
        if ignore_direction:
            if c1 != "ALL" and c1 not in (record.get("actor1"), record.get("actor2")):
                continue
            if c2 != "ALL" and c2 not in (record.get("actor1"), record.get("actor2")):
                continue
            if c1 != "ALL" and c2 != "ALL" and {c1, c2} != {record.get("actor1"), record.get("actor2")}:
                continue
        elif not (_country_match(record, c1, 1) and _country_match(record, c2, 2)):
            continue
        if not _matches_query(record, filters.get("query", "")):
            continue
        result.append(record)
    sort = filters.get("sort", "最新")
    if sort == "最早":
        result.sort(key=lambda row: (row.get("event_date", ""), row.get("record_id", "")))
    elif sort == "报道链接数":
        result.sort(key=lambda row: (row.get("num_articles", 0), row.get("event_date", "")), reverse=True)
    else:
        result.sort(key=lambda row: (row.get("event_date", ""), row.get("record_id", "")), reverse=True)
    return result


def _default_filters(records: list[dict]) -> dict:
    dates = [row["event_date"] for row in records if row.get("event_date")]
    return {
        "query": "",
        "start": date.fromisoformat(min(dates)) if dates else date(2014, 1, 1),
        "end": date.fromisoformat(max(dates)) if dates else date.today(),
        "country1": "ALL",
        "country2": "ALL",
        "relations": [],
        "kinds": [],
        "event_types": [],
        "ignore_direction": False,
        "sort": "最新",
    }


def _stats(records: list[dict]) -> dict:
    pairs = set()
    links = set()
    for row in records:
        a, b = row.get("actor1"), row.get("actor2")
        if a and b and a != b:
            pairs.add(tuple(sorted((a, b))))
        if row.get("source_url_valid"):
            links.add(row["source_url"])
    dates = [row["event_date"] for row in records if row.get("event_date")]
    return {
        "records": len(records),
        "pairs": len(pairs),
        "links": len(links),
        "date_range": f"{min(dates)} — {max(dates)}" if dates else "暂无日期",
        "articles": sum(int(row.get("num_articles") or 0) for row in records),
        "kinds": Counter(row.get("record_kind") for row in records),
    }


def _country_choices(records: list[dict]) -> list[tuple[str, str]]:
    codes = {row.get("actor1") for row in records} | {row.get("actor2") for row in records}
    codes.discard(None)
    codes.discard("")
    ordered = [code for code in COUNTRY_LABELS if code != "ALL" and code in codes]
    extras = sorted(codes - set(ordered))
    return [("ALL", "全部国家 / 地区"), *[(code, COUNTRY_LABELS.get(code, code)) for code in [*ordered, *extras]]]


def _year_figure(records: list[dict]) -> go.Figure:
    counts = Counter(row["event_date"][:4] for row in records if row.get("event_date"))
    years = sorted(counts)
    fig = go.Figure(go.Scatter(x=years, y=[counts[y] for y in years], mode="lines+markers+text", text=[counts[y] for y in years], textposition="top center", line={"color": "#1677d2", "width": 3}, marker={"size": 8}))
    fig.update_layout(height=280, margin={"l": 45, "r": 18, "t": 20, "b": 42}, xaxis_title="事件日期年份", yaxis_title="记录数", hovermode="x unified")
    return fig


def _relation_figure(records: list[dict]) -> go.Figure:
    counts = Counter(row.get("relation_class") or "关系级别未提供" for row in records)
    labels = list(counts)
    colors = [RELATION_COLOR.get(label, "#b8c9d9") for label in labels]
    fig = go.Figure(go.Bar(x=[counts[label] for label in labels], y=labels, orientation="h", marker_color=colors, text=[counts[label] for label in labels], textposition="outside"))
    fig.update_layout(height=280, margin={"l": 95, "r": 45, "t": 20, "b": 35}, xaxis_title="记录数", yaxis_title="")
    return fig


def _result_card(record: dict, selected: bool) -> str:
    badge = "<span class='event-badge kind-prepared'>已整理事件</span>" if record["record_kind"] == "prepared_event" else "<span class='event-badge kind-verified'>独立核验</span>" if record["record_kind"] == "verified_event" else "<span class='event-badge kind-machine'>机器候选</span>"
    relation = record.get("relation_class") or "关系级别未提供"
    return (
        f"<div class='event-result-card {'selected' if selected else ''}'>"
        f"<div class='event-card-meta'>{badge}<span>{_escape(record.get('event_date') or '日期未提供')}</span><span>{_escape(record.get('actor1_label'))} → {_escape(record.get('actor2_label'))}</span><span>{_escape(relation)}</span></div>"
        f"<h4>{_escape(record.get('display_title'))}</h4><p>{_escape(record.get('location') or '行动地点未提供')} · {_escape(record.get('dataset'))}</p>"
        f"</div>"
    )


def _detail(record: dict, key: str) -> None:
    status_class = "good" if record["record_kind"] == "verified_event" else "prepared" if record["record_kind"] == "prepared_event" else "pending"
    st.markdown(f"<div class='event-detail-head'><div><div class='event-eyebrow'>来源与事件详情</div><h2>{_escape(record['display_title'])}</h2></div><span class='event-status {status_class}'>{_escape(record['verification_status'])}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<p class='event-detail-description'>{_escape(record['display_description'])}</p>", unsafe_allow_html=True)
    facts = [
        ("事件日期", record.get("event_date") or "暂无公开日期"),
        ("来源归档日期", record.get("archive_date") or "未提供 / 不与事件日期混用"),
        ("参与方", f"{record.get('actor1_label')} → {record.get('actor2_label')}"),
        ("行动地点", record.get("location") or "暂无地理名称"),
        ("数据类型", record.get("record_kind_label")),
        ("数据集", record.get("dataset") or "GDELT"),
    ]
    cols = st.columns(2)
    for index, (label, value) in enumerate(facts):
        cols[index % 2].markdown(f"<div class='event-fact'><small>{_escape(label)}</small><strong>{_escape(value)}</strong></div>", unsafe_allow_html=True)
    if record.get("source_url"):
        st.markdown("#### 原始来源与阅读")
        left, right = st.columns(2)
        with left:
            if record.get("source_url_valid"):
                st.link_button("打开原文链接 ↗", record["source_url"], use_container_width=True)
            else:
                st.caption("当前记录没有可验证的 HTTP(S) 原文地址。")
        with right:
            source_button(record["source_url"], "站内查看来源登记", key=key + "-source")
        read_key = key + "-read"
        if st.button("读取网页正文", key=read_key, use_container_width=True, disabled=not record.get("source_url_valid")):
            st.session_state[key + "-article"] = fetch_web_article(record["source_url"])
        article = st.session_state.get(key + "-article")
        if article:
            if article.get("status") == "ok":
                st.markdown(f"**{article.get('title') or '来源网页正文'}**")
                with st.container(height=350, border=True):
                    st.write(article.get("text", ""))
            elif article.get("status") == "no_text":
                st.warning("网页可以访问，但没有提取到足够正文；请使用原文链接查看。")
            else:
                st.warning("网页暂时无法读取，原文链接仍保留。")
    with st.expander("研究字段与机器溯源"):
        detail = {
            "record_id": record.get("record_id"),
            "CAMEO 原始编码": record.get("event_code") or "暂无",
            "CAMEO 根类别": record.get("event_category") or "暂无",
            "关系类别": record.get("relation_class") or "未提供",
            "Goldstein": record.get("goldstein") if record.get("goldstein") is not None else "暂无",
            "AvgTone": record.get("avg_tone") if record.get("avg_tone") is not None else "暂无",
            "新闻文章计数": record.get("num_articles", 0),
            "机器提及计数": record.get("num_mentions", 0),
            "原始文件行号": record.get("source_line") or "暂无",
            "候选进入原因": record.get("relevance_reasons") or "暂无",
            "来源文件": record.get("source_file") or record.get("source_archive") or "暂无",
        }
        st.json(detail)
    if record.get("review_note"):
        st.info("研究备注：" + record["review_note"])


def _css() -> None:
    st.markdown(
        """<style>
        .event-search-shell{background:linear-gradient(135deg,#f9fcff,#eaf5ff);border:1px solid #d7e7f5;border-radius:18px;padding:22px 26px;margin-bottom:18px}
        .event-search-shell h3{color:#123f73!important;margin:0 0 6px!important}.event-search-shell p{color:#5f7d9c;margin:0}
        .event-kicker,.event-eyebrow{color:#287bbd;font-size:12px;letter-spacing:.12em;font-weight:800;text-transform:uppercase}
        .event-filter-note{background:#e5f2ff;border:1px solid #cfe5f8;border-radius:10px;padding:10px 14px;color:#416b91;font-size:13px}
        .event-result-card{padding:13px 15px;border:1px solid #d7e6f2;border-radius:11px;background:#fff;margin:0 0 6px;box-shadow:0 5px 15px rgba(24,92,145,.04)}
        .event-result-card.selected{border-color:#2584d0;box-shadow:0 0 0 2px #cfe8ff}
        .event-result-card h4{font-size:15px!important;color:#123f73!important;margin:7px 0 3px!important}.event-result-card p{font-size:12px;color:#718aa3;margin:0}
        .event-card-meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12px;color:#6c87a2}.event-card-meta span:not(.event-badge){background:#f0f6fb;border-radius:5px;padding:3px 6px}
        .event-badge{display:inline-block;border-radius:99px;padding:3px 8px;font-size:11px;font-weight:700}.kind-prepared{color:#1264a7;background:#e2f1ff}.kind-machine{color:#b86b13;background:#fff0d8}.kind-verified{color:#1d845c;background:#e0f7eb}
        .event-detail-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;border-bottom:1px solid #dbe8f2;padding-bottom:10px}.event-detail-head h2{font-size:23px!important;margin:7px 0 0!important;color:#123f73!important}.event-status{border-radius:99px;padding:5px 10px;font-size:12px;font-weight:700;white-space:nowrap}.event-status.good{color:#147c55;background:#e0f7eb}.event-status.prepared{color:#1264a7;background:#e2f1ff}.event-status.pending{color:#aa6818;background:#fff0d8}
        .event-detail-description{color:#527392;line-height:1.8}.event-fact{padding:9px 11px;background:#f4f9fd;border-radius:8px;margin:4px 0 8px}.event-fact small{display:block;color:#7b94ab}.event-fact strong{display:block;color:#234f78;margin-top:3px;font-size:14px}
        .event-section-label{border-left:4px solid #1878c9;padding-left:10px;color:#123f73;font-weight:800;font-size:19px;margin:24px 0 12px}
        [data-testid="stVerticalBlockBorderWrapper"]{border-color:#d7e6f2!important}
        </style>""",
        unsafe_allow_html=True,
    )


def render_event_search_center() -> None:
    records = load_unified_records()
    _css()
    section_title("ARCTIC EVENT INTELLIGENCE", "北极事件检索中心", "统一检索国家互动、机器候选事件与原始来源证据；数据类型和核验状态始终明确显示。")

    defaults = _default_filters(records)
    state_key = "event-center-filters"
    current = st.session_state.get(state_key, defaults)
    dates = [row["event_date"] for row in records if row.get("event_date")]
    min_day, max_day = date.fromisoformat(min(dates)), date.fromisoformat(max(dates))
    choices = _country_choices(records)
    with st.container(border=True):
        st.markdown("<div class='event-kicker'>统一检索入口</div><h3>先搜索，再逐条阅读来源</h3><p>事件记录、机器候选和后续核验事实共用一套结果列表；原始文件和来源归档日期不会被隐藏。</p>", unsafe_allow_html=True)
        with st.form("event-center-form", clear_on_submit=False):
            query = st.text_input("关键词", value=current.get("query", ""), placeholder="搜索国家、地点、项目、机构或来源网址")
            c1, c2, c3, c4 = st.columns(4)
            start = c1.date_input("事件日期起", value=max(min_day, current.get("start", min_day)), min_value=min_day, max_value=max_day)
            end = c2.date_input("事件日期止", value=min(max_day, current.get("end", max_day)), min_value=min_day, max_value=max_day)
            country_codes = [x[0] for x in choices]
            country1_index = country_codes.index(current.get("country1", "ALL")) if current.get("country1", "ALL") in country_codes else 0
            country2_index = country_codes.index(current.get("country2", "ALL")) if current.get("country2", "ALL") in country_codes else 0
            country1 = c3.selectbox("国家 / 地区（角色1）", choices, index=country1_index)
            country2 = c4.selectbox("国家 / 地区（角色2）", choices, index=country2_index)
            c5, c6, c7 = st.columns(3)
            current_relation = (current.get("relations") or [""])[0]
            relation_index = RELATION_CLASSES.index(current_relation) + 1 if current_relation in RELATION_CLASSES else 0
            relation = c5.selectbox("关系类别", ["全部关系类别", *RELATION_CLASSES], index=relation_index)
            kind_options = [("全部记录", []), *[(label, [kind]) for kind, label in KIND_LABELS.items()]]
            current_kind = (current.get("kinds") or [""])[0]
            kind_label_options = [label for label, _ in kind_options]
            kind_index = kind_label_options.index(KIND_LABELS[current_kind]) if current_kind in KIND_LABELS else 0
            kind_label = c6.selectbox("数据类型", kind_label_options, index=kind_index)
            sort = c7.selectbox("排序", ["最新", "最早", "报道链接数"], index=["最新", "最早", "报道链接数"].index(current.get("sort", "最新")))
            with st.expander("高级筛选：CAMEO 根类别与角色方向"):
                event_types = st.multiselect("CAMEO 根类别（默认不限制）", list(EVENT_TYPES), default=current.get("event_types", []), format_func=lambda code: f"{code} · {EVENT_TYPES[code]}")
                ignore_direction = st.checkbox("忽略角色方向", value=current.get("ignore_direction", False), help="例如中国—俄罗斯和俄罗斯—中国按同一国家对匹配。")
            submitted = st.form_submit_button("检索", type="primary", use_container_width=True)
        if submitted:
            if start > end:
                st.error("事件日期起不能晚于事件日期止。")
            else:
                st.session_state[state_key] = {
                    "query": query, "start": start, "end": end, "country1": country1[0], "country2": country2[0],
                    "relations": [] if relation == "全部关系类别" else [relation],
                    "kinds": next(kinds for label, kinds in kind_options if label == kind_label),
                    "event_types": event_types, "ignore_direction": ignore_direction, "sort": sort,
                }
                current = st.session_state[state_key]
        st.markdown(f"<div class='event-filter-note'>当前库：{len(records):,} 条统一记录。已整理网络样本与候选文件按 record_id 去重；事件日期和来源归档日期分开统计。</div>", unsafe_allow_html=True)

    filtered = filter_records(records, current)
    stats = _stats(filtered)
    metrics = st.columns(4)
    metrics[0].metric("检索结果", f"{stats['records']:,} 条")
    metrics[1].metric("国家 / 地区组合", f"{stats['pairs']:,} 对")
    metrics[2].metric("原始报道链接", f"{stats['links']:,} 个")
    metrics[3].metric("事件日期覆盖", stats["date_range"])
    st.caption(f"结果中的新闻文章计数合计 {stats['articles']:,}；它表示机器记录关联的文章数，不等同于独立现实事件数。")

    st.markdown("<div class='event-section-label'>统一结果与来源详情</div>", unsafe_allow_html=True)
    left, right = st.columns([1.05, 1], gap="large")
    page_size = 10
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.number_input("结果页", min_value=1, max_value=page_count, value=1, step=1, key="event-center-page", label_visibility="collapsed")
    start_index = (int(page) - 1) * page_size
    page_records = filtered[start_index:start_index + page_size]
    selected_id = st.session_state.get("event-center-selected")
    if selected_id not in {row["record_id"] for row in filtered}:
        selected_id = page_records[0]["record_id"] if page_records else None
        if selected_id:
            st.session_state["event-center-selected"] = selected_id
    selected = next((row for row in filtered if row["record_id"] == selected_id), None)
    with left:
        st.markdown(f"#### 检索结果 <small style='color:#6c87a2'>（{len(filtered):,} 条 · 第 {int(page)}/{page_count} 页）</small>", unsafe_allow_html=True)
        if not page_records:
            st.info("没有匹配记录。可以扩大日期范围、清空数据类型或减少关键词。")
        for record in page_records:
            with st.container(border=True):
                st.markdown(_result_card(record, record["record_id"] == selected_id), unsafe_allow_html=True)
                if st.button("查看详情", key="event-open-" + re.sub(r"[^A-Za-z0-9_-]", "_", record["record_id"]), use_container_width=True):
                    st.session_state["event-center-selected"] = record["record_id"]
                    st.rerun()
    with right:
        if selected:
            _detail(selected, "event-detail-" + re.sub(r"[^A-Za-z0-9_-]", "_", selected["record_id"]))
        else:
            st.info("点击左侧结果查看事件详情和来源。")

    st.markdown("<div class='event-section-label'>趋势与分布</div>", unsafe_allow_html=True)
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.markdown("#### 事件日期趋势")
        show_chart(_year_figure(filtered), key="event-center-trend")
    with chart_right:
        st.markdown("#### 关系类别分布")
        show_chart(_relation_figure(filtered), key="event-center-relations")

    st.markdown("<div class='event-section-label'>候选库与方法说明</div>", unsafe_allow_html=True)
    kind_counts = stats["kinds"]
    cards = st.columns(3)
    for col, kind in zip(cards, KIND_LABELS):
        col.metric(KIND_LABELS[kind], f"{kind_counts.get(kind, 0):,} 条")
    st.info("“已整理事件”来自固定的国家关系事件样本；“机器候选”来自较大 GDELT 候选文件；“独立核验”只有完成来源核对并归并后才进入。三类记录保留不同质量等级，不直接相加解释为现实事件数量。")
    dl_left, dl_right = st.columns(2)
    export_columns = ["record_id", "record_kind_label", "verification_status", "event_date", "archive_date", "dataset", "actor1_label", "actor2_label", "event_category", "relation_class", "location", "source_url", "num_articles", "goldstein", "avg_tone"]
    export_frame = pd.DataFrame([{key: row.get(key, "") for key in export_columns} for row in filtered])
    dl_left.download_button("下载当前检索结果 · CSV", export_frame.to_csv(index=False).encode("utf-8-sig"), "arctic-event-search-results.csv", "text/csv", use_container_width=True, on_click="ignore")
    dl_right.download_button("下载当前检索结果 · JSON", json.dumps(filtered, ensure_ascii=False, indent=2), "arctic-event-search-results.json", "application/json", use_container_width=True, on_click="ignore")
    with st.expander("来源、日期与使用边界"):
        st.write("事件日期是 GDELT 记录中的事件日期；来源归档日期是原始数据文件日期，两者不互相替代。机器候选的标题使用中性机器编码摘要，没有把网页标题猜写成新闻事实。")
        st.write("原始链接可打开时提供网页读取按钮；网页读取受来源站点访问限制，不能替代人工核验。Goldstein、AvgTone 和机器事件编码是研究字段，不是国家关系评分或现实事件强度。")

