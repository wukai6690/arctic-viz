"""Verify published rows, unaltered map files, dates, downloads and empty states."""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.mosaic_research import DATA, TASKS, load_mosaic, mosaic_bundle, track_figure
from scripts.collect_mosaic_case import ICE_DATES


def main():
    data=load_mosaic();manifest=data['manifest']
    processed=list(csv.DictReader((DATA/'track_10min.csv').open(encoding='utf-8-sig')))
    source_rows={}
    for leg,file in enumerate(manifest['tracks'],1):
        path=DATA/file['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==file['sha256']
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        header=next(i for i,line in enumerate(lines) if line.startswith('Date/Time\tLatitude'))
        fields=lines[header].split('\t')
        count=0
        for number,line in enumerate(lines[header+1:],header+2):
            row=dict(zip(fields,line.split('\t')))
            source_rows[(leg,number)]=row;count+=1
        assert count==file['rows']
    assert len(processed)==manifest['track_rows']==len(source_rows)==55793
    for row in processed:
        original=source_rows[(int(row['leg']),int(row['source_line']))]
        assert datetime.fromisoformat(original['Date/Time'])==datetime.fromisoformat(row['timestamp'])
        assert float(original['Latitude'])==float(row['latitude'])
        assert float(original['Longitude'])==float(row['longitude'])
        assert 50<float(row['latitude'])<=90 and -180<=float(row['longitude'])<=180
    assert all(a['timestamp']<b['timestamp'] for a,b in zip(processed,processed[1:]))
    raw_by_timestamp={r['timestamp']:r for r in processed}
    for row in data['route']+data['daily']:
        assert row['timestamp'] in raw_by_timestamp
        original=raw_by_timestamp[row['timestamp']]
        assert float(original['latitude'])==row['latitude'] and float(original['longitude'])==row['longitude']
    for daily in data['daily']:
        day=daily['timestamp'][:10]
        noon=datetime.fromisoformat(day+'T12:00:00')
        rows=[r for r in processed if r['timestamp'].startswith(day)]
        nearest=min(rows,key=lambda r:abs(datetime.fromisoformat(r['timestamp'])-noon))
        assert nearest['timestamp']==daily['timestamp']
    assert len(data['daily'])==389 and manifest['missing_days']==[]
    assert [r['date'] for r in data['ice']]==ICE_DATES
    sizes=set();hashes=set()
    for item in data['ice']:
        assert item['status']=='available'
        assert item['date'].replace('-','') in item['url']
        path=DATA/item['path'];sha=hashlib.sha256(path.read_bytes()).hexdigest()
        assert sha==item['sha256'];hashes.add(sha)
        with Image.open(path) as im:
            im.verify();sizes.add(im.size)
        assert item['grid_km']==6.25 and item['product']=='AMSR2 / ASI sea-ice concentration'
    assert len(hashes)==14
    source_ids={r['id'] for r in data['sources']}
    for task in TASKS:assert set(task['source_ids'])<=source_ids
    for day in ['2019-09-20','2019-10-15','2020-02-15','2020-10-12','2019-09-21']:
        content=mosaic_bundle(day);assert content==mosaic_bundle(day)
        with zipfile.ZipFile(io.BytesIO(content)) as bundle:
            record=json.loads(bundle.read('manifest.json'))
            assert record['selection']=={'day':day}
            rows=list(csv.DictReader(io.StringIO(bundle.read('selected_day_positions.csv').decode('utf-8-sig'))))
            assert rows and all(r['timestamp'].startswith(day) for r in rows)
            assert (f'ice-{day}.png' in bundle.namelist())==(day in ICE_DATES)
        figure=track_figure(day)
        current=next(r for r in data['daily'] if r['timestamp'].startswith(day))
        assert figure.data[-1].lat[0]==current['latitude']
        for trace in figure.data:
            if trace.name=='截至所选时刻':
                assert all(t.replace(' UTC','').replace(' ','T')<=current['timestamp'] for t in trace.text)
    # Keep Streamlit's short-lived generated test script inside this project.
    temp=DATA/'test-runtime';temp.mkdir(exist_ok=True)
    os.environ['TEMP']=str(temp);os.environ['TMP']=str(temp);tempfile.tempdir=str(temp)
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('from src.mosaic_research import render_mosaic_research\nrender_mosaic_research()').run(timeout=30)
    assert not app.exception,list(app.exception)
    app.radio[0].set_value('全部船位日期').run(timeout=30)
    app.select_slider[0].set_value('2019-09-21').run(timeout=30)
    assert not app.exception,list(app.exception)
    assert any('尚未保存同日冰情图' in item.value for item in app.info)
    app.radio[0].set_value('已有同期冰图的日期').run(timeout=30)
    assert not app.exception and app.select_slider[0].value in ICE_DATES
    report=dict(status='passed',raw_positions_reconciled=len(processed),daily_positions_checked=len(data['daily']),
                ice_files_checked=14,image_sizes=sorted(sizes),zip_dates_checked=5,
                source_joins=True,missing_date_ui=True,date_mode_reset=True)
    (DATA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
