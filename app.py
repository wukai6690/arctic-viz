"""
北极地缘气候多源数据可视化平台
主入口文件 - 多页面 Streamlit 应用
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="北极战略数据可视化平台",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E88E5 0%, #0D47A1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 0.5rem 0 0.3rem 0;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #546E7A;
        text-align: center;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        padding: 1.2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(30,136,229,0.25);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-card-green {
        background: linear-gradient(135deg, #43A047 0%, #2E7D32 100%);
        padding: 1.2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(67,160,71,0.25);
    }
    .metric-card-red {
        background: linear-gradient(135deg, #E53935 0%, #C62828 100%);
        padding: 1.2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(229,57,53,0.25);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .streamlit-expanderHeader {
        font-weight: 600;
    }
    section[data-testid="stSidebar"] {
        background-color: #f0f4f8;
    }
    .stSidebar > div {
        padding-top: 1rem;
    }
    /* 蓝色渐变按钮 */
    .stButton > button:first-child {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(30,136,229,0.4);
    }
    /* 页面卡片 */
    .page-card {
        border: 1px solid #e0e0e0;
        border-radius: 16px;
        padding: 1.2rem;
        margin: 0.3rem 0;
        transition: all 0.2s;
        cursor: pointer;
    }
    .page-card:hover {
        border-color: #1E88E5;
        box-shadow: 0 4px 16px rgba(30,136,229,0.15);
        transform: translateY(-2px);
    }
    /* 分割线样式 */
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🧭 导航菜单")
        st.divider()

        st.markdown("""
        **项目信息**
        - 课题：北极地缘气候多源数据可视化
        - 框架：Streamlit + Folium + Plotly
        - 数据：GDELT / NSIDC / GeoJSON
        """)
        st.divider()

        st.markdown("""
        **技术说明**

        本平台采用纯 Python 架构：
        - **前端**：Streamlit 自动渲染
        - **地图**：Folium (Leaflet.js)
        - **图表**：Plotly
        - **数据**：本地 CSV / GeoJSON

        无需编写 HTML/CSS/JS！
        """)
        st.divider()

        # 数据状态快速查看
        st.markdown("**📂 数据文件状态**")
        processed_dir = os.path.join(os.path.dirname(__file__), 'data', 'processed')
        if os.path.exists(processed_dir):
            files = os.listdir(processed_dir)
            csv_files = [f for f in files if f.endswith('.csv')]
            if csv_files:
                st.success(f"✅ {len(csv_files)} 个数据文件已就绪")
                for f in csv_files[:5]:
                    st.caption(f"  📄 {f}")
            else:
                st.warning("⚠️ 数据文件不存在，请先在「数据获取」页面生成数据")
        else:
            st.warning("⚠️ data/processed/ 目录不存在")

        st.divider()
        st.caption("© 2024 北极地缘气候研究项目")
        st.caption("大创专项 · 数据可视化平台 v2.0")


render_sidebar()

# ==================== 首页主体 ====================
st.markdown('<div class="main-header">🌍 北极地缘气候多源数据可视化平台</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '基于 <b>GDELT</b> 地缘事件数据 · <b>NSIDC</b> 海冰监测数据 · <b>三大航道</b> GeoJSON<br>'
    '聚焦「技术进步赋能地缘权力延伸」与「中国北极安全应对策略」'
    '</div>',
    unsafe_allow_html=True
)

# 顶部 KPI 指标卡
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        '<div class="metric-card">'
        '<div style="font-size:0.9rem;opacity:0.85">GDELT 事件记录</div>'
        '<div style="font-size:1.8rem;font-weight:700">38,500+</div>'
        '<div style="font-size:0.8rem;opacity:0.75">2018-2024</div>'
        '</div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<div class="metric-card-green">'
        '<div style="font-size:0.9rem;opacity:0.85">海冰年均下降</div>'
        '<div style="font-size:1.8rem;font-weight:700">-13.2%</div>'
        '<div style="font-size:0.8rem;opacity:0.75">1989-2024</div>'
        '</div>',
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        '<div class="metric-card-red">'
        '<div style="font-size:0.9rem;opacity:0.85">航道通航季延长</div>'
        '<div style="font-size:1.8rem;font-weight:700">+45天</div>'
        '<div style="font-size:0.8rem;opacity:0.75">近十年趋势</div>'
        '</div>',
        unsafe_allow_html=True
    )
with col4:
    st.markdown(
        '<div class="metric-card">'
        '<div style="font-size:0.9rem;opacity:0.85">覆盖国家/地区</div>'
        '<div style="font-size:1.8rem;font-weight:700">11</div>'
        '<div style="font-size:0.8rem;opacity:0.75">北极核心利益方</div>'
        '</div>',
        unsafe_allow_html=True
    )

st.divider()

# 核心研究问题
st.markdown("### 📌 项目核心研究问题")
cols = st.columns(3)
with cols[0]:
    st.info("""
    **🌡️ 气候驱动**
    北极海冰快速融化如何从物理层面催生新航道？
    """)
with cols[1]:
    st.info("""
    **⚔️ 技术竞争**
    高端船舶制造与极地通信卫星领域大国博弈格局如何演变？
    """)
with cols[2]:
    st.info("""
    **🇨🇳 中国路径**
    如何在规则制定、科技合作与风险防控三条路径上构建北极战略？
    """)

st.divider()
st.markdown("### 🗂️ 功能模块入口")

page_cols = st.columns(3)
pages_info = [
    ("🗺️", "北极交互地图",
     "查看三大航道轨迹、科考站分布、GDELT 事件热力图，支持时间滑块联动"),
    ("❄️", "海冰数据面板",
     "历年北极海冰面积变化趋势、季节性分析、趋势预测与航道通航关联"),
    ("📊", "GDELT 事件分析",
     "按国家、类别、情感分析北极地缘政治事件，揭示大国博弈动态"),
]

for i, (icon, title, desc) in enumerate(pages_info):
    with page_cols[i]:
        st.markdown(f"""
        <div class="page-card">
            <div style="font-size:1.6rem;margin-bottom:0.5rem">{icon}</div>
            <div style="font-weight:700;font-size:1.05rem;color:#1E88E5;margin-bottom:0.3rem">{title}</div>
            <div style="font-size:0.85rem;color:#546E7A;line-height:1.5">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

page_cols2 = st.columns(3)
pages_info2 = [
    ("🏛️", "战略叙事图文联动",
     "按时间线展示中国北极战略演进，配合地图自动切换战略解读"),
    ("📥", "GDELT 数据获取",
     "从 GDELT 官网抓取最新数据，按北极关键词过滤与聚合处理"),
    ("🗄️", "数据管理中心",
     "GDELT 1.0/2.0 清洗流水线、数据质量报告、多源数据说明"),
]

for i, (icon, title, desc) in enumerate(pages_info2):
    with page_cols2[i]:
        st.markdown(f"""
        <div class="page-card">
            <div style="font-size:1.6rem;margin-bottom:0.5rem">{icon}</div>
            <div style="font-weight:700;font-size:1.05rem;color:#1E88E5;margin-bottom:0.3rem">{title}</div>
            <div style="font-size:0.85rem;color:#546E7A;line-height:1.5">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# 数据生态图
st.markdown("### 🔗 北极多源数据生态")
st.markdown("""
本平台整合了以下数据源，构建北极研究数据闭环：

| 数据层 | 数据源 | 说明 |
|--------|--------|------|
| **事件数据** | GDELT 1.0/2.0 | 每日更新 · 覆盖全球新闻 · 情感分析 |
| **气候数据** | NSIDC 海冰指数 | 1979-2024 · 月度更新 · 趋势预测 |
| **地理数据** | GeoJSON 手工标注 | 三大航道 · 科考站分布 · 冲突事件 |
| **政策数据** | 官方白皮书/报告 | 中国/美国/俄罗斯北极政策文件 |
""")

st.divider()
st.markdown("""
### 📖 使用指南

1. **首次使用**：在终端运行 `pip install -r requirements.txt` 安装全部依赖
2. **启动平台**：运行 `streamlit run app.py`，浏览器自动打开
3. **左侧导航**：点击页面名称切换功能模块
4. **GDELT 数据**：进入「数据获取」页面生成样本数据或抓取真实数据
5. **时间滑块**：拖动地图页面的时间滑块，地图与叙事文字同步变化
""")
