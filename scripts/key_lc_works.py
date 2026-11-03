"""Books by keyed people -> the key log, from LC's catalogue (2026-11-02). Writes a proposal.

The reviewed-book route reached books through reviews; this works the other way. For every person key holding
an LC authority, the books LC catalogued under that authority (MDSConnect Books All 2016, offline index from
scripts/lc_bib_index.py: records to 2016) become works with the person's role:
- a heading resolves to the key's authority by its $0, or by its text equal to the authority's authorised
  heading (lc_resolve_authorities.resolve), or an earlier authorised form LC keeps as a variant, with the same
  family name and dates (`former_heading`, 2026-11-03: Tina Loo's books are catalogued under 'Loo, Tina Merrill,
  1962-', her heading until 2019); or, for a heading without dates, the one live, differentiated authority in
  the whole file with that name once dates and fuller form are dropped (`unique_bases`: 'Gilroy, Paul.' for
  'Gilroy, Paul, 1956-'); other variant forms and undifferentiated authorities are not used;
- **authored**: the main entry (100), or an added entry (700) with an author relator ('joint author',
  'author'); **edited**: an added entry with an editor or compiler relator. Other relators (translator,
  illustrator, former owner) and added entries without a relator are left out: older records do not say
  whether the person wrote, edited or only wrote a preface.
- **one work per book, editions together**: records whose lead person (the first author, else the first
  editor) and normalised main title (245 $a, leading article and punctuation dropped, first ten words) agree
  are one work. Each record's LCCN is an anchor of the work (`lccn:<lccn>`; the control number of this file
  is the LCCN); the earliest publication year is kept as the member `lc-first-year:<year>`.

Two phases, applied in turn:
1. `--phase works`: mints the works, or attaches new editions to a work already holding one of its LCCNs.
2. `--phase relations`: one claim per person, role and work, anchored on the catalogue assertions
   (`lc-authored:<lccn>:<lcid>` or `lc-edited:...`, one per edition), with endpoints `lcnaf:<lcid>` and the work's earliest LCCN.
   Claims are `recorded`: one catalogue, however many editions.

    python3 scripts/key_lc_works.py --phase works --out data/identifiers/lc-works-2026-11-02
    python3 scripts/identifiers.py apply data/identifiers/lc-works-2026-11-02/works.json.gz
    python3 scripts/key_lc_works.py --phase relations --out data/identifiers/lc-works-2026-11-02
    python3 scripts/identifiers.py apply data/identifiers/lc-works-2026-11-02/relations.json.gz
"""
import argparse
import glob
import gzip
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise
from lc_resolve_authorities import label_dates, load_names, resolve

AUTHOR = {'author', 'joint author', 'aut', 'joint aut', 'co-author', 'coauthor'}
EDITOR = {'ed', 'editor', 'joint ed', 'joint editor', 'editor of compilation', 'comp', 'compiler', 'joint comp',
          'ed. and tr', 'edt'}
ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'}


def title_key(t):
    t = re.sub(r"['’‘ʼ]", '', t or '')                  # Labour's / Labour’s -> labours
    t = re.sub(r'\s*&\s*', ' and ', t)                    # 'Capitalism & slavery' is 'Capitalism and Slavery' (2026-11-03)
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    w = re.sub(r'[^a-z0-9 ]+', ' ', t).split()
    while w and w[0] in ARTICLES:
        w = w[1:]
    return ' '.join(w[:10])


def role_of(tag, relators):
    rel = {r.strip(' .,').lower() for r in relators or ()}
    if tag == '100' or rel & AUTHOR:
        return 'authored'
    if rel & EDITOR:
        return 'edited'
    return None


def former_heading(heading, label):
    """A variant that is an earlier form of the authorised heading: same family name and the same dates, which
    are present ('Loo, Tina Merrill, 1962-' for 'Loo, Tina, 1962-', revised in 2019; the 2016 records keep the
    old form). A variant without dates, or with other dates, is another person's 'see from' form as often as not."""
    d = label_dates(heading)
    return bool(d) and d == label_dates(label) and heading.split(',')[0].strip().lower() == label.split(',')[0].strip().lower()


BASE_SQL = r"""lower(trim(regexp_replace(regexp_replace(label, '\s*\([^)]*\)', '', 'g'),
                 ',\s*(b\.|d\.|born|died|approximately|active|fl\.)?\s*-?\d{3,4}[^,]*$', ''), ' ,.'))"""


def base_name(heading):
    """A heading without dates or fuller form: 'Kuhn, Thomas S. (Thomas Samuel), 1922-1996' -> 'kuhn, thomas s'."""
    h = re.sub(r'\s*\([^)]*\)', '', heading or '')
    h = re.sub(r',\s*(b\.|d\.|born|died|approximately|active|fl\.)?\s*-?\d{3,4}[^,]*$', '', h)
    return h.strip(' ,.').lower()


def unique_bases(names_path, keyed):
    """Base name -> LC id, for keyed authorities whose base name no other live, differentiated personal-name
    authority in the whole file shares (2026-11-03: Gilroy's 1993 record reads 'Gilroy, Paul.', the authority
    'Gilroy, Paul, 1956-'; Kuhn's 'Kuhn, Thomas S.' for 'Kuhn, Thomas S. (Thomas Samuel), 1922-1996')."""
    db = duckdb.connect()
    db.execute("SET memory_limit = '4GB'")
    db.execute('CREATE TABLE k(lcid VARCHAR)')
    db.executemany('INSERT INTO k VALUES (?)', [(x,) for x in keyed])
    rows = db.execute(f"""WITH b AS (SELECT lcid, {BASE_SQL} AS base FROM read_parquet('{names_path}')
                                     WHERE NOT undifferentiated AND NOT deprecated),
                          u AS (SELECT base FROM b GROUP BY base HAVING count(*) = 1)
                          SELECT b.base, b.lcid FROM b JOIN u USING (base) JOIN k USING (lcid)""").fetchall()
    return dict(rows)


EDITING = re.compile(r'\b(edited|editors?|eds?\.|compiled|compilers?|hrsg|herausgegeben|herausgeber|sous la direction|'
                     r'dirig[ée]e?s?|[ée]dit[ée]e?s? par|organizad[oa]s?|organiza[çc][ãa]o|org\.|a cura di|coordinad[oa]s?|'
                     r'coordenad[oa]s?|coordinated|redactie|redigert|toim\.)', re.I)


def editor_by_statement(tag, relators, family, responsibility):
    """An added entry without a relator is an editor when the record's statement of responsibility (245 $c) speaks
    of editing and names the person ('edited by Eric Hobsbawm and Terence Ranger'; 2026-11-03: older records give
    collections no relators, so their editors were left out)."""
    if tag != '700' or relators or not responsibility or not family:
        return None
    fam = unicodedata.normalize('NFKD', family).encode('ascii', 'ignore').decode().lower().strip(' ,.')
    text = unicodedata.normalize('NFKD', responsibility).encode('ascii', 'ignore').decode().lower()
    return 'edited' if EDITING.search(responsibility) and len(fam) > 1 and re.search(r'\b' + re.escape(fam) + r'\b', text) else None


def catalogue_roles(index, names, bases=None):
    """LCCN -> [(pos, lcid, role)] for headings that resolve to one of the loaded authorities (by $0, the
    authorised heading, or an earlier form of it: former_heading), or, for a heading without dates that resolves
    to none, the one authority in the whole file with that base name (unique_bases)."""
    bases = bases or {}
    roles = defaultdict(list)
    for part in sorted(glob.glob(f'{index}/headings-*.parquet')):
        rec_part = part.replace('/headings-', '/records-')
        has_resp = 'responsibility' in {c[0] for c in duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{rec_part}')").fetchall()}
        resp = f"r.responsibility" if has_resp else "''"
        rows = duckdb.sql(f"SELECT h.control, h.pos, h.tag, h.heading, h.uri, h.relators, h.family, {resp} FROM read_parquet('{part}') h "
                          f"LEFT JOIN read_parquet('{rec_part}') r ON r.control = h.control WHERE h.tag IN ('100', '700')").fetchall()
        for control, pos, tag, heading, uri, rel, family, responsibility in rows:
            role = role_of(tag, rel) or editor_by_statement(tag, rel, family, responsibility)
            if not role:
                continue
            lcid, via = resolve(dict(heading=heading, uri=uri or ''), names)
            if not lcid or (via == 'variant' and not former_heading(heading, names[0][lcid]['label'])):
                lcid = bases.get(base_name(heading)) if not label_dates(heading) else None
                via = 'unique_base' if lcid else via
            if lcid and not names[0][lcid].get('undifferentiated'):
                roles[control.strip()].append((0 if tag == '100' else pos, lcid, role))
    return roles


def works_from(index, roles):
    """[(lead lcid, title key) -> dict(records=[(lccn, title, year)], people={(lcid, role): [lccn]})]."""
    db = duckdb.connect()
    db.execute('CREATE TABLE want(control VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(c,) for c in roles])
    recs = db.execute(f"SELECT trim(control), title, title_a, date1 FROM read_parquet('{index}/records-*.parquet') "
                      "WHERE trim(control) IN (SELECT control FROM want)").fetchall()
    works = {}
    for lccn, title, title_a, date1 in recs:
        rs = sorted(set(roles[lccn]), key=lambda x: (x[2] != 'authored', x[0]))
        tk = title_key(title_a or title)
        if not tk:
            continue
        w = works.setdefault((rs[0][1], tk), dict(records=[], people=defaultdict(list)))
        w['records'].append((lccn, (title or title_a or '').strip(' /:;,.'), date1 if (date1 or '')[:4].isdigit() else ''))
        for _, lcid, role in rs:
            if lccn not in w['people'][lcid, role]:
                w['people'][lcid, role].append(lccn)
    return works


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--phase', choices=('works', 'relations'), required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--index', default='/mnt/e/lc-bib-2016/index')
    ap.add_argument('--names', default='/mnt/e/lc-authorities/personal-names.parquet')
    args = ap.parse_args()
    state = State.load(args.state)
    lc_key = {a[6:]: k for a, k in state.anchor.items() if a.startswith('lcnaf:') and state.keys[k]['type'] == 'person'}
    names = load_names(args.names, set(lc_key))
    works = works_from(args.index, catalogue_roles(args.index, names, unique_bases(args.names, set(lc_key))))
    report, ops = Counter(works=len(works)), []
    for (lead, tk), w in sorted(works.items()):
        recs = sorted(w['records'], key=lambda r: (r[2] or '9999', r[0]))
        anchors = [f'lccn:{r[0]}' for r in recs]
        owners = {state.anchor[a] for a in anchors if a in state.anchor}
        if args.phase == 'works':
            if len(owners) > 1:
                report['editions_on_several_works'] += 1
                continue
            if owners:
                new = [a for a in anchors if a not in state.anchor]
                if new:
                    ops.append(dict(event='attach', key=owners.pop(), anchors=new, aliases=[], members=[],
                                    basis='further editions in the LC catalogue'))
                    report['editions_attached'] += 1
                continue
            year = next((r[2] for r in recs if r[2]), '')
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='work', label=recs[0][1][:250], resolution='established',
                            anchors=anchors, aliases=[], members=[f'lc-first-year:{year}'] if year else [],
                            basis=f'LC catalogue (Books All 2016): {len(recs)} edition(s) under LC {lead}'))
            report['works_minted'] += 1
            continue
        if len(owners) != 1:
            report['work_not_keyed'] += 1
            continue
        for (lcid, role), lccns in sorted(w['people'].items()):
            claim_anchors = [f'lc-{role}:{x}:{lcid}' for x in sorted(lccns)]
            have = {state.anchor[a] for a in claim_anchors if a in state.anchor}
            if have:
                new = [a for a in claim_anchors if a not in state.anchor]
                if len(have) == 1 and new:
                    ops.append(dict(event='attach', key=have.pop(), anchors=new, aliases=[], members=[],
                                    basis='the same role in a further edition'))
                report[f'{role}_already_keyed'] += 1
                continue
            ops.append(dict(event='mint', key=f'new:{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=claim_anchors, relation=dict(subject=f'lcnaf:{lcid}', predicate=role, object=anchors[0])))
            report[f'{role}_minted'] += 1
    materialise(state, dict(basis='lc works', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    name = 'works' if args.phase == 'works' else 'relations'
    (args.out / f'{name}.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis="books by keyed people in LC's catalogue (MDSConnect Books All 2016)", decided_by='build', ops=ops),
        ensure_ascii=False).encode() + b'\n'))
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)))
    (args.out / f'report-{name}.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
