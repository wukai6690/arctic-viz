"""A short review route with truthful stages rather than invented achievements."""
import streamlit as st
from src.presentation import section_title
from src.home_views import open_case

STEPS=['研究问题','真实观测','案例比较','证据边界','实际工作']
def render_tour():
    section_title('A GUIDED READING','研究导览','用五步了解研究问题、材料、案例与尚待完成的工作。可直接跳到任意一步。')
    stage=st.radio('导览步骤',range(5),format_func=lambda x:f'{x+1}. {STEPS[x]}',horizontal=True,key='tour-stage')
    st.progress((stage+1)/5,text=f'{stage+1} / 5 · {STEPS[stage]}')
    if stage==0:
        st.subheader('技术与地缘关系，怎样在具体项目中相互作用？')
        st.write('气候与海冰提供环境背景；船舶、通信和设施改变活动条件；合作安排、用户需求和制度环境又影响技术的组织与使用。我们用三个案例逐项核对，而不先给国家或地区打分。')
        for label,text in [('MOSAiC','持续观测怎样依靠装备与跨机构协作？'),('ASBM','高纬需求如何进入技术设计和客户分工？'),('亚马尔','冰级船舶如何与港口、季节和运输安排共同作用？')]:st.markdown('**'+label+'**');st.write(text)
    elif stage==1:
        st.subheader('先把位置与日期对上，再谈环境影响')
        st.write('MOSAiC 案例使用 Polarstern 真实航迹；固定日期的官方冰情图提供同日背景。选择一个日期，分别查看船在哪里、冰情图表现什么、任务记录能支持什么。')
        if st.button('打开 MOSAiC 航迹与冰情',key='tour-mosaic'):open_case('mosaic')
        st.caption('海冰密集度不等于冰厚或航行风险；区域月值也不等于船边观测。图上位置不能单独证明合作效果。')
    elif stage==2:
        st.subheader('同一套问题，阅读两个不同项目')
        for col,(cid,title,body) in zip(st.columns(2,gap='large'),[('asbm','ASBM · 从需求到使用','政府前期提案、客户协议、实际发射、交接与使用记录分开登记。覆盖目标不等于已经实测的服务质量。'),('yamal','亚马尔 · 从港口到一次运输','对照 2017–2018 年投产和运输时序。净航行时间、货次、产量和装运量分别保留单位与统计期。')]):
            with col:
                st.subheader(title);st.write(body)
                if st.button('阅读案例',key='tour-'+cid):open_case(cid)
        st.caption('两个案例中的需求、技术和制度安排各不相同；这里用于比较过程，不估计统一的因果效应。')
    elif stage==3:
        st.subheader('每个判断都要回答：依据是什么，缺口在哪里？')
        for title,body in [('事实','原始观测、机构公告与文件中的日期、任务、参与方及数值。'),('解释','多个事实的时序与关联可提出机制理解；同时列出替代解释。'),('待核验','报道候选、独立使用效果、访谈与现场材料；尚未具备的资料不写成结果。')]:st.markdown('**'+title+'**');st.write(body)
        st.page_link('pages/6_数据中心工具.py',label='查看覆盖范围、数据和方法')
        st.page_link('pages/5_中国安全风险.py',label='查看政策对照与机制证据')
    else:
        st.subheader('把网站建设与研究成果分别交代')
        st.write('目前完成的是可追溯的资料组织、地图与实景阅读、三个深入案例及研究记录入口。团队需要继续复核解释，并开展真实调研。')
        st.info('团队已确认尚未开展访谈或实地调研；记录模板与调研计划不计为成果。')
        st.page_link('pages/12_研究过程.py',label='进入研究过程与调研记录')
        st.caption('展示结束时可说明：我们已整理什么、能得出什么、暂时不能回答什么，以及下一步怎样验证。')
    st.divider();a,b=st.columns(2)
    def move(delta):st.session_state['tour-stage']=max(0,min(4,stage+delta))
    a.button('上一步',disabled=stage==0,on_click=move,args=(-1,),use_container_width=True)
    b.button('下一步',disabled=stage==4,on_click=move,args=(1,),use_container_width=True)
