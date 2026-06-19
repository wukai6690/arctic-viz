"""
GDELT 2.0 北极事件数据下载与筛选脚本 v2
=======================================
策略：仅通过北极地理坐标(>60°N) + 北极国家 + 关键词组合筛选，
大幅减少无关事件。输出本地CSV供Streamlit离线使用。

GDELT 2.0 58列格式:
   0: GlobalEventID   1: SQLDATE         2: MonthYear      3: Year
   5: Actor1Code      6: Actor1Name      7: Actor1CountryCode
  15: Actor2Code     16: Actor2Name     17: Actor2CountryCode
  26: EventCode      30: GoldsteinScale 31: NumMentions   33: NumArticles  34: AvgTone
  39: Actor1Geo_Lat  40: Actor1Geo_Long 46: Actor2Geo_Lat  47: Actor2Geo_Long
  53: ActionGeo_Lat  54: ActionGeo_Long 51: ActionGeo_CountryCode
  50: ActionGeo_FullName  57: SOURCEURL
"""

import csv
import io
import os
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ====== 配置 ======
BASE_URL = "http://data.gdeltproject.org/events/"
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
TEMP_DIR = DATA_DIR / "_gdelt_temp"

ARCTIC_LAT_MIN = 60.0  # 北极圈附近

# 核心北极国家 (actor country必须在其中才算)
ARCTIC_CORE = {"RUS", "USA", "CAN", "NOR", "DNK", "FIN", "SWE", "ISL", "GRL", "CHN"}

# 北极关键词(英文, 大小写不敏感) —— 用于二次筛选
ARCTIC_KW = [
    "arctic", "high north", "northern sea", "northwest passage",
    "northeast passage", "greenland", "svalbard", "barents", "bering",
    "yamal", "polar silk", "icebreaker", "ice-class", "ice class",
    "arctic shipp", "arctic secur", "arctic militar", "arctic council",
    "arctic sovereig", "arctic resource", "arctic drill",
    "arctic govern", "arctic strateg", "arctic polic",
    "arctic scien", "arctic research", "arctic cooperat",
    "polar region", "northern fleet", "arctic base", "arctic station",
]

DOWNLOAD_CONFIG = {
    "recent_days": 7,             # 最近7天
    "sample_start": "2024-01-01", # 采样起始
    "sample_end": "2026-06-12",   # 采样结束
    "sample_days_per_month": 1,   # 每月只取1天
}

# 输出列
SHORT_HEADER = [
    "GlobalEventID", "SQLDATE", "MonthYear", "Year",
    "Actor1Code", "Actor1Name", "Actor1CountryCode",
    "Actor2Code", "Actor2Name", "Actor2CountryCode",
    "EventCode", "GoldsteinScale",
    "NumMentions", "NumArticles", "AvgTone",
    "Actor1Geo_Lat", "Actor1Geo_Long",
    "Actor2Geo_Lat", "Actor2Geo_Long",
    "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_CountryCode", "ActionGeo_FullName", "SOURCEURL",
]
# 源列索引 -> 输出列
SRC_IDX = [0, 1, 2, 3, 5, 6, 7, 15, 16, 17, 26, 30, 31, 33, 34, 39, 40, 46, 47, 53, 54, 51, 50, 57]


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def get_date_list():
    dates = set()
    today = datetime.now()
    for i in range(DOWNLOAD_CONFIG["recent_days"]):
        d = today - timedelta(days=i)
        dates.add(d.strftime("%Y%m%d"))

    start = datetime.strptime(DOWNLOAD_CONFIG["sample_start"], "%Y-%m-%d")
    end = datetime.strptime(DOWNLOAD_CONFIG["sample_end"], "%Y-%m-%d")
    current = datetime(start.year, start.month, 1)
    while current <= end:
        sample_date = current + timedelta(days=14)  # 每月15号附近
        ds = sample_date.strftime("%Y%m%d")
        if start <= sample_date <= end and ds not in dates:
            dates.add(ds)
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
    return sorted(dates)


def is_arctic_event(row):
    """
    严格筛选北极事件：
    A) 任一actor/action纬度 > 60°N  且  actor国家是北极核心国家
    B) 或 任一纬度 > 66.5°N (北极圈内，无论哪个国家)
    C) 或 SOURCEURL 中明确包含 arctic/polar 关键词
    """
    # C: URL关键词检测
    url = (row[57] or "").lower() if len(row) > 57 else ""
    for kw in ["arctic", "polar"]:
        if kw in url:
            return True

    # 检查纬度
    has_high_lat = False
    for lidx in [39, 46, 53]:
        if lidx < len(row) and row[lidx]:
            try:
                if float(row[lidx]) >= ARCTIC_LAT_MIN:
                    has_high_lat = True
                if float(row[lidx]) >= 66.5:  # B: 北极圈内
                    return True
            except ValueError:
                pass

    if not has_high_lat:
        return False

    # A: 纬度>60 且 核心北极国家
    for cidx in [7, 17, 51]:
        if cidx < len(row) and row[cidx] and row[cidx].strip().upper() in ARCTIC_CORE:
            return True

    return False


def download_and_filter(date_str):
    filename = f"{date_str}.export.CSV.zip"
    url = BASE_URL + filename
    zip_path = TEMP_DIR / filename

    if not zip_path.exists():
        print(f"  Downloading {filename}...", end=" ", flush=True)
        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 404:
                print("404 (no data for this date)")
                return 0
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
            mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"OK ({mb:.1f}MB)")
        except requests.RequestException as e:
            print(f"FAIL: {e}")
            return 0
    else:
        print(f"  Cached {filename}")

    print(f"  Filtering...", end=" ", flush=True)
    arctic_rows = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_name = f"{date_str}.export.CSV"
            if csv_name not in zf.namelist():
                print("CSV not in zip")
                return 0
            with zf.open(csv_name) as f:
                reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
                for row in reader:
                    if len(row) >= 58 and is_arctic_event(row):
                        arctic_rows.append([row[i] if i < len(row) else "" for i in SRC_IDX])
        print(f"{len(arctic_rows)} Arctic events")
    except Exception as e:
        print(f"FAIL: {e}")
        return 0

    if arctic_rows:
        out_path = DATA_DIR / f"gdelt_{date_str}_arctic.csv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(SHORT_HEADER)
            writer.writerows(arctic_rows)
        print(f"  -> {out_path.name}")
    return len(arctic_rows)


def merge_results():
    csv_files = sorted(DATA_DIR.glob("gdelt_*_arctic.csv"))
    if not csv_files:
        print("No results to merge")
        return

    print(f"\nMerging {len(csv_files)} files...")
    all_rows = []
    header = None
    for fp in csv_files:
        with open(fp, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            h = next(reader, None)
            if header is None:
                header = h
            all_rows.extend(list(reader))

    seen = set()
    unique = []
    for row in all_rows:
        gid = row[0]
        if gid not in seen:
            seen.add(gid)
            unique.append(row)
    print(f"  {len(all_rows)} raw, {len(unique)} unique")

    # 事件明细表 (带经纬度，可用于地图)
    grid_path = DATA_DIR / "gdelt_arctic_by_grid.csv"
    with open(grid_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(unique)
    kb = grid_path.stat().st_size / 1024
    print(f"  -> {grid_path.name} ({kb:.0f} KB)")

    # 年度x国家聚合
    _build_yearly(unique, header)


def _build_yearly(rows, header):
    # header: 0=GID,1=SQLDATE,2=MonthYear,3=Year,4=A1Code,5=A1Name,6=A1CC,...
    # 14=AvgTone
    yc_count = {}
    yc_tones = {}
    for row in rows:
        try:
            yr = int(row[3])
            cc = row[6].strip().upper()
            if not cc:
                continue
        except (ValueError, IndexError):
            continue
        key = (yr, cc)
        yc_count[key] = yc_count.get(key, 0) + 1
        try:
            tone = float(row[14])
            yc_tones.setdefault(key, []).append(tone)
        except (ValueError, IndexError):
            pass

    yc_path = DATA_DIR / "gdelt_arctic_by_year_country.csv"
    with open(yc_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "CountryCode", "EventCount", "AvgTone"])
        for (yr, cc), cnt in sorted(yc_count.items()):
            tones = yc_tones.get((yr, cc), [0])
            avg = round(sum(tones) / len(tones), 2) if tones else 0
            writer.writerow([yr, cc, cnt, avg])
    print(f"  -> {yc_path.name}")


def cleanup_temp():
    import shutil
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print("Temp cleaned")


def main():
    ensure_dirs()
    dates = get_date_list()
    print(f"Plan: {len(dates)} days ({dates[0]} ~ {dates[-1]})\n")

    total = 0
    ok = 0
    for i, d in enumerate(dates):
        print(f"[{i+1}/{len(dates)}] {d}")
        c = download_and_filter(d)
        if c > 0:
            total += c
            ok += 1
        if i < len(dates) - 1:
            time.sleep(0.3)

    print(f"\nDone! {ok}/{len(dates)} days, {total} events")
    if ok > 0:
        merge_results()
        cleanup_temp()


if __name__ == "__main__":
    main()
