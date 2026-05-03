"""
核心数据层 - 统一管理所有静态和动态数据
避免重复爬取，保证各页面数据一致性
"""

import os
import json
import math
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
GEO_DIR = os.path.join(os.path.dirname(__file__), '..', 'geojson')


# =========================================================================
# 海冰数据
# =========================================================================

def load_ice_data():
    """加载北极海冰面积数据"""
    monthly_path = os.path.join(DATA_DIR, 'ice_area_monthly.csv')
    summary_path = os.path.join(DATA_DIR, 'ice_area_summary.csv')
    long_path = os.path.join(DATA_DIR, 'ice_area_long.csv')

    if os.path.exists(monthly_path):
        df = pd.read_csv(monthly_path, index_col='year')
    else:
        df = _generate_ice_data()[0]

    if os.path.exists(long_path):
        long_df = pd.read_csv(long_path)
    else:
        _, _, long_df = _generate_ice_data()

    df_min = df.min(axis=1)
    df_max = df.max(axis=1)
    df_mean = df.mean(axis=1).round(2)
    df_summary = pd.DataFrame({'mean': df_mean, 'minimum': df_min, 'maximum': df_max})
    return df, df_summary, long_df


def _generate_ice_data():
    """生成海冰数据 CSV（基于NSIDC风格的趋势衰减模型）"""
    os.makedirs(DATA_DIR, exist_ok=True)
    years = list(range(1979, 2025))
    rng = np.random.RandomState(42)

    month_means = {
        'jan': 13.05, 'feb': 14.20, 'mar': 14.60, 'apr': 14.15,
        'may': 12.35, 'jun': 9.55,  'jul': 7.20,  'aug': 5.70,
        'sep': 6.15,  'oct': 9.60,  'nov': 11.60, 'dec': 12.80
    }
    decline = -0.065

    records = []
    for i, yr in enumerate(years):
        row = {'year': yr}
        for m, base in month_means.items():
            noise = rng.uniform(-0.15, 0.15)
            val = max(base + i * decline + noise, base * 0.65)
            row[m] = round(val, 2)
        records.append(row)

    df = pd.DataFrame(records).set_index('year')
    df.to_csv(os.path.join(DATA_DIR, 'ice_area_monthly.csv'))

    df_min = df.min(axis=1)
    df_max = df.max(axis=1)
    df_mean = df.mean(axis=1).round(2)
    pd.DataFrame({'mean': df_mean, 'minimum': df_min, 'maximum': df_max}).to_csv(
        os.path.join(DATA_DIR, 'ice_area_summary.csv'))

    long_df = df.reset_index().melt(
        id_vars=['year'], value_vars=list(month_means.keys()),
        var_name='month', value_name='ice_extent'
    )
    month_abbr = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
    long_df['month_num'] = long_df['month'].map({k: i+1 for i, k in enumerate(month_abbr)})
    long_df.to_csv(os.path.join(DATA_DIR, 'ice_area_long.csv'), index=False)

    return df, pd.DataFrame({'mean': df_mean, 'minimum': df_min, 'maximum': df_max}), long_df


# =========================================================================
# CMIP6 预测数据
# =========================================================================

def load_cmip6_forecast():
    """生成 CMIP6 情景预测数据"""
    years = list(range(2025, 2101, 5))
    rng = np.random.RandomState(123)

    base_2024 = 9.5
    ssp126_vals, ssp585_vals = [], []
    for i, yr in enumerate(years):
        ssp126_vals.append(max(base_2024 - 0.01 * i + rng.uniform(-0.1, 0.1), 1.0))
        ssp585_vals.append(max(base_2024 - 0.03 * i + rng.uniform(-0.15, 0.15), 0.5))

    return pd.DataFrame({
        'year': years,
        'SSP1-2.6': [round(v, 2) for v in ssp126_vals],
        'SSP5-8.5': [round(v, 2) for v in ssp585_vals]
    })


# =========================================================================
# GDELT 数据
# =========================================================================

def load_gdelt_data():
    """加载 GDELT 处理后的数据"""
    grid_path = os.path.join(DATA_DIR, 'gdelt_arctic_by_grid.csv')
    yc_path = os.path.join(DATA_DIR, 'gdelt_arctic_by_year_country.csv')

    grid_df = pd.read_csv(grid_path) if os.path.exists(grid_path) else _generate_gdelt_grid()
    yc_df = pd.read_csv(yc_path) if os.path.exists(yc_path) else _generate_gdelt_yc()

    # 确保列名兼容处理
    if 'Year_local' not in grid_df.columns:
        if 'year' in grid_df.columns:
            grid_df = grid_df.rename(columns={'year': 'Year_local'})
        elif 'Year' in grid_df.columns:
            grid_df = grid_df.rename(columns={'Year': 'Year_local'})

    return grid_df, yc_df


def _generate_gdelt_grid():
    """生成 GDELT 网格数据"""
    rng = np.random.RandomState(99)
    categories = [
        'arctic_resource', 'arctic_military', 'arctic_shipping',
        'arctic_research', 'arctic_infrastructure', 'arctic_technology',
        'arctic_cooperation', 'arctic_governance'
    ]
    rows = []
    for year in range(2018, 2025):
        for _ in range(80):
            lat = rng.uniform(65, 82)
            lon = rng.uniform(-170, 180)
            rows.append({
                'lat_grid': round(lat / 5) * 5,
                'lon_grid': round(lon / 5) * 5,
                'Year_local': year,
                'EventCategory': rng.choice(categories),
                'EventCount': rng.randint(1, 25),
                'AvgTone': round(rng.uniform(-4, 3), 2)
            })
    df = pd.DataFrame(rows)
    return df.groupby(['lat_grid', 'lon_grid', 'Year_local', 'EventCategory']).agg(
        EventCount=('EventCount', 'sum'),
        AvgTone=('AvgTone', 'mean')
    ).reset_index()


def _generate_gdelt_yc():
    """生成 GDELT 年度国家数据"""
    rng = np.random.RandomState(77)
    countries = ['RUS', 'CHN', 'USA', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL']
    rows = []
    for year in range(2018, 2025):
        for country in countries:
            base = 30 if country == 'RUS' else 8 if country in ['USA', 'CHN'] else 3
            count = int(base * (1 + 0.08 * (year - 2018)) + rng.randint(0, 15))
            tone_base = {'CHN': 1.5, 'RUS': -1.0, 'USA': -2.0}.get(country, 0.5)
            rows.append({
                'year': year,
                'CountryCode': country,
                'EventCount': count,
                'AvgTone': round(tone_base + rng.uniform(-1, 1), 2)
            })
    return pd.DataFrame(rows)


# =========================================================================
# 科考站数据
# =========================================================================

def load_stations():
    """加载科考站数据（包含所有大北极国家）"""
    path = os.path.join(GEO_DIR, 'research_stations.geojson')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _generate_stations()


def _generate_stations():
    """生成科考站数据（备用）"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "黄河站", "country": "中国", "country_code": "CHN",
                    "established": 2004,
                    "research_focus": ["极地空间环境", "极光观测", "大气物理"],
                    "tech_domain": "极地通信卫星",
                    "description": "中国第一个北极科考站，位于斯瓦尔巴群岛。"
                },
                "geometry": {"type": "Point", "coordinates": [11.93, 78.92]}
            }
        ]
    }


# =========================================================================
# 地缘博弈网络数据
# =========================================================================

def load_geopolitics_network(period=None):
    """生成大北极国家地缘博弈关系网络数据（支持多时期切换）"""
    periods = {
        '2018-2021': [
            {"source": "RUS", "target": "CHN", "relation": "cooperation", "strength": 80},
            {"source": "RUS", "target": "USA", "relation": "competition", "strength": 65},
            {"source": "RUS", "target": "NOR", "relation": "competition", "strength": 60},
            {"source": "RUS", "target": "CAN", "relation": "competition", "strength": 55},
            {"source": "USA", "target": "CAN", "relation": "cooperation", "strength": 90},
            {"source": "USA", "target": "NOR", "relation": "cooperation", "strength": 85},
            {"source": "USA", "target": "DNK", "relation": "cooperation", "strength": 80},
            {"source": "USA", "target": "CHN", "relation": "competition", "strength": 60},
            {"source": "CHN", "target": "NOR", "relation": "cooperation", "strength": 65},
            {"source": "CHN", "target": "FIN", "relation": "cooperation", "strength": 60},
            {"source": "NATO", "target": "USA", "relation": "cooperation", "strength": 95},
            {"source": "NATO", "target": "NOR", "relation": "cooperation", "strength": 90},
            {"source": "NATO", "target": "DNK", "relation": "cooperation", "strength": 85},
            {"source": "NATO", "target": "RUS", "relation": "competition", "strength": 75},
            {"source": "ARC", "target": "RUS", "relation": "cooperation", "strength": 50},
            {"source": "ARC", "target": "USA", "relation": "cooperation", "strength": 70},
            {"source": "EU", "target": "DNK", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "FIN", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "SWE", "relation": "cooperation", "strength": 75},
            {"source": "JPN", "target": "CHN", "relation": "competition", "strength": 50},
            {"source": "KOR", "target": "CHN", "relation": "cooperation", "strength": 55},
        ],
        '2022-2024': [
            {"source": "RUS", "target": "CHN", "relation": "cooperation", "strength": 90},
            {"source": "RUS", "target": "USA", "relation": "confrontation", "strength": 95},
            {"source": "RUS", "target": "NOR", "relation": "confrontation", "strength": 80},
            {"source": "RUS", "target": "CAN", "relation": "competition", "strength": 70},
            {"source": "USA", "target": "CAN", "relation": "cooperation", "strength": 95},
            {"source": "USA", "target": "NOR", "relation": "cooperation", "strength": 90},
            {"source": "USA", "target": "DNK", "relation": "cooperation", "strength": 85},
            {"source": "USA", "target": "CHN", "relation": "confrontation", "strength": 90},
            {"source": "CHN", "target": "NOR", "relation": "cooperation", "strength": 60},
            {"source": "CHN", "target": "FIN", "relation": "cooperation", "strength": 55},
            {"source": "NATO", "target": "USA", "relation": "cooperation", "strength": 95},
            {"source": "NATO", "target": "NOR", "relation": "cooperation", "strength": 95},
            {"source": "NATO", "target": "DNK", "relation": "cooperation", "strength": 90},
            {"source": "NATO", "target": "RUS", "relation": "confrontation", "strength": 100},
            {"source": "ARC", "target": "RUS", "relation": "confrontation", "strength": 30},
            {"source": "ARC", "target": "USA", "relation": "cooperation", "strength": 60},
            {"source": "EU", "target": "DNK", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "FIN", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "SWE", "relation": "cooperation", "strength": 75},
            {"source": "JPN", "target": "CHN", "relation": "competition", "strength": 65},
            {"source": "KOR", "target": "CHN", "relation": "cooperation", "strength": 50},
        ],
        'all': [
            {"source": "RUS", "target": "CHN", "relation": "cooperation", "strength": 85},
            {"source": "RUS", "target": "USA", "relation": "confrontation", "strength": 80},
            {"source": "RUS", "target": "NOR", "relation": "competition", "strength": 70},
            {"source": "RUS", "target": "CAN", "relation": "competition", "strength": 65},
            {"source": "USA", "target": "CAN", "relation": "cooperation", "strength": 92},
            {"source": "USA", "target": "NOR", "relation": "cooperation", "strength": 88},
            {"source": "USA", "target": "DNK", "relation": "cooperation", "strength": 82},
            {"source": "USA", "target": "CHN", "relation": "confrontation", "strength": 85},
            {"source": "CHN", "target": "NOR", "relation": "cooperation", "strength": 62},
            {"source": "CHN", "target": "FIN", "relation": "cooperation", "strength": 58},
            {"source": "NATO", "target": "USA", "relation": "cooperation", "strength": 95},
            {"source": "NATO", "target": "NOR", "relation": "cooperation", "strength": 92},
            {"source": "NATO", "target": "DNK", "relation": "cooperation", "strength": 88},
            {"source": "NATO", "target": "RUS", "relation": "confrontation", "strength": 87},
            {"source": "ARC", "target": "RUS", "relation": "cooperation", "strength": 40},
            {"source": "ARC", "target": "USA", "relation": "cooperation", "strength": 65},
            {"source": "EU", "target": "DNK", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "FIN", "relation": "cooperation", "strength": 80},
            {"source": "EU", "target": "SWE", "relation": "cooperation", "strength": 75},
            {"source": "JPN", "target": "CHN", "relation": "competition", "strength": 58},
            {"source": "KOR", "target": "CHN", "relation": "cooperation", "strength": 52},
        ]
    }

    nodes = [
        {"id": "RUS", "name": "俄罗斯", "type": "state", "influence": 95, "color": "#E53935"},
        {"id": "USA", "name": "美国", "type": "state", "influence": 90, "color": "#1565C0"},
        {"id": "CHN", "name": "中国", "type": "state", "influence": 75, "color": "#FF0000"},
        {"id": "CAN", "name": "加拿大", "type": "state", "influence": 60, "color": "#43A047"},
        {"id": "NOR", "name": "挪威", "type": "state", "influence": 55, "color": "#FF6B35"},
        {"id": "DNK", "name": "丹麦", "type": "state", "influence": 50, "color": "#FFA726"},
        {"id": "FIN", "name": "芬兰", "type": "state", "influence": 45, "color": "#9C27B0"},
        {"id": "SWE", "name": "瑞典", "type": "state", "influence": 45, "color": "#00BCD4"},
        {"id": "ISL", "name": "冰岛", "type": "state", "influence": 40, "color": "#795548"},
        {"id": "JPN", "name": "日本", "type": "state", "influence": 55, "color": "#BCAAA4"},
        {"id": "KOR", "name": "韩国", "type": "state", "influence": 50, "color": "#1E88E5"},
        {"id": "EU", "name": "欧盟", "type": "organization", "influence": 65, "color": "#003399"},
        {"id": "NATO", "name": "北约", "type": "organization", "influence": 70, "color": "#008000"},
        {"id": "ARC", "name": "北极理事会", "type": "organization", "influence": 60, "color": "#607D8B"},
    ]

    key = period if period in periods else 'all'
    links = periods[key]
    for link in links:
        link['period'] = key
    return {"nodes": nodes, "links": links}


# =========================================================================
# 专利技术数据
# =========================================================================

def load_patent_data():
    """生成极地核心技术专利数据"""
    rng = np.random.RandomState(55)
    categories = ['遥感探测', '冰区船舶', '油气开采', '冻土工程', '气候模拟']
    countries = ['RUS', 'CHN', 'USA', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR']
    records = []
    for year in range(2000, 2025):
        for country in countries:
            for cat in categories:
                if rng.random() < 0.25:
                    base = 50 if country == 'CHN' else 30 if country == 'USA' else 10 if country == 'RUS' else 5
                    count = int(base * (1 + 0.05 * (year - 2000)) + rng.randint(0, 20))
                    records.append({
                        'year': year,
                        'country': country,
                        'category': cat,
                        'patent_count': count,
                        'avg_quality': round(rng.uniform(60, 95), 1)
                    })
    return pd.DataFrame(records)


def load_tech_network():
    """生成技术合作网络数据"""
    institutions = [
        {"id": "CAS", "name": "中国科学院", "country": "CHN", "type": "research"},
        {"id": "NORS", "name": "挪威极地研究所", "country": "NOR", "type": "research"},
        {"id": "USGS", "name": "美国地质调查局", "country": "USA", "type": "research"},
        {"id": "RAS", "name": "俄罗斯科学院", "country": "RUS", "type": "research"},
        {"id": "CSIC", "name": "中国船舶集团", "country": "CHN", "type": "industry"},
        {"id": "SCAN", "name": "俄罗斯国家核公司", "country": "RUS", "type": "industry"},
        {"id": "GAZ", "name": "俄罗斯天然气工业", "country": "RUS", "type": "industry"},
        {"id": "KNMI", "name": "荷兰皇家气象研究所", "country": "NLD", "type": "research"},
        {"id": "JAXA", "name": "日本宇宙航空研究机构", "country": "JPN", "type": "research"},
        {"id": "AARI", "name": "俄罗斯北极研究所", "country": "RUS", "type": "research"},
        {"id": "UIC", "name": "伊利诺伊大学", "country": "USA", "type": "research"},
        {"id": "SMHI", "name": "瑞典气象水文研究所", "country": "SWE", "type": "research"},
        {"id": "DMI", "name": "丹麦气象研究所", "country": "DNK", "type": "research"},
    ]
    links = [
        {"source": "CAS", "target": "NORS", "strength": 75, "type": "joint_research"},
        {"source": "CAS", "target": "JAXA", "strength": 60, "type": "satellite_data"},
        {"source": "NORS", "target": "USGS", "strength": 85, "type": "climate_monitoring"},
        {"source": "NORS", "target": "KNMI", "strength": 80, "type": "climate_modeling"},
        {"source": "USGS", "target": "UIC", "strength": 70, "type": "research"},
        {"source": "RAS", "target": "AARI", "strength": 90, "type": "internal"},
        {"source": "RAS", "target": "GAZ", "strength": 85, "type": "oil_gas_dev"},
        {"source": "CSIC", "target": "SCAN", "strength": 55, "type": "shipbuilding"},
        {"source": "CAS", "target": "UIC", "strength": 45, "type": "academic"},
        {"source": "JAXA", "target": "USGS", "strength": 65, "type": "satellite_data"},
        {"source": "KNMI", "target": "UIC", "strength": 60, "type": "climate_modeling"},
        {"source": "AARI", "target": "NORS", "strength": 40, "type": "arctic_research"},
        {"source": "SMHI", "target": "KNMI", "strength": 70, "type": "climate_monitoring"},
        {"source": "SMHI", "target": "NORS", "strength": 65, "type": "climate_modeling"},
        {"source": "DMI", "target": "NORS", "strength": 60, "type": "climate_monitoring"},
    ]
    return {"nodes": institutions, "links": links}


# =========================================================================
# 安全风险数据
# =========================================================================

def load_risk_data():
    """生成北极安全风险评估数据（多维度风险评估）"""
    rng = np.random.RandomState(66)
    regions = [
        {"name": "楚科奇海", "lat": 68, "lon": -172, "belong": "美俄争议区"},
        {"name": "白令海峡", "lat": 65, "lon": -168, "belong": "美俄交界区"},
        {"name": "东西伯利亚海", "lat": 74, "lon": 150, "belong": "俄罗斯专属区"},
        {"name": "拉普捷夫海", "lat": 76, "lon": 125, "belong": "俄罗斯专属区"},
        {"name": "喀拉海", "lat": 76, "lon": 70, "belong": "俄罗斯专属区"},
        {"name": "巴伦支海", "lat": 74, "lon": 20, "belong": "挪俄争议区"},
        {"name": "挪威海", "lat": 70, "lon": 5, "belong": "北约控制区"},
        {"name": "格陵兰海", "lat": 72, "lon": -15, "belong": "北约控制区"},
        {"name": "波弗特海", "lat": 74, "lon": -140, "belong": "美加争议区"},
        {"name": "加拿大群岛区", "lat": 76, "lon": -100, "belong": "加拿大主张区"},
    ]
    categories = ['航道通行', '科考安全', '技术壁垒', '权益冲突']
    records = []
    for region in regions:
        for cat in categories:
            base = 5 if cat == '权益冲突' else 3
            records.append({
                'region': region['name'],
                'lat': region['lat'],
                'lon': region['lon'],
                'belong': region['belong'],
                'category': cat,
                'risk_level': min(10, max(1, base + rng.randint(0, 6))),
                'trend': rng.choice(['上升', '稳定', '下降']),
                'main_factors': rng.choice([
                    '大国军事对峙', '极端气候', '环保舆论制约',
                    '航道管辖争议', '技术出口管制', '主权声索冲突',
                    '冰情不确定性', '破冰能力不足'
                ])
            })
    return pd.DataFrame(records)


# =========================================================================
# SWOT 数据
# =========================================================================

def get_swot_data():
    """中国北极战略 SWOT 分析数据"""
    return {
        "strengths": [
            ("科研实力", "极地科考体系完善，「雪龙2」实现全年候航行能力"),
            ("资本优势", "北极能源项目投资规模领先，「一带一路」融资体系支撑"),
            ("技术进步", "极地LNG船、破冰船建造技术快速追赶"),
            ("战略视野", "「人类命运共同体」理念提供独特的北极治理观"),
        ],
        "weaknesses": [
            ("距离劣势", "非北极国家，距北极核心区数千公里，投送能力有限"),
            ("制度缺失", "缺乏北极治理机制正式成员资格，话语权不足"),
            ("技术差距", "核动力破冰船、极地通信卫星等领域仍有差距"),
            ("经验不足", "北极航道商业运营经验积累时间较短"),
        ],
        "opportunities": [
            ("航道价值", "气候变化加速航道通航窗口扩大，商业价值凸显"),
            ("合作空间", "科技合作仍是大国北极关系「压舱石」"),
            ("规则制定", "北极治理规则重构期为中国参与提供窗口"),
            ("能源需求", "北极油气资源满足中国能源进口多元化需求"),
        ],
        "threats": [
            ("大国对抗", "中美博弈向北极延伸，技术脱钩风险上升"),
            ("航道控制", "俄罗斯强化东北航道管辖限制自由通行"),
            ("环境约束", "国际环保压力限制资源开发空间"),
            ("理事受阻", "北极理事会功能受损，多边合作机制弱化"),
        ]
    }


# =========================================================================
# 政策文本数据
# =========================================================================

def load_policy_texts():
    """各国北极政策文本摘要（用于词云和情感分析）"""
    return {
        "RUS": {
            "name": "俄罗斯",
            "text": "北极战略核心区域国家主权安全航道管控资源开发核动力破冰船北方舰队军事部署能源出口基础设施投资科考站网络环境保护永冻土资源天然气水合物北方海航道管理局海域划界军事化存在",
            "sentiment": -1.5,
            "key_words": ["主权", "管控", "军事", "能源", "破冰船"],
            "summary": "强调北极主权、安全与航道管控，通过军事部署强化存在，核动力破冰船为战略工具"
        },
        "USA": {
            "name": "美国",
            "text": "北极领导力航行自由安全威胁竞争战略国防部部署极地安全倡议气候变化环境保护科研合作盟友协调北极理事会参与航行自由原则印太战略延伸极地作战能力",
            "sentiment": -2.0,
            "key_words": ["领导力", "竞争", "安全", "盟友", "航行自由"],
            "summary": "坚持航行自由，将中俄定位北极挑战者，通过国防部北极战略应对竞争"
        },
        "CHN": {
            "name": "中国",
            "text": "近北极国家北极利益攸关方冰上丝绸之路人类命运共同体科技合作可持续发展和平利用航道投资能源合作科研交流环境保护共同治理一带一路极地命运共同体共建共享",
            "sentiment": 2.0,
            "key_words": ["合作", "和平", "共同", "科技", "可持续"],
            "summary": "定位「近北极国家」与「利益攸关方」，倡导「人类命运共同体」理念，侧重科技合作"
        },
        "NOR": {
            "name": "挪威",
            "text": "巴伦支海合作环境保护可持续渔业资源管理科研合作国际法框架北极理事会积极参与航运安全气候变化应对和平利用斯瓦尔巴德群岛条约体系极地治理领导者",
            "sentiment": 1.5,
            "key_words": ["环保", "可持续", "合作", "国际法", "渔业"],
            "summary": "推动巴伦支海合作与环境保护，主张以国际法框架解决争端"
        },
        "CAN": {
            "name": "加拿大",
            "text": "北极主权内水声索西北航道管辖北方居民权益环境保护原住民权利基础设施科研能力气候变化适应北方补给线主权安全北方海道管理阿拉斯加边境",
            "sentiment": -0.5,
            "key_words": ["主权", "管辖", "环保", "居民", "原住民"],
            "summary": "强调北极主权和西北航道管辖，注重原住民权益和环境保护"
        },
        "DNK": {
            "name": "丹麦",
            "text": "格陵兰自治北极治理领导者北极理事会轮值主席气候变化科学支撑环境保护科研合作国际合作安全议题格陵兰大陆架声索极地科学大国北极战略框架",
            "sentiment": 1.0,
            "key_words": ["治理", "气候", "科学", "环保", "国际"],
            "summary": "推动北极治理与气候科学，通过格陵兰发挥北极影响力"
        }
    }


# =========================================================================
# 航道数据
# =========================================================================

def load_route_data():
    """加载三大北极航道数据"""
    return {
        '东北航道': {
            'start': '欧洲（挪威）',
            'end': '亚洲（白令海峡）',
            'distance': '约5600海里',
            'duration': '20-30天',
            'operator': '俄罗斯主导',
            'open_months': '7-11月',
            'description': '沿俄罗斯北岸连接欧洲与亚洲的传统航道'
        },
        '西北航道': {
            'start': '北大西洋（格陵兰/加拿大）',
            'end': '北太平洋（阿拉斯加）',
            'distance': '约4500海里',
            'duration': '25-40天',
            'operator': '加拿大主张管辖',
            'open_months': '8-10月',
            'description': '穿越加拿大北极群岛的航道，商业价值待开发'
        },
        '跨极航道': {
            'start': '欧洲',
            'end': '亚洲',
            'distance': '约4000海里（最短）',
            'duration': '15-25天（最短）',
            'operator': '国际水域',
            'open_months': '9-10月（仅夏季）',
            'description': '穿越北极点的直航航道，受气候变化影响最大'
        }
    }


# =========================================================================
# 趋势计算
# =========================================================================

def compute_trend(df_summary):
    """计算海冰变化趋势"""
    years = df_summary.index.values.astype(float)
    means = df_summary['mean'].values
    x_mean = years.mean()
    y_mean = means.mean()
    slope = np.sum((years - x_mean) * (means - y_mean)) / np.sum((years - x_mean) ** 2)
    intercept = y_mean - slope * x_mean
    fitted = slope * years + intercept
    ss_res = np.sum((means - fitted) ** 2)
    ss_tot = np.sum((means - y_mean) ** 2)
    r_squared = 1 - ss_res / ss_tot
    return {
        'slope': round(float(slope), 4),
        'intercept': round(float(intercept), 2),
        'r_squared': round(float(r_squared), 4),
        'decline_per_decade': round(float(abs(slope) * 10), 2)
    }


# =========================================================================
# 季节统计
# =========================================================================

def get_seasonal_stats(long_df):
    """计算季节性统计"""
    spring = long_df[long_df['month_num'].isin([3, 4, 5])].groupby('year')['ice_extent'].mean()
    summer = long_df[long_df['month_num'].isin([6, 7, 8])].groupby('year')['ice_extent'].mean()
    autumn = long_df[long_df['month_num'].isin([9, 10, 11])].groupby('year')['ice_extent'].mean()
    winter_df = long_df[long_df['month_num'].isin([12, 1, 2])].copy()
    winter_df['winter_year'] = winter_df.apply(
        lambda r: r['year'] if r['month_num'] in [1, 2] else r['year'] + 1, axis=1
    )
    winter = winter_df.groupby('winter_year')['ice_extent'].mean()
    return pd.DataFrame({
        '春季(3-5月)': spring,
        '夏季(6-8月)': summer,
        '秋季(9-11月)': autumn,
        '冬季(12-2月)': winter
    }).round(2)


# =========================================================================
# M-K 突变检验（简化版）
# =========================================================================

def mk_test(series):
    """
    Mann-Kendall 趋势检验（简化实现）
    返回: {has_trend: bool, z_value: float, p_value: float, trend: str}
    """
    import math
    n = len(series)
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = series[j] - series[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1
    var_s = (n * (n - 1) * (2 * n + 5)) / 18
    if s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0
    # Two-tailed p-value approximation
    if abs(z) > 0:
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    else:
        p_value = 1.0
    return {
        'has_trend': abs(z) > 1.96,
        'z_value': round(z, 3),
        'p_value': round(p_value, 4),
        'trend': '显著下降' if z < -1.96 else '显著上升' if z > 1.96 else '无显著趋势'
    }


# =========================================================================
# 气候/环境数据（气温、冻土等模拟）
# =========================================================================

def load_climate_data():
    """生成北极气候辅助数据（气温、冻土活动层等）"""
    rng = np.random.RandomState(88)
    years = list(range(1980, 2025))
    records = []
    for yr in years:
        records.append({
            'year': yr,
            'arctic_temp_anomaly': round(1.5 + (yr - 1980) * 0.045 + rng.uniform(-0.2, 0.2), 2),
            'permafrost_thickness': round(350 - (yr - 1980) * 1.5 + rng.uniform(-5, 5), 1),
            'precipitation_change': round((yr - 1980) * 0.08 + rng.uniform(-0.5, 0.5), 2),
        })
    return pd.DataFrame(records)


# =========================================================================
# 策略建议数据库
# =========================================================================

def get_strategy_recommendations(scenario):
    """获取策略建议（基于风险情景）"""
    strategies = {
        "正常运营情景": {
            "title": "常规推进策略",
            "color": "#43A047",
            "risk_level": "低",
            "items": [
                ("科考安全", "深化极地科考合作，扩大「雪龙2」航线覆盖范围，与北欧国家共享科考数据"),
                ("技术攻关", "加快核动力破冰船国产化论证，推进极地通信卫星星座规划"),
                ("航道保障", "深化与俄罗斯能源合作，确保「冰上丝绸之路」物流畅通"),
                ("外交参与", "积极争取北极理事会正式观察员地位，提升制度性话语权"),
            ]
        },
        "航道封锁情景": {
            "title": "多元通道策略",
            "color": "#FF6B35",
            "risk_level": "中高",
            "items": [
                ("科考安全", "加强国内极地模拟训练能力建设，减少对单一海域依赖"),
                ("技术攻关", "突破极地无人航行技术，发展自主导航与应急通信能力"),
                ("航道保障", "开拓西北航道替代方案，加强与加拿大的沟通协调"),
                ("外交参与", "通过「一带一路」多边平台争取航道通行权益国际法支持"),
            ]
        },
        "多边机制停摆情景": {
            "title": "双边替代策略",
            "color": "#1565C0",
            "risk_level": "中",
            "items": [
                ("科考安全", "通过双边科考协议替代多边框架，确保科研连续性"),
                ("技术攻关", "加大自主技术研发投入，降低外部技术依赖"),
                ("航道保障", "探索与域内国家签署双边航道合作协议的可能性"),
                ("外交参与", "利用上海合作组织等平台，构建替代性合作框架"),
            ]
        },
        "大国军事对峙升级情景": {
            "title": "风险管控策略",
            "color": "#E53935",
            "risk_level": "高",
            "items": [
                ("科考安全", "暂时回避敏感区域科考，优先保障人员安全"),
                ("技术攻关", "加速极地军民两用技术自主化，降低「卡脖子」风险"),
                ("航道保障", "暂停高风险航段商业运营，等待局势缓和"),
                ("外交参与", "通过非官方渠道传递缓和信号，避免直接对抗"),
            ]
        },
        "极端气候灾害情景": {
            "title": "应急响应策略",
            "color": "#7B1FA2",
            "risk_level": "中",
            "items": [
                ("科考安全", "建立极地气象预警联动机制，提升应急响应速度"),
                ("技术攻关", "发展极端环境作业装备，提升船舶抗风险能力"),
                ("航道保障", "制定极端气候应急预案，建立航运保险机制"),
                ("外交参与", "推动建立北极气候灾害联合应对机制"),
            ]
        }
    }
    return strategies.get(scenario, strategies["正常运营情景"])


# =========================================================================
# 下载数据集元数据
# =========================================================================

def get_downloadable_datasets():
    """返回可下载数据集的元数据列表"""
    return [
        {
            "name": "北极海冰面积数据集",
            "desc": "NSIDC格式，1979-2024逐月海冰面积范围数据",
            "file": "ice_area_monthly.csv",
            "rows": "552条",
            "format": "CSV",
            "size": "~15KB",
            "source": "NSIDC Sea Ice Index (模拟数据)"
        },
        {
            "name": "北极海冰年度汇总",
            "desc": "年均值、年最大、年最小值，1979-2024",
            "file": "ice_area_summary.csv",
            "rows": "46条",
            "format": "CSV",
            "size": "~2KB",
            "source": "NSIDC 汇总"
        },
        {
            "name": "GDELT北极事件网格聚合",
            "desc": "按5°×5°网格聚合，含事件类型和情感值",
            "file": "gdelt_arctic_by_grid.csv",
            "rows": "动态",
            "format": "CSV",
            "size": "动态",
            "source": "GDELT 全球事件数据库"
        },
        {
            "name": "GDELT年度国家聚合",
            "desc": "按年度和国家聚合的事件统计和情感分析",
            "file": "gdelt_arctic_by_year_country.csv",
            "rows": "动态",
            "format": "CSV",
            "size": "动态",
            "source": "GDELT 汇总"
        },
        {
            "name": "极地科考站分布",
            "desc": "各国在北极的科考站位置和研究领域",
            "file": "research_stations.geojson",
            "rows": "~20个站点",
            "format": "GeoJSON",
            "size": "~8KB",
            "source": "INTERACT / 手工整理"
        },
        {
            "name": "北极战略航道数据",
            "desc": "三大航道地理轨迹和通航信息",
            "file": "arctic_routes.geojson",
            "rows": "3条",
            "format": "GeoJSON",
            "size": "~4KB",
            "source": "手工整理"
        },
    ]
