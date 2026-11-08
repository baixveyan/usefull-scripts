"""Manifest-based HTTPS dataset downloader; preview unless --download is given."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener, urlopen
import uuid

ALGORITHMS = {'sha256': 64, 'md5': 32}


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('files'), list) or not data['files']:
        raise ValueError('Manifest requires version=1 and nonempty files list')
    names = set()
    for entry in data['files']:
        if not isinstance(entry, dict):
            raise ValueError('Each file must be an object')
        name = entry.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name) or name.endswith('.'):
            raise ValueError('File names must be plain ASCII names without directories')
        if name.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}:
            raise ValueError('Reserved Windows filename')
        if name.casefold() in names:
            raise ValueError('Duplicate file name')
        names.add(name.casefold())
        url = entry.get('url')
        if not isinstance(url, str) or any(char.isspace() or ord(char) < 32 for char in url):
            raise ValueError('Invalid download URL')
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError('Use HTTPS URLs without credentials or fragments')
        if entry.get('accept') not in (None, 'application/vnd.github.raw+json', 'application/octet-stream'):
            raise ValueError('Unsupported Accept content type')
        algorithm = entry.get('algorithm')
        digest = entry.get('digest')
        if algorithm not in ALGORITHMS or not isinstance(digest, str) or not re.fullmatch(f'[0-9a-fA-F]{{{ALGORITHMS[algorithm]}}}', digest):
            raise ValueError('Expected valid sha256 or md5 digest')
    return data['files']


def checksum(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open('rb') as source:
        while block := source.read(1024 * 1024):
            hasher.update(block)
    return hasher.hexdigest()


def fetch(entry: dict, output: Path, opener=None, max_bytes=1024 * 1024 * 1024) -> str:
    """Never overwrite an existing target; publish verified bytes via hard link."""
    opener = opener or urlopen
    target = output / entry['name']
    if target.is_symlink():
        raise ValueError('Refusing symbolic-link target')
    if target.exists():
        if not target.is_file() or checksum(target, entry['algorithm']).lower() != entry['digest'].lower():
            raise ValueError('Existing file differs; inspect or move it before retrying')
        return 'verified-existing'
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / ('.download-' + uuid.uuid4().hex + '.part')
    try:
        hasher = hashlib.new(entry['algorithm'])
        total = 0
        headers = {'User-Agent': 'PracticalDatasetDownloader/1.0'}
        if entry.get('accept'):
            headers['Accept'] = entry['accept']
        request = Request(entry['url'], headers=headers)
        with temporary.open('xb') as destination, opener(request, timeout=30) as response:
            # urllib normally follows redirects. Reject downgrade before consuming bytes.
            final_url = response.geturl() if hasattr(response, 'geturl') else entry['url']
            if urlsplit(final_url).scheme != 'https':
                raise ValueError('HTTPS downgrade refused')
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > max_bytes:
                    raise ValueError('Download exceeds per-file byte limit')
                destination.write(block)
                hasher.update(block)
        if hasher.hexdigest().lower() != entry['digest'].lower():
            raise ValueError('Downloaded file checksum mismatch')
        # link() fails if target exists on both Windows and Unix; no overwrite race.
        # Filesystems lacking hard links fail explicitly rather than publishing partial data.
        os.link(temporary, target)
        return 'downloaded-verified'
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download', action='store_true', help='Fetch and verify; otherwise preview only')
    parser.add_argument('--direct-network', action='store_true', help='Explicitly ignore system proxy for this process only')
    parser.add_argument('--max-mib', type=int, default=1024, help='Per-file download limit, default 1024 MiB')
    args = parser.parse_args(argv)
    if args.max_mib < 1:
        parser.error('--max-mib must be positive')
    try:
        entries = load_manifest(args.manifest)
    except (OSError, ValueError, TypeError) as exc:
        print(f'Manifest error: {exc}', file=sys.stderr)
        return 2
    failures = 0
    opener = build_opener(ProxyHandler({})).open if args.direct_network else None
    for entry in entries:
        if not args.download:
            print(f"PREVIEW {entry['name']} -> {args.output / entry['name']} [{entry['algorithm']}]")
            continue
        try:
            status = fetch(entry, args.output, opener=opener, max_bytes=args.max_mib * 1024 * 1024)
            print(f"{status}: {entry['name']}")
        except Exception as exc:
            failures += 1
            # Avoid exposing signed URLs or credentials in network exception strings.
            print(f"FAILED {entry['name']}: {type(exc).__name__}; check network, checksum, limit, output and filesystem", file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
