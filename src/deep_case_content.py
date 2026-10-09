"""Content-only case reports, shared by the website and document exports."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_deep_cases():
    return json.loads((ROOT / 'data/reference/deep_cases.json').read_text(encoding='utf-8'))


def get_deep_case(case_id):
    return next((c for c in load_deep_cases()['cases'] if c['id'] == case_id), None)


def case_report_text(case_id):
    """Return a reproducible Chinese report, including source locators and limits."""
    data = load_deep_cases()
    case = next((c for c in data['cases'] if c['id'] == case_id), None)
    if case is None:
        raise ValueError(f'未知案例：{case_id}')
    sources = {s['id']: s for s in data['sources']}
    labels = {sid: i + 1 for i, sid in enumerate(case['source_ids'])}
    def refs(row):
        return ' '.join(f'[{labels[sid]}]' for sid in row.get('source_ids', []))
    scope = case['scope']
    out = [case['title'], case['subtitle'], '', f"资料核对：{data['reviewed_at']} · 版本 {data['version']}",
           '', '研究问题', case['question'], '', '时间、空间与观察单位', scope['label'],
           f"{scope['start']} 至 {scope['end']}", scope['geography'], scope['observation_unit'],
           '', '案例概述', case['summary'], '', '目前能够支持的判断']
    for i, row in enumerate(case['findings'], 1):
        out += [f"{i}. {row['title']}（{row['status']}）", row['text'] + ' ' + refs(row), '边界：' + row['limits'], '']
    out += ['量化事实及统计口径']
    for row in case['metrics']:
        out += [f"{row['label']}：{row['value']} {row['unit']}；{row['period']}。{refs(row)}",
                '含义：' + row['meaning'], '边界：' + row['limits']]
    out += ['', '历史时间线']
    for row in case['timeline']:
        date = row['date'] + (' 至 ' + row['date_end'] if row.get('date_end') else '')
        out += [f"{date} · {row['title']} · {row['date_kind']}（精度：{row['date_precision']}）", row['text'] + ' ' + refs(row)]
    out += ['', '任务、能力、参与方与可观察结果']
    for row in case['comparisons']:
        out += [row['task'] + ' ' + refs(row), '能力：' + row['capability'], '参与方：' + '、'.join(row['actors']),
                '观察结果：' + row['observed_outcome'], '边界：' + row['limits']]
    if case.get('historical_relations'):
        out += ['', '历史股权关系']
        for row in case['historical_relations']:
            out += [f"{row['actor']}：{row['share']}{row['unit']}；{row['period']}。{refs(row)}"]
    out += ['', '机制解释与证据']
    for row in case['mechanism_evidence']:
        out += [row['direction'], row['claim'] + ' ' + refs(row), '已观察：' + row['observed'], '尚未建立：' + row['not_established']]
    out += ['', '替代解释与下一步核对']
    for row in case['alternatives']:
        out += [row['explanation'], '需要核对：' + row['test_needed']]
    out += ['', '资料局限', *['• ' + x for x in case['limits']], '', '中国参与的后续研究问题', *['• ' + x for x in case['china_questions']],
            '', '方法说明', data['methodology'], '', '来源登记']
    for sid in case['source_ids']:
        source = sources[sid]
        out += [f"[{labels[sid]}] {source['title']} · {source['publisher']}",
                f"发表日期：{source['published_at'] or '未核定；不以统计期代替'}；核对日期：{source['retrieved_at']}",
                '定位：' + source['locator'], source['url'], source['notice'], '']
    return '\n'.join(out).rstrip() + '\n'
