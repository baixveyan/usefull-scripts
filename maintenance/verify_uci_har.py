"""Explicit UCI archive/subject-split check; removes data, retains receipt only."""
import argparse
from datetime import date
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from urllib.request import ProxyHandler, build_opener
import uuid
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', required=True, action='store_true')
    parser.add_argument('--direct-network', action='store_true')
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sample = root / 'maintenance' / ('download-check-' + uuid.uuid4().hex)
    sample.mkdir()
    url = 'https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip'
    opener = build_opener(ProxyHandler({})) if args.direct_network else build_opener()
    archive_path = sample / 'official.zip'
    metadata = {}
    try:
        print('Downloading official UCI archive (temporary data only)', flush=True)
        hasher = hashlib.sha256()
        total = 0
        with opener.open(url, timeout=30) as response, archive_path.open('xb') as output:
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > 200 * 1024 * 1024:
                    raise ValueError('Unexpectedly large archive')
                hasher.update(block)
                output.write(block)
        spec = importlib.util.spec_from_file_location('uci_split_audit', root / 'datasets/split-audit/audit.py')
        audit = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = audit
        spec.loader.exec_module(audit)
        with zipfile.ZipFile(archive_path) as outer:
            candidates = [name for name in outer.namelist() if name.endswith('/train/subject_train.txt')]
            nested = None
            if not candidates:
                inner_names = [name for name in outer.namelist() if Path(name).name == 'UCI HAR Dataset.zip']
                if len(inner_names) != 1 or outer.getinfo(inner_names[0]).file_size > 150 * 1024 * 1024:
                    raise ValueError('Unknown official archive layout')
                nested = zipfile.ZipFile(io.BytesIO(outer.read(inner_names[0])))
            archive = nested or outer
            try:
                splits = {}
                for split in ('train', 'test'):
                    suffix = f'/{split}/subject_{split}.txt'
                    names = [name for name in archive.namelist() if name.endswith(suffix)]
                    if len(names) != 1 or archive.getinfo(names[0]).file_size > 1024 * 1024:
                        raise ValueError('Unexpected subject ID file')
                    path = sample / (split + '.txt')
                    path.write_bytes(archive.read(names[0]))
                    splits[split] = audit.read_ids(path, 'lines')
                metadata = audit.report(splits)
            finally:
                if nested:
                    nested.close()
        if metadata['group_overlap_detected'] or sum(value['rows'] for value in metadata['splits'].values()) != 10299:
            raise ValueError('Unexpected split statistics')
        report = dict(checked_on=args.date.isoformat(), source=url, compressed_bytes=total,
                      observed_sha256=hasher.hexdigest(), official_checksum_available=False,
                      scope='official HTTPS archive; selected subject ZIP entries and split statistics only; no training',
                      raw_data_retained=False, audit=metadata)
    finally:
        if sample.resolve().parent != (root / 'maintenance').resolve() or not sample.name.startswith('download-check-'):
            raise RuntimeError('Refusing unexpected cleanup')
        for path in sample.iterdir():
            path.unlink()
        sample.rmdir()
    (root / 'datasets/uci-har/verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('UCI archive and real subject split: PASS; data removed', flush=True)
    print(json.dumps(metadata))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
