"""Small HTTP/proxy diagnostic; no persistent settings changes, no response bodies."""
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener, getproxies, urlopen


def target_info(value):
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError('Whitespace/control characters in URL')
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Expected HTTP(S) URL without embedded credentials')
    return dict(scheme=parsed.scheme, host=parsed.hostname,
                port=parsed.port or (443 if parsed.scheme == 'https' else 80))


def proxy_summary(proxies):
    result = {}
    for protocol in ('http', 'https', 'all'):
        if not proxies.get(protocol):
            continue
        try:
            value = proxies[protocol]
            parsed = urlsplit(value if '://' in value else 'http://' + value)
            result[protocol] = dict(scheme=parsed.scheme, host=parsed.hostname, port=parsed.port,
                                    credentials_present=bool(parsed.username or parsed.password))
        except (TypeError, ValueError):
            result[protocol] = dict(configured=True, parseable=False)
    return result


def probe(url, timeout, opener=None):
    target_info(url)
    request = Request(url, method='HEAD', headers={'User-Agent': 'PracticalNetworkCheck/1.0'})
    try:
        with (opener or urlopen)(request, timeout=timeout) as response:
            status = response.status
            return dict(http_response_received=True, successful_status=200 <= status < 400,
                        status=status, final_host=urlsplit(response.geturl()).hostname)
    except HTTPError as exc:
        status = exc.code
        exc.close()
        return dict(http_response_received=True, successful_status=False, status=status, error_type='HTTPError')
    except Exception as exc:
        reason = exc.reason if isinstance(exc, URLError) else exc
        return dict(http_response_received=False, successful_status=False, error_type=type(reason).__name__)


def diagnose(urls, timeout=8, compare_direct=False, default_opener=None, direct_opener=None, proxies=None):
    if not 1 <= len(urls) <= 5 or not 1 <= timeout <= 30:
        raise ValueError('Use 1–5 URLs and timeout 1–30 seconds')
    targets = [target_info(url) for url in urls]
    report = dict(schema_version=1, proxies=proxy_summary(getproxies() if proxies is None else proxies),
                  compared_direct=compare_direct, endpoints=[])
    direct = direct_opener
    if compare_direct and direct is None:
        direct = build_opener(ProxyHandler({})).open
    for index, (url, target) in enumerate(zip(urls, targets), 1):
        item = dict(endpoint=index, target=target, system_path=probe(url, timeout, default_opener))
        if compare_direct:
            item['direct_path'] = probe(url, timeout, direct)
        report['endpoints'].append(item)
    return report


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('urls', nargs='+')
    parser.add_argument('--timeout', type=int, default=8)
    parser.add_argument('--compare-direct', action='store_true', help='Also try process-local direct HTTP(S), ignoring proxy')
    args = parser.parse_args(argv)
    try:
        result = diagnose(args.urls, args.timeout, args.compare_direct)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # A successful alternate route does not hide a failure on the default route.
        return 0 if all(item['system_path']['successful_status'] for item in result['endpoints']) else 1
    except (ValueError, TypeError):
        print('Invalid URL, count or timeout; credentials and URL query are not printed', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
