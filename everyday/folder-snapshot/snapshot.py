"""Read-only logical folder-size snapshots and comparisons. No file content is read."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import heapq
import json
import os
from pathlib import Path
import stat
import sys


def scan(root: Path, top=20, excludes=()):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Scan root must be a directory')
    if not 1 <= top <= 1000:
        raise ValueError('top must be between 1 and 1000')
    groups = {}
    root_files = dict(bytes=0, files=0)
    largest = []
    errors = []
    skipped = 0
    total = count = 0
    excluded = set(excludes)
    stack = [(root, None)]
    while stack:
        directory, group = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    relative = Path(entry.path).relative_to(root).as_posix()
                    if entry.name in excluded:
                        skipped += 1
                        continue
                    try:
                        info = entry.stat(follow_symlinks=False)
                        reparse = getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
                        if stat.S_ISLNK(info.st_mode) or reparse:
                            skipped += 1
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            child_group = group if group is not None else entry.name
                            groups.setdefault(child_group, dict(bytes=0, files=0))
                            stack.append((Path(entry.path), child_group))
                        elif stat.S_ISREG(info.st_mode):
                            bucket = root_files if group is None else groups[group]
                            bucket['bytes'] += info.st_size
                            bucket['files'] += 1
                            total += info.st_size
                            count += 1
                            candidate = (info.st_size, relative)
                            if len(largest) < top:
                                heapq.heappush(largest, candidate)
                            elif candidate > largest[0]:
                                heapq.heapreplace(largest, candidate)
                        else:
                            skipped += 1
                    except OSError as exc:
                        errors.append(dict(path=relative, error=type(exc).__name__))
        except OSError as exc:
            errors.append(dict(path=directory.relative_to(root).as_posix(), error=type(exc).__name__))
    return dict(schema_version=1, kind='folder-snapshot', root=str(root),
                created_at=datetime.now(timezone.utc).isoformat(),
                total_bytes=total, total_files=count, root_files=root_files,
                groups=dict(sorted(groups.items())),
                largest_files=[dict(path=path, bytes=size) for size, path in sorted(largest, reverse=True)],
                excluded_names=sorted(excluded), skipped_entries=skipped, errors=errors,
                partial=bool(errors), byte_semantics='logical per path; hard links may count more than once')


def compare(before, after):
    for item in (before, after):
        if item.get('schema_version') != 1 or item.get('kind') != 'folder-snapshot':
            raise ValueError('Unsupported snapshot format')
    if os.path.normcase(before['root']) != os.path.normcase(after['root']):
        raise ValueError('Snapshots refer to different roots')
    if before['excluded_names'] != after['excluded_names']:
        raise ValueError('Snapshots have different exclusions')
    changes = []
    for name in sorted(set(before['groups']) | set(after['groups'])):
        old = before['groups'].get(name, dict(bytes=0, files=0))
        new = after['groups'].get(name, dict(bytes=0, files=0))
        changes.append(dict(folder=name, bytes_delta=new['bytes'] - old['bytes'], files_delta=new['files'] - old['files']))
    return dict(schema_version=1, kind='folder-comparison', root=after['root'],
                total_bytes_delta=after['total_bytes'] - before['total_bytes'],
                total_files_delta=after['total_files'] - before['total_files'],
                root_files_bytes_delta=after['root_files']['bytes'] - before['root_files']['bytes'],
                folders=sorted(changes, key=lambda item: (-item['bytes_delta'], item['folder'])),
                partial=before['partial'] or after['partial'])


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='command', required=True)
    scanning = subcommands.add_parser('scan')
    scanning.add_argument('root', type=Path)
    scanning.add_argument('--top', type=int, default=20)
    scanning.add_argument('--exclude', action='append', default=[])
    scanning.add_argument('--output', type=Path)
    comparing = subcommands.add_parser('compare')
    comparing.add_argument('before', type=Path)
    comparing.add_argument('after', type=Path)
    comparing.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'scan':
            if args.output and args.output.resolve().is_relative_to(args.root.resolve()):
                raise ValueError('Save snapshot outside scan root so it is not counted on later scans')
            result = scan(args.root, args.top, args.exclude)
        else:
            result = compare(json.loads(args.before.read_text(encoding='utf-8-sig')),
                             json.loads(args.after.read_text(encoding='utf-8-sig')))
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8', newline='\n') as output:
                output.write(rendered)
            print(f'Created: {args.output}')
        else:
            print(rendered, end='')
        return 1 if result['partial'] else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
