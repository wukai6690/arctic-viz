"""Build a bounded, source-linked Arctic country event network from GDELT archives.

The published artifact is intentionally an auditable sample of selected archive
windows. It is not presented as a complete annual count or as a direct measure
of diplomatic relations.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/analysis/gdelt/network/raw"
OUT = ROOT / "data/analysis/gdelt/network/network.json"

COUNTRIES = {
    "CHN": {"name": "中国", "english": "China", "role": "观察国"},
    "USA": {"name": "美国", "english": "United States", "role": "北极国家"},
    "RUS": {"name": "俄罗斯", "english": "Russia", "role": "北极国家"},
    "CAN": {"name": "加拿大", "english": "Canada", "role": "北极国家"},
    "NOR": {"name": "挪威", "english": "Norway", "role": "北极国家"},
    "DNK": {"name": "丹麦", "english": "Denmark", "role": "北极国家"},
    "FIN": {"name": "芬兰", "english": "Finland", "role": "北极国家"},
    "SWE": {"name": "瑞典", "english": "Sweden", "role": "北极国家"},
    "ISL": {"name": "冰岛", "english": "Iceland", "role": "北极国家"},
}
TERMS = (
    "arctic", "svalbard", "spitsbergen", "barents", "kara sea", "chukchi",
    "beaufort", "greenland", "murmansk", "tromso", "tromsø", "sabetta",
    "northern sea route", "northwest passage", "ny-alesund", "north pole",
)
QUAD = {1: "言语合作", 2: "物质合作", 3: "言语冲突", 4: "物质冲突"}


def _terms(text: str) -> list[str]:
    text = re.sub(r"[-_]", " ", str(text).casefold())
    return [term for term in TERMS if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text)]


def _float(value: str) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _row_event(row: list[str], archive_date: str, line: int, dataset: str, source_url: str) -> dict | None:
    if len(row) != 58 or row[7] not in COUNTRIES or row[17] not in COUNTRIES or row[7] == row[17]:
        return None
    lat = _float(row[53])
    location = row[50] or ""
    source = row[57] or ""
    hits = _terms(location + " " + source)
    # A pair is in the Arctic sample when the coded action location is above
    # 60N or the location/source text contains a declared Arctic term.
    if not (lat is not None and lat >= 60) and not hits:
        return None
    try:
        event_date = datetime.strptime(row[1], "%Y%m%d").date().isoformat()
        quad = int(row[29])
    except (ValueError, TypeError):
        return None
    if quad not in QUAD:
        return None
    return {
        "id": f"{dataset.lower().replace(' ', '')}:{row[0]}",
        "date": event_date,
        "archive_date": archive_date,
        "actor1": row[7],
        "actor2": row[17],
        "actor1_name": row[6],
        "actor2_name": row[16],
        "event_code": row[26],
        "quad_class": quad,
        "category": QUAD[quad],
        "goldstein": _float(row[30]),
        "avg_tone": _float(row[34]),
        "num_mentions": int(row[31] or 0),
        "num_sources": int(row[32] or 0),
        "num_articles": int(row[33] or 0),
        "latitude": lat,
        "longitude": _float(row[54]),
        "location": location,
        "source_url": source,
        "source_line": line,
        "dataset": dataset,
        "filter_reasons": hits or ["行动地理编码 ≥ 60°N"],
    }


def parse_zip(path: Path, archive_date: str, dataset: str) -> tuple[list[dict], dict]:
    url = f"https://data.gdeltproject.org/events/{archive_date.replace('-', '')}.export.CSV.zip"
    events: dict[str, dict] = {}
    scanned = 0
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1 or archive.testzip() is not None:
            raise ValueError(f"invalid archive: {path.name}")
        with archive.open(names[0]) as stream:
            for line, row in enumerate(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace"), delimiter="\t"), 1):
                scanned += 1
                event = _row_event(row, archive_date, line, dataset, url)
                if event:
                    events[event["id"]] = event
    return list(events.values()), {
        "archive_date": archive_date, "dataset": dataset, "url": url,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size, "scanned_rows": scanned,
        "candidate_events": len(events),
    }


def existing_2019() -> tuple[list[dict], dict]:
    events = []
    sources = []
    for path in sorted((ROOT / "data/analysis/gdelt/daily").glob("2019-09-*.json")):
        package = json.loads(path.read_text(encoding="utf-8"))
        sources.append(package["source"])
        for row in package.get("records", []):
            if row.get("actor1_country") not in COUNTRIES or row.get("actor2_country") not in COUNTRIES:
                continue
            if row["actor1_country"] == row["actor2_country"]:
                continue
            events.append({
                "id": row["id"], "date": row["date"], "archive_date": row["archive_date"],
                "actor1": row["actor1_country"], "actor2": row["actor2_country"],
                "actor1_name": row.get("actor1", ""), "actor2_name": row.get("actor2", ""),
                "event_code": row.get("event_code", ""), "quad_class": row["quad_class"],
                "category": row["category"], "goldstein": row.get("goldstein"), "avg_tone": None,
                "num_mentions": 1, "num_sources": 1, "num_articles": 1,
                "latitude": row.get("latitude"), "longitude": row.get("longitude"),
                "location": row.get("location", ""), "source_url": row.get("source_url", ""),
                "source_line": row.get("source_line"), "dataset": row.get("dataset", "GDELT 1.0"),
                "filter_reasons": row.get("relevance_reasons", []),
            })
    return events, {"archive_date": "2019-09-17/23", "dataset": "GDELT 1.0", "sources": sources,
                    "scanned_rows": sum(json.loads(p.read_text(encoding="utf-8")).get("coverage", {}).get("scanned_rows", 0) for p in sorted((ROOT / "data/analysis/gdelt/daily").glob("2019-09-*.json"))),
                    "candidate_events": len(events)}


def aggregate(events: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for event in events:
        key = tuple(sorted((event["actor1"], event["actor2"])))
        groups[key].append(event)
    edges = []
    for (source, target), rows in sorted(groups.items()):
        positive = sum(r["quad_class"] in (1, 2) for r in rows)
        negative = sum(r["quad_class"] in (3, 4) for r in rows)
        gold = [r["goldstein"] for r in rows if r.get("goldstein") is not None]
        tones = [r["avg_tone"] for r in rows if r.get("avg_tone") is not None]
        edges.append({
            "source": source, "target": target, "event_count": len(rows),
            "article_count": sum(r.get("num_articles", 0) for r in rows),
            "mention_count": sum(r.get("num_mentions", 0) for r in rows),
            "source_count": sum(r.get("num_sources", 0) for r in rows),
            "positive_events": positive, "negative_events": negative,
            "goldstein_mean": round(sum(gold) / len(gold), 3) if gold else None,
            "tone_mean": round(sum(tones) / len(tones), 3) if tones else None,
            "first_date": min(r["date"] for r in rows), "last_date": max(r["date"] for r in rows),
            "categories": dict(Counter(r["category"] for r in rows)),
            "event_ids": [r["id"] for r in rows[:80]],
        })
    degree = Counter()
    articles = Counter()
    for edge in edges:
        degree[edge["source"]] += edge["event_count"]
        degree[edge["target"]] += edge["event_count"]
        articles[edge["source"]] += edge["article_count"]
        articles[edge["target"]] += edge["article_count"]
    nodes = [{"code": code, **COUNTRIES[code], "event_degree": degree[code], "article_degree": articles[code]} for code in COUNTRIES]
    return edges, nodes


def main() -> None:
    windows = []
    for year in (2015, 2020, 2025):
        path = RAW / f"{year}-09-15.export.CSV.zip"
        # The GDELT 2.0 daily archive begins in February 2015; the selected
        # 2015, 2020 and 2025 files therefore share the 2.0 label.
        events, source = parse_zip(path, f"{year}-09-15", "GDELT 2.0")
        edges, nodes = aggregate(events)
        windows.append({"id": str(year), "label": f"{year} · 9月15日样本", "year": year,
                        "date_start": f"{year}-09-15", "date_end": f"{year}-09-15",
                        "events": events, "edges": edges, "nodes": nodes, "source": source,
                        "sample_note": "单日档案样本；用于交互展示和方法试验，不能解释为全年统计。"})
    events, source = existing_2019();edges, nodes = aggregate(events)
    windows.insert(1, {"id": "2019", "label": "2019 · 9月17—23日窗口", "year": 2019,
                        "date_start": "2019-09-17", "date_end": "2019-09-23", "events": events,
                        "edges": edges, "nodes": nodes, "source": source,
                        "sample_note": "沿用已整理的 MOSAiC 启航窗口；7 个日档，不是全年统计。"})
    package = {
        "version": "gdelt-arctic-network-20261013-v1", "generated_at": "2026-10-13",
        "dataset_note": "国家对网络由 GDELT 机器编码事件聚合而来；它描述新闻中的互动记录，不等同于外交关系强度。",
        "scope": "节点为中国、美国、俄罗斯、加拿大、挪威、丹麦、芬兰、瑞典和冰岛；事件需同时识别两个节点，且行动地理位于北纬60度以北或来源/地名含声明的北极词项。",
        "aggregation": {"edge_width": "article_count（无文章数时退回事件数）", "edge_color": "QuadClass 合作/冲突及 Goldstein 均值", "node_size": "事件度数"},
        "countries": [{"code": code, **COUNTRIES[code]} for code in COUNTRIES], "windows": windows,
        "limitations": ["年份之间是选定日档或短窗口，不能当作完整年度序列。", "报道数量受到语言、媒体覆盖与 GDELT 机器编码影响。", "GoldsteinScale按事件类型赋值，不是调查得到的国家关系评分。", "正式研究结论需扩展日档、去重现实事件并进行人工核验。"],
        "citations": [{"title": "GDELT Event Database", "url": "https://gdeltproject.org/data.html"}, {"title": "GDELT Event Codebook V2.0", "url": "https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf"}, {"title": "北京师范大学全球新闻事件数据共享平台", "url": "https://gde.bnu.edu.cn/"}],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "windows": [(w["id"], len(w["events"]), len(w["edges"])) for w in windows]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
