"""Check truthful fieldwork preparation, exact exports and private/public isolation.

All saved fixtures live under test-results/research-process; never data/private.
Fixtures are explicitly test plans. Completed records are validated in memory only.
"""
import hashlib
import json
import logging
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
OUT = ROOT / 'test-results/research-process' / uuid4().hex
OUT.mkdir(parents=True, exist_ok=True)
# Keep AppTest's temporary main scripts inside the approved test directory.
os.environ['TMP'] = str(OUT)
os.environ['TEMP'] = str(OUT)
import tempfile
tempfile.tempdir = str(OUT)
import streamlit as st
from streamlit.testing.v1 import AppTest
from src import research_process as process

for name in ['streamlit', 'streamlit.runtime.scriptrunner_utils.script_run_context']:
    logging.getLogger(name).setLevel(logging.ERROR)


def plan(**changes):
    return {**process.template(), 'id': 'test-plan-001', 'question': '自动化测试：能否保存一份待开展的计划？',
            'summary': '仅为测试夹具，不是真实访谈或调研成果。', **changes}


def completed(**changes):
    return plan(**{'status': '已完成', 'activity_date': '2026-01-01',
                   'evidence_reference': 'TEST-ONLY-NO-ACTUAL-INTERVIEW', 'consent': '仅限团队内部整理',
                   'limits': '内存中的校验夹具，不形成真实已完成成果。', **changes})


def private_snapshot():
    folder = ROOT / 'data/private'
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()} if folder.exists() else {}


ORIGINAL_PRIVATE = private_snapshot()


def by_label(items, label):
    return next(item for item in items if item.label == label)


def healthy(app):
    assert not app.exception, [x.message for x in app.exception]


class RecordValidation(unittest.TestCase):
    def test_template_contains_no_completed_work(self):
        blank = process.template()
        self.assertEqual(blank['status'], '计划')
        self.assertEqual(blank['consent'], '尚未征求')
        self.assertFalse(blank['activity_date'])
        self.assertFalse(blank['summary'])
        self.assertFalse(blank['evidence_reference'])
        self.assertFalse(blank['participant_code'])
        with self.assertRaises(ValueError):
            process.validate_record(blank)
        valid = process.validate_record(plan(activity_date='2099-12-31'))
        self.assertEqual(valid['status'], '计划')
        self.assertEqual(valid['activity_date'], '2099-12-31')

    def test_rejects_invalid_shapes_types_and_ids(self):
        invalid = [None, [], 'json text', 123, {**plan(), 'file_path': '../../private'},
                   plan(id='../escape'), plan(id='a/b'), plan(id='C:\\escape'), plan(id='a'),
                   plan(id='a' * 51), plan(kind='不存在的类别'), plan(status='已核实'),
                   plan(consent='默认允许'), plan(question='  '), plan(summary='字' * 10001)]
        for field in process.FIELDS:
            invalid.append({**plan(), field: ['not', 'text']})
            invalid.append({**plan(), field: None})
        for row in invalid:
            with self.subTest(record=repr(row)[:90]):
                with self.assertRaises(ValueError):
                    process.validate_record(row)
        cleaned = process.validate_record(plan(id=' test-trim ', question='  有待核对的问题  '))
        self.assertEqual(cleaned['id'], 'test-trim')
        self.assertEqual(cleaned['question'], '有待核对的问题')

    def test_requires_calendar_date_in_advertised_format(self):
        for invalid in ['20261010', '2026-W41-6', '2026-02-30', '10/10/2026', '2026-10-10T00:00:00']:
            with self.subTest(date=invalid):
                with self.assertRaises(ValueError):
                    process.validate_record(plan(activity_date=invalid))

    def test_completed_requires_actual_material_and_past_date(self):
        process.validate_record(completed())
        for field in ['activity_date', 'summary', 'evidence_reference', 'limits']:
            row = completed()
            row[field] = ''
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    process.validate_record(row)
        with self.assertRaises(ValueError):
            process.validate_record(completed(activity_date='2099-12-31'))

    def test_completed_human_activity_needs_recording_permission(self):
        for kind in ['访谈', '用户试用']:
            row = completed()
            row.update(kind=kind, consent='尚未征求')
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    process.validate_record(row)
        for field in ['summary', 'evidence_reference', 'participant_code']:
            row = plan(summary='', consent='不允许记录或引用')
            row[field] = 'TEST-NO-PERSON'
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    process.validate_record(row)
        process.validate_record(plan(summary='', consent='不允许记录或引用'))


class StorageIsolation(unittest.TestCase):
    def setUp(self):
        self.file = OUT / (self._testMethodName + '.jsonl')
        self.flags = patch.dict(os.environ, {'ARCTIC_ENABLE_LOCAL_REVIEW': '1'})
        self.private = patch.object(process, 'PRIVATE', self.file)
        self.flags.start()
        self.private.start()
        self.addCleanup(self.flags.stop)
        self.addCleanup(self.private.stop)

    def test_local_revisions_append_and_latest_remains_plan(self):
        first = process.save_record(plan())
        second = process.save_record(plan(summary='第二版测试计划：仍未开展任何真实活动。'))
        history = [json.loads(x) for x in self.file.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['summary'], first['summary'])
        self.assertNotEqual(history[0]['summary'], second['summary'])
        self.assertTrue(all(r['status'] == '计划' and r['visibility'] == 'private' for r in history))
        self.assertTrue(all(r['saved_at'] for r in history))
        latest = process.local_records()
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]['summary'], second['summary'])
        exported = [{k: r.get(k, '') for k in process.FIELDS} for r in latest]
        self.assertEqual(process.validate_record(exported[0])['status'], '计划')
        self.assertNotIn('visibility', exported[0])

    def test_public_mode_never_reads_or_writes_private_file(self):
        process.save_record(plan(summary='PRIVATE-TEST-SENTINEL'))
        before = self.file.read_bytes()
        for flag in ['0', '', 'true']:
            with self.subTest(flag=flag), patch.dict(os.environ, {'ARCTIC_ENABLE_LOCAL_REVIEW': flag}):
                self.assertEqual(process.local_records(), [])
                with self.assertRaises(ValueError):
                    process.save_record(plan())
                self.assertEqual(self.file.read_bytes(), before)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(process.local_records(), [])
            with self.assertRaises(ValueError):
                process.save_record(plan())

    def test_paths_cannot_escape_or_target_public_content(self):
        invalid = [ROOT.parent / 'outside-fieldwork-check.jsonl',
                   ROOT / '..' / 'outside-fieldwork-check.jsonl',
                   ROOT / 'src' / 'fieldwork-check.jsonl',
                   ROOT / 'data/reference/fieldwork-check.jsonl',
                   ROOT / 'static' / 'fieldwork-check.jsonl',
                   OUT / 'not-a-jsonl.txt']
        for target in invalid:
            self.assertFalse(target.exists(), f'Test must not touch an existing target: {target}')
            with self.subTest(path=str(target)):
                # Assert rejection before any mutation; deliberately never clean an
                # unexpected public file here because it is evidence of a failed guard.
                with self.assertRaises(ValueError):
                    process.save_record(plan(), target)
                self.assertFalse(target.exists())

    def test_one_corrupt_line_does_not_hide_valid_history(self):
        process.save_record(plan())
        with self.file.open('a', encoding='utf-8') as f:
            f.write('{broken json\n')
        rows = process.local_records()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], 'test-plan-001')


class UserInterface(unittest.TestCase):
    def setUp(self):
        self.file = OUT / (self._testMethodName + '.jsonl')
        self.env = patch.dict(os.environ, {'ARCTIC_ENABLE_LOCAL_REVIEW': '0'})
        self.private = patch.object(process, 'PRIVATE', self.file)
        self.downloads = []
        original = st.download_button
        def capture(label, data, *args, **kwargs):
            self.downloads.append((label, data, args, kwargs))
            return original(label, data, *args, **kwargs)
        self.download_patch = patch.object(st, 'download_button', side_effect=capture)
        self.env.start()
        self.private.start()
        self.download_patch.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.private.stop)
        self.addCleanup(self.download_patch.stop)
        self.app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
        healthy(self.app)
        self.app.switch_page('pages/12_研究过程.py').run()
        healthy(self.app)

    def export(self, label):
        matching = [data for name, data, *_ in self.downloads if name == label]
        self.assertTrue(matching, label)
        payload = matching[-1]
        return json.loads(payload.decode('utf-8') if isinstance(payload, bytes) else payload)

    def submit(self):
        self.downloads.clear()
        by_label(self.app.button, '整理为可下载记录').click().run()
        healthy(self.app)

    def test_all_tabs_public_form_export_and_invalid_reset(self):
        self.assertEqual([t.label for t in self.app.tabs], ['资料与修改记录', '调研记录入口', '待开展的研究'])
        self.assertTrue(any('尚未开展实地调研或访谈' in x.value for x in self.app.info))
        template = self.export('下载空白记录模板 · JSON')
        self.assertEqual(template['status'], '计划')
        self.assertFalse(template['summary'] or template['activity_date'])
        self.assertFalse(any(b.label == '追加保存到本地私有记录' for b in self.app.button))
        self.assertFalse(self.file.exists())
        by_label(self.app.text_input, '记录编号').set_value('test-public-plan')
        by_label(self.app.text_area, '这次活动要回答什么问题').set_value('测试计划：未开展调研。')
        self.submit()
        initial = self.export('下载这份研究记录 · JSON')
        self.assertEqual(initial['id'], 'test-public-plan')
        self.assertEqual(initial['status'], '计划')
        self.assertFalse(initial['activity_date'])
        by_label(self.app.text_area, '这次活动要回答什么问题').set_value('已编辑但尚未重新整理的测试计划。').run()
        self.assertEqual(self.export('下载这份研究记录 · JSON'), initial)
        self.submit()
        self.assertIn('尚未重新整理', self.export('下载这份研究记录 · JSON')['question'])
        by_label(self.app.selectbox, '完成状态').set_value('已完成')
        self.submit()
        self.assertTrue(self.app.error)
        self.assertFalse(any(name == '下载这份研究记录 · JSON' for name, *_ in self.downloads))
        self.assertFalse(self.file.exists())

    def test_import_format_limits_and_exact_download(self):
        good = plan(id='test-import', activity_date='2099-12-31')
        cases = [
            (json.dumps(good, ensure_ascii=False).encode(), None, True),
            (json.dumps([good, {**good, 'id': 'test-import-2'}], ensure_ascii=False).encode(), None, True),
            (b'{bad', None, False),
            (b'null', None, False),
            (b'"not a record"', None, False),
            (b'\xff\xfe', None, False),
            (json.dumps({**good, 'summary': []}).encode(), None, False),
            (json.dumps([good] * 201).encode(), None, False),
            (json.dumps(good).encode(), 1_000_001, False),
        ]
        for payload, size, valid in cases:
            with self.subTest(payload=payload[:30], size=size):
                uploaded = SimpleNamespace(size=size if size is not None else len(payload), getvalue=lambda: payload)
                self.downloads.clear()
                with patch.object(st, 'file_uploader', return_value=uploaded):
                    self.app.run()
                healthy(self.app)
                matches = [x for x in self.downloads if x[0] == '下载检查后的记录']
                self.assertEqual(bool(matches), valid)
                if valid:
                    expected = json.loads(payload)
                    if not isinstance(expected, list):
                        expected = [expected]
                    self.assertEqual(self.export('下载检查后的记录'), [process.validate_record(r) for r in expected])
                    self.assertTrue(all(r['status'] == '计划' for r in expected))
                else:
                    self.assertTrue(self.app.error)
                self.assertFalse(self.file.exists())

    def test_local_save_revision_and_public_visibility(self):
        with patch.dict(os.environ, {'ARCTIC_ENABLE_LOCAL_REVIEW': '1'}):
            self.app.run()
            healthy(self.app)
            by_label(self.app.text_input, '记录编号').set_value('test-local-ui')
            by_label(self.app.text_area, '这次活动要回答什么问题').set_value('UI-PRIVATE-SENTINEL-TEST-PLAN')
            self.submit()
            by_label(self.app.button, '追加保存到本地私有记录').click().run()
            healthy(self.app)
            by_label(self.app.text_area, '记录摘要').set_value('第二版测试计划；未开展活动。')
            self.submit()
            by_label(self.app.button, '追加保存到本地私有记录').click().run()
            healthy(self.app)
            latest = self.export('导出本地记录的最新版本')
            self.assertEqual(len(latest), 1)
            self.assertEqual(latest[0]['summary'], '第二版测试计划；未开展活动。')
            self.assertEqual(latest[0]['status'], '计划')
        history = self.file.read_bytes()
        self.assertEqual(len(history.splitlines()), 2)
        # A separate public session must not expose the local fixture even though
        # the PRIVATE constant still points at the fixture file on disk.
        self.downloads.clear()
        public = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=90).run()
        public.switch_page('pages/12_研究过程.py').run()
        healthy(public)
        self.assertFalse(any(x.label == '追加保存到本地私有记录' for x in public.button))
        self.assertFalse(any(name == '导出本地记录的最新版本' for name, *_ in self.downloads))
        self.assertNotIn('UI-PRIVATE-SENTINEL', str(public))
        self.assertEqual(history, self.file.read_bytes())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    untouched = private_snapshot() == ORIGINAL_PRIVATE
    report = dict(ok=result.wasSuccessful() and untouched, tests_run=result.testsRun,
                  failures=[str(test) for test, _ in result.failures],
                  errors=[str(test) for test, _ in result.errors],
                  actual_private_data_unchanged=untouched,
                  fixture_directory=str(OUT), note='所有落盘夹具均为测试计划，不代表真实调研或访谈。')
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['ok'] else 1)
