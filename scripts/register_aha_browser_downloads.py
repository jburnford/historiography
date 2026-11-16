#!/usr/bin/env python3
"""Register user-downloaded AHA History dissertation PDFs (browser route) in place on E:.

Companion to ``find_aha_repository_links.py`` (2026-11-04): the user saves PDFs from its link
pages into one folder (default ``<pdf store>/aha-browser-2026-11-04/``). Chrome keeps each
repository's own file name, so files are tied to records by their title pages, not their names.
No network requests, moves or writes to E:.

A file is registered only when the whole file validates (PDF header and EOF, 50+ pages, every page
parses), its opening pages read as a doctorate (Doctor of Philosophy, PhD, doctoral) and exactly
one completed AHA History PhD matches them: 80% or more of the AHA title's longer words and the
dissertator's surname on pages 1-5, then, among several, the best score if it is unique (or, when the
title changed, the dissertator's full name and university). Since 2026-11-15 every candidate must also
pass consistent(): the dissertator as a name on pages 1-5 outside supervisor/committee lines, no thesis
date on pages 1-2 well after the AHA year, and no contradiction with an AHA id, surname or year in the
file name (see the note above consistent() for the false matches that prompted it). The AHA
record supplies author, title, year, advisors and department; the department sets the institution
code (``INSTITUTIONS``, existing codes kept so coverage tables merge). Everything else is held in
held.jsonl with its reason.

Records go to ``us-dissertations-expansion-2026-10-20/manual-aha-2026-11-04/`` (records.jsonl,
downloads.jsonl), which ``audit_us_dissertation_collection.py`` finds and the ingest reads. Canadian
departments are registered with ``country: CA``.
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
FIELD = ROOT/'data/field-research'
AHA = FIELD/'aha-dissertations-2026-10-13/records.csv'
LINKS = FIELD/'aha-repository-links-2026-11-04/matches.csv'
DEFAULT_DIRECTORY = Path('/mnt/e/historiography-dissertation-pdfs/aha-browser-2026-11-04')
DEFAULT_OUT = FIELD/'us-dissertations-expansion-2026-10-20/manual-aha-2026-11-04'
SOURCE = ('User browser download on E: from the OpenAlex/DataCite-matched AHA link pages '
          '(find_aha_repository_links.py); registered after local title-page and whole-file validation')

# AHA department prefix -> institution code already used in doctorates.json (first match wins).
INSTITUTIONS = [
    ('Univ. of California, Berkeley', 'ucberkeley'), ('Univ. of California, Davis', 'ucdavis'),
    ('Univ. of California, Irvine', 'ucirvine'), ('Univ. of California, Los Angeles', 'ucla'),
    ('Univ. of California, Riverside', 'ucriverside'), ('Univ. of California, San Diego', 'ucsd'),
    ('Univ. of California, Santa Barbara', 'ucsb'), ('Univ. of California, Santa Cruz', 'ucsantacruz'),
    ('Univ. of Chicago', 'uchicago'), ('Harvard Univ.', 'harvard'), ('Yale Univ.', 'yale'),
    ('Univ. of Pennsylvania', 'penn'), ('Stanford Univ.', 'stanford'), ('Duke Univ.', 'duke'),
    ('Johns Hopkins Univ.', 'johnshopkins'), ('Cornell Univ.', 'cornell'), ('Rice Univ.', 'rice'),
    ('Vanderbilt Univ.', 'vanderbilt'), ('Univ. of Michigan', 'michigan'), ('Univ. of Maryland', 'maryland'),
    ('Univ. of Minnesota', 'minnesota'), ('Univ. of New Mexico', 'newmexico'), ('Univ. of Oklahoma', 'oklahoma'),
    ('Univ. of Tennessee', 'tennessee'), ('Univ. of Virginia', 'virginia'), ('Univ. of Washington', 'washington'),
    ('Univ. of Wisconsin, Madison', 'wisconsinmadison'), ('Univ. of North Carolina, Chapel Hill', 'unc'),
    ('Univ. of Florida', 'florida'), ('Univ. of Kansas', 'kansas'), ('Univ. of Kentucky', 'kentucky'),
    ('Univ. of Alabama', 'alabama'), ('Univ. of Arizona', 'arizona'), ('Univ. of Arkansas', 'arkansas'),
    ('Univ. of Nebraska', 'nebraska'), ('Univ. of South Carolina', 'southcarolina'), ('Temple Univ.', 'temple'),
    ('Louisiana State Univ.', 'lsu'), ('Southern Methodist Univ.', 'smu'),
    ('Univ. of Alberta', 'alberta'), ('Univ. of Calgary', 'calgary'), ('Carleton Univ.', 'carleton'),
    ('Concordia Univ., Can.', 'concordia'), ('Dalhousie Univ.', 'dalhousie'), ('Univ. of Guelph', 'guelph'),
    ('Wilfrid Laurier Univ.', 'laurier'), ('Univ. Laval', 'laval'), ('Univ. of Manitoba', 'manitoba'),
    ('McGill Univ.', 'mcgill'), ('McMaster Univ.', 'mcmaster'), ('Memorial Univ.', 'memorial'),
    ('Univ. de Montreal', 'montreal'), ('Univ. of Ottawa', 'ottawa'), ("Queen's Univ., Can.", 'queens'),
    ('Simon Fraser Univ.', 'sfu'), ('Univ. of Toronto', 'toronto'), ('Univ. of British Columbia', 'ubc'),
    ('Univ. of New Brunswick', 'unb'), ('Univ. du Quebec, Montreal', 'uqam'), ('Univ. of Saskatchewan', 'usask'),
    ('Univ. of Victoria', 'uvic'), ('Univ. of Waterloo', 'waterloo'), ('Univ. of Western Ontario', 'western'),
    ('York Univ.', 'york'),
    # new institutions with short codes
    ('Princeton Univ.', 'princeton'), ('Columbia Univ.', 'columbia'), ('New York Univ.', 'nyu'),
    ('Graduate Center, CUNY', 'cuny'), ('Ohio State Univ.', 'ohiostate'), ('Rutgers', 'rutgers'),
    ('Univ. of Texas, Austin', 'texasaustin'), ('Texas A&M Univ.', 'texasam'),
    ('Univ. of Illinois, Urbana-Champaign', 'illinois'), ('Univ. of Notre Dame', 'notredame'),
]
CANADA = {'alberta', 'calgary', 'carleton', 'concordia', 'dalhousie', 'guelph', 'laurier', 'laval', 'manitoba',
          'mcgill', 'mcmaster', 'memorial', 'montreal', 'ottawa', 'queens', 'sfu', 'toronto', 'ubc', 'unb', 'uqam',
          'usask', 'uvic', 'waterloo', 'western', 'york', 'rmc', 'trent'}


def now():
    return datetime.now(timezone.utc).isoformat()


def rows(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold()


def words(text):
    return re.findall(r'[a-z0-9]+', fold(text))


def institution(department):
    """(code, display name) for an AHA department; new institutions get a slug of the AHA name."""
    for prefix, code in INSTITUTIONS:
        if department.startswith(prefix):
            return code, prefix
    parts = [p.strip() for p in department.split(',')]
    unit = re.compile(r'(Dept|Dépt|School|Sch\.|Prog|Program|Center|Centre|History|Historical)')
    name = parts[0]
    for part in parts[1:]:  # campus or system qualifiers ('Columbus', 'State Univ. of New York'), not the unit
        if unit.match(part) or 'Dept' in part:
            break
        name += ', ' + part
    # whole words only: 'Catholic', 'Northeastern' and 'Cincinnati' keep their letters; Coll. stays distinct
    slug = ''.join({'coll': 'college'}.get(w, w) for w in words(name)
                   if w not in {'univ', 'of', 'the', 'at', 'inst', 'can'})
    return slug or 'unknown', name


# 2026-11-15: false matches under --since 1900 (a 2018 Western thesis registered as AHA 57191
# 'Taylor, Edith 1937'; a 2011 Toronto thesis by 'Christopher David Marshall Ernst' as AHA 38522
# 'Marshall, David 1987'). Causes: (a) the surname could be any word on pages 1-5 (acknowledgements,
# abstract, cited authors: 'Jones', 'Scott', 'Taylor', 'Wilson'), and a short, generic AHA title
# ('History of the British Post Office, 1830-40') reaches 80% on most theses that use its words;
# (b) the full-name route matched a run of the author's own middle names ('David Marshall' inside
# 'Christopher David Marshall Ernst') or a supervisor; (c) nothing compared the AHA year with the
# title page or the file name. Now every candidate must also pass consistent(): the dissertator as a
# name on pages 1-5 outside supervisor/committee lines (name_on_pages: a short name line, or given
# name/initial + surname), no
# thesis date on pages 1-2 after the AHA year + YEAR_WINDOW without one near the AHA year, and no
# contradiction with an AHA id, surname or year carried in the file name. A file whose first candidate fails falls through to the next route.
YEAR_WINDOW = 3
ROLE = re.compile(r'(supervis|advis[oe]r|committee|examin|director|directeur|directrice|chair\b|reader|'
                  r'approv|accepted by|\bdean\b|professor|\bprof\b|\bjury\b|membres? du|signature|co-?direct)', re.I)


def byline_text(text):
    """Lines of these pages (folded words) outside lines naming supervisors, committee members or examiners."""
    return [' '.join(words(line)) for line in text.splitlines() if not ROLE.search(line) and words(line)]


def name_on_pages(row, lines):
    """The dissertator as a name on the pages (``lines`` from byline_text): the surname on a short line
    of at most 8 words (title-page byline, copyright line), or the first given name / its initial within
    three words before the surname. A surname inside running text is not enough ('Bennett Jones LLP' in
    the acknowledgements). Given names are not required on short lines: the AHA directory often lists
    the dissertator under a short form (Tim, Mike, Jen) or another spelling (Allison / Alison)."""
    surname, _, given = row['dissertator'].partition(',')
    sur, giv = ' '.join(words(surname)), words(given)
    if not sur:
        return False
    at = re.compile(rf'\b{sur}\b')
    if any(sum(len(w) > 1 for w in l.split()) <= 8 and at.search(l) for l in lines):  # letter-spaced names count short
        return True
    flat = ' '.join(lines)
    if giv:
        first = giv[0]
        forms = [rf'\b{first}\b(?: \w+){{0,3}} {sur}\b', rf'\b{sur} {first}\b', rf'\b{first[0]}\b(?: \w+){{0,3}} {sur}\b']
        return any(re.search(f, flat) for f in forms)
    return False


YEAR = r'\b(1[89]\d\d|20[0-3]\d)\b'
RANGE = r'\b(1[5-9]\d\d|20[0-3]\d)\s*(?:[-–—/]|to|à)\s*(\d{4}|\d{2})\b'
# lines whose years date a reproduction, a download or a link, not the thesis
NOT_THESIS_DATE = re.compile(r'(proquest|\bumi\b|microfi|microform|library and archives|biblioth[eè]que et archives|'
                             r'reproduc|download|https?:|\d{1,2}/\d{1,2}/\d{4})', re.I)


def content_years(text):
    """Years inside ranges ('1945-1965', '1945-65'): dates of the subject, not of the thesis."""
    out = set()
    for a, b in re.findall(RANGE, text):
        out |= {int(a), int(b) if len(b) == 4 else int(a[:2] + b)}
    return out


def front_years(front):
    """Years printed on pages 1-2 that may date the thesis (ranges in its title, reproduction notices,
    download stamps and links left out). Earlier degrees (B.A. 2005) remain: see consistent()."""
    text = '\n'.join(l for l in front.splitlines() if not NOT_THESIS_DATE.search(l))
    return {int(y) for y in re.findall(YEAR, text)} - content_years(text)


def file_hints(name):
    """(aha id, surname words, year) carried by a file name built by this project's download lists:
    'ca-<uni>-<record>[-aha<ID>]-<Surname>-<YEAR>.pdf' and 'aha-b<N>-<Surname>-<Given>-<YEAR>-<Univ>-...'.
    Repository file names give (None, set(), None)."""
    stem = Path(name).stem
    aha_id = (re.search(r'(?:^|-)aha(\d+)(?:-|$)', stem) or [None, None])[1]
    parts = stem.split('-')
    names, year = set(), None
    if re.match(r'(ca|us)-', stem) and parts[-1].isdigit() and len(parts[-1]) == 4:
        year = int(parts[-1])
        for p in reversed(parts[:-1]):
            if any(c.isdigit() for c in p) or p in ('oai', 'aha'):
                break
            names |= set(words(p))
    elif re.match(r'aha-b\d+-', stem):
        at = next((i for i, p in enumerate(parts[2:], 2) if re.fullmatch(r'(19|20)\d\d', p)), None)
        if at:
            year = int(parts[at])
            names = {w for p in parts[2:at] for w in words(p)}
    return aha_id, names, year


def consistent(row, ctx):
    """None if AHA record ``row`` fits this file, else the reason it cannot be the thesis on it."""
    surname = [w for w in words(row['dissertator'].split(',')[0]) if len(w) > 1]
    if not surname or not (name_on_pages(row, ctx['names'])
                           or (ctx.get('squash') and len(''.join(surname)) > 3 and ''.join(surname) in ctx['squash'])):
        return 'dissertator surname not on a name line (or with the given name) on pages 1-5 outside supervisor/committee lines'
    year = int(row['year'])
    title_years = {int(y) for y in re.findall(YEAR, row['title'])} | content_years(row['title'])
    years = ctx['years'] - title_years
    # One-sided: a thesis cannot print a date long after its AHA completion year, but its front pages
    # carry earlier years (prior degrees, subject dates) and the AHA year can lag the thesis by years.
    if any(y > year + YEAR_WINDOW for y in years) and not any(year - 8 <= y <= year + YEAR_WINDOW for y in years):
        return f'pages 1-2 date the thesis after AHA {year} ({", ".join(map(str, sorted(years)))})'
    hint_id, hint_names, hint_year = ctx['hints']
    if hint_id and hint_id != row['id']:
        return f'file name carries AHA id {hint_id}'
    if hint_names and not any(w in hint_names for w in surname):
        return f'file name surname ({" ".join(sorted(hint_names))}) differs'
    if hint_year and abs(hint_year - year) > YEAR_WINDOW:
        return f'file name year {hint_year} differs from AHA {year}'
    return None


def best(hits, ctx, rejected):
    """The unique best-scoring consistent candidate of [(score, record)], else None."""
    kept = []
    for score, r in hits:
        why = consistent(r, ctx)
        if why:
            rejected.append(f"AHA {r['id']} ({r['dissertator']} {r['year']}): {why}")
        else:
            kept.append((score, r))
    kept.sort(key=lambda h: -(h[0] or 0))
    if kept and (len(kept) == 1 or (kept[0][0] or 0) > (kept[1][0] or 0)):
        return kept[0]
    return None


def aha_match(text, aha):
    """[(score, record)]: completed AHA History PhDs with 80%+ of their title's longer words and a
    surname word on these pages (consistent() then checks where the surname is)."""
    present = set(words(text))
    hits = []
    for r in aha:
        title = [w for w in words(r['title']) if len(w) > 3]
        surname = [w for w in words(r['dissertator'].split(',')[0]) if len(w) > 1]
        if len(title) < 2 or not surname or not any(w in present for w in surname):
            continue
        score = sum(w in present for w in title) / len(title)
        if score >= 0.8:
            hits.append((score, r))
    return hits


STOP = {'univ', 'of', 'the', 'at', 'inst', 'can', 'coll', 'state', 'dept', 'and'}


def name_match(text, aha):
    """For a title changed after the AHA listing (as register_uchicago_downloads.py): [(None, record)]
    for completed AHA History PhDs whose dissertator's first given name and surname appear together
    (the surname ending a name: not followed by a further capitalised name word, so 'David Marshall'
    inside 'Christopher David Marshall Ernst' does not count) and whose university's name words all
    appear on the opening pages. best() keeps it only if exactly one is consistent."""
    flat = ' '.join(words(text))
    present = set(flat.split())
    # name runs as printed: capitalised words (or all caps) on one line
    runs = [' '.join(words(m.group(0))) for line in text.splitlines()
            for m in re.finditer(r"(?:\b(?:[A-ZÀ-Þ][\w'’.-]*|de|du|des|la|le|van|von|der|den|di|da|del|dos)\s+){1,6}"
                                 r"[A-ZÀ-Þ][\w'’-]*", line)]
    hits = []
    for r in aha:
        surname, _, given = r['dissertator'].partition(',')
        sur, giv = words(surname), words(given)
        if not sur or not giv or len(giv[0]) < 2 or sur[-1] not in present or giv[0] not in present:
            continue
        pattern = re.compile(rf'\b{giv[0]}\b(?: \w+){{0,3}} {" ".join(sur)}$')
        if not any(pattern.search(run) for run in runs):
            continue
        place = [w for w in words(institution(r['department'])[1]) if w not in STOP and len(w) > 2]
        if place and all(w in present for w in place):
            hits.append((None, r))
    return hits


def squashed_match(squashed, aha):
    """aha_match for letter-spaced text: title words and surname as substrings of the space-free text."""
    hits = []
    for r in aha:
        title = [w for w in words(r['title']) if len(w) > 4]
        surname = ''.join(words(r['dissertator'].split(',')[0]))
        if len(title) < 3 or len(surname) < 4 or surname not in squashed:
            continue
        score = sum(w in squashed for w in title) / len(title)
        if score >= 0.8:
            hits.append((score, r))
    return hits


def match_file(path, opening, front, squashed, aha):
    """(match, rejected): the first route with a unique consistent candidate (title words and
    surname; full name and university; letter-spaced text), and why other candidates were refused."""
    names = byline_text(opening)
    ctx = dict(names=names, years=front_years(front), hints=file_hints(path.name),
               # letter-spaced pages: the surname is judged on the space-free text
               squash=''.join(names).replace(' ', '') if squashed else '')
    rejected = []
    for hits in (lambda: aha_match(opening, aha), lambda: name_match(front, aha),
                 lambda: squashed_match(squashed, aha) if squashed else []):
        found = best(hits(), ctx, rejected)
        if found:
            return found, rejected
    return None, rejected


def validate(path, aha):
    size = path.stat().st_size
    if not 1024 <= size <= 750*(1 << 20):
        raise ValueError('PDF size outside validation bounds')
    with path.open('rb') as handle:
        if not handle.read(1024).lstrip().startswith(b'%PDF'):
            raise ValueError('Missing PDF header')
        handle.seek(max(0, size-65536))
        if b'%%EOF' not in handle.read():
            raise ValueError('Missing PDF EOF; incomplete download')
    info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, check=True, timeout=120)
    match = re.search(r'(?m)^Pages:\s*(\d+)', info.stdout)
    pages = int(match.group(1)) if match else 0
    if pages < 100:  # 2026-11-05: a 78-page article manuscript matched its author's thesis title
        raise ValueError(f'Only {pages} pages; not counted as a full dissertation')
    opening = subprocess.run(['pdftotext', '-f', '1', '-l', '5', str(path), '-'],
                             capture_output=True, text=True, check=True, timeout=120).stdout
    flat = ' '.join(words(opening))
    # Letter-spaced scans ('P L A C E I N R E T U R N', MSU library copies): judge them on the
    # text with all spaces removed.
    squashed = ''.join(words(opening)) if sum(len(w) == 1 for w in flat.split()) > 0.5 * max(len(flat.split()), 1) else ''
    doctorate = r'doctor of philos\w*|\bph ?d\b|\bdoctoral\b|doctorat|philosophiae doctor|\bthese\b'
    if not (re.search(doctorate, flat) or (squashed and re.search(r'doctorofphilos|doctoral|degreeofphd', squashed))):
        raise ValueError('Opening pages do not read as a doctorate')
    # Names only from the first two pages: acknowledgements on pages 3-5 name colleagues of the same department.
    front = subprocess.run(['pdftotext', '-f', '1', '-l', '2', str(path), '-'],
                           capture_output=True, text=True, check=True, timeout=120).stdout
    matched, rejected = match_file(path, opening, front, squashed, aha)
    if not matched:
        raise ValueError('No unique completed AHA History PhD matches the opening pages '
                         '(title words and surname, or full name and university)'
                         + (f'; refused: {"; ".join(rejected[:3])}' if rejected else ''))
    subprocess.run(['pdftotext', str(path), '/dev/null'], capture_output=True, check=True, timeout=600)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    if path.stat().st_size != size:
        raise OSError('File changed during validation')
    return dict(path=str(path), bytes=size, pages=pages, sha256=digest.hexdigest(), primary=True, part=1,
                name=path.name), matched


def check(job):
    path, aha = job
    try:
        file, matched = validate(path, aha)
        return path, file, matched, None
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return path, None, None, str(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--directory', type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--links', type=Path, default=LINKS)
    parser.add_argument('--since', type=int, default=2005, help='earliest AHA year a file may match')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--files', nargs='*', help='only these file names inside --directory')
    parser.add_argument('--recheck-held', action='store_true', help='validate files held before again')
    args = parser.parse_args()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from find_aha_repository_links import held_titles, held_aha_ids, title_key
    held_set = held_titles()
    held_ids = held_aha_ids() - {r.get('aha_id') for r in rows(args.out/'records.jsonl')}

    aha = [r for r in csv.DictReader(open(AHA, encoding='utf-8'))
           if r['status'] == 'completed' and r['year'].isdigit() and int(r['year']) >= args.since
           and not r['title'].startswith('[')]
    links = {}
    if args.links.exists():
        links = {r['id']: r for r in csv.DictReader(open(args.links, encoding='utf-8', newline=''))}
    seen = {f.get('name') for r in rows(args.out/'downloads.jsonl') for f in r.get('files', [])}
    if not args.recheck_held:
        seen |= {r['file'] for r in rows(args.out/'held.jsonl')}
    hashes = {f['sha256'] for r in rows(args.out/'downloads.jsonl') for f in r.get('files', [])}
    used = {r.get('aha_id') for r in rows(args.out/'records.jsonl')}
    files = sorted(p for p in args.directory.glob('*') if p.suffix.lower() == '.pdf'
                   and (not args.files or p.name in args.files))
    jobs = [(p, aha) for p in files if p.name not in seen]
    print(f'{len(files)} files: {len(files) - len(jobs)} already seen, {len(jobs)} to validate', flush=True)
    if not args.dry_run:
        args.out.mkdir(parents=True, exist_ok=True)

    registered = held = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for path, file, matched, error in pool.map(check, jobs):
            stamp = now()
            if not error and file['sha256'] in hashes:
                error = 'Same file already registered under another record'
            if not error and (title_key(matched[1]["title"]) in held_set or matched[1]["id"] in held_ids):
                error = f'AHA record {matched[1]["id"]} is already in the graph (thesis held)'
            if not error and matched[1]['id'] in used:
                error = f'AHA record {matched[1]["id"]} already registered from another file'
            if error:
                held += 1
                print('held', path.name, '-', error, flush=True)
                if not args.dry_run:
                    with (args.out/'held.jsonl').open('a') as handle:
                        handle.write(json.dumps(dict(at=stamp, file=path.name, reason=error), ensure_ascii=False)+'\n')
                continue
            score, row = matched
            hashes.add(file['sha256'])
            used.add(row['id'])
            registered += 1
            code, name = institution(row['department'])
            link = links.get(row['id']) or {}
            item_url = link.get('landing_url') or link.get('pdf_url') or ''
            print('registered', path.name, '-', code, 'AHA', row['id'], '-', row['dissertator'], row['year'],
                  '-', row['title'][:60], flush=True)
            if args.dry_run:
                continue
            identifier = 'aha_' + row['id']
            advisors = [a.strip() for a in row['advisors'].split(';') if a.strip()] if row.get('advisors') else []
            how = (f'title words {score:.0%}, dissertator surname' if score is not None else
                   'dissertator full name and university name; the title differs from the AHA listing')
            basis = (f'Opening pages read as a doctorate; completed AHA History PhD {row["id"]} ({row["department"]}) '
                     f'matched on the opening pages ({how}).')
            record = dict(
                institution=code, institution_name=name, id=identifier, title=row['title'], authors=[row['dissertator']],
                advisors=advisors, year=int(row['year']), candidate_years=[int(row['year'])],
                degree=['Doctor of Philosophy'], degree_classification='doctoral', programme='History',
                department_discipline=[row['department'].split(', ')[-1]], eligibility='history_phd',
                eligibility_basis=basis, history_scope='explicit_history_program_or_department', aha_id=row['id'],
                aha_record=row, country='CA' if code in CANADA else 'US', item_url=item_url,
                pdf_urls=[link['pdf_url']] if link.get('pdf_url') else [], access_category='user_supplied_pdf',
                source_harvest=str(args.out.relative_to(ROOT)), source_pdf=file['path'], source=SOURCE,
                checked_at=stamp, provenance_note='Original file left in place; repository checksum not independently verified.')
            result = dict(institution=code, id=identifier, title=row['title'], item_url=item_url,
                          country=record['country'], status='downloaded', checked_at=stamp, source=SOURCE,
                          files=[file], chain=[])
            with (args.out/'records.jsonl').open('a') as handle:
                handle.write(json.dumps(record, ensure_ascii=False)+'\n')
            with (args.out/'downloads.jsonl').open('a') as handle:
                handle.write(json.dumps(result, ensure_ascii=False)+'\n')
    print(f'registered {registered}, held {held}' + (' (dry run: nothing written)' if args.dry_run else ''), flush=True)


if __name__ == '__main__':
    main()
