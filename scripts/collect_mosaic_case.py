"""Collect a bounded, reproducible MOSAiC case from PANGAEA and Meereisportal.

No browser-time requests.  Five published 10-minute tracks are retained verbatim.
Ice dates are fixed before collection: voyage endpoints and the 15th of each
complete intervening month.  Failed dates remain missing, never substituted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/analysis/mosaic'
REVIEWED = '2026-10-10'
TRACKS = [(1, '924668'), (2, '924674'), (3, '924681'), (4, '926829'), (5, '926910')]
ICE_DATES = ['2019-09-20'] + [f'2019-{m:02d}-15' for m in range(10, 13)] + [f'2020-{m:02d}-15' for m in range(1, 10)] + ['2020-10-12']
ICE_PAGE = 'https://data.meereisportal.de/relaunch/concentrationmosaic.php?lang=en'
TERMS = 'https://data.meereisportal.de/relaunch/imprint?lang=en'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url, path, refresh=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        return path.read_bytes()
    last = None
    for _ in range(3):
        try:
            response = requests.get(url, timeout=(15, 45), headers={'User-Agent': 'ArcticResearchStudentCase/1.0'})
            response.raise_for_status()
            content = response.content
            if path.suffix == '.tab' and b'Date/Time\tLatitude\tLongitude' not in content:
                raise ValueError('Expected a published PANGAEA tabular file')
            if path.suffix == '.png':
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != 'PNG':
                        raise ValueError('Expected PNG')
                    image.verify()
            path.write_bytes(content)
            return content
        except (requests.RequestException, ValueError, OSError) as exc:
            last = exc
    raise RuntimeError(f'{url}: {type(last).__name__}: {last}')


def source(sid, title, url, summary, locator='', published_at='', **extra):
    return dict(id=sid, title=title, url=url, publisher='AWI / PANGAEA', summary=summary,
                kind='MOSAiC 实证案例', notice='本站中文导读；航迹与冰情保留原始出处、时间及使用条件。',
                locator=locator, published_at=published_at, retrieved_at=REVIEWED, **extra)


def parse_track(path, leg, doi):
    text = path.read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith('Date/Time\tLatitude\tLongitude'))
    table = csv.DictReader(lines[header_index:], delimiter='\t')
    rows = []
    for line_number, row in enumerate(table, header_index + 2):
        stamp = datetime.fromisoformat(row['Date/Time'])
        lat, lon = float(row['Latitude']), float(row['Longitude'])
        if not 50 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f'Unexpected position at {path.name}:{line_number}')
        rows.append(dict(timestamp=stamp.isoformat(timespec='seconds'), latitude=lat,
                         longitude=lon, leg=leg, source_id=f'mosaic-track-{leg}',
                         source_line=line_number))
    if not rows or any(a['timestamp'] >= b['timestamp'] for a, b in zip(rows, rows[1:])):
        raise ValueError(f'Empty or unsorted track: {path.name}')
    citation = next(line.split('\t', 1)[1] for line in lines if line.startswith('Citation:\t'))
    if 'CC-BY-4.0' not in text:
        raise ValueError('Published track licence changed; manual review required')
    return rows, citation


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def collect(refresh=False):
    DATA.mkdir(parents=True, exist_ok=True)
    rows, sources, files = [], [], []
    for leg, doi in TRACKS:
        path = DATA / f'raw/track-leg{leg}.tab'
        url = f'https://doi.pangaea.de/10.1594/PANGAEA.{doi}?format=textfile'
        fetch(url, path, refresh)
        part, citation = parse_track(path, leg, doi)
        rows.extend(part)
        files.append(dict(path=path.relative_to(DATA).as_posix(), url=url, sha256=digest(path),
                          bytes=path.stat().st_size, rows=len(part), license='CC BY 4.0',
                          license_url='https://creativecommons.org/licenses/by/4.0/', citation=citation))
        sources.append(source(f'mosaic-track-{leg}', f'Polarstern PS122/{leg} · 10 分钟航迹',
                              f'https://doi.pangaea.de/10.1594/PANGAEA.{doi}',
                              [f'公开且经处理的导航传感器航迹。本段 {len(part):,} 个船位，覆盖 {part[0]["timestamp"]}—{part[-1]["timestamp"]}。',
                               '含航行和随冰漂流；本站未将船位变化当作主动航速或通航条件。'],
                              'Date/Time、Latitude、Longitude；原表行号保留', citation=citation))
    rows.sort(key=lambda row: row['timestamp'])
    if len({row['timestamp'] for row in rows}) != len(rows):
        raise ValueError('Duplicate timestamps between published legs need review')
    segment, gaps, previous = 0, [], None
    for row in rows:
        stamp = datetime.fromisoformat(row['timestamp'])
        if previous and (stamp - previous).total_seconds() > 3600:
            segment += 1
            gaps.append(dict(start=previous.isoformat(), end=stamp.isoformat(), hours=(stamp - previous).total_seconds()/3600))
        row['segment'] = segment
        previous = stamp
    write_csv(DATA / 'track_10min.csv', rows)
    daily = {}
    route = {}
    for row in rows:
        stamp = datetime.fromisoformat(row['timestamp'])
        day = stamp.date().isoformat()
        noon = stamp.replace(hour=12, minute=0, second=0)
        if day not in daily or abs(stamp-noon) < abs(datetime.fromisoformat(daily[day]['timestamp'])-noon):
            daily[day] = row
        # Retain a real position nearest the start of each 6h bin; never interpolate.
        route.setdefault((day, stamp.hour // 6, row['segment']), row)
    sampled = list(route.values())
    if sampled[-1]['timestamp'] != rows[-1]['timestamp']:
        sampled.append(rows[-1])
    write_json(DATA / 'route_6hour.json', sampled)
    write_csv(DATA / 'daily_positions.csv', list(daily.values()))

    def get_ice(day):
        url = f'https://data.meereisportal.de/maps/iup/regional/MOSAIC/{day[:4]}/thumbs_800/sic_MOSAIC_{day.replace("-", "")}_eng.png'
        path = DATA / f'ice/{day}.png'
        record = dict(date=day, source_id='mosaic-ice', url=url,
                      path=path.relative_to(DATA).as_posix(), product='AMSR2 / ASI sea-ice concentration',
                      grid_km=6.25, projection='EPSG:3411', region='MOSAIC fixed Arctic map frame',
                      license='Meereisportal attributed map reuse; not a Creative Commons licence',
                      license_url=TERMS, attribution='Quelle / Source: meereisportal.de; Alfred-Wegener-Institut and IUP, University of Bremen',
                      citation='Spreen, Kaleschke & Heygster (2008), doi:10.1029/2005JC003384; Grosfeld et al. (2016), doi:10.2312/polfor.2016.011')
        try:
            fetch(url, path, refresh)
            with Image.open(path) as im:
                record.update(width=im.width, height=im.height)
            record.update(status='available', sha256=digest(path), bytes=path.stat().st_size)
        except RuntimeError as exc:
            record.update(status='unavailable', error=str(exc))
        print(day, record['status'], flush=True)
        return record

    with ThreadPoolExecutor(max_workers=3) as executor:
        ice = list(executor.map(get_ice, ICE_DATES))
    write_json(DATA / 'ice_manifest.json', ice)
    sources.extend([
        {**source('mosaic-ice', 'MOSAiC 同期海冰密集度与官方船位图', ICE_PAGE,
                  ['AMSR2 海冰密集度描述像元中的海冰覆盖比例。本站按预先固定日期保存原始官方缩略图，保留图例、署名与日期。',
                   '冰情图标题日期与图内船位时间不是同一字段；官方船位标记有时为次日，须按原图图例读取。灰色无数据区域不等于无冰。'],
                  'Specifications；Description of maps；Terms of use / Citation'), 'publisher':'Meereisportal / AWI / IUP Bremen'},
        {**source('mosaic-map-terms', 'Meereisportal 地图使用条件', TERMS,
                  ['使用处理过的地图须给出所列参考文献或注明 Quelle: meereisportal.de。本站保留完整官方图幅与来源。',
                   '此项地图使用条件不同于照片许可，也不将官方图片重新标为 CC BY。'], 'Copyright；Terms of use'), 'publisher':'Alfred-Wegener-Institut'},
        source('mosaic-open-data', 'MOSAiC 公开数据与引用规则', 'https://mosaic-expedition.org/mosaic-data/',
               ['官方入口指向经处理并带 DOI 的公开数据；原始船载资料和经过整理的数据需要分别识别。',
                '公开数据支持复核具体观测产出，但不能由此推断国家间政治关系改善。'], 'Fully published datasets；FAIR rules'),
        source('mosaic-snow-buoy', '2019S90 雪深浮标 · 实际观测数据', 'https://doi.pangaea.de/10.1594/PANGAEA.925319',
               ['Nicolaus 等记录了 2019-10-11—2019-10-25 的浮标雪深、位置及气象资料；设备包括四路声学雪深测量与 GPS。',
                '本站以该数据集说明具体装备对应何种可查产出，尚未下载或分析其雪深数值。'],
               'Abstract；Parameters；Coverage', '2020-12-02'),
        {**source('mosaic-atmosphere', 'MOSAiC 大气观测 · 设备、机构与产出', 'https://doi.org/10.1525/elementa.2021.00060',
                  ['Shupe 等的观测综述表 B2 对应船载云雷达、激光雷达、微波辐射计及其测量对象与负责机构。',
                   '设备清单支持分工梳理；逐台设备有效运行时间仍需检查对应数据集。'], 'Appendix B, Table B2', '2022'), 'publisher':'Shupe et al. / Elementa'},
        {**source('mosaic-fram-label', '弗拉姆海峡 · 地名参考位置', 'https://www.marineregions.org/gazetteer.php?id=26579&p=details',
                  ['Marine Regions 的 SeaVoX 海区条目列出参考位置 78.658077°N、0.613282°E。本站仅据此放置地名标签。',
                   '条目属于 alternative classification；单个参考点不表示海峡边界，也不用于船位判断或面积统计。'],
                  'MRGID 26579；Latitude / Longitude'), 'publisher':'VLIZ Marine Regions / SeaVoX'}
    ])
    write_json(ROOT / 'data/reference/mosaic_sources.json', sources)
    first = datetime.fromisoformat(rows[0]['timestamp']).date()
    last = datetime.fromisoformat(rows[-1]['timestamp']).date()
    expected = [(first + timedelta(days=i)).isoformat() for i in range((last-first).days+1)]
    manifest = dict(version='mosaic-case-20261010-v1', reviewed_at=REVIEWED,
                    tracks=files, track_rows=len(rows), route_display_rows=len(sampled), daily_rows=len(daily),
                    start=rows[0]['timestamp'], end=rows[-1]['timestamp'], coordinate_system='WGS84 latitude/longitude',
                    time_basis='UTC navigation timestamps; source does not append a timezone suffix',
                    missing_days=[day for day in expected if day not in daily], gaps_over_one_hour=gaps,
                    ice_selection_rule='航次首尾日期与其间每月 15 日；固定 14 日期，不按冰情结果挑选，不用其他日期替换失败日。',
                    ice_requested_dates=ICE_DATES, ice_available=sum(i['status']=='available' for i in ice),
                    map_method='官方 10 分钟点原样合并。日船位选择同日距 12:00 最近的真实记录；地图线取每 6 小时箱的首个真实点，并保留原表行号。大于 1 小时的原始缺口分段，不插值、不补零。',
                    limitations=['日船位代表单个时刻，不能代表日均位置。', '海冰图为同一 AMSR2 产品与固定 Arctic 图幅，不从图片反推数值，也不与本站月度范围/面积相减。',
                                 '船位包含主动航行和随冰漂流；本页不计算通航天数、航行风险、船舶性能或政治效应。',
                                 '冰图中船舶图例可采用与冰情标题不同的时间；与本站 GPS 面板按各自时间阅读。',
                                 '官方说明页与图例对 2020 年 5 月离开浮冰及 6 月返回的日期不一致（16/17 日、17/19 日）；本站阶段说明只取中旬精度，待查航次日志。'],
                    acknowledgements='Sea-ice concentration maps for selected dates from 2019-09-20 to 2020-10-12 are provided by meereisportal.de (REKLIM-2013-04). Data used were produced as part of MOSAiC20192020.')
    write_json(DATA / 'manifest.json', manifest)
    print(json.dumps({k:manifest[k] for k in ['track_rows','route_display_rows','daily_rows','start','end','ice_available','missing_days']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    collect(args.refresh)
