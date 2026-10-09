"""A question-led entrance with explicit research status."""
from html import escape
import streamlit as st
from src.evidence_views import place_catalog,photo_figure
from src.research_catalog import project_media

CASES={
 'mosaic':('01 / 科研协作','MOSAiC：怎样在浮冰上持续观测？','沿真实航迹，对照同期冰情，理解船舶、观测设备与国际协作的分工。'),
 'asbm':('02 / 高纬通信','ASBM：需求怎样进入技术设计？','按立项、发射、交付组织证据，区分覆盖设计与实际服务表现。'),
 'yamal':('03 / 能源运输','亚马尔：一艘船的航行说明什么？','追踪 2018 年东向运输，区分航行事实、净航行时间与全年通航能力。'),
}

def open_case(case):
    st.session_state['_case_pending']=case
    st.switch_page('pages/11_案例研究.py')

def render_home():
    left,right=st.columns([1.15,1],gap='large')
    with left:
        st.markdown('<div class="home-intro"><div class="eyebrow">地理大创 · 北极地缘与技术双向互动研究</div><h1>技术如何改变北极活动，<br>又如何受到地缘关系影响？</h1><p>以科考、通信和能源运输为切口，将环境观测、真实项目与政策材料放在同一条证据链中，讨论中国参与北极活动的条件。</p></div>',unsafe_allow_html=True)
        st.caption('阶段成果：三个深入案例与可核查资料集；机制解释仍需更多样本检验。')
        a,b=st.columns(2)
        a.page_link('pages/13_研究导览.py',label='从这里开始 · 研究导览',use_container_width=True)
        b.page_link('pages/11_案例研究.py',label='阅读三个案例',use_container_width=True)
    with right:
        photos=project_media().get('mosaic',[])
        if photos:photo_figure(photos[0])
        st.caption('从一艘科研船出发，看设备、环境与协作怎样共同支撑一次任务。照片拍摄时点以图注为准。')
    st.divider();st.subheader('已经做了什么，材料能说明什么')
    items=[('整理观测与位置','区域海冰观测、真实船舶航迹和地点档案，让讨论先有时间与空间依据。','观测可描述环境；单个海区的月值不能替代船边冰况。'),('追溯项目与关系','把任务、技术、参与方、时间节点和资料出处逐项对应。','项目材料支持具体事实；案例差异尚不构成因果估计。'),('建立研究过程记录','保留资料核验、界面修改与待验证问题，提供调研记录和整理入口。','截至 2026-10-10 尚未开展访谈或实地调研，模板不计为成果。')]
    for col,(title,body,limit) in zip(st.columns(3,gap='large'),items):
        with col:st.markdown(f'<article class="research-work"><h3>{escape(title)}</h3><p>{escape(body)}</p><small>{escape(limit)}</small></article>',unsafe_allow_html=True)
    st.subheader('三个案例，三种观察角度')
    for col,(cid,(kicker,title,desc)) in zip(st.columns(3,gap='large'),CASES.items()):
        with col:
            st.caption(kicker);st.markdown('### '+title);st.write(desc)
            if st.button('进入案例',key='home-case-'+cid,use_container_width=True):open_case(cid)
    st.divider();a,b=st.columns([1.4,1],gap='large')
    with a:
        st.subheader('目前形成的认识')
        st.write('技术带来新的活动条件，但活动能否持续，还取决于组织协作、服务安排、港口设施和制度环境。三个案例分别保留事实、解释与尚未证实的部分。')
        st.page_link('pages/5_中国安全风险.py',label='查看双向作用、政策对照与中国参与条件')
        st.caption('这是一组有边界的案例认识，尚不能推广为整个北极的普遍规律。')
    with b:
        st.subheader('继续探索')
        for label,path in [('北极地图 · 从地点查看项目与实景','pages/1_北极全景地图.py'),('实景图集 · 港口、社区与科研现场','pages/9_实景图集.py'),('研究过程 · 已完成工作与待开展调研','pages/12_研究过程.py'),('数据与方法 · 覆盖范围和原始资料','pages/6_数据中心工具.py')]:st.page_link(path,label=label)
    with st.expander('资料覆盖与研究边界'):
        st.write('研究主时窗为 2016—2025 年；案例保留必要前史。2026 年为未结束年度。三海区长期海冰观测用于环境背景，不能自动解释某个项目。')
        st.write('GDELT 已采集 2019-09-17 至 2019-09-23 的七个日档，是 MOSAiC 启航窗口的候选样本，尚非十年完整样本。机器候选、人工核验与现实事件分别处理。')
        st.write(f'地图收录 {len(place_catalog()["places"])} 个地点；实景照片保留作者、日期与许可。资料数量不替代研究创新性。')
