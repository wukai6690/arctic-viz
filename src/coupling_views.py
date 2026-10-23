"""Climate–geopolitics–technology coupling explorer.

The page deliberately presents a researchable mechanism chain rather than an
unvalidated single "coupling score".  Climate observations, GDELT candidates
and patent publications stay in separate evidence layers and are joined only
by the selected month or year.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import ROOT, section_title, show_chart
from src.seaice_views import load_monthly_evidence, load_seaice_index
from src.study_data import regional_data


PATENT_PATH = ROOT / "data/analysis/patents/patents.json"

COUNTRY_LABELS = {
    "China": "中国", "United States": "美国", "Russia": "俄罗斯", "Canada": "加拿大",
    "Norway": "挪威", "Denmark": "丹麦", "Finland": "芬兰", "Sweden": "瑞典",
    "Japan": "日本", "Germany": "德国", "United Kingdom": "英国", "France": "法国",
    "India": "印度", "Australia": "澳大利亚", "South Korea": "韩国", "WIPO": "WIPO",
}
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
REGION_LABELS = {"barents": "巴伦支海", "kara": "喀拉海", "chukchi": "楚科奇海"}
REGION_COLORS = {"barents": "#f08b5d", "kara": "#e7b34d", "chukchi": "#59a8c8"}

# These are reference route and station positions, not vessel tracks.  They
# give the coupling map a stable geographic frame while the evidence layers
# remain source-linked and separately labelled.
ROUTES = {
    "北方海航道参考线": [(69.0, 33.1), (71.3, 52.7), (71.8, 82.0), (72.6, 129.7), (69.7, 170.3)],
    "西北航道参考线": [(64.5, -165.4), (74.7, -94.9), (75.0, -83.0), (64.2, -51.7)],
}
STATIONS = [
    (78.2, 15.6, "Svalbard / 斯瓦尔巴"), (69.6, 18.9, "Tromsø / 特罗姆瑟"),
    (71.3, 72.1, "Sabetta / 萨别塔"), (69.7, 170.3, "Pevek / 佩韦克"),
    (64.5, -165.4, "Nome / 诺姆"), (74.7, -94.9, "Resolute / 雷索卢特"),
]


@st.cache_data(show_spinner=False)
def _load_patent_records() -> pd.DataFrame:
    if not PATENT_PATH.exists():
        return pd.DataFrame()
    records = json.loads(PATENT_PATH.read_text(encoding="utf-8")).get("records", [])
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    for field in ("publication_date", "priority_date"):
        frame[field + "_parsed"] = pd.to_datetime(frame.get(field, ""), errors="coerce", dayfirst=True)
    frame["evidence_date"] = frame["publication_date_parsed"].fillna(frame["priority_date_parsed"])
    frame["evidence_month"] = frame["evidence_date"].dt.strftime("%Y-%m").fillna("")
    frame["evidence_year"] = frame["evidence_date"].dt.year
    frame["country_label"] = frame.get("country", "").map(lambda value: COUNTRY_LABELS.get(str(value), str(value) or "未注明"))
    frame["title_display"] = frame.get("title_zh", "").fillna("").astype(str).str.strip()
    blank = frame["title_display"].eq("")
    frame.loc[blank, "title_display"] = frame.loc[blank, "title"].fillna("").astype(str)
    frame["technology_display"] = frame.get("technology", "").fillna("").astype(str).str.replace("�", "", regex=False)
    return frame


@st.cache_data(show_spinner=False)
def _load_region_frame() -> pd.DataFrame:
    payload = regional_data()
    frame = pd.DataFrame(payload.get("records", []))
    if frame.empty:
        return frame
    frame["date"] = frame["date"].astype(str)
    frame["region_label"] = frame["region_id"].map(REGION_LABELS).fillna(frame["region_id"])
    return frame


def _month_options() -> list[str]:
    index = load_seaice_index()
    return index["date"].astype(str).tolist() if not index.empty else []


def _closest_image(month: str) -> Path | None:
    frame = load_seaice_index()
    if frame.empty:
        return None
    row = frame.loc[frame["date"].eq(month)]
    if row.empty:
        return None
    path = Path(row.iloc[0]["path"])
    return path if path.exists() else None


def _month_summary(month: str) -> dict:
    index = load_seaice_index()
    row = index.loc[index["date"].eq(month)] if not index.empty else pd.DataFrame()
    item = row.iloc[0].to_dict() if not row.empty else {}
    patents, gdelt = load_monthly_evidence()
    p = patents.loc[patents["evidence_month"].eq(month)].copy() if not patents.empty else patents
    g = gdelt.loc[gdelt["evidence_month"].eq(month)].copy() if not gdelt.empty else gdelt
    return {"ice": item, "patents": p, "gdelt": g}


def _same_year(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    if frame.empty or "evidence_month" not in frame.columns:
        return frame.iloc[0:0] if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    return frame.loc[frame["evidence_month"].astype(str).str.startswith(str(year))].copy()


def _country_from_row(row: pd.Series) -> str:
    value = str(row.get("country", "") or "")
    if value in COUNTRY_CENTERS:
        return value
    text = " ".join(str(row.get(k, "")) for k in ("participants_or_leads", "location", "title", "actor1", "actor2"))
    aliases = {"CHN": "China", "USA": "United States", "RUS": "Russia", "CAN": "Canada", "NOR": "Norway", "DNK": "Denmark", "FIN": "Finland", "SWE": "Sweden"}
    for alias, country in aliases.items():
        if alias in text.upper():
            return country
    for country in COUNTRY_CENTERS:
        if country.casefold() in text.casefold() or COUNTRY_LABELS[country] in text:
            return country
    return ""


def _coupling_map(month: str, patents: pd.DataFrame, gdelt: pd.DataFrame, region_frame: pd.DataFrame, layers: list[str]) -> go.Figure:
    fig = go.Figure()
    if "航线参考" in layers:
        for name, points in ROUTES.items():
            fig.add_trace(go.Scattergeo(lat=[p[0] for p in points], lon=[p[1] for p in points], mode="lines",
                name=name, line={"width": 3, "color": "#d8795e" if "北方" in name else "#8a82bd", "dash": "dash"},
                hovertemplate=f"{name}<extra></extra>"))
    if "科考站" in layers:
        fig.add_trace(go.Scattergeo(lat=[p[0] for p in STATIONS], lon=[p[1] for p in STATIONS], mode="markers+text",
            text=[p[2] for p in STATIONS], textposition="top center", name="科考站与港口",
            marker={"size": 8, "color": "#184d75", "line": {"width": 1, "color": "#fff"}},
            hovertemplate="%{text}<br>固定参考位置<extra></extra>"))
    if "气候信号" in layers and not region_frame.empty:
        current = region_frame.loc[region_frame["date"].eq(month)].copy()
        if not current.empty:
            fig.add_trace(go.Scattergeo(lat=[REGION_CENTERS[r][0] for r in current["region_id"]], lon=[REGION_CENTERS[r][1] for r in current["region_id"]],
                mode="markers+text", text=[f"{REGION_LABELS.get(r, r)}<br>{a/1e6:.2f}M km²" for r, a in zip(current["region_id"], current["extent_km2"])], textposition="bottom center", name="海冰区域观测",
                marker={"size": [12 + 18 * min(1, abs(float(a or 0)) / 1_000_000) for a in current["area_anomaly_km2"]], "color": [REGION_COLORS.get(r, "#59a8c8") for r in current["region_id"]], "line": {"width": 2, "color": "#fff"}},
                customdata=current[["region_label", "extent_km2", "area_anomaly_km2", "status"]].values,
                hovertemplate="%{customdata[0]}<br>海冰范围：%{customdata[1]:,.0f} km²<br>面积距平：%{customdata[2]:,.0f} km²<br>状态：%{customdata[3]}<extra></extra>"))
    if "地缘事件" in layers and not gdelt.empty:
        rows = gdelt.head(45).copy()
        grouped = []
        for country, part in rows.assign(country=rows.apply(_country_from_row, axis=1)).groupby("country"):
            if country not in COUNTRY_CENTERS:
                continue
            grouped.append((country, len(part), "；".join(part.get("title", pd.Series(dtype=str)).astype(str).head(2))))
        if grouped:
            fig.add_trace(go.Scattergeo(lat=[COUNTRY_CENTERS[c][0] for c, _, _ in grouped], lon=[COUNTRY_CENTERS[c][1] for c, _, _ in grouped], mode="markers+text",
                text=[f"{COUNTRY_FLAGS.get(c, '')} {COUNTRY_LABELS.get(c, c)}" for c, _, _ in grouped], textposition="top center", name="地缘事件候选",
                marker={"size": [10 + 5 * math.sqrt(n) for _, n, _ in grouped], "color": "#e57b6e", "opacity": .86, "line": {"width": 1.5, "color": "#fff"}},
                customdata=[[COUNTRY_LABELS.get(c, c), n, title] for c, n, title in grouped], hovertemplate="%{customdata[0]}<br>当月候选：%{customdata[1]} 条<br>%{customdata[2]}<extra></extra>"))
    if "技术专利" in layers and not patents.empty:
        rows = patents.assign(country=patents.apply(_country_from_row, axis=1)).groupby("country").size().reset_index(name="count")
        rows = rows.loc[rows["country"].isin(COUNTRY_CENTERS)]
        if not rows.empty:
            fig.add_trace(go.Scattergeo(lat=[COUNTRY_CENTERS[c][0] for c in rows["country"]], lon=[COUNTRY_CENTERS[c][1] for c in rows["country"]], mode="markers+text",
                text=[f"{COUNTRY_FLAGS.get(c, '')} {COUNTRY_LABELS.get(c, c)}" for c in rows["country"]], textposition="bottom center", name="技术专利公开",
                marker={"size": [10 + 4 * math.sqrt(n) for n in rows["count"]], "color": "#2d91c8", "opacity": .88, "line": {"width": 1.5, "color": "#fff"}},
                customdata=[[COUNTRY_LABELS.get(c, c), int(n)] for c, n in zip(rows["country"], rows["count"])], hovertemplate="%{customdata[0]}<br>同月公开：%{customdata[1]} 条<extra></extra>"))
    fig.update_layout(height=650, margin={"l": 0, "r": 0, "t": 10, "b": 25}, showlegend=True,
        legend={"orientation": "h", "y": .01, "x": .5, "xanchor": "center", "font": {"size": 10}},
        geo={"projection": {"type": "orthographic", "rotation": {"lat": 90, "lon": 0}}, "showland": True, "landcolor": "#eaf4f8", "showocean": True, "oceancolor": "#d7eef8", "showlakes": True, "lakecolor": "#d7eef8", "showcoastlines": True, "coastlinecolor": "#7eabc0", "showframe": False, "bgcolor": "#f8fcff"},
        paper_bgcolor="#ffffff")
    return fig


REGION_CENTERS = {"barents": (73, 38), "kara": (75, 77), "chukchi": (70, -170)}


def _evidence_cards(month: str, patents: pd.DataFrame, gdelt: pd.DataFrame, region_frame: pd.DataFrame) -> None:
    climate = region_frame.loc[region_frame["date"].eq(month)] if not region_frame.empty else pd.DataFrame()
    climate_text = f"{len(climate)} 个有观测区域" if not climate.empty else "当前月无区域表记录"
    p_year = _same_year(patents, int(month[:4]))
    st.markdown(
        f"<div class='coupling-chain'><div class='coupling-node climate'><small>01 / CLIMATE SIGNAL</small><b>海冰环境</b><span>{climate_text} · 影像 {month}</span></div><div class='coupling-arrow'>→</div><div class='coupling-node activity'><small>02 / ACTIVITY CONDITION</small><b>航道与活动条件</b><span>以航线参考、区域冰情和事件记录共同定位</span></div><div class='coupling-arrow'>→</div><div class='coupling-node technology'><small>03 / TECHNOLOGY RESPONSE</small><b>技术与专利</b><span>同月公开 {len(patents):,} 条 · 同年 {len(p_year):,} 条</span></div><div class='coupling-arrow'>→</div><div class='coupling-node geopolitics'><small>04 / GOVERNANCE</small><b>地缘互动</b><span>当月 GDELT 候选 {len(gdelt):,} 条</span></div></div>", unsafe_allow_html=True)


def render_coupling_page() -> None:
    ice_options = _month_options()
    if not ice_options:
        st.error("未找到海冰月度影像索引，无法启动耦合探索器。")
        return
    default = "2019-09" if "2019-09" in ice_options else ice_options[-1]
    section_title("ARCTIC COUPLING EXPLORER", "气候 · 地缘 · 技术动态联动", "在同一时间轴上查看海冰环境、航线参考、地缘事件候选与技术专利公开；每条线索都保留自己的资料边界。")
    st.markdown("<div class='coupling-hero'><div><b>不是一个未经验证的耦合指数</b><span>从气候信号出发，沿着活动条件、技术响应与治理互动追踪一条可核验的研究链。</span></div><div class='coupling-hero-tag'>2016—2026 · 月度探索</div></div>", unsafe_allow_html=True)
    left, right = st.columns([1.45, 1])
    month = left.select_slider("统一时间轴 · 海冰月份", options=ice_options, value=default, key="coupling-month")
    layers = right.multiselect("地图图层", ["气候信号", "航线参考", "科考站", "地缘事件", "技术专利"], default=["气候信号", "航线参考", "科考站", "地缘事件", "技术专利"], key="coupling-layers")
    summary = _month_summary(month)
    patents, gdelt = summary["patents"], summary["gdelt"]
    regions = _load_region_frame()
    image_path = _closest_image(month)
    image_col, map_col = st.columns([.9, 1.65], gap="large")
    with image_col:
        st.markdown(f"<div class='coupling-panel-heading'><span>CLIMATE LAYER · {month}</span><b>北极海冰密集度</b><small>NSIDC Sea Ice Index 月度影像，影像是环境背景，不直接等于航道通行结论。</small></div>", unsafe_allow_html=True)
        if image_path:
            st.image(str(image_path), width="stretch")
        ice = summary["ice"]
        a, b = st.columns(2)
        a.metric("海冰范围", f"{float(ice.get('extent', 0) or 0):.2f} 百万 km²" if ice.get("extent") not in (None, "") else "未记录")
        b.metric("海冰面积", f"{float(ice.get('area', 0) or 0):.2f} 百万 km²" if ice.get("area") not in (None, "") else "未记录")
        st.caption("图像与索引来自本站保存的 NSIDC Sea Ice Index 月度资料；区域表只覆盖已整理的巴伦支海、喀拉海和楚科奇海。")
    with map_col:
        st.markdown("<div class='coupling-panel-heading'><span>SPATIAL COUPLING MAP</span><b>空间联动视图</b><small>国家级事件与专利标记只代表来源主体/公开地区，不代表具体部署或事件坐标。</small></div>", unsafe_allow_html=True)
        show_chart(_coupling_map(month, patents, gdelt, regions, layers), key="coupling-map", config={"displayModeBar": True, "displaylogo": False})
    _evidence_cards(month, patents, gdelt, regions)
    tabs = st.tabs(["空间联动", "机制分析", "证据与边界"])
    with tabs[0]:
        st.markdown("<div class='coupling-section-heading'><span>SELECTED MONTH</span><b>当前月份的证据摘要</b><small>三类资料按同一个 YYYY-MM 选择器联动，但各自的日期口径仍然分开。</small></div>", unsafe_allow_html=True)
        p_year = _same_year(patents, int(month[:4]))
        g_types = Counter(gdelt.get("relation_type", pd.Series(dtype=str)).astype(str).tolist()) if not gdelt.empty else Counter()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("月度海冰影像", "1 张", "已接入")
        c2.metric("当月地缘候选", f"{len(gdelt):,}", "GDELT 事件记录")
        c3.metric("当月专利公开", f"{len(patents):,}", "按公开日归档")
        c4.metric("同年专利公开", f"{len(p_year):,}", "避免把空月份当成无技术活动")
        if g_types:
            st.write("当月事件类型：" + "、".join(f"{key.replace('gdelt_', '')}（{value}）" for key, value in g_types.most_common(5)))
        st.dataframe(pd.DataFrame([{"日期": row.get("date", ""), "类型": row.get("technology_display", ""), "国家": row.get("country_label", ""), "标题": row.get("title_display", ""), "来源": row.get("source_url", "")} for _, row in patents.head(8).iterrows()]), hide_index=True, width="stretch") if not patents.empty else st.info("当前月份没有已整理的专利公开记录；右侧指标同时显示同年记录，避免误读为技术活动为零。")
    with tabs[1]:
        st.markdown("<div class='coupling-section-heading'><span>MECHANISM HYPOTHESIS</span><b>从环境变化到技术与治理响应</b><small>这是待检验的机制假设，页面不把时间同现自动解释成因果关系。</small></div>", unsafe_allow_html=True)
        st.markdown("<div class='mechanism-grid'><div><small>A / 环境信号</small><b>海冰变化</b><p>用月度影像与区域海冰范围描述背景条件，先回答“哪里、什么时候发生了什么变化”。</p></div><div><small>B / 活动条件</small><b>航线与活动</b><p>用北方海航道和西北航道参考线承载空间问题；真实船舶轨迹需要接入 AIS 或 PAME ASTD 后再替换。</p></div><div><small>C / 技术响应</small><b>专利公开</b><p>把公开日或优先权日归入时间轴，显示技术主题与申请人国家，不把专利公开等同于实际部署。</p></div><div><small>D / 治理互动</small><b>地缘事件</b><p>GDELT 记录是机器编码的新闻候选，需回到原文和官方材料核验，不能直接作为外交关系强度。</p></div></div>", unsafe_allow_html=True)
        st.info("建议的研究检验路径：先按区域和月份对齐海冰、航运和公开事件，再检查滞后窗口与替代解释；只有在指标、覆盖和混杂因素处理充分后，才讨论统计关联。")
    with tabs[2]:
        st.markdown("<div class='coupling-section-heading'><span>TRACEABILITY</span><b>资料来源与使用边界</b><small>下载当前月份的联动快照，带回页面使用的原始字段。</small></div>", unsafe_allow_html=True)
        st.markdown("- 海冰：NSIDC Sea Ice Index 月度影像与本站索引；区域数值表保留 1991—2020 同月基准。\n- 地缘：GDELT 结构化网络样本与归档候选，按事件日期分组。\n- 技术：本站已整理的公开专利详情库，按公开日优先、优先权日回退。\n- 航线与站点：当前为参考线路和固定位置，点击地图不会把示意线解释为真实航迹。")
        export = {"month": month, "ice": summary["ice"], "patents": patents.fillna("").to_dict("records"), "gdelt": gdelt.fillna("").to_dict("records"), "scope": "三轴联动展示，不构成因果结论。"}
        st.download_button("下载当前月份联动快照 · JSON", json.dumps(export, ensure_ascii=False, default=str, indent=2), f"arctic-coupling-{month}.json", "application/json", key="coupling-download", on_click="ignore")
        st.warning("当前页面把气候、地缘和技术作为可追踪证据层并列展示。它们的时间粒度、地理精度和覆盖范围不同，不能据此宣称已经证明三者之间存在因果闭环。")

