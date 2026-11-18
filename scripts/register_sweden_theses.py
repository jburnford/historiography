#!/usr/bin/env python3
"""Register the Swedish History doctoral theses downloaded by scripts/sweden_theses_fetch.py (2026-11-16).

Offline: no network requests, no writes, moves or deletions on E:. Metadata come from the SwePub pilot
(data/field-research/diva-sweden-pilot-2026-11-14: theses.csv.gz, one row per thesis; people.csv.gz, one row
per person credit). Files sit in /mnt/e/diva-history-theses-2026-11-14/pdfs/<host group>/<record>.pdf, named
by sweden_theses_fetch.py from the SwePub record id, which ties each file to its row.

A file is registered when:
- the whole file validates: PDF header and %%EOF, at least MIN_PAGES pages (a DiVA FULLTEXT can be a
  'spikblad' or abstract only), pdfinfo and pdftotext read it;
- its row passes scope() below. History: the pilot's screen 'history' or 'economic_history' (economic history,
  history of science and ideas, history of technology and history of education count, user rulings 2026-11-15/16).
  Ancient history counts unless it is archaeology, philology or history of religions (ruling 2026-11-17,
  ancient_ruling.verdict). Held until the user rules: church history and theology. Out: archaeology, art, film,
  literature, music and fashion; and rows whose local doctoral subject (DiVA forskarutbildningsämne) is
  another discipline with no History-family subject (screen 'medium' or a History code on a non-History
  subject), except education subjects (history of education counts). Rows with no subject and no code
  ('low', title screen only) are kept unless the title names an art, music, church-building or ancient topic.

Each registered record carries the thesis's people as they appear in SwePub: ``advisors`` (supervisors, then
assistant supervisors; ``assistant_supervisors`` lists the latter) and, as its own field, ``opponents``: the
fakultetsopponent, the outside examiner who opposes the thesis at the public defence. The opponent is not a
supervisor and not a committee member, and is kept apart so it can become its own edge later. Names only plus
printed affiliation and ORCID where SwePub gives them; no person key is minted (authors and people are seeds).

Writes records.jsonl, held.jsonl and summary.json in data/field-research/diva-sweden-pilot-2026-11-14/
register-2026-11-17/ (``--dry-run``: prints only). The ingest reads records.jsonl through the
``sweden_swepub`` adapter.
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ancient_ruling import HELD_REASON, verdict  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'data/field-research/diva-sweden-pilot-2026-11-14'
OUT = PILOT / 'register-2026-11-17'
PDFS = Path('/mnt/e/diva-history-theses-2026-11-14/pdfs')
MIN_PAGES = 30  # spikblad/abstract files are 1-12 pages; compilation-thesis summaries (kappa) of 30-59 pages are kept, flagged
KAPPA_PAGES = 60
LANG = {'swe': 'sv', 'eng': 'en', 'ger': 'de', 'deu': 'de', 'nor': 'no', 'spa': 'es', 'fre': 'fr', 'dan': 'da',
        'ita': 'it', 'rus': 'ru'}

HIST_SUBJECT = re.compile(r'histor|östersjö|baltic and east european', re.I)
EDUCATION_SUBJECT = re.compile(r'utbildning|education|pedagog|didakti', re.I)
CHURCH_SUBJECT = re.compile(r'kyrkohistoria|church history|teologi|theolog|religion', re.I)
ART_SUBJECT = re.compile(r'film|cinema|konstvetenskap|konsthist|art history|art science|fine art|litteratur|literature|musik|music|fashion'
                         r'|modevetenskap|arkeolog|archaeolog|antik|classic|indolog|sanskrit|sanscrit', re.I)
ANCIENT_TITLE = re.compile(r'\bantik(en|ens|a)?\b|antiquity|\bancient\b|romersk|romarna|grekisk|hellenist|bronsålder|'
                           r'järnålder|stenålder|bronze age|iron age|neolithic|pharao|\bathen|\bsumer|assyri|babylon', re.I)
ROMAN_EN = re.compile(r'\bRoman\b')
MEDIEVAL = re.compile(r'medieval|middle ages|medeltid|papacy|påve|byzan', re.I)
ART_TITLE = re.compile(r'\bkonst\b|konstnär|konsthist|målning|måleri|arkitektur|architect|\bmusik|\bmusic|\bfilm|litteratur|'
                       r'literature|\bkyrkor\b|altar|\bart\b|painting|opera', re.I)
INDIGENOUS = re.compile(r'\bsam(er|erna|isk\w*|i|ernas)\b|sápmi|sapmi|\blapp|urfolk|ursprungsfolk|indigenous|aborigin|native '
                        r'american|first nations|\binuit|maori|tornedal|kven|meänkiel', re.I)


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold()


def file_name(record_id):
    return re.sub(r'[^A-Za-z0-9]+', '-', record_id.split(':', 1)[-1]).strip('-') + '.pdf'


def subjects(row):
    return [s.split(':', 1)[-1].strip() for s in (row.get('local_subjects') or '').split(' | ') if s.strip()]


def scope(row):
    """(include, reason)."""
    subs = subjects(row)
    joined = ' | '.join(subs)
    title = ' '.join(x for x in (row['title'], row.get('subtitle')) if x)
    codes = set((row.get('ssif5') or '').split())
    if row['screen'] not in ('history', 'economic_history'):
        return False, f"pilot screen {row['screen']}: not History"
    if CHURCH_SUBJECT.search(joined):
        return False, f'church history / theology / religion subject ({joined}): user has not ruled'
    ancient = '60105' in codes or ((ANCIENT_TITLE.search(title) or (row.get('language') == 'eng' and ROMAN_EN.search(title)))
                                   and not MEDIEVAL.search(title))
    if ancient:  # ruling 2026-11-17: ancient history is History unless archaeology (philology, religion held)
        v = verdict(title)
        if v != 'history':
            return False, f'{HELD_REASON[v]} (SSIF {row.get("ssif5") or "none"})'
    if '60103' in codes and not any(HIST_SUBJECT.search(s) for s in subs):
        return False, f'archaeology code 60103 without a History subject ({joined or "no subject"}): out'
    if ART_SUBJECT.search(joined) and not any(HIST_SUBJECT.search(s) and not ART_SUBJECT.search(s) for s in subs):
        return False, f'art / film / literature / music / archaeology subject ({joined}): out'
    if subs and not any(HIST_SUBJECT.search(s) for s in subs):
        if any(EDUCATION_SUBJECT.search(s) for s in subs):
            return True, f'education subject with History code {row.get("ssif5")} ({joined}): history of education counts'
        return False, f'doctorate in another subject ({joined}) with History code {row.get("ssif5") or "none"}: not a History PhD'
    if row['confidence'] == 'low' and ART_TITLE.search(title):
        return False, 'no subject or code; title names an art, music or church-building topic: out'
    label = 'economic history' if row['screen'] == 'economic_history' else 'History'
    return True, f"{label} ({row['confidence']}: {row['confidence_reason']})"


def validate(path):
    size = path.stat().st_size
    with path.open('rb') as handle:
        if not handle.read(1024).lstrip().startswith(b'%PDF'):
            raise ValueError('not a PDF (no PDF header)')
        handle.seek(max(0, size - 65536))
        if b'%%EOF' not in handle.read():
            raise ValueError('incomplete PDF (no %%EOF)')
    info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, timeout=120)
    if info.returncode:
        raise ValueError('pdfinfo cannot read the file')
    m = re.search(r'(?m)^Pages:\s*(\d+)', info.stdout)
    pages = int(m.group(1)) if m else 0
    if pages < MIN_PAGES:
        raise ValueError(f'only {pages} pages: not the full thesis (spikblad, abstract or summary)')
    opening = subprocess.run(['pdftotext', '-f', '1', '-l', '6', str(path), '-'], capture_output=True, text=True, timeout=120)
    if opening.returncode:
        raise ValueError('pdftotext cannot read the opening pages')
    flat = fold(opening.stdout)
    doctorate = bool(re.search(r'avhandling|doktor|doctoral|dissertation|\bph\.? ?d\b|doctor of philosophy|\bdiss\b', flat))
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return dict(bytes=size, pages=pages, sha256=digest.hexdigest(), doctorate_words=doctorate,
                text_layer=len(flat.strip()) > 200)


def check(path):
    try:
        return path, validate(path), None
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return path, None, str(exc)


def person(p):
    name = ', '.join(x for x in (p['family'], p['given']) if x)
    out = dict(name=name)
    for k in ('orcid', 'affiliation', 'birth_year', 'title'):
        if p.get(k):
            out[k] = p[k].strip(' |') if k == 'affiliation' else p[k]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    rows = list(csv.DictReader(gzip.open(PILOT / 'theses.csv.gz', 'rt', encoding='utf-8', newline='')))
    by_name = {}
    for r in rows:
        by_name.setdefault(file_name(r['record_id']), r)
    people = defaultdict(list)
    for p in csv.DictReader(gzip.open(PILOT / 'people.csv.gz', 'rt', encoding='utf-8', newline='')):
        people[p['record_id']].append(p)
    log = {}
    for line in open(PDFS / 'fetch-log.tsv', encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        if len(parts) >= 5 and parts[1] == 'ok':
            log[parts[3]] = dict(at=parts[0], host=parts[2], url=parts[4])
    files = sorted(p for p in PDFS.glob('*/*') if p.is_file() and p.suffix.lower() == '.pdf')
    stamp = datetime.now(timezone.utc).isoformat()
    records, held = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for path, info, error in pool.map(check, files):
            row = by_name.get(path.name)
            title = (row or {}).get('title', '')
            base = dict(at=stamp, file=str(path.relative_to(PDFS)), record_id=(row or {}).get('record_id'), title=title,
                        year=(row or {}).get('year'), university=(row or {}).get('university'),
                        local_subjects=(row or {}).get('local_subjects'), ssif5=(row or {}).get('ssif5'))
            if error:
                held.append(dict(base, reason=error))
                continue
            if not row:
                held.append(dict(base, reason='file name matches no SwePub record'))
                continue
            ok, why = scope(row)
            if not ok:
                held.append(dict(base, reason=why, pages=info['pages']))
                continue
            credits = people.get(row['record_id'], [])
            authors = [person(p)['name'] for p in credits if p['role'] == 'author'] or [row['author']]
            sup = [person(p) for p in credits if p['role'] == 'supervisor']
            asst = [person(p) for p in credits if p['role'] == 'assistant_supervisor']
            opp = [person(p) for p in credits if p['role'] == 'opponent']
            full_title = row['title'] + (f": {row['subtitle']}" if row.get('subtitle') and row['subtitle'] not in row['title'] else '')
            flags = []
            if INDIGENOUS.search(full_title):
                flags.append('indigenous_related_title')
            if not info['doctorate_words']:
                flags.append('no_doctorate_words_on_opening_pages')
            if not info['text_layer']:
                flags.append('no_text_layer_on_opening_pages')
            if info['pages'] < KAPPA_PAGES:
                flags.append('short_file_compilation_summary_only')
            if row['confidence'] == 'low':
                flags.append('low_confidence_screen')
            fetched = log.get(path.name) or {}
            records.append(dict(
                record_id=row['record_id'], duplicate_ids=row['duplicate_ids'].split(), urn=row.get('urn') or None,
                institution='se:' + (row.get('university_code') or 'unknown'), awarding_institution=row.get('university'),
                university_basis=row.get('university_basis'),
                id='swepub-' + re.sub(r'[^A-Za-z0-9]+', '-', row['record_id'].split(':', 1)[-1]).strip('-'),
                title=full_title, authors=authors, author_orcid=row.get('author_orcid') or None,
                advisors=[p['name'] for p in sup + asst], assistant_supervisors=[p['name'] for p in asst],
                supervisors_detail=sup + asst, opponents=opp,
                year=int(row['year']) if row.get('year', '').isdigit() else None, defence_date=row.get('defence_date') or None,
                language=[LANG.get(row.get('language'), row.get('language'))] if row.get('language') else [],
                local_subjects=subjects(row), ssif=(row.get('ssif5') or '').split(), screen=row['screen'],
                screen_confidence=row['confidence'], register_basis=why, register_flags=flags,
                isbn=row.get('isbn') or None, doi=row.get('doi') or None, series=row.get('series') or None,
                publisher=row.get('publisher') or None,
                item_url=row.get('urn') or row.get('fulltext_url') or row.get('resolved_link'),
                eligibility_basis=(f"SwePub doctoral thesis {row['record_id']} ({row.get('university') or 'university not given'}, "
                                   f"{row.get('year') or 'year not given'}); {why}"),
                files=[dict(path=str(path), bytes=info['bytes'], sha256=info['sha256'], pages=info['pages'],
                            url=fetched.get('url'), fetched_at=fetched.get('at'))],
                checked_at=stamp))
    reasons = defaultdict(int)
    for h in held:
        reasons[re.sub(r'\(.*?\)|\d+', '#', h['reason'])] += 1
    summary = dict(at=stamp, files=len(files), registered=len(records), held=len(held), held_by_reason=dict(reasons),
                   registered_by_screen={s: sum(r['screen'] == s for r in records) for s in ('history', 'economic_history')},
                   with_opponents=sum(bool(r['opponents']) for r in records),
                   opponent_credits=sum(len(r['opponents']) for r in records),
                   with_advisors=sum(bool(r['advisors']) for r in records),
                   flags={f: sum(f in r['register_flags'] for r in records)
                          for f in sorted({f for r in records for f in r['register_flags']})},
                   years=dict(sorted(defaultdict(int, {str(y // 10 * 10): sum(1 for r in records if r['year'] and r['year'] // 10 * 10 == y // 10 * 10)
                                                       for y in {r['year'] for r in records if r['year']}}).items())),
                   institutions=dict(sorted({r['institution']: sum(x['institution'] == r['institution'] for x in records)
                                             for r in records}.items(), key=lambda kv: -kv[1])))
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    if args.dry_run:
        for h in held:
            print('held', h['file'], '-', h['reason'], '-', (h['title'] or '')[:80])
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
    (OUT / 'held.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in held))
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
