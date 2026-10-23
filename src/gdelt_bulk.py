"""Large GDELT candidate-event library used by the geopolitics search page."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from src.presentation import ROOT, show_chart

DATA_PATH = ROOT / "data/analysis/gdelt/bulk/gdelt_geopolitics_22815.csv"


@st.cache_data(show_spinner=False)
def load_bulk_candidates() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    frame = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    return frame


def render_bulk_candidates() -> None:
    frame = load_bulk_candidates()
    if frame.empty:
        st.warning("大规模 GDELT 候选库尚未随部署包发布。")
        return
    st.markdown('<div class="data-note"><b>大规模新闻候选库</b><span>22,815 条 GDELT 机器候选事件，来自 2019-09-17—2019-09-23 七个官方日档。它补充事件检索，不替代逐条原文核验。</span></div>', unsafe_allow_html=True)
    st.subheader("大规模候选事件检索")
    st.caption("记录保留原始新闻链接、CAMEO 关系类别和行动地点；网站将其作为新闻感知层单独展示。")
    a, b, c, d = st.columns(4)
    a.metric("候选事件", f"{len(frame):,}")
    b.metric("有原文链接", f"{frame['source_url'].astype(bool).sum():,}")
    c.metric("候选日期", f"{frame['date'].min().date()}—{frame['date'].max().date()}")
    d.metric("关系类别", frame["relation_type"].nunique())
    c1, c2, c3 = st.columns(3)
    years = sorted(int(x) for x in frame["year"].dropna().unique())
    year = c1.selectbox("事件年份", ["全部年份", *years], key="bulk-gdelt-year")
    relation = c2.selectbox("关系类别", ["全部类别", *sorted(frame["relation_type"].dropna().unique())], key="bulk-gdelt-relation")
    query = c3.text_input("检索地点、参与方或标题", key="bulk-gdelt-query", placeholder="例如 Canada、Svalbard、Arctic").strip().casefold()
    filtered = frame
    if year != "全部年份": filtered = filtered[filtered["year"] == int(year)]
    if relation != "全部类别": filtered = filtered[filtered["relation_type"] == relation]
    if query:
        hay = filtered[["title", "participants_or_leads", "location", "summary"]].fillna("").astype(str).agg(" ".join, axis=1).str.casefold()
        filtered = filtered[hay.str.contains(query, regex=False)]
    st.caption(f"当前筛选 {len(filtered):,} 条；候选事件不等于已核验现实事件。")
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        top = filtered["relation_type"].value_counts().head(8).rename_axis("relation_type").reset_index(name="count")
        fig = px.bar(top, x="count", y="relation_type", orientation="h", labels={"count": "候选数", "relation_type": "关系类别"}, color_discrete_sequence=["#2e91d2"])
        fig.update_layout(height=330, margin=dict(l=10, r=20, t=20, b=35), yaxis=dict(categoryorder="total ascending"))
        show_chart(fig, key="bulk-gdelt-relations")
    with right:
        shown = filtered.sort_values("date").tail(300)
        rows = shown[["date", "title", "participants_or_leads", "location", "relation_type", "source_url"]].copy()
        rows["date"] = rows["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(rows.rename(columns={"date": "日期", "title": "机器标题", "participants_or_leads": "参与方", "location": "行动地点", "relation_type": "关系类别", "source_url": "来源链接"}), hide_index=True, height=330, width="stretch", column_config={"来源链接": st.column_config.LinkColumn("来源链接", display_text="打开原文")})
    st.download_button("下载当前筛选候选库", filtered.to_csv(index=False).encode("utf-8-sig"), "gdelt-arctic-candidates-filtered.csv", "text/csv", key="bulk-gdelt-download", on_click="ignore")
    with st.expander("来源与方法"):
        st.write("GDELT 1.0 官方日档按北极国家参与方、高纬行动地理、北极主题词或跨北极国家关系筛选。机器编码的事件、文章数和 Goldstein 倾向需要回到原文后才能成为核验事实。")
        st.code("https://data.gdeltproject.org/events/", language=None)
