# 北极观察研究平台

当前主线为原 Streamlit 项目的整理与扩充，入口仍是 `streamlit run app.py`。原网站继续使用 [Streamlit 公开地址](https://arctic-viz-dmfjpjmbr7mqqndyzgfwcm.streamlit.app/)，部署分支为 `master`。本机可运行 `启动原版优化平台.ps1`，打开 http://127.0.0.1:8501 。

## 当前展示

- **研究总览**：研究问题、资料规模和主要入口。
- **北极地图**：29 个地点、150 张地点实景；地名标签、检索与筛选、地点档案、项目跳转和球面视图。每个地点有四个方面的中文介绍、独立标明的研究问题、延伸地点、按题材筛选的图集和离线资料包。
- **实景图集**：167 张独立真实图片；按地点、项目、拍摄内容和关键词检索，分页展示、完整画面放大、返回地图或项目。照片、署名和许可可本地下载。
- **站内资料**：30 篇开放许可背景正文、项目/政策导读、原始数据与影像出处。主要资料按钮在当前页打开阅读窗口，不跳往外站；原地址保留为可复制文本。
- **区域联动**：巴伦支海、喀拉海和楚科奇海，使用与官方统计表配套的真实海区边界；固定海区、年份和月份后查看同月观测/距平曲线、机械选出的低冰年份、项目/政策/核验事件时间线及资料覆盖。海区、时窗、月份及面积/范围选择跨页面保留，可下载当前范围的复核包。
- **技术与地缘**：7 个专题、20 条有来源的项目关系；每个项目补充技术档案与双向作用材料，分别说明设计规格、部署交付、实际使用和资料缺口。
- **研究发现**：7 张机制证据卡、5 份政策的四主题对照、4 类中国参与任务、3 个假设条件比较、6 条明确署名的参与者表述，以及首批文献与研究主张对照。来源在站内阅读，当前选择可连同依据导出。
- **数据与方法**：来源目录、定位和核验口径、照片许可、CSV/JSON/GeoJSON 下载及会话内 CSV 上传制图。
- **观测与研究资料**：真实海冰观测（长期、季节、月度）、GDELT 候选报道、项目说明。

地点覆盖港口与航道节点、科研聚落、空间设施、城市和自然区域，包含北极圈以外的关联产业城市。每处至少 5 张地点照片；另有 17 张项目影像，合计 167 张不同文件的真实照片。本次新增 26 张经画面检查的照片，涵盖自然地貌、社区建筑、商店、航空导航、城市遗迹、工业设施和历史街景。船舶在香港访问时的照片放在船舶专题，不当作上海实景；Kinuvik 所配伊努维克天线只作设施背景，ASBM 合影明确摄于美国加利福尼亚。未确认拍摄地点的船内照片没有加入地点实景。

专题包括雪龙2号、MOSAiC、Kinuvik、AWIPEV、亚马尔 LNG（2017 年历史截面）、CHARS 和 ASBM（2024 年发射节点）。13 条发布方/主管部门来源支撑项目事实。关系线表示所列角色，没有人为设置强度；地理连线表示项目地点联系，不是航迹或海缆。

本轮研究扩充增加了政策、技术机制、活动及文献导读。ASBM 档案区分 2024 年发射、运行控制交接公告与军事能力交付/通话展示。区域联动的“实际活动”展示 PAME 公开的 2013/2025 航运端点与 8 条项目记录；航运统计采用 Polar Code Arctic 范围，独立于三海区观测筛选，不提供 AIS 航迹或不存在的连续年度曲线。

地图的“时点影像”整理了萨别塔、基律纳、新奥尔松共 12 张既有照片的拍摄时间与场景，支持并排阅读和下载。它们不是同机位配准影像，不用于直接测量建设量或气候趋势；本轮不增加照片总数。NASA GIBS 历史影像尝试未取得可用文件，尚未纳入展示。

## 资料边界

- `data/reference/published.json`：575 个月度 NSIDC 记录和 120 条 GDELT 候选记录，固定版本 `20261008T140617Z-4c5fac37ed`。候选记录尚未全部核验，覆盖窗口可在“数据与方法”查看。
- `data/reference/places.json`：29 个地点的名称、位置说明、来源和逐张照片许可。新增位置来自公开地理目录；城市、区域及设施坐标的精度须按定位说明使用。
- `data/reference/place_profiles.json`：29 份中文地点导读，116 个主题介绍与 29 个待检验研究问题。中文背景改写保留 Wikipedia 署名、对应版本与 CC BY-SA 许可；研究问题不冒充来源结论。
- `data/library/`：30 篇开放许可英文正文、来源版本/许可/哈希，以及本站项目与方法导读。正文提取不含原网页版式、图片和脚注链接；非开放许可项目网页仅整理已经核对的事实，未取得的新闻全文明确显示“尚未收录”。
- `data/reference/research.json`：项目事实、时间节点、20 条关系和来源，核对日期为 2026-10-09。案例为人工选取，不代表完整样本；机制解释尚未通过因果识别检验。
- `data/reference/research_extensions.json`：研究扩充固定版本 `20261009-research-extension-v1`，包括 16 条来源导读、5 份政策、7 份技术档案、7 张机制卡、8 条项目记录、4 类参与任务、6 条参与者表述、3 个假设情景及 4 项文献对照。明确保留计划、交付、使用、表述与研究解释的区别；“功能性安全”仍是待检验框架。
- `data/reference/place_history.json`：三个地点的时点影像分组，引用既有照片及其作者、许可、拍摄日期，不将照片日期当作设施竣工日期。
- `data/reference/project_media.json`：7 个项目的独立影像资料，明确科考现场、研究站、设施背景和历史活动，不把异地项目照片当作城市实景。
- `data/analysis/regional_ice.json`：NSIDC 官方区域表的 1,725 条月度记录（1978-11—2026-09；其中 6 条缺失），分别保留面积与范围、原始单元格、1991—2020 同月基准和来源哈希。
- `data/analysis/regions.geojson`：由配套 Meier 2007 海区掩膜转换的 25 km 网格边界，保持标准经度；聚焦日期变更线附近时，底图与关联地点连续显示。不是法律边界或通航范围；地图上的关联地点不作为海区内站点密度统计。
- `data/analysis/gdelt/daily/`：2019-09-17—2019-09-23 的 7 个 GDELT 1.0 日档，扫描 1,118,230 行，保留 2,017 条候选。窗口事先锚定 MOSAiC 的启航安排，未作为十年全样本，也不与先前 GDELT 2.0 快照拼接计数。原文件行号、哈希、归档日期和机器事件日期分别保留。
- `data/analysis/evidence_context.json`：7 个项目的技术作用、替代解释和进一步验证方向；5 个有原文的历史政策节点。政策不是当前状态或活动效果的替代指标。
- `data/analysis/patent_sample.csv`：3 个真实公开文本、2 个专利族的人工选取样本。按最早优先权日，只有 1 个族落入 2016—2025；不用于国家排名或部署地图。
- `static/places/`：照片缩略版本，完整显示并保留作者与许可。`static/maps/` 为本地地理底图及 Plotly 地理资源。

海冰缺失值保留为空，基准为完整的 1991—2020 同月观测。海冰总量不换算为航道通航天数。原版模拟专利、预测、风险分数和策略沙盘已退出主要展示；原页面代码保存在 `legacy_pages/20261009/` 供后续研究参考。

研究主时窗明确为 **2016—2025（10 个完整日历年）**；2026 年属于未结束年度。月份筛选用于同月海冰比较，项目和政策按所选年份区间筛选。十年冰情齐全，不代表事件、专利等资料也达到同等覆盖。斜率只描述所选窗口，不报告未经检验的因果关系、风险分数或复杂滞后模型。

## 数据整理与核验

1. 区域观测：`python scripts/publish_regional_ice.py`。先核对原始文件哈希、六张工作表的表头/单位/日期/面积关系与边界，再发布 JSON。`--refresh` 更新官方源文件，旧的已验证原始文件存入 `data/analysis/raw/versions/`。生成边界需要 `requirements-analysis.txt` 中的依赖；网站运行不需要这些地理处理库。
2. 历史事件：`python scripts/collect_gdelt_history.py --start 2016-01-01 --end 2025-12-31 --max-files 31 --workers 2`，每次最多处理 31 个缺失日档，再次运行续采。`--reprocess` 按当前规则重读已有原档。采集结果、隔离异常行和剩余日档数均保留。全时窗补齐尚未执行。
3. 原文核验：在“事件线索 → 历史案例窗口与核验 → 原文核验与归并”核对事实、日期和区域，为同一现实事件填写稳定编号。核验记录以追加方式保存在 `data/analysis/event_reviews.jsonl`；变更为排除/待核验后退出已核验事件表。测试写入隔离目录，不伪造正式核验结果。
4. 专利导入：“技术与地缘 → 技术检索与专利样本”提供 CSV 模板、必填/日期/重复检查和专利族归并。上传结果仅留在会话中，相关性仍需研究者判断。
5. 复核导出：“区域联动 → 资料覆盖与导出”打包观测、汇总、覆盖、证据节点、海区边界与来源/方法清单。空的事件表表示尚无完成核验的记录，不表示没有真实事件。

本机启动脚本仅绑定 `127.0.0.1`，并为此进程启用核验写入。默认公开部署不启用核验写入；如需多人编辑，应另接身份权限及持久存储，不能直接在公开实例启用本地核验开关。

地图默认使用本地 Natural Earth 轮廓，可切换 OpenStreetMap 街道瓦片。街道底图仍需网络；本地图层不等于街道导航服务。低缩放级别自动避让密集标签，放大或悬停可读地名。选中地点可查看全部实景并进入对应专题。

## 维护与验证

- `src/atlas_views.py`：地图与地点联动。
- `src/place_profiles.py`：地点介绍、延伸比较与离线 ZIP；包内 HTML、照片和正文可解压后离线阅读。
- `src/source_library.py`：站内阅读、来源目录、正文检索与下载；浏览时不发起外部抓取，不展示未经核验的新闻摘要。
- `src/photo_views.py`：可检索图集、分页、放大、来源清单和返回地点/专题。
- `src/research_views.py`：专题、关系来源与研究发现。
- `src/research_extensions.py` / `src/research_extension_data.py`：政策比较、机制、任务条件、参与者表述、活动、文献与影像分组；导出固定版本、当前选择和对应出处，相同输入产生相同 ZIP 字节。
- `src/support_views.py`：气候、来源、下载和上传工具。
- `src/study_data.py` / `src/study_scope.py` / `src/study_views.py`：覆盖检查、同月统计、跨页研究范围和区域证据展示。
- `src/review_views.py`：事件核验及专利族整理。
- `src/presentation.py` / `src/research.css`：导航和恢复后的米白、灰绿浅色界面；图表、地图与控件保留清楚的类别区分。
- `.streamlit/config.toml`：主题与静态文件配置，需要随代码一起部署。
- `data/editorial/research/`：在线照片检索元数据和坐标记录，搜索结果不直接发布。
- `scripts/build_atlas_additions.py`：人工选定的图片与中文图注。
- `scripts/atlas_assets.py`：搜索和发布，校验许可、文件内容与哈希。
- `scripts/expand_real_photos.py`：分开执行搜索、暂存和发布。候选及下载失败记录在 `data/editorial/photo_expansion/`；必须在 `visual_review.json` 逐张写入画面核对结论后才可发布。原始照片发布器保留后续已核验的增补照片。
- `scripts/build_research_catalog.py`：可复核的专题事实与来源定义。
- `scripts/build_research_extensions.py`：人工核对的研究扩充目录；运行后写入固定 JSON。`scripts/collect_research_images.py` 仅抓取有限数量的 NASA GIBS 候选，须另行画面核对后才可发布；需要分析环境的 `pyproj`，不参与网站运行。
- `scripts/collect_place_library.py`：采集明确选定的开放许可条目和图片候选，保留版本并对限速退避。`scripts/build_place_profiles.py` 保存中文人工导读；`scripts/enrich_place_photos.py` 经 `data/editorial/place_enrichment/review.json` 逐项画面检查后发布。`scripts/tag_photo_subjects.py` 整理已核对图注的题材标签。

检查：`python tests/atlas_data_check.py`、`python tests/legacy_app_check.py`、`python tests/research_browser_check.py`、`python tests/map_label_diagnostic.py`。浏览器检查需本机 Edge 和 Playwright。结果与图片核对图在 `test-results/research/`，页面运行记录在 `test-results/original/app-report.json`。

新增检查：`python tests/study_data_check.py` 将 3,450 个数值/缺失单元格对回官方表，并检查基准、日期变更线、日档/事件日期、词边界误匹配、专利族及核验撤销；`python tests/study_scope_check.py` 检查跨页状态及未发布月份；`python tests/study_browser_check.py` 检查真实浏览器的筛选、跨页状态、导出、导入和移动端。结果在 `test-results/study/`。

图集验收：`python tests/photo_gallery_check.py` 检查全库文件去重、检索、翻页重置、空结果与 7 个专题的照片；`python tests/photo_browser_check.py` 检查图片实际加载、放大窗口、来源下载、跨页跳转、超过三张的地点图集及手机布局。结果与桌面/移动端截图在 `test-results/photo-expansion/`。区域页面先展示同月均值、最低年份和有效观测摘要，精确表格仍可展开与导出；长段研究解释使用可换行文本。

前期独立原型与采集流程仅保留在本地 `rebuild/`，不随当前 Streamlit 网站发布。当前展示读取独立固定资料包，刷新页面不会自动采集或更新数据。原始 GDELT ZIP 不提交仓库；如需运行逐行原档复核检查，先按上文采集命令获取对应七个日档。

站内阅读验收：`python tests/local_reading_check.py` 校验 29 个地点的介绍、至少五张照片、来源哈希、30 篇正文和每个离线包，并实际切换所有地点。`python tests/local_reading_browser_check.py` 验证阅读弹窗保持地点、正文检索/下载、项目依据、图集筛选、ZIP、手机布局，以及阻断外部浏览器请求后仍可阅读的本地内容。报告与截图在 `test-results/local-reading/`。

下载按钮使用已准备好的文件，不因下载触发整页刷新。区域复核包不再嵌入生成时钟，相同资料和筛选生成相同字节，避免普通重绘改变下载地址；原始资料日期仍完整保留。`python tests/stable_export_check.py` 验证文件稳定性和指标变化后的区分。

区域复核包保存到运行时生成的 `static/exports/`，以内容哈希命名，并通过本站地址下载，避免临时媒体地址被回收。该目录不提交版本库；这里只保存本站已经公开提供的区域研究资料，上传的私人表格仍仅通过当前会话导出。

研究扩充验收：`python tests/research_extension_check.py` 检查来源与项目关联、80 种政策/主题组合、真实照片哈希、七个专题、四类任务和三个情景；`python tests/research_extension_browser_check.py` 在端口 8502 检查站内阅读、实际 ZIP/TXT/JSON 下载、图片加载与 390 px 手机布局。可通过 `ARCTIC_TEST_URL` 指定公开站点；报告在 `test-results/research-extension/`。开发预览可使用 `scripts/start_extension_preview.ps1`，与本机原站点的 8501 端口分开。
