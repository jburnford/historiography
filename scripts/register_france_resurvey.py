#!/usr/bin/env python3
"""Register the French History theses downloaded from the 2026-11-15 access re-survey (user wget run of
open-urls.tsv and ai-excluded-urls.tsv into /mnt/e/historiography-dissertation-pdfs/france-wget-2026-11-16).

Offline: no network requests, no writes, moves or deletions on E:. Each file is tied to its thesis by the NNT
in its name (fr-<NNT>-<Author>.pdf) and to the ABES record in the corrected History screen of the 2026-11-12
snapshot (/mnt/e/france-theses-snapshot-2026-11-12/screen/history-screen.jsonl.gz, same record shape as the
2026-10-30 candidates.json). The output folder then holds candidates.json + downloads.jsonl in the shape the
``france_thesesfr`` ingest adapter reads, so the ingest needs only a second registry entry.

A file is registered when:
- the whole file validates: PDF header and %%EOF, at least MIN_PAGES pages, pdfinfo and pdftotext read it;
- its NNT is in the History screen, with an ABES record;
- the History scope holds (scope() below). Ancient history counts unless it is archaeology, philology/text
  edition or history of religions (ruling 2026-11-17; ancient_ruling.verdict); economics doctorates whose only
  history signal is a RAMEAU subject ('economic-subject') count when the title reads as economic history. Held:
  art/architecture/film/music/literature history, the EPHE religious-studies doctorate ('Histoire des religions
  et anthropologie religieuse'), ecology disciplines. Kept: History in its period/area forms, history of science and techniques, history of education
  and economic history disciplines (user rulings 2026-11-15/16), history of religions inside History doctorates.

Everything else goes to held.jsonl with its reason. The opening pages are also checked for doctorate wording
(thèse, doctorat, docteur); a miss is recorded on the row ('doctorate_words_on_opening_pages': false) and not
held, since the national record is the evidence that the thesis is a defended doctorate.

usage: python3 scripts/register_france_resurvey.py [--dry-run]
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ancient_ruling import HELD_REASON, verdict  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SURVEY = ROOT / 'data/field-research/france-theses-resurvey-2026-11-15'
OUT = SURVEY / 'register-2026-11-17'
PDFS = Path('/mnt/e/historiography-dissertation-pdfs/france-wget-2026-11-16')
SCREEN = Path('/mnt/e/france-theses-snapshot-2026-11-12/screen/history-screen.jsonl.gz')
MIN_PAGES = 60

ANCIENT_DISCIPLINE = re.compile(r"histoire ancienne|antiquite|histoire grecque|histoire romaine|epigraphie|mondes anciens"
                                r"|civilisations? antiques|egyptolog|assyriolog", re.I)
ANCIENT_TITLE = re.compile(r"\bav\.? ?j\.?-?c\b|avant (notre ere|j\.?-?c)|\bantiquite\b|\bantiques?\b|empire romain|republique romaine"
                           r"|epoque (romaine|hellenistique|archaique)|gaule romaine|romanisation|rome antique|grece (ancienne|antique)"
                           r"|monde grec|cites grecques|sanctuaires? grecs?|hellenisti|\bpharaon|egypte ancienne|mesopotam|assyri|babylon"
                           r"|\bgaule\b|gallo-romain|\bepigraph|\bpapyr|\bnecropole|\bage du (bronze|fer)\b|\bneolithi|\bprotohistor", re.I)
LATE_ANTIQUE_OK = re.compile(r"\bmoyen.?age\b|\bmedieva|carolingien|merovingien|a nos jours|reception de l'antiquite", re.I)
ART_DISCIPLINE = re.compile(r"architecture|paysage|histoire de l'art|arts? plastiques|cinema|musicolog|litterature", re.I)
ART_TITLE = re.compile(r"\bpeint|\bsculpt|\barchitect|\bcinema|\bfilms?\b|\bmusique|\bmusical|\bopera\b|\blitteratur|\broman(s|cier)\b"
                       r"|\bpoesie|\bpoete|\btheatre|\biconograph|\bart(s|iste|istes)?\b|\bvitra|\bmosaique|\borfevr|\bmanuscrits? enlumin",
                       re.I)
INDIGENOUS = re.compile(r"autochtone|amerindien|peuples? indigenes|indigenes (du|d'amerique)|aborigen|premieres nations|first nations|\binuit|metis\b|kanak|maori"
                        r"|amazonie|mapuche|guarani|\bsami\b|lapon|native american|nations? indiennes?|indiens? (d'amerique|du canada|des plaines)|iroquois"
                        r"|wendat|huron|\binnus?\b|\bcree\b|ojibw|mi'?kmaq|aztec|maya\b|andin|quechua|aymara|kalinago|caraibes? (indiens|amerind)",
                        re.I)


def fold(text):
    text = unicodedata.normalize('NFKD', (text or '').replace('’', "'"))
    return re.sub(r'\s+', ' ', ''.join(c for c in text if not unicodedata.combining(c))).strip()


ECON_HISTORY_TITLE = re.compile(r"histoire|historique|cliometr|\bsiecles?\b|ancien regime|old regime|entre-deux|colonis|"
                                r"\b1[5-9]\d\d\b|\b[xvi]+e siecle|long terme|grande depression|revolution|capitalisme", re.I)
ARCHAEOLOGY_DISCIPLINE = re.compile(r"archeolog|prehistoire|protohistoire", re.I)


def scope(rec, survey_row):
    """(include, reason). Rulings applied: ancient history is History unless archaeology (user 2026-11-17), with
    philology/text edition held (coordinator's reading) and history of religions/theology held (not ruled), all by
    ancient_ruling.verdict(); economics doctorates count only when their title reads as economic history (user
    2026-11-17: 'we're looking for economic history and not economics')."""
    screen = survey_row.get('screen') or rec.get('screen')
    disc = fold(rec.get('discipline'))
    title = fold((rec.get('titres') or {}).get('fr') or next(iter((rec.get('titres') or {}).values()), ''))
    ldisc = disc.lower()
    if screen == 'economic-subject':
        if ECON_HISTORY_TITLE.search(title):
            return True, f'economics doctorate ({rec.get("discipline")}) whose title reads as economic history (ruling 2026-11-17)'
        return False, f'economics doctorate ({rec.get("discipline")}), title not economic history: economics is out (ruling 2026-11-17)'
    if 'anthropologie religieuse' in ldisc:
        return False, f'religious-studies doctorate ({rec.get("discipline")}): with church history/theology, user has not ruled'
    if 'ecolog' in ldisc:
        return False, f'ecology discipline ({rec.get("discipline")}): adjacent, not History'
    if re.search(r"option ?: ?architecture", ldisc):
        return False, f'architecture option ({rec.get("discipline")}): art/architecture history is out'
    ancient = (screen == 'ancient' or (ANCIENT_DISCIPLINE.search(ldisc) and 'medievaux' not in ldisc)
               or (ANCIENT_TITLE.search(title) and not LATE_ANTIQUE_OK.search(title)))
    if ancient:
        if ARCHAEOLOGY_DISCIPLINE.search(ldisc) and 'histoire' not in ldisc:
            return False, f'{HELD_REASON["archaeology"]} (discipline: {rec.get("discipline")})'
        v = verdict(title)
        if v != 'history':
            return False, f'{HELD_REASON[v]} (discipline: {rec.get("discipline")})'
        return True, f'ancient history, released by the ruling of 2026-11-17 (screen {screen}; discipline: {rec.get("discipline")})'
    if ART_DISCIPLINE.search(ldisc) or ("de l'art" in ldisc):
        if ART_TITLE.search(title):
            return False, f'art/film/music/literature topic in a mixed discipline ({rec.get("discipline")}): out'
    elif ART_TITLE.search(title) and screen == 'history':
        # a History doctorate on an art topic: History by department, flagged
        return True, f'History discipline ({rec.get("discipline")}); title names an art/literature topic (flagged)'
    return True, f'History screen {screen}: {rec.get("discipline")}'


def validate(path):
    size = path.stat().st_size
    with path.open('rb') as handle:
        if not handle.read(1024).lstrip().startswith(b'%PDF'):
            raise ValueError('not a PDF (no PDF header; HTML or other page saved as .pdf)')
        handle.seek(max(0, size - 65536))
        if b'%%EOF' not in handle.read():
            raise ValueError('incomplete PDF (no %%EOF)')
    info = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, timeout=120)
    if info.returncode:
        raise ValueError('pdfinfo cannot read the file')
    m = re.search(r'(?m)^Pages:\s*(\d+)', info.stdout)
    pages = int(m.group(1)) if m else 0
    if pages < MIN_PAGES:
        raise ValueError(f'only {pages} pages: not the full thesis (fragment, notice or volume extract)')
    opening = subprocess.run(['pdftotext', '-f', '1', '-l', '6', str(path), '-'], capture_output=True, text=True, timeout=120)
    if opening.returncode:
        raise ValueError('pdftotext cannot read the opening pages')
    flat = fold(opening.stdout).lower()
    doctorate = bool(re.search(r'\bthese\b|doctorat|docteur|\bdoctoral|\bph\.? ?d\b|doctor of philosophy|dottorato', flat))
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return dict(bytes=size, pages=pages, sha256=digest.hexdigest(), doctorate_words=doctorate,
                text_layer=len(flat) > 200)


def check(path):
    try:
        return path, validate(path), None
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return path, None, str(exc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    survey = {r['nnt']: r for r in csv.DictReader(open(SURVEY / 'records.csv', encoding='utf-8'))}
    urls = {}
    for name in ('open-urls.tsv', 'ai-excluded-urls.tsv'):
        for line in open(SURVEY / name, encoding='utf-8'):
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2:
                urls[parts[1]] = parts[0]
    files = sorted(p for p in PDFS.glob('fr-*.pdf'))
    wanted = {p.name.split('-')[1] for p in files}
    records = {}
    with gzip.open(SCREEN, 'rt', encoding='utf-8') as fh:
        for line in fh:
            r = json.loads(line)
            if r['nnt'] in wanted:
                records[r['nnt']] = r
    stamp = datetime.now(timezone.utc).isoformat()
    cands, downloads, held = [], [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for path, info, error in pool.map(check, files):
            nnt = path.name.split('-')[1]
            rec, srow = records.get(nnt), survey.get(nnt) or {}
            title = ((rec or {}).get('titres') or {}).get('fr') or srow.get('title') or ''
            base = dict(at=stamp, file=path.name, nnt=nnt, title=title, discipline=(rec or srow).get('discipline'),
                        year=(rec or {}).get('date_soutenance', '')[:4] or srow.get('year'))
            if error:
                held.append(dict(base, reason=error))
                continue
            if not rec:
                held.append(dict(base, reason='NNT not in the corrected History screen of the 2026-11-12 snapshot'))
                continue
            ok, why = scope(rec, srow)
            if not ok:
                held.append(dict(base, reason=why, pages=info['pages']))
                continue
            flags = []
            if INDIGENOUS.search(fold(title)):
                flags.append('indigenous_related_title')
            if 'flagged' in why:
                flags.append('art_topic_in_history_discipline')
            if not info['doctorate_words']:
                flags.append('no_doctorate_words_on_opening_pages')
            if not info['text_layer']:
                flags.append('no_text_layer_on_opening_pages')
            cands.append(dict(rec, register_basis=why, register_flags=flags))
            downloads.append(dict(nnt=nnt, checked_at=stamp, status='downloaded', url=urls.get(path.name),
                                  path=str(path), bytes=info['bytes'], sha256=info['sha256'], pages=info['pages'],
                                  doctorate_words_on_opening_pages=info['doctorate_words'], flags=flags,
                                  source='user wget run of the 2026-11-15 re-survey lists (2026-11-16)'))
    reasons = {}
    for h in held:
        key = re.sub(r'\(.*?\)|\d+', '#', h['reason'])
        reasons[key] = reasons.get(key, 0) + 1
    summary = dict(at=stamp, files=len(files), registered=len(cands), held=len(held), held_by_reason=reasons,
                   flags={f: sum(f in c['register_flags'] for c in cands)
                          for f in sorted({f for c in cands for f in c['register_flags']})})
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    if args.dry_run:
        for h in held:
            print('held', h['file'], '-', h['reason'], '-', h['title'][:80])
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'candidates.json').write_text(json.dumps(cands, ensure_ascii=False, indent=1) + '\n')
    (OUT / 'downloads.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in downloads))
    (OUT / 'held.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in held))
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
