"""Collect at most five untrusted public repository candidates, never install them."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import ProxyHandler, Request, build_opener, urlopen


def canonical(value):
    if not isinstance(value, str):
        raise ValueError('Repository URL must be text')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or parsed.hostname not in {'github.com', 'gitlab.com'} or parsed.username or parsed.password:
        raise ValueError('Expected public GitHub/GitLab HTTPS repository URL')
    path = parsed.path.rstrip('/')
    if path.endswith('.git'):
        path = path[:-4]
    if len(path.strip('/').split('/')) < 2:
        raise ValueError('Expected namespace/repository path')
    return f'https://{parsed.hostname}{path}'.casefold()


def request_url(provider, query, limit):
    if not query.strip() or len(query) > 256 or not 1 <= limit <= 5:
        raise ValueError('Use nonempty query <=256 characters and limit between 1 and 5')
    if provider == 'github':
        return 'https://api.github.com/search/repositories?' + urlencode(dict(q=query, per_page=limit))
    if provider == 'gitlab':
        return 'https://gitlab.com/api/v4/projects?' + urlencode(dict(search=query, per_page=limit, simple='true', archived='false', order_by='star_count', sort='desc'))
    raise ValueError('Unknown provider')


def known_sources(root):
    known = set()
    catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8-sig'))
    for item in catalog['entries']:
        try:
            known.add(canonical(item.get('source')))
        except ValueError:
            pass
    directory = root / 'maintenance/candidates'
    if directory.exists():
        for path in directory.glob('*.json'):
            previous = json.loads(path.read_text(encoding='utf-8-sig'))
            for item in previous.get('candidates', []):
                known.add(canonical(item['source']))
    return known


def collect(provider, query, limit, known=(), opener=None):
    endpoint = request_url(provider, query, limit)
    request = Request(endpoint, headers={'User-Agent': 'PracticalToolDiscovery/1.0', 'Accept': 'application/json'})
    with (opener or urlopen)(request, timeout=20) as response:
        payload = response.read(2 * 1024 * 1024 + 1)
        if len(payload) > 2 * 1024 * 1024:
            raise ValueError('Unexpectedly large repository metadata response')
        rate_hint = response.headers.get('X-RateLimit-Remaining') or response.headers.get('RateLimit-Remaining')
    raw = json.loads(payload.decode('utf-8'))
    incomplete = bool(raw.get('incomplete_results')) if provider == 'github' else False
    items = raw['items'] if provider == 'github' else raw
    if not isinstance(items, list):
        raise ValueError('Unexpected metadata response')
    seen = set(known)
    candidates = []
    for item in items[:limit]:
        if item.get('archived') or item.get('fork') or item.get('forked_from_project'):
            continue
        source = item['html_url'] if provider == 'github' else item['web_url']
        key = canonical(source)
        if key in seen:
            continue
        seen.add(key)
        license_hint = (item.get('license') or {}).get('spdx_id') if provider == 'github' else None
        if license_hint in {'NOASSERTION', 'OTHER'}:
            license_hint = None
        candidates.append(dict(
            source=source,
            name=str(item.get('full_name') or item.get('path_with_namespace') or '')[:200],
            description=str(item.get('description') or '')[:500],
            stars_hint=int(item.get('stargazers_count') or item.get('star_count') or 0),
            activity_hint=item.get('pushed_at') if provider == 'github' else item.get('last_activity_at'),
            license_hint=license_hint,
            default_branch=item.get('default_branch'),
            state='unreviewed-candidate',
        ))
    return dict(schema_version=1, provider=provider, query=query, request=endpoint,
                untrusted_source_metadata=True, incomplete_results=incomplete,
                remaining_requests_hint=rate_hint, returned_count=min(len(items), limit), candidates=candidates)


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', required=True, choices=['github', 'gitlab'])
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan', action='store_true', help='Print request only; no network or files')
    parser.add_argument('--direct-network', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        endpoint = request_url(args.provider, args.query, args.limit)
        if args.plan:
            print(endpoint)
            return 0
        if args.output and args.output.exists():
            raise ValueError('Output exists; use another file name')
        opener = build_opener(ProxyHandler({})).open if args.direct_network else None
        result = collect(args.provider, args.query, args.limit, known_sources(root), opener)
        result['checked_on'] = args.date.isoformat()
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8', newline='\n') as output:
                output.write(rendered)
            print(f"Saved {len(result['candidates'])} unreviewed candidate(s): {args.output}")
        else:
            print(rendered, end='')
        return 0
    except Exception as exc:
        status = getattr(exc, 'code', None)
        print(f'Discovery failed: {type(exc).__name__}' + (f' HTTP {status}' if status else '') + '; no automatic retry', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
