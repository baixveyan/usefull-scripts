"""Verify generated article coverage, local links and asset containment."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site/dist'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {'src', 'href'}:
                self.links.append(value)


def main():
    manifest = json.loads((ROOT / 'papers/CVPR2026/manifest.json').read_text(encoding='utf-8'))
    done = [r for r in manifest['papers'] if r['status'] == 'reviewed']
    assert len(list((OUT / 'notes').glob('*.html'))) == len(done)
    for r in done:
        assert (OUT / 'notes' / (r['id']+'.html')).exists()
    for path in OUT.rglob('*.html'):
        parser = Links()
        parser.feed(path.read_text(encoding='utf-8'))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            assert target.is_relative_to(OUT.resolve()), (path, link)
            assert target.exists(), (path, link)
    data = (OUT / 'assets/papers.js').read_text(encoding='utf-8')
    records = json.loads(data.removeprefix('window.PAPERS=').removesuffix(';'))
    assert len(records) == manifest['listed_count']
    assert sum(r['reviewed'] for r in records) == len(done)
    assert all(r['href'].startswith('https://openaccess.thecvf.com/') for r in records if not r['reviewed'])
    print(f'Site check PASS: {len(done)} articles, {len(records)} records, all local HTML links contained and present')


if __name__ == '__main__':
    main()
