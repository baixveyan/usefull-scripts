"""Parse a saved official CVF listing; never fetch or execute external code."""
import argparse
from datetime import date
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / 'papers' / 'CVPR2026'


def parse_listing(text):
    rows = []
    seen = set()
    for block in text.split('<dt class="ptitle">')[1:]:
        match = re.search(r'<a href="([^"]+)">(.*?)</a>', block, re.S)
        if not match:
            raise ValueError('Missing title link')
        url = urljoin('https://openaccess.thecvf.com', html.unescape(match[1]))
        if not url.startswith('https://openaccess.thecvf.com/content/CVPR2026/html/'):
            raise ValueError('Unexpected conference or URL')
        if url in seen:
            raise ValueError('Duplicate paper URL')
        seen.add(url)
        pdf = re.search(r'href="([^"]+\.pdf)"[^>]*>pdf</a>', block)
        if not pdf:
            raise ValueError('Missing PDF')
        rows.append(dict(id=Path(url).stem, title=html.unescape(re.sub('<[^>]+>', '', match[2])).strip(),
                         authors=[html.unescape(x) for x in re.findall(r'name="query_author" value="([^"]+)"', block)],
                         url=url, pdf=urljoin(url, html.unescape(pdf[1])), status='queued',
                         topic='unclassified', note_path=None, checked_on=None))
    if not rows:
        raise ValueError('Empty listing')
    return sorted(rows, key=lambda r: (r['title'].casefold(), r['id']))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('html', type=Path)
    p.add_argument('--checked-on', required=True, type=date.fromisoformat, help='actual listing retrieval date YYYY-MM-DD')
    p.add_argument('--write', action='store_true', help='save metadata, preserving existing paper states')
    args = p.parse_args()
    data = args.html.read_bytes()
    rows = parse_listing(data.decode('utf-8'))
    destination = COLLECTION / 'manifest.json'
    if destination.exists():
        old = json.loads(destination.read_text(encoding='utf-8'))
        previous = {r['id']: r for r in old['papers']}
        missing = set(previous) - {r['id'] for r in rows}
        if missing:
            raise ValueError('Listing lost existing papers; review manually before replacing')
        for r in rows:
            if r['id'] in previous:
                r.update({k: v for k, v in previous[r['id']].items()
                          if k not in {'id', 'title', 'authors', 'url', 'pdf'}})
    result = dict(schema_version=1, conference='CVPR2026', scope='CVF main conference; excludes workshops and findings',
                  source='https://openaccess.thecvf.com/CVPR2026?day=all', checked_on=args.checked_on.isoformat(),
                  listing_sha256=hashlib.sha256(data).hexdigest(), official_accepted_count=4089,
                  listed_count=len(rows), count_discrepancy=4089-len(rows), papers=rows)
    print(f'{len(rows)} unique main-conference papers; {sum(r["status"] == "reviewed" for r in rows)} reviewed notes')
    if args.write:
        COLLECTION.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
