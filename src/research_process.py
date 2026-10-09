"""Public evidence trail and private, append-only fieldwork preparation."""
import hashlib,json,os,re
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import streamlit as st
from src.presentation import ROOT,section_title
PRIVATE=ROOT/'data/private/fieldwork.jsonl'
KINDS=['访谈','实地观察','资料核验','用户试用']
STATES=['计划','已完成']
CONSENT=['尚未征求','仅限团队内部整理','允许匿名引用','允许署名引用','不允许记录或引用']
FIELDS=['id','kind','status','activity_date','question','participant_code','place','summary','evidence_reference','consent','limits','change_basis']

def template():return {k:({'kind':'访谈','status':'计划','consent':'尚未征求'}.get(k,'')) for k in FIELDS}

def validate_record(record):
    if not isinstance(record,dict):raise ValueError('每条记录须为一个对象。')
    if set(record)-set(FIELDS):raise ValueError('记录包含模板以外的字段，请先移除。')
    r={k:record.get(k,'') for k in FIELDS}
    if any(not isinstance(v,str) for v in r.values()):raise ValueError('模板中的字段均须为文字。')
    r={k:v.strip() for k,v in r.items()}
    if any(len(v)>10000 for v in r.values()):raise ValueError('单个字段请控制在 10000 字以内。')
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,50}',r['id']):raise ValueError('编号使用 3—50 位字母、数字、下划线或短横线。')
    if r['kind'] not in KINDS or r['status'] not in STATES or r['consent'] not in CONSENT:raise ValueError('类型、状态或引用约定不在模板选项中。')
    if not r['question']:raise ValueError('请填写这次活动要回答的研究问题。')
    if r['activity_date']:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r['activity_date']):raise ValueError('日期使用 YYYY-MM-DD。')
        try:when=date.fromisoformat(r['activity_date'])
        except ValueError:raise ValueError('日期使用 YYYY-MM-DD。') from None
        if r['status']=='已完成' and when>datetime.now(timezone(timedelta(hours=8))).date():raise ValueError('已完成活动不能使用未来日期。')
    if r['status']=='已完成' and not all(r[k] for k in ['activity_date','summary','evidence_reference','limits']):raise ValueError('已完成记录须有实际日期、摘要、材料索引与解释边界。')
    if r['status']=='已完成' and r['kind'] in ['访谈','用户试用'] and r['consent'] not in CONSENT[1:4]:raise ValueError('完成的访谈或用户试用需要先确认记录与引用约定。')
    if r['consent']=='不允许记录或引用' and any(r[k] for k in ['summary','evidence_reference','participant_code']):raise ValueError('对方不允许记录时，不保存其内容与身份索引。')
    return r

def save_record(record,path=None):
    if os.environ.get('ARCTIC_ENABLE_LOCAL_REVIEW')!='1':raise ValueError('公开网站不写入研究记录；请下载后在本地工作区整理。')
    r=validate_record(record);target=Path(path) if path else PRIVATE
    if target.suffix!='.jsonl' or not any(target.resolve().is_relative_to((ROOT/d).resolve()) for d in ['data/private','test-results']):raise ValueError('保存位置须在本项目的私有记录目录内。')
    r.update(saved_at=datetime.now(timezone.utc).isoformat(),visibility='private')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    return r

def local_records():
    if os.environ.get('ARCTIC_ENABLE_LOCAL_REVIEW')!='1' or not PRIVATE.exists():return []
    latest={}
    broken=0
    for line in PRIVATE.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try:
                row=json.loads(line)
                if not isinstance(row,dict) or not isinstance(row.get('id'),str):raise ValueError('Invalid stored record')
                latest[row['id']]=row
            except (ValueError,TypeError):broken+=1
    if broken:st.warning(f'有 {broken} 条本地记录暂时无法解析，已保留原文件；请检查这些行。其余记录仍可阅读。')
    return list(latest.values())

def artifact_register():
    entries=[('区域海冰整理','data/analysis/regional_ice.json','NSIDC 三海区月度观测及基准期字段'),('公开项目整理','data/reference/research.json','项目事实、参与关系、时间节点与出处'),('政策和机制整理','data/reference/research_extensions.json','政策对照、任务条件与证据边界'),('深入案例整理','data/reference/deep_cases.json','ASBM 与亚马尔案例的时序、解释及来源'),('MOSAiC 来源清单','data/reference/mosaic_sources.json','真实航迹与同期冰情的来源登记')]
    result=[]
    for title,rel,description in entries:
        p=ROOT/rel
        if p.exists():result.append(dict(title=title,file=rel,description=description,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    validation=ROOT/'data/analysis/mosaic/validation.json'
    if validation.exists():result.append(dict(title='MOSAiC 数据检查记录',file=str(validation.relative_to(ROOT)),description='已执行的原始船位、日期、图像与下载检查；不是访谈记录。',sha256=hashlib.sha256(validation.read_bytes()).hexdigest(),bytes=validation.stat().st_size))
    return result

def render_process():
    section_title('RESEARCH NOTEBOOK','研究过程','看得到材料怎样进入网站，也看得到哪些工作还没有开展。')
    st.info('截至 2026-10-10，团队确认尚未开展实地调研或访谈。提纲、空白模板和计划记录不计入调研成果。')
    record_tab,entry_tab,plan_tab=st.tabs(['资料与修改记录','调研记录入口','待开展的研究'])
    with record_tab:
        st.subheader('已有工作留下哪些材料')
        st.write('下方列出实际存在的整理文件；校验值用于辨认版本，不表示全部内容已由团队人工复核。资料整理和网站开发使用了工具辅助，研究解释仍需团队审阅。')
        for row in artifact_register():
            with st.expander(row['title']):
                st.write(row['description']);st.caption(row['file']);st.code(row['sha256'],language=None)
                st.download_button('下载该版本资料',(ROOT/row['file']).read_bytes(),Path(row['file']).name,'application/json',key='process-file-'+row['file'],on_click='ignore')
        from src.study_data import reviews,verified_events,collection_progress
        p=collection_progress();a,b,c=st.columns(3)
        a.metric('GDELT 已采集日档',p['files']);b.metric('候选记录的核验条目',len(reviews()));c.metric('归并后的已核验事件',len(verified_events()))
        st.caption('0 表示尚无正式核验记录，不表示没有相关事件。')
        st.page_link('pages/3_地缘战略格局.py',label='进入候选检索与原文核验')
        st.subheader('本轮修改依据 · 2026-10-10')
        for title,text in [('首屏需要说明研究','首页改为问题、已做工作、阶段认识和边界，并提供逐步导览。'),('环境与项目需要具体对应','MOSAiC 接入真实航迹与固定日期冰情；ASBM、亚马尔固定研究时窗、证据与替代解释。'),('同一主题要能相邻比较','政策对照优先呈现同一问题下的两份材料；地图收起次要筛选，图集交错呈现不同题材。'),('调研尚未开展','建立私有记录与导出入口，公开页保留零成果状态；不生成受访者、引文和实际调查日期。')]:
            st.markdown('**'+title+'**');st.write(text)
        st.download_button('下载资料版本清单 · JSON',json.dumps(artifact_register(),ensure_ascii=False,indent=2),'research-artifact-register.json','application/json',key='process-register',on_click='ignore')
    with entry_tab:render_entry()
    with plan_tab:
        st.subheader('先用小规模调研检验具体问题')
        st.write('以下均为待开展计划；邀请对象、时间和可公开范围尚未确定。')
        for title,questions in [('MOSAiC · 科研协作',['真实任务中，设备、船舶和数据共享分别解决什么问题？','公开材料没有解释的协作成本和限制是什么？']),('ASBM · 通信使用',['高纬使用者怎样判断通信服务是否满足任务？','设计覆盖、正式交付和实际体验之间还缺哪些证据？']),('亚马尔 · 运输安排',['冰级船舶之外，港口、季节、合同和接收条件如何影响一次航运？','如何区分净航行时间与完整运输周期？']),('网站试用 · 结题展示',['能否在一分钟内说出研究问题与已完成工作？','能否找到一个判断的来源，并说明它的解释边界？'])]:
            with st.expander(title):
                for q in questions:st.write('• '+q)
        st.caption('访谈形成后先核对原始材料和引用约定，再决定可用的匿名摘录。不得把拟议回答填入实际记录。')

def render_entry():
    st.write('先记录研究问题，再记录实际材料。使用参与者代号和材料编号；录音、联系方式与同意书由团队单独保管。本地记录保持私有，不会自动公开。')
    local=os.environ.get('ARCTIC_ENABLE_LOCAL_REVIEW')=='1'
    st.caption('本地整理模式：可追加保存记录。' if local else '公开阅读模式：可填写和下载；不永久保存会话中的填写内容。')
    st.download_button('下载空白记录模板 · JSON',json.dumps(template(),ensure_ascii=False,indent=2),'fieldwork-template.json','application/json',on_click='ignore')
    with st.form('fieldwork-form'):
        a,b=st.columns(2);rid=a.text_input('记录编号',placeholder='例如 interview-001');kind=b.selectbox('活动类型',KINDS)
        a,b=st.columns(2);status=a.selectbox('完成状态',STATES);when=b.text_input('计划或实际日期',placeholder='YYYY-MM-DD；计划可暂留空')
        question=st.text_area('这次活动要回答什么问题')
        a,b=st.columns(2);person=a.text_input('参与者代号或角色（选填）');place=b.text_input('地点或线上方式（选填）')
        summary=st.text_area('记录摘要',placeholder='计划阶段填准备内容；完成后写有原始材料支持的观察。')
        evidence=st.text_input('原始材料编号或受控目录索引',placeholder='仅记录索引，不上传个人资料')
        consent=st.selectbox('记录与引用约定',CONSENT)
        limits=st.text_area('材料能说明什么，还有哪些限制');change=st.text_area('据此需要修改的内容（选填）')
        submitted=st.form_submit_button('整理为可下载记录')
    if submitted:
        try:st.session_state['_fieldwork_export']=validate_record(dict(zip(FIELDS,[rid,kind,status,when,question,person,place,summary,evidence,consent,limits,change])))
        except ValueError as e:st.session_state.pop('_fieldwork_export',None);st.error(str(e))
    record=st.session_state.get('_fieldwork_export')
    if record:
        st.success('已整理为会话记录。修改表单后需再次整理，下载内容才会更新。')
        with st.expander('核对这份记录',expanded=True):st.json(record)
        st.download_button('下载这份研究记录 · JSON',json.dumps(record,ensure_ascii=False,indent=2),record['id']+'.json','application/json',key='fieldwork-download',on_click='ignore')
        if local and st.button('追加保存到本地私有记录',key='fieldwork-save'):
            try:save_record(record);st.success('已追加保存；同编号保留修订历史，未公开。')
            except ValueError as e:st.error(str(e))
    with st.expander('导入已有记录进行格式检查'):
        uploaded=st.file_uploader('选择按模板整理的 JSON',type=['json'],key='fieldwork-import')
        if uploaded:
            try:
                if uploaded.size>1_000_000:raise ValueError('请拆分为不超过 1 MB 的记录文件。')
                obj=json.loads(uploaded.getvalue());rows=obj if isinstance(obj,list) else [obj]
                if len(rows)>200:raise ValueError('每批最多检查 200 条。')
                checked=[validate_record(r) for r in rows]
                st.success(f'{len(checked)} 条格式检查通过；真实性与引用约定仍需人工复核。');st.json(checked)
                st.download_button('下载检查后的记录',json.dumps(checked,ensure_ascii=False,indent=2),'checked-fieldwork.json','application/json',on_click='ignore')
            except (ValueError,TypeError,UnicodeError) as e:st.error('无法导入：'+str(e))
    if local:
        rows=local_records()
        with st.expander(f'本地私有记录 · {len(rows)} 个编号'):
            if rows:
                st.json(rows);st.download_button('导出本地记录的最新版本',json.dumps([{k:r.get(k,'') for k in FIELDS} for r in rows],ensure_ascii=False,indent=2),'private-fieldwork-latest.json','application/json',on_click='ignore')
            else:st.caption('尚未保存记录。')
