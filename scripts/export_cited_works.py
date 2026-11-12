"""Cited works matched on 2026-11-10 (LC 2016 books, OpenAlex, Crossref) -> tracked two-layer tables (2026-11-10).

The three matchers of 2026-11-10 tie dissertation-cited works the key log does not hold to a public record:
- data/identifiers/cited-works-lc-full-2026-11-10/crosswalk.csv.gz   (books -> LCCNs; key_cited_works_lc_full.py)
- data/identifiers/cited-works-openalex-2026-11-10/crosswalk.csv.gz  (articles, chapters, books 2017+ -> DOI or
  OpenAlex id; key_cited_works_openalex.py) and its chapter-volumes.csv.gz (a chapter's containing volume)
- data/identifiers/cited-works-crossref-2026-11-10/crosswalk.csv.gz  (articles, chapters -> DOI; key_cited_works_crossref.py)
and data/identifiers/cited-work-authors-2026-11-10/links.csv.gz (link_cited_work_authors.py) says who wrote them.

Owner (2026-11-10), the two-layer rule: these works are NOT minted in the key log. They live here and appear in the
graph as Work nodes keyed by public identifier (`lccn:<lccn>`, `doi:<doi>`, `openalex:<W id>` when OpenAlex has no
DOI), resolution `unkeyed`; when the key log holds that identifier the citation goes to the key (build_graph).
Citers are dissertations only, so these works get no outgoing CITES.

One corpus work -> one cited work id. Precedence when several crosswalks hold a corpus work:
1. LC (books; 20 works are also in the OpenAlex crosswalk: LC wins);
2. Crossref (the Crossref crosswalk only holds works the OpenAlex one did not);
3. OpenAlex, except where the Crossref agreement check (agreement-different.csv.gz) found another DOI for the work:
   Crossref's DOI is preferred, unless the hand review (agreement-review.csv) says the OpenAlex DOI is the right one
   (`openalex`), or that both DOIs are one article (`both`): then the Crossref DOI is the id and the OpenAlex DOI an
   alias;
4. OpenAlex rows after the Crossref matcher's guards, imported from key_cited_works_crossref (not re-matched):
   different part markers ('Part 1' / 'Part 2'), an erratum/addendum notice taken for the article, and (articles and
   chapters) another venue in another year.
An LC edition cluster carries all its LCCNs; its id is the first LCCN as the crosswalk lists them (the earliest record,
as key_lc_works anchors claims on the work's earliest LCCN). Works whose identifiers overlap (two corpus works sharing
an LCCN, a DOI alias that is another work's id) are one cited work (union of their identifiers).

Writes data/graph/cited-works/ (gzipped CSV, each file under 50 MB; parts if a table grows past that):
- cites.csv.gz          dissertation_id, work (cited work id), source (lc-full / openalex / crossref), basis
- works.csv.gz          id, title, year, kind, container, lccns (all, ';'), alias_ids (';'), source, basis,
                        corpus_works, citing_theses
- authors.csv.gz        work, source, position, role, raw_name, source_person_id (lcnaf: / openalex: / orcid:),
                        state (exact / linked / possible / none), branch, person_key (exact, linked), candidates
                        (possible; '|'), n_candidates, signals, citing_theses
- chapter-volumes.csv.gz  corpus chapter work_id -> the containing volume (kept out of CITES: citing a chapter is not
                        citing the volume)
- report.json
Only ids, titles of cited works and names of cited authors: no thesis text.

Added 2026-11-11:
- Crossref metadata matches (data/identifiers/cited-works-crossref-meta-2026-11-11, key_cited_works_crossref_meta.py;
  source `crossref-meta`). Precedence: last, after LC > Crossref > OpenAlex: it only fills works that none of the
  earlier crosswalks holds (by construction its corpus excluded them; any overlap is counted and the earlier one kept).
  Its held rows are never used, and as a review-collision guard every match flagged `review_like` in match-flags.csv.gz
  is dropped (a record whose title reads as a book review: price, pages, 'By <Name>', one or two pages).
- Journal-metadata matches (data/identifiers/cited-works-journal-meta-2026-11-11, key_cited_works_journal_meta.py;
  source `journal-meta`; ids `doi:`, `ojs:` (an OJS OAI record) or `openalex:`). Precedence: after every other
  crosswalk; held rows never used, rows with review_like = 1 dropped. Translations still apply on top.
- Translations and editions (data/identifiers/cited-works-translations-2026-11-11, NOTES.md). A corpus work in that
  crosswalk with relation translation or edition is cited as its canonical (original) work: the cites row goes to the
  canonical id with source `translation` / `edition`, basis = route, `cited_as` = the node the citation went to
  before (a key of the older crosswalks, a cited-works id) or `corpus:<work_id>` when the work was unmatched, and
  `replaces` = the older crosswalks' key when no other corpus work of that thesis still maps to it (the build drops
  that thesis edge, so a moved citation is not counted twice). Part-marker guard: a row whose cited title and
  canonical title both carry a part or volume marker that differ ('Part 2' / 'vol. 1') is held. Canonical `lccn:`
  ids that no cited work holds become works here (source `lc-translations`). Compilations (relation compilation, no
  single original) become works keyed `corpus:<work_id>` (source `compilation`) with an author row (state `linked`,
  branch `compilation`) to compilations.csv.gz's kg_person_key.
- Recent books (2026-11-12; data/identifiers/cited-works-recent-books-2026-11-12, key_cited_works_recent_books.py;
  source `recent-books`; ids `doi:` or `openalex:`, kind book): Crossref book records and OpenAlex works found with no
  subject filter for corpus books 2017+ and books before 2017 cited by 3+ theses that no crosswalk held. Precedence:
  older keyed crosswalks > LC > Crossref (11-10) > OpenAlex > Crossref metadata > journal metadata > recent books;
  translations last. A corpus work an earlier crosswalk chose is skipped (counted); when the key log holds the DOI the
  build cites the key. Their printed authors are read by link_work_people.py nameonly-extra.
- editions.csv.gz: one row per corpus work moved: work_id, cited_as, canonical, relation, route, basis, confidence,
  cited_language, cited_title, cited_year, theses (the build's EDITION_OF table).

    python3 scripts/export_cited_works.py
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identifiers import ROOT  # noqa: E402
import key_cited_works_crossref as kcr  # noqa: E402  (guards: part_of, NOTICE, other_venue)

IDS = ROOT / 'data/identifiers'
LC = IDS / 'cited-works-lc-full-2026-11-10'
OA = IDS / 'cited-works-openalex-2026-11-10'
CR = IDS / 'cited-works-crossref-2026-11-10'
CM = IDS / 'cited-works-crossref-meta-2026-11-11'
JM = IDS / 'cited-works-journal-meta-2026-11-11'
TR = IDS / 'cited-works-translations-2026-11-11'
RB = IDS / 'cited-works-recent-books-2026-11-12'
LINKS = IDS / 'cited-work-authors-2026-11-10/links.csv.gz'
OLD = [IDS / 'cited-works-2026-11-04/crosswalk.csv.gz', IDS / 'cited-articles-2026-11-03b/crosswalk.csv.gz',
       IDS / 'cited-own-works-2026-11-03f/crosswalk.csv.gz']
# the other crosswalks behind data/graph/cites.csv.gz (2026-11-11 check: OLD explains 676k of its 785k rows, these
# four translation checks and the Qwen tail the rest but 378); read for the translation moves and the 'before' count
OLD_MORE = [IDS / f'translation-check-2026-11-03{x}/crosswalk.csv.gz' for x in ('d', 'c', 'b', '')] + [
    IDS / 'qwen-tail-2026-11-04/crosswalk.csv.gz']
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
OUT = ROOT / 'data/graph/cited-works'
SCRATCH = Path(os.environ.get('CW_SCRATCH', '/tmp/claude-1000/-home-jic823-historiography/'
                              'd3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/integrate2'))
MAX_BYTES = 50_000_000
COMMA = ('lc-comma', 'corpus-comma', 'both-comma')     # LC title forms audited at ~97% (the rest 99%)
# volume markers for the translation part guard, beside key_cited_works_crossref.part_of ('Part 2', '(II)')
VOLUME = re.compile(r'(?i)\b(?:part|partie|parte|teil|pt|vol|vols|volume|tomo|tome|band|bd|livro|libro|book|bk)\b\.?\s*'
                    r'([0-9]+|[ivx]+)\b')
ROMAN = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10'}


def volume_of(title):
    p = kcr.part_of(title)
    if p:
        return p
    m = VOLUME.search(title or '')
    return ROMAN.get(m.group(1).lower(), m.group(1).lower()) if m else None


def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def intor(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# OpenAlex `source` is often a repository or a publisher's e-book platform rather than the venue (Dialnet, HAL,
# 'Routledge eBooks'); the Crossref guard reads a container-title. Same list as link_cited_work_authors.REPOSITORY.
PLATFORM = re.compile(r'(?i)repositor|\bHAL\b|dialnet|ebooks|pers[ée]e|zenodo|philpapers|researchgate|research portal|doaj|'
                      r'digital|archive|bibliography|scholarsarchive|e-?prints|white rose|discovery|depot|dépôt|openedition|'
                      r'ssrn|cairn|jstor|ssoar|university of|universit|library|biblioteca|database|apollo')


def named_venue(source):
    return bool((source or '').strip()) and not PLATFORM.search(source)


def venue_words_shared(a, b):
    """The corpus container and the OpenAlex source share a word of four letters or more (on its first five letters):
    'Historischen Zeitschrift' / 'Historische Zeitschrift', 'Revista da USP' / 'Revista USP' are one venue misspelt
    (a dry run of the raw Crossref guard on the OpenAlex rows, 2026-11-10: 2,215 rows, nearly all such spellings,
    repository copies or e-book platforms; 'Rivisita de Storia della Filosofia' / 'Early Science and Medicine' is the
    case the guard is for)."""
    wa = {w[:5] for w in kcr.oa.ckey(a).split() if len(w) >= 4}
    wb = {w[:5] for w in kcr.oa.ckey(b).split() if len(w) >= 4}
    return bool(wa & wb)


def oa_kind(t):
    return {'book-chapter': 'chapter', 'book': 'book'}.get(t, 'article')


def cr_kind(t):
    return {'book-chapter': 'chapter', 'monograph': 'book', 'book': 'book'}.get(t, 'article')


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        while self.p.setdefault(x, x) != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a


def write_csv(path, header, rows, report):
    """Gzipped CSV; split into path-stem/part-NN.csv.gz if it would pass 50 MB (none does at today's size)."""
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        n = 0
        for r in rows:
            w.writerow(r)
            n += 1
    size = path.stat().st_size
    if size >= MAX_BYTES:
        sys.exit(f'{path.name} is {size / 1e6:.0f} MB: split it into parts before committing')
    report['files'][path.name] = dict(rows=n, bytes=size)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = {'files': {}}
    R = Counter()

    # ---- crosswalk rows -------------------------------------------------------------------------------------
    lc = {r['work_id']: r for r in rd(LC / 'crosswalk.csv.gz')}
    oa = {r['work_id']: r for r in rd(OA / 'crosswalk.csv.gz')}
    cr = {r['work_id']: r for r in rd(CR / 'crosswalk.csv.gz')}
    diff = {r['work_id']: r for r in rd(CR / 'agreement-different.csv.gz')}
    with open(CR / 'agreement-review.csv', newline='', encoding='utf-8') as f:
        review = {r['work_id']: r for r in csv.DictReader(f)}
    R.update(lc_rows=len(lc), openalex_rows=len(oa), crossref_rows=len(cr), agreement_different=len(diff),
             agreement_reviewed=len(review))

    # corpus fields of the OpenAlex works (title, year, container, kind) for the guards
    db = duckdb.connect()
    tmp = SCRATCH / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db.execute(f"SET memory_limit='4GB'; SET threads=3; SET max_temp_directory_size='3GB'; SET temp_directory='{tmp}'")
    db.execute('CREATE TABLE want(work_id VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(w,) for w in oa])
    corpus = {w: dict(title=t, year=intor(y), container=c, kind=k) for w, t, y, c, k in db.execute(
        f"""SELECT work_id, title, year, container, kind FROM read_csv('{CORPUS}/works.csv', all_varchar=true)
            WHERE work_id IN (SELECT work_id FROM want)""").fetchall()}

    # ---- one id per corpus work -------------------------------------------------------------------------------
    chosen = {}          # corpus work -> dict(ids=[preferred, aliases...], source, basis, title, year, kind, container, rank)
    guard = Counter()
    guarded = []
    for w, r in lc.items():
        ls = [x for x in r['lccns'].split(';') if x.strip()]
        chosen[w] = dict(ids=[f'lccn:{x}' for x in ls], source='lc-full', basis=r['basis'], title=r['lc_title'],
                         year=intor(r['lc_year']), kind='book', container='', lccns=ls)
    for w, r in cr.items():
        if w in chosen:
            R['crossref_also_lc'] += 1
            continue
        chosen[w] = dict(ids=[f"doi:{r['doi'].lower()}"], source='crossref', basis=r['basis'], title=r['cr_title'],
                         year=intor(r['cr_year']), kind=cr_kind(r['cr_type']), container=r['cr_journal'], lccns=[])
    for w, r in oa.items():
        if w in chosen:
            R['openalex_also_lc' if chosen[w]['source'] == 'lc-full' else 'openalex_also_crossref'] += 1
            continue
        d = diff.get(w)
        if d:
            side = review.get(w, {}).get('right_side', '')
            R[f'agreement_{side or "unreviewed"}'] += 1
            if side != 'openalex':
                ids = [f"doi:{d['cr_doi'].lower()}"] + ([f"doi:{d['oa_doi'].lower()}"] if side == 'both' else [])
                chosen[w] = dict(ids=ids, source='crossref', basis=f"{d['basis']}+agreement-{side or 'unreviewed'}",
                                 title=d['cr_title'], year=intor(d['cr_year']), kind='article', container=d['cr_journal'],
                                 lccns=[], authors_from_openalex=side == 'both')
                continue
        c = corpus.get(w)
        if c is None:
            R['openalex_not_in_corpus'] += 1
            continue
        t = c['title'] or ''
        rt = r['oa_title'] or ''
        cp, rp = kcr.part_of(t), kcr.part_of(rt)
        if kcr.NOTICE.search(rt) and not kcr.NOTICE.search(t):
            guard['notice'] += 1
            guarded.append((w, 'notice', t, c['year'], c['container'], rt, r['oa_year'], r['oa_source'], r['doi']))
            continue
        if cp and rp and cp != rp:
            guard['part_differs'] += 1
            guarded.append((w, 'part_differs', t, c['year'], c['container'], rt, r['oa_year'], r['oa_source'], r['doi']))
            continue
        if (c['kind'] == 'article' or c['kind'] == 'chapter' and r['oa_type'] == 'article') and kcr.other_venue(
                dict(container=c['container'], year=c['year']), dict(year=intor(r['oa_year']), source=r['oa_source'])):
            guard['other_venue_raw'] += 1
            if named_venue(r['oa_source']) and not venue_words_shared(c['container'], r['oa_source']):
                guard['other_venue_other_year'] += 1
                guarded.append((w, 'other_venue_other_year', t, c['year'], c['container'], rt, r['oa_year'],
                                r['oa_source'], r['doi']))
                continue
        doi = (r['doi'] or '').lower()
        ids = ([f'doi:{doi}'] if doi else []) + ([f"openalex:{r['openalex_id']}"] if r['openalex_id'] else [])
        chosen[w] = dict(ids=ids, source='openalex', basis=r['basis'], title=r['oa_title'], year=intor(r['oa_year']),
                         kind=oa_kind(r['oa_type']), container=r['oa_source'], lccns=[])
    # Crossref metadata matches (2026-11-11): last in precedence, held rows never used, review-like matches dropped
    cm_held = {r['work_id'] for r in rd(CM / 'held.csv.gz')}
    cm_flag = {r['work_id']: r for r in rd(CM / 'match-flags.csv.gz')}
    for r in rd(CM / 'crosswalk.csv.gz'):
        w = r['work_id']
        R['crossref_meta_rows'] += 1
        if w in chosen:
            R[f"crossref_meta_also_{chosen[w]['source']}"] += 1
            continue
        if w in cm_held:
            R['crossref_meta_held'] += 1
            continue
        if cm_flag.get(w, {}).get('review_like') == '1':
            R['crossref_meta_review_like_dropped'] += 1
            continue
        chosen[w] = dict(ids=[f"doi:{r['doi'].lower()}"], source='crossref-meta', basis=r['basis'], title=r['cr_title'],
                         year=intor(r['cr_year']), kind=cr_kind(r['cr_type']), container=r['cr_journal'], lccns=[])
        R['crossref_meta_used'] += 1
    # journal-metadata matches (2026-11-11, key_cited_works_journal_meta.py: OJS/bepress/OpenAlex/Crossref records of
    # the journals the theses cite): last of all, same guards (held rows never used, review-like matches dropped)
    jm_held = {r['work_id'] for r in rd(JM / 'held.csv.gz')}
    for r in rd(JM / 'crosswalk.csv.gz'):
        w = r['work_id']
        R['journal_meta_rows'] += 1
        if w in chosen:
            R[f"journal_meta_also_{chosen[w]['source']}"] += 1
            continue
        if w in jm_held:
            R['journal_meta_held'] += 1
            continue
        if r['review_like'] == '1':
            R['journal_meta_review_like_dropped'] += 1
            continue
        chosen[w] = dict(ids=[r['id']], source='journal-meta', basis=r['basis'], title=r['title'], year=intor(r['year']),
                         kind=cr_kind(r['type']), container=r['journal'], lccns=[])
        R['journal_meta_used'] += 1
    # recent books (2026-11-12, key_cited_works_recent_books.py: Crossref book records and OpenAlex works with no
    # subject filter, for corpus books 2017+ and books before 2017 cited by 3+ theses that no crosswalk holds): after
    # every other crosswalk, before translations; held rows are not in the crosswalk; kind book; ids doi: / openalex:
    for r in rd(RB / 'crosswalk.csv.gz'):
        w = r['work_id']
        R['recent_books_rows'] += 1
        if w in chosen:
            R[f"recent_books_also_{chosen[w]['source']}"] += 1
            continue
        ids = [r['id']] + [x for x in (r['alias_ids'] or '').split(';') if x.strip() and x != r['id']]
        chosen[w] = dict(ids=ids, source='recent-books', basis=r['basis'], title=r['title'], year=intor(r['year']),
                         kind='book', container='', lccns=[], recent_book=r)
        R['recent_books_used'] += 1
    oa_removed = sum(v for k, v in guard.items() if k != 'other_venue_raw')
    report['openalex_guards_removed'] = dict(guard, total=oa_removed)
    write_csv(args.out / 'openalex-guarded.csv.gz', ['work_id', 'guard', 'cited_title', 'cited_year', 'cited_container',
                                                     'oa_title', 'oa_year', 'oa_source', 'oa_doi'], guarded, report)

    # union works whose identifiers overlap; the component's id is the preferred id of its earliest member
    uf = UF()
    for w, c in chosen.items():
        for x in c['ids'][1:]:
            uf.union(c['ids'][0], x)
    members = defaultdict(list)
    for w, c in chosen.items():
        members[uf.find(c['ids'][0])].append(w)

    def rank(w):
        c = chosen[w]
        return ({'lc-full': 0, 'crossref': 1, 'openalex': 2, 'crossref-meta': 3, 'journal-meta': 4,
                 'recent-books': 5}[c['source']], c['year'] or 9999,
                c['ids'][0])
    cid = {}
    works = {}
    for root, ws in members.items():
        ws.sort(key=rank)
        head = chosen[ws[0]]
        wid = head['ids'][0]
        if wid.startswith('openalex:') and any(x.startswith('doi:') for w in ws for x in chosen[w]['ids']):
            wid = next(x for w in ws for x in chosen[w]['ids'] if x.startswith('doi:'))
        allids = list(dict.fromkeys(x for w in ws for x in chosen[w]['ids']))
        if len(ws) > 1 and len({chosen[w]['ids'][0] for w in ws}) > 1:
            R['components_joining_different_ids'] += 1
        for w in ws:
            cid[w] = wid
        works[wid] = dict(title=head['title'], year=min((chosen[w]['year'] for w in ws if chosen[w]['year']), default=None),
                          kind=head['kind'], container=head['container'],
                          lccns=[x[5:] for x in allids if x.startswith('lccn:')],
                          aliases=[x for x in allids if x != wid and not x.startswith('lccn:')],
                          source=head['source'], basis=head['basis'], corpus_works=len(ws), theses=set())
    R['corpus_works_mapped'] = len(cid)
    R['cited_works'] = len(works)

    # ---- translations, editions, compilations (2026-11-11) ---------------------------------------------------------
    lcn_index = {}                                   # lccn -> the cited work holding it
    for wid, v in works.items():
        for x in v['lccns']:
            lcn_index.setdefault(x, wid)
    tr_held = {r['work_id'] for r in rd(TR / 'held.csv.gz')}
    tx, comp, tguard = {}, {}, Counter()
    for r in rd(TR / 'crosswalk.csv.gz'):
        w = r['work_id']
        if w in tr_held:
            tguard['in_held'] += 1
            continue
        if r['relation'] == 'compilation':
            comp[w] = r
            continue
        if r['relation'] not in ('translation', 'edition') or not r['canonical_id']:
            tguard['no_canonical'] += 1
            continue
        a, b = volume_of(r['cited_title']), volume_of(r['canonical_title'])
        if a and b and a != b:
            tguard['part_differs'] += 1
            continue
        can = r['canonical_id']
        if can.startswith('lccn:'):
            x = can[5:]
            if x in lcn_index:
                can = lcn_index[x]
                tguard['canonical_lccn_in_cited_work'] += 1
            else:
                works[can] = dict(title=r['canonical_title'], year=intor(r['canonical_year']), kind='book', container='',
                                  lccns=[x], aliases=[], source='lc-translations', basis=f"{r['route']}/{r['relation']}",
                                  corpus_works=0, theses=set())
                lcn_index[x] = can
                tguard['canonical_lccn_new_work'] += 1
            if works[can]['source'] == 'lc-translations':
                works[can]['corpus_works'] += 1
        tx[w] = dict(r, canonical=can)
    comp_person = {}
    for r in rd(TR / 'compilations.csv.gz'):
        comp_person.setdefault(r['work_id'], r)
    for w, r in comp.items():
        works[f'corpus:{w}'] = dict(title=r['cited_title'], year=intor(r['cited_year']), kind='book', container='',
                                    lccns=[], aliases=[], source='compilation', basis='compilation', corpus_works=1,
                                    theses=set())
    report['translations'] = dict(tguard, moved_works=len(tx), compilations=len(comp),
                                  rule='translation/edition rows of the 2026-11-11 crosswalk minus held rows and rows whose '
                                       'cited and canonical titles carry different part/volume markers')

    # ---- citations --------------------------------------------------------------------------------------------
    old, old_all, old3 = {}, defaultdict(set), set()
    for p in OLD:
        old3.update(r['work_id'] for r in rd(p))
    for p in OLD + OLD_MORE:                        # as export_citations: the first crosswalk naming a work keeps it
        for r in rd(p):
            if r.get('key'):
                old.setdefault(r['work_id'], r['key'])
                old_all[r['work_id']].add(r['key'])
    R['old_crosswalk_works'] = len(old)
    R['new_works_also_in_old_crosswalks'] = len(old.keys() & set(cid))
    # kind of each cited corpus work and country of each thesis, for the rates by type and country
    kind_of = dict(db.execute(f"SELECT work_id, kind FROM read_csv('{CORPUS}/works.csv', all_varchar=true)").fetchall())
    with open(CORPUS / 'dissertations.csv', newline='', encoding='utf-8') as f:
        country = {r['id']: r['country'] for r in csv.DictReader(f)}
    db.close()
    pairs, epairs, cpairs = {}, {}, set()
    keep_old, moved = set(), []
    corpus_rows = matched_old = matched_new = matched_any = recovered = moved_rows = comp_rows = comp_only = 0
    matched_11_10 = 0                                # the 2026-11-10 definition: the three OLD crosswalks or this table
    per_source_rows = Counter()
    rate = defaultdict(Counter)                      # dimension value -> citations, before, after, with_compilations
    for r in rd(CORPUS / 'strict-citations.csv.gz'):
        corpus_rows += 1
        d, w = r['dissertation_id'], r['work_id']
        o, n, t, c = w in old, w in cid, w in tx, w in comp
        matched_old += o
        matched_new += n and not o
        matched_any += o or n
        matched_11_10 += w in old3 or n
        recovered += t and not (o or n)
        comp_rows += c
        comp_only += c and not (o or n or t)        # compilation rows no other route matched
        for dim in (f"kind:{kind_of.get(w) or '?'}", f"country:{country.get(d) or '?'}", 'all'):
            rate[dim].update(citations=1, before=o or n, after=o or n or t, with_compilations=o or n or t or c)
        if t:
            moved_rows += o or n
            moved.append((d, w))
            continue
        if c:
            cpairs.add((d, f'corpus:{w}'))
            works[f'corpus:{w}']['theses'].add(d)
            continue
        if o:
            keep_old.update((d, k) for k in old_all[w])
        if n and not o:
            c = chosen[w]
            per_source_rows[c['source']] += 1
            key = (d, cid[w])
            if key not in pairs:
                pairs[key] = (c['source'], c['basis'])
            works[cid[w]]['theses'].add(d)
    moved_theses = defaultdict(set)
    for d, w in moved:
        r = tx[w]
        can = r['canonical']
        prev = old.get(w) or cid.get(w)
        if not prev or prev == can:                 # unmatched, or an older crosswalk already gave the canonical key
            prev = f'corpus:{w}'
        e = epairs.setdefault((d, can), dict(rel=set(), route=set(), cited_as=set(), replaces=set()))
        e['rel'].add(r['relation'])
        e['route'].add(r['route'])
        e['cited_as'].add(prev)
        e['replaces'].update(k for k in old_all.get(w, ()) if (d, k) not in keep_old)
        if can in works:
            works[can]['theses'].add(d)
        moved_theses[w].add(d)
    R['cites_pairs'] = len(pairs)
    R['edition_pairs'] = len(epairs)
    R['edition_pairs_replacing_an_older_edge'] = sum(1 for e in epairs.values() if e['replaces'])
    R['compilation_pairs'] = len(cpairs)

    def rates(c):
        n = c['citations']
        return dict(citations=n, before=c['before'], after=c['after'], with_compilations=c['with_compilations'],
                    rate_before=round(c['before'] / n, 4), rate_after=round(c['after'] / n, 4),
                    rate_with_compilations=round(c['with_compilations'] / n, 4))
    report['corpus'] = dict(citations=corpus_rows, matched_before=matched_old, matched_new=matched_new,
                            matched_before_translations=matched_any, recovered_by_translations=recovered,
                            matched_after=matched_any + recovered, rate_before=round(matched_old / corpus_rows, 4),
                            rate_before_translations=round(matched_any / corpus_rows, 4),
                            matched_as_counted_2026_11_10=matched_11_10,
                            rate_as_counted_2026_11_10=round(matched_11_10 / corpus_rows, 4),
                            rate_after=round((matched_any + recovered) / corpus_rows, 4),
                            compilation_citations=comp_rows,
                            compilation_citations_not_otherwise_matched=comp_only,
                            # 2026-11-12: counted once (adding comp_rows double counted the rows already matched)
                            rate_with_compilations=round((matched_any + recovered + comp_only) / corpus_rows, 4),
                            moved_citations=moved_rows, new_citations_by_source=dict(per_source_rows),
                            by_kind={k[5:]: rates(v) for k, v in sorted(rate.items()) if k.startswith('kind:')},
                            by_country={k[8:]: rates(v) for k, v in sorted(rate.items(), key=lambda kv: -kv[1]['citations'])
                                        if k.startswith('country:')},
                            note='citations = rows of strict-citations.csv.gz (dissertation, cited corpus work); before = '
                                 'the three older crosswalks behind data/graph/cites.csv.gz; after = those, this table and '
                                 'the translations recovered to an original; moved = already matched rows now cited as the '
                                 'canonical work (not counted twice); with_compilations adds the corpus: compilation works')
    write_csv(args.out / 'cites.csv.gz', ['dissertation_id', 'work', 'source', 'basis', 'cited_as', 'replaces'],
              sorted([(d, w, s, b, '', '') for (d, w), (s, b) in pairs.items()]
                     + [(d, w, ';'.join(sorted(e['rel'])), ';'.join(sorted(e['route'])), ';'.join(sorted(e['cited_as'])),
                         ';'.join(sorted(e['replaces']))) for (d, w), e in epairs.items()]
                     + [(d, w, 'compilation', 'compilation', '', '') for d, w in cpairs]), report)
    write_csv(args.out / 'editions.csv.gz', ['work_id', 'cited_as', 'canonical', 'relation', 'route', 'basis', 'confidence',
                                             'cited_language', 'cited_title', 'cited_year', 'theses'],
              ((w, (lambda x: x if x and x != r['canonical'] else f'corpus:{w}')(old.get(w) or cid.get(w)), r['canonical'], r['relation'], r['route'], r['basis'],
                r['confidence'], r['cited_language'], r['cited_title'], r['cited_year'], len(moved_theses[w]))
               for w, r in sorted(tx.items())), report)
    write_csv(args.out / 'works.csv.gz', ['id', 'title', 'year', 'kind', 'container', 'lccns', 'alias_ids', 'source',
                                          'basis', 'corpus_works', 'citing_theses'],
              ((k, v['title'], v['year'] or '', v['kind'], v['container'] or '', ';'.join(v['lccns']),
                ';'.join(v['aliases']), v['source'], v['basis'], v['corpus_works'], len(v['theses']))
               for k, v in sorted(works.items())), report)

    # ---- authors ------------------------------------------------------------------------------------------------
    arows = {}
    st = Counter()
    for r in rd(LINKS):
        w = r['work_id']
        if w not in cid:
            st['links_work_not_exported'] += 1
            continue
        c = chosen[w]
        want = 'lc-full' if r['source'] == 'lc' else 'openalex'
        if c['source'] != want and not (want == 'openalex' and c.get('authors_from_openalex')):
            st[f'links_{r["source"]}_dropped_work_taken_by_{c["source"]}'] += 1
            continue
        spid = r['source_person_id'] or ''
        if spid and r['source'] == 'lc':
            spid = f'lcnaf:{spid}'
        key = r['key'] if r['state'] in ('exact', 'linked') else ''
        cands = r['candidates'] if r['state'] == 'possible' else ''
        row = (cid[w], r['source'], r['position'], r['role'], r['raw_name'], spid, r['state'], r['branch'], key, cands,
               r['n_candidates'], r['signals'] or '')
        k = (cid[w], r['source'], r['role'], r['raw_name'], spid)
        old_row = arows.get(k)
        order = {'exact': 0, 'linked': 1, 'possible': 2, 'none': 3}
        if old_row is None or order[r['state']] < order[old_row[6]]:
            arows[k] = row
        else:
            st['links_duplicate_folded'] += 1
    for w in comp:                                  # a compilation's author: the KG person of the corpus author
        p = comp_person.get(w, {})
        key = p.get('kg_person_key') or ''
        arows[(f'corpus:{w}', 'compilation', 'author', comp[w]['cited_author'], '')] = (
            f'corpus:{w}', 'compilation', '1', 'author', comp[w]['cited_author'], '', 'linked' if key else 'none',
            'compilation', key, '', '1' if key else '0',
            f"kg_person_share={p.get('kg_person_share')};matched_works={p.get('kg_person_matched_works')}" if key else '')
    for row in arows.values():
        st[f'{row[1]}|{row[6]}'] += 1
    report['authors'] = dict(sorted(st.items()))
    write_csv(args.out / 'authors.csv.gz', ['work', 'source', 'position', 'role', 'raw_name', 'source_person_id', 'state',
                                            'branch', 'person_key', 'candidates', 'n_candidates', 'signals',
                                            'citing_theses'],
              (row + (len(works[row[0]]['theses']),) for _, row in sorted(arows.items())), report)

    # ---- chapter volumes (a separate table, not CITES) -----------------------------------------------------------
    cv = list(rd(OA / 'chapter-volumes.csv.gz'))
    write_csv(args.out / 'chapter-volumes.csv.gz', ['work_id', 'volume_id', 'volume_title', 'volume_year', 'volume_type',
                                                    'volume_source', 'basis', 'cited_by_dissertations'],
              ((r['work_id'], f"doi:{r['doi'].lower()}" if r['doi'] else f"openalex:{r['openalex_id']}", r['oa_title'],
                r['oa_year'], r['oa_type'], r['oa_source'], r['basis'], r['cited_by_dissertations']) for r in cv), report)

    by = Counter((v['source'], v['kind']) for v in works.values())
    report['works_by_source_kind'] = {f'{s}|{k}': n for (s, k), n in sorted(by.items())}
    report['lc_comma_basis_works'] = sum(1 for v in works.values() if v['source'] == 'lc-full'
                                         and v['basis'].split('/')[0] in COMMA)
    report['counts'] = dict(sorted(R.items()))
    report['openalex_rows_removed_by_guards'] = oa_removed
    report['precedence'] = ('LC > Crossref > OpenAlex > Crossref metadata (2026-11-11; fills only works no other crosswalk '
                            'holds, review-like matches dropped) > journal metadata (2026-11-11, same guards) > recent books (2026-11-12, '
                            'Crossref/OpenAlex book records, kind book); OpenAlex DOI replaced by the Crossref DOI where the '
                            'agreement check differs (unless reviewed `openalex`; `both` keeps the OpenAlex DOI as an alias); '
                            'OpenAlex rows after the Crossref guards (part markers, notices, other venue + other year); '
                            'translations and editions (2026-11-11) are applied after the match: the citation goes to the '
                            'canonical work whichever crosswalk matched the cited edition')
    (args.out / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: report[k] for k in ('files', 'corpus', 'openalex_guards_removed', 'counts')}, indent=1))


if __name__ == '__main__':
    main()
