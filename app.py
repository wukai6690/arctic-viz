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
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        padding: 0.5rem 0;
        border-bottom: 3px solid #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #546E7A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-card-green {
        background: linear-gradient(135deg, #43A047 0%, #2E7D32 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-card-red {
        background: linear-gradient(135deg, #E53935 0%, #C62828 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
    .narrative-card {
        background-color: #f8f9fa;
        border-left: 4px solid #1E88E5;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.8rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .streamlit-expanderHeader {
        font-weight: 600;
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
        st.caption("© 2024 北极地缘气候研究项目")
        st.caption("大创专项 · 数据可视化平台 v1.0")


if __name__ == "__main__":
    render_sidebar()

    st.markdown('<div class="main-header">🌍 北极地缘气候多源数据可视化平台</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">'
        '基于 GDELT 地缘事件数据 · NSIDC 海冰监测数据 · 三大航道 GeoJSON<br>'
        '聚焦「技术进步赋能地缘权力延伸」与「中国北极安全应对策略」'
        '</div>',
        unsafe_allow_html=True
    )

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
        ("1_🌍_北极地图概览.py", "🗺️", "北极交互地图",
         "查看三大航道轨迹、科考站分布、GDELT 事件热力图，支持时间滑块联动"),
        ("2_❄️_海冰数据.py", "❄️", "海冰数据面板",
         "历年北极海冰面积变化趋势、季节性分析、与航道通航能力关联"),
        ("3_📊_GDELT事件分析.py", "📊", "GDELT 事件分析",
         "按国家、类别、情感分析北极地缘政治事件，揭示大国博弈动态"),
    ]
    pages_info2 = [
        ("4_🏛️_战略叙事区.py", "🏛️", "战略叙事图文联动",
         "按时间线展示中国北极战略演进，配合地图自动切换战略解读"),
        ("5_📥_数据爬取工具.py", "📥", "GDELT 数据爬虫",
         "从 GDELT 官网抓取最新数据，按北极关键词过滤与聚合处理"),
    ]

    for i, (pg, icon, title, desc) in enumerate(pages_info):
        with page_cols[i]:
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1.2rem;margin:0.3rem 0;">
                <div style="font-size:1.5rem;margin-bottom:0.3rem">{icon}</div>
                <div style="font-weight:600;font-size:1rem;color:#1E88E5">{title}</div>
                <div style="font-size:0.85rem;color:#546E7A;margin-top:0.3rem">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    page_cols2 = st.columns(2)
    for i, (pg, icon, title, desc) in enumerate(pages_info2):
        with page_cols2[i]:
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0;border-radius:12px;padding:1.2rem;margin:0.3rem 0;">
                <div style="font-size:1.5rem;margin-bottom:0.3rem">{icon}</div>
                <div style="font-weight:600;font-size:1rem;color:#1E88E5">{title}</div>
                <div style="font-size:0.85rem;color:#546E7A;margin-top:0.3rem">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    ### 📖 使用指南

    1. **首次使用**：在终端运行 `pip install -r requirements.txt` 安装全部依赖
    2. **启动平台**：运行 `streamlit run app.py`，浏览器自动打开
    3. **左侧导航**：点击页面名称切换功能模块
    4. **GDELT 数据**：进入「数据爬取工具」页面获取最新事件数据
    5. **时间滑块**：拖动地图页面的时间滑块，地图与叙事文字同步变化
    """)
