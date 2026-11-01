"""AHA dissertation authors -> LC name authorities through their published dissertations (2026-11-01). Writes a proposal.

Most AHA authors rest on one source record (`recorded`). Many published the dissertation as a book, and LC's
catalogue names the book's author with an authority heading. Identity by works: an AHA author key joins the
LC authority of a catalogued book that is their dissertation as published.

1. **Match** (LC MDSConnect Books All 2016, offline index from scripts/lc_bib_index.py): a personal-name
   heading (100/700) whose name agrees with the dissertator, on a record whose title is the dissertation by
   key_aha's `own_book` rule: three or more shared content words, at least 60% of the shorter, published no
   earlier than the year before the PhD. The dissertation's main title is compared with the book's whole
   title, subtitle included: a published thesis is often retitled and keeps the thesis title as its
   subtitle (Michael Childs, *Labour's Apprentices: Working-Class Lads in Late Victorian and Edwardian
   England*). A dissertation whose main title has only two content words matches a book with the same main
   title, word for word, published within fifteen years (Erika Dyck, *Psychedelic Psychiatry*). Topic alone
   never joins.
2. **Heading -> authority** with the reviewed-book resolver (`lc_resolve_authorities.resolve`: the record's
   $0, else exactly one live authorised heading, or a heading since closed). Variant forms are not used here
   (the match already rests on one book), and undifferentiated authorities are skipped. Only the name
   records of the matched families are loaded (the full index peaked at 16 GB with the headings).
   `matches.csv` lists each join with the book title, for review.
3. **Clusters**: `aha-phd:<record>` + `lcnaf:<id>`. Refused and queued: an AHA record reaching several
   authorities; an authority reached from several AHA keys that the merge rule does not join; a key holding a
   different LC authority, or that rejected this one. A cluster reaching two keys (the authority already keyed
   elsewhere) merges only when all names agree and no other LC authority is involved, through the merge guard.

    python3 scripts/key_aha_lc_books.py --index /mnt/e/lc-bib-2016/index \\
        --names /mnt/e/lc-authorities/personal-names.parquet --out data/identifiers/aha-lc-books-2026-11-01
"""
import argparse
import csv
import gc
import gzip
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, State, materialise, plan
from key_aha import AHA, own_book
from key_lc_books import family_key, label_of, merge_rule
from key_registry import names_compatible
from lc_canon_people import STOP, as_credit, content, given_agrees, main_title, words
from identity_routes import compatible
from lc_resolve_authorities import load_names, norm, resolve
from merge_guard import guarded


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def aha_authors(state):
    """AHA record id -> (key, record) for author keys without an LC authority whose main title can match."""
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    out = {}
    for k, v in state.keys.items():
        if v['type'] != 'person' or v['status'] not in ('active', 'provisional') \
                or any(a.startswith('lcnaf:') for a in v['anchors']):
            continue
        for a in v['anchors']:
            r = records.get(a[len('aha-phd:'):]) if a.startswith('aha-phd:') else None
            if r and r['dissertator'] and len(content(r['title'] or '')) >= 2 and (r['year'] or '').isdigit():
                out[r['id']] = (k, r)
    return out


def catalogue_works(index, families):
    """family_key -> [(normalised heading, label, uri, [(content words, year)])] for headings of those families."""
    db = duckdb.connect()
    db.execute('SET memory_limit = "6GB"')
    db.execute('CREATE TABLE fam(f VARCHAR)')
    db.executemany('INSERT INTO fam VALUES (?)', [(f,) for f in families])
    rows = db.execute(f"""
        SELECT h.heading, h.family, h.uri, r.title, r.date1
        FROM read_parquet('{index}/headings-*.parquet') h
        JOIN read_parquet('{index}/records-*.parquet') r USING (control)
        WHERE h.tag IN ('100', '700') AND lower(strip_accents(h.family)) IN (SELECT f FROM fam)""").fetchall()
    people = {}
    for heading, family, uri, title, date1 in rows:
        c = {w for w in words(title or '') if w not in STOP}      # the book's whole title, subtitle included
        if len(c) < 3:
            continue
        key = norm(heading)
        p = people.setdefault(key, dict(family=family, uri=uri or '', works=[], titles=[]))
        p['uri'] = p['uri'] or uri or ''
        p['works'].append((c, int(date1) if (date1 or '').isdigit() else None))
        p['titles'].append((title, date1))
    cands = defaultdict(list)
    for key, p in people.items():
        label = label_of(key)
        if ', ' in label:
            cands[family_key(p['family'])].append((key, label, p['works']))
    return cands, people, len(rows)


def matched_lcids(path, heads, uris):
    """LC ids whose authorised label has the family of a matched heading, plus the headings' $0 ids. Every
    authority a label or open-date match can reach shares the heading's family, so resolve() on this subset
    gives the full index's answer for those routes (variants are not used), in a fraction of the memory."""
    db = duckdb.connect()
    db.execute('CREATE TABLE fam(f VARCHAR)')
    db.executemany('INSERT INTO fam VALUES (?)', [(f,) for f in {h.partition(',')[0] for h in heads}])
    ids = {r[0] for r in db.execute(f"""SELECT lcid FROM read_parquet('{path}')
                                       WHERE split_part(label, ',', 1) IN (SELECT f FROM fam)""").fetchall()}
    return ids | {u.rstrip('/').split('/')[-1] for u in uris.values() if u}


def same_main_title(record, cands, people):
    """Headings with a book whose main title is the dissertation's two-word main title, word for word
    (Erika Dyck: 'Psychedelic Psychiatry: LSD and Post-World War II Medical Experimentation', McMaster 2005;
    'Psychedelic psychiatry : LSD from clinic to campus', 2008), compatible names, published from the year
    before the PhD to fifteen years after. own_book needs three shared words, which a two-word title cannot give."""
    d = content(record['title'] or '')
    family, _, given = (record['dissertator'] or '').partition(', ')
    year = int(record['year'])
    hits = set()
    for key, label, _ in cands.get(family_key(family), ()):
        fam, _, giv = label.partition(', ')
        if not (compatible(as_credit(record['dissertator']), giv, fam) and given_agrees(given, giv)):
            continue
        for t, y in people[key]['titles']:
            if content(t or '') == d and (y or '').isdigit() and year - 1 <= int(y) <= year + 15:
                hits.add(key)
                break
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--index', type=Path, required=True, help='lc_bib_index.py output directory')
    ap.add_argument('--names', type=Path, required=True, help='LC personal-name index (personal-names.parquet)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    authors = aha_authors(state)
    families = {fold(r['dissertator'].partition(', ')[0]) for _, r in authors.values()}
    cands, people, n_rows = catalogue_works(args.index, families)
    report, queue = Counter(aha_authors=len(authors), heading_rows=n_rows), []
    matched = {}                                     # record id -> set of normalised headings
    for rid, (k, r) in authors.items():
        two_word = len(content(r['title'] or '')) == 2
        hits = same_main_title(r, cands, people) if two_word else own_book(r, cands)
        if hits:
            matched[rid] = hits
            report['matched_by_identical_two_word_main_title'] += two_word
    report['records_matching_a_book'] = len(matched)
    evidence = {}
    for rid, hs in matched.items():
        d = set(content(authors[rid][1]['title']))
        for h in hs:
            best = max(people[h]['titles'], key=lambda t: len(d & {w for w in words(t[0] or '') if w not in STOP}))
            evidence[rid, h] = best
    heads = {h for hs in matched.values() for h in hs}
    uris = {h: people[h]['uri'] for h in heads}
    del cands, people
    gc.collect()
    names = load_names(args.names, matched_lcids(args.names, heads, uris))     # only the families matched
    by_id = names[0]
    lc_of = {}
    for h in heads:
        lcid, via = resolve(dict(heading=h, uri=uris[h]), names)
        if via == 'variant':          # the match rests on one book; a variant form is not enough
            lcid = ''
        if lcid and not by_id[lcid].get('undifferentiated'):
            lc_of[h] = (lcid, by_id[lcid]['label'])
        report[f'heading_{via}'] += 1
    del names
    gc.collect()
    rejected = {(m.split(':', 1)[1], k) for k, ms in state.members.items() for m in ms if m.startswith('lcnaf-rejected:')}
    rejected |= {(m.split(':', 2)[2], k) for k, ms in state.members.items() for m in ms if m.startswith('rejected:lcnaf:')}
    by_lc = defaultdict(set)
    pairs = {}
    for rid, hs in matched.items():
        lcs = {lc_of[h] for h in hs if h in lc_of}
        if len(lcs) > 1:
            queue.append(dict(kind='record_reaches_several_lcnaf', record=rid, key=authors[rid][0],
                              label=state.keys[authors[rid][0]]['label'], lcnaf=sorted(x[0] for x in lcs)))
            report['record_reaches_several_lcnaf'] += 1
        elif lcs:
            pairs[rid] = next(iter(lcs))
            by_lc[pairs[rid][0]].add(authors[rid][0])
    clusters, rows = [], []
    for rid, (lc, lc_label) in sorted(pairs.items(), key=lambda x: int(x[0])):
        k = authors[rid][0]
        label = label_of(lc_label)
        if len(by_lc[lc]) > 1:
            queue.append(dict(kind='lcnaf_reached_from_several_aha_keys', lcnaf=lc, label=label,
                              keys=sorted(by_lc[lc]), labels=[state.keys[x]['label'] for x in sorted(by_lc[lc])]))
            report['lcnaf_reached_from_several_aha_keys'] += 1
            continue
        owner = state.anchor.get(f'lcnaf:{lc}')
        problem = None
        if (lc, k) in rejected or (owner and (lc, owner) in rejected):
            problem = 'key_rejected_this_lcnaf'
        elif not names_compatible(label, state.keys[k]['label']) or (owner and not names_compatible(label, state.keys[owner]['label'])):
            problem = 'lcnaf_name_differs_from_key'
        if problem:
            queue.append(dict(kind=problem, record=rid, key=k, owner=owner, lcnaf=lc, label=label,
                              key_label=state.keys[k]['label']))
            report[problem] += 1
            continue
        report['joined_to_existing_lc_key' if owner else 'lcnaf_new_to_log'] += 1
        h = next(h for h in matched[rid] if lc_of.get(h, (None,))[0] == lc)
        rows.append(dict(record=rid, key=k, aha_title=authors[rid][1]['title'], aha_year=authors[rid][1]['year'],
                         dissertator=authors[rid][1]['dissertator'], lcnaf=lc, lc_label=lc_label, owner=owner or '',
                         book=evidence[rid, h][0], book_year=evidence[rid, h][1]))
        clusters.append(dict(type='person', label=label, anchors={f'aha-phd:{rid}', f'lcnaf:{lc}'}, members=set(),
                             aliases=set(), resolution='established',
                             basis=f'AHA {rid} published as a book LC catalogues under {lc} (Books All 2016)'))
    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state)))
    materialise(state, dict(basis='aha lc books', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json.gz').write_bytes(gzip.compress(json.dumps(dict(
        basis='AHA dissertations published as books in the LC catalogue (MDSConnect Books All 2016)', decided_by='build',
        ops=ops), ensure_ascii=False).encode() + b'\n'))
    with (args.out / 'matches.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['record'])
        w.writeheader()
        w.writerows(rows)
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(**dict(sorted(report.items())), clusters=len(clusters), ops=dict(Counter(o['event'] for o in ops)),
                   held=len(held), review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
