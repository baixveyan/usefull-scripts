"""Run curated offline checks; does not install packages or access real services."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def commands(root, javascript=False):
    python = sys.executable
    result = [('catalog', [python, 'maintenance/validate_catalog.py']),
              ('navigation', [python, 'maintenance/build_catalog.py', '--check'])]
    for name, directory, pattern in [
        ('calendar', 'booking-helpers/calendar-reminders', 'test_*.py'),
        ('downloads', 'datasets/download-helper', 'test_*.py'),
        ('split-audit', 'datasets/split-audit', 'test_*.py'),
        ('folder-snapshot', 'everyday/folder-snapshot', 'test_*.py'),
        ('network-check', 'everyday/network-check', 'test_*.py'),
        ('translation', 'whatsapp_live_translator', 'test_*.py'),
        ('maintenance', 'maintenance', 'test_maintenance.py'),
        ('candidate-discovery', 'maintenance', 'test_discover.py'),
    ]:
        result.append((name, [python, '-m', 'unittest', 'discover', '-s', directory, '-p', pattern, '-v']))
    if javascript:
        node = shutil.which('node')
        if not node:
            raise RuntimeError('Node is required for --with-javascript')
        result.extend([
            ('source-note-format', [node, 'app-helpers/source-notes/test_format.mjs']),
            ('source-note-popup', [node, 'app-helpers/source-notes/test_popup.mjs']),
            ('source-note-syntax', [node, '--check', 'app-helpers/source-notes/popup.mjs']),
        ])
    if os.name == 'nt':
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if not powershell:
            raise RuntimeError('PowerShell is required for Windows build fixture')
        result.append(('build-fixture', [powershell, '-NoProfile', '-File', str(root / 'maintenance/test_whatsapp_build.ps1')]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='List checks without running')
    parser.add_argument('--with-javascript', action='store_true', help='Also run Node checks; no npm packages required')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    checks = commands(root, args.with_javascript)
    if args.list:
        for name, command in checks:
            print(name + ': ' + repr(command))
        return 0
    failures = []
    for name, command in checks:
        print(f'\nCHECK {name}', flush=True)
        try:
            outcome = subprocess.run(command, cwd=root, timeout=60, check=False)
            if outcome.returncode:
                failures.append(name)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'FAILED: {type(exc).__name__}', flush=True)
            failures.append(name)
    print(f'\nOffline checks: {len(checks) - len(failures)}/{len(checks)} passed')
    if os.name != 'nt':
        print('Windows-only PowerShell build fixture not run on this platform')
    if failures:
        print('Failed: ' + ', '.join(failures))
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
