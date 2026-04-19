# 北极地缘气候多源数据可视化平台

## 依赖安装

在终端中运行以下命令安装全部依赖：

```bash
pip install streamlit pandas numpy plotly folium streamlit-folium requests beautifulsoup4 lxml
```

## 快速启动

```bash
cd d:\beiji
streamlit run app.py
```

## 项目结构

```
beiji/
├── app.py                  # 主入口（多页面导航）
├── pages/
│   ├── 1_🌍_北极地图概览.py        # 交互式Folium地图
│   ├── 2_❄️_海冰数据.py           # 海冰面积可视化
│   ├── 3_📊_GDELT事件分析.py     # 地缘事件分析
│   ├── 4_🏛️_战略叙事区.py         # 图文联动
│   └── 5_📥_数据爬取工具.py       # GDELT数据爬虫
├── src/
│   ├── gdelt_fetcher.py    # GDELT数据抓取核心模块
│   ├── ice_data.py         # 海冰数据处理
│   └── narrative.py        # 战略叙事内容
├── data/
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
└── geojson/
    ├── arctic_routes.geojson    # 三大航道
    ├── research_stations.geojson # 科考站
    └── conflicts.geojson       # 冲突热力
```

## 数据来源

- GDELT: [http://data.gdeltproject.org/events/index.html](http://data.gdeltproject.org/events/index.html)
- NSIDC 海冰数据: [https://nsidc.org/data/g02135](https://nsidc.org/data/g02135)
- 航道数据: NGA Arctic Sea Routes

