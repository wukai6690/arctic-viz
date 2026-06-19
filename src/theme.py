"""
共享深色主题CSS辅助函数
各页面统一调用此函数获取深色主题样式
"""


def get_dark_theme_css():
    """返回完整的深色沉浸主题 CSS（适用于所有页面）"""
    return """
<style>
    :root {
        --bg: #0a0e1a;
        --bg2: #111827;
        --card: #1a2236;
        --card2: #1f2a42;
        --border: rgba(255,255,255,0.07);
        --text: rgba(255,255,255,0.92);
        --text2: rgba(255,255,255,0.6);
        --text3: rgba(255,255,255,0.35);
    }
    .stApp > header { background: transparent !important; }
    section[data-testid="stMain"] { background: var(--bg) !important; }
    section[data-testid="stMain"] > div { background: transparent !important; }
    [data-testid="stMainBlockContainer"] { background: transparent !important; padding-top: 0 !important; }
    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e1a, #111827, #1a2236) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }
    /* 全局文字 */
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] li,
    section[data-testid="stMain"] td,
    section[data-testid="stMain"] th { color: var(--text) !important; }
    .stMarkdown p, .stMarkdown li { color: var(--text2) !important; }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: transparent !important; gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important; padding: 8px 18px !important;
        font-weight: 600 !important; font-size: 0.85rem !important;
        color: var(--text2) !important; background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.06) !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(59,130,246,0.2) !important; color: #93c5fd !important;
    }
    /* Streamlit 组件深色覆盖 */
    [data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: 0.8rem !important; }
    [data-testid="stCaption"] { color: var(--text3) !important; }
    .stCheckbox label { color: var(--text2) !important; }
    [data-baseweb="select"] > div { color: var(--text) !important; }
    .stSelectbox [data-baseweb="select"] > div { color: var(--text) !important; }
    .stMultiSelect [data-baseweb="select"] > div { color: var(--text) !important; }
    [data-testid="stSlider"] label { color: var(--text2) !important; }
    .stNumberInput label { color: var(--text2) !important; }
    .stNumberInput input { color: var(--text) !important; }
    hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.2rem 0 !important; }
    .streamlit-expander {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    .streamlit-expander summary { color: var(--text) !important; font-weight: 600 !important; }
    .stAlert { border-radius: 12px !important; }
    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid var(--border) !important;
    }
    /* DataFrame 深色 */
    [data-testid="stDataFrame"] { background: var(--card) !important; border-radius: 12px !important; }
    /* 滚动条 */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }
</style>
"""
