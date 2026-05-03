"""
关于本项目页面
项目成果展示、学术框架、团队信息
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="关于项目", page_icon="ℹ️", layout="wide")


# =========================================================================
# 全局样式
# =========================================================================
st.markdown("""
<style>
    .stApp [data-testid="stMainBlockContainer"] { background: #ffffff; }
    section[data-testid="stMain"] { background: #ffffff; }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown li, section[data-testid="stMain"] p,
    section[data-testid="stMain"] h1, section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3, section[data-testid="stMain"] h4 {
        color: #1e293b !important;
    }
    .page-hero {
        background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
        border-radius: 14px;
        padding: 36px 32px;
        margin-bottom: 28px;
    }
    .page-hero h1 { color: white !important; font-size: 1.6rem; font-weight: 800; margin: 0 0 6px 0; }
    .page-hero p { color: rgba(255,255,255,0.8) !important; font-size: 0.88rem; margin: 0; }
    .section-title {
        font-size: 1rem; font-weight: 700; color: #0f172a;
        margin-bottom: 16px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0;
    }
    .result-card {
        background: white; border-radius: 12px; padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.04);
        height: 100%;
    }
    .result-icon { font-size: 2rem; margin-bottom: 12px; }
    .result-title { font-weight: 700; font-size: 1rem; color: #0f172a; margin-bottom: 8px; }
    .result-desc { font-size: 0.82rem; color: #64748b; line-height: 1.6; }
    .arch-card {
        background: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# =========================================================================
# 侧边栏
# =========================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 12px 0 20px 0;">
            <div style="font-size:2.5rem;">ℹ️</div>
            <div style="font-size:1.05rem; font-weight:700; color:white !important; margin-top:6px;">关于项目</div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.55);">v5.0</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<hr style="border-color:rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        pages_map = [
            ("🏠", "首页概览", "app.py"),
            ("🌡️", "气候时空监测", "pages/2_气候时空监测.py"),
            ("🏛️", "地缘战略格局", "pages/3_地缘战略格局.py"),
            ("⚙️", "技术竞争与合作", "pages/4_极地核心技术.py"),
            ("🛡️", "中国安全风险", "pages/5_中国安全风险.py"),
            ("🗄️", "数据中心工具", "pages/6_数据中心工具.py"),
            ("ℹ️", "关于本项目", "pages/7_关于本项目.py"),
        ]
        for icon, label, path in pages_map:
            st.page_link(path, label=label, icon=icon)
        st.divider()
        st.caption("© 2025-2026 大创专项")


render_sidebar()


# =========================================================================
# 页面头部
# =========================================================================
st.markdown("""
<div class="page-hero">
    <h1>ℹ️ 关于本项目</h1>
    <p>项目介绍 · 研究框架 · 技术架构 · 团队信息</p>
</div>
""", unsafe_allow_html=True)


# =========================================================================
# 项目介绍
# =========================================================================
st.markdown("## 📋 项目介绍")

st.markdown("""
**北极地缘与技术多要素联动3D可视化平台**是基于「大北极」格局下地缘与技术双向互动机制研究开发的数据可视化系统。

本平台立足地理学、政治学与计算机科学的跨学科交叉，聚焦以下核心研究问题：

1. **气候驱动机制**：北极海冰快速融化如何从物理层面催生新航道？
2. **技术竞争格局**：大国在高端船舶制造与极地通信卫星领域的博弈如何演变？
3. **中国应对策略**：如何在规则制定、科技合作与风险防控三条路径上构建北极战略？
""")

st.divider()


# =========================================================================
# 核心成果
# =========================================================================
st.markdown("## 🎯 项目核心成果")

成果_cols = st.columns(3)
成果_data = [
    ("💻", "软件开发", "基于 Python + Streamlit 的北极地缘与技术互动3D动态可视化平台，一键部署至 Streamlit Community Cloud，集成 Plotly / Folium 专业可视化库，全平台支持。"),
    ("📊", "专题研究报告", "约 2-3万字 的深度研究报告，包含「技术-地缘」双向互动机制、大北极国家网络演化规律、中国安全应对策略建议等核心内容。"),
    ("📄", "学术论文", "提炼平台构建方法与数据挖掘成果，目标 SCI/SSCI期刊或高水平学术会议，聚焦地缘政治与地理信息科学交叉领域。"),
]
for i, (icon, title, desc) in enumerate(成果_data):
    with 成果_cols[i]:
        st.markdown(f"""
        <div class="result-card">
            <div class="result-icon">{icon}</div>
            <div class="result-title">{title}</div>
            <div class="result-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 六大模块
# =========================================================================
st.markdown("## 🧭 平台六大核心模块")

modules = [
    ("🌡️", "气候时空监测", "气温、海冰密集度等要素的栅格热力图，支持时间滑块播放1980-2025年动态演变与CMIP6情景预测。点击区域弹出时间序列折线图、M-K突变检验结果、关键年份对比。"),
    ("🏛️", "地缘战略格局", "矢量展示各国军事基地、科考站与主权边界，构建大国博弈关系网络图谱，政策文本词频与情感分析，支持按历史阶段切换。"),
    ("⚙️", "技术竞争与合作", "极地核心专利时空分布气泡图+热力图，技术合作网络图谱，「技术-地缘」双轴联动看板，五国竞争力雷达图。"),
    ("🛡️", "安全风险评估", "航道通行、科考安全、技术壁垒、权益冲突四维风险矩阵，SWOT分析，中国应对策略推演沙盘（5种情景）。"),
    ("🗄️", "数据中心", "多源数据集下载（CSV/GeoJSON），CSV上传可视化（5种图表类型），时空查询工具，多指标归一化对比分析。"),
    ("ℹ️", "关于项目", "项目介绍、研究框架、技术架构与团队信息。"),
]

for icon, title, desc in modules:
    st.markdown(f"""
    <div style="display:flex;gap:14px;padding:12px 0;border-bottom:1px solid #f1f5f9;align-items:flex-start;">
        <div style="font-size:1.8rem;flex-shrink:0;width:36px;">{icon}</div>
        <div>
            <div style="font-weight:700;color:#0f172a;font-size:0.98rem;margin-bottom:4px;">{title}</div>
            <div style="font-size:0.82rem;color:#64748b;line-height:1.6;">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 技术架构
# =========================================================================
st.markdown("## 🏗️ 技术架构")

arch_cols = st.columns(3)
arch_data = [
    ("数据层", [
        "GDELT 全球事件数据库",
        "NSIDC 海冰监测数据",
        "各国北极政策文件",
        "专利数据库（模拟）",
        "GeoJSON 地理数据",
    ]),
    ("计算层", [
        "Python 3.10+",
        "Pandas 数据处理",
        "NumPy 科学计算",
        "自定义 M-K 趋势检验",
    ]),
    ("展示层", [
        "Streamlit Web框架",
        "Plotly 交互图表",
        "Folium 地图可视化",
        "Streamlit Community Cloud",
    ]),
]
for i, (title, items) in enumerate(arch_data):
    with arch_cols[i]:
        st.markdown(f"""
        <div class="arch-card">
            <div style="font-weight:700;color:#0f172a;margin-bottom:12px;font-size:0.95rem;">{title}</div>
            <div style="font-size:0.82rem;color:#64748b;line-height:2;">
                {''.join([f'<div>• {item}</div>' for item in items])}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 学术框架
# =========================================================================
st.markdown("## 📐 学术研究框架")

st.markdown("""
本项目突破传统地缘政治的单向分析视角，引入「技术-地缘」互动框架：

**核心假设**：极地技术进步（破冰船、通信卫星、资源开采）不仅是地缘竞争的结果，更是驱动地缘格局演变的关键动力。

**三条互动路径**：

| 路径 | 机制 | 典型案例 |
|------|------|---------|
| 技术→地缘 | 技术突破拓展存在边界 | 核动力破冰船延伸俄罗斯北极存在 |
| 地缘→技术 | 战略需求驱动技术投入 | 北极航道竞争推动极地船舶研发 |
| 技术→合作 | 科技合作维持对话压舱石 | 北极理事会气候监测联合研究 |

**分析维度**：

| 维度 | 观察指标 | 数据来源 |
|------|---------|---------|
| 气候环境 | 海冰面积、通航窗口 | NSIDC |
| 地缘博弈 | 事件数量、情感值 | GDELT |
| 技术竞争 | 专利数量、合作网络 | 专利数据库 |
| 风险评估 | 多维风险矩阵 | 综合评估 |
""")

st.divider()


# =========================================================================
# 团队
# =========================================================================
st.markdown("## 👥 项目团队")

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
        <div style="text-align:center;padding:16px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="width:56px;height:56px;background:#eff6ff;border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;">👤</div>
            <div style="font-weight:700;font-size:0.88rem;color:#0f172a;">{role}</div>
            <div style="font-size:0.75rem;color:#64748b;margin-top:4px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()


# =========================================================================
# 引用说明
# =========================================================================
st.markdown("""
**引用说明：** 本平台可作为教学和科研工具免费使用。如需在学术论文中引用，请参考以下格式：

> 项目组. 北极地缘与技术多要素联动3D可视化平台 v5.0 [EB/OL]. https://arctic-viz-dmfjpjmbr7mqqndyzgfwcm.streamlit.app/, 2025-2026.
""")

st.divider()


# =========================================================================
# 项目大事记
# =========================================================================
st.markdown("## 📅 项目发展历程")

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
        <div style="text-align:center;padding:8px 4px;">
            <div style="width:10px;height:10px;background:#1565C0;border-radius:50%;margin:0 auto 6px;"></div>
            <div style="font-size:0.65rem;color:#94a3b8;">{date}</div>
            <div style="font-size:0.78rem;font-weight:600;color:#0f172a;margin-top:2px;">{event}</div>
            <div style="font-size:0.68rem;color:#64748b;margin-top:2px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.caption("© 2025-2026 北极地缘与技术双向互动机制研究 · 大学生创新创业训练计划专项")
