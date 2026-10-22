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
    revision = json.loads((ROOT / 'papers/CVPR2026/method-revision.json').read_text(encoding='utf-8'))
    entries = revision['items']
    by_id = {r['id']: r for r in done}
    assert len(entries) == len({r['id'] for r in entries}) == len(done)
    assert {r['id'] for r in entries} == set(by_id), 'Revision queue must cover every existing note'
    sources = {r['file']: r for r in json.loads((ROOT / 'site/figures/sources.json').read_text(encoding='utf-8'))}
    for item in entries:
        record = by_id[item['id']]
        assert item['note_path'] == record['note_path']
        assert item['status'] in {'pending', 'completed'}
        assert item['figure_status'] in {'pending', 'completed'}
        assert item['status'] == record['method_revision'], item['id']
        assert item['figure_status'] == record['figure_revision'], item['id']
        if item['figure_status'] == 'completed':
            figure = ROOT / item['figure_file']
            assert figure.resolve().is_relative_to((ROOT / 'site/figures').resolve())
            assert figure.is_file() and figure.name in sources
            assert figure.name in (ROOT / item['note_path']).read_text(encoding='utf-8')
            assert sources[figure.name]['pdf_sha256'] == record['pdf_sha256']
            assert item['figure_checked_on'] and item['figure_validation']
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
    joint = sum(r['status'] == r['figure_status'] == 'completed' for r in entries)
    assert sum(r['revised'] for r in records) == joint
    print(f'Site check PASS: {len(done)} articles, {len(records)} records, all local HTML links contained and present')
    print(f'Revision consistency PASS: {joint}/{len(entries)} methods and figures completed together')


if __name__ == '__main__':
    main()
