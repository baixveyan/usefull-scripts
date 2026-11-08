import contextlib
from datetime import datetime, timezone
import importlib.util
import io
from pathlib import Path
import uuid
import unittest

spec = importlib.util.spec_from_file_location('reminders', Path(__file__).with_name('reminders.py'))
reminders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reminders)


@contextlib.contextmanager
def sample_directory():
    # Explicit mkdir avoids platform-dependent restrictive tempfile ACLs.
    root = Path(__file__).resolve().parent
    directory = root / ('sample-' + uuid.uuid4().hex)
    directory.mkdir()
    try:
        yield directory
    finally:
        if directory.resolve().parent != root:
            raise RuntimeError('Unexpected sample directory')
        for name in ('events.csv', 'events.ics'):
            (directory / name).unlink(missing_ok=True)
        directory.rmdir()


class ReminderTests(unittest.TestCase):
    def make(self, title='提醒', start='2026-11-01T12:00:00+08:00', **kwargs):
        data = io.StringIO()
        fields = ['id', 'title', 'start', *kwargs.keys()]
        writer = reminders.csv.DictWriter(data, fieldnames=fields)
        writer.writeheader()
        writer.writerow(dict(id='event-1', title=title, start=start, **kwargs))
        return data.getvalue()

    def test_timezone_and_alarms(self):
        result = reminders.render(self.make(remind_minutes='60;10;0;10'))
        self.assertIn('DTSTART:20261101T040000Z', result)
        self.assertIn('DTEND:20261101T041500Z', result)
        self.assertEqual(result.count('BEGIN:VALARM'), 3)

    def test_escaping_and_utf8_folding(self):
        title = '中文' * 50 + ',;\\\nEND:VEVENT'
        result = reminders.render(self.make(title=title))
        for line in result.split('\r\n'):
            self.assertLessEqual(len(line.encode('utf-8')), 75)
        unfolded = result.replace('\r\n ', '')
        self.assertIn('SUMMARY:' + reminders.text(title), unfolded)
        self.assertEqual(result.count('\r\nEND:VEVENT\r\n'), 1)
        self.assertNotIn('\n', result.replace('\r\n', ''))

    def test_reject_bad_input(self):
        for values in [dict(start='2026-11-01T12:00'), dict(start='2026-02-30T12:00+08:00'),
                       dict(remind_minutes='-1'), dict(remind_minutes='oops'),
                       dict(duration_minutes='0'), dict(url='javascript:alert(1)'),
                       dict(url='https://example.com/\nBEGIN:VEVENT')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                reminders.render(self.make(**values))

    def test_duplicate_ids_and_columns(self):
        source = self.make()
        with self.assertRaises(ValueError):
            reminders.render(source + source.splitlines()[-1] + '\n')
        with self.assertRaises(ValueError):
            reminders.render('id,title,start,id\na,b,c,d\n')

    def test_stable_uid_and_stamp(self):
        first = reminders.render(self.make(), datetime(2026, 1, 1, tzinfo=timezone.utc))
        second = reminders.render(self.make(), datetime(2026, 1, 2, tzinfo=timezone.utc))
        uid = lambda value: next(line for line in value.splitlines() if line.startswith('UID:'))
        self.assertEqual(uid(first), uid(second))
        self.assertIn('DTSTAMP:20260101T000000Z', first)

    def test_empty_and_malformed(self):
        for value in ['id,title,start\n', 'title,start\na,b\n', 'id,title,start\na,b,c,extra\n']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                reminders.render(value)

    def test_cli_dry_run_and_refuse_overwrite(self):
        with sample_directory() as directory:
            source, output = Path(directory) / 'events.csv', Path(directory) / 'events.ics'
            source.write_text('\ufeff' + self.make(), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(reminders.main([str(source), '--output', str(output), '--dry-run']), 0)
                self.assertFalse(output.exists())
                self.assertEqual(reminders.main([str(source), '--output', str(output)]), 0)
                original = output.read_bytes()
                self.assertIn(b'\r\n', original)
                self.assertEqual(reminders.main([str(source), '--output', str(output)]), 2)
                self.assertEqual(output.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
