"""Validate evidence joins, time scope and non-interchangeable quantities."""
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.deep_case_content import case_report_text, get_deep_case, load_deep_cases


def main():
    data = load_deep_cases()
    sources = {s['id']: s for s in data['sources']}
    projects = {p['id'] for p in json.loads((ROOT / 'data/reference/research.json').read_text(encoding='utf-8'))['projects']}
    assert len(sources) == len(data['sources'])
    assert {c['id'] for c in data['cases']} == {'asbm', 'yamal'}
    for s in sources.values():
        assert all(k in s for k in ('id', 'url', 'title', 'publisher', 'summary', 'kind', 'notice', 'locator', 'published_at', 'retrieved_at'))
        assert s['url'].startswith('https://') and isinstance(s['summary'], list)
        date.fromisoformat(s['retrieved_at'])
        if s['published_at']:
            date.fromisoformat(s['published_at'])
    def check_refs(value, collected):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'source_ids':
                    assert child and set(child) <= sources.keys(), child
                    collected.update(child)
                else:
                    check_refs(child, collected)
        elif isinstance(value, list):
            for child in value:
                check_refs(child, collected)
    for c in data['cases']:
        assert c['project_id'] in projects
        used = set()
        check_refs({k: v for k, v in c.items() if k != 'source_ids'}, used)
        assert used == set(c['source_ids'])
        for section in ['findings', 'metrics', 'timeline', 'comparisons', 'mechanism_evidence']:
            assert c[section] and all(row['source_ids'] for row in c[section])
        for row in c['timeline']:
            assert re.fullmatch(r'\d{4}-\d{2}(-\d{2})?', row['date'])
            assert len(row['date']) == (7 if row['date_precision'] == 'month' else 10)
            assert c['scope']['start'][:len(row['date'])] <= row['date'] <= c['scope']['end'][:len(row['date'])]
            assert row['date_kind']
        for m in c['metrics']:
            assert isinstance(m['value'], (int, float)) and m['meaning'] and m['limits']
            if 'raw_value' in m:
                assert abs(m['value'] - m['raw_value'] * m['scale']) < 1e-8
        report = case_report_text(c['id'])
        assert report == case_report_text(c['id'])
        assert all(sources[sid]['url'] in report for sid in c['source_ids'])
        assert all(text in report for text in c['limits'])
        assert all(row['limits'] in report for row in c['metrics'])
    asbm = get_deep_case('asbm')
    timeline = {row['id']: row for row in asbm['timeline']}
    assert timeline['asbm-t4']['date'] == '2024-10'  # No invented handover day.
    assert timeline['asbm-t5']['date'] == '2024-10-17'
    assert '商业' in asbm['findings'][2]['text'] and '预期' in asbm['findings'][2]['text']
    yamal = get_deep_case('yamal')
    metrics = {m['id']: m for m in yamal['metrics']}
    assert metrics['yamal-cargoes']['unit'] == '船货'
    assert metrics['yamal-shipped-rounded']['value'] == 840
    assert metrics['yamal-shipped-precise']['value'] == 836
    assert metrics['yamal-produced']['value'] == 860
    assert (date(2018, 7, 17) - date(2018, 6, 25)).days != metrics['yamal-net-days']['value']
    assert round(sum(x['share'] for x in yamal['historical_relations']), 1) == 100
    media = json.loads((ROOT / 'data/reference/project_media.json').read_text(encoding='utf-8'))
    places = json.loads((ROOT / 'data/reference/places.json').read_text(encoding='utf-8'))['places']
    for c in data['cases']:
        for suggestion in c['media_suggestions']:
            rows = media[suggestion['project_id']] if suggestion['collection'] == 'project_media' else next(p['photos'] for p in places if p['id'] == suggestion['place_id'])
            assert suggestion['photo_id'] in {str(p['id']) for p in rows}
    spec = importlib.util.spec_from_file_location('case_builder', ROOT / 'scripts/build_deep_cases.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build() == data, 'Frozen JSON differs from authoring source'
    raw = json.loads((ROOT / 'data/analysis/case_sources/facts.json').read_text(encoding='utf-8'))
    assert raw['sources'] == data['sources']
    for case in raw['cases']:
        original = get_deep_case(case['id'])
        assert case['metrics'] == original['metrics'] and case['timeline'] == original['timeline']
    try:
        case_report_text('missing')
    except ValueError:
        pass
    else:
        raise AssertionError('Unknown case accepted')
    print(json.dumps(dict(ok=True, cases=len(data['cases']), sources=len(sources),
                          timeline_nodes=sum(len(c['timeline']) for c in data['cases']),
                          metrics=sum(len(c['metrics']) for c in data['cases'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
