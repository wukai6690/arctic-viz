"""
GDELT 数据抓取模块
抓取 http://data.gdeltproject.org/events/index.html 的数据，
按北极相关关键词过滤，并输出为可视化友好的 CSV 格式。
"""

import os
import re
import time
import logging
from datetime import datetime
from typing import Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://data.gdeltproject.org/events"
INDEX_URL = f"{BASE_URL}/index.html"

ARCTIC_KEYWORDS = [
    "arctic", "polar", "north pole", "siberia", "alaska", "northern sea route",
    "northeast passage", "northwest passage", "transpolar", "circumpolar",
    "icebreaker", "ice breaker", "sea ice", "greenland", "svalbard",
    "murmansk", "murmansk", "novaya zemlya", "kara sea", "laptev sea",
    "east siberian sea", "chukchi sea", "beaufort sea",
    "russia arctic", "norway arctic", "canada arctic", "usa arctic",
    "denmark arctic", "finland arctic", "sweden arctic", "iceland arctic",
    "china arctic", "chinese polar", "silk road polar",
    "shipbuilding arctic", "satellite arctic", "lng carrier",
    "yamal", "sabetta", "belkomur", "arctic council",
    "north slope", "prudhoe bay", "barents sea", "pechora sea"
]

EVENT_TYPES = [
    "arctic shipping", "arctic resource", "arctic cooperation",
    "arctic technology", "arctic military", "arctic diplomacy",
    "arctic infrastructure", "arctic research", "arctic governance"
]


class GdeltFetcher:
    """GDELT 数据抓取与处理类"""

    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        })
        os.makedirs(data_dir, exist_ok=True)

    def fetch_index_page(self) -> list[str]:
        """获取 GDELT 事件文件列表"""
        logger.info(f"正在访问 GDELT 索引页面: {INDEX_URL}")
        try:
            resp = self.session.get(INDEX_URL, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.endswith('.export.CSV.zip') or href.endswith('.export.csv'):
                    links.append(href)
            logger.info(f"发现 {len(links)} 个 GDELT 数据文件")
            return links
        except Exception as e:
            logger.error(f"获取索引页面失败: {e}")
            return []

    def fetch_monthly_urls(self, year: int = None, month: int = None) -> list[str]:
        """获取特定年月的数据文件 URL"""
        all_links = self.fetch_index_page()
        if not year:
            return all_links

        filtered = []
        for link in all_links:
            if year:
                year_str = f"{year}0101" if not month else f"{year}{month:02d}01"
                if year_str in link or f"{year}" in link:
                    filtered.append(link)
            else:
                filtered.append(link)
        return filtered

    def parse_gdelt_row(self, line: str) -> Optional[dict]:
        """解析单行 GDELT CSV 数据"""
        fields = line.strip().split('\t')
        if len(fields) < 60:
            return None

        try:
            row = {
                'GlobalEventID': fields[0],
                'Day': fields[1],
                'MonthYear': fields[2],
                'Year': fields[3],
                'FractionDate': fields[4],
                'Actor1Code': fields[5],
                'Actor1Name': fields[6],
                'Actor1CountryCode': fields[7],
                'Actor2Code': fields[8],
                'Actor2Name': fields[9],
                'Actor2CountryCode': fields[10],
                'EventCode': fields[11],
                'EventBaseCode': fields[12],
                'EventRootCode': fields[13],
                'QuadClass': fields[14],
                'GoldsteinScale': fields[15],
                'NumMentions': fields[16],
                'NumSources': fields[17],
                'NumArticles': fields[18],
                'AvgTone': fields[19],
                'Actor1Geo_Type': fields[20],
                'Actor1Geo_FullName': fields[21],
                'Actor1Geo_CountryCode': fields[22],
                'Actor1Geo_Lat': fields[23],
                'Actor1Geo_Long': fields[24],
                'Actor2Geo_Type': fields[25],
                'Actor2Geo_FullName': fields[26],
                'Actor2Geo_CountryCode': fields[27],
                'Actor2Geo_Lat': fields[28],
                'Actor2Geo_Long': fields[29],
                'ActionGeo_Type': fields[30],
                'ActionGeo_FullName': fields[31],
                'ActionGeo_CountryCode': fields[32],
                'ActionGeo_Lat': fields[33],
                'ActionGeo_Long': fields[34],
                'DATEADDED': fields[35],
            }
            return row
        except IndexError:
            return None

    def filter_arctic_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """根据北极关键词过滤事件"""
        if df.empty:
            return df

        search_fields = ['Actor1Name', 'Actor2Name', 'Actor1Geo_FullName',
                         'Actor2Geo_FullName', 'ActionGeo_FullName']

        mask = pd.Series([False] * len(df), index=df.index)
        for kw in ARCTIC_KEYWORDS:
            for field in search_fields:
                if field in df.columns:
                    mask |= df[field].fillna('').str.lower().str.contains(kw, na=False)

        arctic_df = df[mask].copy()

        def classify_event(row):
            text = ' '.join([
                str(row.get('Actor1Name', '')),
                str(row.get('Actor2Name', '')),
                str(row.get('ActionGeo_FullName', ''))
            ]).lower()

            if any(k in text for k in ['shipping', 'route', 'passage', 'navigat', 'vessel', 'ship']):
                return 'arctic_shipping'
            elif any(k in text for k in ['satellite', 'communicat', 'signal', 'gps', 'glonass']):
                return 'arctic_technology'
            elif any(k in text for k in ['military', 'navy', 'army', 'troop', 'exercis', 'warship']):
                return 'arctic_military'
            elif any(k in text for k in ['oil', 'gas', 'resource', 'mine', 'drill', 'lng', 'pipeline']):
                return 'arctic_resource'
            elif any(k in text for k in ['cooperat', 'agreement', 'treaty', 'diplomat', 'council']):
                return 'arctic_cooperation'
            elif any(k in text for k in ['research', 'scientist', 'expedition', 'station', 'study']):
                return 'arctic_research'
            elif any(k in text for k in ['infrastructure', 'port', 'pipeline', 'facility', 'terminal']):
                return 'arctic_infrastructure'
            else:
                return 'arctic_general'

        arctic_df['EventCategory'] = arctic_df.apply(classify_event, axis=1)
        return arctic_df

    def aggregate_by_grid(self, df: pd.DataFrame, grid_size: float = 5.0) -> pd.DataFrame:
        """按经纬度网格聚合事件，便于热力图展示"""
        if df.empty:
            return pd.DataFrame()

        lat_col = 'ActionGeo_Lat'
        lon_col = 'ActionGeo_Long'

        if lat_col not in df.columns or lon_col not in df.columns:
            return df

        df = df.copy()
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
        df = df.dropna(subset=[lat_col, lon_col])

        df['lat_grid'] = (df[lat_col] / grid_size).round() * grid_size
        df['lon_grid'] = (df[lon_col] / grid_size).round() * grid_size

        agg_dict = {
            'GlobalEventID': 'count',
            'EventCategory': lambda x: x.mode().iloc[0] if len(x) > 0 else 'unknown',
            'AvgTone': 'mean',
            'Year': 'first'
        }

        grouped = df.groupby(['lat_grid', 'lon_grid', 'Year']).agg(agg_dict).reset_index()
        grouped.rename(columns={'GlobalEventID': 'EventCount'}, inplace=True)
        grouped['AvgTone'] = grouped['AvgTone'].round(2)
        return grouped

    def aggregate_by_year_country(self, df: pd.DataFrame) -> pd.DataFrame:
        """按年份和国家聚合事件"""
        if df.empty:
            return pd.DataFrame()

        country_col = 'ActionGeo_CountryCode'
        if country_col not in df.columns:
            country_col = 'Actor1CountryCode'

        agg = df.groupby(['Year', country_col]).agg(
            EventCount=('GlobalEventID', 'count'),
            AvgTone=('AvgTone', 'mean')
        ).reset_index()
        agg.rename(columns={country_col: 'CountryCode'}, inplace=True)
        agg['AvgTone'] = agg['AvgTone'].round(2)
        return agg

    def fetch_and_process(
        self,
        year_start: int = 2018,
        year_end: int = 2024,
        use_sample: bool = True
    ) -> dict:
        """
        主处理流程：抓取 GDELT 数据，过滤北极相关事件，输出多个 CSV
        """
        logger.info("=" * 60)
        logger.info("GDELT 北极数据抓取处理流程启动")
        logger.info("=" * 60)

        if use_sample:
            logger.info("使用样本数据模式（实际部署时可切换为完整抓取）")
            sample_file = os.path.join("data", "processed", "gdelt_arctic_sample.csv")
            if os.path.exists(sample_file):
                df = pd.read_csv(sample_file)
                logger.info(f"加载样本数据: {len(df)} 条")
            else:
                logger.warning("样本数据不存在，将返回空结果")
                return {
                    'raw': pd.DataFrame(),
                    'filtered': pd.DataFrame(),
                    'by_grid': pd.DataFrame(),
                    'by_year_country': pd.DataFrame()
                }
        else:
            urls = self.fetch_monthly_urls()
            all_rows = []
            for i, url in enumerate(urls):
                if i >= 50:
                    break
                try:
                    logger.info(f"下载 [{i+1}/{len(urls)}]: {url.split('/')[-1]}")
                    resp = self.session.get(url, timeout=60)
                    resp.raise_for_status()

                    content = resp.content
                    if url.endswith('.zip'):
                        import zipfile, io
                        with zipfile.ZipFile(io.BytesIO(content)) as z:
                            for name in z.namelist():
                                if name.endswith('.csv'):
                                    with z.open(name) as f:
                                        text = f.read().decode('utf-8', errors='ignore')
                                        for line in text.splitlines():
                                            if line.startswith('GLOBALEVENTID'):
                                                continue
                                            row = self.parse_gdelt_row(line)
                                            if row:
                                                all_rows.append(row)
                    else:
                        for line in content.decode('utf-8', errors='ignore').splitlines():
                            if line.startswith('GLOBALEVENTID'):
                                continue
                            row = self.parse_gdelt_row(line)
                            if row:
                                all_rows.append(row)

                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"处理 {url} 失败: {e}")
                    continue

            if not all_rows:
                return {'raw': pd.DataFrame(), 'filtered': pd.DataFrame(),
                        'by_grid': pd.DataFrame(), 'by_year_country': pd.DataFrame()}

            df = pd.DataFrame(all_rows)
            df.to_csv(os.path.join(self.data_dir, "gdelt_raw_all.csv"), index=False)
            logger.info(f"原始数据保存: {len(df)} 条")

        filtered_df = self.filter_arctic_events(df)
        filtered_file = os.path.join("data", "processed", "gdelt_arctic_filtered.csv")
        filtered_df.to_csv(filtered_file, index=False)
        logger.info(f"北极事件过滤结果: {len(filtered_df)} 条 -> {filtered_file}")

        by_grid = self.aggregate_by_grid(filtered_df, grid_size=5.0)
        by_grid_file = os.path.join("data", "processed", "gdelt_arctic_by_grid.csv")
        by_grid.to_csv(by_grid_file, index=False)
        logger.info(f"网格聚合结果: {len(by_grid)} 条 -> {by_grid_file}")

        by_year_country = self.aggregate_by_year_country(filtered_df)
        by_year_country_file = os.path.join("data", "processed", "gdelt_arctic_by_year_country.csv")
        by_year_country.to_csv(by_year_country_file, index=False)
        logger.info(f"年度国家聚合: {len(by_year_country)} 条 -> {by_year_country_file}")

        logger.info("GDELT 数据处理流程完成!")
        return {
            'raw': df,
            'filtered': filtered_df,
            'by_grid': by_grid,
            'by_year_country': by_year_country
        }
