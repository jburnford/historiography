"""Authors of much-cited books who hold no key -> keys, through LC's record of the book (2026-11-03). Writes a proposal.

The ranked list of ungrounded cited works (ungrounded_works.py) is led by books whose author no key holds
(`author_not_keyed`, and from the second run `author_keyed_no_lc` and `primary_source`: Ilmar Rohloff de Mattos, *O Tempo Saquarema*; Robert Slenes, *Na senzala, uma flor*). The book
identifies its author (identity by works): for each such book cited by at least --min theses, LC's 2016 catalogue
(local index, scripts/lc_bib_index.py) is searched for records of the same book:
- the record's main title (key_lc_works.title_key, before the first colon) equals the cited main title, three
  words or more, or the whole titles are equal;
- a 100/700 heading on it has the cited author's family name (accents ignored) and a compatible given name
  (key_registry.names_compatible), and every given name of the shorter form is in the longer one
  (namesake_check_groups.given_names_agree: the 2026-11-03 runs tied pooled ids like 'silva|maria' and 'lopes|jose'
  to the one Maria or José whose book LC had; namesake-check-2026-11-04 holds Sol's reading of those ties);
- the record's year is within five of the cited year (editions and reprints);
- that heading resolves to exactly one live, differentiated LC personal-name authority (lc_resolve_authorities
  .resolve: $0, authorised heading, or an earlier form with the same dates).
When all the cited author's matching records give one authority, the author is that person: the key holding the
authority gains `diss-person:<corpus id>`, or a new key is minted with `lcnaf:<id>` and `diss-person:<corpus id>`
(established: a public PID); a key that holds the corpus id but no LC authority gains the authority (Rotundo,
Lyotard), and when another key holds that authority the two are held for review, not merged. Books the ranked list
files as primary sources are taken too (Brazilian bibliographies mark translated classics as sources). Corpus ids given as variants of one author ('bullock|alan', 'bullock|allan') go onto
the one key; a corpus id naming no one in particular ('curtis', 'davis|j') is skipped, and so is one whose
already-grounded citations reach works of another person of that family (--crosswalk; thompson|edward). An id cited by 10+
theses whose matched books carry under --min-share of them is held in minor-share.json (a pooled id: reis|jose). The next key_lc_works run then keys their LC books, and the crosswalk their citations.

    python3 scripts/key_cited_book_authors.py --ranked data/identifiers/ungrounded-works-2026-11-03c/ranked.csv.gz \\
        --out data/identifiers/cited-book-authors-2026-11-03
"""
import argparse
import csv
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_lc_works import former_heading, title_key
from key_registry import names_compatible
from lc_resolve_authorities import load_names, resolve
from namesake_check_groups import given_names_agree
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LC_INDEX = Path('/mnt/e/lc-bib-2016/index')
LC_NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
# LC's 2016 record of the book carries a heading LC has since replaced with a new authority (checked on id.loc.gov)
LC_CORRECTIONS = {
    'rosen|hannah': ('no2009177673', 'Rosen, Hannah (Hannah R.)'),  # 2008029870 is under Rosén, Hannah (n84020424)
}


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip(' ,.')


def weak_corpus_id(person):
    """A corpus id that names no one in particular: family name only, initials only, or a year caught in the name
    ('curtis', 'davis|j', 'meiggs|1960 r'); anchoring it would send every such citation to one person."""
    family, _, given = person.partition('|')
    return not given or any(ch.isdigit() for ch in given) or all(len(t) == 1 for t in given.split())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ranked', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min', type=int, default=5)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--crosswalk', type=Path, nargs='*', default=[],
                    help='crosswalks of cited works already grounded: an id also cited for another keyed person is a mix')
    ap.add_argument('--min-share', type=float, default=0.25,
                    help="hold an id when its matched books carry less than this share of the theses citing it")
    ap.add_argument('--candidates-only', action='store_true', help='write candidates.json and stop (no key log load)')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute("SET memory_limit = '3GB'")
    db.execute("SET temp_directory = '/mnt/e/duckdb-tmp'")
    books = db.execute(f"""SELECT work_id, title, try_cast(year AS INT), try_cast(theses AS INT) FROM read_csv('{args.ranked}', all_varchar=true)
                           WHERE reason IN ('author_not_keyed', 'author_keyed_no_lc', 'primary_source') AND kind IN ('book', 'book_or_serial', 'unstyled')
                             AND try_cast(theses AS INT) >= {args.min}""").fetchall()
    db.execute('CREATE TABLE b(w VARCHAR)')
    db.executemany('INSERT INTO b VALUES (?)', [(r[0],) for r in books])
    people = defaultdict(list)                        # work -> (corpus person id, display name)
    for p, w, name in db.execute(f"""SELECT a.person_key, a.work_id, c.name FROM read_csv('{CORPUS}/authored.csv.gz') a
            LEFT JOIN read_csv('{CORPUS}/cited-people.csv', all_varchar=true) c USING (person_key)
            WHERE a.work_id IN (SELECT w FROM b)""").fetchall():
        people[w].append((p, name or p))
    keys = {}                                          # title key -> [(work id, year)]
    for w, title, year, n in books:
        main, whole = title_key((title or '').split(':')[0]), title_key(title or '')
        for k in {main if len(main.split()) >= 3 else None, whole}:
            if k:
                keys.setdefault(k, []).append((w, year))
    firsts = {k.split()[0] for k in keys}
    db.execute('CREATE TABLE tk(k VARCHAR)')
    db.executemany('INSERT INTO tk VALUES (?)', [(k,) for k in firsts])
    # cheap SQL prefilter on the first word of the title once accents, punctuation and a leading article are gone;
    # title_key decides in Python
    recs = db.execute(f"""SELECT control, title, title_a, year FROM (
            SELECT trim(control) AS control, title, title_a, try_cast(date1 AS INT) AS year,
                   list_filter(string_split(regexp_replace(strip_accents(lower(coalesce(title_a, ''))), '[^a-z0-9 ]+', ' ', 'g'), ' '),
                               x -> x <> '') AS ws FROM read_parquet('{LC_INDEX}/records-*.parquet'))
            WHERE len(ws) > 0 AND (ws[1] IN (SELECT k FROM tk) OR (len(ws) > 1 AND ws[2] IN (SELECT k FROM tk)))""").fetchall()
    hits = defaultdict(set)                            # LC control -> our work ids
    for control, title, title_a, year in recs:
        for k in {title_key((title_a or '').split(':')[0]), title_key(title or '')}:
            for w, wy in keys.get(k, ()):
                if not (wy and year and abs(wy - year) > 5):
                    hits[control].add(w)
    db.execute('CREATE TABLE hc(c VARCHAR)')
    db.executemany('INSERT INTO hc VALUES (?)', [(c,) for c in hits])
    heads = db.execute(f"""SELECT trim(control), heading, uri, family, given FROM read_parquet('{LC_INDEX}/headings-*.parquet')
                           WHERE trim(control) IN (SELECT c FROM hc) AND tag IN ('100', '700')""").fetchall()
    # resolve only the headings we need
    from lc_resolve_authorities import norm
    db.execute('CREATE TABLE hh(h VARCHAR)')
    db.executemany('INSERT INTO hh VALUES (?)', [(norm(h),) for _, h, _, _, _ in heads])
    lcids = {r[0] for r in db.execute(f"""SELECT lcid FROM read_parquet('{LC_NAMES}') WHERE label IN (SELECT h FROM hh)
                                         UNION SELECT lcid FROM (SELECT lcid, unnest(variants) AS v FROM read_parquet('{LC_NAMES}'))
                                         WHERE v IN (SELECT h FROM hh)""").fetchall()}
    lcids |= {u.rstrip('/').split('/')[-1] for _, _, u, _, _ in heads if u}
    names = load_names(LC_NAMES, lcids)
    found = defaultdict(set)                            # (work, corpus person) -> LC ids
    for control, heading, uri, family, given in heads:
        lcid, via = resolve(dict(heading=heading, uri=uri or ''), names)
        if not lcid or names[0][lcid].get('undifferentiated') or names[0][lcid].get('deprecated'):
            continue
        if via == 'variant' and not former_heading(heading, names[0][lcid]['label']):
            continue                                   # another person's 'see from' form as often as not
        for w in hits[control]:
            for p, display in people.get(w, ()):
                if fold(family) == fold(display.split(',')[0]) and names_compatible(names[0][lcid]['label'], display) \
                        and given_names_agree(names[0][lcid]['label'], display):
                    found[w, p].add(lcid)
    by_person = defaultdict(set)
    for (w, p), ids in found.items():
        by_person[p] |= ids
    cands = []
    theses = {r[0]: r[3] for r in books}
    for p, ids in sorted(by_person.items()):
        ws = sorted({w for (w, q) in found if q == p}, key=lambda w: -theses[w])
        label = names[0][next(iter(ids))]['label'] if len(ids) == 1 else ''
        if p in LC_CORRECTIONS:
            lcid, label = LC_CORRECTIONS[p]
            ids = {lcid}
        cands.append(dict(person=p, lc=sorted(ids), label=label, works=ws, theses=sum(theses[w] for w in ws)))
    (args.out / 'candidates.json').write_text(json.dumps(cands, ensure_ascii=False, indent=1) + '\n')
    report = Counter(books=len(books), lc_records=len(hits), people_found=len(by_person),
                     one_authority=sum(1 for c in cands if len(c['lc']) == 1), several=sum(1 for c in cands if len(c['lc']) > 1))
    print(json.dumps(report))
    if args.candidates_only:
        return
    # 2026-11-03: thompson|edward was cited for E. J. Thompson's India books and for E. P. Thompson's Grid of Inheritance;
    # an id whose grounded citations already reach works of another person of that family names no one in particular
    others = defaultdict(set)                          # corpus id -> keys of other people its grounded works belong to
    if args.crosswalk:
        files = ', '.join(f"'{x}'" for x in args.crosswalk)
        graph = ROOT / 'build/graph'
        for p, key, label in db.execute(f"""
                WITH x AS (SELECT DISTINCT work_id, key FROM read_csv([{files}], all_varchar=true, union_by_name=true)),
                anc AS (SELECT a, key AS wk FROM (SELECT key, unnest(anchors) AS a FROM '{graph}/work.parquet')),
                xk AS (SELECT x.work_id, coalesce(w.key, anc.wk) AS wk FROM x LEFT JOIN '{graph}/work.parquet' w ON w.key = x.key
                       LEFT JOIN anc ON anc.a = x.key),
                au AS (SELECT "from" AS pk, "to" AS wk FROM {keylog(graph, 'authored')} UNION SELECT "from", "to" FROM {keylog(graph, 'edited')})
                SELECT DISTINCT a.person_key, au.pk, pp.label FROM read_csv('{CORPUS}/authored.csv.gz') a JOIN xk USING (work_id)
                JOIN au ON au.wk = xk.wk JOIN '{graph}/person.parquet' pp ON pp.key = au.pk""").fetchall():
            if fold(p.split('|')[0]) == fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1]):
                others[p].add(key)
    # 2026-11-04 namesake check: a minor book pulled a much-cited pooled id onto its author (reis|jose, 9 of the
    # 222 citations José Carlos Reis's books draw; mello|maria 7 of 51; johnson|samuel's Yoruba history beside Dr
    # Johnson). Ids whose matched books carry less than --min-share of their citing theses go to minor-share.json.
    with open(CORPUS / 'cited-people.csv', newline='', encoding='utf-8') as f:
        id_theses = {r['person_key']: int(r['cited_by_dissertations'] or 0) for r in csv.DictReader(f)}
    minor = []
    state = State.load(args.state)
    by_lc = defaultdict(list)                        # one key per authority: 'bullock|alan' and 'bullock|allan' are one man
    for c in cands:
        if len(c['lc']) != 1:
            continue
        if weak_corpus_id(c['person']):
            report['weak_corpus_id'] += 1
            continue
        holder = state.anchor.get(f'diss-person:{c["person"]}')
        if others.get(c['person'], set()) - {state.anchor.get(f'lcnaf:{c["lc"][0]}'), holder}:
            report['id_cited_for_another_person'] += 1
            continue
        if holder and any(a.startswith('lcnaf:') for a in state.keys[holder]['anchors']):
            report['corpus_id_keyed_with_lc'] += 1
            continue
        total = id_theses.get(c['person'], 0)
        if total >= 10 and c['theses'] < args.min_share * total:
            report['minor_share'] += 1
            minor.append(dict(c, id_theses=total))
            continue
        by_lc[c['lc'][0]].append(c)
    (args.out / 'minor-share.json').write_text(json.dumps(minor, ensure_ascii=False, indent=1) + '\n')
    clusters = []
    for lc, cs in sorted(by_lc.items()):
        anchors = {f'lcnaf:{lc}'} | {f'diss-person:{c["person"]}' for c in cs}
        owners = {state.anchor[a] for a in anchors if a in state.anchor}
        report['mint' if not owners else 'attach' if len(owners) == 1 else 'several_keys'] += 1
        report['corpus_ids'] += len(cs)
        clusters.append(dict(type='person', label=cs[0]['label'], members=set(), aliases=set(), resolution='established',
                             anchors=anchors,
                             basis='; '.join(f'author of the cited book {c["works"][0]} (corpus id {c["person"]})' for c in cs)
                                   + f': LC catalogues it under {cs[0]["label"]} ({lc})'))
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='cited book authors', ops=ops), 'dry-run', 'dry-run')
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="authors of much-cited books no key held, identified by LC's record of the book", decided_by='rule', ops=ops),
        ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    report = dict(report, ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
