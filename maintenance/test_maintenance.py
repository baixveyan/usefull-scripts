import contextlib
import io
import json
from pathlib import Path
import shutil
import unittest
import uuid

import build_catalog
import search_catalog
from validate_catalog import validate


@contextlib.contextmanager
def repository():
    parent = Path(__file__).resolve().parent
    root = parent / ('catalog-sample-' + uuid.uuid4().hex)
    root.mkdir()
    (root / 'docs').mkdir()
    (root / 'app-helpers/demo').mkdir(parents=True)
    for path in ('README.md', 'docs/taxonomy.md', 'docs/catalog.md', 'app-helpers/demo/README.md'):
        (root / path).write_text('# Synthetic sample\n', encoding='utf-8')
    entries = [dict(id='demo', title='演示工具', path='app-helpers/demo/README.md',
                    category='app-helpers', subcategory='translation', type='guide',
                    languages=['Markdown'], tags=['demo'], status='documented', source=None,
                    upstream_license=None, upstream_ref=None, upstream_commit=None,
                    checked_on='2026-10-19', validation='synthetic fixture only')]
    def save():
        (root / 'catalog.json').write_text(json.dumps(dict(schema_version=1, entries=entries), ensure_ascii=False), encoding='utf-8')
    save()
    try:
        yield root, entries, save
    finally:
        if root.resolve().parent != parent or not root.name.startswith('catalog-sample-'):
            raise RuntimeError('Unexpected fixture root')
        shutil.rmtree(root)


class MaintenanceTests(unittest.TestCase):
    def test_valid_index_and_missing_field(self):
        with repository() as (root, entries, save):
            self.assertEqual(validate(root), [])
            del entries[0]['validation']
            save()
            self.assertTrue(any('Missing fields' in error for error in validate(root)))

    def test_duplicate_ids_and_escaping_path(self):
        with repository() as (root, entries, save):
            entries.append(entries[0].copy())
            save()
            self.assertTrue(any('Duplicate id' in error for error in validate(root)))
            entries.pop()
            entries[0]['path'] = '../outside.md'
            save()
            self.assertTrue(any('escapes repository' in error for error in validate(root)))

    def test_missing_and_malformed_links(self):
        with repository() as (root, entries, save):
            (root / 'README.md').write_text('[missing](absent.md)\n[bad](https://[)\n', encoding='utf-8')
            errors = validate(root)
            self.assertTrue(any('absent.md' in error for error in errors))
            self.assertTrue(any('malformed link' in error for error in errors))

    def test_generation_is_deterministic_and_escapes_title(self):
        with repository() as (root, entries, save):
            entries[0]['title'] = '标题 | [link]\nnext'
            first = build_catalog.render(entries)
            self.assertEqual(first, build_catalog.render(list(reversed(entries))))
            self.assertIn(r'\|', first)
            self.assertIn(r'\[link\]', first)
            self.assertNotIn('标题 | [link]\n', first)

    def test_generator_preserves_unmarked_document(self):
        with repository() as (root, entries, save):
            target = root / 'docs/catalog.md'
            original = target.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(build_catalog.main(['--root', str(root), '--write']), 2)
                self.assertEqual(target.read_bytes(), original)
                target.write_text(build_catalog.HEADER + '\n# old\n', encoding='utf-8')
                self.assertEqual(build_catalog.main(['--root', str(root), '--write']), 0)
                self.assertEqual(build_catalog.main(['--root', str(root), '--check']), 0)

    def test_chinese_search_and_status_filter(self):
        with repository() as (root, entries, save):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(search_catalog.main(['翻译', '--root', str(root), '--json']), 0)
            self.assertEqual(len(json.loads(output.getvalue())), 1)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                search_catalog.main(['--status', 'tested', '--root', str(root), '--json'])
            self.assertEqual(json.loads(output.getvalue()), [])


if __name__ == '__main__':
    unittest.main()
