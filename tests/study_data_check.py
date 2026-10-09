"""Evidence/coverage invariants, including source-cell reconciliation and review reversal."""
import hashlib,io,json,sys,uuid,zipfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import openpyxl
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'.analysis-deps'))
from src import study_data as d
from scripts.collect_gdelt_history import parse_archive,relevance_terms,FILTER_VERSION

checks=[];data=d.regional_data();frame=d.ice_frame()
review_file=d.DATA/'event_reviews.jsonl';initial_reviews=review_file.read_bytes() if review_file.exists() else None
assert len(frame)==1725 and sum(frame.status=='missing')==6
assert not frame.duplicated(['region_id','year','month']).any()
book=ROOT/'data/analysis/raw/N_Sea_Ice_Index_Regional_Monthly_Data_G02135_v4.0.xlsx'
assert hashlib.sha256(book.read_bytes()).hexdigest()==data['sources'][0]['sha256']
wb=openpyxl.load_workbook(book,data_only=True,read_only=False)
for row in data['records']:
    for metric in ['area','extent']:
        sheet,cell=row[metric+'_cell'].split('!')
        assert wb[sheet][cell].value==row[metric+'_km2'],(row['date'],sheet,cell)
wb.close();checks.append('All 3,450 regional values/missing cells agree with hashed official workbook')
for (rid,month),group in frame.groupby(['region_id','month']):
    for metric in ['extent','area']:
        baseline=group[group.year.between(1991,2020)][metric+'_km2'].dropna()
        assert len(baseline)==30
        assert np.allclose(group[metric+'_baseline_km2'],round(baseline.mean(),3))
        valid=group[group[metric+'_km2'].notna()]
        assert np.allclose(valid[metric+'_anomaly_km2'],(valid[metric+'_km2']-round(baseline.mean(),3)).round(3))
    summary=d.monthly_summary(rid,month,2016,2025)
    expected=group[group.year.between(2016,2025)].set_index('year').extent_km2
    assert summary['n']==10 and summary['low_years']==expected.index[np.isclose(expected,expected.min(),rtol=0,atol=.0005)].tolist()
missing=frame[frame.extent_km2.isna()].iloc[0]
summary=d.monthly_summary(missing.region_id,int(missing.month),int(missing.year),int(missing.year))
assert summary['n']==0 and summary['missing']==1 and summary['min_km2'] is None and summary['low_years']==[]
assert d.monthly_summary('kara',12,2026,2026)['missing']==1
assert d.monthly_summary('kara',9,2026,2026)['n']==1
checks.append('Same-month 30-year baselines; missing/future values never become zeros; minima are data-selected')
from shapely.geometry import shape
for feature in d.region_geometry()['features']:
    geometry=shape(feature['geometry']);assert geometry.is_valid and not geometry.is_empty
    assert -180<=geometry.bounds[0]<=geometry.bounds[2]<=180 and geometry.bounds[1]>55
    for polygon in feature['geometry']['coordinates']:
        for ring in polygon:
            assert all(abs(a[0]-b[0])<=180 for a,b in zip(ring,ring[1:])),feature['properties']['id']
checks.append('Matching NSIDC mask geometry is valid and contains no longitude jumps')
from src.map_geometry import geometry_near_longitude,near_longitude
canonical=d.region_geometry()['features'][2];before=json.dumps(canonical,sort_keys=True)
display=geometry_near_longitude(canonical,-170);bounds=shape(display['geometry']).bounds
assert bounds[2]-bounds[0]<65 and -200<bounds[0]<-170 and -170<bounds[2]<-140
assert json.dumps(canonical,sort_keys=True)==before
assert near_longitude(170,-170)==-190 and near_longitude(-170,170)==190
synthetic={'type':'MultiPolygon','coordinates':[[[[170,65],[180,65],[180,75],[170,75],[170,65]]],[[[-180,65],[-170,65],[-170,75],[-180,75],[-180,65]]]]}
assert shape(geometry_near_longitude(synthetic,-170)).bounds==(-190,65,-170,75)
checks.append('Date-line viewport shifts polygon parts and places without changing canonical coordinates')
assert not relevance_terms('Antarctica Antarctic antarctic-research')
assert 'arctic' in relevance_terms('https://example.org/arctic-research')
assert 'northern sea route' in relevance_terms('https://example.org/northern-sea-route')
def machine_row(i,loc='Barents Sea',lat='72',event='20180920'):
    r=['']*58;r[0]=str(i);r[1]=event;r[29]='1';r[30]='1';r[49]='3';r[50]=loc;r[53]=lat;r[54]='30';r[57]='https://example.org/news';return r
rows=[machine_row(1),machine_row(1),machine_row(2,'Antarctica','-80'),machine_row(3,event='20200920'),['bad']]
memory=io.BytesIO()
with zipfile.ZipFile(memory,'w') as z:z.writestr('test.CSV','\n'.join('\t'.join(r) for r in rows))
parsed,audit=parse_archive(memory.getvalue(),'2019-09-20','source-test')
assert len(parsed)==1 and parsed[0]['date']=='2018-09-20' and parsed[0]['archive_date']=='2019-09-20'
assert audit['quarantine_count']==2 and audit['scanned_rows']==5
checks.append('GDELT word boundaries, source/event date distinction, ID deduplication and quarantine')
raw=ROOT/'data/analysis/raw/gdelt'
for file in (d.DATA/'gdelt/daily').glob('*.json'):
    day=json.loads(file.read_text(encoding='utf-8'));stamp=day['coverage']['archive_date'].replace('-','')
    assert day['source']['filter_version']==FILTER_VERSION
    assert hashlib.sha256((raw/(stamp+'.export.CSV.zip')).read_bytes()).hexdigest()==day['source']['sha256']
assert d.collection_progress()['files']==7
coverage=d.coverage_table(2016,2025)
assert len(coverage)==30 and coverage['GDELT已采集日档'].sum()==21
assert not coverage['GDELT说明'].str.startswith('日档齐全').any()
checks.append('Seven hashed archives never imply full-year or ten-year event coverage')
patents=pd.read_csv(d.DATA/'patent_sample.csv',dtype=str,keep_default_na=False)
family,issues=d.validate_patents(patents)
assert not issues and len(patents)==3 and len(family)==2
assert len(family[pd.to_datetime(family.priority_date).dt.year.between(2016,2025)])==1
duplicate=pd.concat([patents,patents.iloc[[0]]],ignore_index=True)
assert any('重复公开号' in x['原因'] for x in d.validate_patents(duplicate)[1])
bad=patents.copy();bad.loc[0,'priority_date']='2025-01-01'
assert d.validate_patents(bad)[1]
bad=patents.copy();bad.loc[1,'priority_date']='2019-07-06'
assert any('优先权' in x['原因'] for x in d.validate_patents(bad)[1])
checks.append('Patent publications deduplicate to families; earliest priority determines inclusion')
definitions=d.region_definitions();test_dir=ROOT/'test-results'/('review-fixture-'+uuid.uuid4().hex)
test_dir.mkdir(parents=True);(test_dir/'gdelt/daily').mkdir(parents=True)
fixture=[{**parsed[0],'id':'gdelt1:'+str(i)} for i in [1,2]]
(test_dir/'gdelt/daily/2019-09-20.json').write_text(json.dumps({'records':fixture}),encoding='utf-8')
with patch.object(d,'DATA',test_dir),patch.object(d,'region_definitions',return_value=definitions):
    assert len(d.candidates())==2 and not d.verified_events()
    for i in [1,2]:d.save_review('gdelt1:'+str(i),'verified','自动测试人员','测试夹具说明，不是真实项目核验。','test-one-event','2018-09-20','barents','https://example.org/source','仅供测试的事实')
    assert len(d.verified_events())==1 and len(d.verified_events()[0]['candidate_ids'])==2
    try:d.save_review('gdelt1:2','verified','自动测试人员','测试同一编号不应具有不同日期。','test-one-event','2018-09-21','barents','https://example.org/source','测试')
    except ValueError:pass
    else:raise AssertionError('Conflicting event dates were accepted')
    d.save_review('gdelt1:1','excluded','自动测试人员','测试撤销一个错误纳入的记录。')
    assert len(d.verified_events())==1
    d.save_review('gdelt1:2','pending','自动测试人员','测试将另一条记录恢复为待核验。')
    assert not d.verified_events() and len((test_dir/'event_reviews.jsonl').read_text(encoding='utf-8').splitlines())==4
checks.append('Isolated audit fixture: real-event deduplication, conflicting dates rejected, reversals retained')
assert (review_file.read_bytes() if review_file.exists() else None)==initial_reviews,'Test must not alter production reviews'
out=ROOT/'test-results/study';out.mkdir(exist_ok=True,parents=True)
(out/'data-report.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
