"""Inspectable candidate review and patent-family sample preparation."""
import json,os
from datetime import date
import pandas as pd
import streamlit as st
from src.source_library import source_button,source_table
from src.study_data import (DATA,PATENT_COLUMNS,candidates,reviews,save_review,verified_events,
    coverage_records,collection_progress,region_definitions,validate_patents,read_json)
from src.study_scope import scope

STATUS={'pending':'待核验','verified':'已核验','excluded':'已排除'}

def render_history():
    rows=candidates();coverage=coverage_records();p=collection_progress();real=verified_events()
    st.subheader('历史报道：从候选记录到现实事件')
    if st.session_state.pop('_review_saved',False):st.success('核验已追加保存，候选状态和归并结果已更新。')
    a,b,c=st.columns(3);a.metric('已采集日档',p['files']);b.metric('去重后的候选记录',len(rows));c.metric('已核验并归并的事件',len(real))
    if coverage:
        st.caption(f'GDELT 1.0 日档：{min(p["days"])}—{max(p["days"])}，共 {p["files"]} 天。以 MOSAiC 启航安排为锚点预先选取 7 日窗口；不是十年事件全样本。')
    st.caption('候选条件为地点/网址中的北极相关词，或机器地理编码在北极圈以北。地名歧义、国家级坐标、旧闻和多条编码仍需查看原文。已核验为 0 只表示核验进度。')
    explore,review,coverage_tab=st.tabs(['候选检索','原文核验与归并','采集进度'])
    with explore:
        a,b=st.columns([2,1]);query=a.text_input('检索历史报道',placeholder='地点、机构或原文网址',key='history-query').strip().casefold()
        status=b.selectbox('核验状态',['all',*STATUS],format_func=lambda x:'全部状态' if x=='all' else STATUS[x],key='history-status')
        filtered=[r for r in rows if (status=='all' or r['status']==status) and (not query or query in ' '.join(str(r.get(k,'')) for k in ['location','actor1','actor2','source_url','claim']).casefold())]
        st.caption(f'匹配 {len(filtered)} 条候选；同一新闻可能对应多个机器编码。')
        if filtered:
            frame=pd.DataFrame([{'候选编号':r['id'],'机器事件日期':r['date'],'来源日档':', '.join(r['archive_dates']),'地点编码':r['location'],'定位层级':r['geo_type'],'主体一':r['actor1'],'主体二':r['actor2'],'机器分类':r['category'],'状态':STATUS[r['status']],'报道原文':r['source_url']} for r in filtered])
            source_table(frame,'报道原文','history-sources',height=430)
            st.download_button('下载当前候选及溯源字段 · JSON',json.dumps(filtered,ensure_ascii=False,indent=2),'gdelt-candidates.json','application/json',key='history-download',on_click='ignore')
        else:st.info('没有符合检索条件的候选记录。')
        if real:
            st.markdown('#### 人工核验后的现实事件')
            st.dataframe(pd.DataFrame(real),hide_index=True,width='stretch')
            st.download_button('下载归并后的已核验事件 · JSON',json.dumps(real,ensure_ascii=False,indent=2),'reviewed-events.json','application/json',on_click='ignore')
        st.caption('机器分类与 Goldstein 值保留在下载中，不用作现实事件强度或风险分数。')
    with review:
        st.write('先打开原文，核对事情、日期、地点和参与方。多篇报道谈的是同一件事时，填写相同的“现实事件编号”。')
        review_query=st.text_input('按候选编号、地点或网址寻找待核验记录',key='review-query').strip().casefold()
        options=[r for r in rows if not review_query or any(review_query in str(r.get(k,'')).casefold() for k in ['id','location','source_url'])]
        st.caption(f'符合条件 {len(options)} 条；菜单最多展示前 100 条，请用关键词缩小范围。')
        options=options[:100];lookup={r['id']:r for r in options}
        if not options:st.info('没有找到待核验记录。')
        else:
            if st.session_state.get('review-candidate') not in lookup:st.session_state['review-candidate']=options[0]['id']
            rid=st.selectbox('选择候选记录',list(lookup),format_func=lambda i:lookup[i]['date']+' · '+lookup[i]['location']+' · '+i,key='review-candidate')
            r=lookup[rid]
            source_button(r['source_url'],'查看候选报道的本地记录',key='review-local-source')
            st.caption(f'来源 {r["dataset"]} ｜ 日档 {r["archive_date"]} ｜ 原文件行号 {r["source_line"]} ｜ 命中：'+ '、'.join(r['relevance_reasons']))
            with st.expander('机器记录与上一次核验'):st.json(r)
            local=os.environ.get('ARCTIC_ENABLE_LOCAL_REVIEW')=='1'
            if not local:st.caption('当前实例提供查阅与表格导出；核验写入由本地研究工作区启用。')
            with st.form('event-review-'+rid):
                a,b=st.columns(2)
                review_status=a.selectbox('核验结论',list(STATUS),format_func=STATUS.get,index=list(STATUS).index(r['status']))
                reviewer=b.text_input('核验人',value=r.get('reviewer',''))
                claim=st.text_input('经原文核对的事实摘要',value=r.get('claim',''))
                event_key=st.text_input('现实事件编号',value=r.get('event_key',''),placeholder='自定义稳定编号；同一事件使用同一个编号')
                a,b=st.columns(2)
                event_date=a.text_input('核验后的事件日期',value=r.get('event_date',''),placeholder='YYYY-MM-DD；不能直接照抄日档日期')
                regions={'pan_arctic':'全北极 / 不作海区归属',**{k:v['name'] for k,v in region_definitions().items()}}
                assigned=r.get('region_id','pan_arctic')
                region=b.selectbox('核验后的研究区域',list(regions),format_func=regions.get,index=list(regions).index(assigned) if assigned in regions else 0)
                evidence=st.text_input('支撑事实的原文网址',value=r.get('evidence_url',r['source_url']))
                note=st.text_area('核验说明或排除理由',value=r.get('note',''),placeholder='说明依据所在段落、地点歧义、重复关系或仍待确认的问题。')
                submitted=st.form_submit_button('保存核验记录',disabled=not local)
            if submitted:
                try:
                    save_review(rid,review_status,reviewer,note,event_key,event_date,region,evidence,claim)
                    st.session_state['_review_saved']=True;st.rerun()
                except ValueError as e:st.error(str(e))
            st.caption('保存保留核验人、时间和依据。再次标注会追加新版本；被排除或改回待核验的记录不再计入已核验事件。原始候选保留。')
    with coverage_tab:
        if coverage:st.dataframe(pd.DataFrame(coverage).rename(columns={'archive_date':'日档日期','status':'采集状态','scanned_rows':'扫描行数','candidate_rows':'候选数','quarantine_count':'隔离异常行数'}),hide_index=True,width='stretch')
        report=read_json('gdelt/last_run.json',{})
        if report:st.caption(f'最近任务：{report["start"]}—{report["end"]}；尚未完成 {report["remaining"]} 个日档。')
        st.write('采集任务支持按日期分批补齐、断点续传、文件校验和异常行隔离。每次先下载并校验，再发布候选包；页面浏览不触发大批量下载。')
        with st.expander('研究工作区的补采方法'):
            st.code('python scripts/collect_gdelt_history.py --start 2016-01-01 --end 2025-12-31 --max-files 31 --workers 2',language='text')
            st.caption('每次最多处理 31 个缺失日档，重复运行继续下一批。补齐全时窗需要较多下载量和人工核验，当前未自动启动十年全量下载。')
        st.download_button('下载采集覆盖清单 · JSON',json.dumps(coverage,ensure_ascii=False,indent=2),'gdelt-archive-coverage.json','application/json',on_click='ignore')
        source_button('https://data.gdeltproject.org/events/index.html','阅读 GDELT 采集与字段导读',key='gdelt-guide')

def render_patents():
    st.subheader('技术检索：先核对专利族，再组织时间')
    sample=pd.read_csv(DATA/'patent_sample.csv',dtype=str,keep_default_na=False)
    families,issues=validate_patents(sample)
    start,end=scope()['years'];inside=families[pd.to_datetime(families.priority_date).dt.year.between(start,end)]
    a,b,c=st.columns(3);a.metric('已核对公开文本',len(sample));b.metric('归并后专利族',len(families));c.metric(f'{start}—{end} 优先权时窗内的族',len(inside))
    st.caption('人工选取的真实技术样本，仅用于展示核对和去重方法。它们不是完整北极专利检索结果，也没有被认定为已在现有项目中部署。')
    source_table(families.rename(columns={'family_id':'专利族编号','priority_date':'最早优先权日','title':'标题','applicant':'申请人（资料记录）','technology':'技术标签','publication_count':'本样本公开文本数','source_url':'来源'}),'来源','patent-families')
    st.caption('KR20210004497A 与 KR102629446B1 只计一个专利族。US9929796B2 虽在 2018 年公开，最早优先权日在 2009 年，不能计入 2016—2025 年新增发明。')
    with st.expander('逐条查看相关性判断和公开文本'):
        source_table(sample,'source_url','patent-records')
    st.download_button('下载已核对专利样本 · CSV',sample.to_csv(index=False).encode('utf-8-sig'),'patent-sourced-sample.csv','text/csv',key='patent-sample',on_click='ignore')
    with st.expander('导入检索结果，检查并按族归并'):
        st.caption('导入只在当前会话预览，不自动替代已核对样本。每条相关性说明需要由研究者填写；程序只能检查格式、重复和日期。')
        st.download_button('下载专利整理模板 · CSV',(','.join(PATENT_COLUMNS)+'\n').encode('utf-8-sig'),'patent-review-template.csv','text/csv',on_click='ignore')
        uploaded=st.file_uploader('上传整理后的专利 CSV',type=['csv'],key='patent-upload')
        if uploaded:
            try:
                if uploaded.size>20_000_000:raise ValueError('请将文件拆分为不超过 20 MB 的批次。')
                frame=pd.read_csv(uploaded,dtype=str,keep_default_na=False);family,errors=validate_patents(frame)
                if errors:st.error('发现以下问题，未生成正式归并结果。');st.dataframe(pd.DataFrame(errors),hide_index=True,width='stretch')
                else:
                    st.success(f'{len(frame)} 个公开文本，归并为 {len(family)} 个专利族。格式检查通过，相关性仍需人工确认。')
                    st.dataframe(family,hide_index=True,width='stretch')
                    st.download_button('下载归并后的专利族 · CSV',family.to_csv(index=False).encode('utf-8-sig'),'patent-families.csv','text/csv',on_click='ignore')
            except (ValueError,UnicodeError,pd.errors.ParserError) as e:st.error('无法导入：'+str(e))
    with st.expander('扩大检索时采用的统一口径'):
        st.write('先划定技术范围：破冰船、冰区航行、极区通信与观测分别检索；“北极”一词不足以覆盖相关技术。组合关键词、分类号与人工相关性核验，保存检索平台、检索式、日期、命中数和排除理由。')
        st.write('时间按同一专利族的最早优先权日；公开号用于回溯文本，不把 A/B 文本或不同国家同族公开重复计为多项发明。族编号保留提供方命名空间，跨平台合并需要复核。申请人地址不能用作技术部署坐标。')
        st.write('扩充数据后，还需要记录近期公开滞后、申请人名称归并、合作申请及覆盖范围，才能考虑年度趋势和机构比较。')
        source_button('https://www.wipo.int/web-publications/world-intellectual-property-indicators-2024-highlights/en/patents-highlights.html','阅读专利整理口径',key='patent-guide')
