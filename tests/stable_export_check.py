"""Same evidence and filters keep one download identity; a changed metric changes it."""
import hashlib,io,json,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.study_views import export_bundle,persisted_study_export
scope={'region':'kara','years':[2016,2025],'month':3}
before=export_bundle(scope,'extent');time.sleep(2.2);after=export_bundle(scope,'extent')
assert before==after,'Identical evidence must not generate a different media URL on rerun'
area=export_bundle(scope,'area');assert area!=before
url=persisted_study_export(scope,'extent')
assert persisted_study_export(scope,'extent')==url
assert (ROOT/'static/exports'/url.rsplit('/',1)[-1]).read_bytes()==before
for data,metric in [(before,'extent'),(area,'area')]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        assert json.loads(z.read('manifest.json'))['metric']==metric
        assert json.loads(z.read('manifest.json'))['scope']==scope
print('Stable export verified:',hashlib.sha256(before).hexdigest())
