# 北极地缘气候多源数据可视化平台

基于 GDELT 地缘事件数据库、NSIDC 海冰监测数据与多源 GeoJSON 标注数据，
构建北极地缘气候研究的数据可视化平台，聚焦「技术进步赋能地缘权力延伸」与「中国北极安全应对策略」。

## 快速启动

```bash
cd D:/beiji
pip install -r requirements.txt
streamlit run app.py
```

## 项目结构

```
beiji/
├── app.py                      # 主入口（首页概览 + 侧边栏）
├── pages/
│   ├── 1_🌍_北极地图概览.py      # 交互式 Folium 地图（航道/科考站/热力图）
│   ├── 2_❄️_海冰数据.py          # 海冰面积趋势 + 季节分析 + 趋势预测
│   ├── 3_📊_GDELT事件分析.py     # GDELT 年度趋势/国家对比/类别分布/情感分析
│   ├── 4_🏛️_战略叙事区.py       # 图文联动时间线 + 政策建议框架
│   ├── 5_📥_数据获取.py          # GDELT 数据抓取与北极过滤（快速模式）
│   └── 6_🗄️_数据管理中心.py     # GDELT 1.0/2.0 完整流水线 + 质量报告 + 多源数据说明
├── src/
│   ├── gdelt_fetcher.py       # GDELT 数据抓取核心模块
│   ├── ice_data.py            # NSIDC 海冰数据处理与趋势计算
│   └── narrative.py           # 战略叙事内容（1979-2024）
├── gdelt_pipeline.py          # GDELT 1.0 流式清洗 + GDELT 2.0 DOC API
├── keywords.csv               # 北极关键词表（按 group/priority 分类）
├── data/
│   ├── raw/                   # GDELT 原始 ZIP 文件缓存
│   └── processed/             # 清洗/聚合后的数据
│       ├── gdelt_arctic_by_grid.csv          # 按网格聚合的北极事件
│       ├── gdelt_arctic_by_year_country.csv  # 按年×国家聚合的事件
│       ├── ice_area_monthly.csv             # NSIDC 月度海冰面积
│       └── ice_area_summary.csv              # 年度统计摘要
└── geojson/
    ├── arctic_routes.geojson      # 三大航道（东北/西北/中央）
    ├── research_stations.geojson   # 北极科考站（修正版）
    └── conflicts.geojson           # 地缘冲突事件热力点
```

## 功能模块

### 🗺️ 北极地图概览
交互式 Folium 地图，支持：
- 三大航道轨迹（东北航道/西北航道/中央航道）
- 北极科考站分布（中国黄河站、斯瓦尔巴群岛等）
- GDELT 事件热力图（按年份过滤）
- 地缘冲突事件分类标注（技术竞争/航道/资源/军事等）
- 时间滑块与战略叙事文字联动

### ❄️ 海冰数据面板
- 1979-2024 年北极海冰年均面积趋势（线性回归）
- 月度热力图（12个月×45年）
- 四季变化对比（含变化率条形图）
- 航道通航潜力指数（基于9月冰情计算）
- **新增**：线性趋势预测（2025-2034），含95%置信区间

### 📊 GDELT 事件分析
- 年度事件数量趋势（堆积柱状图 + 折线图）
- 国家维度分析（条形图 + 趋势线）
- 事件类别分布（饼图 + 年度堆叠柱状图）
- 情感分析（AvgTone 各国对比 + 各类别情感均值）
- **修复**：Year/Year_local 列兼容，空数据保护

### 🏛️ 战略叙事图文联动
- 1979-2024 年10个关键节点战略叙事
- 国家级事件卡片 + 核心信息卡
- 三大政策建议框架（规则制定/科技合作/风险防控）
- 「技术赋能地缘」分析框架说明

### 📥 数据获取
- 快速生成北极事件模拟数据（GDELT 格式）
- GDELT 官网实时抓取（按年份过滤）
- 北极关键词分类（8大类别 + 噪音过滤）
- 自动网格聚合 + 年度国家聚合

### 🗄️ 数据管理中心（新功能）
- **GDELT 1.0 流水线**：流式下载→按北极关键词过滤→月度面板聚合
- **GDELT 2.0 DOC API**：artlist/timelinevol/timelinetone/timelinesourcecountry 四种模式
- **数据质量报告**：文件完整性检查、清洗率统计、失败文件日志
- **多源数据说明**：GDELT/NSIDC/政策文件/GeoJSON 完整获取指南
- **数据预览与导出**：任意 CSV 文件预览、列统计、下载

## 数据来源

| 数据源 | 地址 | 覆盖范围 |
|--------|------|----------|
| GDELT 1.0 | http://data.gdeltproject.org/events/index.html | 1979-至今 |
| GDELT 2.0 API | https://api.gdeltproject.org/api/v2/doc/doc | 近12个月 |
| NSIDC 海冰 | https://nsidc.org/data/g02135 | 1979-2024 |
| NGA 航道数据 | https://nga.mil/ | 北极航道 |
| INTERACT 科考站 | https://eu-interact.org/ | 北极科考站 |

## 关键词策略

`keywords.csv` 按以下分组管理北极相关关键词：

- **space**（北极地区）：Arctic, High North, Northern Sea Route, Northwest Passage...
- **actor**（利益攸关方）：中国/俄罗斯/美国/加拿大等11国 + 北极理事会
- **technology**（技术领域）：icebreaker, LNG, satellite communication, navigation...
- **geopolitics**（地缘政治）：security, military, sanctions, cooperation...
- **climate**（气候）：climate change, sea ice, melting ice, navigability...
- **resource**（资源）：critical minerals, natural gas, oil, fisheries...
- **noise**（噪音排除）：Antarctic, penguin, Arctic Monkeys, cruise...
