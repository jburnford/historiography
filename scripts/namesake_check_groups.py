"""Corpus ids anchored to an LC author whose given names differ from the cited name -> groups for Sol (2026-11-04).

key_cited_book_authors.py (2026-11-03 runs) anchored a dissertation corpus id (`diss-person:silva|maria`) to the
key of the LC author of one much-cited book cited under that id. The names had to be compatible (family name, first
given name), so a pooled id ('silva|maria' covers every Maria ... da Silva the bibliographies cite) could go to one
Maria: the canon map then shows Maria Aparecida de Aquino Silva's 335 citing theses under Maria Beatriz Nizza da
Silva's key. Here every anchor those runs made is checked word by word: each given name of the shorter form must
appear in the longer one (an initial matches its name; particles and LC dates are ignored). An anchor that fails
goes to Sol with the id's most-cited works, so the works decide (identity by works): spelling variants
(Raphael / Rafael Bluteau) stay, namesakes and pooled ids are detached by apply_namesake_verdicts.py.

    python3 scripts/namesake_check_groups.py --out data/identifiers/namesake-check-2026-11-04
    python3 scripts/namesake_check_groups.py --out data/identifiers/namesake-check-2026-11-04/r2 --judged data/identifiers/namesake-check-2026-11-04
    python3 scripts/namesake_check_groups.py --out data/identifiers/namesake-check-2026-11-04/r3 --persons mello|maria johnson|samuel \\
        jones|owen phillips|paul turnbull|david torres|joao c --judged data/identifiers/namesake-check-2026-11-04 data/identifiers/namesake-check-2026-11-04/r2
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

import duckdb

from identifiers import ROOT

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
RUNS = ['cited-book-authors-2026-11-03', 'cited-book-authors-2026-11-03b']
LETTERS = str.maketrans({'ł': 'l', 'Ł': 'L', 'ø': 'o', 'Ø': 'O', 'đ': 'd', 'Đ': 'D', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe'})
PARTICLES = {'de', 'da', 'do', 'dos', 'das', 'e', 'van', 'von', 'der', 'den', 'la', 'le', 'du', 'di', 'del', 'y', 'jr',
             'sr', 'ii', 'iii', 'dr', 'orgs', 'org', 'ed', 'eds'}


def given_words(label):
    family, comma, given = label.partition(',')
    if not comma:
        given = ' '.join(label.split()[:-1])
    given = unicodedata.normalize('NFKD', given.translate(LETTERS)).encode('ascii', 'ignore').decode().lower()
    given = re.sub(r'\b(1[0-9]{3}|20[0-9]{2}|approximately|active|born|died)\b.*', '', given)
    words = [t for t in re.split(r'[^a-z]+', given) if t]
    # 'e' joins names in Portuguese ('Oliveira e Costa') but is an initial in first place ('Gombrich, E. H.')
    return [t for n, t in enumerate(words) if t not in PARTICLES or (n == 0 and len(t) == 1)]


def given_names_agree(a, b):
    """Every given name of the shorter form is in the longer one; an initial matches a name it begins, and a
    short form its full form ('A. H. de Oliveira' / 'António Henrique R. de Oliveira', 'Pat' / 'Patricia';
    'Maria Aparecida' / 'Maria Beatriz' do not)."""
    wa, wb = given_words(a), given_words(b)
    if not wa or not wb:
        return True
    short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)

    def same(s, t):
        lo, hi = sorted((s, t), key=len)
        return s == t or (len(lo) == 1 or len(lo) >= 3) and hi.startswith(lo)
    return all(any(same(s, t) for t in long_) for s in short)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--size', type=int, default=10)
    ap.add_argument('--works', type=int, default=15)
    ap.add_argument('--persons', nargs='*', default=[], help="corpus ids to check whatever their names (two runs named different LC people)")
    ap.add_argument('--judged', type=Path, nargs='*', default=[], help='round dirs whose g*/verdicts.json already answer an id')
    args = ap.parse_args()
    names = {r['person_key']: r for r in csv.DictReader(open(CORPUS / 'cited-people.csv'))}
    db = duckdb.connect()
    keyed = {a.split(':', 1)[1]: (k, label, list(anchors)) for k, label, anchors, a in db.execute(
        "SELECT key, label, anchors, a FROM (SELECT key, label, anchors, unnest(anchors) a FROM 'build/graph/person.parquet') "
        "WHERE a LIKE 'diss-person:%'").fetchall()}
    anchored = {}                                      # corpus id -> (LC heading the run matched, its books)
    for run in RUNS:
        d = ROOT / 'data/identifiers' / run
        cands = {c['person']: c for c in json.loads((d / 'candidates.json').read_text())}
        for op in json.loads((d / 'proposal.json').read_text())['ops']:
            for a in op.get('anchors', []):
                if a.startswith('diss-person:'):
                    p = a.split(':', 1)[1]
                    c = cands.get(p, {})
                    anchored.setdefault(p, (c.get('label') or op.get('label') or '', c.get('lc'), c.get('works', [])))
    items = []
    for p, (lc_label, lc, books) in sorted(anchored.items()):
        # the run's LC heading, and the label of the key holding the id now (a later run's candidate can name
        # another LC person: reis|jose went to José de Oliveira Reis, then the second run found José Carlos Reis)
        name = names.get(p, {}).get('name', p)
        now = keyed.get(p, (None, '', []))[1] or ''
        if p in args.persons or any(h and not given_names_agree(name, h) for h in (lc_label, now)):
            items.append(dict(person=p, lc=lc, lc_label=lc_label or now, matched_books=books))
    db.execute('CREATE TABLE p(p VARCHAR)')
    db.executemany('INSERT INTO p VALUES (?)', [(i['person'],) for i in items])
    works = {}
    for p, w, title, year, kind, authors, n in db.execute(f"""
            SELECT a.person_key, w.work_id, w.title, w.year, w.kind, w.authors, try_cast(w.cited_by_dissertations AS INT) n
            FROM read_csv('{CORPUS}/authored.csv.gz') a JOIN read_csv('{CORPUS}/works.csv', all_varchar=true) w USING (work_id)
            WHERE a.person_key IN (SELECT p FROM p) ORDER BY n DESC""").fetchall():
        works.setdefault(p, []).append(dict(work=w, title=title, year=year, kind=kind, cited_authors=authors, theses=n))
    out = []
    for i in items:
        r = names.get(i['person'], {})
        k = keyed.get(i['person'])
        ws = works.get(i['person'], [])
        out.append(dict(i, cited_name=r.get('name'), cited_by_theses=int(r.get('cited_by_dissertations') or 0),
                        key=k[0] if k else None, key_label=k[1] if k else None,
                        key_anchors=[a for a in (k[2] if k else []) if not a.startswith('diss-person:')][:12],
                        works_count=len(ws), works=ws[:args.works]))
    judged = {v['person'] for d in args.judged for f in d.glob('g*/verdicts.json') for v in json.loads(f.read_text())}
    out = [i for i in out if i['person'] not in judged or i['person'] in args.persons]
    out.sort(key=lambda i: -i['cited_by_theses'])
    groups = [dict(id=f'g{n // args.size + 1:03d}', items=out[n:n + args.size]) for n in range(0, len(out), args.size)]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(anchored=len(anchored), conflicts=len(out), keyed=sum(1 for i in out if i['key']), groups=len(groups))))


if __name__ == '__main__':
    main()
