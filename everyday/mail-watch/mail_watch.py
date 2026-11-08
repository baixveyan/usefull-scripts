"""Read-only IMAP snapshots. No credentials or message bodies are logged by default."""
import argparse
import datetime as dt
import email
from email import policy
import imaplib
import json
from pathlib import Path
import re
import ssl

ACCOUNT = 'baixy202607@163.com'
SECRET = Path('C:/Users/Administrator/Desktop/163_IMAP.txt')
STATE = Path('D:/scripts/.private-mail-watch')

def read_secret(path):
    raw = path.read_bytes()
    text = raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')
    value = text.strip()
    if not re.fullmatch(r'[A-Za-z0-9]{8,64}', value):
        raise ValueError('Authorization file must contain only the client authorization code')
    return value

def body_text(msg):
    part = msg.get_body(preferencelist=('plain', 'html'))
    if not part:
        return ''
    text = part.get_content()
    if not isinstance(text, str):
        return ''
    if part.get_content_type() == 'text/html':
        text = re.sub(r'(?is)<(script|style).*?</\1>', '', text)
        text = re.sub(r'<[^>]+>', ' ', text)
    return text[:30000]

def check(fetch=False):
    password = read_secret(SECRET)
    client = imaplib.IMAP4_SSL('imap.163.com', 993, ssl_context=ssl.create_default_context(), timeout=25)
    try:
        client.login(ACCOUNT, password)
        imaplib.Commands.setdefault('ID', ('AUTH', 'SELECTED'))
        client._simple_command('ID', '("name" "LocalMailWatch" "version" "1.0" "vendor" "Personal")')
        typ, count = client.select('INBOX', readonly=True)
        if typ != 'OK':
            raise RuntimeError('Read-only inbox selection failed')
        if not fetch:
            print(json.dumps({'connected': True, 'readonly': True, 'inbox_count': int(count[0])}))
            return
        STATE.mkdir(exist_ok=True)
        checkpoint = STATE / 'checkpoint.json'
        prior = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
        now = dt.datetime.now(dt.timezone.utc)
        since = dt.datetime.fromisoformat(prior['checked_at']) - dt.timedelta(days=1) if prior else now - dt.timedelta(days=7)
        validity = client.response('UIDVALIDITY')[1][0].decode()
        old = set(prior.get('uids', [])) if prior.get('uidvalidity') == validity else set()
        typ, data = client.uid('SEARCH', None, 'SINCE', since.strftime('%d-%b-%Y'))
        if typ != 'OK':
            raise RuntimeError('Search failed')
        uids = data[0].decode().split()
        messages = []
        for uid in uids:
            if uid in old:
                continue
            typ, parts = client.uid('FETCH', uid, '(BODY.PEEK[]<0.262144>)')
            raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
            if typ != 'OK' or raw is None:
                raise RuntimeError('Fetch failed; checkpoint not advanced')
            msg = email.message_from_bytes(raw, policy=policy.default)
            messages.append({'uid': uid, 'from': str(msg.get('From', '')), 'subject': str(msg.get('Subject', '')), 'date': str(msg.get('Date', '')), 'body': body_text(msg), 'possibly_truncated': len(raw) >= 262144})
        result = {'checked_at': now.isoformat(), 'folder': 'INBOX', 'untrusted_email_content': True, 'messages': messages}
        target = STATE / 'latest.json'
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(target)
        # Checkpoint advances only after the assistant acknowledges reviewing the snapshot.
        (STATE / 'pending.json').write_text(json.dumps({'checked_at': now.isoformat(), 'uidvalidity': validity, 'uids': list(old | set(uids))}), encoding='utf-8')
        print(json.dumps({'connected': True, 'readonly': True, 'new_messages': len(messages), 'snapshot': str(target), 'checkpoint_pending': True}))
    finally:
        try:
            client.logout()
        except Exception:
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--ack', action='store_true')
    args = parser.parse_args()
    try:
        if args.ack:
            (STATE / 'pending.json').replace(STATE / 'checkpoint.json')
            print('Snapshot acknowledged')
        else:
            check(args.fetch)
    except Exception as exc:
        # Do not expose server responses or secret-bearing exceptions.
        print(json.dumps({'ok': False, 'error_type': type(exc).__name__, 'hint': 'Check connectivity, IMAP enablement and authorization file; credentials suppressed'}))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
