"""
可视化工具库 - 提供统一的图表和地图绘制函数
增强版：改善3D地球、热力图、网络图等视觉效果
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import math


# =========================================================================
# 配色方案
# =========================================================================

ARCTIC_THEME = {
    'primary': '#1E88E5',
    'secondary': '#1565C0',
    'accent_red': '#E53935',
    'accent_orange': '#FF6B35',
    'accent_green': '#43A047',
    'accent_purple': '#7B1FA2',
    'ice_blue': '#B3E5FC',
    'arctic_dark': '#0D47A1',
    'bg': '#FFFFFF',
    'grid': '#E0E0E0',
}

COUNTRY_COLORS = {
    'RUS': '#E53935', 'CHN': '#FF0000', 'USA': '#1565C0',
    'NOR': '#FF6B35', 'CAN': '#43A047', 'DNK': '#FFA726',
    'FIN': '#9C27B0', 'SWE': '#00BCD4', 'ISL': '#795548',
    'JPN': '#BCAAA4', 'KOR': '#1E88E5', 'EU': '#003399',
    'NATO': '#008000', 'ARC': '#607D8B'
}

COUNTRY_NAMES = {
    'RUS': '俄罗斯', 'CHN': '中国', 'USA': '美国', 'NOR': '挪威',
    'CAN': '加拿大', 'DNK': '丹麦', 'FIN': '芬兰', 'SWE': '瑞典',
    'ISL': '冰岛', 'JPN': '日本', 'KOR': '韩国', 'EU': '欧盟',
    'NATO': '北约', 'ARC': '北极理事会'
}

CATEGORY_COLORS = {
    'arctic_resource': '#FDD835',
    'arctic_military': '#8E24AA',
    'arctic_shipping': '#FF6B35',
    'arctic_research': '#1E88E5',
    'arctic_infrastructure': '#00BCD4',
    'arctic_technology': '#E53935',
    'arctic_cooperation': '#43A047',
    'arctic_general': '#757575',
    'arctic_governance': '#6D4C41'
}

CAT_LABELS = {
    'arctic_resource': '资源开发',
    'arctic_military': '军事活动',
    'arctic_shipping': '航道航运',
    'arctic_research': '科研活动',
    'arctic_infrastructure': '基础设施',
    'arctic_technology': '技术竞争',
    'arctic_cooperation': '科技合作',
    'arctic_general': '一般事件',
    'arctic_governance': '治理规则'
}

CAT_LABELS_CN = {
    '遥感探测': 'Remote Sensing',
    '冰区船舶': 'Ice-class Ships',
    '油气开采': 'Oil & Gas',
    '冻土工程': 'Permafrost Eng.',
    '气候模拟': 'Climate Modeling',
}


# =========================================================================
# 3D 地球仪（增强版）
# =========================================================================

def create_3d_globe(highlight_arctic=True, height=480):
    """创建北极3D地球模型（增强版：添加更多地理细节）"""
    fig = go.Figure()

    # 北极圈参考圆
    arctic_lons = np.linspace(-180, 180, 180)
    arctic_lats = [66.5] * len(arctic_lons)
    fig.add_trace(go.Scattergeo(
        lon=arctic_lons, lat=arctic_lats,
        mode='lines',
        line=dict(width=1.5, color='#90CAF9', dash='dash'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # 北极区域高亮
    if highlight_arctic:
        theta = np.linspace(0, 2*np.pi, 100)
        r = 0.3
        arctic_hl_lon = 180 * np.cos(theta)
        arctic_hl_lat = 66.5 + 23.5 * np.sin(theta) * r
        fig.add_trace(go.Scattergeo(
            lon=arctic_hl_lon, lat=arctic_hl_lat,
            mode='lines',
            line=dict(width=0, color='rgba(0,0,0,0)'),
            fill='toself',
            fillcolor='rgba(100,180,255,0.12)',
            showlegend=False,
            hoverinfo='skip'
        ))

    # 添加标注点
    annotation_locs = [
        {'lon': 11.93, 'lat': 78.92, 'name': '黄河站(中国)'},
        {'lon': 15.65, 'lat': 78.22, 'name': '新奥勒松(挪威)'},
        {'lon': -133.73, 'lat': 71.32, 'name': 'Utqiagvik(美国)'},
        {'lon': -45.54, 'lat': 71.59, 'name': '北冰洋点'},
        {'lon': 60.0, 'lat': 80.0, 'name': '北极点'},
    ]
    fig.add_trace(go.Scattergeo(
        lon=[loc['lon'] for loc in annotation_locs],
        lat=[loc['lat'] for loc in annotation_locs],
        mode='markers+text',
        marker=dict(size=8, color='#FF6B35', line=dict(width=1, color='white')),
        text=[loc['name'] for loc in annotation_locs],
        textposition='top center',
        textfont=dict(size=8, color='#333333'),
        hovertemplate='%{text}<extra></extra>',
        showlegend=False
    ))

    fig.update_layout(
        geo=dict(
            scope='north america',
            projection_type='azimuthal equal area',
            projection_rotation=dict(lon=0, lat=90),
            center=dict(lat=75, lon=0),
            showland=True,
            landcolor='rgba(230,240,250,0.85)',
            showocean=True,
            oceancolor='rgba(180,220,240,0.5)',
            showlakes=True,
            lakecolor='rgba(180,220,240,0.6)',
            showcountries=True,
            countrycolor='rgba(180,190,200,0.5)',
            showcoastlines=True,
            coastlinecolor='rgba(150,170,190,0.8)',
            coastlinewidth=0.8,
            showframe=False,
            lonaxis_range=[-180, 180],
            lataxis_range=[50, 90],
            bgcolor='rgba(6,9,18,0.85)'
        ),
        paper_bgcolor='rgba(6,9,18,0.85)',
        plot_bgcolor='rgba(6,9,18,0.85)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        showlegend=False
    )
    return fig


def create_3d_globe_annotate(stations_data=None, routes_data=None, events_data=None, height=550):
    """
    创建带标注的北极3D地球（用于展示科考站、航道、事件）
    stations_data: GeoJSON FeatureCollection
    routes_data: GeoJSON FeatureCollection
    events_data: DataFrame with lat, lon, category, count
    """
    fig = go.Figure()

    # 基础底图
    fig.update_layout(
        geo=dict(
            scope='north america',
            projection_type='orthographic',
            projection_rotation=dict(lon=0, lat=90),
            center=dict(lat=75, lon=0),
            showland=True,
            landcolor='rgba(230,240,250,0.9)',
            showocean=True,
            oceancolor='rgba(180,210,240,0.6)',
            showlakes=True,
            lakecolor='rgba(180,220,240,0.7)',
            showcountries=True,
            countrycolor='rgba(160,180,200,0.5)',
            showcoastlines=True,
            coastlinecolor='rgba(140,160,180,0.7)',
            coastlinewidth=0.7,
            showframe=False,
            lonaxis_range=[-180, 180],
            lataxis_range=[55, 90],
            bgcolor='rgba(6,9,18,0.9)'
        ),
        paper_bgcolor='rgba(6,9,18,0.9)',
        plot_bgcolor='rgba(6,9,18,0.9)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        showlegend=True,
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='center', x=0.5,
            bgcolor='rgba(6,9,18,0.85)',
            font=dict(color='rgba(255,255,255,0.9)')
        )
    )

    # 北极圈
    arctic_lons = np.linspace(-180, 180, 180)
    arctic_lats = [66.5] * len(arctic_lons)
    fig.add_trace(go.Scattergeo(
        lon=arctic_lons, lat=arctic_lats,
        mode='lines',
        line=dict(width=1.2, color='#90CAF9', dash='dash'),
        showlegend=True,
        name='北极圈(66.5°N)',
        hoverinfo='skip'
    ))

    # 科考站
    if stations_data and 'features' in stations_data:
        station_colors = {
            '中国': '#FF0000', '美国': '#1565C0', '俄罗斯': '#8B0000',
            '挪威': '#FF6B35', '丹麦': '#FFA726', '芬兰': '#9C27B0',
            '瑞典': '#00BCD4', '冰岛': '#795548', '日本': '#BCAAA4',
            '国际合作（多国）': '#607D8B', '丹麦/美国': '#FFA726', '挪威/国际': '#FF6B35'
        }
        for feat in stations_data['features']:
            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            if not geom or 'coordinates' not in geom:
                continue
            lon, lat = geom['coordinates'][0], geom['coordinates'][1]
            country = props.get('country', '未知')
            name = props.get('name', '未知')
            color = station_colors.get(country, '#757575')
            fig.add_trace(go.Scattergeo(
                lon=[lon], lat=[lat],
                mode='markers+text',
                marker=dict(size=12, color=color, line=dict(width=1.5, color='white'), symbol='circle'),
                text=[name],
                textposition='top center',
                textfont=dict(size=8, color='#333333'),
                hovertemplate=f'<b>{name}</b><br>国家: {country}<br>设立: {props.get("established", "N/A")}<extra></extra>',
                name=f'科考站: {name}',
                showlegend=False
            ))

    # 航道
    if routes_data and 'features' in routes_data:
        route_colors = {
            '东北航道': '#E53935',
            'Northeast Passage': '#E53935',
            '西北航道': '#1565C0',
            'Northwest Passage': '#1565C0',
            '跨极航道': '#43A047',
            'Transpolar': '#43A047',
        }
        for feat in routes_data['features']:
            props = feat.get('properties', {})
            geom = feat.get('geometry', {})
            if not geom or 'coordinates' not in geom:
                continue
            coords = geom['coordinates']
            if geom['type'] == 'LineString':
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                name = props.get('name', props.get('name_en', '航道'))
                color = route_colors.get(name, '#FF6B35')
                fig.add_trace(go.Scattergeo(
                    lon=lons, lat=lats,
                    mode='lines',
                    line=dict(width=2.5, color=color),
                    hoverinfo='text',
                    text=f"<b>{name}</b><br>{props.get('description', '')}",
                    name=f'航道: {name}',
                    showlegend=True
                ))

    # GDELT 事件热力
    if events_data is not None and not events_data.empty:
        try:
            lat_col = 'lat_grid' if 'lat_grid' in events_data.columns else 'lat'
            lon_col = 'lon_grid' if 'lon_grid' in events_data.columns else 'lon'
            fig.add_trace(go.Scattergeo(
                lon=events_data[lon_col].tolist(),
                lat=events_data[lat_col].tolist(),
                mode='markers',
                marker=dict(
                    size=8,
                    color=events_data['EventCount'].tolist() if 'EventCount' in events_data.columns else 5,
                    colorscale='YlOrRd',
                    opacity=0.7,
                    line=dict(width=0)
                ),
                text=events_data['EventCategory'] if 'EventCategory' in events_data.columns else '',
                hovertemplate='%{text}<extra></extra>',
                name='GDELT事件',
                showlegend=True
            ))
        except Exception:
            pass

    return fig


# =========================================================================
# KPI 迷你趋势图
# =========================================================================

def create_metric_trend_chart(data, color="#1E88E5", height=80):
    """创建带趋势线的指标迷你图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(data))),
        y=data,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=4, color=color),
        hovertemplate='%{y:.1f}<extra></extra>'
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        paper_bgcolor='#0f1729',
        plot_bgcolor='#0f1729',
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False, fixedrange=True),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, fixedrange=True),
        hovermode='closest'
    )
    return fig


# =========================================================================
# 雷达图
# =========================================================================

def create_radar_chart(categories, values, title="", color="#1E88E5"):
    """创建雷达图"""
    fig = go.Figure()
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=f'rgba({r},{g},{b},0.2)',
        line=dict(color=color, width=2),
        marker=dict(size=4),
        hovertemplate='%{theta}: %{r}<extra></extra>'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(values)*1.2]),
            angularaxis=dict(tickfont_size=11)
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
        height=300,
        title=dict(text=title, x=0.5, font_size=13)
    )
    return fig


def create_multi_radar(categories, data_dict, title=""):
    """创建多国多维度雷达图"""
    fig = go.Figure()
    colors = ['#FF0000', '#1565C0', '#E53935', '#43A047', '#FF6B35', '#9C27B0']
    for i, (country, values) in enumerate(data_dict.items()):
        r, g, b = int(colors[i % len(colors)][1:3], 16), int(colors[i % len(colors)][3:5], 16), int(colors[i % len(colors)][5:7], 16)
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor=f'rgba({r},{g},{b},0.12)',
            line=dict(color=colors[i % len(colors)], width=2),
            name=country,
            hovertemplate='%{theta}: %{r}<extra></extra>'
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=450,
        margin=dict(l=20, r=20, t=40, b=40),
        title=dict(text=title, x=0.5, font_size=14)
    )
    return fig


# =========================================================================
# 热力图
# =========================================================================

def create_heatmap(data, x_labels, y_labels, title="", colorscale="Blues"):
    """创建热力图"""
    fig = go.Figure(data=go.Heatmap(
        z=data, x=x_labels, y=y_labels,
        colorscale=colorscale,
        colorbar=dict(title=''),
        hovertemplate='%{y} %{x}: %{z:.2f}<extra></extra>'
    ))
    fig.update_layout(
        margin=dict(l=60, r=20, t=40, b=40),
        height=400,
        title=dict(text=title, x=0.5, font_size=14),
        xaxis_title='',
        yaxis_title=''
    )
    return fig


def create_seasonal_heatmap(long_df, year_range=(1990, 2024), color_scheme='Ice'):
    """创建季节-年份热力图"""
    filtered = long_df[(long_df['year'] >= year_range[0]) & (long_df['year'] <= year_range[1])]
    pivot = filtered.pivot_table(values='ice_extent', index='year', columns='month_num', aggfunc='mean')
    month_names = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    if 0 in pivot.columns:
        pivot = pivot.drop(columns=0)
    if all(c in pivot.columns for c in range(1, 13)):
        pivot.columns = [month_names[c-1] for c in pivot.columns]

    colors = {
        'Ice': [[0, '#E3F2FD'], [0.5, '#1E88E5'], [1, '#0D47A1']],
        'YlOrRd': [[0, '#FFFFCC'], [0.5, '#FD8D3C'], [1, '#800026']],
        'Viridis': [[0, '#440154'], [0.5, '#21918C'], [1, '#FDE725']],
    }
    cs = colors.get(color_scheme, colors['Ice'])
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=cs,
        colorbar=dict(title='M km²'),
        hovertemplate='%{y}年 %{x}<br>海冰: %{z:.2f} M km²<extra></extra>'
    ))
    fig.update_layout(
        xaxis_title='月份', yaxis_title='年份',
        height=550, margin=dict(l=60, r=20, t=20, b=40)
    )
    return fig


# =========================================================================
# 气泡图（专利分布）
# =========================================================================

def create_patent_bubble(df, size_col='patent_count', color_col='country', height=400):
    """创建专利气泡图"""
    fig = px.scatter(
        df, x='year', y='category', size=size_col,
        color=color_col,
        hover_name='country',
        color_discrete_map={k: COUNTRY_COLORS.get(k, '#757575') for k in df[color_col].unique()}
    )
    fig.update_layout(
        xaxis_title='年份', yaxis_title='技术类别',
        height=height,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=60, r=20, t=40, b=60)
    )
    return fig


def create_patent_heatmap(df, height=400):
    """创建专利热力图（按国家和类别）"""
    pivot = df.groupby(['country', 'category'])['patent_count'].sum().reset_index()
    pivot_pivot = pivot.pivot(index='country', columns='category', values='patent_count').fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_pivot.values,
        x=pivot_pivot.columns,
        y=pivot_pivot.index,
        colorscale='Purples',
        colorbar=dict(title='专利总数'),
        hovertemplate='%{y} %{x}: %{z}<extra></extra>',
        text=pivot_pivot.values,
        texttemplate='%{z:.0f}',
        textfont=dict(color='white', size=11)
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=120, r=40, t=40, b=40),
        xaxis_title='',
        yaxis_title=''
    )
    return fig


# =========================================================================
# SWOT 可视化（增强）
# =========================================================================

def create_swot_chart(swot_data, height=380):
    """创建SWOT四象限可视化（增强版）"""
    categories = {
        'strengths':     {'label': '优势 S', 'color': '#43A047', 'bg': 'rgba(67,160,71,0.08)',  'x': 0, 'y': 1},
        'weaknesses':    {'label': '劣势 W', 'color': '#E53935', 'bg': 'rgba(229,57,53,0.08)',   'x': 1, 'y': 1},
        'opportunities': {'label': '机会 O', 'color': '#1E88E5', 'bg': 'rgba(30,136,229,0.08)', 'x': 0, 'y': 0},
        'threats':       {'label': '威胁 T', 'color': '#FF6B35', 'bg': 'rgba(255,107,53,0.08)', 'x': 1, 'y': 0},
    }
    fig = go.Figure()

    for key, meta in categories.items():
        items = swot_data[key]
        n = len(items)
        for i, (title, desc) in enumerate(items):
            y_offset = (i - (n-1)/2) * (0.15)
            x_pos = meta['x']
            x_dir = -1 if x_pos == 0 else 1
            x_text = 0.25 if x_pos == 0 else 0.75

            fig.add_annotation(
                x=x_text, y=0.5 + y_offset,
                xref='paper', yref='paper',
                text=f"<b>{title}</b><br><span style='font-size:10px;color:#546E7A'>{desc[:25]}{'...' if len(desc)>25 else ''}</span>",
                showarrow=False,
                align='center',
                bgcolor=meta['bg'],
                bordercolor=meta['color'],
                borderwidth=1.5,
                borderpad=5,
                font=dict(size=11, color='rgba(255,255,255,0.85)'),
                width=220
            )

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[-0.05, 1.05]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#0f1729',
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        shapes=[
            dict(type='rect', x0=0, x1=0.5, y0=0.5, y1=1,
                 fillcolor='rgba(67,160,71,0.06)', line=dict(color='#43A047', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0.5, x1=1, y0=0.5, y1=1,
                 fillcolor='rgba(229,57,53,0.06)', line=dict(color='#E53935', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0, x1=0.5, y0=0, y1=0.5,
                 fillcolor='rgba(30,136,229,0.06)', line=dict(color='#1E88E5', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0.5, x1=1, y0=0, y1=0.5,
                 fillcolor='rgba(255,107,53,0.06)', line=dict(color='#FF6B35', width=2), xref='paper', yref='paper'),
        ],
        annotations=[
            dict(x=0.25, y=0.75, xref='paper', yref='paper', text='<b>优势 S</b>',
                 showarrow=False, font=dict(size=16, color='#43A047')),
            dict(x=0.75, y=0.75, xref='paper', yref='paper', text='<b>劣势 W</b>',
                 showarrow=False, font=dict(size=16, color='#E53935')),
            dict(x=0.25, y=0.25, xref='paper', yref='paper', text='<b>机会 O</b>',
                 showarrow=False, font=dict(size=16, color='#1E88E5')),
            dict(x=0.75, y=0.25, xref='paper', yref='paper', text='<b>威胁 T</b>',
                 showarrow=False, font=dict(size=16, color='#FF6B35')),
        ]
    )
    return fig


# =========================================================================
# 风险矩阵
# =========================================================================

def create_risk_matrix(df, category='all', height=None):
    """创建风险热力图矩阵"""
    if category != 'all':
        df = df[df['category'] == category]
    pivot = df.pivot_table(values='risk_level', index='region', columns='category', aggfunc='mean')

    colorscale = [
        [0.0, '#43A047'], [0.3, '#FDD835'], [0.6, '#FF9800'], [1.0, '#E53935']
    ]
    h = height or max(380, len(pivot) * 45)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=colorscale, zmin=1, zmax=10,
        colorbar=dict(title='风险等级', tickvals=[1, 3, 5, 7, 10],
                      ticktext=['1低', '3', '5中', '7', '10高']),
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>',
        text=pivot.values, texttemplate='%{z:.0f}',
        textfont=dict(color='white', size=13)
    ))
    fig.update_layout(
        margin=dict(l=140, r=40, t=40, b=60),
        height=h, xaxis_title='', yaxis_title=''
    )
    return fig


# =========================================================================
# 时间序列预测图
# =========================================================================

def create_forecast_chart(df_summary, cmip6_df, height=450):
    """创建海冰趋势与CMIP6预测图"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_summary.index, y=df_summary['mean'],
        mode='lines+markers', name='历史年均值',
        line=dict(color='#1E88E5', width=2.5),
        marker=dict(size=5)
    ))
    fig.add_trace(go.Scatter(
        x=df_summary.index, y=df_summary['minimum'],
        mode='lines', name='年度最小值(9月)',
        line=dict(color='#90CAF9', width=1.5, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=cmip6_df['year'], y=cmip6_df['SSP1-2.6'],
        mode='lines+markers', name='SSP1-2.6 (低碳)',
        line=dict(color='#43A047', width=2, dash='dash'),
        marker=dict(symbol='diamond', size=6)
    ))
    fig.add_trace(go.Scatter(
        x=cmip6_df['year'], y=cmip6_df['SSP5-8.5'],
        mode='lines+markers', name='SSP5-8.5 (高排放)',
        line=dict(color='#E53935', width=2, dash='dash'),
        marker=dict(symbol='diamond', size=6)
    ))

    # 2050/2100预测标注
    for yr in [2050, 2100]:
        row = cmip6_df[cmip6_df['year'] == yr]
        if not row.empty:
            val = row['SSP1-2.6'].values[0]
            fig.add_vline(x=yr, line=dict(color='#43A047', width=1, dash='dot'))
            fig.add_annotation(
                x=yr, y=val + 0.5,
                text=f"<b>{yr}年</b><br>{val:.1f}M",
                showarrow=False, font=dict(size=9, color='#43A047')
            )

    fig.update_layout(
        xaxis_title='年份', yaxis_title='海冰面积 (百万平方公里)',
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=height,
        margin=dict(l=60, r=20, t=20, b=40),
        shapes=[dict(type='rect', x0=2024, x1=2100, y0=0, y1=16,
                     fillcolor='rgba(59,130,246,0.08)', line=dict(width=0))]
    )
    return fig


# =========================================================================
# 地理网络图（增强版）
# =========================================================================

def create_network_graph(net_data, title="", height=480, style='circular'):
    """创建地缘博弈关系网络图（增强版：支持多种布局）"""
    nodes = net_data['nodes']
    links = net_data['links']
    edge_colors = {'cooperation': '#43A047', 'competition': '#FF6B35', 'confrontation': '#E53935'}
    edge_dashes = {'cooperation': 'solid', 'competition': 'dash', 'confrontation': 'dot'}

    fig = go.Figure()

    # 计算节点位置
    n = len(nodes)
    if style == 'circular':
        angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
        r = 1.3
        node_x = [r * np.cos(angles[n['id']]) for n in nodes]
        node_y = [r * np.sin(angles[n['id']]) for n in nodes]
    else:
        # 力导向近似布局（按影响力分层）
        node_x, node_y = [], []
        influence_sorted = sorted(nodes, key=lambda x: x['influence'], reverse=True)
        influence_groups = {}
        for i, node in enumerate(influence_sorted):
            tier = min(i // 5, 3)
            influence_groups.setdefault(tier, []).append(node['id'])
        tier_r = {0: 0.4, 1: 0.8, 2: 1.2, 3: 1.6}
        for tier, ids in influence_groups.items():
            n_tier = len(ids)
            for j, nid in enumerate(ids):
                angle = 2 * np.pi * j / n_tier
                r_t = tier_r[tier]
                node_x.append(r_t * np.cos(angle))
                node_y.append(r_t * np.sin(angle))
        node_pos = {nodes[i]['id']: (node_x[i], node_y[i]) for i in range(n)}
        node_x = [node_pos[n['id']][0] for n in nodes]
        node_y = [node_pos[n['id']][1] for n in nodes]

    # 边
    for link in links:
        s, t = link['source'], link['target']
        if style == 'circular':
            if s in angles and t in angles:
                x_s = r * np.cos(angles[s]); y_s = r * np.sin(angles[s])
                x_t = r * np.cos(angles[t]); y_t = r * np.sin(angles[t])
                fig.add_trace(go.Scatter(
                    x=[x_s, x_t], y=[y_s, y_t],
                    mode='lines',
                    line=dict(
                        color=edge_colors.get(link['relation'], '#757575'),
                        width=link['strength'] / 18,
                        dash=edge_dashes.get(link['relation'], 'solid')
                    ),
                    hoverinfo='text',
                    text=f"{COUNTRY_NAMES.get(s, s)} → {COUNTRY_NAMES.get(t, t)}: "
                         f"{link['relation']} ({link['strength']})",
                    showlegend=False
                ))
        else:
            x_s, y_s = node_pos.get(s, (0, 0))
            x_t, y_t = node_pos.get(t, (0, 0))
            fig.add_trace(go.Scatter(
                x=[x_s, x_t], y=[y_s, y_t],
                mode='lines',
                line=dict(
                    color=edge_colors.get(link['relation'], '#757575'),
                    width=link['strength'] / 18,
                    dash=edge_dashes.get(link['relation'], 'solid')
                ),
                hoverinfo='text',
                text=f"{COUNTRY_NAMES.get(s, s)} → {COUNTRY_NAMES.get(t, t)}: "
                     f"{link['relation']} ({link['strength']})",
                showlegend=False
            ))

    # 节点
    node_colors = [n['color'] for n in nodes]
    node_text = [f"{COUNTRY_NAMES.get(n['id'], n['name'])}<br>影响力: {n['influence']}" for n in nodes]
    node_sizes = [14 + n['influence'] / 12 for n in nodes]

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1.5, color='white')),
        text=[COUNTRY_NAMES.get(n['id'], n['name']) for n in nodes],
        textposition='top center',
        textfont=dict(size=9, color='rgba(255,255,255,0.9)'),
        hovertemplate='%{text}<extra></extra>',
        showlegend=False
    ))

    rng = max(abs(max(node_x + node_x)), abs(max(node_y + node_y))) * 1.8
    fig.update_layout(
        title=dict(text=title, x=0.5, font_size=13),
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
        xaxis=dict(visible=False, range=[-rng, rng]),
        yaxis=dict(visible=False, range=[-rng, rng]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='#0f1729',
    )
    return fig


# =========================================================================
# 政策词频图
# =========================================================================

def create_word_freq_chart(policy_texts, height=400):
    """用柱状图展示政策文本关键词词频（使用2字词/3字词分词，避免字符级错误）"""
    # 中文停用词
    stopwords = {
        '的', '和', '与', '在', '为', '了', '对', '及', '是', '等', '以', '或', '中', '北极',
        '国', '家', '主', '权', '的', '和', '与', '一', '不', '在', '有', '个', '人', '这',
        '上', '中', '大', '来', '为', '和', '国', '地', '到', '以', '于', '地', '上', '下',
        '之', '年', '来', '能', '而', '则', '又', '可', '也', '被', '将', '其', '所', '及',
        '从', '当', '会', '要', '对', '进行', '通过', '作为', '具有', '可以', '以及'
    }
    all_words = []
    for code, data in policy_texts.items():
        text = data.get('text', '')
        # 提取2-3字符的词组合（适合中文的简单分词）
        for n in [2, 3]:
            for i in range(len(text) - n + 1):
                word = text[i:i+n]
                if word not in stopwords and not any(c in '，。、；：？！""''（）【】《》·\n\r\t ' for c in word):
                    all_words.append({'word': word, 'country': code, 'count': 1})

    if not all_words:
        return go.Figure()

    word_df = pd.DataFrame(all_words)
    # 取2字符词为主（更准确）
    two_char = word_df[word_df['word'].str.len() == 2]
    three_char = word_df[word_df['word'].str.len() == 3]
    two_counts = two_char.groupby(['word', 'country']).size().reset_index(name='count')
    three_counts = three_char.groupby(['word', 'country']).size().reset_index(name='count')
    # 合并，取各自分组前12个
    two_top = two_counts.sort_values('count', ascending=False).head(12)
    three_top = three_counts.sort_values('count', ascending=False).head(8)
    word_counts = pd.concat([two_top, three_top]).sort_values('count', ascending=False).head(25)

    color_map = {k: COUNTRY_COLORS.get(k, '#757575') for k in word_counts['country'].unique()}
    fig = px.bar(
        word_counts, x='count', y='word',
        color='country', orientation='h',
        color_discrete_map=color_map,
        title=''
    )
    fig.update_layout(
        height=height,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=120, r=20, t=20, b=40),
        yaxis_title='',
        xaxis_title='词频',
        template='plotly_dark',
        font=dict(size=11)
    )
    return fig


# =========================================================================
# 情感分析图
# =========================================================================

def create_sentiment_chart(policy_texts, height=300):
    """创建情感分析对比图"""
    countries = sorted(policy_texts.keys(), key=lambda x: policy_texts[x]['sentiment'])
    sentiments = [policy_texts[c]['sentiment'] for c in countries]
    names = [policy_texts[c]['name'] for c in countries]
    colors = ['#43A047' if s > 0 else '#E53935' for s in sentiments]

    fig = go.Figure(go.Bar(
        x=sentiments, y=names,
        orientation='h',
        marker_color=colors,
        hovertemplate='%{y}: %{x:.2f}<extra></extra>'
    ))
    fig.add_vline(x=0, line_dash='dash', line_color='gray')
    fig.update_layout(
        xaxis_title='情感值 (-10 负面 ~ +10 正面)',
        yaxis_title='国家',
        height=height,
        margin=dict(l=100, r=20, t=20, b=40)
    )
    return fig


# =========================================================================
# 技术-地缘联动双轴图
# =========================================================================

def create_tech_geopolitics_chart(patent_df, gdelt_df=None, height=420):
    """创建技术-地缘双轴联动看板"""
    fig = go.Figure()

    pat_trend = patent_df.groupby('year')['patent_count'].sum()

    fig.add_trace(go.Scatter(
        x=pat_trend.index, y=pat_trend.values,
        mode='lines+markers', name='专利申请量',
        yaxis='y1', line=dict(color='#9C27B0', width=2.5),
        marker=dict(size=6),
        hovertemplate='%{x}年专利: %{y}<extra></extra>'
    ))

    if gdelt_df is not None and not gdelt_df.empty:
        gdelt_trend = gdelt_df.groupby('year')['EventCount'].sum()
        # 只取专利数据年份范围内的GDELT数据
        common_years = sorted(set(pat_trend.index) & set(gdelt_trend.index))
        if common_years:
            fig.add_trace(go.Scatter(
                x=common_years,
                y=[gdelt_trend.get(y, 0) for y in common_years],
                mode='lines+markers', name='GDELT事件数',
                yaxis='y2', line=dict(color='#E53935', width=2),
                marker=dict(symbol='diamond', size=6),
                hovertemplate='%{x}年事件: %{y}<extra></extra>'
            ))

    # 关键时间节点
    for yr, label, color in [
        (2009, '俄北极点海底插旗', '#E53935'),
        (2013, '中国入北极理事会', '#FF0000'),
        (2017, '冰上丝绸之路', '#FF6B35'),
        (2022, '俄乌冲突', '#8B0000'),
    ]:
        fig.add_vline(x=yr, line=dict(color=color, width=1, dash='dot'))
        fig.add_annotation(
            x=yr, y=max(pat_trend.values) * 0.95,
            text=label, showarrow=False, font=dict(size=8, color=color),
            textangle=-30, yshift=5
        )

    fig.update_layout(
        xaxis=dict(title='年份'),
        yaxis=dict(title='专利申请量', side='left', showgrid=True, gridcolor='rgba(255,255,255,0.06)'),
        yaxis2=dict(title='GDELT事件数', side='right', overlaying='y', showgrid=False),
        template='plotly_dark', hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=height, margin=dict(l=60, r=60, t=20, b=40)
    )
    return fig


# =========================================================================
# 通用布局更新
# =========================================================================

def finalize_layout(fig, title="", height=400, legend_pos='bottom'):
    """统一图表布局"""
    leg_pos = dict(
        bottom=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        right=dict(orientation='v', yanchor='top', y=1, xanchor='right', x=1.02)
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font_size=14),
        template='plotly_dark',
        height=height,
        legend=leg_pos.get(legend_pos, leg_pos['bottom']),
        margin=dict(l=60, r=20, t=40, b=40)
    )
    return fig
