"""Place atlas with sourced project links, photographs and geographic filters."""
import json
from html import escape
from pathlib import Path
import folium
import streamlit as st
from branca.element import MacroElement,Template
from streamlit_folium import st_folium
from src.presentation import section_title,show_chart
from src.evidence_views import place_catalog,reference_data,photo_figure,photo_grid,create_local_map,finish_local_map
from src.research_catalog import research_catalog,place_category,place_region,projects_for_place,open_project,valid_events
from src.source_library import source_button,source_href
from src.place_profiles import render_profile,photo_topic,place_articles

COLORS={'港口与航道':'#508491','科研观测':'#5b8266','空间设施':'#897aa1','城市与聚落':'#ab8861','自然区域':'#809584','关联产业':'#a96b5f'}
THEMES={
    '全部地点': {'projects':None,'note':'点击地名，阅读地点、实景与相关项目。'},
    '科研协作': {'projects':['xuelong2','mosaic','awipev','chars'],'note':'从科考船建造、出航港口与研究设施，查看已整理科研项目的地理联系。'},
    '通信设施': {'projects':['kinuvik','asbm'],'note':'显示已有资料关联的卫星接收站。ASBM 是轨道卫星项目，尚未建立经过核对的地面站关联。'},
    '能源运输': {'projects':['yamal'],'note':'从萨别塔进入亚马尔 LNG 案例。港口位置与项目关系不等于实际航迹。'},
    '社区与生活': {'projects':None,'category':'城市与聚落','note':'从社区与聚落阅读当地环境和生活；地点类型不代表已核验的项目联系。'},
}

def apply_atlas_editorial():
    st.markdown('<style>'+Path(__file__).with_name('atlas_editorial.css').read_text(encoding='utf-8')+'</style>',unsafe_allow_html=True)

def themed_places(places,projects,theme):
    """Project themes use catalogued place joins, never inferred route endpoints."""
    setting=THEMES[theme]
    if setting.get('category'):
        return [p for p in places if place_category(p)==setting['category']]
    if setting['projects'] is None:return list(places)
    ids={pid for project in projects if project['id'] in setting['projects'] for pid in project['place_ids']}
    return [p for p in places if p['id'] in ids]

def change_theme():
    st.session_state.pop('atlas_focus',None)
    reset_map()

def reset_map():
    st.session_state['atlas_map_epoch']=st.session_state.get('atlas_map_epoch',0)+1
    st.session_state.pop('atlas_last_click',None)

def focus_selected():
    reset_map();st.session_state['atlas_focus']=st.session_state.get('atlas_choice')

def restore_overview():
    st.session_state.pop('atlas_focus',None)
    reset_map()

def map_label_layout(m,markers):
    helper=MacroElement()
    helper.markers=markers
    helper._template=Template('''{% macro script(this, kwargs) %}
    (function(){
      const map={{this._parent.get_name()}};
      const markers=[{% for marker in this.markers %}{{marker.get_name()}}{% if not loop.last %},{% endif %}{% endfor %}];
      function labels(){
        const occupied=[];
        markers.forEach(function(marker){
          const tip=marker.getTooltip();if(tip)tip.update();const el=tip&&tip.getElement();if(!el)return;
          el.style.visibility='visible';const rect=el.getBoundingClientRect();
          if(map.getZoom()<6 && occupied.some(r=>!(rect.right+4<r.left||rect.left-4>r.right||rect.bottom+3<r.top||rect.top-3>r.bottom)))el.style.visibility='hidden';
          else occupied.push(rect);
        });
      }
      map.on('moveend zoomend resize',()=>setTimeout(labels,80));
      [100,500,1500,3000].forEach(delay=>setTimeout(labels,delay));
      let scheduled=false;
      const observer=new ResizeObserver(()=>{if(!scheduled){scheduled=true;requestAnimationFrame(()=>{scheduled=false;labels();});}});
      markers.forEach(marker=>{const el=marker.getTooltip().getElement();if(el)observer.observe(el);});
      observer.observe(map.getContainer());
      window.addEventListener('unload',()=>observer.disconnect(),{once:true});
      markers.forEach(marker=>{marker.on('mouseover',()=>{const e=marker.getTooltip().getElement();if(e)e.style.visibility='visible';});marker.on('mouseout',labels);});
    })();
    {% endmacro %}''')
    helper.add_to(m)

def render_atlas():
    apply_atlas_editorial()
    catalog=place_catalog();places=catalog['places'];by_id={p['id']:p for p in places}
    research=research_catalog();sources={s['id']:s for s in research['sources']}
    st.markdown('<header class="atlas-editorial-heading"><small>ARCTIC ATLAS</small><h1>北极地图</h1><p>沿着地点认识北极，再从项目追溯关系与依据。</p></header>',unsafe_allow_html=True)
    from src.study_scope import scope,scope_label,open_study
    study=scope();active=st.session_state.get('_study_active',False);scope_token=(active,study['region'])
    pending=st.session_state.pop('_atlas_pending_place',None)
    returning='atlas_choice' not in st.session_state and 'atlas_search' not in st.session_state
    if not st.session_state.get('atlas_initialized') or returning:
        requested=st.query_params.get('place')
        scope_changed=st.session_state.get('_atlas_scope_token') not in [None,scope_token]
        if not scope_changed or requested!=st.session_state.get('_atlas_selected_place'):
            pending=pending or requested
        if not pending and st.session_state.get('_atlas_scope_token')==scope_token:
            pending=st.session_state.get('_atlas_selected_place')
        st.session_state['atlas_initialized']=True
    if pending in by_id:
        st.session_state['atlas_choice']=pending
        st.session_state['atlas_region']='全部地区';st.session_state['atlas_kind']='全部类型';st.session_state['atlas_search']=''
        st.session_state['atlas-theme']='全部地点'
        st.session_state['atlas_focus']=pending;reset_map()
    from src.study_data import ASSOCIATIONS,region_geometry
    if st.session_state.get('_atlas_scope_token')!=scope_token:
        st.session_state['_atlas_scope_token']=scope_token
        st.session_state['atlas-study-filter']=active and study['region']!='all';reset_map()
    study_ids=set(ASSOCIATIONS.get(study['region'],[]))
    if pending and pending not in study_ids:st.session_state['atlas-study-filter']=False
    if active:st.caption('当前研究范围：'+scope_label()+'。地点关联表示沿岸或服务联系，不等于位于海区内部。')
    with st.container(key='atlas-toolbar'):
        c1,c2,c3=st.columns([1.7,1,1],vertical_alignment='bottom')
        query=c1.text_input('查找地点',placeholder='中文名、英文名或区域',key='atlas_search',on_change=reset_map).strip().casefold()
        theme=c2.selectbox('研究主题',list(THEMES),key='atlas-theme',on_change=change_theme)
        with c3.popover('筛选与图层',width='stretch'):
            region=st.selectbox('地区',['全部地区',*sorted(set(place_region(p) for p in places))],key='atlas_region',on_change=reset_map)
            category=st.selectbox('地点类型',['全部类型',*COLORS],key='atlas_kind',on_change=reset_map)
            base=st.selectbox('底图',['浅色地理','街道地图'],key='atlas_base',on_change=reset_map)
            relation=st.checkbox('显示项目联系',value=True,key='atlas_relations',on_change=reset_map)
            overlay=st.checkbox('显示研究海区边界',value=active,key='atlas-study-overlay',on_change=reset_map)
            linked_only=st.checkbox('仅显示当前海区关联地点',key='atlas-study-filter',disabled=study['region']=='all',on_change=reset_map)
            if st.button('打开海区观测与对照',key='atlas-open-study'):open_study()
    filtered=[p for p in themed_places(places,research['projects'],theme) if (not linked_only or study['region']=='all' or p['id'] in study_ids) and (region=='全部地区' or place_region(p)==region) and (category=='全部类型' or place_category(p)==category) and query in (p['name']+' '+p['english']+' '+place_region(p)).casefold()]
    filters=[v for v in [region if region!='全部地区' else '',category if category!='全部类型' else '', '当前海区关联' if linked_only and study['region']!='all' else ''] if v]
    st.caption(f'显示 {len(filtered)} / {len(places)} 个地点'+(' · '+' · '.join(filters) if filters else '')+' ｜ '+THEMES[theme]['note'])
    if not filtered:
        st.info('没有符合条件的地点，请调整地区、类型或搜索词。');return
    ids=[p['id'] for p in filtered]
    if st.session_state.get('atlas_choice') not in ids:
        previous=st.session_state.get('_atlas_selected_place')
        st.session_state['atlas_choice']=previous if previous in ids else ('nyalesund' if 'nyalesund' in ids else ids[0])
    selection=st.session_state['atlas_choice']
    st.session_state['_atlas_selected_place']=selection
    place=by_id[selection];st.query_params['place']=selection
    map_col,detail=st.columns([2.3,1],gap='large')
    with map_col:
        from src.map_geometry import geometry_near_longitude,near_longitude
        focus=by_id.get(st.session_state.get('atlas_focus'))
        if focus and focus['id'] not in ids:focus=None
        center=[focus['latitude'],focus['longitude']] if focus else [68,0]
        def position(p):return [p['latitude'],near_longitude(p['longitude'],center[1]) if abs(center[1])>120 else p['longitude']]
        zoom=4 if focus else 1.5
        m=create_local_map(center,zoom)
        if base=='街道地图':
            for child in m._children.values():
                if isinstance(child,folium.GeoJson):child.show=False
                if isinstance(child,folium.TileLayer):child.show=True
        m.options.update(minZoom=1,maxZoom=17,zoomSnap=.25,zoomDelta=.5)
        if overlay:
            from src.study_views import COLORS as SEA_COLORS
            for feature in region_geometry()['features']:
                if abs(center[1])>120:feature=geometry_near_longitude(feature,center[1])
                rid=feature['properties']['id'];color=SEA_COLORS[rid]
                folium.GeoJson(feature,name=feature['properties']['name']+' · 统计海区',style_function=lambda f,c=color:dict(fillColor=c,color=c,weight=1,fillOpacity=.22),tooltip=folium.GeoJsonTooltip(fields=['name'],aliases=['NSIDC 统计海区'])).add_to(m)
        folium.PolyLine([[66.56,-180],[66.56,0],[66.56,180]],color='#7f9bb3',weight=1,dash_array='5,8',tooltip='北极圈 · 约 66.56°N').add_to(m)
        # Connections have documentary meaning; they are deliberately not shipping routes.
        if relation:
            for project in research['projects']:
                if THEMES[theme]['projects'] is not None and project['id'] not in THEMES[theme]['projects']:continue
                linked=[by_id[i] for i in project['place_ids'] if i in ids]
                if len(linked)==2:
                    source=sources[project['facts'][0]['source_id']]
                    body=f'<b>{escape(project["title"])}</b><p>项目地点联系示意，不是航迹或海缆。</p><a href="{source_href(source["url"])}" target="_top">站内阅读项目资料</a>'
                    folium.PolyLine([position(p) for p in linked],color='#8a94ac',weight=2,dash_array='6,8',tooltip=project['title'],popup=folium.Popup(body,max_width=300)).add_to(m)
        markers=[]
        ordered=sorted(filtered,key=lambda p:p['id']!=selection)
        for p in ordered:
            color=COLORS[place_category(p)];selected=p['id']==selection;size=18 if selected else 12
            html=f'<span class="atlas-dot" style="display:block;width:{size}px;height:{size}px;background:{color};border:2px solid white;border-radius:50%;box-shadow:0 0 0 {3 if selected else 1}px {color}55"></span>'
            marker=folium.Marker(position(p),title=p['name'],icon=folium.DivIcon(html=html,icon_size=(size,size),icon_anchor=(size/2,size/2)),tooltip=folium.Tooltip(escape(p['name']),permanent=True,direction='top',offset=(0,-10)))
            marker.add_to(m);markers.append(marker)
        map_label_layout(m,markers)
        finish_local_map(m)
        epoch=st.session_state.get('atlas_map_epoch',0)
        result=st_folium(m,height=580,use_container_width=True,key=f'atlas-map-{epoch}',returned_objects=['last_object_clicked'])
        click=(result or {}).get('last_object_clicked')
        if click:
            token=(epoch,click.get('lat'),click.get('lng'))
            if st.session_state.get('atlas_last_click')!=token:
                st.session_state['atlas_last_click']=token
                match=next((p for p in filtered if abs(p['latitude']-click.get('lat',999))<.0001 and abs((p['longitude']-click.get('lng',999)+180)%360-180)<.0001),None)
                if match and match['id']!=selection:
                    st.session_state['_atlas_click_pending']=match['id'];st.rerun()
        st.markdown('<div class="atlas-legend">'+''.join(f'<span><i style="background:{c}"></i>{k}</span>' for k,c in COLORS.items())+'</div>',unsafe_allow_html=True)
        if overlay:st.caption('海区边界与区域海冰统计配套，来源 NSIDC Meier 2007 掩膜；不表示法律边界或可通航范围。')
        st.button('恢复北极全景',key='atlas_reset',on_click=restore_overview)
    with detail:
        st.selectbox('当前地点',ids,format_func=lambda x:by_id[x]['name']+' · '+by_id[x]['english'],key='atlas_choice',on_change=focus_selected)
        st.markdown(f'<div class="eyebrow">{escape(place_region(place))} / {escape(place_category(place))}</div>',unsafe_allow_html=True)
        st.subheader(place['name']);st.caption(place['english'])
        photo_figure(place['photos'][0]);st.write(place['description'])
        st.caption(f'{abs(place["latitude"]):.2f}°{"N" if place["latitude"]>=0 else "S"} · {abs(place["longitude"]):.2f}°{"E" if place["longitude"]>=0 else "W"} ｜地点示意位置')
        linked=projects_for_place(selection)
        if linked:
            for project in linked:
                if st.button('阅读专题 · '+project['title'],key='map-project-'+project['id'],width='stretch'):open_project(project['id'])
        else:st.caption('该地点当前作为地理背景；尚未建立可核验的项目关联。')
    st.divider()
    intro_tab,photos_tab,history_tab,evidence_tab,globe_tab=st.tabs(['认识这个地点','地点图集','时点影像','资料与事件','球面视图'])
    with intro_tab:render_profile(place)
    with history_tab:
        from src.research_extensions import render_place_history
        render_place_history(place)
    with photos_tab:
        st.subheader(place['name']+' · 实景档案')
        st.caption(place['location_note'])
        st.caption(f'收录 {len(place["photos"])} 张照片；缩略图保留完整画面，可在下方放大。')
        topics=list(dict.fromkeys(photo_topic(p) for p in place['photos']))
        topic=st.radio('按拍摄内容浏览',['全部视角',*topics],horizontal=True,key='atlas-topic-'+place['id'])
        shown=[p for p in place['photos'] if topic=='全部视角' or photo_topic(p)==topic]
        st.caption(f'当前展示 {len(shown)} / {len(place["photos"])} 张')
        photo_grid(shown,'atlas-'+place['id'])
        with st.expander('放大查看照片'):
            chosen=st.radio('照片编号',range(len(place['photos'])),format_func=lambda n:f'第 {n+1} 张',horizontal=True,key='atlas_photo-'+place['id'])
            photo_figure(place['photos'][chosen],download=True,key='atlas-large-'+place['id'])
        st.page_link('pages/9_实景图集.py',label='搜索全部地点与项目照片 ↗')
    with evidence_tab:
        st.subheader('保存在本站的地点阅读材料')
        for i,article in enumerate(place_articles(selection)):
            source_button(article['url'],'阅读背景正文 · '+article['title'],key='atlas-article-'+selection+'-'+str(i))
        source_button(place['reference_url'],'地点资料与出处',key='atlas-reference-'+selection)
        if place.get('coordinate_source'):source_button(place['coordinate_source'],'位置目录与坐标来源',key='atlas-coordinate-'+selection)
        for project in linked:
            st.markdown('**'+project['title']+'**')
            for i,f in enumerate(project['facts'][:2]):
                s=sources[f['source_id']];st.write(f['text'])
                source_button(s['url'],'阅读项目依据',key='atlas-fact-'+project['id']+'-'+str(i))
        events=valid_events(place,catalog,reference_data())
        st.markdown('#### GDELT 报道线索')
        if events:
            st.caption(f'{len(events)} 条机器记录，尚待原文核验。')
            for n,url in enumerate(dict.fromkeys(e['source_url'] for e in events if e.get('source_url')),1):source_button(url,f'查看报道记录 {n}',key='atlas-event-'+str(n))
        else:st.caption('当前采集窗口内没有已配对的报道，不代表这里没有发生相关活动。')
    with globe_tab:
        import plotly.graph_objects as go
        fig=go.Figure(go.Scattergeo(lat=[p['latitude'] for p in filtered],lon=[p['longitude'] for p in filtered],text=[p['name'] for p in filtered],mode='markers',marker=dict(size=7,color=[COLORS[place_category(p)] for p in filtered]),hovertemplate='%{text}<extra></extra>'))
        fig.update_layout(height=550,margin=dict(l=0,r=0,t=5,b=0),geo=dict(projection=dict(type='orthographic',rotation=dict(lat=65,lon=-20)),showland=True,showocean=True,showcountries=True))
        show_chart(fig,key='atlas-globe')
        st.caption('球面视图可拖动旋转。地点选择、图集与来源请使用上方地图及地点菜单。')

def prepare_map_click():
    selected=st.session_state.pop('_atlas_click_pending',None)
    if selected:st.session_state['atlas_choice']=selected
