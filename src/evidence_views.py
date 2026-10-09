"""Verified observations and licensed place photos inside the original app."""
from pathlib import Path
from html import escape
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.presentation import ROOT, show_chart
from src.source_library import source_button,source_table

def reference_data():
    return json.loads((ROOT/'data/reference/published.json').read_text(encoding='utf-8'))

def place_catalog():
    return json.loads((ROOT/'data/reference/places.json').read_text(encoding='utf-8'))

def photo_path(photo):
    return ROOT/'static'/'places'/Path(photo['src']).name

def photo_credit(photo):
    st.markdown(f'<div class="photo-credit"><strong>{escape(photo["caption"])}</strong><br>{escape(photo["author"])} · {escape(photo["date"])}<br>{escape(photo["license"])}</div>',unsafe_allow_html=True)
    with st.expander('照片出处与许可'):
        if photo.get('subject_scope'):st.caption(photo['subject_scope'])
        st.caption(photo.get('changes','保留来源画面。'))
        st.caption('原始照片地址');st.code(photo['source_url'],language=None,wrap_lines=True)
        st.caption('许可条款地址');st.code(photo['license_url'],language=None,wrap_lines=True)

def photo_figure(photo,download=False,key='photo'):
    st.image(str(photo_path(photo)),width='stretch')
    photo_credit(photo)
    if download:
        path=photo_path(photo)
        st.download_button('下载这张实景照片',path.read_bytes(),path.name,key=key+'-image',on_click='ignore')
        st.download_button('下载照片署名与许可',json.dumps(photo,ensure_ascii=False,indent=2),path.stem+'-credit.json','application/json',key=key+'-credit',on_click='ignore')

def photo_grid(photos,key):
    """Three columns per row; never silently drop photographs after the third."""
    for offset in range(0,len(photos),3):
        for col,photo in zip(st.columns(3,gap='large'),photos[offset:offset+3]):
            with col,st.container(key='photo-card-'+key+'-'+photo['id']):
                photo_figure(photo)

def create_local_map(location,zoom):
    import folium
    from branca.element import MacroElement, Template
    m=folium.Map(location=location,zoom_start=zoom,tiles=None,control_scale=True)
    land=json.loads((ROOT/'static/maps/land.geojson').read_text(encoding='utf-8'))
    if abs(location[1])>120:
        from src.map_geometry import geometry_near_longitude
        land=geometry_near_longitude(land,location[1])
    folium.GeoJson(land,name='浅色地理轮廓 · Natural Earth',overlay=False,show=True,
        style_function=lambda feature:{'fillColor':'#f7f7ef','color':'#b3c4b8','weight':0 if abs(location[1])>120 else .7,'fillOpacity':1},
        attribution='Natural Earth · public domain').add_to(m)
    folium.TileLayer('OpenStreetMap',name='街道地图 · OpenStreetMap',show=False).add_to(m)
    # Maps created in an inactive Streamlit tab initially have no layout size.
    # Redraw vector bounds when the tab becomes visible or the window resizes.
    resize=MacroElement()
    resize._template=Template('''{% macro script(this, kwargs) %}
    (function() {
        const map = {{ this._parent.get_name() }};
        const container = map.getContainer();
        const observer = new ResizeObserver(function() {
            if (container.clientWidth && container.clientHeight) {
                requestAnimationFrame(function() { map.invalidateSize({pan: false}); });
            }
        });
        observer.observe(container);
        window.addEventListener('unload', function() { observer.disconnect(); }, {once: true});
    })();
    {% endmacro %}''')
    resize.add_to(m)
    m.get_root().html.add_child(folium.Element('<style>.leaflet-container{background:#dfe9e9!important}.leaflet-tooltip{font-size:11px;border:1px solid #ccd9cc;background:#ffffff;box-shadow:none;color:#3d6652;border-radius:2px}</style>'))
    return m

def finish_local_map(m):
    """LayerControl must be emitted after every layer it references exists in JavaScript."""
    import folium
    for key,child in list(m._children.items()):
        if isinstance(child,folium.LayerControl):del m._children[key]
    folium.LayerControl(position='topright',collapsed=True).add_to(m)
    return m

def render_observations():
    data=reference_data()
    df=pd.DataFrame(data['sea_ice'])
    st.markdown('<span class="status-observed">NSIDC 官方观测</span>',unsafe_allow_html=True)
    st.subheader('按同一个月份，观察长期变化')
    st.caption('范围：海冰浓度达到阈值的海域总面积。面积：按海冰浓度计算的覆盖面积。两者均保留官方单位。')
    col1,col2,col3=st.columns([1,1,2])
    month=col1.selectbox('观测月份',list(range(1,13)),index=8,format_func=lambda n:f'{n} 月',key='observed_month')
    metric=col2.selectbox('观测指标',['extent','area'],format_func=lambda n:'海冰范围' if n=='extent' else '海冰面积',key='observed_metric')
    years=col3.slider('观测年份',int(df.year.min()),int(df.year.max()),(int(df.year.min()),int(df.year.max())),key='observed_years')
    selected=df[(df.month==month)&df.year.between(*years)].sort_values('year')
    valid=selected[selected[metric].notna()]
    if valid.empty:
        st.info('所选范围没有有效观测，请调整月份或年份。');return
    latest=valid.iloc[-1]
    cols=st.columns(3)
    cols[0].metric(f'{latest.date} '+('海冰范围' if metric=='extent' else '海冰面积'),f'{latest[metric]:.2f} 百万 km²')
    anomaly=latest[metric+'_anomaly']
    cols[1].metric('相对 1991–2020 同月均值',f'{anomaly:+.2f} 百万 km²' if pd.notna(anomaly) else '基准资料不足')
    cols[2].metric('本次筛选的有效观测',f'{len(valid)} 个月份')
    fig=go.Figure()
    # Reindex years so absent observations create real gaps in the line.
    series=selected.set_index('year').reindex(range(years[0],years[1]+1))
    fig.add_trace(go.Scatter(x=series.index,y=series[metric],mode='lines+markers',name='官方观测',line=dict(color='#427da9',width=2.4),marker=dict(size=5),connectgaps=False,hovertemplate='%{x} 年：%{y:.2f} 百万 km²<extra></extra>'))
    fig.add_trace(go.Scatter(x=series.index,y=series[metric+'_baseline'],mode='lines',name='1991–2020 同月均值',line=dict(color='#b39665',width=1.5,dash='dash'),connectgaps=False))
    fig.update_layout(height=420,margin=dict(t=50,b=45,l=55,r=20),xaxis_title='年份',yaxis_title='百万平方公里',yaxis=dict(rangemode='tozero'),hovermode='x unified',legend=dict(orientation='h',y=1.12))
    show_chart(fig,key='official_sea_ice')
    st.caption(f'观测覆盖 {df.date.min()}—{df.date.max()} · 缺失不补零 · 基准必须具有完整的 30 年同月观测 · 固定版本 {data["version"]}')
    with st.expander('查看观测明细与原始文件'):
        source_map={s['id']:s for s in data['sources']}
        table=selected[['date',metric,metric+'_baseline',metric+'_anomaly','source_id','source_line']].copy()
        table['原始文件']=table.source_id.map(lambda key:source_map[key]['url'])
        source_table(table.rename(columns={'date':'月份',metric:'观测值',metric+'_baseline':'同月基准',metric+'_anomaly':'相对差值','source_line':'原始行号'}),'原始文件','observation-files')
        st.download_button('下载当前观测与来源',selected.to_csv(index=False).encode('utf-8-sig'),f'nsidc-{metric}-month-{month}.csv','text/csv',key='official_ice_download',on_click='ignore')
        source_button('https://nsidc.org/data/g02135/versions/4','阅读 NSIDC 产品导读',key='observations-guide')

def render_candidate_events():
    data=reference_data()
    st.markdown('<span class="status-observed">GDELT 来源记录 · 待核验</span>',unsafe_allow_html=True)
    st.subheader('从原始报道核查事件线索')
    intervals=data.get('coverage',{}).get('event_ingestion_intervals',[])
    if intervals:st.caption('来源更新窗口（UTC）：'+ '；'.join(i['start']+' — '+i['end'] for i in intervals)+'。此窗口不代表完整历史覆盖。')
    query=st.text_input('检索已采集线索',placeholder='地点、行为体或事件编号',key='verified_events_query')
    events=[e for e in data['events'] if query.lower().strip() in ' '.join(str(e[k]) for k in ['location','actor1','actor2','gdelt_id']).lower()]
    st.caption(f'符合检索的 {len(events)} 条机器抽取记录。来源条目数不等于现实事件数。')
    if not events:st.info('没有匹配记录。');return
    source_table(pd.DataFrame([{'日期':e['date'],'地点':e['location'],'行为体一':e['actor1'],'行为体二':e['actor2'],'类型':e['category'],'状态':'已核验' if e['review_status']=='accepted' else '待核验','报道链接':e['source_url']} for e in events]),'报道链接','snapshot-sources')
    selected=st.selectbox('查看一条来源记录',events,format_func=lambda e:f'{e["gdelt_id"]} · {e["location"]}',key='verified_event_detail')
    for rule in place_catalog()['excluded_matches']:
        if selected['location']==rule['location'] and (not rule['url_contains'] or rule['url_contains'] in (selected['source_url'] or '')):st.info(rule['reason'])
    st.write(f'**{selected["actor1"]} → {selected["actor2"]}**')
    st.caption(f'事件日期 {selected["date"]} · {selected["category"]} · GDELT 原始文件第 {selected["source_line"]} 行。类别与名称尚需原文核验。')
    if selected['source_url']:source_button(selected['source_url'],'站内查看报道记录',key='snapshot-source')

def render_place_gallery():
    import folium
    from streamlit_folium import st_folium
    catalog=place_catalog();places=catalog['places']
    st.subheader('地图上的名字，现实中的北极')
    st.caption(f'{len(places)} 个地点 · {sum(len(p["photos"]) for p in places)} 张实景照片。照片用于认识地点；区域标记不是精确的事件发生坐标。')
    # The marker response selects the same gallery as the accessible dropdown.
    m=create_local_map([71,-25],2)
    label_layout={'pituffik':('right',(12,-24)),'kullorsuaq':('left',(-14,7)),'greenland':('right',(12,16)),
                  'nuuk':('left',(-14,12)),'kiruna':('right',(20,18)),'narvik':('left',(-10,-12)),
                  'rauma':('left',(-12,18)),'kola':('right',(14,-14))}
    for place in places:
        direction,offset=label_layout.get(place['id'],('top',(0,-10)))
        icon=folium.DivIcon(html='<span style="display:block;width:14px;height:14px;background:#497b6a;border:2px solid white;border-radius:50%"></span>',icon_size=(14,14),icon_anchor=(7,7))
        folium.Marker([place['latitude'],place['longitude']],icon=icon,title=place['name'],tooltip=folium.Tooltip(escape(place['name']),permanent=True,direction=direction,offset=offset)).add_to(m)
    finish_local_map(m)
    result=st_folium(m,height=400,use_container_width=True,key='original_places_map',returned_objects=['last_object_clicked'])
    click=(result or {}).get('last_object_clicked')
    if click:
        token=(click.get('lat'),click.get('lng'))
        if st.session_state.get('last_place_click')!=token:
            st.session_state['last_place_click']=token
            match=next((p for p in places if abs(p['latitude']-click.get('lat',999))<.001 and abs(p['longitude']-click.get('lng',999))<.001),None)
            if match:st.session_state['place_choice']=match['id']
    ids=[p['id'] for p in places];by_id={p['id']:p for p in places}
    selection=st.selectbox('选择实景地点',ids,format_func=lambda key:by_id[key]['name']+' · '+by_id[key]['english'],key='place_choice')
    place=by_id[selection]
    st.write(place['description'])
    st.caption(place['location_note'])
    photo_grid(place['photos'],'legacy-'+selection)
    with st.expander('放大查看照片'):
        number=st.radio('照片',range(len(place['photos'])),horizontal=True,format_func=lambda n:f'第 {n+1} 张',key='place_photo_number-'+selection)
        photo_figure(place['photos'][number])
    data=reference_data()
    def valid(e):
        return not any(e['location']==r['location'] and (not r['url_contains'] or r['url_contains'] in (e['source_url'] or '')) for r in catalog['excluded_matches'])
    events=[e for e in data['events'] if e['location'] in place['aliases'] and valid(e)]
    st.markdown('#### 关联报道线索')
    if events:
        # One link per source article, retaining how many machine records refer to it.
        urls=dict.fromkeys(e['source_url'] for e in events if e['source_url'])
        st.caption(f'{len(events)} 条来源记录，涉及 {len(urls)} 个报道链接；尚不等同于已核实事件。')
        for i,url in enumerate(urls,1):source_button(url,f'站内查看报道 {i}',key=f'legacy-source-{i}')
    else:st.caption('当前版本没有可关联的事件；该地点作为地理背景保留。')

def render_verified_downloads():
    data=reference_data()
    st.subheader('真实资料与来源清单')
    col1,col2,col3=st.columns(3)
    col1.download_button('NSIDC 海冰观测 · CSV',pd.DataFrame(data['sea_ice']).to_csv(index=False).encode('utf-8-sig'),'nsidc-observations.csv','text/csv',key='reference_ice',on_click='ignore')
    col2.download_button('GDELT 候选记录 · JSON',json.dumps({'version':data['version'],'coverage':data.get('coverage'),'events':data['events'],'sources':[s for s in data['sources'] if s['source']=='gdelt']},ensure_ascii=False,indent=2),'gdelt-candidates-with-sources.json','application/json',key='reference_events',on_click='ignore')
    col3.download_button('地点照片来源 · JSON',json.dumps(place_catalog(),ensure_ascii=False,indent=2),'place-photo-sources.json','application/json',key='reference_photos',on_click='ignore')
    st.caption(f'观测与候选记录版本：{data["version"]}。照片清单、地点与项目资料有各自的核对日期。')
