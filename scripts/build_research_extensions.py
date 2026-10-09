"""Publish manually checked research cards. No generated event counts or risk scores."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATE='2026-10-09'
sources=[]
def source(id,title,url,publisher,published,summary,locator,excerpt='',kind='研究资料导读'):
    sources.append(dict(id=id,title=title,url=url,publisher=publisher,published_at=published,retrieved_at=DATE,
        summary=[summary],locator=locator,excerpt=excerpt,kind=kind,
        notice='本站核对后的中文导读与短引文，未保存原网页全文。资料日期与适用范围分别保留。'))
source('norway-2021','挪威北极政策 · 2021 年英文摘要','https://www.regjeringen.no/en/documents/arctic_policy/id2830120/','挪威政府','2021-01-26',
       '材料同时讨论安全、国际合作、北方社区与技术发展。政府提出改善北方通信和基础设施；这些是政策方向，实施效果需要另查项目资料。','Preface；§1.3；§7 Infrastructure, transport and communications',
       'For us, foreign and domestic policy converge in the Arctic.','政策对照导读')
source('norway-2025','Norway in the North · 2025 年战略','https://www.regjeringen.no/en/documents/norway-in-the-north/id3116799/?ch=1','挪威政府','2025-09-26',
       '战略把北方社区活力与安全、应急准备联系起来，将国防、基础设施和地方发展放在同一框架下。这里按英文版发布日登记。','Introduction；five priority areas',
       'vibrant local communities where people want to live','政策对照导读')
source('norway-2025-infra','2025 年战略 · 连接社区的基础设施','https://www.regjeringen.no/en/documents/norway-in-the-north/id3116799/?ch=5','挪威政府','2025-09-26',
       '该章提出韧性通信、跨境数字通道以及运输与国防部门协作。计划措施尚不能直接等同于已形成的备用容量或可靠性。','Infrastructure to connect communities；最后一段',
       'high-quality, resilient mobile and broadband services','政策对照导读')
source('science-agreement','北极科学合作协定 · 美国北极研究委员会说明','https://www.arctic.gov/science-agreement/','US Arctic Research Commission','',
       '说明页记载：协定于 2017-05-11 签署、2018-05-23 生效，涉及缔约方科学活动中的人员、设备、研究设施与数据访问。不能据此推定中国或任何团队自动获得准入。','Science Agreement 开篇；协定适用主体与地理范围',
       'access to research infrastructure and facilities; and access to data.','政策对照导读')
source('china-policy','中国的北极政策 · 2018 年白皮书','https://english.www.gov.cn/archive/white_paper/2018/01/26/content_281476026660336.htm','国务院新闻办公室','2018-01-26',
       '白皮书阐明认识、保护、利用北极和参与治理的目标，提出科研、环保、合作及可持续利用等政策主张。它提供中国立场，不能单独证明项目绩效。','III. Policy Goals and Basic Principles；IV. China’s Policies and Positions',
       'understand, protect, develop and participate in the governance of the Arctic','政策对照导读')
source('council-2024','北极理事会逐步恢复工作组线上会议','https://arctic-council.org/news/arctic-council-advances-resumption-of-project-level-work/','Arctic Council','2024-02-28',
       '这份历史公告说明工作组线上会议逐步恢复，同时高级官员层级的外交会议仍暂停。ICC 主席在公告中强调伙伴关系及原住民有效参与。这里只描述公告时点。','公告开篇；ICC 主席表述；末两段','', '政策对照导读')
source('asbm-handover','ASBM 卫星运行控制交接','https://spacenorway.com/press-release/asbm-handover-marks-an-important-milestone/','Space Norway','2024-10-17',
       '运营方宣布两颗 ASBM 卫星完成在轨测试后的交接，运行控制转入 Space Norway。此节点表明交接，不包含逐月可用率。','ASBM handover；Norwegian control')
source('asbm-operation','ASBM 开始向挪威军方提供能力','https://spacenorway.com/news/operational-capability-in-the-high-north/','Space Norway','2024-12-16',
       '运营方称 ASBM 项目已投入运行，并记载通过卫星与海岸警卫队船舶通话的展示。供应方明确把为军方提供能力作为项目主要理由；这是运营方表述，尚非独立绩效评估。','ASBM project is operational；项目主任引语')
source('asbm-spec','ASBM 1 & 2 · 公开技术档案','https://spacenorway.com/infrastructure/satellite-fleet/asbm-1-asbm-2/','Space Norway','',
       '运营方档案列出两颗卫星的高椭圆轨道、制造商和载荷。设计寿命与轨道参数属于技术规格，不能替代用户获得服务的条件或实测效果。','Fact Sheet；Payloads')
source('mosaic-return','MOSAiC · AWI 科考回顾','https://www.awi.de/im-fokus/mosaic-expedition.html','Alfred Wegener Institute','',
       'AWI 回顾记载 MOSAiC 于 2020-10-12 在不来梅港结束；破冰船、飞机与后勤协作支持跨季节观测。该网页持续更新，本条仅记录历史结束节点。','Jubiläum；Rückblick auf die Expedition')
source('pame-shipping','PAME 公布的 2013 与 2025 年航运对照','https://www.pame.is/','PAME','',
       '首页公布 Polar Code 北极统计范围内的两年端点：独立船舶 1,298 与 1,812 艘，航行距离约 610 万与 1,190 万海里。数值来自公开汇总，并非本站取得的逐船 AIS。','What changed between 2013 and 2025?；ASSR #1 updated 2026')
source('pame-access','ASTD 数据内容与申请条件','https://www.pame.is/ourwork/arctic-shipping/astd/','PAME','',
       'ASTD 设不同访问等级，需要申请；学生属于可申请有限免费访问的类别。本站尚未申请或取得该受限数据库的逐船数据。','Three access levels；Apply for access')
source('indigenous-participation','北极理事会原住民永久参与方','https://arctic-council.org/about/permanent-participants/','Arctic Council','',
       '官方目录列出六个原住民永久参与方组织，并说明其在协商与决策中的咨询权。组织地位不能代替具体社区对具体项目的意见。','Permanent Participants；full consultation rights')
source('gibs-method','NASA GIBS 历史影像服务说明','https://nasa-gibs.github.io/gibs-api-docs/access-basics/','NASA GIBS','',
       'GIBS 提供带日期的地图影像接口。本项目固定图层、投影和区域范围保存影像，以便离线对照。影像中云、积雪、光照和轨道覆盖均会影响可见内容。','WMS；EPSG:3413；Time')
source('melia-2016','Melia、Haines 与 Hawkins：海冰与跨北极航运路线','https://doi.org/10.1002/2016GL069315','Geophysical Research Letters','2016',
       '该研究结合冰厚、船型假设、气候模式与路径算法讨论未来航运潜力。它说明航行潜力已有相关研究，也说明月度海冰总量不足以代替船型与区域条件。','Melia et al. (2016), 43, 9720–9728；§2 Calculating Shipping Routes')
source('shupe-2022','Shupe 等：MOSAiC 大气观测综述','https://doi.org/10.1525/elementa.2021.00060','Elementa: Science of the Anthropocene','2022-02-07',
       '论文整理 MOSAiC 大气观测的组织、仪器和观测案例，可用来追查平台如何支持实际科研产出。它不直接检验国家间地缘关系的变化。','Shupe et al. (2022), 10(1), 00060；摘要与观测设计')

policies=[
 dict(id='cn2018',name='中国 · 2018 北极政策',source_id='china-policy',date='2018-01-26',actor='中国',genre='政策白皮书',project_ids=['xuelong2','yamal'],
      themes={'科研合作':'提出开展科学研究与国际交流。','技术与设施':'提出增强认识北极的科研能力。','社区与环境':'强调环境保护及可持续发展。','参与条件':'表达中国参与立场；具体权利仍须核对适用规则。'},scope='中国政府政策主张，不是其他国家的准入许可。'),
 dict(id='no2021',name='挪威 · 2021 英文政策摘要',source_id='norway-2021',date='2021-01-26',actor='挪威',genre='白皮书英文摘要',project_ids=['asbm','awipev'],
      themes={'科研合作':'强调基于利益的国际合作与知识支撑。','技术与设施':'技术发展与北方通信是政策议题。','社区与环境':'把北方社区、萨米文化与发展共同讨论。','参与条件':'非北极国家参与须结合具体领域与法律框架。'},scope='英文摘要发布于 2021 年，不与 2025 年完整战略作机械词频比较。'),
 dict(id='no2025',name='挪威 · 2025 北方战略',source_id='norway-2025',extra_source_ids=['norway-2025-infra'],date='2025-09-26',actor='挪威',genre='国家战略',project_ids=['asbm','awipev'],
      themes={'科研合作':'知识服务于治理，合作对象与国家利益相联系。','技术与设施':'基础设施章节提出韧性通信与跨境数字通道。','社区与环境':'将社区活力与安全、应急准备联系起来。','参与条件':'列出政府优先事项，不证明措施均已落实。'},scope='按英文网页版本日期整理；不是对 2021 年摘要的逐条修订文本。'),
 dict(id='science2018',name='多边 · 科学合作协定说明',source_id='science-agreement',date='2018-05-23',actor='北极八国',genre='协定官方说明',project_ids=['mosaic','awipev','chars'],
      themes={'科研合作':'便利缔约方相关人员、设备与研究活动。','技术与设施':'涉及研究基础设施与数据访问。','社区与环境':'鼓励传统与地方知识参与科学活动。','参与条件':'缔约方及参与者定义需要核对；不自动适用于所有国家。'},scope='此日期为生效日；签署日为 2017-05-11。收录的是官方说明导读。'),
 dict(id='council2024',name='多边 · 2024 工作组会议安排',source_id='council-2024',date='2024-02-28',actor='北极理事会',genre='工作安排公告',project_ids=['mosaic','awipev','chars'],
      themes={'科研合作':'同意逐步恢复工作组线上会议。','技术与设施':'涉及线上会议形式，不证明设施已开放。','社区与环境':'公告包含 ICC 对有效参与的关切。','参与条件':'当时高级官员层级会议仍暂停。'},scope='2024 年历史状态；不能据此判断 2026 年全部机制运行状态。')
]

def mechanism(id,title,projects,direction,status,claim,material,institution,discourse,sequence,alternatives,missing):
    return dict(id=id,title=title,project_ids=projects,direction=direction,status=status,claim=claim,
                layers={'物质条件':material,'制度安排':institution,'各方表述':discourse},sequence=[dict(date=d,description=t,source_id=s) for d,t,s in sequence],
                alternatives=alternatives,missing=missing,source_ids=list(dict.fromkeys(s for _,_,s in sequence)))
mechanisms=[
 mechanism('kinuvik-service','Kinuvik：站点如何形成接收协作',['kinuvik'],'技术 → 活动与关系','有分工事实',
  '站点开幕材料与服务方介绍支持确认设施和配对关系；用户是否因此获得更好的服务，仍需运行资料。',
  '高纬站点及其天线、地面数据传输设施。','加拿大站点建设与 SSC 地面站服务安排分别核对。','服务方描述站点网络，不能据此推断所有客户的实际体验。',
  [('2010-08-10','加拿大公布伊努维克卫星站启用。','inuvik-opening'),('未标明日期','SSC 公开页面介绍 Esrange 与 Inuvik 协作。','kinuvik')],
  '任务轨道、服务合同和其他站点也会影响接收安排。','任务级覆盖、服务规则、接收成功率与传输记录。'),
 mechanism('asbm-demand','ASBM：用户需求进入技术项目',['asbm'],'地缘与制度 → 技术','有主体说明',
  '运营方明确将为挪威军方提供能力列为项目主要理由，可据此追查需求如何进入项目安排。',
  '高纬通信任务与卫星、载荷、地面系统共同构成服务。','政府、运营方与制造商各有角色。','运营方说明项目理由；其表述需要与采购及独立使用材料对照。',
  [('2024-08-12','发布两颗卫星成功发射消息。','asbm-launch'),('2024-10-17','宣布运行控制交接。','asbm-handover'),('2024-12-16','说明军方能力交付及项目理由。','asbm-operation')],
  '商业载荷、成本、轨道设计与产业能力也可能影响方案选择。','预算与需求形成过程、合同安排及替代方案评估。'),
 mechanism('asbm-use','ASBM：从卫星交付到通信使用',['asbm'],'技术 → 活动与关系','有使用节点',
  '发射、交接和使用公告构成不同阶段，支持判断能力逐步进入使用；尚不足以估计地缘影响。',
  '两颗高椭圆轨道卫星与配套地面系统。','运营控制交接与客户使用安排。','运营方通过通话展示说明能力投入使用。',
  [('2024-10-17','完成交接的公告。','asbm-handover'),('2024-12-16','与海岸警卫队船舶通话展示。','asbm-operation')],
  '一次展示不等于长期稳定服务；服务变化也可能来自其他通信系统。','可用率、服务条件、长期使用记录及用户独立评价。'),
 mechanism('xuelong-network','雪龙2号：技术项目中的跨机构分工',['xuelong2'],'技术 → 活动与关系','有分工事实',
  '交付材料可支持设计与建造分工的讨论。项目是否改变合作关系，仍待前后材料。',
  '设计、建造与极地任务需要不同能力。','基本设计、详细设计、建造和组织实施分工。','交付新闻对项目成果的陈述。',
  [('2019-07-11','雪龙2号交付，材料记录参与分工。','xuelong-delivery')],
  '分工可能同时受采购、既有合作与成本影响。','合作形成过程、关键部件与航次使用记录。'),
 mechanism('mosaic-platform','MOSAiC：平台与后勤支持联合观测',['mosaic'],'技术 → 活动与关系','有活动与成果',
  '启航、结束和观测论文可以连接平台、行动与科学产出；政治互信的变化还需要独立证据。',
  '破冰船、冰上观测设备与补给体系。','联合科考组织与后勤协作。','观测论文说明科研目标与实际观测内容。',
  [('2019-09-20','启航公告列明的特罗姆瑟出发安排。','mosaic-departure'),('2020-10-12','科考在不来梅港结束。','mosaic-return'),('2022-02-07','大气观测综述发表。','shupe-2022')],
  '合作也受既有科研网络、经费与研究计划推动。','任务级分工、数据共享记录及前后合作网络。'),
 mechanism('council-conditions','工作机制变化如何影响科学协作',['mosaic','awipev','chars'],'地缘与制度 → 技术','关系仍待核验',
  '工作组会议安排提供制度背景，但不能据此断言某个科研项目暂停或恢复。',
  '线上交流与现场科研使用不同基础设施。','2024 年公告区分工作组会议与外交层级会议。','ICC 强调有效参与和长期伙伴关系。',
  [('2018-05-23','科学合作协定生效。','science-agreement'),('2024-02-28','公布逐步恢复工作组线上会议的安排。','council-2024')],
  '项目自身经费、设备、天气或人员安排也会影响进度。','具体项目在相同时段的会议、人员交流与设备使用记录。'),
 mechanism('yamal-chain','亚马尔：运输条件与参与安排',['yamal'],'技术 → 活动与关系','有历史节点',
  '2017 年首批出口与当时投资安排提供共同观察点，尚不能单独区分各项条件的贡献。',
  '港口、生产设施与冰区运输的配套需求。','历史投资参与与项目组织。','参与企业发布的出口公告。',
  [('2017-12-08','参与方公布项目开始出口。','yamal-cargo')],
  '市场、合同、投资与技术条件可能共同推动项目。','同一时期的运输量、船舶使用、运营与政策变化。')
]

capabilities=[
 dict(project_id='xuelong2',need='为极地科考提供船舶平台',design='设计方列出 PC3 冰级；属于设计档案口径。',deployment='2019 年交付，基本设计、详细设计、建造与组织实施有出处。',operation='本资料集尚未整理连续航次与任务绩效。',limits='冰级不能直接换算为全年通航能力或某条航线的安全程度。',missing='任务日期、区域、仪器使用、观测成果与运行条件。',source_ids=['xuelong-design','xuelong-delivery']),
 dict(project_id='asbm',need='为高纬用户提供通信能力',design='两颗高椭圆轨道卫星；规格来自运营方公开档案。',deployment='2024 年 8 月发射，10 月公告完成运行控制交接。',operation='2024 年 12 月运营方公告记载军方能力交付与通话展示。',limits='供应方声明不能替代独立可用率、用户准入与商业服务评估。',missing='服务覆盖的时空精度、实际可用率、准入与备份条件。',source_ids=['asbm-spec','asbm-launch','asbm-handover','asbm-operation']),
 dict(project_id='kinuvik',need='支持极轨卫星的数据接收',design='SSC 公开材料介绍 Esrange 与 Inuvik 的站点协作。',deployment='加拿大 2010 年站点揭幕记录与 SSC 站点介绍分别保留。',operation='尚未获得任务级接收成功率或服务中断序列。',limits='设施介绍与站点配对不能证明某个用户已获得服务。',missing='任务协议、接收覆盖、传输延迟、访问规则与连续运行记录。',source_ids=['kinuvik','inuvik-opening']),
 dict(project_id='mosaic',need='支持跨季节的北极系统观测',design='漂流科考由船舶平台、仪器与后勤共同支持。',deployment='2019-09 启航，2020-10 结束。',operation='已有大气观测综述可用于追查观测实施与数据用途。',limits='科学产出不能直接作为政治关系改善的指标。',missing='具体参与任务、补给影响与数据共享使用记录。',source_ids=['mosaic-departure','mosaic-return','shupe-2022']),
 dict(project_id='yamal',need='组织冰区能源项目的出口运输',design='港口、生产设施与船舶运输需要配套。',deployment='以 2017 年开始出口及当时投资关系为历史截面。',operation='已核对首批出口公告，未整理连续运输量。',limits='历史股权与单次出口不代表 2026 年经营情况。',missing='逐年或逐月运输、船型、运力与历史经营资料。',source_ids=['yamal-cargo']),
 dict(project_id='awipev',need='支持定点长期观测',design='德法联合基地与新奥尔松承载机构提供不同设施支持。',deployment='联合基地介绍与承载机构目录已收录。',operation='尚未整理逐年设施使用和数据产出记录。',limits='科研设施存在不等于任何团队可自由使用。',missing='研究准入、任务申请、设备使用与数据发布规则。',source_ids=['awipev','nya-host']),
 dict(project_id='chars',need='支持加拿大北极科学与当地合作',design='科研园区包含研究与服务设施。',deployment='2019 年官方开幕资料与园区说明。',operation='开幕记录不代表完整的使用率或社区收益评估。',limits='主管部门对社区合作的说明不能替代当地意见调查。',missing='设施使用、合作成果与当地组织公开反馈。',source_ids=['chars-opening','chars-campus'])
]

activities=[
 dict(id='mosaic-start',project_id='mosaic',date='2019-09-20',event='准备公告列明的特罗姆瑟启航安排；此来源是事前公告',stage='计划节点',source_id='mosaic-departure'),
 dict(id='mosaic-end',project_id='mosaic',date='2020-10-12',event='MOSAiC 在不来梅港结束',stage='实施节点',source_id='mosaic-return'),
 dict(id='mosaic-paper',project_id='mosaic',date='2022-02-07',event='大气观测综述发表',stage='成果发表',source_id='shupe-2022'),
 dict(id='asbm-launch',project_id='asbm',date='2024-08-12',event='挪威时间的发射日期，运营方同日发布公告',stage='部署节点',source_id='asbm-launch'),
 dict(id='asbm-transfer',project_id='asbm',date='2024-10-17',event='发布运行控制交接公告；实际交接为 10 月中旬',stage='交接公告',source_id='asbm-handover'),
 dict(id='asbm-service',project_id='asbm',date='2024-12-16',event='军方能力交付及卫星通话展示',stage='使用公告',source_id='asbm-operation'),
 dict(id='xuelong-delivery',project_id='xuelong2',date='2019-07-11',event='雪龙2号交付',stage='交付节点',source_id='xuelong-delivery'),
 dict(id='yamal-export',project_id='yamal',date='2017-12-08',event='项目开始出口的公告',stage='使用公告',source_id='yamal-cargo')
]
shipping=dict(source_id='pame-shipping',geography='Polar Code 北极统计范围',periods=[2013,2025],
              note='两年端点，未采集中间年度；不属于三个试点海区的逐月统计。不与海冰曲线直接拼接作相关分析。',
              observations=[dict(year=2013,unique_ships=1298,distance_million_nm=6.1),dict(year=2025,unique_ships=1812,distance_million_nm=11.9)],
              precision='船舶为独立船舶数；航行距离为来源四舍五入到百万海里后一位小数的汇总。')

tasks=[
 dict(id='science',name='开展极地科考',project_ids=['xuelong2','mosaic','awipev'],question='船舶、设施与参与安排能否共同支持一项具体任务？',
      conditions=[['物质条件','已有项目依据','雪龙2号交付和 MOSAiC 实施节点可核对。','xuelong-delivery'],['制度安排','需按主体核对','科学合作协定涉及参与者与设施访问；不能自动推及中国团队。','science-agreement'],['实际使用','部分材料','MOSAiC 论文可追查观测内容，中国团队的具体参与需另核。','shupe-2022']],
      action='按具体航次整理人员、设备、补给、合作协议与数据成果。',missing='中国参与任务及适用安排的直接材料。'),
 dict(id='data',name='获取通信与观测数据',project_ids=['kinuvik','asbm'],question='有设备之后，谁能够在什么条件下使用服务？',
      conditions=[['物质条件','已有设施依据','站点配对与卫星运行节点已登记。','kinuvik'],['制度安排','资料不足','公开项目介绍没有完整说明中国用户的服务资格、价格及访问条件。','asbm-spec'],['服务连续性','资料不足','运行公告尚不足以给出长期可用率。','asbm-operation']],
      action='向公开服务说明追查用户、任务、覆盖、访问规则和备份条件。',missing='用户协议与任务级运行数据；不把未公开等同于不可获得。'),
 dict(id='transport',name='参与运输与能源项目',project_ids=['yamal'],question='投资参与、运输能力与运营规则能否在同一时点对应？',
      conditions=[['物质条件','有历史节点','2017 年出口公告支持确认项目进入出口阶段。','yamal-cargo'],['制度安排','仅历史截面','投资参与关系按当时材料记录，不外推到当前。','yamal-cargo'],['实际活动','资料不足','全北极航运汇总不能代替亚马尔项目运输量。','pame-shipping']],
      action='固定年份，补齐船舶、运输量、合同公开信息与适用政策。',missing='项目连续经营与运输记录。'),
 dict(id='cooperation',name='持续参与科研与治理',project_ids=['chars','awipev','mosaic'],question='参与渠道、当地意见与项目运行是否都能得到材料支持？',
      conditions=[['参与渠道','有历史安排','2024 年工作组会议安排与外交层级会议状态不同。','council-2024'],['当地参与','有组织依据','永久参与方目录说明咨询角色，不能代替具体社区授权。','indigenous-participation'],['成果反馈','待补充','需要当地组织对具体项目的公开意见与合作成果。','chars-campus']],
      action='分别记录谁参与、通过什么机制、表达什么意见、形成什么结果。',missing='具体项目的参与过程与直接反馈。')
]

perspectives=[
 dict(id='china-government',actor='中国政府',role='政策制定者',date='2018-01-26',topic='参与目标',position='白皮书提出认识、保护、利用北极和参与治理。',source_id='china-policy',locator='III. Policy Goals',limit='政府立场不代表全部企业或研究者的实际活动。'),
 dict(id='norway-government',actor='挪威政府',role='政策制定者',date='2025-09-26',topic='社区与安全',position='战略把社区活力、安全与应急准备相联系。',source_id='norway-2025',locator='Introduction',limit='政策方向尚需预算、执行和结果材料。'),
 dict(id='space-norway',actor='Space Norway',role='项目运营方',date='2024-12-16',topic='项目需求',position='运营方把向挪威军方提供能力列为 ASBM 的主要理由。',source_id='asbm-operation',locator='项目主任表述',limit='发布方具有项目利益关联；独立效果评估尚缺。'),
 dict(id='awi',actor='AWI 与 MOSAiC 研究团队',role='科研机构',date='2022-02-07',topic='科学观测',position='科考回顾和论文说明平台与跨季节观测的组织。',source_id='shupe-2022',locator='论文摘要与观测设计',limit='科研目标与成果不自动证明政治关系变化。'),
 dict(id='icc',actor='Inuit Circumpolar Council 主席',role='原住民组织',date='2024-02-28',topic='有效参与',position='在理事会公告中强调伙伴关系和原住民充分、有效参与。',source_id='council-2024',locator='Sara Olsvig 表述',limit='一位组织代表在这一时点的表述，不是全部社区对所有项目的意见。'),
 dict(id='chars-host',actor='Polar Knowledge Canada',role='科研设施主管机构',date='2019-08-21',topic='设施与地方合作',position='CHARS 开幕材料把研究设施与当地合作放在同一说明中。',source_id='chars-opening',locator='官方开幕公告',limit='这仍是主管机构材料；本站尚未收录相应社区的直接评价。')
]

scenarios=[
 dict(id='comms',name='通信条件变化',project_id='asbm',baseline='公开材料确认 ASBM 部署与使用节点；本站没有特定用户的服务协议。',
      changed='假设某项通信服务暂不可用',affected='依赖该服务的任务可能受影响；需先核对该任务是否实际使用它。',
      options=[dict(name='保留原服务并核查恢复安排',conditions='需要明确故障范围、恢复安排和业务优先级。',limits='尚无具体故障事件或恢复时长。'),dict(name='评估其他通信路径',conditions='核对覆盖、终端兼容、访问资格、容量和成本。',limits='尚无材料证明特定替代服务可直接接替。')],
      source_ids=['asbm-operation','norway-2025-infra'],missing='具体任务依赖、备份协议与切换实测。'),
 dict(id='access',name='科研参与条件变化',project_id='awipev',baseline='有基地介绍和协定说明；研究者准入须按具体主体与项目核实。',
      changed='假设现场进入条件暂时不满足',affected='现场采样可能需要调整，但不意味着所有数据分析工作停止。',
      options=[dict(name='调整任务时间或设施安排',conditions='需要承载机构确认、经费与设备条件。',limits='未核定延期成本或可用时段。'),dict(name='先使用已开放数据开展分析',conditions='需要数据许可、适合的变量及完整度。',limits='既有数据不一定能代替原定现场观测。')],
      source_ids=['awipev','science-agreement','shupe-2022'],missing='项目准入通知、任务需求和数据适用性。'),
 dict(id='shipping',name='冰区运输条件变化',project_id='yamal',baseline='有历史出口节点和全北极两年航运汇总；未建立项目级船舶与航线模型。',
      changed='假设某一航段冰情不满足指定船舶条件',affected='需重核船型、航段与运营约束，不能用全北极海冰面积判断可否通行。',
      options=[dict(name='调整航行时段与组织方式',conditions='需要局地冰情、船舶等级及专业运营评估。',limits='本站不计算安全航线或通航许可。'),dict(name='比较其他运输安排',conditions='需要合同、运力、时间与成本资料。',limits='尚无完整参数，不能给出经济性排序。')],
      source_ids=['yamal-cargo','melia-2016','pame-shipping'],missing='项目级活动、冰情与船舶性能资料。')
]
literature=[
 dict(id='route',claim='气候变化与航道潜力存在研究空白',source_ids=['melia-2016'],finding='已有研究把冰厚、船型与路径选择结合起来。',contribution='本项目可补充公开证据之间的时空对照和参与条件分析。',status='需要收窄创新表述',next='不能宣称首次研究海冰与航运关系；扩展检索不同模型与实测研究。'),
 dict(id='platform',claim='技术平台能够支持联合科学活动',source_ids=['shupe-2022','mosaic-return'],finding='已有观测论文和科考记录可支持具体任务分析。',contribution='可以追查技术角色、组织安排与产出之间的联系。',status='有文献起点',next='政治关系变化需要独立资料；不要把科研产出当作国家关系指标。'),
 dict(id='functional',claim='功能性安全可作为中国参与条件的分析框架',source_ids=['china-policy','science-agreement'],finding='政策目标与参与规则可提供概念的现实参照。',contribution='把准入、能力、连续性与参与过程转成有出处的问题表。',status='概念仍待文献检验',next='继续核对相近概念、适用边界与既有定义，尚不主张首创。'),
 dict(id='coupling',claim='技术与地缘存在双向作用',source_ids=['asbm-operation','norway-2025-infra'],finding='运营方理由与政策措施提供可追查的材料。',contribution='将方向、时序、主体表述和替代解释逐项登记。',status='机制待进一步检验',next='补充比较案例与反例；现有材料不支持复杂耦合系数或因果估计。')
]

def build():
    data=dict(version='20261009-research-extension-v1',reviewed_at=DATE,sources=sources,policies=policies,mechanisms=mechanisms,
              capabilities=capabilities,activities=activities,shipping=shipping,tasks=tasks,perspectives=perspectives,scenarios=scenarios,literature=literature)
    (ROOT/'data/reference/research_extensions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print({k:len(v) for k,v in data.items() if isinstance(v,list)})
if __name__=='__main__':build()
