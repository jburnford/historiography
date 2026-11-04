#!/usr/bin/env python3
"""Register user-downloaded University of Chicago dissertation PDFs (Knowledge@UChicago) in place on E:.

The user downloaded the PDFs from Knowledge@UChicago in 13 zips (2026-11-03); they were unpacked
unchanged into ``<pdf store>/uchicago-2026-11-03/``. Each file name starts with the repository record
id (``0bk55-bkc26_Timmons_uchicago_0330D_16545.pdf``). No network requests: the repository's robots.txt
disallows its API, so metadata comes from each PDF's own title page and the AHA directory.

A file is registered only when the whole file validates (PDF header and EOF, 50+ pages, every page
parses) and the title page reads The University of Chicago, Doctor of Philosophy, and either:
- names the Department of History, or
- matches a completed AHA History PhD at Chicago (the AHA directory lists the department's own
  doctorates, joint degrees included): the AHA title's words on the title page (80% or more) and
  the dissertator's surname there.
The AHA record supplies author, title, year and advisors where it matches. Where the title changed
after the AHA listing, a record of the same person (surname and first given name, year within 3) still
supplies author and advisors, with the title page's title. Otherwise all are read from the title page (title above "A dissertation submitted", author after "By", year after
"Chicago, Illinois"). Everything else (art history, anthropology, classics...) is held in held.jsonl.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
FIELD = ROOT / 'data/field-research'
DEFAULT_DIRECTORY = Path('/mnt/e/historiography-dissertation-pdfs/uchicago-2026-11-03')
DEFAULT_OUT = FIELD / 'us-dissertations-expansion-2026-10-20/manual-uchicago'
AHA = FIELD / 'aha-dissertations-2026-10-13/records.csv'
AHA_DEPARTMENT = 'Univ. of Chicago, Graduate Dept. of History'
RECORD_URL = 'https://knowledge.uchicago.edu/records/{}'
SOURCE = ('User download from Knowledge@UChicago (13 zips, 2026-11-03), unpacked unchanged on E:; '
          'registered after local title-page and whole-file validation')


def now():
    return datetime.now(timezone.utc).isoformat()


def rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fold(text):
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold()


def words(text):
    return re.findall(r'[a-z0-9]+', fold(text))


def aha_match(page, aha):
    """The completed Chicago AHA History PhD whose title (80%+ of its longer words) and dissertator
    surname are on the title page; None if none or several."""
    present = set(words(page))
    hits = []
    for r in aha:
        title = [w for w in words(r['title']) if len(w) > 3]
        surname = [w for w in words(r['dissertator'].split(',')[0]) if len(w) > 1]
        if len(title) < 2 or not surname or not all(w in present for w in surname):
            continue
        score = sum(w in present for w in title) / len(title)
        if score >= 0.8:
            hits.append((score, r))
    hits.sort(key=lambda h: -h[0])
    if hits and (len(hits) == 1 or hits[0][0] > hits[1][0]):
        return hits[0]
    return None


def name_match(author, year, aha):
    """The completed Chicago AHA History PhD of the same person when the title changed after the AHA
    listing: surname and first given name equal to the title page's, AHA year within 3 years; None
    unless exactly one."""
    names = words(author)
    if len(names) < 2 or not year:
        return None
    hits = []
    for r in aha:
        surname, _, given = r['dissertator'].partition(',')
        sur, giv = words(surname), words(given)
        if not sur or not giv or giv[0] != names[0] or abs(int(r['year']) - year) > 3:
            continue
        if ' '.join(sur) in ' '.join(names[1:]):
            hits.append(r)
    return hits[0] if len(hits) == 1 else None


SMALL = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'from', 'in', 'into', 'of', 'on', 'or', 'the', 'to', 'with',
         'de', 'del', 'des', 'du', 'la', 'le', 'y', 'e', 'da', 'do', 'dos', 'das', 'van', 'von', 'der'}


def unshout(text):
    """Title case for an all-capitals title-page line ('VENENUM BIBIT: THE POISON TRIAL' -> 'Venenum Bibit: The
    Poison Trial'); text that is mostly lower case is returned as it is."""
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) < 0.8 * len(letters):
        return text
    out = []
    for i, w in enumerate(text.split()):
        low = w.lower()
        first = i == 0 or out[-1].endswith((':', '—', '?'))
        if re.fullmatch(r'\W*c\.(?:\d.*)?|\d+(?:st|nd|rd|th)\W*', low):     # c.1665, (c. 1900), 19th
            out.append(low)
        elif re.fullmatch(r'[ivxl]+[.,:]?', low) and low not in SMALL:  # roman numerals
            out.append(w.upper())
        elif low in SMALL and not first:
            out.append(low)
        else:
            out.append('-'.join(re.sub(r'^(\W*)(mc)?(\w)', lambda m: m[1] + ('Mc' if m[2] else '') + m[3].upper(), q)
                                if not (q.startswith('mc') and len(q) <= 3) else q.capitalize() for q in low.split('-')))
    return ' '.join(out)


def inverted(author, hint):
    """'JOSÉ CAMILO RUIZ TASSINARI' -> 'Ruiz Tassinari, José Camilo', taking the surname from the file
    name ('RuizTassinari') where it ends the name, else the last word."""
    parts = unshout(author).split()
    key = re.sub(r'[^a-z]', '', fold(hint))
    for k in range(min(4, len(parts) - 1), 0, -1):
        if key and re.sub(r'[^a-z]', '', fold(''.join(parts[-k:]))) == key:
            return f"{' '.join(parts[-k:])}, {' '.join(parts[:-k])}"
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else author


def title_page(text):
    """(title, author, year) read from a UChicago title page; parts not found are ''/None."""
    lines = [' '.join(l.split()) for l in text.splitlines()]
    lines = [l for l in lines if l]
    upper = [fold(l) for l in lines]
    start = next((i + 1 for i, l in enumerate(upper) if 'university of chicago' in l), 0)
    end = next((i for i, l in enumerate(upper) if l.startswith('a dissertation submitted')), None)
    title = ' '.join(lines[start:end]) if end and end > start else ''
    author = ''
    for i, l in enumerate(upper):
        if l == 'by' and i + 1 < len(lines):
            author = lines[i + 1]
            break
        if l.startswith('by ') and end is not None and i > end:
            author = lines[i][3:]
            break
    year = None
    flat = ' '.join(upper)
    m = re.search(r'chicago,? ill\w*,? (?:[a-z]+ )?((?:19|20)\d\d)', flat)  # 'ILLIONIS' on one
    if m:
        year = int(m.group(1))
    return title, author, year


def validate(path, aha):
    size = path.stat().st_size
    if not 1024 <= size <= 750 * (1 << 20):
        raise ValueError('PDF size outside validation bounds')
    with path.open('rb') as handle:
        if not handle.read(1024).lstrip().startswith(b'%PDF'):
            raise ValueError('Missing PDF header')
        handle.seek(max(0, size - 65536))
        if b'%%EOF' not in handle.read():
            raise ValueError('Missing PDF EOF; incomplete file')
    info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, check=True, timeout=120)
    match = re.search(r'(?m)^Pages:\s*(\d+)', info.stdout)
    pages = int(match.group(1)) if match else 0
    if pages < 50:
        raise ValueError(f'Only {pages} pages; not counted as a full dissertation')
    first = subprocess.run(['pdftotext', '-layout', '-f', '1', '-l', '1', str(path), '-'],
                           capture_output=True, text=True, check=True, timeout=120).stdout
    opening = subprocess.run(['pdftotext', '-f', '1', '-l', '3', str(path), '-'],
                             capture_output=True, text=True, check=True, timeout=120).stdout
    flat = ' '.join(words(opening))
    if 'university of chicago' not in flat:
        raise ValueError('Title page does not name The University of Chicago')
    if not re.search(r'doctor of philos\w*', flat):  # 'PHILOSPHY' on one title page
        raise ValueError('Title page does not read Doctor of Philosophy')
    history = bool(re.search(r'\bdepartment of history\b', flat))
    matched = aha_match(first if aha_match(first, aha) else opening, aha)
    if not history and not matched:
        dept = re.search(r'\b(department|committee|divinity school|program) (?:of|on|in) ((?:\w+ ){1,6})', flat)
        raise ValueError('Not a History PhD: title page names '
                         + (f'{dept.group(1)} of {dept.group(2).strip()}' if dept else 'no Department of History')
                         + ' and no completed Chicago AHA History PhD matches')
    subprocess.run(['pdftotext', str(path), '/dev/null'], capture_output=True, check=True, timeout=600)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    if path.stat().st_size != size:
        raise OSError('File changed during validation')
    title, author, year = title_page(opening)
    return dict(path=str(path), bytes=size, pages=pages, sha256=digest.hexdigest(), primary=True, part=1,
                name=path.name), dict(history=history, aha=matched, title=title, author=author, year=year)


def check(job):
    path, aha = job
    try:
        file, page = validate(path, aha)
        return path, file, page, None
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return path, None, None, str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--directory', type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    aha = [r for r in csv.DictReader(open(AHA, encoding='utf-8'))
           if r['department'] == AHA_DEPARTMENT and r['status'] == 'completed']
    done = {r['id'] for r in rows(args.out / 'downloads.jsonl') if r.get('status') == 'downloaded'}
    hashes = {f['sha256'] for r in rows(args.out / 'downloads.jsonl') for f in r.get('files', [])}
    held_before = {r['file'] for r in rows(args.out / 'held.jsonl')}
    jobs, skipped = [], 0
    for path in sorted(args.directory.glob('*.pdf')):
        record_id = path.name.split('_', 1)[0]
        if not re.fullmatch(r'[a-z0-9]{5}-[a-z0-9]{5}', record_id):
            raise SystemExit(f'unexpected file name (no record id): {path.name}')
        if f'uchicago_{record_id}' in done or path.name in held_before:
            skipped += 1
            continue
        jobs.append((path, aha))
    print(f'{len(jobs) + skipped} files: {skipped} already seen, {len(jobs)} to validate', flush=True)
    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)

    registered = held = 0
    aha_used = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for path, file, page, error in pool.map(check, jobs):
            record_id = path.name.split('_', 1)[0]
            identifier = f'uchicago_{record_id}'
            stamp = now()
            match = page and page['aha']
            if not error and file['sha256'] in hashes:
                error = 'Same file already registered under another record'
            if not error and match and match[1]['id'] in aha_used:
                error = f'AHA record {match[1]["id"]} already matched by {aha_used[match[1]["id"]]}'
            if not error and not match and page['author']:
                hit = name_match(page['author'], page['year'], [r for r in aha if r['id'] not in aha_used])
                if hit:
                    match = page['aha'] = (None, hit)
            if not error and not match and not (page['title'] and page['author'] and page['year']):
                error = f'Title page not read (title {bool(page["title"])}, author {bool(page["author"])}, year {page["year"]})'
            if error:
                held += 1
                print('held', path.name, '-', error, flush=True)
                if not args.dry_run:
                    with (args.out / 'held.jsonl').open('a') as handle:
                        handle.write(json.dumps(dict(at=stamp, file=path.name, item_url=RECORD_URL.format(record_id),
                                                     reason=error), ensure_ascii=False) + '\n')
                continue
            hashes.add(file['sha256'])
            registered += 1
            if match:
                score, row = match
                aha_used[row['id']] = path.name
                title, authors, year = row['title'], [row['dissertator']], int(row['year'])
                advisors = [a.strip() for a in row['advisors'].split(';') if a.strip()] if row.get('advisors') else []
                how = (f'matched on the title page (title words {score:.0%}, dissertator surname)' if score is not None else
                       'matched by name and year (surname and first given name on the title page, AHA year within 3); '
                       'the title changed after the AHA listing, so the title page\'s title is used')
                if score is None:
                    title = unshout(page['title']) or title
                    year = page['year'] or year
                basis = (f'Title page reads Doctor of Philosophy, The University of Chicago'
                         f'{", Department of History" if page["history"] else ""}; completed AHA History PhD {row["id"]} '
                         f'({row["department"]}) {how}.')
            else:
                hint = path.name.split('_')[1].split('-')[0] if '_' in path.name else ''
                row, title, authors, year, advisors = (None, unshout(page['title']), [inverted(page['author'], hint)],
                                                       page['year'], [])
                basis = ('Title page reads Doctor of Philosophy, The University of Chicago, Department of History; '
                         'no AHA record matched, so title, author and year are read from the title page.')
            print('registered', path.name, '-', 'AHA ' + row['id'] if row else 'title page', '-', authors[0], year,
                  '-', title[:70], flush=True)
            if args.dry_run:
                continue
            record = dict(
                institution='uchicago', institution_name='University of Chicago', id=identifier, title=title,
                authors=authors, advisors=advisors, year=year, candidate_years=[year], degree=['Doctor of Philosophy'],
                degree_classification='doctoral', programme='History', department_discipline=['History'],
                eligibility='history_phd', eligibility_basis=basis,
                history_scope='explicit_history_program_or_department', aha_id=row['id'] if row else None,
                aha_record=row, country='US', item_url=RECORD_URL.format(record_id), pdf_urls=[],
                access_category='user_supplied_pdf', source_harvest=str(args.out.relative_to(ROOT)),
                source_pdf=file['path'], source=SOURCE, checked_at=stamp,
                provenance_note='Unpacked unchanged from the user\'s zips; repository checksum not independently verified.')
            result = dict(institution='uchicago', id=identifier, title=title, item_url=record['item_url'], country='US',
                          status='downloaded', checked_at=stamp, source=SOURCE, files=[file], chain=[])
            with (args.out / 'records.jsonl').open('a') as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            with (args.out / 'downloads.jsonl').open('a') as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f'registered {registered}, held {held}, already seen {skipped}'
          + (' (dry run: nothing written)' if args.dry_run else ''), flush=True)


if __name__ == '__main__':
    main()
