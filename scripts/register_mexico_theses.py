#!/usr/bin/env python3
"""Register the downloaded Mexican History doctorates after a title-page check (2026-11-04).

Reads candidates.jsonl and downloads.jsonl (scripts/mexico_download.py) and the PDFs on E:. No network.
User, 2026-11-04: "stick with history for now" -- History doctorates only, no neighbouring programmes
(Estudios Latinoamericanos, Estudios Mesoamericanos, Historia del Arte, Estudios del Desarrollo...).

A thesis is registered when every part is a whole PDF (pdfinfo reads it, 50+ pages in all) and its
title page (first four pages, text layer, or Tesseract OCR when there is none):
- names a doctorate in History ("Doctor/Doctora/Doctorado en Historia ...", not Historia del Arte); or
- names no degree legibly (often a garbled scan) while the repository record itself names the History
  doctorate: UNAM ("Título otorgado: Doctorado en Historia"), Ibero ("Doctorado en Historia" in the
  description), Colegio de San Luis (its Doctorado en Historia collection), El Colegio de México
  (academic_degree). Instituto Mora and Colegio de Michoacán records do not name the programme, so
  there the title page must.
A title page that names another doctorate (Estudios del Desarrollo, Ciencias Sociales, Historia del
Arte...) is held, whatever the record says. Held theses go to held.jsonl with the reason.

    python3 scripts/register_mexico_theses.py        # -> records.jsonl, held.jsonl, register-report.json

Names: repository forms vary ('JORGE OLVERA AGUILAR', 'Mena Macedo, Margarita; 690274'); all become
'Surnames, Given names', the last two words being the two Mexican surnames unless the record inverts
the name itself. Year: the earliest year in the record (Ibero records also carry the deposit year).
Title-page years were tried and dropped: Ibero title pages all carry the university's 1981 decree of
official recognition, and UNAM title pages quote dates from the thesis subject.
"""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/field-research/mexico-theses-2026-11-04'
INSTITUTIONS = {
    'unam': 'Universidad Nacional Autónoma de México',
    'colmex': 'El Colegio de México',
    'mora': 'Instituto de Investigaciones Dr. José María Luis Mora',
    'colmich': 'El Colegio de Michoacán',
    'colsan': 'El Colegio de San Luis',
    'ibero': 'Universidad Iberoamericana',
}
# sources whose record names the History doctorate itself (see mexico_download.screen)
RECORD_NAMES_DEGREE = {'unam', 'ibero', 'colsan', 'colmex'}
DEGREE = re.compile(r'(?:DOCTOR[AE]?|Doctor[ae]?|Doctorado|DOCTORADO)(?:\s+(?:TUTORIAL|Tutorial))?\s+(?:EN|en)\s+'
                    r'([A-Za-zÁÉÍÓÚÜáéíóúüñÑ ,.]{3,70})')
OTHER = re.compile(r'desarrollo|ciencias\s+soci|sociales|antropolog|\barte\b|latinoamerican|mesoamerican|literatura|'
                   r'filosof|econom|educaci|sociolog|pol[ií]tic|geograf|letras|ling[uü][ií]st|estudios\s+regionales',
                   re.I)
PARTICLES = {'de', 'del', 'la', 'las', 'los', 'y', 'i', 'da', 'van', 'von'}


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).casefold()


def title_page_text(path):
    """First four pages; OCR (Spanish needs only the Latin alphabet, eng model) when there is no text layer."""
    try:
        text = subprocess.run(['pdftotext', '-l', '4', str(path), '-'], capture_output=True, timeout=120).stdout.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        text = ''
    if len(re.sub(r'\s+', '', text)) >= 150 and degree_reading(text)[0] != 'none':
        return text, 'text'
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdftoppm', '-r', '200', '-l', '3', '-gray', str(path), f'{tmp}/p'], capture_output=True, timeout=300)
        out = []
        for img in sorted(Path(tmp).glob('p*.pgm')):
            out.append(subprocess.run(['tesseract', str(img), '-', '-l', 'eng'], capture_output=True, timeout=300)
                       .stdout.decode('utf-8', 'replace'))
    ocr = '\n'.join(out)
    # a text layer that names no degree (often a garbled scan layer): use the OCR reading if it names one
    if len(re.sub(r'\s+', '', text)) >= 150 and degree_reading(ocr)[0] == 'none':
        return text, 'text'
    return ocr, 'ocr'


def pages(path):
    try:
        info = subprocess.run(['pdfinfo', str(path)], capture_output=True, timeout=120).stdout.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired:
        return None
    m = re.search(r'^Pages:\s+(\d+)', info, re.M)
    return int(m.group(1)) if m else None


def degree_reading(text):
    """('history' | 'other' | 'none', the phrases read)."""
    flat = re.sub(r'\s+', ' ', text)
    phrases = [p.strip(' ,.') for p in DEGREE.findall(flat)]
    hist = [p for p in phrases if re.match(r'histori', fold(p)) and not re.search(r'\barte\b', fold(p))]
    if hist:
        return 'history', phrases
    if any(OTHER.search(p) for p in phrases):
        return 'other', phrases
    return 'none', phrases


def mx_name(raw):
    """'JORGE OLVERA AGUILAR' -> 'Olvera Aguilar, Jorge'; 'Mena Macedo, Margarita; 690274' -> 'Mena Macedo, Margarita'."""
    name = re.sub(r'\s*\((?:asesor|director|tutor)[^)]*\)', '', raw or '', flags=re.I)
    name = re.sub(r';\s*\d+\s*$', '', name).strip(' ;,')
    name = re.sub(r'\s+', ' ', name)
    if not name:
        return ''
    if name.isupper() or (',' in name and name.split(',')[0].isupper()):
        name = ' '.join(w.lower() if w.lower() in PARTICLES else w.capitalize() for w in name.split())
    if ',' in name:
        return name
    words = name.split()
    if len(words) < 2:
        return name
    # surnames: the last two words with their particles ('Gómez de Lara'), or the last when only two words
    i = len(words) - 1
    count = 1 if len(words) == 2 else 2
    taken = 0
    while i > 0 and taken < count:
        taken += 1
        i -= 1
        while i > 0 and words[i].lower() in PARTICLES:
            i -= 1
    surnames, given = words[i + 1:], words[:i + 1]
    if not given:
        return name
    surnames = [w.lower() if w.lower() in PARTICLES and n else w for n, w in enumerate(surnames)]
    return f"{' '.join(surnames)}, {' '.join(given)}"


def people(source, c):
    """(advisors, committee) from the record."""
    raw = c.get('advisors') or []
    if source == 'ibero':  # director carries a CVU number; the others listed are readers ('lectores')
        clean = [r for r in raw if not re.match(r'director:', r, re.I)]
        directors = [mx_name(r) for r in clean if re.search(r';\s*\d+', r)]
        readers = [mx_name(r) for r in clean if not re.search(r';\s*\d+', r)]
        return directors, [dict(name=n, category='lector') for n in readers]
    return [mx_name(r) for r in raw if mx_name(r)], []


def record_year(c):
    r = c['record']
    years = [int(y) for v in (r.get('date') or r.get('date_created') or []) for y in re.findall(r'(?:19|20)\d\d', str(v))]
    return str(min(years)) if years else (c.get('year') or None)


def check(job):
    c, row = job
    files = row.get('files') or []
    out = dict(id=c['id'], source=c['source'])
    if row.get('status') != 'ok' or not files:
        return dict(out, held=f"download {row.get('status')}")
    total, parts = 0, []
    for f in files:
        p = Path(f['path'])
        if not p.exists():
            return dict(out, held=f'missing file {p}')
        n = pages(p)
        with open(p, 'rb') as fh:
            head = fh.read(5)
        if n is None or head != b'%PDF-':
            return dict(out, held=f'unreadable PDF {p.name}')
        total += n
        parts.append(dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), pages=n))
    if total < 50:
        return dict(out, held=f'only {total} pages')
    text, how = title_page_text(Path(files[0]['path']))
    reading, phrases = degree_reading(text)
    out.update(parts=parts, pages=total, title_page=how, degree_phrases=phrases[:4], reading=reading,
               year=record_year(c))
    if reading == 'history':
        out['basis'] = 'title page names the History doctorate'
    elif reading == 'other':
        out['held'] = f"title page names another doctorate: {'; '.join(phrases[:3])}"
    elif c['source'] in RECORD_NAMES_DEGREE:
        out['basis'] = 'repository record names the History doctorate; title page names no degree legibly'
    else:
        out['held'] = 'title page names no degree legibly and the record does not name the programme'
    return out


def main():
    cands = {c['id']: c for c in map(json.loads, open(D / 'candidates.jsonl', encoding='utf-8'))}
    rows = {}
    for r in map(json.loads, open(D / 'downloads.jsonl', encoding='utf-8')):
        if r['id'] not in rows or r.get('status') == 'ok':
            rows[r['id']] = r
    jobs = [(cands[i], r) for i, r in rows.items() if i in cands]
    with ProcessPoolExecutor(6) as pool:
        results = list(pool.map(check, jobs, chunksize=4))
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    records, held = [], []
    for res in results:
        c = cands[res['id']]
        if res.get('held'):
            held.append(dict(id=res['id'], source=res['source'], title=c['title'], author=c['author'], item_url=c['item_url'],
                             reason=res['held'], degree_phrases=res.get('degree_phrases', [])))
            continue
        advisors, committee = people(c['source'], c)
        lang = [fold(l) for l in c['record'].get('language') or []]
        records.append(dict(
            institution=f"mx:{c['source']}", id=c['id'], title=c['title'].strip(), authors=[mx_name(c['author'])],
            advisors=advisors, committee=committee, year=res['year'],
            language=['es'] if not lang or any(l.startswith(('spa', 'espa', 'es')) for l in lang) else lang,
            item_url=c['item_url'], awarding_institution=INSTITUTIONS[c['source']],
            eligibility_basis=f"{res['basis']} ({'; '.join(res['degree_phrases'][:2]) or 'no degree phrase read'})",
            title_page=res['title_page'], files=res['parts'], pages=res['pages'], checked_at=now))
    records.sort(key=lambda r: (r['institution'], r['id']))
    with open(D / 'records.jsonl', 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with open(D / 'held.jsonl', 'w', encoding='utf-8') as f:
        for h in sorted(held, key=lambda h: h['id']):
            f.write(json.dumps(h, ensure_ascii=False) + '\n')
    from collections import Counter
    report = dict(checked_at=now, registered=dict(Counter(r['institution'] for r in records)),
                  held={f'{s}: {r}': n for (s, r), n in Counter((h['source'], h['reason'].split(':')[0]) for h in held).items()},
                  basis=dict(Counter(r['eligibility_basis'].split(' (')[0] for r in records)),
                  title_page=dict(Counter(r['title_page'] for r in records)),
                  no_year=sum(1 for r in records if not r['year']))
    (D / 'register-report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
