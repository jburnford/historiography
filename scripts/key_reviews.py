"""Book reviews -> the key log: review works, the books they review, their reviewers (2026-11-02). Writes a proposal.

User, 2026-11-02: connect the reviews data into the graph, with edges between reviewers and the authors of the
books they review. Inputs (read-only): the H-Net and Reviews in History catalogue
(/home/jic823/hnet-reviews/data/export/reviews.parquet, `is_real` rows), its review -> book bridge and book
table (data/books/), LC's records for those books (lc_catalogue_harvest: books.ndjson, books-2016.ndjson) and
the credit -> LC authority resolution (scripts/lc_resolve_authorities.py, credits.csv).

- **Books**: one work per reviewed book, anchored `hnet-book:<book_id>`, with `lccn:<LCCN>` when LC's record
  for the book was found (so it joins the LC book work keyed by key_lc_works); H-Net book ids sharing an LCCN
  are one cluster.
- **Book authors**: an `authored` claim from each LC authority LC's record of the same book credits
  (credits.csv, outcome with an LC id), unless that person already authors that work in the log.
- **Reviews**: one work per review, `hnet-review:<id>` or `rih-review:<id>` (recorded on its source page), and a
  `reviews` claim (review -> book), except where the catalogue's book citation is repeated from another record
  (collective reviews) or missing (`unlinked_reviews`).
- **Reviewers**: one person per reviewer name and affiliation as printed (`review-credit:<name>|<affiliation>`;
  a review without an affiliation gets its own, `review-credit:<source>:<id>`), with an `authored` claim for
  the review. A reviewer joins a keyed person when the names agree (key_aha_lc_notes.name_agrees: given names
  as names or nicknames, no single initials) and exactly one such person has a career fact agreeing with
  the printed affiliation:
  - the institution the AHA directory lists for them (current post);
  - a school where their AHA students took doctorates;
  - the school of their own AHA dissertation, the review dated from eight years before the PhD to three
    after (doctoral students review for H-Net);
  - a post in their LC authority's notes (670 clauses about teaching, 373 affiliations);
  - an employment or education in their ORCID record.
  When several keys pass, each on its own fact, they are one person split across keys (an AHA key and an LC
  key, both placing Constance Bouchard at Akron) and merge, through the merge guard and key_aha_career's merge
  rule (as there: Gauvreau). Otherwise the reviewer is minted `recorded` (one source record); refused groups
  are listed in candidates.json.
The graph build derives reviewer -> author edges (REVIEWED) from these claims.

    python3 scripts/key_reviews.py --out data/identifiers/reviews-2026-11-02
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, PUBLIC_SCHEMES, ROOT, State, materialise, plan
from key_aha import AHA, DIRECTORY
from key_aha_career import merge_rule, orcid_facts, surname
from merge_guard import guarded
from key_aha_lc_notes import JOB, DOCTORATE, by_letter, clauses, lc_records, lc_school_agrees, letters, name_agrees

UP = Path('/home/jic823/hnet-reviews/data')
CREDITS = ROOT / 'data/field-research/lc-authorities-2026-10-30/reviews-2026-11-02/credits.csv'
SOURCE = {'hnet': 'hnet-review', 'reviews_in_history': 'rih-review'}


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+', s))


def is_ref(aff):
    """The stand-in for a missing affiliation: the review's own reference ('hnet-review:123')."""
    return aff.split(':', 1)[0] in SOURCE.values()


HONORIFIC = re.compile(r'^((professor|prof|dr|mr|mrs|ms|miss|sir|dame|revd|rev|reverend|emeritus|the)\.?\s+)+', re.I)
GENERIC = {'', 'university', 'college', 'institute', 'school', 'centre', 'center', 'museum', 'library'}


def readings(name, aff):
    """Ways to read a printed credit as (name, affiliation). Reviews in History prints honorifics ('Professor
    Jeremy Black') and its parser sometimes leaves the affiliation's first words in the name ("Professor Catherine
    O'Donnell Arizona State" + 'University'): with no affiliation, or a generic word, the name's trailing words
    are also read as the affiliation's start."""
    n = HONORIFIC.sub('', name).strip()
    a = '' if is_ref(aff) else aff
    out = [(n, a)]
    if norm(a) in GENERIC:
        toks = n.split()
        out += [(' '.join(toks[:i]), ' '.join(toks[i:] + ([a] if a else []))) for i in range(2, len(toks))]
    return out


def year_of(date):
    m = re.search(r'\b(19|20)\d\d\b', date or '')
    return int(m.group()) if m else None


def unlinked_reviews(reviews, identified):
    """Reviews whose book link is not kept (2026-11-02):
    - collective reviews: H-Soz-u-Kult (and a few others) post one review of several books once per book, but
      the catalogue repeats the first book's citation on every record (Burghard Ciesla's 20 records of June 2004
      all cite *Was geschah am 17. Juni?*; the bodies name the other books). The same reviewer and book title on
      several records of one source keep the link on the first record only; the others are the same review
      posted twice, or a review of a book the catalogue does not name;
    - Reviews in History records whose parsed title is 'Reviews in History' and whose book has no ISBN or LCCN
      (`identified`: book ids that have one); most such records name their book by ISBN.
    Repeats are found by reviewer and book id (or title, without a book id)."""
    groups = defaultdict(list)
    out = {}
    for r in reviews:
        if norm(r[8]) == 'reviews in history' and r[7] not in identified:
            out[r[0], r[1]] = 'no book (landing page)'
        else:
            groups[r[0], norm(r[2]), r[7] or norm(r[8])].append(r)
    for rs in groups.values():
        if len(rs) > 1:
            first = min(rs, key=lambda r: (int(r[1]) if r[1].isdigit() else 0, r[1]))
            out.update({(r[0], r[1]): f'repeats the citation of {SOURCE[first[0]]}:{first[1]}' for r in rs if r is not first})
    return out


def lc_book_lccn(paths):
    """book_id -> LCCN of LC's record for the book, and book_id -> its title there (the last file wins, as in
    lc_resolve_authorities)."""
    out, titles = {}, {}
    for p in paths:
        with open(p, encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                lccn = (r.get('record') or {}).get('lccn')
                if lccn:
                    out[r['book_id']] = lccn.strip()
                    titles[r['book_id']] = (r.get('record') or {}).get('title') or ''
    return out, titles


def reviewer_facts(k, v, ctx, aff, year):
    """Career facts of key k agreeing with a printed affiliation."""
    why = []
    for a in v['anchors']:
        if a.startswith('aha:'):
            t = a[4:]
            if any(lc_school_agrees(i, aff) for i in ctx['institution'].get(t, ())):
                why.append('AHA directory post')
            if any(lc_school_agrees(s, aff) for s in ctx['students'].get(t, ())):
                why.append("students' school")
        elif a.startswith('aha-phd:') and a[8:] in ctx['records']:
            r = ctx['records'][a[8:]]
            if year and (r['year'] or '').isdigit() and -8 <= year - int(r['year']) <= 3 \
                    and lc_school_agrees(r['department'], aff):
                why.append(f'own AHA dissertation ({r["year"]})')
        elif a.startswith('lcnaf:') and a[6:] in ctx['lc']:
            notes, affs, _ = ctx['lc'][a[6:]]
            posts = [c for n in notes for c in clauses(n) if JOB.search(c) and not DOCTORATE.search(c)] + affs
            if any(lc_school_agrees(aff, p) or lc_school_agrees(p, aff) for p in posts):
                why.append('LC notes post')
        elif a.startswith('orcid:'):
            f = ctx['orcid'].setdefault(a[6:], orcid_facts(a[6:]))
            if any(lc_school_agrees(o, aff) for o in f['emp'] | f['edu']):
                why.append('ORCID affiliation')
    return sorted(set(why))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--lc', type=Path, default=Path('/mnt/e/lc-authorities'))
    args = ap.parse_args()
    state = State.load(args.state)
    db = duckdb.connect()
    reviews = db.execute(f"""SELECT r.source, r.review_id, r.reviewer, r.reviewer_affiliation, r.review_date, r.network,
                                    r.source_url, b.book_id, r.book_title, r.book_author
                             FROM read_parquet('{UP}/export/reviews.parquet') r
                             LEFT JOIN read_parquet('{UP}/books/review_book.parquet') b USING (source, review_id)
                             WHERE r.is_real ORDER BY r.source, r.review_id""").fetchall()
    books = {r[0]: r for r in db.execute(f"SELECT book_id, book_title, book_author, pub_year4, isbn13, lccn "
                                         f"FROM read_parquet('{UP}/books/books.parquet')").fetchall()}
    lccn, lc_title = lc_book_lccn([args.lc / 'books-2016.ndjson', args.lc / 'books.ndjson'])
    report = Counter()
    clusters, claims = [], []
    unlinked = unlinked_reviews(reviews, {b for b, r in books.items() if r[4] or r[5]})
    report['reviews_book_link_not_kept'] = len(unlinked)
    linked = [r for r in reviews if (r[0], r[1]) not in unlinked]

    # books: H-Net book ids sharing an LCCN are one work
    groups = defaultdict(set)              # by the work key the LCCN reaches (LC duplicate works were merged)
    for bk in {r[7] for r in linked if r[7]}:
        ks = state.lookup(f'lccn:{lccn[bk]}') if bk in lccn else []
        groups[ks[0] if len(ks) == 1 else f'lccn:{lccn[bk]}' if bk in lccn else f'hnet-book:{bk}'].add(bk)
    for g, bks in sorted(groups.items()):
        bk = min(bks)
        title, author, year = books[bk][1], books[bk][2], books[bk][3]
        if norm(title) == 'reviews in history':          # a parsing failure; LC's title, or the ISBN
            title = lc_title.get(bk) or f'ISBN {books[bk][4]}'
            author = author if author and norm(author) != 'reviews in history' else ''
        lccns = {f'lccn:{lccn[b]}' for b in bks if b in lccn}
        clusters.append(dict(type='work', label=f'{title} / {author}' if author else title,
                             anchors={f'hnet-book:{b}' for b in bks} | lccns,
                             members={f'year:{year}'} if (year or '')[:4].isdigit() else set(), aliases=set(),
                             resolution='established' if lccns else 'recorded',
                             basis='a book reviewed by H-Net or Reviews in History'
                                   + (f', LC record {", ".join(sorted(x[5:] for x in lccns))}' if lccns else '')))
        report['books_lccn' if lccns else 'books_hnet_only'] += 1

    # book authors by LC's record of the same book
    authored = {(s[0], o[0]) for _, s, _, o in state.relations('authored') if len(s) == 1 and len(o) == 1}
    seen = set()
    with CREDITS.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if not r['lcnaf'] or r['book_id'] not in {b for bs in groups.values() for b in bs} or (r['book_id'], r['lcnaf']) in seen:
                continue
            seen.add((r['book_id'], r['lcnaf']))
            person = state.lookup(f'lcnaf:{r["lcnaf"]}')
            work = state.lookup(f'lccn:{lccn[r["book_id"]]}') if r['book_id'] in lccn else []
            if not person:
                report['book_author_lc_not_keyed'] += 1
                continue
            if work and (person[0], work[0]) in authored:
                report['book_author_already_in_log'] += 1
                continue
            claims.append(dict(anchor=f'hnet-authored:{r["book_id"]}:{r["lcnaf"]}', subject=f'lcnaf:{r["lcnaf"]}',
                               predicate='authored', object=f'hnet-book:{r["book_id"]}'))
            report['book_author_claims'] += 1

    # reviewers
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = {r['id']: r for r in csv.DictReader(f)}
    students = defaultdict(set)
    for r in records.values():
        for t in (r['advisor_ids'] or '').split(';'):
            if t.strip():
                students[t.strip()].add(r['department'])
    institution = defaultdict(set)
    with DIRECTORY.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['institution']:
                institution[r['token']].add(r['institution'])
    live = {k: v for k, v in state.keys.items() if v['type'] == 'person' and v['status'] in ('active', 'provisional')}
    index = by_letter([(v['label'], k) for k, v in live.items()])
    printed = defaultdict(list)                      # (name, affiliation or review) -> reviews
    first = {}
    for r in reviews:
        if not (r[2] or '').strip():
            report['reviews_without_reviewer'] += 1
            continue
        who = (r[2].strip(), (r[3] or '').strip())
        who = who if who[1] else (who[0], f'{SOURCE[r[0]]}:{r[1]}')
        own = f'review-credit:{who[1]}' if is_ref(who[1]) else f'review-credit:{norm(who[0])}|{norm(who[1])}'
        first.setdefault(own, who)                   # spellings that normalise alike are one credit
        printed[first[own]].append(r)
    cands = {}
    for (name, aff), rs in printed.items():
        for n, a in readings(name, aff):
            cs = {k for c in letters(n, first_only=True) for _, k in index.get((surname(n), c), ()) if name_agrees(n, live[k]['label'])}
            if cs and a:
                cands.setdefault((name, aff), []).append((a, cs))
    lc = lc_records({a[6:] for v in cands.values() for _, cs in v for k in cs for a in live[k]['anchors'] if a.startswith('lcnaf:')}, args.lc)
    ctx = dict(records=records, students=students, institution=institution, lc=lc, orcid={})
    credits, listed, joins_csv, relabels = [], [], [], []
    merge_ok = guarded(state, merge_rule(state), exclude=args.out)
    for (name, aff), rs in sorted(printed.items()):
        own = f'review-credit:{aff}' if is_ref(aff) else f'review-credit:{norm(name)}|{norm(aff)}'
        year = min((y for y in (year_of(r[4]) for r in rs) if y), default=None)
        hits = {}
        for a, cs in cands.get((name, aff), ()):
            for k in cs:
                why = reviewer_facts(k, live[k], ctx, a, year)
                if why:
                    hits[k] = sorted(set(hits.get(k, [])) | set(why))
        if len(hits) == 1 or (len(hits) > 1 and merge_ok(dict(anchors=set()), sorted(hits))):
            credits.append((own, name, aff, hits))
            report['reviewer_credits_joined' if len(hits) == 1 else 'reviewer_credits_join_several_keys'] += 1
        else:
            if len(hits) > 1:
                report['reviewer_credits_several'] += 1
                listed.append(dict(name=name, affiliation=aff, reviews=len(rs), outcome='several',
                                   candidates={k: dict(label=live[k]['label'], facts=w) for k, w in hits.items()}))
            else:
                report['reviewer_credits_new'] += 1
            label = readings(name, aff)[0][0] or name
            clusters.append(dict(type='person', label=label, anchors={own}, members=set(), aliases=set(),
                                 resolution='recorded', basis=f'reviewer credit: {name}' + ('' if is_ref(aff) else f', {aff}')))
            for k in state.lookup(own):                 # keys minted before honorifics were read
                if live.get(k) and live[k]['label'] != label and all(x.startswith('review-credit:') for x in live[k]['anchors']):
                    relabels.append(dict(event='relabel', key=k, label=label, basis='the printed name without its honorific'))
        for r in rs:
            claims.append(dict(anchor=f'review-authored:{SOURCE[r[0]]}:{r[1]}', subject=own, predicate='authored',
                               object=f'{SOURCE[r[0]]}:{r[1]}'))
    # Several keys passing for one credit, each on its own career fact at the printed institution, are one person
    # (as in key_aha_career: Gauvreau). Credits are grouped by connected keys: plan holds several clusters on one key.
    parent = {}

    def root(k):
        while parent.get(k, k) != k:
            k = parent[k]
        return k
    num = lambda k: int(k[2:])                                    # noqa: E731
    pure = lambda k: all(x.startswith('review-credit:') for x in live[k]['anchors'])   # noqa: E731
    owners = {c[0]: [k for k in state.lookup(c[0]) if k in live] for c in credits}
    for own, _, _, hits in credits:            # the key already holding a credit belongs to its group too
        ks = sorted(set(hits) | set(owners[own]), key=num)
        for k in ks[1:]:
            parent[root(k)] = root(ks[0])
    groups = defaultdict(list)
    for c in credits:
        groups[root(next(iter(c[3])))].append(c)
    for g, cs in sorted(groups.items()):
        held_by = sorted({k for c in cs for k in owners[c[0]]}, key=num)
        keys = sorted({k for c in cs for k in c[3]} | {k for k in held_by if not pure(k)}, key=num)
        target = live[keys[0]]['label']
        stale = [k for k in held_by if pure(k) and not merge_ok(dict(anchors=set()), sorted({k, keys[0]}))]
        if stale and all(live[k]['label'] == target for k in stale):   # refused for another reason (merge guard)
            report['reviewer_groups_refused'] += 1
            listed += [dict(name=n, affiliation=a, outcome='group_refused', held_by=stale,
                            candidates={k: dict(label=live[k]['label'], facts=w) for k, w in h.items()}) for _, n, a, h in cs]
            continue
        stale = [k for k in stale if live[k]['label'] != target]
        if stale:      # a reviewer key whose printed label the merge rule cannot read: relabel now, join next run
            report['reviewer_groups_deferred_for_relabel'] += 1
            relabels += [dict(event='relabel', key=k, label=target, basis='the name of the person the credit joins '
                                                                         '(honorific or affiliation words in the printed name)')
                         for k in stale]
            continue
        if len(keys) > 1 and not merge_ok(dict(anchors=set()), keys):    # joined pairwise, refused as a whole
            report['reviewer_groups_refused'] += 1
            for own, name, aff, hits in cs:
                clusters.append(dict(type='person', label=name, anchors={own}, members=set(), aliases=set(),
                                     resolution='recorded', basis=f'reviewer credit: {name}, {aff}'))
                listed.append(dict(name=name, affiliation=aff, outcome='group_refused',
                                   candidates={k: dict(label=live[k]['label'], facts=w) for k, w in hits.items()}))
            continue
        for own, name, aff, hits in cs:
            for k, why in hits.items():
                joins_csv.append([k, live[k]['label'], name, aff, '; '.join(why)])
        clusters.append(dict(type='person', label=live[keys[0]]['label'],
                             anchors={sorted(live[k]['anchors'])[0] for k in keys} | {c[0] for c in cs},  # pure keys join by their credit
                             members=set(), aliases=set(), resolution=live[keys[0]]['resolution'],
                             basis='; '.join(f'reviewer {n} ({a}): ' + ' / '.join(f'{k} {", ".join(w)}' for k, w in h.items())
                                             for _, n, a, h in cs)[:500]))

    # reviews
    for r in reviews:
        if not r[7]:
            report['reviews_without_book'] += 1
        anchor = f'{SOURCE[r[0]]}:{r[1]}'
        network = r[5] if r[0] == 'hnet' else 'Reviews in History'
        clusters.append(dict(type='work', label=f'Review of {r[8] or "?"}' + (f' ({network}, {r[4]})' if r[4] else f' ({network})'),
                             anchors={anchor}, members={f'year:{year_of(r[4])}'} if year_of(r[4]) else set(),
                             aliases={f'url:{r[6]}'} if r[6] else set(), resolution='established',
                             basis=f'review published by {network}'))
        if r[7] and (r[0], r[1]) not in unlinked:
            claims.append(dict(anchor=f'reviews:{anchor}', subject=anchor, predicate='reviews', object=f'hnet-book:{r[7]}'))
        report['reviews'] += 1

    ops, assign, held = plan(state, clusters, guarded(state, merge_rule(state), exclude=args.out))
    ops += relabels
    for o in [o for o in ops if o['event'] == 'merge']:     # an AHA-only survivor takes the PID key's fuller name
        into, gone = state.keys[o['into']], state.keys[o['key']]
        if not any(a.split(':', 1)[0] in PUBLIC_SCHEMES for a in into['anchors']) and len(gone['label']) > len(into['label']) \
                and any(a.split(':', 1)[0] in PUBLIC_SCHEMES for a in gone['anchors']):   # never a printed credit
            ops.append(dict(event='relabel', key=o['into'], label=gone['label'], basis='the name on the PID key it joined'))
    have = set(state.anchor)
    for i, c in enumerate(claims):
        if c['anchor'] in have:
            continue
        ops.append(dict(event='mint', key=f'new:claim-{i}', type='claim', label='', resolution='recorded',
                        anchors=[c['anchor']], relation=dict(subject=c['subject'], predicate=c['predicate'], object=c['object'])))
    report['claims'] = len(claims)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'candidates.json').write_text(json.dumps(listed, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    with (args.out / 'reviewer-joins.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['key', 'label', 'reviewer', 'affiliation', 'facts'])
        w.writerows(joins_csv)
    materialise(state, dict(basis='reviews', ops=ops), 'dry-run', 'dry-run')
    import gzip
    with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(dict(basis='Book reviews (H-Net, Reviews in History): review works, reviewed books, reviewers and '
                             'book authors', decided_by='build', ops=ops), f, ensure_ascii=False, default=sorted)
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
