"""
GDELT 北极事件样本数据
基于 GDELT 格式模拟的北极相关地缘政治事件数据
用于可视化平台演示
"""

import pandas as pd
import numpy as np

np.random.seed(42)

years = list(range(2018, 2025))
countries = ['RUS', 'CHN', 'USA', 'NOR', 'CAN', 'DNK', 'FIN', 'SWE', 'ISL', 'JPN', 'KOR']
categories = [
    'arctic_shipping', 'arctic_resource', 'arctic_technology',
    'arctic_military', 'arctic_cooperation', 'arctic_research',
    'arctic_infrastructure', 'arctic_governance'
]

data_rows = []
for year in years:
    for country in countries:
        for category in categories:
            if np.random.random() < 0.15:
                lat = np.random.uniform(65, 82)
                lon = np.random.uniform(-170, 180)
                count = np.random.randint(1, 25)

                tone_base = 0
                if country == 'CHN':
                    tone_base = 2.5
                elif country == 'RUS':
                    tone_base = 0.5
                elif country == 'USA':
                    tone_base = -2.0
                else:
                    tone_base = 1.0

                if category == 'arctic_military':
                    tone_base -= 3.0
                elif category == 'arctic_cooperation':
                    tone_base += 2.0

                tone = round(tone_base + np.random.uniform(-1, 1), 2)

                data_rows.append({
                    'GlobalEventID': f'{year}{country}{category[:3]}{count:04d}',
                    'Day': f'{year}0101',
                    'Year': year,
                    'Actor1CountryCode': country,
                    'Actor2CountryCode': countries[np.random.randint(0, len(countries))],
                    'ActionGeo_CountryCode': country,
                    'ActionGeo_Lat': round(lat, 2),
                    'ActionGeo_Long': round(lon, 2),
                    'EventCategory': category,
                    'NumArticles': np.random.randint(1, 100),
                    'AvgTone': tone
                })

df = pd.DataFrame(data_rows)
df.to_csv('data/processed/gdelt_arctic_sample.csv', index=False)
print(f"样本数据已生成: {len(df)} 条记录")
print(df.groupby(['Year', 'EventCategory']).size().unstack(fill_value=0))
