"""
北极海冰数据处理模块
处理 NSIDC 海冰范围数据，提供多年均值、趋势分析等可视化数据。
"""

import os
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data', 'processed')

MONTH_ABBR = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
               'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
MONTH_NAMES_CN = ['1月', '2月', '3月', '4月', '5月', '6月',
                    '7月', '8月', '9月', '10月', '11月', '12月']


def _generate_csv():
    """生成海冰数据 CSV，使用确定性算法确保数组长度一致"""
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

    # summary
    df_min = df.min(axis=1)
    df_max = df.max(axis=1)
    df_mean = df.mean(axis=1).round(2)
    pd.DataFrame({'mean': df_mean, 'minimum': df_min, 'maximum': df_max}).to_csv(
        os.path.join(DATA_DIR, 'ice_area_summary.csv'))

    # long format
    long_df = df.reset_index().melt(
        id_vars=['year'], value_vars=MONTH_ABBR,
        var_name='month', value_name='ice_extent'
    )
    long_df['month_num'] = long_df['month'].map({k: i+1 for i, k in enumerate(MONTH_ABBR)})
    long_df.to_csv(os.path.join(DATA_DIR, 'ice_area_long.csv'), index=False)
    return df, pd.DataFrame({'mean': df_mean, 'minimum': df_min, 'maximum': df_max}), long_df


def load_ice_data():
    """加载北极海冰面积数据，优先从 CSV 读取，CSV 不存在则自动生成"""
    csv_path = os.path.join(DATA_DIR, 'ice_area_monthly.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, index_col='year')
    else:
        df, _, _ = _generate_csv()

    df_min = df.min(axis=1)
    df_max = df.max(axis=1)
    df_mean = df.mean(axis=1).round(2)
    df_min.name = 'minimum'
    df_max.name = 'maximum'
    df_mean.name = 'mean'

    df_summary = pd.DataFrame({
        'mean': df_mean,
        'minimum': df_min,
        'maximum': df_max
    })

    long_df = df.reset_index().melt(
        id_vars=['year'],
        value_vars=MONTH_ABBR,
        var_name='month',
        value_name='ice_extent'
    )
    long_df['month_num'] = long_df['month'].map({k: i+1 for i, k in enumerate(MONTH_ABBR)})

    return df, df_summary, long_df


def compute_trend(df_summary: pd.DataFrame) -> dict:
    """计算多年海冰变化趋势"""
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

    total_change = means[-1] - means[0]
    pct_change = (total_change / means[0]) * 100

    return {
        'slope': round(float(slope), 4),
        'intercept': round(float(intercept), 2),
        'r_squared': round(float(r_squared), 4),
        'total_change': round(float(total_change), 2),
        'pct_change': round(float(pct_change), 2),
        'trend': '下降' if slope < 0 else '上升',
        'decline_per_decade': round(float(abs(slope) * 10), 2)
    }


def get_seasonal_stats(long_df: pd.DataFrame) -> pd.DataFrame:
    """计算季节性统计"""
    spring = long_df[long_df['month_num'].isin([3, 4, 5])].groupby('year')['ice_extent'].mean()
    summer = long_df[long_df['month_num'].isin([6, 7, 8])].groupby('year')['ice_extent'].mean()
    autumn = long_df[long_df['month_num'].isin([9, 10, 11])].groupby('year')['ice_extent'].mean()

    # 冬季跨年：12月归入下一年（用"所属冬季年份"作为分组键）
    winter_df = long_df[long_df['month_num'].isin([12, 1, 2])].copy()
    winter_df['winter_year'] = winter_df.apply(
        lambda r: r['year'] if r['month_num'] in [1, 2] else r['year'] + 1, axis=1
    )
    winter = winter_df.groupby('winter_year')['ice_extent'].mean()

    seasons_df = pd.DataFrame({
        '春季(3-5月)': spring,
        '夏季(6-8月)': summer,
        '秋季(9-11月)': autumn,
        '冬季(12-2月)': winter
    })
    seasons_df.index.name = 'year'
    return seasons_df.round(2)
