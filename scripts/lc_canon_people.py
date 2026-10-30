"""Canon-map people -> LC name authorities and life dates, through the books the theses cite (PID-PLAN.md section 6).

For each person on the canon map (data/dissertation-layer/site/canon-map.json) the script takes their
most-cited books in the dissertation graph (authored.csv.gz + works.csv, kind = book) and searches the
LC catalogue by main title and surname (SRU, `dc.title` and `dc.creator`, up to five records). A record
counts only if:
- its title (245 $a) agrees with the cited title (same main title after normalisation, or token overlap
  of at least 0.8; the cited main title needs two or more content words), and
- exactly one of its personal-name headings is compatible with the person's name
  (identity_routes.compatible).
The heading is resolved through the local LC name index (scripts/lc_names_index.py), as in
scripts/lc_resolve_authorities.py. A book resolves only if every title-agreeing record names the same
authority (otherwise `records_disagree`: namesakes behind one title). Books are tried most-cited first,
up to --books, until the authority is confirmed; two books naming different authorities give
`books_disagree`.

**Tiers** (reviewed by a Fable agent on 2026-10-30). A canon key is a name cluster from bibliography
parsing, so one book only shows that *a* person of that name wrote it:
- `exact`: the key has a full given name and at least one confirmation: a second book naming the same
  authority, an LC 670 source citing the title, or LC's own Wikidata link equal to a title-verified
  dissertation QID. Only this tier may become an `lcnaf:` anchor in the key log.
- `candidate_single_book`, `candidate_initials_only` (a single initial: 'Taylor, A.' mixes people;
  two or more initials, 'Thompson, E. P.', count as a full name),
  `candidate_wikidata_disagrees`: recorded for review, never anchors.
Life dates are read with their source (046 or heading) and precision.

Read-only against the repository; LC responses are cached.

    python3 scripts/lc_canon_people.py --cache /mnt/e/lc-authorities/sru-canon \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/field-research/lc-authorities-2026-10-30/canon
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import State  # noqa: E402
from identity_routes import compatible  # noqa: E402
from key_canon_map import CANON, D, TITLE_TIERS, canon_keys  # noqa: E402
from lc_authority_pilot import MARC, SRU, Fetcher, bib_headings  # noqa: E402
from lc_catalogue_harvest import record_facts  # noqa: E402
from lc_resolve_authorities import label_dates, life, load_names, resolve  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRU5 = SRU.replace('maximumRecords=1', 'maximumRecords=5')
STOP = {'the', 'a', 'an', 'of', 'and', 'in', 'on', 'to', 'for', 'la', 'le', 'les', 'de', 'des', 'du', 'et', 'l', 'd'}


def words(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    return re.findall(r'[a-z0-9]+', t)


def main_title(t):
    """The title before its subtitle. Periods are not split on ('St. Louis', 'U.S. Foreign Policy')."""
    return re.split(r'\s*[:;=/]\s*', t or '', maxsplit=1)[0].strip(' .,')


def content(t):
    return [w for w in words(main_title(t)) if w not in STOP]


def titles_agree(cited, record):
    """Same main title after normalisation, or token overlap >= 0.8; at least two content words."""
    a, b = words(main_title(cited)), words(main_title(record))
    sa, sb = set(content(cited)), set(content(record))
    if len(sa) < 2 or not b:
        return False
    return a == b or len(sa & sb) / len(sa | sb) >= 0.8


def source_names_title(sources, cited):
    """An LC 670 source citation that contains the cited main title (three or more words)."""
    w = words(main_title(cited))
    if len([x for x in w if x not in STOP]) < 2 or len(w) < 3:
        return False
    needle = ' '.join(w)
    return any(needle in ' '.join(words(s)) for s in sources)


def initials_only(label):
    """A single initial ('Taylor, A.'): such keys pool several people. Two or more initials
    ('Thompson, E. P.') are specific enough to be treated like a full name."""
    toks = re.findall(r'[^\W\d_]+', label.partition(', ')[2])
    return len(toks) < 2 and all(len(x) == 1 for x in toks)


def records(xml):
    """Each MARC record of an SRU response, wrapped so bib_headings/record_facts can read it alone."""
    out = []
    for rec in ET.fromstring(xml).iter(f'{MARC}record'):
        wrap = ET.Element('wrap')
        wrap.append(rec)
        s = ET.tostring(wrap, encoding='unicode')
        out.append((bib_headings(s)[0], record_facts(s)))
    return out


def as_credit(label):
    """'Thompson, E. P.' -> 'E. P. Thompson' (the form identity_routes.compatible expects)."""
    family, comma, given = label.partition(', ')
    return f'{given} {family}' if comma else label


def books_by_person(keys, per_person):
    db = duckdb.connect()
    db.execute("CREATE TABLE k(person_key VARCHAR)")
    db.executemany("INSERT INTO k VALUES (?)", [(k,) for k in keys])
    db.execute(f"""CREATE TABLE a AS SELECT person_key, work_id FROM read_csv('{D / 'authored.csv.gz'}', all_varchar=true)
                   WHERE person_key IN (SELECT person_key FROM k)""")
    rows = db.execute(f"""
        SELECT a.person_key, w.work_id, w.title, w.year, CAST(w.cited_by_dissertations AS INTEGER) AS n
        FROM a JOIN read_csv('{D / 'works.csv'}', all_varchar=true, max_line_size=10000000) w USING (work_id)
        WHERE w.kind = 'book' AND w.title IS NOT NULL
        ORDER BY a.person_key, n DESC, w.work_id""").fetchall()
    out = defaultdict(list)
    for key, wid, title, year, n in rows:
        if len(out[key]) < per_person and len(content(title)) >= 2:
            out[key].append(dict(work_id=wid, title=title, year=year or '', cited=n))
    return out


def query(title, family):
    t = ' '.join(words(main_title(title))[:8])
    f = (words(family) or [''])[0]
    return f'dc.title="{t}" and dc.creator={f}' if t and f else ''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--names', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--books', type=int, default=3, help='books tried per person')
    ap.add_argument('--delay', type=float, default=2.0)
    ap.add_argument('--pause', type=float, default=60)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    canon = json.loads(CANON.read_text(encoding='utf-8'))
    nodes = sorted(canon['nodes'], key=lambda n: -n['cited'])
    if args.limit:
        nodes = nodes[:args.limit]
    graph_key = canon_keys(canon['nodes'])
    state = State.load(ROOT / 'data/identifiers/events.jsonl')
    books = books_by_person({graph_key[n['name'], n['qid']] for n in nodes}, args.books)
    qid_basis = {}
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        wanted = set(graph_key.values())
        for r in csv.DictReader(f):
            if r['person_key'] in wanted:
                qid_basis[r['person_key']] = r['qid_basis']
    names = load_names(args.names)
    by_id = names[0]
    print(f'{len(nodes)} canon people; {sum(map(len, books.values()))} books to try; {len(by_id):,} LC names', flush=True)
    fetch = Fetcher(args.cache, args.delay)

    rows, stats, streak = [], Counter(), 0
    for k, n in enumerate(nodes, 1):
        gk = graph_key[n['name'], n['qid']]
        key = state.lookup(f'diss-person:{gk}')
        family = n['label'].partition(', ')[0]
        person = as_credit(n['label'])
        found, tried, outcome = [], 0, 'no_book'
        for b in books.get(gk, []):
            q = query(b['title'], family)
            r = fetch.get(SRU5 + urllib.parse.quote(q))
            if r['status'] == 0:
                streak += 1
                if streak >= 3:
                    time.sleep(args.pause)
                outcome = outcome if found else 'unanswered'
                continue
            streak, tried = 0, tried + 1
            try:
                recs = records(r['body'])
            except ET.ParseError:
                continue
            ids, seen_title = set(), False
            for heads, facts in recs:
                if not titles_agree(b['title'], facts.get('title', '')):
                    continue
                seen_title = True
                match = [h for h in heads if compatible(person, h['given'], h['family'])
                         or (h['fuller'] and compatible(person, h['fuller'], h['family']))]
                if len(match) > 1:
                    ids.add('ambiguous')
                elif match:
                    lcid, via = resolve(match[0], names)
                    if lcid and not by_id[lcid]['undifferentiated']:
                        ids.add(lcid)
                        hit = dict(lcid=lcid, via=via, book=b, record_title=facts['title'])
            if len(ids) == 1 and 'ambiguous' not in ids:
                found.append(hit)
            elif ids:
                outcome = outcome if found else 'records_disagree'      # namesakes behind one title
                continue
            else:
                outcome = outcome if found else ('person_not_resolved' if seen_title else
                                                 'no_title_match' if recs else 'no_lc_record')
                continue
            lcids = {f['lcid'] for f in found}
            if len(lcids) > 1:
                break
            a = by_id[found[0]['lcid']]
            lc_qids = {e.rsplit('/', 1)[-1] for e in a['external'] if 'wikidata.org/entity/' in e}
            if (n['qid'] and n['qid'] in lc_qids and qid_basis.get(gk) in TITLE_TIERS) or \
                    any(source_names_title(a['sources'], f['book']['title']) for f in found) or len(found) >= 2:
                break           # confirmed: no need for more books
        lcids = {f['lcid'] for f in found}
        if len(lcids) > 1:
            outcome = 'books_disagree'
        elif lcids:
            outcome = 'resolved'
        stats[outcome] += 1
        row = dict(key=key[0] if len(key) == 1 else '', graph_key=gk, label=n['label'], cited=n['cited'],
                   dissertation_qid=n['qid'] or '', dissertation_qid_basis=qid_basis.get(gk, ''),
                   outcome=outcome, books_tried=tried)
        if outcome == 'resolved':
            f, a = found[0], by_id[found[0]['lcid']]
            lf = life(a, label_dates(a['label']))
            lc_qids = {e.rsplit('/', 1)[-1] for e in a['external'] if 'wikidata.org/entity/' in e}
            wd = ('' if not lc_qids or not n['qid'] else 'agrees' if n['qid'] in lc_qids else 'disagrees')
            src = any(source_names_title(a['sources'], x['book']['title']) for x in found)
            confirmations = [c for c, ok in (('second_book', len(found) >= 2), ('lc_670_names_title', src),
                                             ('wikidata_agrees', wd == 'agrees' and
                                              qid_basis.get(gk) in TITLE_TIERS)) if ok]
            if initials_only(n['label']):
                tier = 'candidate_initials_only'
            elif wd == 'disagrees':
                tier = 'candidate_wikidata_disagrees'
            elif confirmations:
                tier = 'exact'
            else:
                tier = 'candidate_single_book'
            row.update(lcnaf=f['lcid'], lc_label=a['label'], via=f['via'], tier=tier,
                       confirmations=' '.join(confirmations), books_agreeing=len(found),
                       evidence_works=' '.join(x['book']['work_id'] for x in found),
                       evidence_title=f['record_title'],
                       birth_year=lf['birth'][0], birth_value=lf['birth'][1], birth_source=lf['birth'][2],
                       birth_precision=lf['birth'][3], death_year=lf['death'][0], death_value=lf['death'][1],
                       death_source=lf['death'][2], death_precision=lf['death'][3],
                       external=' '.join(e for e in a['external'] if 'viaf.org/en/viaf/LC' not in e),
                       lc_wikidata=' '.join(sorted(lc_qids)), wikidata_check=wd)
        rows.append(row)
        if k % 100 == 0:
            print(f'{k}/{len(nodes)} people, {fetch.requests} requests, {dict(stats)}', flush=True)

    fields = ['key', 'graph_key', 'label', 'cited', 'dissertation_qid', 'dissertation_qid_basis', 'outcome',
              'books_tried', 'lcnaf', 'lc_label', 'via', 'tier', 'confirmations', 'books_agreeing', 'evidence_works',
              'evidence_title', 'birth_year', 'birth_value', 'birth_source', 'birth_precision', 'death_year',
              'death_value', 'death_source', 'death_precision', 'external', 'lc_wikidata', 'wikidata_check']
    with open(args.out / 'canon-people-lc.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    res = [r for r in rows if r['outcome'] == 'resolved']
    summary = dict(canon_snapshot=canon['snapshot'], people=len(rows), requests=fetch.requests,
                   outcomes=dict(stats.most_common()),
                   with_birth_year=sum(1 for r in res if r['birth_year']),
                   with_death_year=sum(1 for r in res if r['death_year']),
                   wikidata_check=dict(Counter(r['wikidata_check'] or 'not_checkable' for r in res)),
                   tiers=dict(Counter(r['tier'] for r in res).most_common()),
                   birth_source=dict(Counter(r['birth_source'] or 'none' for r in res)),
                   unresolved_keys_reached=sum(1 for r in res if r['key'] and
                                               state.keys[r['key']]['resolution'] == 'unresolved'))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
