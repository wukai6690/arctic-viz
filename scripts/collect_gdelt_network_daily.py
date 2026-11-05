"""Collect compact daily Arctic bilateral GDELT aggregates.

The raw GDELT daily archive is downloaded only long enough to parse it. The
published output keeps one small JSON file per archive date with country-pair
aggregates and a few source URLs for evidence drill-down. Raw ZIP files are
removed after successful processing unless ``--keep-raw`` is supplied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/gdelt_network"
OUT_DIR = ROOT / "data/analysis/gdelt/network/daily"
MANIFEST_PATH = ROOT / "data/analysis/gdelt/network/daily_manifest.json"

NODES = {"CHN", "USA", "RUS", "CAN", "NOR", "DNK", "FIN", "SWE", "ISL"}
QUAD = {1: "言语合作", 2: "物质合作", 3: "言语冲突", 4: "物质冲突"}
TERMS = (
    "arctic", "svalbard", "spitsbergen", "barents", "kara sea", "chukchi",
    "beaufort", "greenland", "murmansk", "tromso", "tromsø", "sabetta",
    "northern sea route", "northwest passage", "ny-alesund", "north pole",
    "北极", "格陵兰",
)
FILTER_VERSION = "arctic-bilateral-daily-v1"


def _terms(text: str) -> list[str]:
    normalized = re.sub(r"[-_]+", " ", unquote(str(text)).casefold())
    return [term for term in TERMS if re.search(r"(?<![a-z])" + re.escape(term.replace("-", " ")) + r"(?![a-z])", normalized)]


def _float(value: str) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _int(value: str) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def _download(day: date, raw_path: Path) -> bytes:
    if raw_path.exists():
        return raw_path.read_bytes()
    url = f"https://data.gdeltproject.org/events/{day:%Y%m%d}.export.CSV.zip"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(20, 180), headers={"User-Agent": "ArcticResearch/1.0 (bilateral daily archive)"}) as response:
                response.raise_for_status()
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(262144):
                    size += len(chunk)
                    if size > 100_000_000:
                        raise ValueError("daily archive exceeds 100 MB safety limit")
                    chunks.append(chunk)
                body = b"".join(chunks)
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                if archive.testzip() is not None:
                    raise ValueError("ZIP CRC mismatch")
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(body)
            return body
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 + attempt)
    raise RuntimeError(f"download failed for {day.isoformat()}: {last_error}")


def _parse_archive(body: bytes, archive_date: date) -> tuple[dict[str, dict], dict[str, int]]:
    groups: dict[str, dict] = {}
    scanned = 0
    candidate_events = 0
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise ValueError("unexpected ZIP member count")
        with archive.open(names[0]) as stream:
            reader = csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace"), delimiter="\t")
            for row in reader:
                scanned += 1
                if len(row) != 58:
                    continue
                actor1, actor2 = row[7].strip().upper(), row[17].strip().upper()
                if actor1 not in NODES or actor2 not in NODES or actor1 == actor2:
                    continue
                lat = _float(row[53])
                location = row[50] or ""
                source_url = row[57] or ""
                hits = _terms(location + " " + source_url)
                if not (lat is not None and lat >= 60) and not hits:
                    continue
                quad = _int(row[29])
                if quad not in QUAD or not row[0].isdigit():
                    continue
                event_day = str(row[1])
                if len(event_day) != 8 or not event_day.isdigit():
                    continue
                try:
                    event_date = date(int(event_day[:4]), int(event_day[4:6]), int(event_day[6:8]))
                except ValueError:
                    continue
                if event_date > archive_date:
                    continue
                key = "|".join(sorted((actor1, actor2)))
                edge = groups.setdefault(key, {
                    "source": min(actor1, actor2),
                    "target": max(actor1, actor2),
                    "event_count": 0,
                    "article_count": 0,
                    "mention_count": 0,
                    "source_count": 0,
                    "positive_events": 0,
                    "negative_events": 0,
                    "goldstein_sum": 0.0,
                    "goldstein_count": 0,
                    "tone_sum": 0.0,
                    "tone_count": 0,
                    "event_date_min": event_date.isoformat(),
                    "event_date_max": event_date.isoformat(),
                    "event_ids": [],
                    "source_urls": [],
                    "_top_scores": [],
                })
                candidate_events += 1
                edge["event_count"] += 1
                edge["article_count"] += _int(row[33])
                edge["mention_count"] += _int(row[31])
                edge["source_count"] += _int(row[32])
                edge["positive_events"] += int(quad in (1, 2))
                edge["negative_events"] += int(quad in (3, 4))
                goldstein = _float(row[30])
                if goldstein is not None:
                    edge["goldstein_sum"] += goldstein
                    edge["goldstein_count"] += 1
                tone = _float(row[34])
                if tone is not None:
                    edge["tone_sum"] += tone
                    edge["tone_count"] += 1
                edge["event_date_min"] = min(edge["event_date_min"], event_date.isoformat())
                edge["event_date_max"] = max(edge["event_date_max"], event_date.isoformat())
                event_id = "gdelt:" + row[0]
                if len(edge["event_ids"]) < 20:
                    edge["event_ids"].append(event_id)
                if source_url:
                    score = _int(row[33]) * 10 + _int(row[31])
                    edge["_top_scores"].append((score, source_url))
    return groups, {"scanned_rows": scanned, "candidate_events": candidate_events}


def _finalize_edge(edge: dict) -> dict:
    event_count = max(1, edge["event_count"])
    top_urls: list[str] = []
    for _, url in sorted(edge.pop("_top_scores"), reverse=True):
        if url not in top_urls:
            top_urls.append(url)
        if len(top_urls) >= 3:
            break
    edge["source_urls"] = top_urls
    goldstein_count = edge.pop("goldstein_count")
    tone_count = edge.pop("tone_count")
    edge["goldstein_mean"] = round(edge.pop("goldstein_sum") / goldstein_count, 3) if goldstein_count else None
    edge["tone_mean"] = round(edge.pop("tone_sum") / tone_count, 3) if tone_count else None
    edge["event_date_range"] = f"{edge.pop('event_date_min')}—{edge.pop('event_date_max')}"
    edge["relation_class"] = "合作" if edge["positive_events"] > edge["negative_events"] else "冲突" if edge["negative_events"] > edge["positive_events"] else "混合"
    return edge


def collect_day(day: date, keep_raw: bool) -> dict:
    output_path = OUT_DIR / f"{day.isoformat()}.json"
    if output_path.exists():
        try:
            package = json.loads(output_path.read_text(encoding="utf-8"))
            if package.get("filter_version") == FILTER_VERSION:
                return {"date": day.isoformat(), "status": "cached", "pair_rows": len(package.get("edges", []))}
        except (OSError, json.JSONDecodeError):
            pass
    raw_path = RAW_DIR / f"{day:%Y%m%d}.export.CSV.zip"
    body = _download(day, raw_path)
    digest = hashlib.sha256(body).hexdigest()
    groups, stats = _parse_archive(body, day)
    edges = [_finalize_edge(groups[key]) for key in sorted(groups)]
    package = {
        "archive_date": day.isoformat(),
        "dataset": "GDELT 1.0 daily export",
        "filter_version": FILTER_VERSION,
        "source": {"url": f"https://data.gdeltproject.org/events/{day:%Y%m%d}.export.CSV.zip", "sha256": digest, "bytes": len(body)},
        "coverage": {**stats, "pair_rows": len(edges)},
        "edges": edges,
    }
    _atomic_json(output_path, package)
    if not keep_raw:
        try:
            raw_path.unlink()
        except FileNotFoundError:
            pass
    return {"date": day.isoformat(), "status": "ok", "pair_rows": len(edges), **stats}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--max-files", type=int, default=31)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--keep-raw", action="store_true")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if start > end or not date(2013, 4, 1) <= start:
        raise ValueError("use a completed GDELT daily archive range from 2013-04-01 onward")
    if not 1 <= args.max_files <= 366 or not 1 <= args.workers <= 4:
        raise ValueError("max-files must be 1–366 and workers must be 1–4")
    days = [start + timedelta(days=index) for index in range((end - start).days + 1)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    todo = [day for day in days if not (OUT_DIR / f"{day.isoformat()}.json").exists()][:args.max_files]
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(collect_day, day, args.keep_raw): day for day in todo}
        for future in as_completed(futures):
            day = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {"date": day.isoformat(), "status": "failed", "error": type(error).__name__, "message": str(error)}
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    previous = {}
    if MANIFEST_PATH.exists():
        try:
            previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = {}
    statuses = dict(previous.get("days", {}))
    for result in results:
        statuses[result["date"]] = result
    manifest = {
        "filter_version": FILTER_VERSION,
        "requested_start": start.isoformat(),
        "requested_end": end.isoformat(),
        "requested_days": len(days),
        "completed_days": sum(statuses.get(day.isoformat(), {}).get("status") in {"ok", "cached"} for day in days),
        "missing_or_failed_days": [day.isoformat() for day in days if statuses.get(day.isoformat(), {}).get("status") not in {"ok", "cached"}],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "days": statuses,
    }
    _atomic_json(MANIFEST_PATH, manifest)
    if any(result.get("status") == "failed" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
