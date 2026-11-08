"""Offline group-ID overlap audit for CSV or one-ID-per-line dataset splits."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import itertools
import json
from pathlib import Path
import sys


@dataclass
class Split:
    rows: int
    ids: set[str]


def read_ids(path: Path, file_format='csv', column='subject_id') -> Split:
    ids: set[str] = set()
    count = 0
    with path.open(encoding='utf-8-sig', newline='') as source:
        if file_format == 'csv':
            reader = csv.DictReader(source, strict=True)
            if not reader.fieldnames or column not in reader.fieldnames:
                raise ValueError('Required group-ID column is missing')
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError('Duplicate CSV column names')
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f'Wrong CSV field count near line {reader.line_num}')
                value = row[column].strip()
                if not value:
                    raise ValueError(f'Empty group ID near line {reader.line_num}')
                ids.add(value)
                count += 1
        elif file_format == 'lines':
            for number, line in enumerate(source, 1):
                value = line.strip()
                if not value:
                    raise ValueError(f'Empty group ID on line {number}')
                ids.add(value)
                count += 1
        else:
            raise ValueError('Unknown format')
    if not count:
        raise ValueError('Split has no records')
    return Split(count, ids)


def report(splits: dict[str, Split]) -> dict:
    if len(splits) < 2:
        raise ValueError('At least two splits are required')
    overlaps = []
    for left, right in itertools.combinations(splits, 2):
        overlap = splits[left].ids & splits[right].ids
        overlaps.append(dict(left=left, right=right, overlapping_groups=len(overlap)))
    return dict(
        schema_version=1,
        group_overlap_detected=any(pair['overlapping_groups'] for pair in overlaps),
        splits={name: dict(rows=value.rows, unique_groups=len(value.ids)) for name, value in splits.items()},
        pairs=overlaps,
        scope='exact normalized group-ID equality only; not a complete data-leakage audit',
    )


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', action='append', required=True, help='NAME=PATH; repeat for each split')
    parser.add_argument('--format', choices=['csv', 'lines'], default='csv')
    parser.add_argument('--id-column', default='subject_id')
    args = parser.parse_args(argv)
    try:
        splits = {}
        for value in args.split:
            name, separator, path = value.partition('=')
            name = name.strip()
            if not separator or not name or not path or name in splits:
                raise ValueError('Each --split must have a unique nonempty NAME=PATH')
            splits[name] = read_ids(Path(path), args.format, args.id_column)
        result = report(splits)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result['group_overlap_detected'] else 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f'Input error: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
