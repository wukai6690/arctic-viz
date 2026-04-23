#!/usr/bin/env python3
"""
轻量版 GDELT 1.0 + GDELT 2.0 清洗脚本

特点：
- GDELT 1.0 默认按文件、按块(chunksize)处理，避免一次性读入所有数据
- 默认只输出推荐保留的记录，显著降低内存与磁盘占用
- 支持本地 ZIP 和从 GDELT 1.0 index.html 按日期抓取
- GDELT 2.0 继续通过 DOC API 抓取文章与时间线，增加容错与限流处理
- GDELT 2.0 采用 API 粗筛 + 本地精筛策略，避免超长查询导致报错

依赖：pandas requests
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import tempfile
import time  # 用于增加请求延时，防止触发 GDELT 反爬限制
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd
import requests

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT1_INDEX_URL = "http://data.gdeltproject.org/events/index.html"
GDELT1_BASE_URL = "http://data.gdeltproject.org/events/"

# GDELT 1.0 front file columns (2013-04-01 之后)
GDELT1_FRONT_COLUMNS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode", "Actor1Geo_ADM1Code",
    "Actor1Geo_Lat", "Actor1Geo_Long", "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode", "Actor2Geo_ADM1Code",
    "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode", "ActionGeo_ADM1Code",
    "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# 只保留分析需要的列，显著降低内存压力
GDELT1_USECOLS = [
    "GLOBALEVENTID", "SQLDATE",
    "Actor1Code", "Actor1Name", "Actor1CountryCode",
    "Actor2Code", "Actor2Name", "Actor2CountryCode",
    "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
    "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
    "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "ActionGeo_FullName", "ActionGeo_CountryCode",
    "SOURCEURL",
]
GDELT1_USECOL_INDEXES = [GDELT1_FRONT_COLUMNS.index(c) for c in GDELT1_USECOLS]

ARCTIC_STAKEHOLDER_CODES = {
    "USA", "CAN", "RUS", "NOR", "DNK", "ISL", "FIN", "SWE", "CHN",
    "JPN", "KOR", "DEU", "FRA", "GBR", "EU",
}
TEXT_GROUPS = ["space", "actor", "technology", "geopolitics", "climate", "resource"]
TEXT_COLS_GDELT1 = [
    "Actor1Name", "Actor2Name", "Actor1Code", "Actor2Code",
    "Actor1Geo_FullName", "Actor2Geo_FullName", "ActionGeo_FullName", "SOURCEURL",
]


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def normalize_priority(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(str(value).strip().lower(), 0)


def parse_ymd_date(value: str) -> datetime:
    return datetime.strptime(str(value), "%Y-%m-%d")


def count_matches(text: str, patterns: Sequence[re.Pattern]) -> int:
    if not text:
        return 0
    total = 0
    for patt in patterns:
        if patt.search(text):
            total += 1
    return total


@dataclass
class KeywordTable:
    df: pd.DataFrame

    @classmethod
    def from_csv(cls, csv_path: str | Path) -> "KeywordTable":
        df = pd.read_csv(csv_path)
        required = {"group", "keyword"}
        if not required.issubset(df.columns):
            raise ValueError(f"关键词 CSV 缺少必要列: {required}")
        if "priority" not in df.columns:
            df["priority"] = "medium"
        if "use_for_filter" not in df.columns:
            df["use_for_filter"] = 1
        df = df.fillna("").copy()
        df["group"] = df["group"].astype(str).str.strip().str.lower()
        df["keyword"] = df["keyword"].astype(str).str.strip()
        df["priority_rank"] = df["priority"].map(normalize_priority)
        df["use_for_filter"] = pd.to_numeric(df["use_for_filter"], errors="coerce").fillna(1).astype(int)
        df = df[df["keyword"] != ""].copy()
        return cls(df=df)

    def terms(self, group: str, min_priority: str = "medium", top_n: Optional[int] = None, only_active: bool = True) -> List[str]:
        rank = normalize_priority(min_priority)
        out = self.df[self.df["group"] == str(group).lower()].copy()
        if only_active:
            out = out[out["use_for_filter"] == 1]
        out = out[out["priority_rank"] >= rank].sort_values(["priority_rank", "keyword"], ascending=[False, True])
        terms = out["keyword"].drop_duplicates().tolist()
        return terms[:top_n] if top_n else terms

    def compile_matchers(self, only_active: bool = True) -> Dict[str, List[re.Pattern]]:
        matchers: Dict[str, List[re.Pattern]] = {}
        for group in sorted(self.df["group"].unique()):
            out = self.df[self.df["group"] == group].copy()
            if only_active and group != "noise":
                out = out[out["use_for_filter"] == 1]
            patterns = []
            for term in out["keyword"].drop_duplicates().tolist():
                term = str(term).strip().strip('"')
                if not term:
                    continue
                if re.search(r"\s", term):
                    patt = re.compile(re.escape(term), re.IGNORECASE)
                else:
                    patt = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)
                patterns.append(patt)
            matchers[group] = patterns
        return matchers


# -----------------------------
# GDELT 1.0：轻量流式处理
# -----------------------------
def fetch_gdelt1_index_urls(index_url: str = GDELT1_INDEX_URL, base_url: str = GDELT1_BASE_URL) -> List[str]:
    resp = requests.get(index_url, timeout=60)
    resp.raise_for_status()
    files = sorted(set(re.findall(r"(\d{8}\.export\.CSV\.zip)", resp.text)))
    return [base_url + f for f in files]


def filter_gdelt1_urls_by_date(urls: Sequence[str], start_date: str, end_date: str) -> List[str]:
    start_dt = parse_ymd_date(start_date)
    end_dt = parse_ymd_date(end_date)
    selected = []
    for url in urls:
        m = re.search(r"(\d{8})\.export\.CSV\.zip$", str(url))
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y%m%d")
        if start_dt <= dt <= end_dt:
            selected.append(str(url))
    return selected


def iter_local_event_files(pattern: str | Path) -> List[str]:
    files = sorted(glob.glob(str(pattern)))
    if not files:
        raise FileNotFoundError(f"未找到文件: {pattern}")
    return files


def download_to_local(url: str, cache_dir: Optional[Path] = None) -> Tuple[str, bool]:
    """返回本地 zip 路径, 是否需要后续删除"""
    filename = url.rsplit("/", 1)[-1]
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / filename
        if target.exists() and target.stat().st_size > 0:
            return str(target), False
        tmp_path = target
        need_cleanup = False
    else:
        fd, tmp_name = tempfile.mkstemp(suffix=".zip", prefix="gdelt1_")
        os.close(fd)
        tmp_path = Path(tmp_name)
        need_cleanup = True

    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return str(tmp_path), need_cleanup


def iter_event_chunks_from_zip(zip_path: str, chunksize: int) -> Iterator[pd.DataFrame]:
    reader = pd.read_csv(
        zip_path,
        sep="\t",
        header=None,
        names=GDELT1_FRONT_COLUMNS,
        usecols=GDELT1_USECOL_INDEXES,
        compression="zip",
        dtype=str,
        low_memory=True,
        on_bad_lines="skip",
        chunksize=chunksize,
    )
    for chunk in reader:
        chunk["_source_file"] = os.path.basename(zip_path)
        yield chunk


def clean_gdelt1_chunk(df: pd.DataFrame, kw: KeywordTable, stakeholder_codes: Optional[set[str]] = None) -> pd.DataFrame:
    if stakeholder_codes is None:
        stakeholder_codes = ARCTIC_STAKEHOLDER_CODES

    df = df.copy()
    if "SQLDATE" in df.columns:
        df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], format="%Y%m%d", errors="coerce")
        df["year_month"] = df["SQLDATE"].dt.to_period("M").astype(str)

    for col in ["GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Actor1CountryCode", "Actor2CountryCode", "ActionGeo_CountryCode", "Actor1Geo_CountryCode", "Actor2Geo_CountryCode"]:
        if col not in df.columns:
            df[col] = ""

    df["has_stakeholder"] = (
        df["Actor1CountryCode"].isin(stakeholder_codes)
        | df["Actor2CountryCode"].isin(stakeholder_codes)
        | df["ActionGeo_CountryCode"].isin(stakeholder_codes)
        | df["Actor1Geo_CountryCode"].isin(stakeholder_codes)
        | df["Actor2Geo_CountryCode"].isin(stakeholder_codes)
    ).astype(int)

    text_cols = [c for c in TEXT_COLS_GDELT1 if c in df.columns]
    df["_match_text"] = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)

    active_matchers = kw.compile_matchers(only_active=True)
    all_matchers = kw.compile_matchers(only_active=False)
    noise_matchers = all_matchers.get("noise", [])

    for group in TEXT_GROUPS:
        patterns = active_matchers.get(group, [])
        df[f"{group}_match_count"] = df["_match_text"].apply(lambda x: count_matches(str(x), patterns))
        df[f"has_{group}"] = (df[f"{group}_match_count"] > 0).astype(int)

    df["noise_match_count"] = df["_match_text"].apply(lambda x: count_matches(str(x), noise_matchers))
    df["is_noise_suspect"] = (df["noise_match_count"] > 0).astype(int)

    thematic_sum = df[["has_space", "has_actor", "has_technology", "has_geopolitics", "has_climate", "has_resource"]].sum(axis=1)
    df["recommended_keep"] = ((df["has_stakeholder"] == 1) & (thematic_sum >= 1) & (df["is_noise_suspect"] == 0)).astype(int)

    keep_cols = [
        "GLOBALEVENTID", "SQLDATE", "year_month",
        "Actor1Name", "Actor1CountryCode", "Actor2Name", "Actor2CountryCode",
        "EventCode", "EventBaseCode", "EventRootCode", "QuadClass",
        "GoldsteinScale", "NumMentions", "NumSources", "NumArticles", "AvgTone",
        "ActionGeo_FullName", "ActionGeo_CountryCode", "SOURCEURL",
        "has_stakeholder",
        "has_space", "has_actor", "has_technology", "has_geopolitics", "has_climate", "has_resource",
        "noise_match_count", "is_noise_suspect", "recommended_keep",
        "_source_file",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    return df[keep_cols].copy()


def update_monthly_agg(agg_map: Dict[Tuple, Dict[str, float]], cleaned_chunk: pd.DataFrame) -> None:
    if cleaned_chunk.empty:
        return
    work = cleaned_chunk[cleaned_chunk["recommended_keep"] == 1].copy()
    if work.empty:
        return
    group_cols = ["year_month", "Actor1CountryCode", "Actor2CountryCode", "EventRootCode"]
    grouped = work.groupby(group_cols, dropna=False)

    for key, sub in grouped:
        stats = agg_map[key]
        stats["event_count"] += float(len(sub))
        stats["mentions_sum"] += float(pd.to_numeric(sub["NumMentions"], errors="coerce").fillna(0).sum())
        stats["sources_sum"] += float(pd.to_numeric(sub["NumSources"], errors="coerce").fillna(0).sum())
        stats["articles_sum"] += float(pd.to_numeric(sub["NumArticles"], errors="coerce").fillna(0).sum())

        gs = pd.to_numeric(sub["GoldsteinScale"], errors="coerce")
        stats["goldstein_sum"] += float(gs.fillna(0).sum())
        stats["goldstein_count"] += float(gs.notna().sum())

        tone = pd.to_numeric(sub["AvgTone"], errors="coerce")
        stats["tone_sum"] += float(tone.fillna(0).sum())
        stats["tone_count"] += float(tone.notna().sum())


def agg_map_to_df(agg_map: Dict[Tuple, Dict[str, float]]) -> pd.DataFrame:
    rows = []
    for key, stats in agg_map.items():
        year_month, actor1, actor2, event_root = key
        rows.append({
            "year_month": year_month,
            "Actor1CountryCode": actor1,
            "Actor2CountryCode": actor2,
            "EventRootCode": event_root,
            "event_count": int(stats["event_count"]),
            "mentions_sum": stats["mentions_sum"],
            "sources_sum": stats["sources_sum"],
            "articles_sum": stats["articles_sum"],
            "goldstein_mean": (stats["goldstein_sum"] / stats["goldstein_count"]) if stats["goldstein_count"] else None,
            "tone_mean": (stats["tone_sum"] / stats["tone_count"]) if stats["tone_count"] else None,
        })
    return pd.DataFrame(rows)


def iter_event_sources(events_file_pattern: Optional[str], start_date: Optional[str], end_date: Optional[str], max_files: Optional[int]) -> Tuple[str, List[str]]:
    if events_file_pattern:
        files = iter_local_event_files(events_file_pattern)
        return "local", files[:max_files] if max_files else files

    if not start_date or not end_date:
        raise ValueError("请提供 --events，或同时提供 --start-date 和 --end-date")

    urls = fetch_gdelt1_index_urls()
    selected = filter_gdelt1_urls_by_date(urls, start_date, end_date)
    return "remote", selected[:max_files] if max_files else selected


def run_gdelt1_pipeline(
    keyword_csv: str | Path,
    output_dir: str | Path,
    events_file_pattern: Optional[str | Path] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_files: Optional[int] = None,
    chunksize: int = 20000,
    keep_all_cleaned: bool = False,
    cache_dir: Optional[str | Path] = None,
) -> None:
    outdir = ensure_dir(output_dir)
    kw = KeywordTable.from_csv(keyword_csv)

    cleaned_csv = outdir / "gdelt1_events_cleaned.csv"
    monthly_csv = outdir / "gdelt1_events_monthly_panel.csv"
    summary_json = outdir / "gdelt1_summary.json"
    failed_json = outdir / "gdelt1_failed_files.json"

    for fp in [cleaned_csv, monthly_csv, summary_json, failed_json]:
        if fp.exists():
            fp.unlink()

    source_mode, sources = iter_event_sources(
        events_file_pattern=str(events_file_pattern) if events_file_pattern else None,
        start_date=start_date,
        end_date=end_date,
        max_files=max_files,
    )

    cache_path = ensure_dir(cache_dir) if cache_dir else None
    failed_files: List[dict] = []
    monthly_agg: Dict[Tuple, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    write_header = True

    total_rows = 0
    total_cleaned_rows = 0
    total_kept_rows = 0

    for idx, source in enumerate(sources, start=1):
        local_zip = None
        need_cleanup = False
        try:
            if source_mode == "remote":
                print(f"[{idx}/{len(sources)}] 下载并处理 {source}")
                local_zip, need_cleanup = download_to_local(source, cache_dir=cache_path)
                source_label = source
            else:
                print(f"[{idx}/{len(sources)}] 处理本地文件 {source}")
                local_zip = source
                source_label = source

            for chunk in iter_event_chunks_from_zip(local_zip, chunksize=chunksize):
                total_rows += len(chunk)
                chunk["_source_file"] = os.path.basename(source_label)
                cleaned_chunk = clean_gdelt1_chunk(chunk, kw)
                total_cleaned_rows += len(cleaned_chunk)
                total_kept_rows += int(cleaned_chunk["recommended_keep"].sum())

                update_monthly_agg(monthly_agg, cleaned_chunk)

                out_chunk = cleaned_chunk if keep_all_cleaned else cleaned_chunk[cleaned_chunk["recommended_keep"] == 1].copy()
                if not out_chunk.empty:
                    out_chunk.to_csv(cleaned_csv, mode="a", header=write_header, index=False, encoding="utf-8-sig")
                    write_header = False

            if need_cleanup and local_zip and os.path.exists(local_zip):
                os.remove(local_zip)

        except Exception as e:
            failed_files.append({"source": source, "error": str(e)})
            print(f"处理失败: {source} -> {e}")
            if need_cleanup and local_zip and os.path.exists(local_zip):
                try:
                    os.remove(local_zip)
                except OSError:
                    pass

    monthly_df = agg_map_to_df(monthly_agg)
    if not monthly_df.empty:
        monthly_df.to_csv(monthly_csv, index=False, encoding="utf-8-sig")

    with open(failed_json, "w", encoding="utf-8") as f:
        json.dump(failed_files, f, ensure_ascii=False, indent=2)

    summary = {
        "source_mode": source_mode,
        "files_requested": len(sources),
        "files_failed": len(failed_files),
        "rows_read_total": total_rows,
        "rows_cleaned_total": total_cleaned_rows,
        "rows_recommended_keep_total": total_kept_rows,
        "output_cleaned_csv": str(cleaned_csv),
        "output_monthly_csv": str(monthly_csv),
        "keep_all_cleaned": keep_all_cleaned,
        "chunksize": chunksize,
    }
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("完成。")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


# -----------------------------
# GDELT 2.0 DOC API
# -----------------------------
def phrase_needs_quotes(term: str) -> bool:
    return bool(re.search(r"\s", str(term)))


def escape_query_term(term: str) -> str:
    term = str(term).strip()
    if not term:
        return term
    if term.startswith('"') and term.endswith('"'):
        return term
    return f'"{term}"' if phrase_needs_quotes(term) else term


def build_or_block(terms: Sequence[str]) -> str:
    cleaned = [escape_query_term(t) for t in terms if str(t).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "(" + " OR ".join(cleaned) + ")"


def build_negative_block(noise_terms: Sequence[str]) -> str:
    return " ".join([f"-{escape_query_term(t)}" for t in noise_terms if str(t).strip()])


def build_doc_queries(kw: KeywordTable, min_priority: str = "medium", top_n_per_group: int = 6) -> List[Tuple[str, str]]:
    # 强制限制发往 API 的每组关键词数量最多为 2
    api_top_n = 2
    space = kw.terms("space", min_priority=min_priority, top_n=api_top_n)
    actor = kw.terms("actor", min_priority=min_priority, top_n=api_top_n)
    tech = kw.terms("technology", min_priority=min_priority, top_n=api_top_n)
    geo = kw.terms("geopolitics", min_priority=min_priority, top_n=api_top_n)
    climate = kw.terms("climate", min_priority=min_priority, top_n=api_top_n)
    resource = kw.terms("resource", min_priority=min_priority, top_n=api_top_n)

    # 彻底去掉 API 请求中的噪音排除词 (-noise)
    # 所有噪音词（如 cruise, penguin）留给本地的 Pandas 处理，避免撑爆 API URL
    queries = []

    def add(name: str, *parts: str) -> None:
        q = " ".join([p for p in parts if p]).strip()
        queries.append((name, q))

    # 构造极简版的查询语句
    add("space_tech", build_or_block(space), build_or_block(tech + resource))
    add("space_tech_geo", build_or_block(space), build_or_block(tech + resource), build_or_block(geo))
    add("space_actor_geo", build_or_block(space), build_or_block(actor), build_or_block(geo))
    add("space_climate_tech", build_or_block(space), build_or_block(climate), build_or_block(tech + resource))
    add("space_actor_tech", build_or_block(space), build_or_block(actor), build_or_block(tech))
    
    # 将硬编码的部分也精简
    add("china_arctic",
        build_or_block(["Arctic", "High North"]),
        build_or_block(["China", "Chinese"]))
        
    return queries


def gdelt_doc_request(query: str, mode: str, timespan: str, maxrecords: int = 250, sort: str = "hybridrel") -> dict:
    """带容错和限流处理的请求模块"""
    params = {
        "query": query,
        "mode": mode,
        "timespan": timespan,
        "maxrecords": maxrecords,
        "format": "json",
        "sort": sort,
    }
    
    try:
        resp = requests.get(GDELT_DOC_API, params=params, timeout=90)
        # 强制暂停 2 秒，防止触发 GDELT API 频率限制
        time.sleep(2)
        
        # 检查是否是 200 成功状态码
        if resp.status_code != 200:
            print(f"\n[HTTP 错误] 状态码: {resp.status_code} | Mode: {mode}")
            print(f"请求 URL: {resp.url}")
            print(f"服务器返回内容摘要: {resp.text[:200]}")
            return {}
            
        return resp.json()
        
    except requests.exceptions.JSONDecodeError as e:
        print(f"\n[JSON 解析错误] GDELT 未返回标准 JSON | Mode: {mode}")
        print(f"请求 URL: {resp.url}")
        print(f"服务器实际返回内容: {resp.text[:500]}")
        return {}
    except Exception as e:
        print(f"\n[请求异常] 网络或其他错误: {e} | Mode: {mode}")
        return {}


def extract_timeline_to_df(payload: dict, query_name: str, query: str) -> pd.DataFrame:
    rows = []
    for item in payload.get("timeline", []):
        rec = dict(item)
        rec["query_name"] = query_name
        rec["query"] = query
        rows.append(rec)
    return pd.DataFrame(rows)


def extract_source_country_timeline(payload: dict, query_name: str, query: str) -> pd.DataFrame:
    rows = []
    for item in payload.get("timeline", []):
        base = {"date": item.get("date"), "datetime": item.get("datetime"), "query_name": query_name, "query": query}
        series = item.get("series")
        if isinstance(series, list):
            for sub in series:
                rec = dict(base)
                if isinstance(sub, dict):
                    rec.update(sub)
                rows.append(rec)
        else:
            rec = dict(base)
            rec.update({k: v for k, v in item.items() if k not in base})
            rows.append(rec)
    return pd.DataFrame(rows)


def postprocess_doc_articles(df: pd.DataFrame, kw: KeywordTable) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "seendate" in out.columns:
        out["seendate"] = pd.to_datetime(out["seendate"], errors="coerce")
        out["year_month"] = out["seendate"].dt.to_period("M").astype(str)

    text_cols = [c for c in ["title", "url", "domain", "sourcecountry", "language"] if c in out.columns]
    out["_match_text"] = out[text_cols].fillna("").astype(str).agg(" ".join, axis=1)

    active_matchers = kw.compile_matchers(only_active=True)
    all_matchers = kw.compile_matchers(only_active=False)
    noise_matchers = all_matchers.get("noise", [])

    for group in TEXT_GROUPS:
        patterns = active_matchers.get(group, [])
        out[f"{group}_match_count"] = out["_match_text"].apply(lambda x: count_matches(str(x), patterns))
        out[f"has_{group}"] = (out[f"{group}_match_count"] > 0).astype(int)

    out["noise_match_count"] = out["_match_text"].apply(lambda x: count_matches(str(x), noise_matchers))
    out["is_noise_suspect"] = (out["noise_match_count"] > 0).astype(int)
    thematic_sum = out[["has_actor", "has_technology", "has_geopolitics", "has_climate", "has_resource"]].sum(axis=1)
    out["recommended_keep"] = ((out["has_space"] == 1) & (thematic_sum >= 1) & (out["is_noise_suspect"] == 0)).astype(int)
    return out.drop(columns=["_match_text"], errors="ignore")


def build_doc_monthly_panel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["tone", "norm", "numarticles"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    group_cols = [c for c in ["year_month", "query_name", "sourcecountry", "language"] if c in out.columns]
    if not group_cols:
        group_cols = ["query_name"]
    agg = {"url": "count"} if "url" in out.columns else {}
    if "tone" in out.columns:
        agg["tone"] = "mean"
    if "norm" in out.columns:
        agg["norm"] = "mean"
    monthly = out.groupby(group_cols, dropna=False).agg(agg).reset_index()
    if "url" in monthly.columns:
        monthly = monthly.rename(columns={"url": "article_count"})
    return monthly


def run_gdelt2_doc_pipeline(
    keyword_csv: str | Path,
    output_dir: str | Path,
    timespan: str = "12months",
    maxrecords: int = 250,
    min_priority: str = "medium",
    top_n_per_group: int = 6,
) -> None:
    outdir = ensure_dir(output_dir)
    kw = KeywordTable.from_csv(keyword_csv)
    queries = build_doc_queries(kw, min_priority=min_priority, top_n_per_group=top_n_per_group)

    articles_all = []
    timeline_all = []
    tone_all = []
    source_country_all = []
    query_log = []

    for name, query in queries:
        query_log.append({"query_name": name, "query": query})
        print(f"正在查询主题: {name} (Timespan: {timespan})...")

        art = gdelt_doc_request(query, mode="artlist", timespan=timespan, maxrecords=maxrecords)
        art_df = pd.DataFrame(art.get("articles", []))
        if not art_df.empty:
            art_df["query_name"] = name
            art_df["query"] = query
            articles_all.append(art_df)

        vol = gdelt_doc_request(query, mode="timelinevol", timespan=timespan, maxrecords=maxrecords)
        vol_df = extract_timeline_to_df(vol, query_name=name, query=query)
        if not vol_df.empty:
            vol_df["series_type"] = "timelinevol"
            timeline_all.append(vol_df)

        tone = gdelt_doc_request(query, mode="timelinetone", timespan=timespan, maxrecords=maxrecords)
        tone_df = extract_timeline_to_df(tone, query_name=name, query=query)
        if not tone_df.empty:
            tone_df["series_type"] = "timelinetone"
            tone_all.append(tone_df)

        sc = gdelt_doc_request(query, mode="timelinesourcecountry", timespan=timespan, maxrecords=maxrecords)
        sc_df = extract_source_country_timeline(sc, query_name=name, query=query)
        if not sc_df.empty:
            source_country_all.append(sc_df)

    pd.DataFrame(query_log).to_csv(outdir / "query_log.csv", index=False, encoding="utf-8-sig")

    if articles_all:
        articles = pd.concat(articles_all, ignore_index=True)
        articles = postprocess_doc_articles(articles, kw)
        articles.to_csv(outdir / "doc_articles_cleaned.csv", index=False, encoding="utf-8-sig")
        articles.to_json(outdir / "doc_articles_cleaned.json", orient="records", force_ascii=False, indent=2)
        if "seendate" in articles.columns:
            build_doc_monthly_panel(articles).to_csv(outdir / "doc_articles_monthly_panel.csv", index=False, encoding="utf-8-sig")

    if timeline_all:
        pd.concat(timeline_all, ignore_index=True).to_csv(outdir / "doc_timeline_volume.csv", index=False, encoding="utf-8-sig")
    if tone_all:
        pd.concat(tone_all, ignore_index=True).to_csv(outdir / "doc_timeline_tone.csv", index=False, encoding="utf-8-sig")
    if source_country_all:
        pd.concat(source_country_all, ignore_index=True).to_csv(outdir / "doc_timeline_sourcecountry.csv", index=False, encoding="utf-8-sig")
    
    print("\nGDELT 2.0 数据抓取完成！")


# -----------------------------
# CLI
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="轻量版 GDELT 清洗脚本")
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("gdelt1", help="清洗 GDELT 1.0 事件数据")
    p1.add_argument("--keywords", required=True, help="关键词 CSV")
    p1.add_argument("--output", required=True, help="输出目录")
    p1.add_argument("--events", help="本地事件 ZIP 通配符，例如 data/gdelt1/*.zip")
    p1.add_argument("--start-date", help="远程模式开始日期 YYYY-MM-DD")
    p1.add_argument("--end-date", help="远程模式结束日期 YYYY-MM-DD")
    p1.add_argument("--max-files", type=int, default=None, help="最多处理多少个日文件")
    p1.add_argument("--chunksize", type=int, default=20000, help="每块读取行数，默认 20000")
    p1.add_argument("--keep-all-cleaned", action="store_true", help="默认只写出 recommended_keep=1；加上此参数则写出全部清洗记录")
    p1.add_argument("--cache-dir", help="远程模式缓存 ZIP 的目录；不传则用临时文件")

    p2 = sub.add_parser("gdelt2", help="运行 GDELT 2.0 DOC API")
    p2.add_argument("--keywords", required=True, help="关键词 CSV")
    p2.add_argument("--output", required=True, help="输出目录")
    p2.add_argument("--timespan", default="12months", help="如 3months / 12months")
    p2.add_argument("--maxrecords", type=int, default=250, help="每个查询返回的最大记录数")
    p2.add_argument("--min-priority", default="medium", choices=["low", "medium", "high"])
    p2.add_argument("--top-n-per-group", type=int, default=6)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "gdelt1":
        run_gdelt1_pipeline(
            keyword_csv=args.keywords,
            output_dir=args.output,
            events_file_pattern=args.events,
            start_date=args.start_date,
            end_date=args.end_date,
            max_files=args.max_files,
            chunksize=args.chunksize,
            keep_all_cleaned=args.keep_all_cleaned,
            cache_dir=args.cache_dir,
        )
    elif args.command == "gdelt2":
        run_gdelt2_doc_pipeline(
            keyword_csv=args.keywords,
            output_dir=args.output,
            timespan=args.timespan,
            maxrecords=args.maxrecords,
            min_priority=args.min_priority,
            top_n_per_group=args.top_n_per_group,
        )
    else:
        raise ValueError(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()