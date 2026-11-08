import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import uuid

spec = importlib.util.spec_from_file_location('folder_snapshot', Path(__file__).with_name('snapshot.py'))
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


@contextlib.contextmanager
def samples():
    parent = Path(__file__).resolve().parent
    root = parent / ('sample-' + uuid.uuid4().hex)
    root.mkdir()
    try:
        yield root
    finally:
        if root.resolve().parent != parent:
            raise RuntimeError('Unexpected sample path')
        shutil.rmtree(root)


class SnapshotTests(unittest.TestCase):
    def populate(self, root):
        (root / 'nested/sub').mkdir(parents=True)
        (root / 'empty').mkdir()
        (root / 'root.txt').write_bytes(b'123')
        (root / 'nested/a.bin').write_bytes(b'12345')
        (root / 'nested/sub/b.bin').write_bytes(b'1234567')

    def test_totals_groups_and_top(self):
        with samples() as root:
            self.populate(root)
            result = snapshot.scan(root, top=2)
            self.assertEqual((result['total_bytes'], result['total_files']), (15, 3))
            self.assertEqual(result['root_files'], dict(bytes=3, files=1))
            self.assertEqual(result['groups']['nested'], dict(bytes=12, files=2))
            self.assertEqual(result['groups']['empty'], dict(bytes=0, files=0))
            self.assertEqual([value['bytes'] for value in result['largest_files']], [7, 5])

    def test_exclude_and_no_file_contents_read(self):
        with samples() as root:
            self.populate(root)
            with patch.object(Path, 'open', side_effect=AssertionError('Content read forbidden')):
                result = snapshot.scan(root, excludes=['nested'])
            self.assertEqual(result['total_bytes'], 3)
            self.assertEqual(result['skipped_entries'], 1)

    def test_compare_added_removed_and_changed(self):
        with samples() as root:
            self.populate(root)
            before = snapshot.scan(root)
            (root / 'nested/a.bin').unlink()
            (root / 'new').mkdir()
            (root / 'new/a').write_bytes(b'x' * 10)
            after = snapshot.scan(root)
            result = snapshot.compare(before, after)
            self.assertEqual(result['total_bytes_delta'], 5)
            self.assertEqual(result['total_files_delta'], 0)
            self.assertEqual(result['folders'][0]['folder'], 'new')
            after['excluded_names'] = ['different']
            with self.assertRaises(ValueError):
                snapshot.compare(before, after)

    def test_partial_scan_reports_failure(self):
        with samples() as root:
            with patch.object(snapshot.os, 'scandir', side_effect=PermissionError('synthetic denial')):
                result = snapshot.scan(root)
            self.assertTrue(result['partial'])
            self.assertEqual(result['errors'][0]['error'], 'PermissionError')

    def test_cli_output_guard_and_refuse_overwrite(self):
        with samples() as root:
            self.populate(root)
            output = root.parent / ('snapshot-' + uuid.uuid4().hex + '.json')
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(snapshot.main(['scan', str(root), '--output', str(root / 'bad.json')]), 2)
                    self.assertEqual(snapshot.main(['scan', str(root), '--output', str(output)]), 0)
                    original = output.read_bytes()
                    self.assertEqual(snapshot.main(['scan', str(root), '--output', str(output)]), 2)
                    self.assertEqual(output.read_bytes(), original)
            finally:
                output.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
