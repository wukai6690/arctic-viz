"""Offline MOSAiC case: measured vessel positions beside dated official ice maps."""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.presentation import ROOT, show_chart

DATA = ROOT / 'data/analysis/mosaic'
TASKS = [
    dict(task='定位与跨设备时间对照', equipment='两套 Trimble GPS 与 iXBlue HYDRINS 导航系统',
         institution='Polarstern / AWI 航迹处理团队', output='五航段带 DOI 的 10 分钟定位表',
         evidence='已下载并逐行检查船位；提供原表行号与下载包。', source_ids=['mosaic-track-1','mosaic-track-2','mosaic-track-3','mosaic-track-4','mosaic-track-5']),
    dict(task='把船位放回同期海冰环境', equipment='AMSR2 卫星辐射计；ASI 海冰算法',
         institution='不来梅大学 IUP；AWI / Meereisportal', output='带日期、百分比图例与船位标记的官方地图',
         evidence='已保存 14 个预定日期的图组；可用数量以资料覆盖为准。未把图片转换成船旁密集度数值。', source_ids=['mosaic-ice']),
    dict(task='观测雪深、气象与浮冰位置', equipment='2019S90 雪浮标；四路声学雪深测量与 GPS',
         institution='Nicolaus 等；AWI 发布', output='PANGAEA.925319；2019-10-11—2019-10-25 的小时资料',
         evidence='已核对数据集说明；此页未下载、计算该浮标的雪深序列。', source_ids=['mosaic-snow-buoy']),
    dict(task='观测云与大气廓线', equipment='KAZR 云雷达、Polly XT 激光雷达、微波辐射计',
         institution='DOE-ARM、TROPOS 等；具体设备见综述表 B2', output='观测对象、部署位置与机构对应表；Shupe 等（2022）',
         evidence='可核对设备与分工；完整性和故障需要查各仪器数据，不能由“部署”推断全年无中断。', source_ids=['mosaic-atmosphere']),
]
PHASES = [
    ('2019-10-04','开始随选定浮冰漂流'),
    ('2020-05 中旬','离开此前观测浮冰；说明页与不同日期图例的具体日期不一致'),
    ('2020-06 中旬','返回海冰开展观测；说明页与图例的具体日期不一致'),
    ('2020-07-31','这一阶段的漂流结束'),
    ('2020-08-21','开始新的浮冰漂流'),
    ('2020-09-20','最后阶段的漂流结束'),
]


@st.cache_data(show_spinner=False)
def load_mosaic():
    manifest = json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    route = json.loads((DATA/'route_6hour.json').read_text(encoding='utf-8'))
    ice = json.loads((DATA/'ice_manifest.json').read_text(encoding='utf-8'))
    daily = list(csv.DictReader((DATA/'daily_positions.csv').open(encoding='utf-8-sig')))
    for row in daily:
        row.update(latitude=float(row['latitude']),longitude=float(row['longitude']),leg=int(row['leg']),segment=int(row['segment']),source_line=int(row['source_line']))
    sources = json.loads((ROOT/'data/reference/mosaic_sources.json').read_text(encoding='utf-8'))
    return dict(manifest=manifest,route=route,ice=ice,daily=daily,sources=sources)


def mosaic_report_data():
    """Compact factual material for the platform's report/export integration."""
    data = load_mosaic()
    return dict(manifest=data['manifest'],tasks=TASKS,sources=data['sources'],
                facts=[f"五个已发表航段含 {data['manifest']['track_rows']:,} 条真实船位记录。",
                       f"{len(data['daily'])} 天可选取同日真实船位；已有 {data['manifest']['ice_available']} 张预定日期冰情图。",
                       '特定设备、负责机构与数据产出有可追溯的公开记录。'],
                interpretation='这组材料可用于追查观测活动对设备、平台和数据安排的依赖。',
                gaps=['补给、人员轮换与设备故障尚未与全部观测数据逐一匹配。',
                      '没有评估参与准入、备份能力和合作中断的实际影响。',
                      '观测产出不构成国家关系改善或功能性安全已经实现的证据。'])


def csv_content(rows):
    if not rows:
        return b'\xef\xbb\xbf'
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    return out.getvalue().encode('utf-8-sig')


@st.cache_data(show_spinner=False,max_entries=16)
def mosaic_bundle(day):
    data=load_mosaic()
    position=next(row for row in data['daily'] if row['timestamp'][:10]==day)
    ice=next((row for row in data['ice'] if row['date']==day),None)
    raw=list(csv.DictReader((DATA/'track_10min.csv').open(encoding='utf-8-sig')))
    selected=[row for row in raw if row['timestamp'][:10]==day]
    manifest=dict(version=data['manifest']['version'],selection={'day':day},position=position,
                  ice=ice,method=data['manifest']['map_method'],limitations=data['manifest']['limitations'])
    members={'manifest.json':json.dumps(manifest,ensure_ascii=False,indent=2),
             'selected_day_positions.csv':csv_content(selected),
             'sources.json':json.dumps(data['sources'],ensure_ascii=False,indent=2),
             '阅读说明.txt':'本站选取同日最接近 12:00 的真实船位。官方冰图标题是冰情日期；其船位图例可能采用次日时刻。海冰密集度不是通航风险。\n'+data['manifest']['acknowledgements']}
    if ice and ice['status']=='available':
        members[f'ice-{day}.png']=(DATA/ice['path']).read_bytes()
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in members.items():
            entry=zipfile.ZipInfo(name,date_time=(2026,10,10,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,content)
    return out.getvalue()


def track_figure(day):
    data=load_mosaic()
    position=next(row for row in data['daily'] if row['timestamp'][:10]==day)
    cutoff=position['timestamp']
    figure=go.Figure()
    route=data['route']
    # Separate original-data gaps; never connect across a missing segment.
    segments=sorted({row['segment'] for row in route})
    for first,segment in enumerate(segments):
        rows=[row for row in route if row['segment']==segment]
        figure.add_trace(go.Scattergeo(lat=[r['latitude'] for r in rows],lon=[r['longitude'] for r in rows],
                         mode='lines',line=dict(width=1.4,color='#b9c6c0'),name='全航次参考',
                         legendgroup='whole',showlegend=first==0,hoverinfo='skip'))
        past=[r for r in rows if r['timestamp']<=cutoff]
        if position['segment']==segment and (not past or past[-1]['timestamp']!=cutoff):
            past.append(position)
        figure.add_trace(go.Scattergeo(lat=[r['latitude'] for r in past],lon=[r['longitude'] for r in past],
                         mode='lines',line=dict(width=2.5,color='#326d59'),name='截至所选时刻',
                         legendgroup='past',showlegend=first==0,
                         text=[r['timestamp'].replace('T',' ')+' UTC' for r in past],
                         hovertemplate='%{text}<br>%{lat:.4f}° N · %{lon:.4f}°<extra></extra>'))
    figure.add_trace(go.Scattergeo(lat=[69.6517,90,78.658077],lon=[18.9556,0,0.613282],
                     mode='markers+text',text=['特罗姆瑟','北极点','弗拉姆海峡'],
                     textposition=['bottom right','top center','middle left'],
                     marker=dict(size=4,color='#657b70'),textfont=dict(size=12),
                     name='地理参照',showlegend=False,
                     hovertemplate='%{text}<br>地名参考位置，不是船位或海区边界<extra></extra>'))
    figure.add_trace(go.Scattergeo(lat=[position['latitude']],lon=[position['longitude']],mode='markers',
                     marker=dict(size=11,color='#b16a34',line=dict(color='white',width=2)),name='所选真实船位',
                     text=[position['timestamp'].replace('T',' ')+' UTC'],
                     hovertemplate='%{text}<br>%{lat:.4f}° N · %{lon:.4f}°<extra></extra>'))
    figure.update_layout(height=520,margin=dict(l=0,r=0,t=10,b=65),
                         legend=dict(orientation='h',y=-0.025,yanchor='top',x=0,font=dict(size=11)),
                         geo=dict(projection=dict(type='orthographic',rotation=dict(lat=90,lon=0),scale=1.3),
                                  center=dict(lat=90,lon=0),
                                  lataxis=dict(showgrid=True,dtick=10),
                                  lonaxis=dict(showgrid=True,dtick=45),
                                  showland=True,showocean=True,showcountries=True,showframe=False))
    return figure


def render_mosaic_research(key='mosaic-case'):
    if not (DATA/'manifest.json').exists():
        st.info('MOSAiC 资料包尚未发布。')
        return
    data=load_mosaic();manifest=data['manifest'];report=mosaic_report_data()
    st.subheader('MOSAiC：一年的观测，依赖哪些条件')
    st.write('从真实船位与同期冰情出发，追查设备、机构分工和可复核的观测产出。')
    a,b,c=st.columns(3)
    a.metric('公开船位记录',f'{manifest["track_rows"]:,}')
    b.metric('有船位记录',f'{len(data["daily"])} 个日期')
    c.metric('同期冰情图',f'{manifest["ice_available"]} 个时点')
    st.caption('PANGAEA 五个 PS122 航段 · '+manifest['start'][:10]+'—'+manifest['end'][:10]+'。此案例使用独立航次范围，不跟随三海区月份筛选。')
    atlas,tasks,evidence=st.tabs(['航迹与同期冰情','设备与观测成果','证据与下载'])
    with atlas:
        mode=st.radio('日期范围',['已有同期冰图的日期','全部船位日期'],horizontal=True,key=key+'-mode')
        daily_by_day={row['timestamp'][:10]:row for row in data['daily']}
        available={row['date']:row for row in data['ice'] if row['status']=='available'}
        dates=sorted(set(available)&set(daily_by_day)) if mode.startswith('已有') else sorted(daily_by_day)
        date_key=key+'-date'
        if st.session_state.get(date_key) not in dates:
            st.session_state[date_key]='2019-10-15' if '2019-10-15' in dates else dates[0]
        day=st.select_slider('选择观测日期',options=dates,key=date_key)
        position=daily_by_day[day]
        st.caption(f'实测船位：{position["timestamp"].replace("T"," ")} UTC · {position["latitude"]:.4f}° N，{position["longitude"]:.4f}° · 航段 PS122/{position["leg"]}')
        left,right=st.columns([1,1],gap='large')
        with left:
            st.markdown('**船在哪里**')
            show_chart(track_figure(day),key=key+'-track')
            st.caption('灰线为全航次参考，包含所选日之后的资料。绿线截止到选定船位时刻。线由真实点抽稀绘制，含航行与随冰漂流。')
        with right:
            st.markdown('**同一天的海冰环境**')
            if day in available:
                ice=available[day]
                st.image(str(DATA/ice['path']),width='stretch')
                st.caption('海冰密集度（%）· AMSR2 / ASI · 6.25 km 网格。来源：Meereisportal / Alfred-Wegener-Institut / 不来梅大学 IUP。')
            else:
                st.info('该日有真实船位，尚未保存同日冰情图。切换到“已有同期冰图的日期”可查看已核对图组。')
        st.caption('冰图标题为冰情日期；图内船位标记的时间以原图图例为准，有时为次日。两侧船位不强行当作同一时刻。灰色无数据区域不等于无冰；海冰密集度不能直接换成航行风险。')
        with st.expander('阅读日期、阶段和图例'):
            st.write('本站预先选取航次首尾日与中间每月 15 日，比较同一产品、同一图幅的季节背景。未从图片读取数值或推算冰厚。')
            st.dataframe(pd.DataFrame(PHASES,columns=['日期','官方地图说明中的阶段节点']),hide_index=True,width='stretch')
            st.caption('阶段来源：Meereisportal “Description of maps”与原图图例。5 月离开浮冰分别出现 16/17 日，6 月返回分别出现 17/19 日，尚未用航次日志裁决，故保留中旬精度。节点不用于推断设备是否连续运行。')
    with tasks:
        st.markdown('**从装备名称，走到实际产出**')
        st.dataframe(pd.DataFrame([{'任务':r['task'],'设备':r['equipment'],'负责机构 / 团队':r['institution'],'可核对产出':r['output'],'本站资料状态':r['evidence']} for r in TASKS]),hide_index=True,width='stretch',height=400)
        from src.source_library import source_button
        lookup={row['id']:row for row in data['sources']}
        for i,task in enumerate(TASKS):
            with st.expander(task['task'],expanded=i==0):
                st.write('设备：'+task['equipment'])
                st.write('机构与团队：'+task['institution'])
                st.write('可核对产出：'+task['output'])
                st.caption(task['evidence'])
                for sid in task['source_ids']:
                    source_button(lookup[sid]['url'],'阅读依据 · '+lookup[sid]['title'],key=key+f'-task-{i}-{sid}')
        photos=json.loads((ROOT/'data/reference/project_media.json').read_text(encoding='utf-8')).get('mosaic',[])
        if photos:
            columns=st.columns(min(2,len(photos)))
            for column,photo in zip(columns,photos[:2]):
                path=ROOT/photo['src'].removeprefix('/app/')
                with column:
                    st.image(str(path),caption=photo['caption'],width='stretch')
                    st.caption(f'{photo["author"]} · {photo["license"]}。项目实景是场景说明，不代替对应日期的观测记录。')
        st.write('这张表使“合作支持科研”成为可追查的问题：某项任务由什么设备支持，由谁负责，最后留下了什么资料。要继续判断观测中断或备份能力，还需要任务日志。')
    with evidence:
        st.markdown('**事实**')
        for fact in report['facts']:st.write('• '+fact)
        st.markdown('**研究解释**');st.write(report['interpretation'])
        st.markdown('**仍需验证**')
        for gap in report['gaps']:st.write('• '+gap)
        st.markdown('**资料来源 · 站内阅读**')
        source_lookup={source['id']:source for source in data['sources']}
        source_id=st.selectbox('选择来源',list(source_lookup),format_func=lambda sid:source_lookup[sid]['title'],key=key+'-source')
        source=source_lookup[source_id]
        with st.container(border=True):
            st.markdown('**'+source['title']+'**')
            for paragraph in source['summary']:st.write(paragraph)
            st.caption(source['publisher']+' · 核对 '+source['retrieved_at']+' · '+source['locator'])
            if source.get('citation'):st.caption(source['citation'])
            with st.expander('原始地址与资料条件'):
                st.code(source['url'],language=None)
                st.write(source['notice'])
        st.download_button('下载当前日期证据包 · ZIP',mosaic_bundle(day),f'mosaic-{day}.zip','application/zip',key=key+'-bundle',on_click='ignore')
        st.download_button('下载完整 10 分钟船位 · CSV',(DATA/'track_10min.csv').read_bytes(),'mosaic-track-10min.csv','text/csv',key=key+'-track-csv',on_click='ignore')
        with st.expander('处理方法、覆盖与原始文件'):
            st.write(manifest['map_method'])
            st.write(manifest['ice_selection_rule'])
            st.write('UTC 船载导航时间；本地时区不改变观测日期。原数据采用 WGS84 经纬度。')
            st.write('特罗姆瑟使用本站地点目录的城市中心，北极点为 90°N；弗拉姆海峡标签采用 Marine Regions / SeaVoX 的参考点（78.658077°N，0.613282°E）。地名标签不表示实测船位、设施位置或海区边界。')
            st.caption(f'缺失整日：{len(manifest["missing_days"])}；原始相邻船位间隔超过 1 小时：{len(manifest["gaps_over_one_hour"])} 段。')
            if manifest['gaps_over_one_hour']:st.dataframe(pd.DataFrame(manifest['gaps_over_one_hour']),hide_index=True,width='stretch')
            for i,file in enumerate(manifest['tracks']):
                st.download_button(f'原始 PANGAEA 航段 {i+1} · TSV',(DATA/file['path']).read_bytes(),f'mosaic-leg{i+1}.tab','text/tab-separated-values',key=key+f'-raw-{i}',on_click='ignore')
                st.caption(f'CC BY 4.0 · {file["citation"]}')
            st.download_button('下载版本、哈希与方法 · JSON',(DATA/'manifest.json').read_bytes(),'mosaic-manifest.json','application/json',key=key+'-manifest',on_click='ignore')
            st.caption(manifest['acknowledgements'])
