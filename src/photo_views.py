"""Browse licensed photographs without losing their subjects or provenance."""
import json
import math
from html import escape
import streamlit as st
from src.evidence_views import place_catalog,photo_figure
from src.research_catalog import research_catalog,project_media,place_region,open_place,open_project
from src.atlas_views import apply_atlas_editorial

TOPIC_GUIDES={
    '设施全景':'先看设施的空间位置和周边环境，再进入项目资料核对用途与参与者。',
    '科研设施':'观察站房、天线与科考设备的不同形态；实际观测任务和运行情况需回到项目记录。',
    '交通与港口':'对照港池、船舶、机场与补给设施，理解不同交通节点的分工。照片不用于估算运量。',
    '产业现场':'从建造和生产现场认识项目的物质基础，再核对设施、技术与组织之间的关系。',
    '社区生活':'把建筑、聚落和公共空间放回当地生活环境；影像不能代替居民的意见与访谈。',
    '自然环境':'辨认海岸、冰雪和地貌。不同季节与视点的照片，不直接构成气候变化对照。',
    '历史影像':'先读拍摄日期，再看当时的设施和场景；历史照片不表示地点今天的状态。',
}

def diverse_photos(records):
    """Interleave existing subject labels; keep every record and its provenance."""
    buckets={topic:[] for topic in TOPIC_GUIDES}
    for photo in records:buckets.setdefault(photo.get('topic','其他视角'),[]).append(photo)
    result=[]
    while any(buckets.values()):
        owners=set()
        for photos in buckets.values():
            if not photos:continue
            index=next((i for i,p in enumerate(photos) if p['owner_key'] not in owners),0)
            photo=photos.pop(index);result.append(photo);owners.add(photo['owner_key'])
    return result


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
    apply_atlas_editorial()
    records=photo_records()
    st.markdown('<header class="atlas-editorial-heading"><small>PHOTOGRAPHIC ATLAS</small><h1>实景图集</h1><p>设施、作业与生活：从不同视角认识同一个北极。</p></header>',unsafe_allow_html=True)
    st.caption(f'{len(records)} 张真实影像 · {len(place_catalog()["places"])} 个地点 · {len(project_media())} 个项目。照片保留完整画面，附作者、拍摄日期与来源。')
    a,b,c,d=st.columns([1,1.65,1.7,1],gap='medium')
    kind=a.selectbox('影像类别',['全部影像','地点实景','项目影像'],key='gallery-kind')
    available=filter_photos(records,kind)
    owners=dict.fromkeys(p['owner_key'] for p in available)
    names={p['owner_key']:p['owner'] for p in available}
    if st.session_state.get('gallery-owner') not in ['all',*owners]:st.session_state['gallery-owner']='all'
    owner=b.selectbox('地点或项目',['all',*owners],format_func=lambda x:'所有地点与项目' if x=='all' else names[x],key='gallery-owner')
    query=c.text_input('搜索图集',placeholder='地点、科考、港口、年份…',key='gallery-query')
    topics=['全部视角',*sorted({p.get('topic','其他视角') for p in filter_photos(records,kind,owner)})]
    if st.session_state.get('gallery-topic') not in topics:st.session_state['gallery-topic']='全部视角'
    topic=d.selectbox('拍摄内容',topics,key='gallery-topic')
    chosen=diverse_photos(filter_photos(records,kind,owner,query,topic))
    reading=TOPIC_GUIDES.get(topic,'按设施、交通、科研、社区与环境交错阅读。选择一个地点或项目，可以把不同视角放在一起看。')
    st.markdown('<div class="gallery-reading"><strong>'+escape(topic if topic!='全部视角' else '从不同视角看')+'</strong><p>'+escape(reading)+'</p></div>',unsafe_allow_html=True)
    st.caption('影像按地点和拍摄内容检索，不随侧栏研究年份裁剪。历史设施与项目背景以图注为准；照片与运行记录、关系证据分别阅读。')
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
                st.markdown('<span class="gallery-topic-label">'+escape(photo.get('topic','其他视角'))+'</span>',unsafe_allow_html=True)
                st.caption(photo['kind']+' · '+photo['owner'])
                photo_figure(photo)
                if photo.get('subject_scope'):
                    st.markdown('<div class="gallery-view-note">'+escape(photo['subject_scope'])+'</div>',unsafe_allow_html=True)
                if st.button('放大查看',key='enlarge-'+photo['id']):enlarge_photo(photo)
                label='在地图中查看' if photo['kind']=='地点实景' else '阅读项目'
                if st.button(label,key='photo-owner-'+photo['id']):
                    if photo['kind']=='地点实景':open_place(photo['owner_id'])
                    else:open_project(photo['owner_id'])
    st.download_button('下载当前照片的来源与许可',json.dumps(chosen,ensure_ascii=False,indent=2),
        'arctic-photo-sources.json','application/json',key='gallery-download',on_click='ignore')
