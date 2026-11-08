"""Explicit real-data smoke check; removes downloaded data and saves metadata only."""
import argparse
from collections import Counter
from datetime import date
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from urllib.request import ProxyHandler, build_opener
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', required=True)
    parser.add_argument('--direct-network', action='store_true')
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    module_path = root / 'datasets/download-helper/fetch.py'
    spec = importlib.util.spec_from_file_location('dataset_fetch_verify', module_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    manifest_path = root / 'datasets/download-helper/fashion-mnist.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    entries = helper.load_manifest(manifest_path)
    sample = root / 'maintenance' / ('download-check-' + uuid.uuid4().hex)
    sample.mkdir()
    results = []
    opener = build_opener(ProxyHandler({})).open if args.direct_network else None
    try:
        for entry in entries:
            print('Checking ' + entry['name'], flush=True)
            helper.fetch(entry, sample, opener=opener, max_bytes=100 * 1024 * 1024)
            path = sample / entry['name']
            with gzip.open(path, 'rb') as compressed:
                magic, count = struct.unpack('>II', compressed.read(8))
                expected_count = 60000 if entry['name'].startswith('train-') else 10000
                if count != expected_count:
                    raise ValueError('Unexpected IDX record count')
                detail = dict(records=count, magic=magic)
                if 'images' in entry['name']:
                    rows, columns = struct.unpack('>II', compressed.read(8))
                    if (magic, rows, columns) != (2051, 28, 28):
                        raise ValueError('Unexpected image IDX header')
                    length = 0
                    while block := compressed.read(1024 * 1024):
                        length += len(block)
                    if length != count * rows * columns:
                        raise ValueError('Unexpected image payload size')
                    detail.update(rows=rows, columns=columns, pixel_bytes=length)
                else:
                    labels = compressed.read()
                    if magic != 2049 or len(labels) != count or set(labels) != set(range(10)):
                        raise ValueError('Unexpected label IDX payload')
                    detail['class_counts'] = dict(sorted(Counter(labels).items()))
            results.append(dict(name=entry['name'], source=entry['url'],
                                compressed_bytes=path.stat().st_size,
                                md5=helper.checksum(path, 'md5'),
                                sha256=helper.checksum(path, 'sha256'), idx=detail))
    finally:
        if sample.resolve().parent != (root / 'maintenance').resolve() or not sample.name.startswith('download-check-'):
            raise RuntimeError('Refusing unexpected cleanup')
        for path in sample.iterdir():
            path.unlink()
        sample.rmdir()
    report = dict(checked_on=args.date.isoformat(), upstream_commit=manifest['upstream_commit'],
                  network='explicit process-local direct HTTPS' if args.direct_network else 'system proxy settings',
                  raw_data_retained=False, scope='all four files; official MD5 plus gzip/IDX structure; no model training',
                  files=results)
    output = root / 'datasets/fashion-mnist/verification.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Real download and IDX check: PASS; raw files removed; report saved', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
