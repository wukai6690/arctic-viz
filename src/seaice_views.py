"""Sea-ice image timeline and route evidence view."""
from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.mosaic_research import load_mosaic, mosaic_image_uri, track_figure
from src.presentation import ROOT, section_title, show_chart

SEAICE_DIR = ROOT / "static" / "seaice"
PATENT_PATH = ROOT / "data" / "analysis" / "patents" / "patents.json"
GDELT_BULK_PATH = ROOT / "data" / "analysis" / "gdelt" / "bulk" / "gdelt_geopolitics_22815.csv"


def _image_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


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

    gdelt = pd.DataFrame()
    if GDELT_BULK_PATH.exists():
        gdelt = pd.read_csv(GDELT_BULK_PATH, encoding="utf-8-sig", low_memory=False)
        if not gdelt.empty:
            gdelt["date"] = pd.to_datetime(gdelt.get("date"), errors="coerce")
            gdelt["evidence_month"] = gdelt["date"].dt.strftime("%Y-%m").fillna("")
    return patents, gdelt


def _month_evidence(month: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    patents, gdelt = load_monthly_evidence()
    p = patents.loc[patents["evidence_month"].eq(month)].copy() if not patents.empty else patents
    g = gdelt.loc[gdelt["evidence_month"].eq(month)].copy() if not gdelt.empty else gdelt
    return p, g


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
    dates = sorted(set(available) & set(daily_by_day))
    if not dates:
        st.info("航线资料包尚未包含可配对日期。")
        return
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
        ice = available[day]
        path = ROOT / "data/analysis/mosaic" / ice["path"]
        if path.exists():
            st.image(mosaic_image_uri(path), width="stretch")
            st.caption("同期海冰密集度图 · AMSR2 / ASI · 6.25 km 网格")
        else:
            st.info("该日期的同期冰图未随部署包找到。")
    st.caption("航迹是可复核的船位记录，冰图是同日环境背景；两者不直接推导通航风险或船舶性能。")


def render_seaice_page() -> None:
    frame = load_seaice_index()
    section_title("SEA ICE & ROUTES", "海冰变化与航线证据", "把月度海冰影像、官方统计和真实船位放在同一条时间轴上，先看变化，再讨论航行条件。")
    if frame.empty:
        st.error("海冰影像索引未找到，请检查 static/seaice/。")
        return
    st.markdown('<div class="ice-hero-note"><b>129 张月度影像 · 2016-01—2026-09</b><span>来源：NSIDC Sea Ice Index v4.0（G02135）。影像是月均合成，不是单日实况；范围与面积保留原始口径。</span></div>', unsafe_allow_html=True)
    tabs = st.tabs(["海冰时间切片", "航线与同期冰情", "数据口径与下载"])
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
                st.image(_image_uri(path), width="stretch")
            else:
                st.warning("影像文件缺失：" + str(path))
        with right:
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
        st.markdown("#### 资料来源")
        st.write("影像来自 NSIDC Sea Ice Index, Version 4.0 (G02135), North Monthly Images；分辨率 25 km。2026 年目前整理到 9 月，后续月份未发布。")
        st.code("https://noaadata.apps.nsidc.org/NOAA/G02135/north/monthly/images/", language=None)
        st.markdown("#### 口径边界")
        st.write("影像展示海冰密集度变化，统计表展示范围与面积变化；它们都不能直接转换为某条航线的通航天数、船舶风险或航速。路线图使用 MOSAiC 公开船位记录，另行保留原始时间与数据间断。")
        st.download_button("下载海冰影像索引", (SEAICE_DIR / "索引.csv").read_bytes(), "arctic-seaice-index.csv", "text/csv", on_click="ignore")
        st.download_button("下载口径说明", (SEAICE_DIR / "说明.txt").read_bytes(), "arctic-seaice-method.txt", "text/plain", on_click="ignore")
