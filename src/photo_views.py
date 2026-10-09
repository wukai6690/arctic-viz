"""Browse licensed photographs without losing their subjects or provenance."""
import json
import math
import streamlit as st
from src.evidence_views import place_catalog,photo_figure
from src.presentation import section_title
from src.research_catalog import research_catalog,project_media,place_region,open_place,open_project


def photo_records():
    records=[]
    for place in place_catalog()['places']:
        for photo in place['photos']:
            records.append({**photo,'owner_id':place['id'],'owner':place['name'],
                'kind':'地点实景','region':place_region(place),'owner_key':'place:'+place['id']})
    projects={p['id']:p for p in research_catalog()['projects']}
    for pid,photos in project_media().items():
        for photo in photos:
            records.append({**photo,'owner_id':pid,'owner':projects[pid]['title'],
                'kind':'项目影像','region':'项目现场与背景','owner_key':'project:'+pid})
    return records


def filter_photos(records,kind='全部影像',owner='all',query='',topic='全部视角'):
    words=query.casefold().split()
    return [p for p in records if (kind=='全部影像' or p['kind']==kind)
        and (owner=='all' or p['owner_key']==owner) and (topic=='全部视角' or p.get('topic','其他视角')==topic)
        and all(word in ' '.join(str(p.get(k,'')) for k in
            ['owner','caption','title','region','subject_scope','date','topic']).casefold() for word in words)]


@st.dialog('实景照片',width='large')
def enlarge_photo(photo):
    st.write('**'+photo['owner']+'**')
    photo_figure(photo,download=True,key='enlarged-'+photo['id'])
    if photo.get('subject_scope'):st.caption('拍摄对象与适用范围：'+photo['subject_scope'])


def render_photos():
    records=photo_records()
    section_title('PHOTOGRAPHIC ATLAS','实景图集','从海冰、港口和社区，到科考现场与观测设备。每张照片都能查看作者、拍摄日期与原始来源。')
    counts=st.columns(3)
    counts[0].metric('收录实景照片',f'{len(records)} 张')
    counts[1].metric('地点',f'{len(place_catalog()["places"])} 处')
    counts[2].metric('有影像资料的项目',f'{len(project_media())} 个')
    a,b=st.columns([1,2])
    kind=a.selectbox('影像类别',['全部影像','地点实景','项目影像'],key='gallery-kind')
    available=filter_photos(records,kind)
    owners=dict.fromkeys(p['owner_key'] for p in available)
    names={p['owner_key']:p['owner'] for p in available}
    if st.session_state.get('gallery-owner') not in ['all',*owners]:st.session_state['gallery-owner']='all'
    owner=b.selectbox('地点或项目',['all',*owners],format_func=lambda x:'所有地点与项目' if x=='all' else names[x],key='gallery-owner')
    a,b=st.columns([2,1])
    query=a.text_input('搜索图集',placeholder='地点、科考、天线、港口、年份…',key='gallery-query')
    topics=['全部视角',*sorted({p.get('topic','其他视角') for p in filter_photos(records,kind,owner)})]
    if st.session_state.get('gallery-topic') not in topics:st.session_state['gallery-topic']='全部视角'
    topic=b.selectbox('拍摄内容',topics,key='gallery-topic')
    chosen=filter_photos(records,kind,owner,query,topic)
    st.caption('影像按地点和拍摄内容检索，不随侧栏研究年份裁剪。历史设施与项目背景以图注为准；照片不能代替运行数据或关系证据。')
    signature=(kind,owner,query,topic)
    if st.session_state.get('_gallery-filter')!=signature:
        st.session_state['_gallery-filter']=signature;st.session_state['gallery-page']=1
    if not chosen:st.info('没有符合条件的照片，请更换关键词或筛选范围。');return
    size=12;pages=math.ceil(len(chosen)/size)
    page=st.selectbox('图集页码',list(range(1,pages+1)),format_func=lambda x:f'第 {x} / {pages} 页',key='gallery-page')
    start=(page-1)*size
    st.caption(f'找到 {len(chosen)} 张 · 本页 {start+1}—{min(start+size,len(chosen))} 张。点击“放大查看”可阅读完整画面。')
    for offset in range(start,min(start+size,len(chosen)),3):
        for col,photo in zip(st.columns(3,gap='large'),chosen[offset:min(offset+3,start+size)]):
            with col,st.container(key='photo-card-'+photo['id']):
                st.caption(photo['kind']+' · '+photo['owner'])
                photo_figure(photo)
                if st.button('放大查看',key='enlarge-'+photo['id']):enlarge_photo(photo)
                label='在地图中查看' if photo['kind']=='地点实景' else '阅读项目'
                if st.button(label,key='photo-owner-'+photo['id']):
                    if photo['kind']=='地点实景':open_place(photo['owner_id'])
                    else:open_project(photo['owner_id'])
    st.download_button('下载当前照片的来源与许可',json.dumps(chosen,ensure_ascii=False,indent=2),
        'arctic-photo-sources.json','application/json',key='gallery-download',on_click='ignore')
