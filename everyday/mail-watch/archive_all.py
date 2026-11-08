"""Archive all selectable IMAP folders with read-only PEEK, locally only."""
import email
from email import policy
import hashlib
import imaplib
import json
import re
import ssl
from mail_watch import ACCOUNT, SECRET, STATE, read_secret, body_text

def main():
    client = imaplib.IMAP4_SSL('imap.163.com', 993, ssl_context=ssl.create_default_context(), timeout=30)
    report = []
    index = []
    root = STATE / 'archive'
    root.mkdir(parents=True, exist_ok=True)
    try:
        client.login(ACCOUNT, read_secret(SECRET))
        imaplib.Commands.setdefault('ID', ('AUTH', 'SELECTED'))
        client._simple_command('ID', '("name" "LocalMailWatch" "version" "1.0")')
        typ, folders = client.list()
        if typ != 'OK':
            raise RuntimeError('Folder list failed')
        for line in folders:
            match = re.match(rb'\((.*?)\) "[^"]*" (.*)', line)
            if not match:
                raise RuntimeError('Unsupported folder listing')
            if b'\\noselect' in match[1].lower():
                continue
            mailbox = match[2].decode('ascii')
            typ, count = client.select(mailbox, readonly=True)
            if typ != 'OK':
                report.append({'folder': mailbox, 'error': 'select failed'})
                continue
            validity = client.response('UIDVALIDITY')[1][0].decode()
            target = root / hashlib.sha256(mailbox.encode()).hexdigest()[:16] / validity
            target.mkdir(parents=True, exist_ok=True)
            typ, data = client.uid('SEARCH', None, 'ALL')
            if typ != 'OK':
                raise RuntimeError('Search failed')
            uids = data[0].decode().split()
            for uid in uids:
                path = target / (uid + '.eml')
                if not path.exists():
                    typ, parts = client.uid('FETCH', uid, '(BODY.PEEK[])')
                    raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
                    if typ != 'OK' or raw is None:
                        raise RuntimeError('Fetch failed')
                    temporary = path.with_suffix('.tmp')
                    temporary.write_bytes(raw)
                    temporary.replace(path)
                raw = path.read_bytes()
                msg = email.message_from_bytes(raw, policy=policy.default)
                index.append({'folder': mailbox, 'uid': uid, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'from': str(msg.get('From', '')), 'to': str(msg.get('To', '')), 'subject': str(msg.get('Subject', '')), 'date': str(msg.get('Date', '')), 'body': body_text(msg), 'attachments': [str(p.get_filename()) for p in msg.walk() if p.get_filename()]})
            report.append({'folder': mailbox, 'messages': len(uids)})
        (STATE / 'all-mail-index.json').write_text(json.dumps({'untrusted_email_content': True, 'folders': report, 'messages': index}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'folders': report, 'archived': len(index), 'index': str(STATE / 'all-mail-index.json')}, ensure_ascii=False))
    finally:
        try:
            client.logout()
        except Exception:
            pass

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'error_type': type(exc).__name__, 'credentials_suppressed': True}))
        raise SystemExit(1)
