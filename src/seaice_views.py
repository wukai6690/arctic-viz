"""Sea-ice image timeline and route evidence view."""
from __future__ import annotations

import base64
import io
import json
import mimetypes
from pathlib import Path
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from src.mosaic_research import load_mosaic, mosaic_image_uri, track_figure
from src.presentation import ROOT, section_title, show_chart

SEAICE_DIR = ROOT / "static" / "seaice"
PATENT_PATH = ROOT / "data" / "analysis" / "patents" / "patents.json"
GDELT_BULK_PATH = ROOT / "data" / "analysis" / "gdelt" / "bulk" / "gdelt_geopolitics_22815.csv"
GDELT_NETWORK_PATH = ROOT / "data" / "analysis" / "gdelt" / "network" / "network.json"
GDELT_GRID_PATH = ROOT / "data" / "processed" / "gdelt_arctic_by_grid.csv"
GIF_PATH = SEAICE_DIR / "arctic_seaice_monthly.gif"

COUNTRY_FLAGS = {
    "China": "🇨🇳", "United States": "🇺🇸", "Russia": "🇷🇺", "Canada": "🇨🇦",
    "Norway": "🇳🇴", "Denmark": "🇩🇰", "Finland": "🇫🇮", "Sweden": "🇸🇪",
    "Japan": "🇯🇵", "Germany": "🇩🇪", "United Kingdom": "🇬🇧", "France": "🇫🇷",
    "India": "🇮🇳", "Australia": "🇦🇺", "South Korea": "🇰🇷", "WIPO": "🌐",
}
COUNTRY_CENTERS = {
    "China": (35, 103), "United States": (64, -150), "Russia": (68, 100),
    "Canada": (66, -105), "Norway": (70, 15), "Denmark": (70, 25),
    "Finland": (67, 27), "Sweden": (67, 18), "Japan": (68, 145),
    "Germany": (68, 10), "United Kingdom": (68, -5), "France": (68, 2),
    "India": (68, 78), "Australia": (68, 135), "South Korea": (68, 128),
}


def _image_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _country_from_text(value: object) -> str:
    text = str(value or "").casefold()
    aliases = {
        "china": "China", "chn": "China", "中国": "China",
        "united states": "United States", "usa": "United States", "美国": "United States",
        "russia": "Russia", "rus": "Russia", "俄罗斯": "Russia",
        "canada": "Canada", "can": "Canada", "加拿大": "Canada",
        "norway": "Norway", "nor": "Norway", "挪威": "Norway",
        "denmark": "Denmark", "dnk": "Denmark", "丹麦": "Denmark",
        "finland": "Finland", "fin": "Finland", "芬兰": "Finland",
        "sweden": "Sweden", "swe": "Sweden", "瑞典": "Sweden",
        "japan": "Japan", "jpn": "Japan", "日本": "Japan",
        "germany": "Germany", "deu": "Germany", "德国": "Germany",
        "united kingdom": "United Kingdom", "gbr": "United Kingdom", "英国": "United Kingdom",
        "france": "France", "fra": "France", "法国": "France",
        "india": "India", "ind": "India", "印度": "India",
        "australia": "Australia", "aus": "Australia", "澳大利亚": "Australia",
        "south korea": "South Korea", "kor": "South Korea", "韩国": "South Korea",
    }
    for alias, country in aliases.items():
        if alias in text:
            return country
    return ""


def _polar_xy(lat: float, lon: float, size: tuple[int, int]) -> tuple[int, int]:
    """Approximate NSIDC north-polar-stereographic pixel position.

    It is used as a visual locator for country-level evidence. It is deliberately
    labelled as a reference position because the source tables do not provide
    event coordinates for every patent or news candidate.
    """
    import math
    width, height = size
    cx, cy = width * 0.397, height * 0.519
    scale = min(width, height) * 1.42
    radius = scale * math.tan(math.radians(max(0.0, 90.0 - float(lat))) / 2)
    angle = math.radians(float(lon))
    x = cx + radius * math.sin(angle)
    y = cy + radius * math.cos(angle)
    return int(max(22, min(width - 22, x))), int(max(85, min(height - 70, y)))


@st.cache_data(show_spinner=False, max_entries=256)
def annotated_seaice_image(path_text: str, label: str, country: str, color: str, latitude: float | None = None, longitude: float | None = None) -> bytes:
    path = Path(path_text)
    image = Image.open(path).convert("RGBA")
    lat, lon = COUNTRY_CENTERS.get(country, (70, 0))
    if latitude is not None and longitude is not None:
        lat, lon = float(latitude), float(longitude)
    x, y = _polar_xy(lat, lon, image.size)
    draw = ImageDraw.Draw(image, "RGBA")
    radius = max(14, image.size[0] // 50)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, 225), outline=color, width=max(5, radius // 4))
    draw.ellipse((x - radius // 2, y - radius // 2, x + radius // 2, y + radius // 2), fill=color, outline=(255, 255, 255, 235), width=3)
    try:
        font = ImageFont.truetype("msyh.ttc", max(22, image.size[0] // 54))
    except OSError:
        font = ImageFont.load_default()
    clean = label[:28]
    bbox = draw.textbbox((0, 0), clean, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = min(max(16, x + radius + 12), image.size[0] - tw - 20)
    ty = max(70, y - th - 18)
    draw.rounded_rectangle((tx - 9, ty - 6, tx + tw + 9, ty + th + 6), radius=8, fill=(10, 44, 76, 220), outline=(196, 231, 247, 235), width=2)
    draw.text((tx, ty), clean, fill=(235, 249, 255, 255), font=font)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _gif_uri() -> str:
    if not GIF_PATH.exists():
        return ""
    return "data:image/gif;base64," + base64.b64encode(GIF_PATH.read_bytes()).decode("ascii")


@st.cache_data(show_spinner=False)
def load_seaice_index() -> pd.DataFrame:
    path = SEAICE_DIR / "索引.csv"
    if not path.exists():
        return pd.DataFrame(columns=["year", "month", "filename", "extent", "area", "date", "path"])
    frame = pd.read_csv(path, encoding="utf-8-sig")
    frame = frame.rename(columns={
        "年": "year", "月": "month", "文件名": "filename",
        "海冰范围_百万km2": "extent", "海冰面积_百万km2": "area",
        "数据产品": "product", "版本": "version", "分辨率": "resolution",
    })
    frame["year"] = frame["year"].astype(int)
    frame["month"] = frame["month"].astype(int)
    frame["date"] = frame.apply(lambda r: f"{int(r.year):04d}-{int(r.month):02d}", axis=1)
    frame["path"] = frame["filename"].map(lambda name: SEAICE_DIR / str(name))
    return frame.sort_values(["year", "month"]).reset_index(drop=True)


def _month_from_date(value: object) -> str:
    """Return YYYY-MM for the mixed date formats in the confirmed exports."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=False if text[:4].isdigit() else True)
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m")


@st.cache_data(show_spinner=False)
def load_monthly_evidence() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load monthly patent and geopolitical evidence for the selected ice image.

    The two sources are intentionally kept separate: patent records are dated by
    publication (falling back to priority date), while GDELT rows are dated by
    the archive event date. This keeps the visual layer traceable to each source.
    """
    patents = pd.DataFrame()
    if PATENT_PATH.exists():
        payload = json.loads(PATENT_PATH.read_text(encoding="utf-8"))
        patents = pd.DataFrame(payload.get("records", []))
        if not patents.empty:
            pub = patents.get("publication_date", pd.Series(index=patents.index, dtype=object))
            priority = patents.get("priority_date", pd.Series(index=patents.index, dtype=object))
            patents["evidence_month"] = pub.map(_month_from_date)
            missing = patents["evidence_month"].eq("")
            patents.loc[missing, "evidence_month"] = priority[missing].map(_month_from_date)
            patents["title_display"] = patents.get("title_zh", "").fillna("").astype(str).str.strip()
            blank_title = patents["title_display"].eq("")
            patents.loc[blank_title, "title_display"] = patents.loc[blank_title, "title"].fillna("").astype(str)
            patents["technology_display"] = patents.get("technology", "").fillna("").astype(str).str.replace("�", "", regex=False)

    gdelt_frames: list[pd.DataFrame] = []
    if GDELT_BULK_PATH.exists():
        bulk = pd.read_csv(GDELT_BULK_PATH, encoding="utf-8-sig", low_memory=False)
        if not bulk.empty:
            bulk["date"] = pd.to_datetime(bulk.get("date"), errors="coerce")
            bulk["evidence_month"] = bulk["date"].dt.strftime("%Y-%m").fillna("")
            bulk["evidence_source"] = "GDELT 大规模候选库"
            bulk["latitude"] = pd.NA
            bulk["longitude"] = pd.NA
            gdelt_frames.append(bulk)

    # The structured network sample and the archived processed snapshots fill
    # the months that are absent from the seven-day bulk archive. They are kept
    # as candidates and deduplicated before the page counts them.
    if GDELT_NETWORK_PATH.exists():
        network = json.loads(GDELT_NETWORK_PATH.read_text(encoding="utf-8"))
        rows = []
        for window in network.get("windows", []):
            rows.extend(window.get("events", []))
        structured = pd.DataFrame(rows)
        if not structured.empty:
            structured["date"] = pd.to_datetime(structured.get("date"), errors="coerce")
            structured["evidence_month"] = structured["date"].dt.strftime("%Y-%m").fillna("")
            structured["title"] = structured.apply(lambda r: f"{r.get('actor1_name', r.get('actor1', ''))} → {r.get('actor2_name', r.get('actor2', ''))} · {r.get('category', 'GDELT 事件')}", axis=1)
            structured["summary"] = structured.apply(lambda r: f"{r.get('location', '')} · CAMEO {r.get('event_code', '')} · Goldstein {r.get('goldstein', '')}", axis=1)
            structured["participants_or_leads"] = structured.apply(lambda r: f"{r.get('actor1', '')}; {r.get('actor2', '')}", axis=1)
            structured["relation_type"] = structured.get("category", "structured_gdelt")
            structured["evidence_source"] = "GDELT 结构化网络样本"
            structured["record_id"] = structured.get("id", structured.index.astype(str))
            gdelt_frames.append(structured)

    if GDELT_GRID_PATH.exists():
        grid = pd.read_csv(GDELT_GRID_PATH, low_memory=False)
        if not grid.empty:
            grid["date"] = pd.to_datetime(grid.get("SQLDATE"), format="%Y%m%d", errors="coerce")
            grid["evidence_month"] = grid["date"].dt.strftime("%Y-%m").fillna("")
            grid["title"] = grid.apply(lambda r: f"{r.get('Actor1Name', '')} → {r.get('Actor2Name', '')} · CAMEO {r.get('EventCode', '')}", axis=1)
            grid["summary"] = grid.get("ActionGeo_FullName", "").fillna("").astype(str)
            grid["participants_or_leads"] = grid.apply(lambda r: f"{r.get('Actor1Code', '')}; {r.get('Actor2Code', '')}", axis=1)
            grid["location"] = grid.get("ActionGeo_FullName", "").fillna("").astype(str)
            grid["relation_type"] = grid.get("EventCode", "").astype(str).map(lambda value: f"gdelt_cameo_{value}")
            grid["source_url"] = grid.get("SOURCEURL", "").fillna("")
            grid["record_id"] = grid.get("GlobalEventID", grid.index.astype(str)).astype(str)
            grid["latitude"] = pd.to_numeric(grid.get("ActionGeo_Lat"), errors="coerce")
            grid["longitude"] = pd.to_numeric(grid.get("ActionGeo_Long"), errors="coerce")
            grid["evidence_source"] = "GDELT 归档快照"
            gdelt_frames.append(grid)

    gdelt_frames = [frame.dropna(axis=1, how="all") for frame in gdelt_frames]
    gdelt = pd.concat(gdelt_frames, ignore_index=True, sort=False) if gdelt_frames else pd.DataFrame()
    if not gdelt.empty:
        for column in ["record_id", "date", "title", "summary", "participants_or_leads", "location", "relation_type", "source_url", "evidence_source"]:
            if column not in gdelt:
                gdelt[column] = ""
        gdelt["record_id"] = gdelt["record_id"].fillna("").astype(str)
        gdelt["source_url"] = gdelt["source_url"].fillna("").astype(str)
        gdelt["dedup_key"] = gdelt["record_id"].where(gdelt["record_id"].ne(""), gdelt["date"].astype(str) + "|" + gdelt["source_url"] + "|" + gdelt["title"].astype(str))
        gdelt = gdelt.drop_duplicates(subset=["dedup_key"]).drop(columns=["dedup_key"], errors="ignore").reset_index(drop=True)
    return patents, gdelt


def _month_evidence(month: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    patents, gdelt = load_monthly_evidence()
    p = patents.loc[patents["evidence_month"].eq(month)].copy() if not patents.empty else patents
    g = gdelt.loc[gdelt["evidence_month"].eq(month)].copy() if not gdelt.empty else gdelt
    return p, g


def _important_evidence_options(patents: pd.DataFrame, gdelt: pd.DataFrame) -> list[dict]:
    """Return a compact, high-signal list used by the image annotation control."""
    options = [{"key": "none", "kind": "overview", "label": "不显示证据标记", "country": "", "color": "#2e97cf"}]
    if not gdelt.empty:
        preferred = gdelt.copy()
        preferred["priority"] = preferred["relation_type"].astype(str).str.contains("material_conflict|material_cooperation", case=False, regex=True).astype(int)
        preferred = preferred.sort_values(["priority", "date"], ascending=[False, False]).drop_duplicates(subset=["location", "relation_type"]).head(5)
        for idx, row in preferred.iterrows():
            country = _country_from_text(f"{row.get('location', '')} {row.get('participants_or_leads', '')} {row.get('title', '')}")
            country = country or "Canada"
            flag = COUNTRY_FLAGS.get(country, "🌐")
            title = str(row.get("title", "未命名地缘事件"))
            options.append({"key": f"geo-{idx}", "kind": "geo", "label": f"{flag} 地缘 · {title[:42]}", "country": country, "color": "#ef8d5c", "source": row.get("source_url", ""), "latitude": row.get("latitude"), "longitude": row.get("longitude")})
    if not patents.empty:
        preferred = patents.copy()
        preferred["priority"] = preferred["technology_display"].astype(str).str.contains("船|冰|航|观测|卫星|通信", regex=True).astype(int)
        preferred = preferred.sort_values(["priority", "publication_date"], ascending=[False, False]).head(5)
        for idx, row in preferred.iterrows():
            country = _country_from_text(row.get("country", "")) or str(row.get("country", ""))
            flag = COUNTRY_FLAGS.get(country, "🌐")
            title = str(row.get("title_display", "未命名专利"))
            options.append({"key": f"patent-{idx}", "kind": "patent", "label": f"{flag} 专利 · {title[:42]}", "country": country, "color": "#2e97cf", "source": row.get("source_url", ""), "latitude": None, "longitude": None})
    return options


def _evidence_badges(month: str, patents: pd.DataFrame, gdelt: pd.DataFrame) -> None:
    """Place a clear, non-geographic evidence marker directly above the raster."""
    st.markdown(
        f'<div class="month-evidence-badges">'
        f'<span class="month-badge month-badge-ice">{escape(month)} · 影像月份</span>'
        f'<span class="month-badge month-badge-geo">地缘候选 {len(gdelt):,}</span>'
        f'<span class="month-badge month-badge-patent">专利公开 {len(patents):,}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_month_evidence(month: str, patents: pd.DataFrame, gdelt: pd.DataFrame) -> None:
    """Render the evidence rail paired with the selected monthly image."""
    st.markdown('<div class="evidence-rail-title"><span>MONTHLY EVIDENCE LAYER</span><b>当月地缘与技术线索</b></div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    a.metric("地缘事件候选", f"{len(gdelt):,}", "GDELT 机器编码候选")
    b.metric("技术专利公开", f"{len(patents):,}", "按公开日归入月份")
    _, all_gdelt = load_monthly_evidence()
    covered_months = set(all_gdelt["evidence_month"].dropna().astype(str)) if not all_gdelt.empty else set()
    if gdelt.empty:
        if month not in covered_months:
            st.warning("当前月份没有接入 GDELT 快照；这里的 0 表示数据覆盖边界，不表示该月没有地缘活动。")
        else:
            st.info("当前月份的 GDELT 候选经过筛选后为空；这里的 0 只表示当前候选库没有匹配记录。")
    if patents.empty:
        st.caption("当前专利公开日数据中没有该月份记录；专利数量按公开日统计，不用邻近月份补值。")
    sources = sorted(set(str(value) for value in gdelt.get("evidence_source", pd.Series(dtype=object)).dropna())) if not gdelt.empty else []
    st.caption("地缘证据来源层：" + ("、".join(sources) if sources else "该月未接入快照"))

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="evidence-column-heading"><span class="evidence-dot geo-dot"></span>地缘事件候选</div>', unsafe_allow_html=True)
        if gdelt.empty:
            st.info("该月份暂无已整理的 GDELT 候选事件。")
        else:
            rows = gdelt.sort_values(["date", "relation_type"], ascending=[False, True]).head(5)
            for _, row in rows.iterrows():
                title = escape(str(row.get("title", "未命名事件")))
                location = escape(str(row.get("location", "未标注地点")))
                relation = escape(str(row.get("relation_type", "候选关系")).replace("gdelt_", ""))
                url = str(row.get("source_url", "")).strip()
                source = f'<a href="{escape(url)}" target="_blank">查看来源 ↗</a>' if url else ""
                st.markdown(
                    f'<div class="evidence-item"><b>{title}</b><small>{location} · {relation} · {source}</small></div>',
                    unsafe_allow_html=True,
                )
    with right:
        st.markdown('<div class="evidence-column-heading"><span class="evidence-dot patent-dot"></span>技术专利公开</div>', unsafe_allow_html=True)
        if patents.empty:
            st.info("该月份暂无已整理的专利公开记录。")
        else:
            rows = patents.sort_values(["publication_date", "publication_number"], ascending=[False, True]).head(5)
            for _, row in rows.iterrows():
                title = escape(str(row.get("title_display", "未命名专利")))
                number = escape(str(row.get("publication_number", "")))
                technology = escape(str(row.get("technology_display", "技术类别未标注")))
                url = str(row.get("source_url", "")).strip()
                source = f'<a href="{escape(url)}" target="_blank">查看专利 ↗</a>' if url else ""
                st.markdown(
                    f'<div class="evidence-item"><b>{title}</b><small>{number} · {technology} · {source}</small></div>',
                    unsafe_allow_html=True,
                )

    if not patents.empty or not gdelt.empty:
        export_rows = []
        for _, row in gdelt.head(1000).iterrows():
            export_rows.append({"月份": month, "证据类型": "地缘事件候选", "日期": str(row.get("date", ""))[:10], "标题": row.get("title", ""), "地点": row.get("location", ""), "关系": row.get("relation_type", ""), "来源": row.get("source_url", "")})
        for _, row in patents.head(1000).iterrows():
            export_rows.append({"月份": month, "证据类型": "技术专利公开", "日期": row.get("publication_date", ""), "标题": row.get("title_display", ""), "地点": row.get("country", ""), "关系": row.get("technology_display", ""), "来源": row.get("source_url", "")})
        export = pd.DataFrame(export_rows).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下载本月证据清单", export, f"arctic-evidence-{month}.csv", "text/csv", on_click="ignore", key=f"month-evidence-{month}")
    st.caption("标记表示同月可追溯证据数量；专利记录没有地理坐标，因此不把专利强行放到海冰栅格上。地缘记录的地点来自 GDELT 事件字段，候选关系仍需回看新闻原文。")


def _ice_chart(frame: pd.DataFrame, metric: str = "extent") -> go.Figure:
    label = "海冰范围" if metric == "extent" else "海冰面积"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frame["date"], y=frame[metric], mode="lines+markers", name=label,
        line=dict(color="#1676b8", width=2.4), marker=dict(size=4),
        hovertemplate="%{x}<br>" + label + "：%{y:.3f} 百万 km²<extra></extra>",
    ))
    fig.update_layout(
        height=330, margin=dict(l=12, r=16, t=24, b=42),
        xaxis=dict(title="月份", tickmode="array", tickvals=frame["date"][::12]),
        yaxis=dict(title="百万 km²", rangemode="tozero"), hovermode="x unified",
        showlegend=False,
    )
    return fig


def render_seaice_route(key: str = "seaice-route") -> None:
    data = load_mosaic()
    manifest = data["manifest"]
    daily = data["daily"]
    available = {row["date"]: row for row in data["ice"] if row["status"] == "available"}
    daily_by_day = {row["timestamp"][:10]: row for row in daily}
    all_dates = sorted(daily_by_day)
    dates_with_ice = sorted(set(available) & set(daily_by_day))
    dates = dates_with_ice
    if not all_dates:
        st.info("航线资料包尚未包含可配对日期。")
        return
    route_mode = st.radio("路线浏览范围", ["14 个同期冰图日期", "全部 389 个船位日期"], horizontal=True, key=key + "-mode")
    dates = dates_with_ice if route_mode.startswith("14") else all_dates
    default = "2019-10-15" if "2019-10-15" in dates else dates[0]
    date_key = key + "-date"
    if st.session_state.get(date_key) not in dates:
        st.session_state[date_key] = default
    day = st.select_slider("选择航行日期", options=dates, key=date_key)
    position = daily_by_day[day]
    a, b, c = st.columns(3)
    a.metric("公开船位记录", f"{manifest['track_rows']:,}")
    b.metric("航次日期", f"{len(daily):,} 天")
    c.metric("可配对冰情图", f"{len(available):,} 个时点")
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown('<div class="subpanel-kicker">ROUTE EVIDENCE · MOSAiC PS122</div>', unsafe_allow_html=True)
        show_chart(track_figure(day), key=key + "-track")
        st.caption(f"截至 {position['timestamp'].replace('T', ' ')} UTC · {position['latitude']:.4f}° N · {position['longitude']:.4f}°。航迹保留航行与随冰漂流。")
    with right:
        st.markdown('<div class="subpanel-kicker">SYNCHRONIZED ICE CONTEXT</div>', unsafe_allow_html=True)
        ice = available.get(day)
        path = ROOT / "data/analysis/mosaic" / ice["path"] if ice else None
        if path and path.exists():
            st.image(mosaic_image_uri(path), width="stretch")
            st.caption("同期海冰密集度图 · AMSR2 / ASI · 6.25 km 网格")
        else:
            st.info("该日期有真实船位，但没有随部署包保存同期冰图；切换到‘14 个同期冰图日期’可查看所有已配对图组。")
    st.caption("航迹是可复核的船位记录，冰图是同日环境背景；两者不直接推导通航风险或船舶性能。路线数据覆盖 389 个日期，14 个日期有已保存的同期海冰图。")
    st.markdown('<div class="route-reading-grid"><div><small>ROUTE READING</small><b>航迹记录什么</b><p>路线保留五个已发布航段的真实船位、航行段和随冰漂流段，选定日期会把船位截到对应时刻。</p></div><div><small>ICE CONTEXT</small><b>同期冰情说明什么</b><p>右侧图像提供同日海冰密集度背景，用于描述观测环境，不把单个像素直接解释为船舶风险。</p></div><div><small>RESEARCH LIMIT</small><b>怎样回到证据</b><p>点击日期切换船位和冰图，再从证据包下载原始时间、地图和来源说明。</p></div></div>', unsafe_allow_html=True)
    st.caption("覆盖说明：129 个月海冰影像覆盖 2016-01—2026-09；本条真实 MOSAiC 航线覆盖 2019-09—2020-10。没有把一条 2019—2020 航线复制到其他年份。")
    with st.expander("官方图例、数据结构和解释边界", expanded=True):
        st.markdown("左图为 AWI/PANGAEA 发布的 MOSAiC Polarstern PS122 五航段主航迹，采用 WGS84 经纬度和 UTC 导航时间，共 55,793 条 10 分钟真实船位、389 个有记录日期。浅色线是全航次参考，深色线是截至所选日期的轨迹，红色点是所选时刻船位；路线同时包含主动航行和随冰漂流，原始记录中超过 1 小时的缺口分段保存，不做插值。")
        st.markdown("右图为 Meereisportal/AWI/IUP 使用 AMSR2/ASI 生成的同期海冰密集度图，采用固定北极极地立体投影和 6.25 km 网格。冰图日期与图内船位标记时间可能相差一天，应分别按图例读取。两图并置用于回答‘船位处于什么海冰环境’，不能由单个像素推导船舶性能、风险或政治结论。")
        st.markdown("2016 年以来的 129 个月海冰图和 2019-09—2020-10 的 MOSAiC 航线是两条不同时间轴。若以后接入 Arctic Council/PAME ASTD 等 AIS 统计，应另标为‘月度船流/交通密度’，不能复制 PS122 航线来填满其他年份。")
    src_a, src_b = st.columns(2)
    src_a.link_button("Meereisportal 官方航迹冰图", "https://data.meereisportal.de/relaunch/concentrationmosaic.php?lang=en", use_container_width=True)
    src_b.link_button("PANGAEA PS122 船位数据", "https://doi.pangaea.de/10.1594/PANGAEA.924668", use_container_width=True)
    st.link_button("PAME Arctic Ship Traffic Database（未来月度船流层来源）", "https://www.pame.is/ourwork/arctic-shipping/astd/", use_container_width=False)


def render_seaice_page() -> None:
    frame = load_seaice_index()
    section_title("SEA ICE & ROUTES", "海冰变化与航线证据", "把月度海冰影像、官方统计和真实船位放在同一条时间轴上，先看变化，再讨论航行条件。")
    if frame.empty:
        st.error("海冰影像索引未找到，请检查 static/seaice/。")
        return
    st.markdown('<div class="ice-hero-note"><b>129 张月度影像 · 2016-01—2026-09</b><span>来源：NSIDC Sea Ice Index v4.0（G02135）。影像是月均合成，不是单日实况；范围与面积保留原始口径。</span></div>', unsafe_allow_html=True)
    patents_all, gdelt_all = load_monthly_evidence()
    image_months = set(frame["date"])
    patent_months = image_months.intersection(set(patents_all.get("evidence_month", pd.Series(dtype=object)).astype(str)))
    geo_months = image_months.intersection(set(gdelt_all.get("evidence_month", pd.Series(dtype=object)).astype(str)))
    c1, c2, c3 = st.columns(3)
    c1.metric("海冰月度影像", f"{len(frame):,} 个月", "2016-01—2026-09")
    c2.metric("有专利公开记录的月份", f"{len(patent_months):,} / {len(frame):,}", "按公开日归入")
    c3.metric("有地缘候选覆盖的月份", f"{len(geo_months):,} / {len(frame):,}", "当前已接入 GDELT 层")
    tabs = st.tabs(["月度海冰与证据联动", "MOSAiC 航线与同期冰情", "海冰变化解读"])
    with tabs[0]:
        metric = st.radio("趋势指标", ["extent", "area"], format_func=lambda x: "海冰范围" if x == "extent" else "海冰面积", horizontal=True, key="seaice-metric")
        latest = frame.iloc[-1]
        low = frame.loc[frame[metric].idxmin()]
        a, b, c = st.columns(3)
        a.metric("最新影像", latest["date"], f"{latest[metric]:.3f} 百万 km²")
        b.metric("序列最低值", low["date"], f"{low[metric]:.3f} 百万 km²")
        c.metric("已整理影像", f"{len(frame):,} 张", "2016—2026")
        st.markdown('<div class="subpanel-kicker">MONTHLY OBSERVATION SERIES</div>', unsafe_allow_html=True)
        show_chart(_ice_chart(frame, metric), key="seaice-full-series")
        dates = frame["date"].tolist()
        # Open on the month where both source layers overlap, so the evidence
        # rail is immediately visible; the full 129-month sequence remains
        # available through the slider.
        default_date = "2019-09" if "2019-09" in dates else dates[-1]
        chosen = st.select_slider("查看影像月份", options=dates, value=default_date, key="seaice-image-date")
        selected = frame.loc[frame["date"] == chosen].iloc[0]
        patents, gdelt = _month_evidence(chosen)
        left, right = st.columns([1.12, 0.88], gap="large")
        with left:
            st.markdown(f'<div class="ice-image-frame"><div class="ice-image-label">{chosen} · 北极海冰密集度</div></div>', unsafe_allow_html=True)
            _evidence_badges(chosen, patents, gdelt)
            path = Path(selected["path"])
            if path.exists():
                options = _important_evidence_options(patents, gdelt)
                labels = [item["label"] for item in options]
                selected_label = st.selectbox("选择月度证据标记", labels, key=f"seaice-evidence-marker-{chosen}")
                marker = options[labels.index(selected_label)]
                if marker["kind"] == "overview":
                    st.image(_image_uri(path), width="stretch")
                else:
                    country = marker["country"]
                    latitude = marker.get("latitude") if pd.notna(marker.get("latitude")) else None
                    longitude = marker.get("longitude") if pd.notna(marker.get("longitude")) else None
                    marked = annotated_seaice_image(str(path), f"{COUNTRY_FLAGS.get(country, '🌐')} {country}", country, marker["color"], latitude, longitude)
                    st.image(marked, width="stretch")
                    st.caption("图中标记为国家/地区参考位置；新闻候选与专利记录未提供统一的事件坐标，位置用于定位阅读，不代表事件发生点。")
            else:
                st.warning("影像文件缺失：" + str(path))
        with right:
            st.markdown('<div class="subpanel-kicker">129-MONTH MOTION VIEW</div>', unsafe_allow_html=True)
            gif_uri = _gif_uri()
            if gif_uri:
                st.markdown(f'<div class="seaice-gif-frame"><img src="{gif_uri}" alt="2016—2026 月度海冰变化动画"></div>', unsafe_allow_html=True)
                st.caption("播放 129 张月度海冰密集度图；动画用于观察季节节律和长期收缩背景。")
            st.markdown("**读图提示**")
            st.markdown("深蓝表示开阔水，浅蓝表示低密集度海冰，白色表示高密集度海冰；灰色为陆地。粉色线为产品中的历史中位冰缘。")
            st.metric("海冰范围", f"{selected['extent']:.3f} 百万 km²")
            st.metric("海冰面积", f"{selected['area']:.3f} 百万 km²")
            st.caption("extent 是密集度 ≥15% 的格点面积之和；area 是密集度加权面积，两者不能混用。")
        st.markdown('<div class="monthly-evidence-panel">', unsafe_allow_html=True)
        _render_month_evidence(chosen, patents, gdelt)
        st.markdown('</div>', unsafe_allow_html=True)
    with tabs[1]:
        render_seaice_route()
    with tabs[2]:
        st.markdown('<div class="interpretation-grid"><div class="interpretation-card"><small>01 / SEASONAL SIGNAL</small><h3>夏季收缩，冬季扩张</h3><p>月度动画把季节周期放在连续画面中；选定月份的范围和面积保留 NSIDC 原始统计口径。</p></div><div class="interpretation-card"><small>02 / EVIDENCE LINK</small><h3>环境变化与活动线索同月对照</h3><p>专利按公开日归入月份，地缘候选按事件日期归入月份；有坐标的新闻候选使用行动地理点，专利使用所属国家参考点。</p></div><div class="interpretation-card"><small>03 / RESEARCH BOUNDARY</small><h3>影像不是通航风险结论</h3><p>海冰密集度、船位和新闻候选是三类独立证据；页面把它们并置，避免把环境背景直接换算成航行能力。</p></div></div>', unsafe_allow_html=True)
        st.markdown("#### 两类图怎样读")
        st.markdown("**海冰密集度图**：白色接近 100% 密集度，深蓝接近 0—15%；海冰范围使用密集度至少 15% 的格点面积，海冰面积还会按格点密集度加权。粉色/绿色冰缘是 1981—2010 参考冰缘，适合比较同月偏离，不代表航道边界。")
        st.markdown("**航线与同期冰情图**：红线表示 Polarstern 在 MOSAiC 漂流观测中的轨迹，黑色区域/标记是出发或目标区域，船位点是公开导航记录。路线与海冰图只是时间和空间上的并置，不能据此推出某艘船的通航能力。")
        st.markdown("#### 官方出处")
        st.link_button("NSIDC Sea Ice Index v4.0", "https://nsidc.org/data/g02135/versions/4", use_container_width=False)
        st.link_button("Meereisportal · Polarstern 航迹与海冰密集度", "https://data.meereisportal.de/relaunch/concentrationmosaic.php?lang=en", use_container_width=False)
        st.link_button("PANGAEA · MOSAiC 航段数据", "https://doi.pangaea.de/10.1594/PANGAEA.924668", use_container_width=False)
        st.link_button("GDELT 官方事件归档", "https://data.gdeltproject.org/events/", use_container_width=False)
        st.caption("NSIDC 产品为 25 km 极地立体投影月度产品；Meereisportal 的 MOSAiC 图组使用 AMSR2/IUP Bremen 海冰密集度并叠加 Polarstern 航迹。")
