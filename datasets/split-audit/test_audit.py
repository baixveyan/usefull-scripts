import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import uuid

spec = importlib.util.spec_from_file_location('split_audit', Path(__file__).with_name('audit.py'))
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


@contextlib.contextmanager
def samples():
    parent = Path(__file__).resolve().parent
    root = parent / ('sample-' + uuid.uuid4().hex)
    root.mkdir()
    try:
        yield root
    finally:
        if root.resolve().parent != parent:
            raise RuntimeError('Unexpected fixture root')
        for path in root.iterdir():
            path.unlink()
        root.rmdir()


class AuditTests(unittest.TestCase):
    def test_disjoint_with_repeated_within_split(self):
        result = audit.report({'train': audit.Split(3, {'1', '2'}), 'test': audit.Split(2, {'3'})})
        self.assertFalse(result['group_overlap_detected'])
        self.assertEqual(result['splits']['train'], dict(rows=3, unique_groups=2))

    def test_all_pairs_and_no_identifiers(self):
        result = audit.report({'train': audit.Split(1, {'private-user'}),
                               'val': audit.Split(1, {'another-user'}),
                               'test': audit.Split(1, {'private-user'})})
        self.assertTrue(result['group_overlap_detected'])
        self.assertEqual(len(result['pairs']), 3)
        self.assertEqual(sum(pair['overlapping_groups'] for pair in result['pairs']), 1)
        self.assertNotIn('private-user', json.dumps(result))

    def test_csv_bom_whitespace_leading_zero(self):
        with samples() as root:
            file = root / 'data.csv'
            file.write_text('\ufeffsubject_id,value\n 001 ,a\n001,b\n1,c\n', encoding='utf-8')
            result = audit.read_ids(file)
            self.assertEqual(result.rows, 3)
            self.assertEqual(result.ids, {'001', '1'})

    def test_lines_and_csv_have_same_group_count(self):
        with samples() as root:
            file = root / 'data.txt'
            file.write_text(' 1 \n2\n1\n', encoding='utf-8')
            result = audit.read_ids(file, 'lines')
            self.assertEqual((result.rows, result.ids), (3, {'1', '2'}))

    def test_reject_missing_empty_or_malformed_csv(self):
        for value in ['wrong\n1\n', 'subject_id\n', 'subject_id\n""\n',
                      'subject_id,value\n1\n', 'subject_id,value\n1,x,extra\n',
                      'subject_id,subject_id\n1,2\n']:
            with self.subTest(value=value), samples() as root:
                file = root / 'data.csv'
                file.write_text(value, encoding='utf-8')
                with self.assertRaises(ValueError):
                    audit.read_ids(file)

    def test_cli_exit_statuses(self):
        with samples() as root:
            train, test = root / 'train.txt', root / 'test.txt'
            train.write_text('1\n2\n', encoding='utf-8')
            test.write_text('3\n', encoding='utf-8')
            args = ['--format', 'lines', '--split', f'train={train}', '--split', f'test={test}']
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(audit.main(args), 0)
                test.write_text('2\n', encoding='utf-8')
                self.assertEqual(audit.main(args), 1)
                self.assertEqual(audit.main(args + ['--split', f'test={test}']), 2)


if __name__ == '__main__':
    unittest.main()
