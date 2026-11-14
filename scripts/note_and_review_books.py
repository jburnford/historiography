"""Books named only in LC authority notes, and reviews that name a book with no REVIEWS edge (2026-11-14; ARCHITECTURE.md
section 8, classes 40 and 41). Linked evidence for the build; never writes the key log.

Probe: Valerie Deacon (p-37340). Her book *The Extreme Right in the French Resistance* (LSU Press, 2016) is not in the
LC 2016 file and LC's SRU server refuses connections, so no catalogue record can make the node. Her LC authority's 670
("Her The extreme Right in the French Resistance, 2016:") names it, and three reviews in the graph print 'Valerie
Deacon, The Extreme Right in the French Resistance ...' with no REVIEWS edge.

B1, note books (two-layer rule: an unkeyed work node with the note as provenance, credited as linked evidence; a later
LC catalogue or Crossref record of the same title replaces it):
- authorities: every `lcnaf:` anchored on a live person key, and the strict ties of key_lc_authority_notes.py (not
  applied: link `proposed`, credit state linked);
- a 670 source read as the person's own work ('His/Her/Their <title>, <year>:' or 'Family, Given. <title>, <year>:'
  with the authority's family; key_lc_authority_notes.parse_source); bare and other-author citations are counted, not
  loaded (their role is not stated); a citation whose source or data names a thesis, dissertation or degree is not a
  book; one whose data names the person as editor, translator, compiler or illustrator is counted, not loaded;
- dropped when any work credited to the person (key-log or linked, any kind) has the same main title
  (lc_canon_people.titles_agree), or when a graph book with the same folded main title and a year within two exists
  (counted as `book-node-exists`, left for the works linkers);
- written to data/graph/lc-note-books.csv.gz: work (`lcnote:<lcnaf>:<n>`), title, year, person, lcnaf, link, note.
  The build makes kind-book nodes and a linked AUTHORED credit (source `lc-authority-note`, state exact for an anchored
  authority, linked for a proposed one).

B2, review ties: review records (kind review, or kind_proposed review) with no REVIEWS edge whose label reads as
'Author, Title' / 'Author: Title' / 'Family, Given. Title' / 'Title. By Author' (review_label_parse.py). A tie when one
reading's printed author agrees in full with exactly one live person key (propose_person_dup_merges.names_agree: never
a nickname, never initials alone) and the printed main title agrees with a title credited to that key (book, thesis,
other or edited work; any evidence) or with one of its note books, the review dated 0-8 years after the book (one year
before tolerated), or the label prints the book's ISBN. Two books for one review: held. Written to
data/graph/review-titled-books.csv.gz in the review-books format (rule `titled`); the build adds REVIEWS evidence
linked, source `review-books:titled`. Books from reviews alone (two or more reviews in different venues naming the same
author and main title, no book node) are counted and listed, not created.

    python3 scripts/note_and_review_books.py      # after key_lc_authority_notes.py; reads build/graph
"""
import csv
import gzip
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from key_lc_authority_notes import parse_source, toks  # noqa: E402
from lc_canon_people import titles_agree  # noqa: E402
from link_cited_work_authors import forms  # noqa: E402
from propose_person_dup_merges import names_agree  # noqa: E402
from review_books import fold, main_title as rb_main  # noqa: E402
from review_label_parse import parse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'build/graph'
NOTES = Path('/mnt/e/lc-authorities/personal-notes.parquet')
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
A_DIR = ROOT / 'data/identifiers/lc-authority-notes-2026-11-14'
OUT = ROOT / 'data/identifiers/note-review-books-2026-11-14'
NOTE_BOOKS = ROOT / 'data/graph/lc-note-books.csv.gz'
REVIEW_TIES = ROOT / 'data/graph/review-titled-books.csv.gz'
THESIS = re.compile(r'\bthes[ie]s\b|dissertation|\bph\.?\s?d\b|\bm\.?\s?a\.?\b thesis|doctoral|tesis|th[eè]se|doktorarbeit', re.I)
MARKER = r"(?i)^\s*(review of|book review|rezension|compte[- ]rendu|rese[ñn]a|recensione|resenha)|\((book )?review\)|\[(book )?review\]"
NOT_AUTHOR = re.compile(r'\b(?:eds?\.|editors?|edited|compil|translat|trans\.|tr\.|trad\.|hrsg|hg\.|illustrat|photograph|'
                        r'introd|foreword|preface|pr[eé]face|selected by|interviewed)', re.I)


def fold_main(t):
    return rb_main(t)


def main():
    c = duckdb.connect()
    c.execute("SET memory_limit='5GB'; SET threads=4")
    q = lambda s, *a: c.execute(s, *a).fetchall()
    rep = Counter()
    people = {k: (l or '', lc) for k, l, lc in q(f"SELECT key, label, lcnaf FROM '{G}/person.parquet'")}
    auths = {lc: (k, 'anchor') for k, (l, lc) in people.items() if lc}
    proposed = {}
    with gzip.open(A_DIR / 'ties.csv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['decision'] == 'strict':
                proposed[r['lcnaf']] = r['person']
    for lc, k in proposed.items():
        auths.setdefault(lc, (k, 'proposed'))
    c.execute('CREATE OR REPLACE TABLE al AS SELECT unnest(?) lcid', [sorted(auths)])
    notes = q(f"SELECT n.lcid, n.notes, a.label FROM '{NOTES}' n JOIN '{NAMES}' a ON a.lcid = n.lcid WHERE n.lcid IN (SELECT lcid FROM al)")
    credited = defaultdict(list)                  # person -> (title, year, kind)
    for k, t, y, kind in q(f"""SELECT x."from", w.label, w.year, w.kind FROM (
            SELECT "from", "to" FROM '{G}/authored.parquet' UNION SELECT "from", "to" FROM '{G}/edited.parquet'
            UNION SELECT "from", "to" FROM '{G}/linked_authored.parquet' UNION SELECT "from", "to" FROM '{G}/linked_edited.parquet') x
            JOIN '{G}/work.parquet' w ON w.key = x."to" WHERE w.label IS NOT NULL AND w.kind <> 'review'"""):
        credited[k].append((t, y, kind))
    books_by_title = defaultdict(list)            # folded main title -> (key, year)
    for k, t, y in q(f"SELECT key, label, coalesce(first_year, year) FROM '{G}/work.parquet' WHERE kind = 'book' AND label IS NOT NULL"):
        m = fold_main(t)
        if len(m.split()) >= 2:
            books_by_title[m].append((k, y))
    # keys with scholarly evidence (as lc_catalogue_credits.py): a thesis or AHA anchor, a key-log thesis, a directory
    # anchor, supervision, a review; the anchored population also holds primary-source people (composers, politicians)
    scholarly = {k for (k,) in q(f"""SELECT key FROM '{G}/person.parquet' WHERE len(list_filter(anchors, a -> a LIKE 'aha-phd:%'
            OR a LIKE 'diss-author:%' OR a LIKE 'capes-person:%' OR a LIKE 'ihr:%' OR a LIKE 'aha:%' OR a LIKE 'repo-advisor:%'
            OR a LIKE 'review-credit%')) > 0
            OR key IN (SELECT "from" FROM '{G}/supervised.parquet')
            OR key IN (SELECT a."from" FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
                       WHERE a.evidence = 'keylog' AND w.kind IN ('review', 'thesis'))""")}
    theses = defaultdict(list)                    # person -> (thesis title, year): AHA records and key-log theses
    aha = {}
    for line in open(ROOT / 'data/field-research/aha-dissertations-2026-10-13/records.jsonl', encoding='utf-8'):
        r = json.loads(line)
        if r.get('title') and r.get('year'):
            aha['aha-phd:' + r['id']] = (r['title'], int(r['year']))
    for k, an in q(f"SELECT key, anchors FROM '{G}/person.parquet'"):
        for a in an or []:
            if a in aha:
                theses[k].append(aha[a])
    for k, xs in credited.items():
        theses[k] += [(t, y) for t, y, kind in xs if kind == 'thesis']

    def thesis_like(tt, title):
        # only asked of a note dated within a year of the person's own PhD: two shared words carrying 60% of the note
        # title's weight ('East Prussian and Sudetan German expelles in West Germany' is the 1989 thesis)
        # unweighted: LC's misspellings ('Sudetan', 'expelles') would carry the highest rarity weight
        a, b = toks(tt), toks(title)
        return len(a & b) >= 2 and len(a & b) / max(1, len(b)) >= 0.6
    print('facts loaded', len(notes), 'authorities with notes', flush=True)

    # ---------------------------------------------------------------- B1
    nb_rows, nb_measure = [], []
    for lcid, ns, label in notes:
        k, link = auths[lcid]
        fam = next((f for f, _, _ in forms(label)), '')
        giv = {w for _, _, g in forms(label) for w in g}
        seen = set()
        for i, raw in enumerate(ns or []):
            src, _, data = raw.partition(' :: ')
            p = parse_source(src, fam, giv)
            if not p:
                continue
            form, title, year = p
            rep[f'b1_note_citations|{form}'] += 1
            if THESIS.search(src) or THESIS.search(data):
                rep['b1_thesis_notes'] += 1
                continue
            # NUC reports ('nuc87-52716: His ... [MI] 1974') are mostly microfilmed dissertations with cut titles;
            # recordings, scores, microforms and visual material are not books; a cut title ('...') or a year not set off
            # by a comma ('Music in Texas--frontier to 1900:') cannot name a book
            if re.match(r'(?i)nuc', src) or re.search(r'\[(?:SR|MI|VM|MU|GR|SCORE)\]', src) or '...' in src or \
                    not re.search(r'(?<![-\d])\d{4}-?\d{0,4}\s*[:.]?\s*$', src) or \
                    not re.search(r',\s*\[?(?:c|p|©)?\s*\d{4}\??\]?\s*[:.]?\s*$', src) or \
                    re.search(r'\d{4}-\d{2,4}\s*[:.]?\s*$', src):
                rep['b1_not_a_book_record'] += 1
                continue
            m = fold_main(title)
            if m in seen or len(m.split()) < 2:
                continue
            seen.add(m)
            # the person's own thesis (an AHA record or a key-log thesis): the same title, or the rare words of the
            # title, in the PhD year +-1 (LC made many authorities from the dissertation)
            if any(abs(year - ty) <= 1 and (titles_agree(title, tt) or fold_main(tt) == m or thesis_like(tt, title))
                   for tt, ty in theses.get(k, ()) if ty):
                rep['b1_the_persons_thesis'] += 1
                continue
            if any(titles_agree(title, t) or fold_main(t) == m for t, _, _ in credited.get(k, ())):
                rep[f'b1_already_credited|{form}'] += 1
                continue
            if any(y is None or abs(y - year) <= 2 for _, y in books_by_title.get(m, ())):
                rep[f'b1_book_node_exists_uncredited|{form}'] += 1
                continue
            if re.search(r'\bPDF\b|\bM\.\s?A\. degree|\bmaster|\bvita\b|\bleaf\b|\bleaves\b|\bp(?:age|\.) i{1,3}v?\b|'
                         r'\b(?:Spring|Fall|Summer|Winter|May|August|December) \d{4}\)', data):    # an electronic thesis ('PDF title page')
                rep['b1_thesis_notes'] += 1
                continue
            title = re.sub(r'(?:,\s*\d{4})+$', '', title).strip(' ,')    # 'In the shadow of the sword, 1988, c1987'
            role = 'not-author' if NOT_AUTHOR.search(data) else 'author'
            sch = k in scholarly
            rep[f"b1_missing|{form}|{role}|{link}|{'scholarly' if sch else 'other-key'}"] += 1
            nb_measure.append(dict(person=k, lcnaf=lcid, form=form, role=role, link=link, title=title, year=year,
                                   scholarly=sch))
            if form in ('own', 'own-name') and role == 'author' and sch:
                nb_rows.append(dict(work=f'lcnote:{lcid}:{i}', title=title, year=year, person=k, lcnaf=lcid, link=link,
                                    abbreviated=bool(re.search(r'\b[a-z]{2,6}\.(?=\s|,|$)', title)), note=raw[:300]))
    rep['b1_loaded_books'] = len(nb_rows)
    rep['b1_loaded_people'] = len({r['person'] for r in nb_rows})
    rep['b1_loaded_by_link'] = dict(Counter(r['link'] for r in nb_rows))
    rep['b1_loaded_abbreviated_titles'] = sum(1 for r in nb_rows if r['abbreviated'])
    OUT.mkdir(parents=True, exist_ok=True)
    import hashlib
    nbs = sorted(nb_rows, key=lambda r: hashlib.md5(r['work'].encode()).hexdigest())[:60]    # stable across reruns
    sp = OUT / 'note-books-sample-checked.csv'
    old = {}
    if sp.exists():
        with open(sp, encoding='utf-8') as f:
            old = {r['work']: (r['verdict'], r['note_by_hand']) for r in csv.DictReader(f)}
    with open(sp, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work', 'person', 'person_label', 'link', 'year', 'title', 'note', 'verdict', 'note_by_hand'])
        for r in nbs:
            w.writerow([r['work'], r['person'], people[r['person']][0], r['link'], r['year'], r['title'], r['note'][:200],
                        *old.get(r['work'], ('', ''))])
    with gzip.open(NOTE_BOOKS, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['work', 'title', 'year', 'person', 'lcnaf', 'link', 'abbreviated', 'note'])
        w.writeheader()
        w.writerows(sorted(nb_rows, key=lambda r: r['work']))
    print('B1', len(nb_rows), 'note books loaded', flush=True)

    # ---------------------------------------------------------------- B2
    nb_of = defaultdict(list)
    for r in nb_rows:
        nb_of[r['person']].append((r['title'], r['year'], 'book', r['work']))
    work_of = defaultdict(list)                   # person -> (title, year, kind, key) of credited works
    for k, t, y, kind, key, isbn in q(f"""SELECT x."from", w.label, coalesce(w.first_year, w.year), w.kind, w.key, w.isbn FROM (
            SELECT "from", "to" FROM '{G}/authored.parquet' UNION SELECT "from", "to" FROM '{G}/edited.parquet'
            UNION SELECT "from", "to" FROM '{G}/linked_authored.parquet' UNION SELECT "from", "to" FROM '{G}/linked_edited.parquet') x
            JOIN '{G}/work.parquet' w ON w.key = x."to" WHERE w.label IS NOT NULL AND w.kind IN ('book', 'thesis', 'other')"""):
        work_of[k].append((t, y, kind, key, isbn))
    for k, xs in nb_of.items():
        for t, y, kind, key in xs:
            work_of[k].append((t, y, 'note-book', key, None))
    isbn_book = {}
    for key, isbn in q(f"SELECT key, isbn FROM '{G}/work.parquet' WHERE isbn IS NOT NULL AND kind = 'book'"):
        for x in re.split(r'[;, ]+', isbn):
            x = re.sub(r'[^0-9Xx]', '', x).upper()
            if len(x) in (10, 13):
                isbn_book.setdefault(x, set()).add(key)
    pidx = defaultdict(list)
    given_names = Counter(w for l, _ in people.values() for _, _, g in forms(l)[:1] for w in g[:1] if len(w) > 1)
    given_names = {w for w, n in given_names.items() if n >= 2}
    for k, (l, _) in people.items():
        for f, _, g in forms(l):
            if g and not all(len(x) == 1 for x in g):
                pidx[f].append(k)
    revs = q(f"""SELECT w.key, w.label, w.year, w.kind, w.journal, w.resolution FROM '{G}/work.parquet' w
                 WHERE w.label IS NOT NULL AND w.key NOT IN (SELECT "from" FROM '{G}/reviews.parquet')
                 AND (w.kind = 'review' OR w.kind_proposed = 'review'
                      OR (w.kind IN ('article', 'other') AND regexp_matches(w.label, '{MARKER}')))""")
    rep['b2_population'] = len(revs)
    credited_on = defaultdict(set)                # review -> people credited on it (any evidence): never the reviewed author
    c.execute('CREATE OR REPLACE TABLE rv AS SELECT unnest(?) AS key', [[r[0] for r in revs]])
    for k, w_ in q(f"""SELECT "from", "to" FROM '{G}/authored.parquet' WHERE "to" IN (SELECT key FROM rv)
                      UNION SELECT "from", "to" FROM '{G}/linked_authored.parquet' WHERE "to" IN (SELECT key FROM rv)"""):
        credited_on[w_].add(k)
    rep['b2_review_kind_total'] = q(f"SELECT count(*) FROM '{G}/work.parquet' WHERE kind = 'review'")[0][0]
    rep['b2_review_kind_without_REVIEWS'] = sum(1 for r in revs if r[3] == 'review')
    rep['b2_kind_proposed_review_without_REVIEWS'] = q(f"""SELECT count(*) FROM '{G}/work.parquet' WHERE kind <> 'review'
        AND kind_proposed = 'review' AND key NOT IN (SELECT "from" FROM '{G}/reviews.parquet')""")[0][0]
    ties, held, groups = [], [], defaultdict(list)
    for key, label, ryear, kind, journal, res in revs:
        p = parse(label)
        if not p:
            rep['b2_not_parsed'] += 1
            continue
        rep['b2_parsed' if p['reads'] else 'b2_isbn_only'] += 1
        if p['isbns']:
            rep['b2_with_isbn'] += 1
        hits = {}
        for x in p['isbns']:
            for b in isbn_book.get(x, ()):
                hits[b] = ('isbn', x, '')
        for rd in p['reads']:
            m = fold_main(rd['title'])
            if len(m.split()) < 2 or len(m) < 10:
                continue
            groups[(fold(rd['names'][0]), m)].append((key, journal, ryear, bool(p['isbns']), rd['title'], rd['names'][0]))
            for nm in rd['names']:
                cands = {k for f, _, _ in forms(nm) for k in pidx.get(f, ()) if names_agree(people[k][0], nm)}
                if not cands:
                    continue
                rep[f"b2_reading_name_on_keys|{'one' if len(cands) == 1 else 'several'}"] += 1
                if cands & credited_on.get(key, set()):
                    rep['b2_reviewed_author_credited_on_the_review'] += 1
                    continue
                for k in cands:
                    for t, by, bkind, bkey, _ in work_of.get(k, ()):
                        if not (titles_agree(rd['title'], t) or fold_main(t) == m):
                            continue
                        if by and ryear and not (by - 1 <= ryear <= by + 8):
                            rep['b2_title_fits_date_does_not'] += 1
                            continue
                        hits.setdefault(bkey, ('titled', f'{nm} | {t[:80]}', k if len(cands) == 1 else 'several:' + k))
        hits = {b: v for b, v in hits.items() if not v[2].startswith('several')}
        if not hits:
            continue
        if len(hits) > 1:
            # a book and its note-book twin, or two keyed editions: keep a graph book over a note book; else held
            real = {b: v for b, v in hits.items() if not b.startswith('lcnote:')}
            hits = real if len(real) == 1 else hits
        if len(hits) > 1:
            held.append(dict(review=key, label=label[:200], books=' '.join(sorted(hits))))
            continue
        (b, (how, basis, k)), = hits.items()
        ties.append(dict(review=key, book=b, rule='titled', basis=f'{how}:{basis}', review_kind=kind, review_resolution=res,
                         book_title='', book_year='', book_lccn='', lc_main_lcnaf='', book_families='', person=k,
                         label=label[:300], to_note_book=b.startswith('lcnote:')))
    rep['b2_ties'] = len(ties)
    rep['b2_ties_by'] = dict(Counter(('note-book' if t['to_note_book'] else 'graph-book') + '|' + t['basis'].split(':', 1)[0]
                                     for t in ties))
    rep['b2_held_two_books'] = len(held)
    cols = ['review', 'book', 'rule', 'basis', 'review_kind', 'review_resolution', 'book_title', 'book_year', 'book_lccn',
            'lc_main_lcnaf', 'book_families']
    with gzip.open(REVIEW_TIES, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(sorted(ties, key=lambda r: r['review']))
    # books from reviews alone: 2+ reviews, different venues, same author + main title, no graph book of that title
    tied = {t['review'] for t in ties}
    # grouped by main title (a label read two ways counts once); the same printed author on two reviews; 3+ title words
    by_title = defaultdict(list)
    for (nm, m), rs in groups.items():
        by_title[m] += [(nm,) + r for r in rs if r[0] not in tied]
    rb = []
    for m, rs in by_title.items():
        if len(m.split()) < 3 or m in books_by_title:
            continue
        revs_by_name = defaultdict(set)
        for r in rs:
            g = next((w for _, _, gg in forms(r[6]) for w in gg if len(w) > 1), None)
            if g in given_names:            # 'Aboriginal Victorians: A History' is a title, not 'Victorians, Aboriginal'
                revs_by_name[r[0]].add(r[1])
        if not revs_by_name:
            continue
        nm, keys_ = max(revs_by_name.items(), key=lambda x: len(x[1]))
        rs = [r for r in rs if r[0] == nm]
        venues = {r[2] or r[1] for r in rs}
        if len(keys_) >= 2 and len(venues) >= 2:
            rb.append(dict(author=rs[0][6], title=rs[0][5][:200], reviews=len(keys_), venues=len(venues),
                           isbn=any(r[4] for r in rs), first_review=min((r[3] for r in rs if r[3]), default='')))
    rep['b2_books_from_reviews_alone'] = len(rb)
    rep['b2_books_from_reviews_alone_with_isbn'] = sum(1 for r in rb if r['isbn'])
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / 'books-from-reviews.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['author', 'title', 'reviews', 'venues', 'isbn', 'first_review'])
        w.writeheader()
        w.writerows(sorted(rb, key=lambda r: (-r['reviews'], r['author'])))
    with gzip.open(OUT / 'note-books-measure.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['person', 'lcnaf', 'form', 'role', 'link', 'title', 'year', 'scholarly'])
        w.writeheader()
        w.writerows(nb_measure)
    with gzip.open(OUT / 'review-ties.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(ties[0].keys()))
        w.writeheader()
        w.writerows(ties)
    with gzip.open(OUT / 'review-held.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['review', 'label', 'books'])
        w.writeheader()
        w.writerows(held)
    # hand-check samples (verdict filled by hand)
    rnd = random.Random(1114)
    titles = {k: t for k, t in q(f"SELECT key, label FROM '{G}/work.parquet' WHERE key IN (SELECT unnest(?))", [[t['book'] for t in ties]])}
    for r in nb_rows:
        titles[r['work']] = r['title']
    strata = defaultdict(list)
    for t in ties:
        strata[('note' if t['to_note_book'] else 'graph') + '|' + t['basis'].split(':', 1)[0]].append(t)
    sample = []
    for s_ in sorted(strata):
        sample += rnd.sample(strata[s_], min(25, len(strata[s_])))
    sp = OUT / 'review-sample-checked.csv'
    old = {}
    if sp.exists():
        with open(sp, encoding='utf-8') as f:
            old = {r['review']: (r['verdict'], r['note_by_hand']) for r in csv.DictReader(f)}
    with open(sp, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['stratum', 'review', 'review_label', 'book', 'book_title', 'person', 'person_label', 'basis', 'verdict', 'note_by_hand'])
        for t in sample:
            v = old.get(t['review'], ('', ''))
            w.writerow([('note' if t['to_note_book'] else 'graph') + '|' + t['basis'].split(':', 1)[0], t['review'], t['label'][:200],
                        t['book'], (titles.get(t['book']) or '')[:150], t['person'], people.get(t['person'], ('',))[0], t['basis'][:150], *v])
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, default=str) + '\n')
    print(json.dumps(rep, indent=1, default=str))
    for t in ties:
        if t['person'] == 'p-37340':
            print('PROBE', t['review'], t['book'], t['basis'])
    for r in nb_rows:
        if r['person'] == 'p-37340':
            print('PROBE-BOOK', r)


if __name__ == '__main__':
    main()
