"""
关于本项目
深色沉浸主题 v6.0
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="关于本项目", page_icon="ℹ️", layout="wide")

st.markdown("""
<style>
    :root { --bg: #0a0e1a; --bg2: #111827; --card: #1a2236; --card2: #1f2a42; --border: rgba(255,255,255,0.07); --text: rgba(255,255,255,0.92); --text2: rgba(255,255,255,0.6); --text3: rgba(255,255,255,0.35); }
    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] { background: var(--bg) !important; }
    section[data-testid="stMain"] > div { background: transparent !important; }
    [data-testid="stMainBlockContainer"] { background: transparent !important; padding-top: 0 !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e1a, #111827) !important; }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    section[data-testid="stMain"] p, section[data-testid="stMain"] span, section[data-testid="stMain"] h1, section[data-testid="stMain"] h2, section[data-testid="stMain"] h3, section[data-testid="stMain"] h4, section[data-testid="stMain"] li { color: var(--text) !important; }
    .stMarkdown p, .stMarkdown li { color: var(--text2) !important; }
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px !important; padding: 8px 18px !important; font-weight: 600 !important; font-size: 0.85rem !important; color: var(--text2) !important; background: transparent !important; }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.06) !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(100,116,139,0.2) !important; color: #cbd5e1 !important; }
    hr { border: none !important; border-top: 1px solid var(--border) !important; }
    .page-header { background: linear-gradient(135deg, #0f172a 0%, #334155 100%); padding: 1.8rem 2rem; border-radius: 0 0 18px 18px; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(100,116,139,0.15); position: relative; overflow: hidden; }
    .page-header::before { content: ''; position: absolute; top: -50%; right: -5%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(100,116,139,0.06) 0%, transparent 70%); pointer-events: none; }
    .page-header h1 { color: white !important; font-size: 1.6rem; font-weight: 700; margin: 0 0 0.3rem 0; position: relative; z-index: 1; }
    .page-header p { color: rgba(255,255,255,0.5) !important; font-size: 0.83rem; margin: 0; position: relative; z-index: 1; }
    .dk-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 1.3rem; margin-bottom: 1.2rem; }
    .dk-card:hover { background: var(--card2); }
    .dk-card h2 { font-size: 1rem; font-weight: 700; color: var(--text); margin: 0 0 0.8rem 0; padding-bottom: 0.6rem; border-bottom: 1px solid var(--border); }
    .module-list-item { display: flex; gap: 12px; padding: 0.9rem 0; border-bottom: 1px solid var(--border); }
    .module-list-item:last-child { border-bottom: none; }
    .module-list-item .m-icon { font-size: 1.8rem; flex-shrink: 0; }
    .module-list-item .m-title { font-weight: 700; color: #93c5fd; font-size: 0.95rem; margin-bottom: 3px; }
    .module-list-item .m-desc { font-size: 0.8rem; color: var(--text2); line-height: 1.5; margin: 0; }
    .arch-card { background: var(--card); border-radius: 12px; padding: 1rem; border: 1px solid var(--border); }
    .arch-card h4 { font-size: 0.9rem; font-weight: 700; color: var(--text); margin: 0 0 0.6rem 0; }
    .arch-card ul { font-size: 0.78rem; color: var(--text2); line-height: 1.9; margin: 0; padding-left: 1.2rem; }
    .team-card { background: var(--card); border-radius: 12px; padding: 1rem; border: 1px solid var(--border); text-align: center; }
    .team-card .avatar { width: 52px; height: 52px; background: rgba(59,130,246,0.1); border-radius: 50%; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
    .team-card .role { font-weight: 700; font-size: 0.88rem; color: #93c5fd; margin-bottom: 3px; }
    .team-card .desc { font-size: 0.72rem; color: var(--text3); }
    .ms-item { display: flex; gap: 10px; padding: 0.5rem 0; align-items: flex-start; }
    .ms-item .ms-dot { width: 10px; height: 10px; background: #60a5fa; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
    .ms-item .ms-date { font-size: 0.72rem; color: var(--text3); font-weight: 600; min-width: 50px; }
    .ms-item .ms-text { font-size: 0.78rem; color: var(--text2); line-height: 1.4; }
</style>
<div class="page-header">
    <h1>ℹ️ 关于本项目</h1>
    <p>项目介绍 · 研究框架 · 技术架构 · 团队信息</p>
</div>
""", unsafe_allow_html=True)


# ============ 项目介绍 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>📋 项目介绍</h2>', unsafe_allow_html=True)

st.markdown("""
**北极地缘与技术多要素联动3D可视化平台**是基于「大北极」格局下地缘与技术双向互动机制研究开发的数据可视化系统。

本平台立足地理学、政治学与计算机科学的跨学科交叉，聚焦以下核心研究问题：

1. **气候驱动机制**：北极海冰快速融化如何从物理层面催生新航道？
2. **技术竞争格局**：大国在高端船舶制造与极地通信卫星领域的博弈如何演变？
3. **中国应对策略**：如何在规则制定、科技合作与风险防控三条路径上构建北极战略？
""")
st.markdown('</div>', unsafe_allow_html=True)


# ============ 核心成果 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>🎯 项目核心成果</h2>', unsafe_allow_html=True)

成果_cols = st.columns(3)
成果_data = [
    ("💻", "软件开发", "基于 Python + Streamlit 的北极地缘与技术互动3D动态可视化平台，集成 Plotly / Folium 专业可视化库，一键部署至 Streamlit Community Cloud，全平台支持。"),
    ("📊", "专题研究报告", "约 2-3万字 的深度研究报告，包含「技术-地缘」双向互动机制、大北极国家网络演化规律、中国安全应对策略建议等核心内容。"),
    ("📄", "学术论文", "提炼平台构建方法与数据挖掘成果，目标 SCI/SSCI期刊或高水平学术会议，聚焦地缘政治与地理信息科学交叉领域。"),
]
for i, (icon, title, desc) in enumerate(成果_data):
    with 成果_cols[i]:
        st.markdown(f"""
        <div style="background:var(--card);border-radius:12px;padding:1rem;border-left:4px solid #3b82f6;">
            <div style="font-size:1.8rem;margin-bottom:0.4rem;">{icon}</div>
            <div style="font-weight:700;font-size:0.95rem;color:#93c5fd;margin-bottom:0.4rem;">{title}</div>
            <div style="font-size:0.8rem;color:var(--text2);line-height:1.6;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ============ 六大模块 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>🧭 平台六大核心模块</h2>', unsafe_allow_html=True)

modules = [
    ("🗺️", "北极全景地图", "融合Plotly 3D地球仪 + Folium交互地图 + GDELT热力叠加，点击标记查看科考站/航道详情，支持多底图切换"),
    ("🌡️", "气候时空监测", "1980-2025年气温/海冰时空演变，CMIP6情景预测，航道通航评估，M-K突变检验"),
    ("🏛️", "地缘战略格局", "大国博弈网络图谱、政策文本词云与情感分析、科考站详情、GDELT事件统计"),
    ("⚙️", "技术竞争与合作", "专利气泡图、热力图、技术合作网络、五国竞争力雷达图、「技术-地缘」双轴联动看板"),
    ("🛡️", "安全风险评估", "四维风险热力图、SWOT可视化、中国应对策略推演沙盘（5种情景）"),
    ("🗄️", "数据中心", "数据集下载（CSV/GeoJSON）、CSV上传可视化（5种图表类型）、时空查询工具、多指标归一化对比分析"),
]
for icon, title, desc in modules:
    st.markdown(f"""
    <div class="module-list-item">
        <div class="m-icon">{icon}</div>
        <div>
            <div class="m-title">{title}</div>
            <div class="m-desc">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ============ 技术架构 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>🏗️ 技术架构</h2>', unsafe_allow_html=True)

arch_cols = st.columns(3)
arch_data = [
    ("📂 数据层", ["GDELT 全球事件数据库", "NSIDC 海冰监测数据", "各国北极政策文件", "专利数据库（模拟）", "GeoJSON 地理数据"]),
    ("⚙️ 计算层", ["Python 3.10+", "Pandas 数据处理", "NumPy 科学计算", "自定义 M-K 趋势检验", "Folium 地图渲染"]),
    ("🖥️ 展示层", ["Streamlit Web框架", "Plotly 交互图表", "Folium 地图可视化", "Streamlit Community Cloud"]),
]
for i, (title, items) in enumerate(arch_data):
    with arch_cols[i]:
        st.markdown(f"""
        <div class="arch-card">
            <h4>{title}</h4>
            <ul>{''.join(f'<li>{item}</li>' for item in items)}</ul>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ============ 学术框架 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>📐 学术研究框架</h2>', unsafe_allow_html=True)

st.markdown("""
本项目突破传统地缘政治的单向分析视角，引入「技术-地缘」互动框架：

**核心假设：** 极地技术进步（破冰船、通信卫星、资源开采）不仅是地缘竞争的结果，更是驱动地缘格局演变的关键动力。
""")

fw_cols = st.columns(3)
fw_data = [
    ("🔬 技术→地缘", "技术突破拓展存在边界", "核动力破冰船延伸俄罗斯北极存在", "#3b82f6"),
    ("🗺️ 地缘→技术", "战略需求驱动技术投入", "北极航道竞争推动极地船舶研发", "#ef4444"),
    ("🤝 技术→合作", "科技合作维持对话压舱石", "北极理事会气候监测联合研究", "#22c55e"),
]
for i, (title, mechanism, case, color) in enumerate(fw_data):
    with fw_cols[i]:
        st.markdown(f"""
        <div style="background:var(--card);border-radius:12px;padding:1rem;border-top:3px solid {color};">
            <div style="font-weight:700;color:{color};font-size:0.88rem;margin-bottom:0.5rem;">{title}</div>
            <div style="font-size:0.75rem;color:var(--text2);line-height:1.5;">
                <b>机制：</b>{mechanism}<br>
                <b>案例：</b>{case}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
**分析维度：**
- **气候环境**：海冰面积、通航窗口（来源：NSIDC）
- **地缘博弈**：事件数量、情感值（来源：GDELT）
- **技术竞争**：专利数量、合作网络（来源：专利数据库）
- **风险评估**：多维风险矩阵（来源：综合评估）
""")
st.markdown('</div>', unsafe_allow_html=True)


# ============ 团队 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>👥 项目团队</h2>', unsafe_allow_html=True)

team_cols = st.columns(4)
team = [
    ("项目负责人", "研究方向：极地战略与地缘政治"),
    ("核心开发", "技术实现：数据可视化与Web开发"),
    ("数据分析", "数据处理：GDELT、NSIDC数据清洗"),
    ("内容策划", "内容撰写：政策分析与报告撰写"),
]
for i, (role, desc) in enumerate(team):
    with team_cols[i]:
        st.markdown(f"""
        <div class="team-card">
            <div class="avatar">👤</div>
            <div class="role">{role}</div>
            <div class="desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ============ 项目大事记 ============
st.markdown('<div class="dk-card">', unsafe_allow_html=True)
st.markdown('<h2>📅 项目发展历程</h2>', unsafe_allow_html=True)

milestones = [
    ("2024.09", "项目启动", "完成需求分析与技术选型"),
    ("2024.10", "平台开发", "完成核心可视化模块开发"),
    ("2024.11", "数据整合", "接入 GDELT、NSIDC 数据"),
    ("2024.12", "功能完善", "增加策略推演、风险矩阵等功能"),
    ("2025.01", "内测上线", "完成首版平台部署测试"),
    ("2025.02", "优化迭代", "UI优化与Bug修复"),
    ("2025.03", "中期检查", "完成阶段性成果汇报"),
    ("2025.04", "论文撰写", "开始学术论文写作"),
]

mil_cols = st.columns(len(milestones))
for i, (date, event, desc) in enumerate(milestones):
    with mil_cols[i]:
        st.markdown(f"""
        <div class="ms-item">
            <div class="ms-dot"></div>
            <div>
                <div class="ms-date">{date}</div>
                <div class="ms-text" style="font-weight:600;color:var(--text);">{event}</div>
                <div class="ms-text">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


st.divider()
st.markdown("""
**引用说明：** 本平台可作为教学和科研工具免费使用。如需在学术论文中引用，请参考以下格式：

> 项目组. 北极地缘与技术多要素联动3D可视化平台 v6.0 [EB/OL]. https://arctic-viz-dmfjpjmbr7mqqndyzgfwcm.streamlit.app/, 2025-2026.

© 2025-2026 北极地缘与技术双向互动机制研究 · 大学生创新创业训练计划专项
""")
