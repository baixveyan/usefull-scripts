"""Offline search of the practical tools catalog (Python 3.10+)."""
import argparse
import json
from pathlib import Path
import sys
from build_catalog import CATEGORIES, SUBCATEGORIES


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='*', help='All terms must match; searches metadata only')
    parser.add_argument('--category', choices=['datasets', 'app-helpers', 'booking-helpers', 'everyday'])
    parser.add_argument('--status', choices=['unreviewed', 'documented', 'tested', 'needs-maintenance', 'archived'])
    parser.add_argument('--json', action='store_true', dest='as_json')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    entries = json.loads((args.root / 'catalog.json').read_text(encoding='utf-8-sig'))['entries']
    results = []
    for entry in entries:
        if args.category and entry['category'] != args.category:
            continue
        if args.status and entry['status'] != args.status:
            continue
        metadata = {key: entry[key] for key in ('id', 'title', 'category', 'subcategory', 'languages', 'tags', 'type')}
        metadata['category_label'] = CATEGORIES.get(entry['category'], '')
        metadata['subcategory_label'] = SUBCATEGORIES.get(entry['subcategory'], '')
        searchable = json.dumps(metadata, ensure_ascii=False).casefold()
        if all(term.casefold() in searchable for term in args.query):
            results.append(entry)
    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for entry in results:
            print(f"[{entry['category']}/{entry['subcategory']}] {entry['title']} ({entry['status']})\n  {entry['path']}")
        print(f'{len(results)} result(s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
