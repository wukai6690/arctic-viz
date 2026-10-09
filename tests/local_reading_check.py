"""Verify local reading completeness, source integrity, archives, and place interactions."""
import hashlib,io,json,logging,os,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.chdir(ROOT)
from src.evidence_views import place_catalog
from src.place_profiles import profiles,place_articles,place_bundle
from src.source_library import article_text,source_records,resolve_source,local_file,LIBRARY
from src.research_catalog import research_catalog
from src.study_data import candidates
from streamlit.testing.v1 import AppTest
for name in ['streamlit','streamlit.runtime.scriptrunner_utils.script_run_context']:
    logging.getLogger(name).setLevel(logging.ERROR)
places=place_catalog()['places'];dossiers=profiles();articles=json.loads((LIBRARY/'articles.json').read_text(encoding='utf-8'))
assert len(places)==len(dossiers)==29 and len(articles)==30
assert all(len(article_text(a))>=300 and a['license'] and a['revision_url'] and a['history_url'] for a in articles.values())
assert len(article_text(articles['sabetta']).split('\n\n'))>5,'Normalize Windows line endings before paragraph search'
checks=[]
for p in places:
    d=dossiers[p['id']]
    assert len(d['sections'])==4 and all(len(s['body'])>=45 for s in d['sections']),p['id']
    assert len(d['research_question'])>=40 and d['compare_id'] in dossiers and d['compare_id']!=p['id']
    assert len(p['photos'])>=5,(p['id'],len(p['photos']))
    assert len({x['sha256'] for x in p['photos']})==len(p['photos'])
    assert all(x.get('topic') and x['author'] and x['license'] for x in p['photos'])
    assert place_articles(p['id']),p['id']
    raw=place_bundle(json.dumps(p,ensure_ascii=False),json.dumps(d,ensure_ascii=False),json.dumps(place_articles(p['id']),ensure_ascii=False))
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        assert bundle.testzip() is None
        names=bundle.namelist();assert len([n for n in names if n.startswith('photos/')])==len(p['photos'])
        assert len([n for n in names if n.startswith('readings/')])==len(place_articles(p['id']))
        html=bundle.read('打开地点档案.html').decode('utf-8')
        assert 'src="http' not in html and p['name'] in html
        for photo in p['photos']:
            assert hashlib.sha256(bundle.read('photos/'+Path(photo['src']).name)).hexdigest()==photo['sha256']
        manifest=json.loads(bundle.read('manifest.json'));assert manifest['place']['id']==p['id']
checks.append('29 complete Chinese dossiers and self-contained ZIPs; every image hash and licensed text revision verified')
records=source_records()
for source in research_catalog()['sources']:
    r=resolve_source(source['url']);assert r['kind']=='项目事实导读' and r['summary']
candidate=candidates()[0];r=resolve_source(candidate['source_url'])
assert r['kind']=='候选报道记录' and not article_text(r) and '尚未收录' in r['notice']
try:local_file('../outside.txt',LIBRARY)
except ValueError:pass
else:raise AssertionError('Path traversal accepted')
checks.append('Project facts and unavailable candidate originals are explicitly distinguished; unsafe local paths rejected')
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=45).run()
app.switch_page('pages/1_北极全景地图.py').run()
for p in places:
    app.selectbox(key='atlas_choice').set_value(p['id']).run()
    assert not app.exception,(p['id'],[e.message for e in app.exception])
    assert any(dossiers[p['id']]['lede'] in m.value for m in app.markdown)
    assert app.selectbox(key='atlas_choice').value==p['id']
checks.append('All 29 places actually render with the matching profile after selection')
app.selectbox(key='atlas_choice').set_value('sabetta').run()
app.button(key='atlas-article-sabetta-0').click().run()
assert not app.exception
assert app.selectbox(key='atlas_choice').value=='sabetta'
assert any('Sabetta'==s.value for s in app.subheader)
checks.append('Opening a local source preserves the selected place')
out=ROOT/'test-results/local-reading';out.mkdir(parents=True,exist_ok=True)
report={'places':len(places),'photos':sum(len(p['photos']) for p in places),'articles':len(articles),'checks':checks}
(out/'data-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
