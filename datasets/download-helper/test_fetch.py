import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('dataset_fetch', Path(__file__).with_name('fetch.py'))
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


@contextlib.contextmanager
def sample_root():
    root = Path(__file__).resolve().parent
    directory = root / ('sample-' + uuid.uuid4().hex)
    directory.mkdir()
    try:
        yield directory
    finally:
        if directory.resolve().parent != root:
            raise RuntimeError('Unexpected fixture path')
        for item in directory.iterdir():
            item.unlink()
        directory.rmdir()


def entry():
    return dict(name='sample.bin', url='https://example.com/sample', algorithm='sha256', digest=hashlib.sha256(b'abc').hexdigest())


class FetchTests(unittest.TestCase):
    def test_accept_header_and_https_downgrade(self):
        with sample_root() as root:
            item = entry()
            item['accept'] = 'application/vnd.github.raw+json'
            requests = []
            def opener(request, **kwargs):
                requests.append(request)
                return io.BytesIO(b'abc')
            fetcher.fetch(item, root, opener)
            self.assertEqual(requests[0].get_header('Accept'), item['accept'])
        with sample_root() as root:
            class Downgrade(io.BytesIO):
                def geturl(self):
                    return 'http://example.com/unsafe'
            with self.assertRaises(ValueError):
                fetcher.fetch(entry(), root, lambda *a, **k: Downgrade(b'abc'))
            self.assertEqual(list(root.iterdir()), [])

    def test_success_skip_and_modified_existing(self):
        with sample_root() as root:
            opener = lambda *args, **kwargs: io.BytesIO(b'abc')
            self.assertEqual(fetcher.fetch(entry(), root, opener), 'downloaded-verified')
            self.assertEqual(fetcher.fetch(entry(), root, lambda *a, **k: self.fail('Should not fetch')), 'verified-existing')
            (root / 'sample.bin').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                fetcher.fetch(entry(), root, opener)
            self.assertEqual((root / 'sample.bin').read_bytes(), b'changed')

    def test_bad_checksum_and_limit_clean_partial(self):
        for payload, limit in [(b'wrong', 100), (b'abc', 2)]:
            with self.subTest(payload=payload), sample_root() as root:
                with self.assertRaises(ValueError):
                    fetcher.fetch(entry(), root, lambda *a, **k: io.BytesIO(payload), max_bytes=limit)
                self.assertEqual(list(root.iterdir()), [])

    def test_network_failure_clean_partial(self):
        with sample_root() as root:
            def fail(*args, **kwargs):
                raise OSError('synthetic failure')
            with self.assertRaises(OSError):
                fetcher.fetch(entry(), root, fail)
            self.assertEqual(list(root.iterdir()), [])

    def test_race_does_not_overwrite(self):
        with sample_root() as root:
            original_link = fetcher.os.link
            def race(source, target):
                Path(target).write_bytes(b'another-process')
                return original_link(source, target)
            with patch.object(fetcher.os, 'link', race), self.assertRaises(FileExistsError):
                fetcher.fetch(entry(), root, lambda *a, **k: io.BytesIO(b'abc'))
            self.assertEqual((root / 'sample.bin').read_bytes(), b'another-process')
            self.assertEqual(len(list(root.iterdir())), 1)

    def test_manifest_validation(self):
        for update in [dict(name='../outside'), dict(name='CON.txt'), dict(url='http://example.com'),
                       dict(url='https://user:password@example.com'), dict(digest='bad')]:
            with self.subTest(update=update), sample_root() as root:
                data = entry()
                data.update(update)
                manifest = root / 'manifest.json'
                manifest.write_text(json.dumps(dict(version=1, files=[data])), encoding='utf-8')
                with self.assertRaises(ValueError):
                    fetcher.load_manifest(manifest)

    def test_preview_no_output(self):
        with sample_root() as root:
            output = root / 'not-created'
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps(dict(version=1, files=[entry()])), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fetcher.main([str(manifest), '--output', str(output)]), 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
