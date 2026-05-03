"""
核心数据层 - 统一管理所有静态和动态数据
避免重复爬取，保证各页面数据一致性
"""

import os
import json
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')


# ============ 海冰数据 ============

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

    df_summary = pd.DataFrame({
        'mean': df_mean,
        'minimum': df_min,
        'maximum': df_max
    })

    return df, df_summary, long_df


def _generate_ice_data():
    """生成海冰数据 CSV"""
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


# ============ CMIP6 预测数据 ============

def load_cmip6_forecast():
    """生成 CMIP6 情景预测数据（SSP1-2.6 和 SSP5-8.5）"""
    years = list(range(2025, 2101, 5))
    rng = np.random.RandomState(123)

    base_2024 = 9.5  # 2024年9月海冰面积基数

    ssp126_vals = []
    ssp585_vals = []
    for i, yr in enumerate(years):
        ssp126_vals.append(max(base_2024 - 0.01 * i + rng.uniform(-0.1, 0.1), 1.0))
        ssp585_vals.append(max(base_2024 - 0.03 * i + rng.uniform(-0.15, 0.15), 0.5))

    return pd.DataFrame({
        'year': years,
        'SSP1-2.6': [round(v, 2) for v in ssp126_vals],
        'SSP5-8.5': [round(v, 2) for v in ssp585_vals]
    })


# ============ GDELT 数据 ============

def load_gdelt_data():
    """加载 GDELT 处理后的数据"""
    grid_path = os.path.join(DATA_DIR, 'gdelt_arctic_by_grid.csv')
    yc_path = os.path.join(DATA_DIR, 'gdelt_arctic_by_year_country.csv')

    grid_df = pd.read_csv(grid_path) if os.path.exists(grid_path) else _generate_gdelt_grid()
    yc_df = pd.read_csv(yc_path) if os.path.exists(yc_path) else _generate_gdelt_yc()

    if 'Year_local' not in grid_df.columns and 'Year' in grid_df.columns:
        grid_df = grid_df.rename(columns={'Year': 'Year_local'})

    return grid_df, yc_df


def _generate_gdelt_grid():
    """生成 GDELT 网格数据"""
    rng = np.random.RandomState(99)
    rows = []
    categories = [
        'arctic_resource', 'arctic_military', 'arctic_shipping',
        'arctic_research', 'arctic_infrastructure', 'arctic_technology',
        'arctic_cooperation', 'arctic_governance'
    ]

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
    categories = [
        'arctic_resource', 'arctic_military', 'arctic_shipping',
        'arctic_research', 'arctic_infrastructure', 'arctic_technology',
        'arctic_cooperation', 'arctic_governance'
    ]

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


# ============ 科考站数据 ============

def load_stations():
    """加载科考站数据"""
    path = os.path.join(os.path.dirname(__file__), '..', 'geojson', 'research_stations.geojson')
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


# ============ 地缘博弈网络数据 ============

def load_geopolitics_network():
    """生成大北极国家地缘博弈关系网络数据"""
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

    # 关系: [source, target, relation_type, strength]
    # relation_type: 'cooperation', 'competition', 'confrontation'
    links = [
        {"source": "RUS", "target": "CHN", "relation": "cooperation", "strength": 80, "period": "2018-2024"},
        {"source": "RUS", "target": "USA", "relation": "confrontation", "strength": 95, "period": "2022-2024"},
        {"source": "RUS", "target": "NOR", "relation": "competition", "strength": 70, "period": "2018-2024"},
        {"source": "RUS", "target": "CAN", "relation": "competition", "strength": 65, "period": "2018-2024"},
        {"source": "USA", "target": "CAN", "relation": "cooperation", "strength": 90, "period": "2018-2024"},
        {"source": "USA", "target": "NOR", "relation": "cooperation", "strength": 85, "period": "2018-2024"},
        {"source": "USA", "target": "DNK", "relation": "cooperation", "strength": 80, "period": "2018-2024"},
        {"source": "USA", "target": "CHN", "relation": "confrontation", "strength": 85, "period": "2018-2024"},
        {"source": "CHN", "target": "NOR", "relation": "cooperation", "strength": 65, "period": "2018-2024"},
        {"source": "CHN", "target": "FIN", "relation": "cooperation", "strength": 60, "period": "2018-2024"},
        {"source": "NATO", "target": "USA", "relation": "cooperation", "strength": 95, "period": "2018-2024"},
        {"source": "NATO", "target": "NOR", "relation": "cooperation", "strength": 90, "period": "2018-2024"},
        {"source": "NATO", "target": "DNK", "relation": "cooperation", "strength": 85, "period": "2018-2024"},
        {"source": "NATO", "target": "RUS", "relation": "confrontation", "strength": 95, "period": "2022-2024"},
        {"source": "ARC", "target": "RUS", "relation": "cooperation", "strength": 50, "period": "2018-2021"},
        {"source": "ARC", "target": "USA", "relation": "cooperation", "strength": 70, "period": "2018-2021"},
        {"source": "EU", "target": "DNK", "relation": "cooperation", "strength": 80, "period": "2018-2024"},
        {"source": "EU", "target": "FIN", "relation": "cooperation", "strength": 80, "period": "2018-2024"},
        {"source": "EU", "target": "SWE", "relation": "cooperation", "strength": 75, "period": "2018-2024"},
        {"source": "JPN", "target": "CHN", "relation": "competition", "strength": 60, "period": "2018-2024"},
        {"source": "KOR", "target": "CHN", "relation": "cooperation", "strength": 55, "period": "2018-2024"},
    ]

    return {"nodes": nodes, "links": links}


# ============ 专利技术数据 ============

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
    ]

    return {"nodes": institutions, "links": links}


# ============ 安全风险数据 ============

def load_risk_data():
    """生成北极安全风险评估数据"""
    rng = np.random.RandomState(66)

    regions = [
        {"name": "楚科奇海", "lat": 68, "lon": -172},
        {"name": "白令海峡", "lat": 65, "lon": -168},
        {"name": "东西伯利亚海", "lat": 74, "lon": 150},
        {"name": "拉普捷夫海", "lat": 76, "lon": 125},
        {"name": "喀拉海", "lat": 76, "lon": 70},
        {"name": "巴伦支海", "lat": 74, "lon": 20},
        {"name": "挪威海", "lat": 70, "lon": 5},
        {"name": "格陵兰海", "lat": 72, "lon": -15},
        {"name": "波弗特海", "lat": 74, "lon": -140},
        {"name": "加拿大群岛区", "lat": 76, "lon": -100},
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
                'category': cat,
                'risk_level': min(10, max(1, base + rng.randint(0, 6))),
                'trend': rng.choice(['上升', '稳定', '下降']),
                'main_factors': rng.choice([
                    '大国军事对峙', '极端气候', '环保舆论制约',
                    '航道管辖争议', '技术出口管制', '主权声索冲突'
                ])
            })

    return pd.DataFrame(records)


# ============ SWOT 数据 ============

def get_swot_data():
    """中国北极战略 SWOT 分析数据"""
    return {
        "strengths": [
            ("科研实力", "极地科考体系完善，『雪龙2』实现全年候航行能力"),
            ("资本优势", "北极能源项目投资规模领先，『一带一路』融资体系支撑"),
            ("技术进步", "极地LNG船、破冰船建造技术快速追赶"),
            ("战略视野", "『人类命运共同体』理念提供独特的北极治理观"),
        ],
        "weaknesses": [
            ("距离劣势", "非北极国家，距北极核心区数千公里，投送能力有限"),
            ("制度缺失", "缺乏北极治理机制正式成员资格，话语权不足"),
            ("技术差距", "核动力破冰船、极地通信卫星等领域仍有差距"),
            ("经验不足", "北极航道商业运营经验积累时间较短"),
        ],
        "opportunities": [
            ("航道价值", "气候变化加速航道通航窗口扩大，商业价值凸显"),
            ("合作空间", "科技合作仍是大国北极关系『压舱石』"),
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


# ============ 政策文本数据 ============

def load_policy_texts():
    """各国北极政策文本摘要（用于词云和情感分析）"""
    return {
        "RUS": {
            "name": "俄罗斯",
            "text": "北极战略核心区域国家主权安全航道管控资源开发核动力破冰船北方舰队军事部署能源出口基础设施投资科考站网络环境保护",
            "sentiment": -1.5,
            "key_words": ["主权", "管控", "军事", "能源", "破冰船"]
        },
        "USA": {
            "name": "美国",
            "text": "北极领导力航行自由安全威胁竞争战略国防部部署极地安全倡议气候变化环境保护科研合作盟友协调北极理事会参与",
            "sentiment": -2.0,
            "key_words": ["领导力", "竞争", "安全", "盟友", "航行自由"]
        },
        "CHN": {
            "name": "中国",
            "text": "近北极国家北极利益攸关方冰上丝绸之路人类命运共同体科技合作可持续发展和平利用航道投资能源合作科研交流环境保护共同治理",
            "sentiment": 2.0,
            "key_words": ["合作", "和平", "共同", "科技", "可持续"]
        },
        "NOR": {
            "name": "挪威",
            "text": "巴伦支海合作环境保护可持续渔业资源管理科研合作国际法框架北极理事会积极参与航运安全气候变化应对",
            "sentiment": 1.5,
            "key_words": ["环保", "可持续", "合作", "国际法", "渔业"]
        },
        "CAN": {
            "name": "加拿大",
            "text": "北极主权内水声索西北航道管辖北方居民权益环境保护原住民权利基础设施科研能力气候变化适应",
            "sentiment": -0.5,
            "key_words": ["主权", "管辖", "环保", "居民", "原住民"]
        },
        "DNK": {
            "name": "丹麦",
            "text": "格陵兰自治北极治理领导者北极理事会轮值主席气候变化科学支撑环境保护科研合作国际合作安全议题",
            "sentiment": 1.0,
            "key_words": ["治理", "气候", "科学", "环保", "国际"]
        }
    }


# ============ 趋势计算 ============

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


# ============ 季节统计 ============

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
