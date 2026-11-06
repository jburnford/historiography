"""Back up processed dissertation PDFs to the external drive on hist-clifford-pgx, and log what is backed up (2026-11-05).

User, 2026-11-05: move the processed dissertation PDFs to the external drive on that machine; delete nothing yet,
copy and log what is backed up. The PDFs live on E: (/mnt/e/historiography-dissertation-pdfs; the corpus `pdf/`
link); the drive is a 12.7 TB ext4 disk at /mnt/data on hist-clifford-pgx (ssh alias `spark`, a shared connection:
~/.ssh/config ControlMaster). "Processed" = listed in the corpus extraction.jsonl (any extraction status: parsed,
no bibliography heading, no text layer...), so harvests still downloading or not yet ingested (Mexico, Glasgow)
are left out until they are.

    python3 scripts/backup_dissertation_pdfs.py list        # files.txt: processed PDFs on E:, relative paths
    python3 scripts/backup_dissertation_pdfs.py list2       # files-pass2.txt: the rest of the store that is not
                                                            # on the unprocessed list (thesis parts, other copies)
    python3 scripts/backup_dissertation_pdfs.py copy --files files-pass2.txt
    python3 scripts/backup_dissertation_pdfs.py copy        # rsync, resumable; appends transfer.log
    python3 scripts/backup_dissertation_pdfs.py manifest    # manifest.csv.gz: local and remote size, remote sha256

Nothing is deleted. The manifest marks each file `ok` (remote size equals local size; rsync verifies each
transferred file against its checksum), `missing` or `size_mismatch`; a later deletion step may read only `ok` rows.
"""
import argparse
import base64
import csv
import gzip
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
SRC = Path('/mnt/e/historiography-dissertation-pdfs')
HOST = 'spark'
DEST = '/mnt/data/jic823/historiography-dissertation-pdfs'
OUT = CORPUS / 'pdf-backup'


def cmd_list(args):
    processed = set()
    with (CORPUS / 'extraction.jsonl').open(encoding='utf-8') as f:
        for line in f:
            p = json.loads(line)['file']
            if p.startswith('pdf/'):
                processed.add(p[4:])
    fresh = time.time() - 3600
    rows, skipped_fresh = [], 0
    for rel in sorted(processed):
        p = SRC / rel
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        if st.st_mtime > fresh:                       # still being written by a harvest
            skipped_fresh += 1
            continue
        rows.append((rel, st.st_size))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'files.txt').write_text(''.join(f'{r}\n' for r, _ in rows), encoding='utf-8')
    print(json.dumps(dict(processed_listed=len(processed), on_disk=len(rows), skipped_fresh=skipped_fresh,
                          gb=round(sum(s for _, s in rows) / 1e9, 1))))


def cmd_list2(args):
    """Pass 2 (2026-11-05): another session's audit (scripts/audit_unprocessed_pdfs.py, pdf-store-unprocessed-2026-11-05)
    counts a thesis's .part02+ files and other files of an extracted (institution, id) as extracted, though
    extraction.jsonl names only one file. Every PDF in the store that the audit does not list (any category: KEEP-*,
    duplicate, incomplete) and pass 1 does not hold is added."""
    unprocessed = set()
    with (ROOT / 'data/field-research/pdf-store-unprocessed-2026-11-05/unprocessed-pdfs.tsv').open(encoding='utf-8') as f:
        next(f)
        for line in f:
            unprocessed.add(line.split('\t', 1)[0])
    pass1 = {l.rstrip('\n') for l in (OUT / 'files.txt').open(encoding='utf-8')}
    fresh = time.time() - 3600
    rows, skipped_fresh, held = [], 0, 0
    for root, _, files in os.walk(SRC):
        for name in files:
            if not name.lower().endswith('.pdf'):
                continue
            p = os.path.join(root, name)
            rel = os.path.relpath(p, SRC)
            if rel in pass1:
                continue
            if p in unprocessed:
                held += 1
                continue
            st = os.stat(p)
            if st.st_mtime > fresh:
                skipped_fresh += 1
                continue
            rows.append((rel, st.st_size))
    rows.sort()
    (OUT / 'files-pass2.txt').write_text(''.join(f'{r}\n' for r, _ in rows), encoding='utf-8')
    print(json.dumps(dict(pass2=len(rows), on_unprocessed_list=held, skipped_fresh=skipped_fresh,
                          gb=round(sum(s for _, s in rows) / 1e9, 1))))


def cmd_copy(args):
    log = OUT / 'transfer.log'
    # BatchMode: never wait at a password prompt when the shared connection has gone (2026-11-05: a drop at 12:21)
    rc = subprocess.call(['rsync', '-a', '--partial', '--files-from', str(OUT / args.files), '--mkpath',
                          '-e', 'ssh -o BatchMode=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=4',
                          '--out-format', '%t|%n|%l', '--log-file', str(OUT / 'rsync-run.log'),
                          f'{SRC}/', f'{HOST}:{DEST}/'], stdout=log.open('a'), stderr=subprocess.STDOUT)
    print(json.dumps(dict(rsync_exit=rc)))
    sys.exit(rc)


def cmd_manifest(args):
    files = sorted({l.rstrip('\n') for name in ('files.txt', 'files-pass2.txt') if (OUT / name).exists()
                    for l in (OUT / name).open(encoding='utf-8') if l.strip()})
    local = {}
    for rel in files:
        try:
            local[rel] = (SRC / rel).stat().st_size
        except FileNotFoundError:
            local[rel] = None
    # sizes and checksums are computed on pgx, next to the copies (one ssh session, file names on stdin)
    script = ('import sys,os,hashlib,json\n'
              f'base={DEST!r}\n'
              'for line in sys.stdin:\n'
              '    rel=line.rstrip("\\n"); p=os.path.join(base,rel)\n'
              '    try:\n'
              '        h=hashlib.sha256()\n'
              '        with open(p,"rb") as f:\n'
              '            for b in iter(lambda: f.read(1<<20), b""): h.update(b)\n'
              '        print(json.dumps([rel, os.path.getsize(p), h.hexdigest()]), flush=True)\n'
              '    except FileNotFoundError:\n'
              '        print(json.dumps([rel, None, None]), flush=True)\n')
    # ssh hands the remote shell one command string, which breaks the script's quoting: send it base64-encoded
    encoded = base64.b64encode(script.encode()).decode()
    proc = subprocess.run(['ssh', '-o', 'BatchMode=yes', HOST,
                           f'python3 -c "import base64; exec(base64.b64decode(\'{encoded}\'))"'], input=''.join(f'{r}\n' for r in files),
                          capture_output=True, text=True, check=True)
    remote = {r: (s, h) for r, s, h in map(json.loads, proc.stdout.splitlines())}
    when = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    counts = {'ok': 0, 'missing': 0, 'size_mismatch': 0}
    with gzip.open(OUT / 'manifest.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path', 'local_bytes', 'remote_bytes', 'remote_sha256', 'status', 'destination', 'checked_at'])
        for rel in files:
            rs, rh = remote.get(rel, (None, None))
            status = 'missing' if rs is None else 'ok' if rs == local[rel] else 'size_mismatch'
            counts[status] += 1
            w.writerow([f'pdf/{rel}', local[rel], rs, rh, status, f'{HOST_FQDN}:{DEST}/{rel}', when])
    (OUT / 'manifest-report.json').write_text(json.dumps(dict(counts, files=len(files), checked_at=when,
                                                              destination=f'{HOST_FQDN}:{DEST}'), indent=1) + '\n')
    print(json.dumps(counts))


HOST_FQDN = 'hist-clifford-pgx.usask.ca'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('step', choices=['list', 'list2', 'copy', 'manifest'])
    ap.add_argument('--files', default='files.txt', help='file list in pdf-backup/ for the copy step')
    a = ap.parse_args()
    {'list': cmd_list, 'list2': cmd_list2, 'copy': cmd_copy, 'manifest': cmd_manifest}[a.step](a)
