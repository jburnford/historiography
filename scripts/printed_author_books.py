"""Catalogue and review books whose label prints the author, with no author credit; and the same book held twice
(ARCHITECTURE.md section 8, class 46; 2026-11-15).

Probe (owner, 2026-11-15): w-441327 'The Toxic Ship ... / Simone M. Müller' (an H-Net reviewed book with an LCCN) had
no AUTHORED row and no candidate although p-23621 'Simone M Müller' is keyed, and her ORCID record had already made
the same book a second node (w-1018969 'The Toxic Ship. The Voyage ...').

Causes (see report.json, README.md):
  A  scripts/key_reviews.py credits an H-Net book's author only through LC's record of the same book resolved to an LC
     authority (credits.csv, column lcnaf; the loop skips every other outcome: no_lc_record, lc_record_not_same_book,
     new_for_unresolved_credit, ...). No other linker reads the printed name: link_work_people.nameonly_targets takes
     only works with a doi:/openalex: anchor, positions() reads reviewers, JSTOR authors and OpenAlex authorships, and
     lc_catalogue_credits needs an LC record (the 2016 file and the SRU caches; most recent books have none).
  B  scripts/key_orcid_works.py joins an ORCID work to the claimant's keyed work only when the claimant already holds a
     claim on it (`own`) and the main title before ':' agrees: the uncredited book is not 'own', and an ORCID title
     printed 'Title. Subtitle' reads as one long main title. work_dup_pairs.py (SAME_WORK, class 11 form B) needs one
     person credited on both works and both years present.

Subcommands
  positions  the class's printed names as name-only positions (link_work_people schema) in WP_SCRATCH, plus the twin
             table (B) and its proposals; the linker then runs on WP_SCRATCH:
               WP_SCRATCH=<dir> python3 scripts/link_work_people.py link --nameonly --gold-no-oa --topic-min 20
  finish     reads WP_SCRATCH/results.parquet, adds the twin fact, writes credits.csv.gz, report.json and the samples

Reads build/graph (read-only), the H-Net book table, the key-log cache read-only (dry run). Writes only OUT and scratch.

    WP_SCRATCH=<dir> python3 scripts/printed_author_books.py positions
    WP_SCRATCH=<dir> python3 scripts/link_work_people.py link --nameonly --gold-no-oa --topic-min 20
    WP_SCRATCH=<dir> python3 scripts/printed_author_books.py finish
"""
import argparse
import csv
import gzip
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from link_cited_work_authors import forms, initial_only  # noqa: E402
from link_work_people import agree_level  # noqa: E402
from work_dup_pairs import fold_title  # noqa: E402

GRAPH = Path(os.environ.get('WP_GRAPH', ROOT / 'build/graph'))
SCRATCH = Path(os.environ.get('WP_SCRATCH', ROOT / 'build/scratch-printed-author-books-2026-11-15'))
OUT = ROOT / 'data/identifiers/printed-author-books-2026-11-15'
HNET_BOOKS = Path('/home/jic823/hnet-reviews/data/books/books.parquet')
HNET_CREDITS = ROOT / 'data/field-research/lc-authorities-2026-10-30/reviews-2026-11-02/credits.csv'
P9_DEFAULT = ROOT / 'build/scratch-2026-11-13/p9data'

EDITOR_TAIL = re.compile(r'(?:,|\s)\s*\(?\b(eds?|editors?|hrsg|hg|hgg|dir|dirs|coords?|comps?)\b\.?\)?\s*$', re.I)
LC_ROLE_LEAD = re.compile(r'^(?:(?:by|von|par|por|di|de|door|av|af)\s+|'
                          r'(?P<ed>(?:edited|ed\.|eds\.|compiled|selected|collected|assembled)(?:\s+and\s+\w+)?\s+by\s+|'
                          r'(?:hrsg\.|herausgegeben|hg\.)\s+von\s+|a\s+cura\s+di\s+|sous\s+la\s+direction\s+de\s+|'
                          r'(?:edición|coordinación|coord\.|dir\.|org\.|organizado|organização)\s+(?:de|por|by)\s+|'
                          r'(?:edited|herausgegeben|hrsg\.?|ed\.)\s+))', re.I)
SKIP_ROLE = re.compile(r'\b(translat|übersetz|traduit|tradu[cz]|trans\.|introduc|einleitung|préface|preface|foreword|'
                       r'afterword|illustrat|photograph|with\s+an?\b|mit\s+einem|avec\s+une?|con\s+una?|map[s]?\s+by)', re.I)
SPLIT = re.compile(r'\s*(?:;|,|&|\band\b|\bund\b|\bet\b|(?-i:\by\b)|(?-i:\be\b)|\bwith\b|\bmit\b)\s*', re.I)
PARTICLES = {'de', 'del', 'della', 'der', 'den', 'des', 'di', 'da', 'do', 'dos', 'das', 'du', 'la', 'le', 'van', 'von',
             'ten', 'ter', 'zu', 'y', 'e', 'al', 'el', 'bin', 'ibn', 'st', 'mac', 'mc'}
SUFFIX_ONLY = re.compile(r'^(jr|sr|ii|iii|iv|phd|md)\.?$', re.I)
EDITION = re.compile(r'\b(\d+(st|nd|rd|th)\s+(ed|edition)|second edition|third edition|revised|rev\. ed|new edition|'
                     r'nouvelle édition|auflage|aufl\.|edición revisada|reprint|abridged|expanded edition|updated edition)\b', re.I)
VOLUME = re.compile(r'\b(vol\.?|volume|volumes|band|bd\.|tome|tomo|teil|part)\s*[0-9ivxlc]+\b', re.I)
SAMPLE_SEED = 20261115


def duck():
    import duckdb
    db = duckdb.connect()
    (SCRATCH / 'tmp').mkdir(parents=True, exist_ok=True)
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET temp_directory='{SCRATCH / 'tmp'}'; SET enable_progress_bar=false")
    return db


def is_name(piece):
    """a printed personal name: two or more words, each capitalised, an initial or a particle; no digits"""
    ws = piece.replace('.', '. ').split()
    if len(ws) < 2 or re.search(r'\d', piece) or len(piece) > 60:
        return False
    for w in ws:
        w0 = w.strip('.,()[]')
        if not w0:
            continue
        if w0.lower() in PARTICLES or w0[0].isupper() or w0[0] in "'’":
            continue
        return False
    return True


def split_names(s):
    """'A B, C D, eds' -> (['A B', 'C D'], 'editor'); role 'author' when no role is printed"""
    s = (s or '').strip().strip('[]').strip()
    role = 'author'
    if EDITOR_TAIL.search(s):
        role = 'editor'
        s = EDITOR_TAIL.sub('', s)
    out = []
    for p in SPLIT.split(s):
        p = p.strip(' .,;:[]()')
        if not p or SUFFIX_ONLY.match(p):
            continue
        if is_name(p):
            out.append(p)
    return out, role


def lc_statement_names(stmt):
    """names of the first clause of an LC statement of responsibility (245 $c): 'edited by A and B ; translated by C'
    -> (['A', 'B'], 'editor'); clauses about translators, introductions, illustrations are not read"""
    first = re.split(r'\s+;\s+|\s+\[and\]\s+|\s*=\s*', stmt or '', 1)[0].strip().strip('[]').strip()
    if SKIP_ROLE.search(first.split(' by ')[0] if ' by ' in first else first[:30]):
        return [], 'skip'
    m = LC_ROLE_LEAD.match(first)
    role = 'author'
    if m:
        role = 'editor' if (m.group('ed') or not re.match(r'(by|von|par|por|di|de|door|av|af)\s', m.group(0), re.I)) else 'author'
        first = first[m.end():]
    if re.search(r'\(eds?\.?\)|\[edit\.\]|\bed(itor)?s?\.?\s*$', first, re.I):
        role = 'editor'
        first = re.sub(r'\(eds?\.?\)|\[edit\.\]', '', first, flags=re.I)
    names, r2 = split_names(first)
    return names, ('editor' if r2 == 'editor' else role)


def fold(t):
    return fold_title(t)


# ---------------------------------------------------------------- positions and twins

def targets(db):
    """the class: catalogue / review books (an hnet-book: or lccn: anchor; kind book, or other with such an anchor) whose
    label prints a statement of responsibility (' / ') and that carry no AUTHORED or EDITED row of any evidence"""
    G = GRAPH
    db.execute(f"""CREATE OR REPLACE TABLE cred AS SELECT DISTINCT "to" w FROM '{G}/authored.parquet'
                   UNION SELECT DISTINCT "to" FROM '{G}/edited.parquet'""")
    db.execute(f"""CREATE OR REPLACE TABLE books AS SELECT key, label, kind, year, resolution, anchors,
                   list_filter(anchors, x -> x LIKE 'hnet-book:%') hb, list_filter(anchors, x -> x LIKE 'lccn:%') lc
            FROM '{G}/work.parquet'
            WHERE (kind = 'book' OR (kind = 'other' AND len(list_filter(anchors, x -> x LIKE 'lccn:%' OR x LIKE 'hnet-book:%')) > 0))
              AND len(list_filter(anchors, x -> x LIKE 'lccn:%' OR x LIKE 'hnet-book:%')) > 0
              AND label LIKE '% / %'""")
    db.execute("CREATE OR REPLACE TABLE tg AS SELECT b.* FROM books b WHERE key NOT IN (SELECT w FROM cred)")


def hnet_authors(db):
    return {b: a for b, a in db.execute(f"SELECT book_id, book_author FROM read_parquet('{HNET_BOOKS}') WHERE book_author IS NOT NULL").fetchall()}


def printed_of(key, label, hb, hauth):
    """(names, role, source) printed on the book: the H-Net catalogue's author field for an H-Net book, else the
    label's statement of responsibility (an LC 245 $c)"""
    for a in sorted(hb or ()):
        s = hauth.get(a.split(':', 1)[1])
        if s:
            names, role = split_names(s)
            return names, role, 'hnet-book'
    stmt = (label or '').split(' / ', 1)[1] if ' / ' in (label or '') else ''
    names, role = lc_statement_names(stmt)
    return names, role, 'lc-statement'


def cmd_positions(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    SCRATCH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    db = duck()
    targets(db)
    R = Counter()
    hauth = hnet_authors(db)
    R['books_with_printed_statement'] = db.execute('SELECT count(*) FROM books').fetchone()[0]
    R['class_books_no_author_or_editor_row'] = db.execute('SELECT count(*) FROM tg').fetchone()[0]
    for res, h, l, n in db.execute("""SELECT resolution, len(hb) > 0, len(lc) > 0, count(*) FROM tg GROUP BY ALL""").fetchall():
        R[f"class_by|{'keyed' if res != 'unkeyed' else 'unkeyed'}|{'hnet' if h else ''}{'+' if h and l else ''}{'lccn' if l else ''}"] += n
    R['class_with_author_candidates'] = db.execute(f"""SELECT count(*) FROM tg WHERE key IN
            (SELECT "to" FROM '{GRAPH}/author_candidates.parquet')""").fetchone()[0]
    # why the H-Net loader left them: the outcome of LC's record for the book's printed credit (credits.csv)
    outcome = defaultdict(set)
    with HNET_CREDITS.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            outcome[r['book_id']].add(r['outcome'] if not r['lcnaf'] else 'lcnaf:' + r['outcome'])
    rows = db.execute("SELECT key, label, kind, year, resolution, anchors, hb, lc FROM tg ORDER BY key").fetchall()
    pos, tg_rows = [], []
    for key, label, kind, year, res, anchors, hb, lc in rows:
        names, role, src = printed_of(key, label, hb, hauth)
        oc = set()
        for a in hb or ():
            oc |= outcome.get(a.split(':', 1)[1], set())
        R[f"class_hnet_lc_outcome|{'+'.join(sorted(oc)) or ('no credit row' if hb else 'not an H-Net book')}"] += 1
        tg_rows.append(dict(work=key, label=label, kind=kind, year=year, resolution=res, source=src, role=role,
                            printed='; '.join(names), n_names=len(names), lc_outcome='+'.join(sorted(oc))))
        if not names:
            R[f'class_no_readable_name|{src}'] += 1
            continue
        R[f'class_books_with_names|{src}|{role}'] += 1
        title = label.split(' / ', 1)[0]
        for i, nm in enumerate(names):
            pos.append(dict(role='author', source=f'printed-{src}', work=key, pos=i, n_auth=len(names), name=nm, year=year,
                            journal='', kind=kind or 'book', title=title[:200], orcid='', oa_author='', rors=[], insts=[],
                            raw_aff=[], oa_work='', inst_printed='', inst_ror='', inst_ror_name='', sig_conf=0.0,
                            credited='', credited_how='', pid=30_000_000 + len(pos), printed_role=role))
    R['positions'] = len(pos)
    schema = pq.read_schema(ROOT / 'build/scratch-2026-11-13/workpeople/positions.parquet')
    pq.write_table(pa.Table.from_pylist([{k: v for k, v in p.items() if k != 'printed_role'} for p in pos], schema=schema),
                   SCRATCH / 'positions.parquet')
    pq.write_table(pa.Table.from_pylist([dict(pid=p['pid'], printed_role=p['printed_role']) for p in pos]), SCRATCH / 'roles.parquet')
    # the linker's other inputs, empty: no OpenAlex references, no identifier credits, no volume people
    (SCRATCH / 'oa-refs.jsonl').write_text('')
    pq.write_table(pa.Table.from_pylist([dict(work='', key='')]), SCRATCH / 'credited-extra.parquet')
    pq.write_table(pa.Table.from_pylist([dict(work='', key='', how='', volume='')]), SCRATCH / 'volume-people.parquet')
    with gzip.open(OUT / 'class-books.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(tg_rows[0]))
        w.writeheader()
        w.writerows(tg_rows)
    twins(db, hauth, R)
    (SCRATCH / 'positions-report.json').write_text(json.dumps(dict(sorted(R.items())), indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(dict(sorted(R.items())), indent=1, ensure_ascii=False))


def kind_ok(k):
    """kinds of the claimed twin that may be the same book: book, edited volume, untyped ('other') or none"""
    return k in (None, '', 'book', 'other')


def twins(db, hauth, R):
    """B: a catalogue / review book whose printed name agrees with a key that holds a key-log credit (authored or edited)
    on another work of the same folded title. Every book with a printed statement is read (credited or not); pairs the
    build already shows as SAME_WORK, or one key, are counted, not proposed."""
    G = GRAPH
    db.create_function('fold_title', fold_title, ['VARCHAR'], 'VARCHAR')
    db.execute("CREATE OR REPLACE TABLE bt AS SELECT key, fold_title(label) t, year, kind, label, hb, resolution, anchors FROM books")
    db.execute("DELETE FROM bt WHERE length(t) < 15 OR len(string_split(t, ' ')) < 3")
    db.execute(f"""CREATE OR REPLACE TABLE kl AS
            SELECT DISTINCT "from" p, "to" w, 'authored' rel FROM '{G}/authored.parquet' WHERE evidence = 'keylog'
            UNION SELECT DISTINCT "from", "to", 'edited' FROM '{G}/edited.parquet' WHERE evidence = 'keylog'""")
    # candidate works: titles that a book bears (prefilter in SQL on a cheap fold, then fold_title exactly)
    db.execute("""CREATE OR REPLACE TABLE bcheap AS SELECT DISTINCT regexp_replace(lower(strip_accents(split_part(label, ' / ', 1))),
                  '[^a-z0-9]+', '', 'g') c FROM books""")
    db.execute(f"""CREATE OR REPLACE TABLE xw AS SELECT w.key, w.label, w.kind, w.year, w.resolution, w.anchors
            FROM '{G}/work.parquet' w WHERE w.key IN (SELECT w FROM kl)
              AND regexp_replace(lower(strip_accents(split_part(w.label, ' / ', 1))), '[^a-z0-9]+', '', 'g') IN (SELECT c FROM bcheap)""")
    db.execute("CREATE OR REPLACE TABLE xt AS SELECT key, fold_title(label) t, kind, year, label, anchors FROM xw")
    cand = db.execute("""SELECT b.key, b.label, b.year, b.kind, b.hb, b.resolution, b.anchors, x.key, x.label, x.year, x.kind, x.anchors, kl.p, kl.rel
            FROM bt b JOIN xt x ON x.t = b.t AND x.key <> b.key JOIN kl ON kl.w = x.key""").fetchall()
    R['twin_title_person_rows'] = len(cand)
    people = {r[12] for r in cand}
    db.register('pp', __import__('pyarrow').table({'k': sorted(people)}))
    plabel = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet' WHERE key IN (SELECT k FROM pp)").fetchall())
    same = set()
    for a, b in db.execute(f"SELECT \"from\", \"to\" FROM '{G}/same_work.parquet'").fetchall():
        same.add((a, b))
        same.add((b, a))
    bcred = defaultdict(set)
    xcred = defaultdict(set)
    ks = sorted({r[0] for r in cand} | {r[7] for r in cand})
    db.register('kk', __import__('pyarrow').table({'k': ks}))
    for p, w in db.execute(f"""SELECT DISTINCT "from", "to" FROM '{G}/authored.parquet' WHERE "to" IN (SELECT k FROM kk)
                               UNION SELECT DISTINCT "from", "to" FROM '{G}/edited.parquet' WHERE "to" IN (SELECT k FROM kk)""").fetchall():
        bcred[w].add(p)
    for p, w in db.execute("SELECT p, w FROM kl WHERE w IN (SELECT k FROM kk)").fetchall():
        xcred[w].add(p)
    nreviews = Counter(dict(db.execute(f"""SELECT "to", count(*) FROM '{G}/reviews.parquet' WHERE "to" IN (SELECT k FROM kk) GROUP BY 1""").fetchall()))
    allp = sorted({p for v in list(bcred.values()) + list(xcred.values()) for p in v})
    labs = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet' WHERE key IN (SELECT unnest(?))", [allp]).fetchall())
    plabel.update(labs)
    pairs = {}
    for bk, blab, by, bkind, hb, bres, banch, xk, xlab, xy, xkind, xanch, p, rel in cand:
        names, role, src = printed_of(bk, blab, hb, hauth)
        lev = max((agree_level(n, plabel.get(p, '')) or '' for n in names), key=lambda v: ('', 'initial', 'variant', 'full').index(v), default='')
        if not lev:
            continue
        key = (bk, xk)
        prev = pairs.get(key)
        if prev and ('', 'initial', 'variant', 'full').index(prev['name_level']) >= ('', 'initial', 'variant', 'full').index(lev):
            continue
        pairs[key] = dict(book=bk, book_label=blab, book_year=by, book_kind=bkind, book_resolution=bres,
                          book_anchors=';'.join(sorted(banch or ())), twin=xk, twin_label=xlab,
                          twin_year=xy, twin_kind=xkind, twin_anchors=';'.join(sorted(xanch or ())), person=p,
                          person_label=plabel.get(p, ''), twin_relation=rel, name_level=lev, printed='; '.join(names),
                          printed_role=role, book_credits=';'.join(sorted(bcred.get(bk, ()))),
                          twin_credits=';'.join(sorted(xcred.get(xk, ()))), book_reviews=nreviews.get(bk, 0))
    # tiers
    by_book, by_twin = defaultdict(set), defaultdict(set)
    for (b, x) in pairs:
        by_book[b].add(x)
        by_twin[x].add(b)
    out = []
    seen_pairs = Counter(frozenset(k) for k in pairs)
    reversed_pairs = {k for k, n in seen_pairs.items() if n > 1}
    for (b, x), r in sorted(pairs.items()):
        why = []
        if (b, x) in same:
            why.append('already-same-work')
        if r['book_credits'] and r['person'] in r['book_credits'].split(';') and (b, x) not in same:
            r['note'] = 'person credited on both'
        if r['name_level'] != 'full':
            why.append(f"name-{r['name_level']}")
        if not kind_ok(r['twin_kind']):
            why.append(f"twin-kind-{r['twin_kind']}")
        if r['book_resolution'] == 'unkeyed':
            why.append('book-unkeyed')
        if len(by_book[b]) > 1:
            why.append('book-has-several-twins')
        if len(by_twin[x]) > 1:
            why.append('twin-has-several-books')
        ed_b, ed_x = bool(EDITION.search(r['book_label'] or '')), bool(EDITION.search(r['twin_label'] or ''))
        if ed_b or ed_x:
            why.append('edition-marker')
        vb, vx = VOLUME.findall(r['book_label'] or ''), VOLUME.findall(r['twin_label'] or '')
        if vb or vx:
            why.append('volume-marker')
        lb = {a for a in (r['book_anchors'] or '').split(';') if a.startswith('lccn:')}
        lx = {a for a in r['twin_anchors'].split(';') if a.startswith('lccn:')}
        if lb and lx and not (lb & lx):
            why.append('two-lccns')            # two LC records: another edition, printing or publisher
        if frozenset((b, x)) in reversed_pairs:
            why.append('pair-found-both-ways')
        tp = set(r['twin_credits'].split(';')) - {''}
        bp = set(r['book_credits'].split(';')) - {''}
        printed_fams = {f for n in r['printed'].split('; ') for f, _, _ in forms(n)[:1]}
        others = [k for k in tp if k != r['person'] and not ({f for f, _, _ in forms(plabel.get(k, ''))[:1]} & printed_fams)]
        if others:
            why.append('twin-credits-a-person-not-printed')
        if [k for k in bp - tp - {r['person']} if not ({f for f, _, _ in forms(plabel.get(k, ''))[:1]} & printed_fams)]:
            why.append('book-credits-a-person-not-printed')
        by_, xy_ = r['book_year'], r['twin_year']
        if by_ is not None and xy_ is not None:
            if abs(by_ - xy_) > 2:
                why.append('years-over-2-apart')
            r['year_tier'] = 'both'
        else:
            r['year_tier'] = 'one-missing' if (by_ is not None or xy_ is not None) else 'both-missing'
            if len(fold_title(r['book_label'])) < 25 or len(fold_title(r['book_label']).split()) < 4:
                why.append('year-missing-short-title')
        r['held'] = ';'.join(why)
        if 'already-same-work' in why:
            r['tier'] = 'already-same-work'
        elif why:
            r['tier'] = 'held'
        else:
            r['tier'] = 'merge' if r['year_tier'] == 'both' else 'merge-year-missing'
        out.append(r)
    R['twin_pairs'] = len(out)
    R['twin_pairs_by_tier'] = dict(Counter(r['tier'] for r in out))
    R['twin_held_reasons'] = dict(Counter(x for r in out if r['tier'] == 'held' for x in r['held'].split(';')))
    R['twin_merge_book_uncredited'] = sum(1 for r in out if r['tier'].startswith('merge') and not r['book_credits'])
    R['twin_merge_book_credits_person'] = sum(1 for r in out if r['tier'].startswith('merge') and r['person'] in r['book_credits'].split(';'))
    R['twin_merge_twin_anchor_kinds'] = dict(Counter(a.split(':', 1)[0] for r in out if r['tier'].startswith('merge')
                                                      for a in {x.split(':', 1)[0] for x in r['twin_anchors'].split(';') if x}))
    with gzip.open(OUT / 'twins.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        cols = list(out[0]) if out else ['book']
        cols = cols + [c for c in ('note',) if c not in cols]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.Table.from_pylist([dict(book=r['book'], twin=r['twin'], person=r['person'], tier=r['tier']) for r in out]
                                        or [dict(book='', twin='', person='', tier='')]), SCRATCH / 'twins.parquet')


# ---------------------------------------------------------------- proposal (B)

def cmd_proposal(args):
    """proposal.json (merge tier) and proposal-year-missing.json: each twin (the claimed work) merged into the catalogue
    book, dry-run validated on the key-log cache (read-only)"""
    import identifiers as I
    import keylog_snapshot as KS
    rows = list(csv.DictReader(gzip.open(OUT / 'twins.csv.gz', 'rt', encoding='utf-8')))
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    R = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    for tier, name in (('merge', 'proposal.json'), ('merge-year-missing', 'proposal-year-missing.json')):
        state = KS.read_state()          # fresh per proposal: the dry run validates in place
        ops, skipped = [], Counter()
        for r in rows:
            if r['tier'] != tier:
                continue
            b, x = r['book'], r['twin']
            kb, kx = state.keys.get(b), state.keys.get(x)
            if not kb or not kx or kb['status'] != 'active' or kx['status'] != 'active':
                skipped['key-not-active'] += 1
                continue
            mb, mx = state.members.get(b, set()), state.members.get(x, set())
            if any(m.startswith('not-same:') and (m.endswith(x) or m.endswith(b)) for m in set(mb) | set(mx)):
                skipped['not-same-mark'] += 1
                continue
            # the catalogue book survives; when only the twin carries an LCCN (a second H-Net record of an LC book), the twin
            hb_l = any(a.startswith('lccn:') for a in kb['anchors'])
            hx_l = any(a.startswith('lccn:') for a in kx['anchors'])
            if hx_l and not hb_l:
                b, x = x, b
                skipped['into-twin-with-lccn'] += 1
            ops.append(dict(event='merge', key=x, into=b, decided_by='rule',
                            basis=(f"one book held twice (printed-author-books-2026-11-15, {tier}): {r['twin']} '{r['twin_label'][:120]}' "
                                   f"({r['twin_year'] or 'no year'}) is credited in the key log to {r['person']} '{r['person_label']}'; "
                                   f"{r['book']} '{r['book_label'][:160]}' ({r['book_year'] or 'no year'}) prints that name "
                                   f"({r['name_level']} agreement) and the same title; merged into {b}")))
        prop = dict(basis=('one book held twice: a work a person claims (ORCID, OpenAlex, Crossref or LC credit in the key log) '
                           'and a catalogue or review book (H-Net, LC) whose printed author is that person by full-name agreement, '
                           'with the same folded title (main title and subtitle; the statement of responsibility removed), '
                           + ('years within 2' if tier == 'merge' else 'one year missing, title of 4+ words and 25+ letters')
                           + '; edition, volume and kind markers, several twins and unprinted co-credited people held '
                           '(printed-author-books-2026-11-15; ARCHITECTURE.md section 8 class 46)'),
                    decided_by='rule', ops=ops)
        events, _ = I.materialise(state, prop, 'dry-run', 'dry-run', inplace=True)
        (OUT / name).write_text(json.dumps(prop, ensure_ascii=False, indent=0) + '\n')
        R[f'proposal|{name}'] = dict(merges=len(ops), dry_run_events=len(events), skipped=dict(skipped))
        print(name, len(ops), 'merges,', len(events), 'dry-run events', dict(skipped), flush=True)
    (OUT / 'report.json').write_text(json.dumps(R, indent=1, ensure_ascii=False) + '\n')


# ---------------------------------------------------------------- finish (A)

def cmd_finish(args):
    """credits.csv.gz in the name-only format (+ printed_role): the linker's state per position; a position whose
    candidate holds the book's twin (B, merge tiers) is linked by that fact (branch own-claimed-twin)"""
    db = duck()
    S = SCRATCH
    tw = defaultdict(set)
    for b, x, p, tier in db.execute(f"SELECT book, twin, person, tier FROM '{S}/twins.parquet' WHERE book <> ''").fetchall():
        if tier in ('merge', 'merge-year-missing'):
            tw[b].add(p)
    q = f"""SELECT p.work, p.pos, p.n_auth, p.name, p.source, p.year, p.title, ro.printed_role, r.state, r.key, r.candidates,
                   r.n_candidates, r.branch, r.signals
            FROM '{S}/results.parquet' r JOIN '{S}/positions.parquet' p USING (pid) JOIN '{S}/roles.parquet' ro USING (pid)
            ORDER BY p.work, p.pos"""
    rows = db.execute(q).fetchall()
    out, R = [], Counter()
    for work, pos, n, name, src, year, title, prole, st, key, cands, ncand, br, sig in rows:
        cs = [c for c in (cands or '').split('|') if c]
        twin_p = tw.get(work, set())
        if st not in ('exact', 'linked') and twin_p:
            hit = [c for c in cs if c in twin_p] or ([key] if key in twin_p else [])
            if len(hit) == 1:
                st, key, br = 'linked', hit[0], 'own-claimed-twin'
                sig = ((sig or '') + ' own-claimed-twin').strip()
                R['twin_fact_promoted'] += 1
        R[f'state|{st}'] += 1
        R[f'state_by_role|{prole}|{st}'] += 1
        if st in ('exact', 'linked'):
            R[f'linked_branch|{br}'] += 1
        out.append(dict(work=work, role='author', printed_role=prole, position=pos, n_authors=n, printed_name=name,
                        printed_institution='', source=src, source_person_id='', year=year, state=st, person_key=key or '',
                        candidates=cands or '', n_candidates=ncand, branch=br, signals=sig or '', title=title))
    R['positions'] = len(out)
    R['books_gaining_a_link'] = len({r['work'] for r in out if r['state'] in ('exact', 'linked')})
    R['books_gaining_a_link_by_role'] = dict(Counter(r['printed_role'] for r in {r['work']: r for r in out if r['state'] in ('exact', 'linked')}.values()))
    R['books_with_candidates_only'] = len({r['work'] for r in out if r['state'] == 'possible'} - {r['work'] for r in out if r['state'] in ('exact', 'linked')})
    R['books_with_no_keyed_name'] = len({r['work'] for r in out} - {r['work'] for r in out if r['state'] != 'none'})
    cols = ['work', 'role', 'printed_role', 'position', 'n_authors', 'printed_name', 'printed_institution', 'source',
            'source_person_id', 'year', 'state', 'person_key', 'candidates', 'n_candidates', 'branch', 'signals']
    with gzip.open(OUT / 'credits.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in out:
            if r['state'] in ('exact', 'linked', 'possible', 'ambiguous'):
                w.writerow(r)
    rep = json.loads((OUT / 'report.json').read_text()) if (OUT / 'report.json').exists() else {}
    rep['positions_stage'] = json.loads((S / 'positions-report.json').read_text())
    rep['links'] = dict(sorted(R.items()))
    (OUT / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(dict(sorted(R.items())), indent=1))
    # seeded samples for the hand check: 40 linked positions, 40 twin pairs from the merge tiers
    rnd = random.Random(SAMPLE_SEED)
    linked = [r for r in out if r['state'] in ('exact', 'linked')]
    sample_a = rnd.sample(linked, min(40, len(linked)))
    twins_rows = [r for r in csv.DictReader(gzip.open(OUT / 'twins.csv.gz', 'rt', encoding='utf-8')) if r['tier'].startswith('merge')]
    sample_b = random.Random(SAMPLE_SEED + 1).sample(twins_rows, min(40, len(twins_rows)))
    plabel = dict(db.execute(f"SELECT key, label FROM '{GRAPH}/person.parquet' WHERE key IN (SELECT unnest(?))",
                             [sorted({r['person_key'] for r in sample_a})]).fetchall())
    with open(OUT / 'sample-to-check.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['part', 'book', 'book_label', 'year', 'printed_name', 'person', 'person_label', 'twin', 'twin_label',
                    'twin_year', 'branch_or_tier', 'signals'])
        for r in sample_a:
            w.writerow(['A', r['work'], r['title'], r['year'], r['printed_name'], r['person_key'], plabel.get(r['person_key'], ''),
                        '', '', '', r['branch'], r['signals'][:300]])
        for r in sample_b:
            w.writerow(['B', r['book'], r['book_label'], r['book_year'], r['printed'], r['person'], r['person_label'], r['twin'],
                        r['twin_label'], r['twin_year'], r['tier'], r['name_level']])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('positions')
    sub.add_parser('proposal')
    sub.add_parser('finish')
    args = ap.parse_args()
    {'positions': cmd_positions, 'proposal': cmd_proposal, 'finish': cmd_finish}[args.cmd](args)


if __name__ == '__main__':
    main()
