#!/usr/bin/env python3
"""Register the user-run Canadian History PhD downloads (2026-11-14 wget lists) from their repository
listing metadata (2026-11-15).

The files in ``/mnt/e/historiography-dissertation-pdfs/canada-wget-2026-11-14/`` were fetched by the user
from two lists written by ``scripts/user_run_canada.py`` (data/field-research/user-run-downloads-2026-11-14/
canada-open-urls.records.csv and canada-ai-excluded-urls.records.csv). Each list row names the file and
its record: an OAI record of a repository's History doctoral sets (record_id 'oai-...'), already screened
by ``user_run_canada.screen`` (department/discipline names History, degree names a doctorate), or an AHA
directory record of a completed History PhD (record_id 'aha<ID>') whose repository copy was found by title
or through OpenAlex/DataCite. This script recovers the metadata of each record (author, department and
degree values, set, handle) from the saved listings on E: (no network requests) and registers the file
after local validation:
  - whole file: PDF header and EOF, 50+ pages, every page parses (pdftotext to /dev/null);
  - pages 1-5 read as a doctorate (Doctor of Philosophy, PhD, doctoral, doctorat, thèse); image-only
    scans without a text layer are read by tesseract OCR (eng) for this check only;
  - the listed author's surname on pages 1-5 and 60%+ of the listed title's longer words there.
History PhDs only: the record's basis (the listing screen's department/degree values, or the AHA History
department) is kept in eligibility_basis. Economic history counts as History; history and philosophy of
science programmes are registered with history_scope 'history_of_science_department' (user decision
2026-11-04) when the title shows a historical period, date or history wording (HISTORY_SIGNAL; else held
for a decision, as possibly philosophy of science); art history is held as not History.
User ruling 2026-11-16 (RULING): history of science and history of education count as History. History of
education PhDs in an education faculty are registered with history_scope 'history_of_education_programme'.
HPS theses without a history signal in the title are registered or held by a reviewed decision in
<out>/reviewed-*.csv (file, decision 'register' or 'hold', note): a thesis that is plainly philosophy of science
with no historical content stays held ('held: philosophy of science (reviewed)'); one not yet reviewed is
held for a decision as before. ``--recheck-kind KIND`` drops the held rows of a kind so the files are taken
again (the same whole-file and title-page validation); released records carry ``review_note``.

Not registered (held.jsonl, with the reason): files registered already by the AHA title-page route
(us-dissertations-expansion-2026-10-20/manual-aha-2026-11-04, by file name), theses already held (title key
in find_aha_repository_links.held_titles, i.e. user_run_canada.held_index; or the AHA id in held_aha_ids),
the same file under another record (sha256), failed validation. A title key that matches a held thesis by
another surname is held for review rather than counted as the same thesis.

Output (metadata only; PDFs stay where they are): <out>/records.jsonl, downloads.jsonl (the manual-aha shape
plus degree_classification/issued_dates/pdf_urls for the 'canadian_harvest' ingest adapter), held.jsonl,
summary.csv (counts by university). Rerunning appends only files not yet seen in records or held.

Usage: python3 scripts/register_canada_user_run.py [--directory DIR] [--out DIR] [--workers 4] [--dry-run]
"""
import argparse
import collections
from concurrent.futures import ProcessPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import user_run_canada as C  # noqa: E402
import user_run_download_lists as U  # noqa: E402
from find_aha_repository_links import held_titles, held_aha_ids, title_key  # noqa: E402
from register_aha_browser_downloads import fold, words, rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIELD = ROOT/'data/field-research'
LISTS = [U.OUT/'canada-open-urls.records.csv', U.OUT/'canada-ai-excluded-urls.records.csv']
OAI_CACHE = U.CACHE.parent/'canada-oai-history-phd-v3.json'
AHA = FIELD/'aha-dissertations-2026-10-13/records.csv'
AHA_MATCHES = C.AHA_RUN/'matches.csv'
MANUAL_AHA = FIELD/'us-dissertations-expansion-2026-10-20/manual-aha-2026-11-04'
HELD_PDFS = FIELD/'dissertation-citations-2026-10-11/dissertations.csv'
DEFAULT_DIRECTORY = Path('/mnt/e/historiography-dissertation-pdfs/canada-wget-2026-11-14')
DEFAULT_OUT = FIELD/'canada-user-run-register-2026-11-15'
SOURCE = ('User-run download (wget, 2026-11-14) from the Canadian History PhD lists of scripts/user_run_canada.py; '
          'registered from the listing metadata after local whole-file and title-page validation')
NAMES = {u[0]: u[1] for u in C.UNIS}
DOCTORATE = r'd?octor of philos\w*|\bph ?d\b|\bdoctoral\b|doctorat|philosophiae doctor|\bthese\b|\bdocteur\b'
# OCAP (memory: historiography-ocap-practice): flag for review, never describe community knowledge.
OCAP = re.compile(r'(first nation|indigenous|aboriginal|m[ée]tis|inuit|inuk|cree|anishinaab|ojibw|haudenosaunee|mohawk|'
                  r'six nations|wendat|huron|mi.kmaq|wolastoq|innu|dene|blackfoot|siksika|nakoda|lakota|dakota|'
                  r'salish|st[óo]:l[oō]|nuu-chah|haida|tsimshian|nisga|gitxsan|kwakwaka|autochtone|amérindien|'
                  r'native|indian|elders?\b|oral histor|traditional knowledge|residential school)', re.I)


# HPS programmes (Toronto IHPST, McGill HPS) also grant philosophy-of-science doctorates. History of science
# counts as History (user decision 2026-11-04); a thesis whose title shows no historical period, date or
# history wording is held for a decision instead of being registered.
HISTORY_SIGNAL = re.compile(r'(\b1[0-9]{3}\b|\b20[0-2][0-9]\b|histor|centur|antiquity|ancient|medieval|middle ages|'
                            r'renaissance|early[- ]modern|enlightenment|victorian|edwardian|interwar|postwar|post-war|'
                            r'cold war|colonial|soviet|(seven|eigh|nine|twen)teenth|origins of|\bera\b)', re.I)
RULING = ('user ruling 2026-11-16: history of science and history of education count as History '
          '(released from held.jsonl)')


def now():
    return datetime.now(timezone.utc).isoformat()


def rid_of(ident):
    return 'oai-' + re.sub(r'[^A-Za-z0-9]+', '-', ident.split(':')[-1])


def listing_metadata(needed=None):
    """(university, record_id) -> listing metadata from the saved OAI harvests (open hosts: the v3
    cache; AI-excluded hosts: the user-run ListRecords pages), same screen as user_run_canada.
    ``needed``: {(university, record_id)}; ListRecords pages (4.5 GB) are parsed only when their bytes
    hold one of those identifiers."""
    meta = {}
    wanted = collections.defaultdict(list)
    for uni, rid in needed or ():
        if rid.startswith('oai-'):
            wanted[uni].append(rb'[^A-Za-z0-9]+'.join(re.escape(x.encode()) for x in rid[4:].split('-')))
    pattern = {uni: re.compile(rb':(?:' + rb'|'.join(v) + rb')</identifier>') for uni, v in wanted.items()}
    cache = json.loads(OAI_CACHE.read_text()) if OAI_CACHE.exists() else {}
    host_key = {h[0]: u[0] for u in C.UNIS for h in u[5]}
    for host, (status, recs) in cache.items():
        for r in recs:
            meta[(host_key.get(host), rid_of(r['oai_id']))] = dict(
                listing_host=host, listing_route='OAI-PMH xoai (open host, user_run_canada step 2)', listing_set=r['set'],
                author=r['author'], title=r['title'], year=r['year'], dept=r['dept'], degree=r['degree'],
                item_url=r['handle'], oai_id=r['oai_id'])
    for host, key in C.LIST_HOSTS.items():
        if needed is not None and key not in pattern:
            continue
        for page in sorted((C.LISTINGS/host).glob('records-*/page-*.xml')):
            raw = page.read_bytes()
            if needed is not None and not pattern[key].search(raw):
                continue
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                continue
            setname = page.parent.name.removeprefix('records-')
            for rec in root.iter(U.OAI + 'record'):
                h = rec.find(U.OAI + 'header')
                md = rec.find(U.OAI + 'metadata')
                if h is None or h.get('status') == 'deleted' or md is None or not len(md):
                    continue
                ident = h.findtext(U.OAI + 'identifier')
                if host == 'archipel.uqam.ca':
                    e = C.parse_eprints_dc(md[0])
                    cite = next((t for t in e['ids'] if re.search(r'doctorat en histoire', t, re.I)), '')
                    entry = dict(author=e['author'], title=e['title'], year=e['year'],
                                 dept=(re.search(r'doctorat en histoire[^,.)]*', cite, re.I) or [''])[0],
                                 degree='; '.join(e['types']),
                                 item_url=next((u for u in e['ids'] if u.startswith('http') and not u.lower().endswith('.pdf')), ''))
                else:
                    m, bits = C.flatten(md[0])
                    hist, doct, dept, deg = C.screen(m)
                    entry = dict(author=(m.get('dc.contributor.author') or m.get('dc.creator') or [''])[0],
                                 title=(m.get('dc.title') or [''])[0], year=((m.get('dc.date.issued') or [''])[0])[:4],
                                 dept='; '.join(sorted(set(dept)))[:200], degree='; '.join(sorted(set(deg)))[:200],
                                 item_url=next((v for v in m.get('dc.identifier.uri', []) if 'handle' in v or 'http' in v), ''),
                                 screen_passed=hist and doct,
                                 advisors=[v for k in m if re.search(r'contributor\.(advisor|supervisor)', k) for v in m[k]])
                meta.setdefault((key, rid_of(ident)), dict(entry, listing_host=host, oai_id=ident, listing_set=setname,
                                                           listing_route='OAI-PMH ListRecords saved by the user run (canada-listings)'))
    return meta


def surname_words(author):
    """Surname words of 'Surname, Given' or 'Given Surname'."""
    author = (author or '').strip()
    sur = author.split(',')[0] if ',' in author else (author.split() or [''])[-1]
    return [w for w in words(sur) if len(w) > 1]


def ocr_pages(path, last):
    """Text of pages 1..last of an image-only PDF by tesseract (eng), via a temporary directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdftoppm', '-f', '1', '-l', str(last), '-r', '200', '-gray', '-png', str(path), f'{tmp}/p'],
                       capture_output=True, check=True, timeout=300)
        out = []
        for png in sorted(Path(tmp).glob('p*.png')):
            out.append(subprocess.run(['tesseract', str(png), '-', '-l', 'eng'], capture_output=True, text=True,
                                      timeout=300, env={'OMP_THREAD_LIMIT': '1', 'PATH': '/usr/bin:/bin'}).stdout)
        return '\n'.join(out)


def validate(job):
    path, surname, title = job
    try:
        size = path.stat().st_size
        if not 1024 <= size <= 750*(1 << 20):
            raise ValueError('PDF size outside validation bounds')
        with path.open('rb') as handle:
            if not handle.read(1024).lstrip().startswith(b'%PDF'):
                raise ValueError('Missing PDF header (not a PDF)')
            handle.seek(max(0, size-65536))
            if b'%%EOF' not in handle.read():
                raise ValueError('Missing PDF EOF; incomplete download')
        info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, check=True, timeout=120)
        pages = int((re.search(r'(?m)^Pages:\s*(\d+)', info.stdout) or [0, 0])[1])
        if pages < 50:
            raise ValueError(f'Only {pages} pages; not counted as a full dissertation')
        opening = subprocess.run(['pdftotext', '-f', '1', '-l', '5', str(path), '-'],
                                 capture_output=True, text=True, check=True, timeout=120).stdout
        ocr = len(words(opening)) < 30
        if ocr:  # image-only scan (no text layer): read pages 1-5 with tesseract, in memory/temp only
            opening = ocr_pages(path, 5)
        flat = ' '.join(words(opening))
        tokens = flat.split()
        squashed = ''.join(tokens) if sum(len(w) == 1 for w in tokens) > 0.5 * max(len(tokens), 1) else ''
        if not (re.search(DOCTORATE, flat) or (squashed and re.search(r'doctorofphilos|doctoral|degreeofphd|doctorat', squashed))):
            raise ValueError('Opening pages do not read as a doctorate')
        present = set(tokens)
        if not surname or not (all(w in present for w in surname) or (squashed and ''.join(surname) in squashed)):
            raise ValueError(f'Listed author surname ({" ".join(surname) or "none"}) not on pages 1-5')
        tw = [w for w in words(title) if len(w) > 3]
        share = sum(bool(w in present or (squashed and w in squashed)) for w in tw) / len(tw) if tw else 0
        if share < 0.6:
            raise ValueError(f'Only {share:.0%} of the listed title words on pages 1-5')
        front = opening if ocr else subprocess.run(['pdftotext', '-f', '1', '-l', '2', str(path), '-'],
                                                   capture_output=True, text=True, check=True, timeout=120).stdout
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from register_aha_browser_downloads import front_years
        years = sorted(front_years(front))
        subprocess.run(['pdftotext', str(path), '/dev/null'], capture_output=True, check=True, timeout=600)
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            while chunk := handle.read(1 << 20):
                digest.update(chunk)
        if path.stat().st_size != size:
            raise OSError('File changed during validation')
        return path, dict(path=str(path), bytes=size, pages=pages, sha256=digest.hexdigest(), primary=True, part=1,
                          name=path.name), dict(title_share=round(share, 2), front_years=years, ocr=ocr), None
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return path, None, None, str(exc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--directory', type=Path, default=DEFAULT_DIRECTORY)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--recheck-held', action='store_true',
                    help="validate again the files held for 'held: validation' (their old held rows are replaced)")
    ap.add_argument('--recheck-kind', action='append', default=[], metavar='KIND',
                    help="take again the files held under this kind (e.g. 'held: adjacent (history of education)'); "
                         "their old held rows are replaced by this run's outcome")
    args = ap.parse_args()

    listed = {}
    for p in LISTS:
        for r in csv.DictReader(p.open(newline='', encoding='utf-8')):
            listed.setdefault(r['file'], dict(r, list=p.name))
    meta = listing_metadata({(r['university'], r['record_id']) for r in listed.values()})
    aha = {r['id']: r for r in csv.DictReader(AHA.open(newline='', encoding='utf-8'))}
    aha_links = {r['id']: r for r in csv.DictReader(AHA_MATCHES.open(newline='', encoding='utf-8'))} if AHA_MATCHES.exists() else {}
    aha_by_title = {}
    for r in aha.values():
        if r['status'] == 'completed':
            aha_by_title.setdefault(title_key(r['title']), r['id'])

    via_aha = {f['name']: r for r in rows(MANUAL_AHA/'downloads.jsonl') for f in r.get('files', [])
               if f.get('path', '').startswith(str(args.directory))}
    manual_ids = {r.get('aha_id') for r in rows(MANUAL_AHA/'records.jsonl')}
    held_t = held_titles()
    held_ids = held_aha_ids()
    held_by_title = collections.defaultdict(list)  # title key -> [(surname words, institution, id)] of extracted theses
    for r in csv.DictReader(HELD_PDFS.open(newline='', encoding='utf-8')):
        held_by_title[title_key(r['title'])].append((set(surname_words(r['author'])), r['institution'], r['id'], r['country']))
    for p in (FIELD/'us-dissertations-expansion-2026-10-20').glob('*/records.jsonl'):
        for r in rows(p):
            held_by_title[title_key(r.get('title'))].append(
                (set(surname_words((r.get('authors') or [''])[0])), r.get('institution'), r.get('id'), r.get('country')))
    hashes = {f.get('sha256') for p in (FIELD/'us-dissertations-expansion-2026-10-20').glob('*/downloads.jsonl')
              for r in rows(p) for f in r.get('files', [])}
    out_records = rows(args.out/'records.jsonl')
    hashes |= {f.get('sha256') for r in rows(args.out/'downloads.jsonl') for f in r.get('files', [])}
    old_held = rows(args.out/'held.jsonl')
    if args.recheck_held:
        old_held = [r for r in old_held if r.get('kind') != 'held: validation']
    if args.recheck_kind:
        old_held = [r for r in old_held if r.get('kind') not in set(args.recheck_kind)]
    reviewed = {}
    for p in sorted(args.out.glob('reviewed-*.csv')):
        reviewed.update({r['file']: r for r in csv.DictReader(p.open(newline='', encoding='utf-8'))})
    seen = {Path(r['source_pdf']).name for r in out_records} | {r['file'] for r in old_held}
    used_aha = {r.get('aha_id') for r in out_records if r.get('aha_id')}

    files = sorted(p for p in args.directory.glob('*.pdf'))
    plan, held, results = [], [], collections.defaultdict(collections.Counter)

    def hold(path, uni, reason, kind):
        results[uni][kind] += 1
        held.append(dict(at=now(), file=path.name, university=uni, reason=reason, kind=kind))

    for path in files:
        row = listed.get(path.name)
        uni = row['university'] if row else (path.name.split('-')[1] if path.name.startswith('ca-') else '?')
        if path.name in seen:
            results[uni]['seen before'] += 1
            continue
        if not row:
            hold(path, uni, 'File name not in either listing CSV', 'held: not listed')
            continue
        if path.name in via_aha:
            results[uni]['already registered (AHA title-page route)'] += 1
            continue
        rid = row['record_id']
        aha_id = rid[3:] if rid.startswith('aha') else (re.search(r'-aha(\d+)-', path.name) or [None, None])[1]
        m = meta.get((uni, rid)) if rid.startswith('oai-') else None
        a = aha.get(aha_id) if aha_id else None
        if rid.startswith('oai-') and not m:
            hold(path, uni, f'Listing record {rid} not found in the saved listings', 'held: no listing metadata')
            continue
        if m and m.get('screen_passed') is False:
            hold(path, uni, f"Listing record no longer passes the History doctorate screen ({m['dept']}; {m['degree']})",
                 'held: screen')
            continue
        scope = 'explicit_history_program_or_department'
        note = None
        if m:
            values = f"{m['dept']}; {m['degree']}"
            plain = re.search(r'(department of history\b(?! in art| of art)|\bhistory and classic|^history\b|; history\b|'
                              r'histoire|doctor of philosophy in history\b|economic history)', values, re.I)
            if re.search(r'art history|history (in|of) art', values, re.I) and not plain:
                hold(path, uni, f"Not History: art history programme ({m['dept'][:120]})", 'held: not History (art history)')
                continue
            if re.search(r'history of education', values, re.I) and not re.search(r'department of history\b', values, re.I):
                scope = 'history_of_education_programme'  # RULING 2026-11-16
                note = f"{RULING}; history of education PhD in an education faculty ({m['dept'][:120]})"
            if re.search(r'history and philosophy of science', values, re.I) and not re.search(r'department of history\b', values, re.I):
                scope = 'history_of_science_department'  # user decision 2026-11-04: history of science is history
        if not aha_id:
            aha_id = aha_by_title.get(title_key(row['title']))
            a = aha.get(aha_id) if aha_id else None
        author = (m or {}).get('author') or (a or {}).get('dissertator') or ''
        title = (m or {}).get('title') or row['title'] or (a or {}).get('title')
        plan.append(dict(path=path, uni=uni, row=row, rid=rid, meta=m, aha=a, aha_id=aha_id if a else None,
                         author=author, title=title, scope=scope, note=note))

    print(f'{len(files)} PDFs; {len(plan)} to validate', flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        checked = list(pool.map(validate, [(p['path'], surname_words(p['author']), p['title']) for p in plan]))

    new_records, new_downloads = [], []
    for p, (path, file, extra, error) in zip(plan, checked):
        uni, m, a, row = p['uni'], p['meta'], p['aha'], p['row']
        if error and a and p['title'] != a['title']:
            # an OAI title that differs from the AHA title: try the AHA wording before holding
            path2, file2, extra2, error2 = validate((path, surname_words(p['author']), a['title']))
            if not error2:
                file, extra, error = file2, extra2, None
        if error:
            hold(path, uni, error, 'held: validation')
            continue
        tk = title_key(p['title'])
        sur = set(surname_words(p['author']))
        same = [h for h in held_by_title.get(tk, []) if h[0] & sur]
        other = [h for h in held_by_title.get(tk, []) if not h[0] & sur]
        if file['sha256'] in hashes:
            hold(path, uni, 'Same file already registered under another record (sha256)', 'held: duplicate file')
            continue
        if p['aha_id'] and (p['aha_id'] in held_ids or p['aha_id'] in manual_ids):
            results[uni]['already held'] += 1
            held.append(dict(at=now(), file=path.name, university=uni, kind='already held',
                             reason=f"AHA record {p['aha_id']} already held or registered"))
            continue
        if same or (tk in held_t and not other):
            h = (same or [('', '', '', '')])[0]
            results[uni]['already held'] += 1
            held.append(dict(at=now(), file=path.name, university=uni, kind='already held',
                             reason=f'Title key already held ({h[1]} {h[2]})'.strip()))
            continue
        if other:
            h = other[0]
            hold(path, uni, f'Title key matches held thesis {h[1]} {h[2]} by another surname; review', 'held: title collision')
            continue
        if p['scope'] == 'history_of_science_department' and not a and not HISTORY_SIGNAL.search(p['title'] or ''):
            rv = reviewed.get(path.name)
            if rv and rv['decision'] == 'hold':
                hold(path, uni, f"Philosophy of science with no historical content (reviewed: {rv['note']}): {p['title'][:150]}",
                     'held: philosophy of science (reviewed)')
                continue
            if not rv or rv['decision'] != 'register':
                hold(path, uni, f"HPS programme thesis whose title shows no historical period, date or history wording "
                                f"(may be philosophy of science); decision needed: {p['title'][:150]}", 'held: adjacent (HPS, no history signal)')
                continue
            p['note'] = f"{RULING}; HPS thesis with historical content (reviewed: {rv['note']})"
        if p['aha_id'] and p['aha_id'] in used_aha:
            hold(path, uni, f"AHA record {p['aha_id']} already registered from another file here", 'held: duplicate record')
            continue
        hashes.add(file['sha256'])
        if p['aha_id']:
            used_aha.add(p['aha_id'])
        held_by_title[tk].append((sur, uni, p['rid'], 'CA'))
        stamp = now()
        year = int(row['year']) if row['year'].isdigit() else (int(a['year']) if a and a['year'].isdigit() else None)
        check = (f"file validated: {file['pages']} pages, every page parses, opening pages"
                 + (' (image-only scan, read by tesseract OCR)' if extra['ocr'] else '') + " read as a doctorate, "
                 f"author surname and {extra['title_share']:.0%} of the title words on pages 1-5")
        if m:
            basis = (f"Repository listing {m['listing_host']} ({m['listing_route']}; set {m['listing_set']}) "
                     f"passed user_run_canada.screen: department/discipline '{m['dept']}', degree '{m['degree']}'"
                     + (f"; AHA History PhD {a['id']} ({a['department']})" if a else '') + f'; {check}.')
            dept = [v.strip() for v in m['dept'].split(';') if v.strip()]
            degree = [v.strip() for v in m['degree'].split(';') if v.strip()] or ['Doctor of Philosophy']
            item_url = m.get('item_url') or ''
            advisors = m.get('advisors') or []
        else:
            link = aha_links.get(a['id']) or {}
            basis = (f"Completed AHA History PhD {a['id']} ({a['department']}); repository copy listed by "
                     f"user_run_canada ({row['host']}); {check}.")
            dept = [a['department'].split(', ')[-1]]
            degree = ['Doctor of Philosophy']
            item_url = link.get('landing_url') or ''
            advisors = []
        if a and a.get('advisors'):
            advisors = advisors or [x.strip() for x in a['advisors'].split(';') if x.strip()]
        authors = [p['author']] if p['author'] else ([a['dissertator']] if a else [])
        ident = f"aha_{a['id']}" if p['rid'].startswith('aha') else p['rid']
        ocap = OCAP.search(p['title'] or '')
        record = dict(
            institution=uni, institution_name=NAMES.get(uni, uni), id=ident, title=p['title'], authors=authors,
            advisors=advisors, year=year, candidate_years=[year] if year else [],
            issued_dates=[str(year)] if year else [], title_page_years=extra['front_years'],
            degree=degree, degree_classification='doctoral', programme='History', department_discipline=dept,
            eligibility='history_phd', eligibility_basis=basis, history_scope=p['scope'],
            aha_id=p['aha_id'], aha_record=a, country='CA', item_url=item_url, pdf_urls=[row['url']],
            listing_host=row['host'], listing_record_id=p['rid'], listing_list=row['list'],
            oai_id=(m or {}).get('oai_id'), access_category='user_supplied_pdf',
            source_harvest=str(args.out.relative_to(ROOT)), source_pdf=file['path'], source=SOURCE, checked_at=stamp,
            provenance_note='Original file left in place on E:; repository checksum not independently verified.')
        if p.get('note'):
            record['review_note'] = p['note']
            record['eligibility_basis'] += f" {p['note']}."
        if ocap:
            record['ocap_review'] = ('Title names Indigenous peoples or communities: OCAP review before any use beyond '
                                     'citation metadata (historiography-ocap-practice)')
        new_records.append(record)
        new_downloads.append(dict(institution=uni, id=ident, title=p['title'], item_url=item_url, country='CA',
                                  status='downloaded', checked_at=stamp, source=SOURCE, files=[file], chain=[]))
        results[uni]['registered'] += 1

    kinds = ['registered', 'already registered (AHA title-page route)', 'already held'] + \
        sorted({k for c in results.values() for k in c} - {'registered', 'already registered (AHA title-page route)', 'already held'})
    for uni in sorted(results):
        print(uni, dict(results[uni]))
    print('registered', len(new_records), 'held', len(held), '(dry run: nothing written)' if args.dry_run else '')
    if args.dry_run:
        return
    args.out.mkdir(parents=True, exist_ok=True)
    for name, items in (('records.jsonl', new_records), ('downloads.jsonl', new_downloads)):
        with (args.out/name).open('a') as f:
            for r in items:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with (args.out/'held.jsonl.tmp').open('w') as f:  # old rows (minus rechecked ones) + this run's
        for r in old_held + held:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    (args.out/'held.jsonl.tmp').replace(args.out/'held.jsonl')
    # summary over everything on file, not only this run
    results = collections.defaultdict(collections.Counter)
    for r in rows(args.out/'records.jsonl'):
        results[r['institution']]['registered'] += 1
    for r in rows(args.out/'held.jsonl'):
        results[r['university']][r['kind']] += 1
    for name in via_aha:
        results[listed.get(name, {}).get('university', '?')]['already registered (AHA title-page route)'] += 1
    kinds = ['registered', 'already registered (AHA title-page route)', 'already held'] + \
        sorted({k for c in results.values() for k in c} - {'registered', 'already registered (AHA title-page route)', 'already held'})
    with (args.out/'summary.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['university'] + kinds)
        for uni in sorted(results):
            w.writerow([uni] + [results[uni].get(k, 0) for k in kinds])
        w.writerow(['TOTAL'] + [sum(c.get(k, 0) for c in results.values()) for k in kinds])


if __name__ == '__main__':
    main()
