"""
关于本项目页面
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

st.set_page_config(page_title="关于项目", page_icon="ℹ️", layout="wide")

st.markdown("""
<style>
    .page-header { background: linear-gradient(135deg, #455A64 0%, #607D8B 100%);
        padding: 1.2rem 1.5rem; border-radius: 0 0 14px 14px; margin-bottom: 1.5rem; }
    .page-header h1 { color: white; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .page-header p { color: rgba(255,255,255,0.85); font-size: 0.85rem; margin: 0.3rem 0 0 0; }
</style>
<div class="page-header">
    <h1>ℹ️ 关于本项目</h1>
    <p>项目介绍 · 研究框架 · 技术架构 · 团队信息</p>
</div>
""", unsafe_allow_html=True)

# ============ 项目介绍 ============
st.markdown("## 📋 项目介绍")

st.markdown("""
**北极地缘与技术多要素联动3D可视化平台**是基于「大北极」格局下地缘与技术双向互动机制研究开发的数据可视化系统。

本平台立足地理学、政治学与计算机科学的跨学科交叉，聚焦以下核心研究问题：

1. **气候驱动机制**：北极海冰快速融化如何从物理层面催生新航道？
2. **技术竞争格局**：大国在高端船舶制造与极地通信卫星领域的博弈如何演变？
3. **中国应对策略**：如何在规则制定、科技合作与风险防控三条路径上构建北极战略？
""")

st.divider()

# ============ 核心成果 ============
st.markdown("## 🎯 项目核心成果")

成果_cols = st.columns(3)

with 成果_cols[0]:
    st.markdown("""
    ### 💻 软件开发
    基于 **Python + Streamlit** 的北极地缘与技术互动3D动态可视化平台
    - 一键部署至 Streamlit Community Cloud
    - 集成 Plotly 专业可视化库
    - 全平台支持（桌面/移动端）
    """)

with 成果_cols[1]:
    st.markdown("""
    ### 📊 专题研究报告
    约 **2-3万字** 的深度研究报告
    - 「技术-地缘」双向互动机制
    - 大北极国家网络演化规律
    - 中国安全应对策略建议
    """)

with 成果_cols[2]:
    st.markdown("""
    ### 📄 知识产权
    - 软件著作权 **1项**
    - 学术论文 **1篇**（目标期刊发表）
    - 计算机软件著作权已申请
    """)

st.divider()

# ============ 六大模块 ============
st.markdown("## 🧭 平台六大核心模块")

modules = [
    ("🌡️", "气候时空监测", "气温、海冰密集度等要素的栅格热力图，支持时间滑块播放1980-2025年动态演变与CMIP6情景预测。"),
    ("🏛️", "地缘战略格局", "矢量展示各国军事基地、科考站与主权边界，构建大国博弈关系网络图谱，政策文本词频与情感分析。"),
    ("⚙️", "技术竞争与合作", "极地核心专利时空分布气泡图，技术合作网络图谱，「技术-地缘」双轴联动看板。"),
    ("🛡️", "安全风险评估", "航道通行、科考安全、技术壁垒、权益冲突四维风险矩阵，SWOT分析，中国应对策略推演沙盘。"),
    ("🗄️", "数据中心", "多源数据集下载，CSV上传可视化，时空查询工具，多指标对比分析。"),
    ("ℹ️", "关于项目", "项目介绍、研究框架、技术架构与团队信息。"),
]

for icon, title, desc in modules:
    st.markdown(f"""
    <div style="display:flex;gap:12px;padding:0.8rem 0;border-bottom:1px solid #f0f0f0;">
        <div style="font-size:1.8rem;flex-shrink:0;">{icon}</div>
        <div>
            <div style="font-weight:700;color:#0D47A1;">{title}</div>
            <div style="font-size:0.85rem;color:#546E7A;line-height:1.5;">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ============ 技术架构 ============
st.markdown("## 🏗️ 技术架构")

arch_cols = st.columns(3)

with arch_cols[0]:
    st.markdown("""
    **数据层**
    - GDELT 全球事件数据库
    - NSIDC 海冰监测数据
    - 各国北极政策文件
    - 专利数据库（模拟）
    - GeoJSON 地理数据
    """)

with arch_cols[1]:
    st.markdown("""
    **计算层**
    - Python 3.10+
    - Pandas 数据处理
    - NumPy 科学计算
    - 自定义聚合算法
    """)

with arch_cols[2]:
    st.markdown("""
    **展示层**
    - Streamlit Web框架
    - Plotly 交互图表
    - Folium 地图可视化
    - Streamlit Community Cloud
    """)

st.divider()

# ============ 学术框架 ============
st.markdown("## 📐 学术研究框架")

st.markdown("""
本项目突破传统地缘政治的单向分析视角，引入「技术-地缘」互动框架：

**核心假设**：极地技术进步（破冰船、通信卫星、资源开采）不仅是地缘竞争的结果，更是驱动地缘格局演变的关键动力。

**分析维度**：

| 维度 | 观察指标 | 数据来源 |
|------|---------|---------|
| 气候环境 | 海冰面积、通航窗口 | NSIDC |
| 地缘博弈 | 事件数量、情感值 | GDELT |
| 技术竞争 | 专利数量、合作网络 | 专利数据库 |
| 风险评估 | 多维风险矩阵 | 综合评估 |
""")

st.divider()

# ============ 团队 ============
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
        <div style="text-align:center;padding:1rem;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="width:50px;height:50px;background:#E3F2FD;border-radius:50%;margin:0 auto 0.5rem;display:flex;align-items:center;justify-content:center;font-size:1.5rem;">👤</div>
            <div style="font-weight:700;font-size:0.9rem;color:#0D47A1;">{role}</div>
            <div style="font-size:0.75rem;color:#546E7A;margin-top:4px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============ 引用说明 ============
st.markdown("""
**引用说明：** 本平台可作为教学和科研工具免费使用。如需在学术论文中引用，请参考以下格式：

> Wukai. 北极地缘与技术多要素联动3D可视化平台 v3.0 [EB/OL]. https://arctic-viz-dmfjpjmbr7mqqndyzgfwcm.streamlit.app/, 2025.

**联系方式：** 如有问题或建议，欢迎通过项目邮箱联系。
""")

st.divider()
st.caption("© 2025 北极地缘与技术双向互动机制研究 · 大学生创新创业训练计划专项")
