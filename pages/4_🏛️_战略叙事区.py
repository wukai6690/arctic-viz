"""
战略叙事图文联动页面
按时间线展示中国北极战略演进，配合时间滑块与地图自动切换
"""

import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.narrative import NARRATIVE_CARDS, get_all_years, get_narrative_by_year, get_policy_recommendations

st.set_page_config(page_title="战略叙事区", page_icon="🏛️", layout="wide")

st.markdown("## 🏛️ 北极战略叙事区")
st.markdown("""
通过时间线视角，呈现 **1979-2024** 年间北极地缘格局演变与中国北极战略演进。
本页面配合地图页面的时间滑块，实现「图-文-数」三位一体的叙事联动。
""")
st.divider()

# 顶部时间轴概览
all_years = get_all_years()

st.markdown("### ⏳ 北极战略演进时间轴 (1979-2024)")

year_options = {year: f"{year}年" for year in all_years}

timeline_cols = st.columns(len(all_years))
for i, year in enumerate(all_years):
    with timeline_cols[i]:
        year_int = int(year)
        card = NARRATIVE_CARDS[year_int]
        short_title = card['title'][:8] + '...' if len(card['title']) > 8 else card['title']
        st.markdown(
            f"<div style='text-align:center;padding:0.3rem;'>"
            f"<div style='font-weight:700;font-size:0.9rem;color:#1E88E5'>{year}</div>"
            f"<div style='font-size:0.7rem;color:#546E7A;line-height:1.3'>{short_title}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

st.divider()

# 主内容区
selected = st.select_slider(
    "拖动时间轴，查看不同时期的战略叙事",
    options=all_years,
    value=all_years[-1],
    format_func=lambda y: f"{y}年"
)

narrative = get_narrative_by_year(selected)
recs = get_policy_recommendations()

# 主体叙事
col_main, col_side = st.columns([7, 3])

with col_main:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1E88E5 0%,#1565C0 100%);
                color:white;padding:1.5rem;border-radius:16px;margin-bottom:1rem;">
        <h2 style="margin:0 0 0.3rem 0;">📅 {selected}年</h2>
        <h3 style="margin:0 0 0.5rem 0;font-weight:400;">{narrative['title']}</h3>
        <div style="opacity:0.85;font-size:0.9rem;">📆 {narrative['period']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:#f8f9fa;padding:1.2rem;border-radius:12px;
                border-left:4px solid #1E88E5;margin-bottom:1rem;">
        <h4 style="margin-top:0;color:#1E88E5">📖 战略态势综述</h4>
        <p style="font-size:1.05rem;line-height:1.8;">{narrative['summary']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🔑 关键事件")
    for event in narrative['key_events']:
        st.markdown(f"- **{event}**")

    st.divider()

    st.markdown("""
    <div style="background:#fff3e0;padding:1.2rem;border-radius:12px;
                border-left:4px solid #FF6B35;margin-top:1rem;">
        <h4 style="margin-top:0;color:#E65100;">🇨🇳 中国视角</h4>
        <p style="font-size:1rem;line-height:1.8;">""" + narrative['chinese_angle'] + """</p>
    </div>
    """, unsafe_allow_html=True)

    if 'tech_competition' in narrative:
        st.markdown("""
        <div style="background:#f3e5f5;padding:1.2rem;border-radius:12px;
                    border-left:4px solid #7B1FA2;margin-top:1rem;">
            <h4 style="margin-top:0;color:#7B1FA2;">⚙️ 技术竞争焦点</h4>
            <p style="font-size:1rem;line-height:1.8;">""" + narrative['tech_competition'] + """</p>
        </div>
        """, unsafe_allow_html=True)

    if 'policy_recommendation' in narrative:
        st.markdown("""
        <div style="background:#e8f5e9;padding:1.2rem;border-radius:12px;
                    border-left:4px solid #2E7D32;margin-top:1rem;">
            <h4 style="margin-top:0;color:#2E7D32;">🛡️ 政策建议</h4>
            <p style="font-size:1rem;line-height:1.8;">""" + narrative['policy_recommendation'] + """</p>
        </div>
        """, unsafe_allow_html=True)

with col_side:
    st.markdown("### 📌 核心信息卡")
    st.markdown(f"""
    <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
        <div style="font-size:0.75rem;color:#90A4AE;margin-bottom:0.3rem;">年份</div>
        <div style="font-size:1.3rem;font-weight:700;color:#1E88E5;">{selected}年</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
        <div style="font-size:0.75rem;color:#90A4AE;margin-bottom:0.3rem;">主题</div>
        <div style="font-size:1rem;font-weight:600;">{narrative['period']}</div>
    </div>
    """, unsafe_allow_html=True)

    event_count = len(narrative['key_events'])
    st.markdown(f"""
    <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
        <div style="font-size:0.75rem;color:#90A4AE;margin-bottom:0.3rem;">关键事件</div>
        <div style="font-size:1.3rem;font-weight:700;">{event_count}项</div>
    </div>
    """, unsafe_allow_html=True)

    has_tech = 'tech_competition' in narrative
    st.markdown(f"""
    <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1rem;margin-bottom:0.8rem;">
        <div style="font-size:0.75rem;color:#90A4AE;margin-bottom:0.3rem;">技术竞争</div>
        <div style="font-size:1rem;font-weight:600;">{'有' if has_tech else '无'}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔗 图文联动")
    st.info("""
    进入「北极地图概览」页面，
    拖动时间滑块到 **""" + str(selected) + """年**，
    地图将同步显示该年的地缘事件分布。
    """)
    st.markdown("""
    配合本页叙事文字，
    实现时间、空间、文本的三维联动效果。
    """)

# 底部：三大政策建议
st.divider()
st.markdown("### 🛡️ 中国北极安全应对策略（综合框架）")

rec_cols = st.columns(3)
rec_data = [
    ("1️⃣", "深度参与规则制定", recs['rule_participation']['title'],
     recs['rule_participation']['description'],
     "#1565C0", "📜"),
    ("2️⃣", "深化科技合作", recs['tech_cooperation']['title'],
     recs['tech_cooperation']['description'],
     "#2E7D32", "🔬"),
    ("3️⃣", "完善风险防控体系", recs['risk_control']['title'],
     recs['risk_control']['description'],
     "#C62828", "🛑"),
]

for i, (num, title, subtitle, desc, color, icon) in enumerate(rec_data):
    with rec_cols[i]:
        st.markdown(f"""
        <div style="background:white;border:1px solid #e0e0e0;border-radius:16px;
                    padding:1.5rem;height:100%;">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">{num}</div>
            <h4 style="margin:0 0 0.3rem 0;color:{color};">{title}</h4>
            <div style="font-size:0.85rem;color:#90A4AE;margin-bottom:0.8rem;">{subtitle}</div>
            <p style="font-size:0.9rem;line-height:1.7;color:#37474F;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("""
**「技术赋能地缘」分析框架说明：**

本项目突破传统单向地缘分析，引入「技术-地缘」互动框架：

1. **技术进步 → 地缘扩展**：极地破冰船技术、核动力推进、极地通信卫星、深海探测能力等技术突破，
   拓展了国家在北极的存在边界和影响范围
2. **地缘需求 → 技术投入**：航道竞争和资源开发的战略需求，反向驱动高端船舶制造和极地基础设施投资
3. **技术合作 → 信任构建**：在政治对抗加剧的背景下，科技合作（极地科考、环境保护、气候监测）
   成为维持大国北极对话的『压舱石』

这就是为什么本平台将「高端船舶制造」和「极地通信卫星」作为技术竞争的核心观察指标。
""")
