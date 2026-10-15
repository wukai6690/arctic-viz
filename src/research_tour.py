"""A compact, evidence-first project structure page for reviewers."""
import streamlit as st
from src.presentation import section_title


def render_tour():
    section_title("项目结构", "先看研究怎么做，再看图怎么读", "这一页只保留评审需要的四个入口：问题、数据、案例和边界。每一项都能回到具体页面或原始记录。")
    tabs = st.tabs(["01 研究问题", "02 数据与方法", "03 案例证据", "04 边界与下一步"])
    with tabs[0]:
        st.subheader("我们要解释什么？")
        st.write("北极活动的条件正在变化。技术设施、船舶与通信能力怎样改变活动方式？国家关系和制度安排又怎样限制或支持这些技术？")
        st.write("网站把问题拆成三条可以核对的线：环境背景、具体项目、国家间事件关系。三条线分别保留数据口径，不用一个分数代替复杂关系。")
        st.markdown("**三个案例入口**")
        for label, path in [("MOSAiC · 科研协作与冰上观测", "pages/11_案例研究.py"), ("ASBM · 高纬通信与服务设计", "pages/11_案例研究.py"), ("亚马尔 · 港口、船舶与能源运输", "pages/11_案例研究.py")]:
            st.page_link(path, label=label)
    with tabs[1]:
        st.subheader("材料怎样变成图？")
        st.write("NSIDC 海冰记录用于环境背景；Polarstern 公开航迹用于 MOSAiC 时空核对；GDELT 事件记录用于国家互动网络。每类材料都保留日期、来源和覆盖边界。")
        st.markdown("**网络图的读法**")
        st.write("节点是北极相关国家，边是 GDELT 机器编码事件的聚合。线宽按新闻文章数，颜色按 Goldstein 均值，节点大小按事件度数。核心、半边缘、边缘颜色只用于结构比较，不等于国家实力排名。")
        st.page_link("pages/14_动态关系网络.py", label="打开动态关系网络与条件检索")
        st.page_link("pages/6_数据中心工具.py", label="查看数据覆盖、字段和下载")
    with tabs[2]:
        st.subheader("证据怎样落到具体地点？")
        st.write("地图和实景图集提供地点背景；案例页把任务、参与方、日期和照片放在同一条阅读路径中。照片保留作者、日期、许可和本地文件，事件来源在站内阅读。")
        a, b = st.columns(2)
        a.page_link("pages/1_北极全景地图.py", label="从地图查看地点")
        b.page_link("pages/9_实景图集.py", label="查看本地实景图集")
        st.caption("照片用于识别场景与设施，不作为事件已经发生或效果已经实现的单独证明。")
    with tabs[3]:
        st.subheader("哪些结论还不能提前写？")
        st.write("当前 GDELT 网络是已经整理的日档和短窗口样本，不是完整年度序列；事件类型由机器编码，不能直接当作外交关系强度。团队尚未开展访谈或实地调研，记录入口保留为下一阶段工作。")
        st.write("下一步优先补齐：按月或按季度扩展 GDELT 样本、人工核验高权重边、记录访谈和现场材料，并把修订依据写入研究过程。")
        st.page_link("pages/12_研究过程.py", label="进入研究过程与调研记录")
        st.page_link("pages/7_关于本项目.py", label="查看项目说明与贡献边界")
