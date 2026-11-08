"""Offline CSV to iCalendar reminders. Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


def text(value: str) -> str:
    value = value.replace('\r\n', '\n').replace('\r', '\n')
    if any(ord(char) < 32 and char not in '\n\t' for char in value):
        raise ValueError('Control characters are not allowed in text')
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line: str) -> str:
    """Fold at <=75 UTF-8 octets, never splitting a code point."""
    parts: list[str] = []
    current = ''
    size = 0
    for char in line:
        length = len(char.encode('utf-8'))
        if size + length > 75:
            parts.append(current)
            current, size = ' ', 1
        current += char
        size += length
    parts.append(current)
    return '\r\n'.join(parts)


def timestamp(value: str) -> datetime:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('start must be ISO time with explicit offset, e.g. 2026-11-01T12:00:00+08:00')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return parsed.astimezone(timezone.utc)


def render(source: str, now: datetime | None = None) -> str:
    reader = csv.DictReader(io.StringIO(source))
    required = {'id', 'title', 'start'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError('CSV requires id,title,start columns')
    if len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError('Duplicate column names')
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Practical Tools//Offline Reminders 1.0//EN', 'CALSCALE:GREGORIAN']
    seen: set[str] = set()
    count = 0
    for row_number, row in enumerate(reader, 2):
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Wrong number of CSV fields')
            event_id = row['id'].strip()
            title = row['title'].strip()
            if not event_id or not title:
                raise ValueError('id and title cannot be empty')
            if event_id in seen:
                raise ValueError('Duplicate id')
            seen.add(event_id)
            start = timestamp(row['start'].strip())
            duration = int(row.get('duration_minutes', '').strip() or '15')
            if not 1 <= duration <= 10080:
                raise ValueError('duration_minutes must be between 1 and 10080')
            raw_alerts = row.get('remind_minutes', '').strip()
            alerts = sorted({int(item.strip()) for item in raw_alerts.split(';')}) if raw_alerts else []
            if any(item < 0 or item > 525600 for item in alerts):
                raise ValueError('remind_minutes must be between 0 and 525600')
            url = row.get('url', '').strip()
            if url:
                if any(char.isspace() or ord(char) < 32 for char in url):
                    raise ValueError('URL must not contain whitespace or control characters')
                parsed_url = urlsplit(url)
                if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
                    raise ValueError('URL must use http or https with a host')
            uid = hashlib.sha256(event_id.encode('utf-8')).hexdigest() + '@practical-tools.local'
            lines.extend(['BEGIN:VEVENT', f'UID:{uid}', f'DTSTAMP:{stamp}',
                          'DTSTART:' + start.strftime('%Y%m%dT%H%M%SZ'),
                          'DTEND:' + (start + timedelta(minutes=duration)).strftime('%Y%m%dT%H%M%SZ'),
                          'SUMMARY:' + text(title)])
            if row.get('description', ''):
                lines.append('DESCRIPTION:' + text(row['description']))
            if url:
                lines.append('URL:' + url)
            for minutes in alerts:
                lines.extend(['BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + text(title),
                              f'TRIGGER:-PT{minutes}M', 'END:VALARM'])
            lines.append('END:VEVENT')
            count += 1
        except (ValueError, OverflowError) as exc:
            raise ValueError(f'CSV row {row_number}: {exc}') from exc
    if not count:
        raise ValueError('CSV has no events')
    lines.append('END:VCALENDAR')
    return '\r\n'.join(fold(line) for line in lines) + '\r\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='UTF-8 CSV (BOM supported)')
    parser.add_argument('--output', type=Path, help='Create a new ICS; refuses overwrite')
    parser.add_argument('--dry-run', action='store_true', help='Print ICS; write nothing')
    args = parser.parse_args(argv)
    if not args.dry_run and not args.output:
        parser.error('--output is required unless --dry-run is used')
    try:
        calendar = render(args.input.read_text(encoding='utf-8-sig'))
        if args.dry_run:
            print(calendar, end='')
        else:
            with args.output.open('x', encoding='utf-8', newline='') as output:
                output.write(calendar)
            print(f'Created: {args.output}')
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
