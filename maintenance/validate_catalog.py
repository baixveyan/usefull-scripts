"""Read-only validation of catalog metadata and local Markdown links."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

CATEGORIES = {'datasets', 'app-helpers', 'booking-helpers', 'everyday'}
STATUSES = {'unreviewed', 'documented', 'tested', 'needs-maintenance', 'archived'}
TYPES = {'guide', 'script', 'browser-extension', 'userscript', 'cli', 'desktop-app', 'web-app'}
REQUIRED = {'id', 'title', 'path', 'category', 'subcategory', 'type', 'languages', 'tags',
            'status', 'source', 'upstream_license', 'upstream_ref', 'upstream_commit', 'checked_on', 'validation'}


def within(root: Path, relative: str) -> Path:
    if not relative or '\\' in relative or ':' in relative:
        raise ValueError('Expected repository-relative slash path')
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError('Path escapes repository')
    return path


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8-sig'))
        if not isinstance(catalog, dict) or catalog.get('schema_version') != 1:
            raise ValueError('Unsupported catalog schema')
        entries = catalog.get('entries')
        if not isinstance(entries, list):
            raise ValueError('entries must be a list')
    except (OSError, ValueError) as exc:
        return [f'catalog.json: {exc}']
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    markdown = {root / 'README.md', root / 'docs/taxonomy.md', root / 'docs/catalog.md'}
    for number, entry in enumerate(entries, 1):
        label = f'entry {number}'
        try:
            if not isinstance(entry, dict):
                raise ValueError('Entry must be an object')
            missing = REQUIRED - entry.keys()
            if missing:
                raise ValueError('Missing fields: ' + ', '.join(sorted(missing)))
            label = str(entry['id'])
            if not isinstance(entry['id'], str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', entry['id']):
                raise ValueError('Invalid id')
            for key in ('title', 'subcategory', 'validation'):
                if not isinstance(entry[key], str) or not entry[key].strip():
                    raise ValueError(f'{key} must be nonempty text')
            if entry['id'] in seen_ids:
                raise ValueError('Duplicate id')
            seen_ids.add(entry['id'])
            if entry['category'] not in CATEGORIES or entry['status'] not in STATUSES or entry['type'] not in TYPES:
                raise ValueError('Invalid category, status or type')
            for key in ('languages', 'tags'):
                if not isinstance(entry[key], list) or not entry[key] or not all(isinstance(value, str) and value.strip() for value in entry[key]):
                    raise ValueError(f'{key} must be a nonempty list of text')
            date.fromisoformat(entry['checked_on'])
            if not isinstance(entry['path'], str):
                raise ValueError('path must be text')
            path = within(root, entry['path'])
            normalized = str(path).casefold()
            if normalized in seen_paths:
                raise ValueError('Duplicate entry path')
            seen_paths.add(normalized)
            if not path.is_file():
                raise ValueError('Entry file does not exist')
            if path.suffix.lower() == '.md':
                markdown.add(path)
            source = entry['source']
            if source is not None:
                if not isinstance(source, str) or urlsplit(source).scheme not in ('http', 'https') or not urlsplit(source).netloc:
                    raise ValueError('source must be HTTP(S) URL or null')
        except (TypeError, ValueError, OSError) as exc:
            errors.append(f'{label}: {exc}')
    for document in sorted(markdown):
        if not document.is_file():
            errors.append(f'Missing navigation document: {document.relative_to(root)}')
            continue
        # Deliberately handles simple inline links; not a complete Markdown parser.
        try:
            content = re.sub(r'```.*?```', '', document.read_text(encoding='utf-8-sig'), flags=re.S)
        except (OSError, UnicodeError) as exc:
            errors.append(f'{document.relative_to(root)}: cannot read Markdown ({type(exc).__name__})')
            continue
        for target in re.findall(r'\]\(([^\s)]+)\)', content):
            try:
                scheme = urlsplit(target).scheme
            except ValueError:
                errors.append(f'{document.relative_to(root)}: malformed link target')
                continue
            if target.startswith('#') or scheme:
                continue
            path_text = unquote(target.split('#', 1)[0])
            destination = (document.parent / path_text).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f'{document.relative_to(root)}: missing or external local target {target}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print('ERROR:', error)
    print(f'Catalog validation: {"FAIL" if errors else "PASS"}')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
