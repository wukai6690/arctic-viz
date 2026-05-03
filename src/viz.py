"""
可视化工具库 - 提供统一的图表和地图绘制函数
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


# ============ 配色方案 ============

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


# ============ 3D 地球仪 ============

def create_3d_globe(highlight_arctic=True):
    """创建北极3D地球模型"""
    fig = go.Figure()

    # 大陆轮廓数据（简化的经纬度边界）
    continents = {
        'Eurasia': {
            'lons': [-10, 30, 60, 90, 120, 140, 180, 140, 100, 60, 30, 0, -10],
            'lats': [35, 45, 55, 65, 70, 65, 70, 75, 70, 65, 55, 45, 35]
        },
        'North America': {
            'lons': [-170, -140, -100, -80, -60, -90, -120, -140, -170],
            'lats': [60, 70, 65, 55, 45, 30, 50, 60, 60]
        },
        'Greenland': {
            'lons': [-50, -30, -20, -40, -50, -60, -50],
            'lats': [60, 75, 80, 70, 65, 60, 60]
        }
    }

    for name, data in continents.items():
        fig.add_trace(go.Scattergeo(
            lon=data['lons'], lat=data['lats'],
            mode='lines',
            line=dict(width=1.5, color='#B0BEC5'),
            fill='toself',
            fillcolor='rgba(200,220,240,0.3)',
            showlegend=False,
            hoverinfo='skip'
        ))

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

    # 如果需要高亮北极区域
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
            fillcolor='rgba(100,180,255,0.15)',
            showlegend=False,
            hoverinfo='skip'
        ))

    fig.update_layout(
        geo=dict(
            scope='north america',
            projection_type='azimuthal equal area',
            projection_rotation=dict(lon=0, lat=90),
            center=dict(lat=75, lon=0),
            showland=True,
            landcolor='rgba(230,240,250,0.8)',
            showocean=True,
            oceancolor='rgba(180,220,240,0.5)',
            showlakes=True,
            lakecolor='rgba(180,220,240,0.6)',
            showcountries=True,
            countrycolor='rgba(180,190,200,0.6)',
            showcoastlines=True,
            coastlinecolor='rgba(150,170,190,0.8)',
            coastlinewidth=0.8,
            showframe=False,
            showgraticule=True,
            graticulecolor='rgba(200,210,220,0.3)',
            lonaxis_range=[-180, 180],
            lataxis_range=[50, 90],
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        showlegend=False
    )

    return fig


# ============ 指标卡片图 ============

def create_metric_trend_chart(data, labels, title="", color="#1E88E5"):
    """创建带趋势线的指标迷你图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(data))),
        y=data,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=5),
        hovertemplate='%{y:.1f}<extra></extra>'
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=80,
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest'
    )
    return fig


# ============ 南北极战略竞争态势雷达图 ============

def create_radar_chart(categories, values, title="", color="#1E88E5"):
    """创建雷达图"""
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.2)',
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


# ============ 热力图 ============

def create_heatmap(data, x_labels, y_labels, title="", colorscale="Blues"):
    """创建热力图"""
    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=x_labels,
        y=y_labels,
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


# ============ 气泡图（专利分布） ============

def create_patent_bubble(df, size_col='patent_count', color_col='country'):
    """创建专利气泡图"""
    fig = px.scatter(
        df, x='year', y='category', size=size_col,
        color=color_col,
        hover_name='country',
        color_discrete_map={k: COUNTRY_COLORS.get(k, '#757575') for k in df[color_col].unique()}
    )
    fig.update_layout(
        xaxis_title='年份',
        yaxis_title='技术类别',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=60, r=20, t=40, b=60)
    )
    return fig


# ============ SWOT 可视化 ============

def create_swot_chart(swot_data):
    """创建SWOT四象限可视化"""
    categories = {
        'strengths': {'label': '优势 S', 'color': '#43A047', 'x': 1, 'y': 1},
        'weaknesses': {'label': '劣势 W', 'color': '#E53935', 'x': 0, 'y': 1},
        'opportunities': {'label': '机会 O', 'color': '#1E88E5', 'x': 1, 'y': 0},
        'threats': {'label': '威胁 T', 'color': '#FF6B35', 'x': 0, 'y': 0},
    }

    fig = go.Figure()

    for key, meta in categories.items():
        items = swot_data[key]
        y_base = meta['y']
        x_pos = meta['x']

        for i, (title, desc) in enumerate(items):
            offset = (i - len(items)/2) * 0.2
            if x_pos == 1:
                x_text = 1.15 + (i % 2) * 0.3
            else:
                x_text = -0.15 - (i % 2) * 0.3

            fig.add_annotation(
                x=x_pos, y=y_base + offset,
                xref='paper', yref='paper',
                text=f"<b>{title}</b><br><span style='font-size:10px'>{desc[:20]}...</span>",
                showarrow=False,
                align='left' if x_pos == 1 else 'right',
                bgcolor=f"rgba{tuple(list(int(meta['color'][i:i+2], 16) for i in [1,3,5]) + [20])}",
                bordercolor=meta['color'],
                borderwidth=1,
                borderpad=4,
                font=dict(size=10),
                width=200
            )

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.5, 1.5]),
        yaxis=dict(visible=False, range=[-0.5, 1.5]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        shapes=[
            dict(type='rect', x0=0, x1=0.5, y0=0.5, y1=1, fillcolor='rgba(67,160,71,0.08)',
                 line=dict(color='#43A047', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0.5, x1=1, y0=0.5, y1=1, fillcolor='rgba(229,57,53,0.08)',
                 line=dict(color='#E53935', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0, x1=0.5, y0=0, y1=0.5, fillcolor='rgba(30,136,229,0.08)',
                 line=dict(color='#1E88E5', width=2), xref='paper', yref='paper'),
            dict(type='rect', x0=0.5, x1=1, y0=0, y1=0.5, fillcolor='rgba(255,107,53,0.08)',
                 line=dict(color='#FF6B35', width=2), xref='paper', yref='paper'),
        ],
        annotations=[
            dict(x=0.25, y=0.75, xref='paper', yref='paper', text='<b>优势 S</b>',
                 showarrow=False, font=dict(size=14, color='#43A047')),
            dict(x=0.75, y=0.75, xref='paper', yref='paper', text='<b>劣势 W</b>',
                 showarrow=False, font=dict(size=14, color='#E53935')),
            dict(x=0.25, y=0.25, xref='paper', yref='paper', text='<b>机会 O</b>',
                 showarrow=False, font=dict(size=14, color='#1E88E5')),
            dict(x=0.75, y=0.25, xref='paper', yref='paper', text='<b>威胁 T</b>',
                 showarrow=False, font=dict(size=14, color='#FF6B35')),
        ]
    )
    return fig


# ============ 风险矩阵 ============

def create_risk_matrix(df, category='all'):
    """创建风险热力图矩阵"""
    if category != 'all':
        df = df[df['category'] == category]

    pivot = df.pivot_table(
        values='risk_level',
        index='region',
        columns='category',
        aggfunc='mean'
    )

    colorscale = [
        [0.0, '#43A047'],   # 绿
        [0.3, '#FDD835'],  # 黄
        [0.6, '#FF9800'],  # 橙
        [1.0, '#E53935']   # 红
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=colorscale,
        zmin=1, zmax=10,
        colorbar=dict(title='风险等级', tickvals=[1, 3, 5, 7, 10],
                      ticktext=['1低', '3', '5中', '7', '10高']),
        hovertemplate='%{y} %{x}: %{z:.0f}<extra></extra>'
    ))

    fig.update_layout(
        margin=dict(l=120, r=40, t=40, b=60),
        height=max(350, len(pivot) * 40),
        xaxis_title='',
        yaxis_title=''
    )
    return fig


# ============ 时间序列预测图 ============

def create_forecast_chart(df_summary, cmip6_df):
    """创建海冰趋势与CMIP6预测图"""
    fig = go.Figure()

    # 历史数据
    fig.add_trace(go.Scatter(
        x=df_summary.index, y=df_summary['mean'],
        mode='lines+markers', name='历史年均值',
        line=dict(color='#1E88E5', width=2.5),
        marker=dict(size=5)
    ))

    # 9月最小值
    fig.add_trace(go.Scatter(
        x=df_summary.index, y=df_summary['minimum'],
        mode='lines', name='年度最小值(9月)',
        line=dict(color='#90CAF9', width=1.5, dash='dot')
    ))

    # CMIP6 SSP1-2.6
    fig.add_trace(go.Scatter(
        x=cmip6_df['year'], y=cmip6_df['SSP1-2.6'],
        mode='lines+markers', name='SSP1-2.6 (低碳)',
        line=dict(color='#43A047', width=2, dash='dash'),
        marker=dict(symbol='diamond', size=6)
    ))

    # CMIP6 SSP5-8.5
    fig.add_trace(go.Scatter(
        x=cmip6_df['year'], y=cmip6_df['SSP5-8.5'],
        mode='lines+markers', name='SSP5-8.5 (高排放)',
        line=dict(color='#E53935', width=2, dash='dash'),
        marker=dict(symbol='diamond', size=6)
    ))

    # 2050和2100预测标注
    for yr, col in [(2050, 'SSP1-2.6'), (2100, 'SSP1-2.6')]:
        row = cmip6_df[cmip6_df['year'] == yr]
        if not row.empty:
            fig.add_vline(x=yr, line=dict(color='#43A047', width=1, dash='dot'))
            fig.add_annotation(x=yr, y=cmip6_df[cmip6_df['year']==2050]['SSP1-2.6'].values[0] if yr == 2050 else cmip6_df[cmip6_df['year']==2100]['SSP1-2.6'].values[0],
                             text=f"{yr}年", showarrow=False, yshift=10, font=dict(size=9, color='#43A047'))

    fig.update_layout(
        xaxis_title='年份',
        yaxis_title='海冰面积 (百万平方公里)',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=450,
        margin=dict(l=60, r=20, t=20, b=40),
        shapes=[dict(type='rect', x0=2024, x1=2100, y0=0, y1=16,
                     fillcolor='rgba(200,220,255,0.15)', line=dict(width=0))]
    )
    return fig


# ============ 地理网络图 ============

def create_network_graph(net_data, title=""):
    """创建地缘博弈关系网络图"""
    nodes = net_data['nodes']
    links = net_data['links']

    edge_colors = {'cooperation': '#43A047', 'competition': '#FF6B35', 'confrontation': '#E53935'}
    edge_dashes = {'cooperation': 'solid', 'competition': 'dash', 'confrontation': 'dot'}

    edge_x, edge_y = [], []
    node_map = {n['id']: (i, n) for i, n in enumerate(nodes)}

    for link in links:
        if link['source'] in node_map and link['target'] in node_map:
            i_s = node_map[link['source']][0]
            i_t = node_map[link['target']][0]
            n_s = node_map[link['source']][1]
            n_t = node_map[link['target']][1]

            # 简单布局：圆形排列
            n = len(nodes)
            angles = {n['id']: 2 * np.pi * i / n for i, n in enumerate(nodes)}
            r = 1

            x_s = r * np.cos(angles[link['source']])
            y_s = r * np.sin(angles[link['source']])
            x_t = r * np.cos(angles[link['target']])
            y_t = r * np.sin(angles[link['target']])

            edge_x.extend([x_s, x_t, None])
            edge_y.extend([y_s, y_t, None])

    fig = go.Figure()

    # 边
    for link in links:
        if link['source'] in node_map and link['target'] in node_map:
            n = len(nodes)
            angles = {n['id']: 2 * np.pi * i / n for i, n in enumerate(nodes)}
            r = 1
            x_s = r * np.cos(angles[link['source']])
            y_s = r * np.sin(angles[link['source']])
            x_t = r * np.cos(angles[link['target']])
            y_t = r * np.sin(angles[link['target']])

            fig.add_trace(go.Scatter(
                x=[x_s, x_t], y=[y_s, y_t],
                mode='lines',
                line=dict(
                    color=edge_colors.get(link['relation'], '#757575'),
                    width=link['strength'] / 20,
                    dash=edge_dashes.get(link['relation'], 'solid')
                ),
                hoverinfo='text',
                text=f"{link['source']}-{link['target']}: {link['relation']} ({link['strength']})",
                showlegend=False
            ))

    # 节点
    n = len(nodes)
    angles = {nodes[i]['id']: 2 * np.pi * i / n for i in range(n)}
    r = 1

    node_x = [r * np.cos(angles[n['id']]) for n in nodes]
    node_y = [r * np.sin(angles[n['id']]) for n in nodes]
    node_colors = [n['color'] for n in nodes]
    node_text = [f"{n['name']}<br>影响力: {n['influence']}" for n in nodes]
    node_sizes = [15 + n['influence'] / 10 for n in nodes]

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1, color='white')),
        text=[n['name'] for n in nodes],
        textposition='outside',
        textfont=dict(size=9),
        hovertemplate='%{text}<extra></extra>',
        showlegend=False
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, font_size=13),
        margin=dict(l=20, r=20, t=40, b=20),
        height=450,
        xaxis=dict(visible=False, range=[-1.8, 1.8]),
        yaxis=dict(visible=False, range=[-1.8, 1.8]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig


# ============ 政策词云（用柱状图模拟） ============

def create_word_freq_chart(policy_texts):
    """用柱状图展示政策文本关键词词频"""
    all_words = []
    stopwords = set(['的', '和', '与', '在', '为', '了', '对', '及', '是', '等', '以', '或', '中', '北极'])

    for code, data in policy_texts.items():
        words = list(data['text'])
        for w in words:
            if w not in stopwords and len(w) > 1:
                all_words.append({'word': w, 'country': code, 'count': 1})

    if not all_words:
        return go.Figure()

    word_df = pd.DataFrame(all_words)
    word_counts = word_df.groupby(['word', 'country']).size().reset_index(name='count')
    word_counts = word_counts.sort_values('count', ascending=False).head(20)

    fig = px.bar(
        word_counts, x='count', y='word',
        color='country', orientation='h',
        color_discrete_map={k: COUNTRY_COLORS.get(k, '#757575') for k in word_counts['country'].unique()}
    )
    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        margin=dict(l=120, r=20, t=40, b=40),
        yaxis_title='',
        xaxis_title='词频'
    )
    return fig


# ============ 通用布局更新 ============

def finalize_layout(fig, title="", height=400, legend_pos='bottom'):
    """统一图表布局"""
    leg_pos = dict(
        bottom=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        right=dict(orientation='v', yanchor='top', y=1, xanchor='right', x=1.02)
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font_size=14),
        template='plotly_white',
        height=height,
        legend=leg_pos.get(legend_pos, leg_pos['bottom']),
        margin=dict(l=60, r=20, t=40, b=40)
    )
    return fig
