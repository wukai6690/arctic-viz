"""Supplementary global bilateral context, kept separate from Arctic counts."""
import csv
import gzip
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / 'data/analysis/gdelt/bilateral_background/daily_bilateral.csv.gz'


@st.cache_data(show_spinner=False)
def load_background() -> dict:
    pairs = {}
    if DATA.exists():
        with gzip.open(DATA, 'rt', encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                if 'GRL' not in (row['country_i'], row['country_j']):
                    pairs.setdefault((row['country_i'], row['country_j']), []).append(row)
    return pairs


def background_figure(rows: list[dict]) -> go.Figure:
    fig = go.Figure()
    for field, label, color in [('relation_daily', '每日指数', '#a7bdce'),
                                ('relation_window', '30天滚动指数', '#287db0')]:
        fig.add_trace(go.Scatter(x=[r['date'] for r in rows],
            y=[float(r[field]) if r[field] else None for r in rows],
            customdata=[[r['event_count'] or '缺失'] for r in rows],
            mode='lines', name=label, connectgaps=False,
            line={'color':color,'width':1 if field=='relation_daily' else 2.5},
            hovertemplate='%{x}<br>'+label+' %{y:.3f}<br>当日事件 %{customdata[0]}<extra></extra>'))
    fig.update_layout(height=320, margin={'l':45,'r':15,'t':15,'b':35},
        xaxis_title='事件日期（SQLDATE）', yaxis={'title':'合作−冲突 / 合作+冲突','range':[-1.05,1.05]},
        legend={'orientation':'h','y':1.15}, paper_bgcolor='white', plot_bgcolor='#fbfdff')
    return fig


def render_background(labels: dict, key: str) -> None:
    pairs = load_background()
    if not pairs:
        return
    with st.expander('补充：全球双边关系背景与30天趋势', expanded=False):
        st.caption('独立口径：统计两国在全球范围的新闻编码互动，按事件日期归属；不与上方北极地域筛选事件相加。')
        options = sorted(pairs)
        left, right = st.columns([2,1])
        pair = left.selectbox('国家对', options, index=options.index(('CHN','USA')),
            format_func=lambda p: labels[p[0]]+' ↔ '+labels[p[1]], key=key+'-pair')
        year = right.selectbox('趋势年份', ['2016—2025', *map(str,range(2016,2026))], key=key+'-year')
        rows = [r for r in pairs[pair] if year=='2016—2025' or r['date'].startswith(year)]
        st.plotly_chart(background_figure(rows), width='stretch', key=key+'-trend')
        st.caption('指数取值 −1 到 1；正值为合作占优，负值为冲突占优。没有事件时不计算比值；缺失源档及跨缺档的滚动窗口留空，不作插值。')
        st.caption('来源：用户提供的 GDELT 1.0 双边聚合包，2016—2025。格陵兰单列编码全为零，暂不纳入选择。审计筛选总数与发布表相差371条，原因待核对；此图仅作背景参考，未用于主网络总量。')
