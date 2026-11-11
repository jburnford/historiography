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

    python3 scripts/export_cited_works.py
"""
import argparse
import csv
import gzip
import json
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
LINKS = IDS / 'cited-work-authors-2026-11-10/links.csv.gz'
OLD = [IDS / 'cited-works-2026-11-04/crosswalk.csv.gz', IDS / 'cited-articles-2026-11-03b/crosswalk.csv.gz',
       IDS / 'cited-own-works-2026-11-03f/crosswalk.csv.gz']
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
OUT = ROOT / 'data/graph/cited-works'
SCRATCH = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/integrate')
MAX_BYTES = 50_000_000
COMMA = ('lc-comma', 'corpus-comma', 'both-comma')     # LC title forms audited at ~97% (the rest 99%)


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
        return ({'lc-full': 0, 'crossref': 1, 'openalex': 2}[c['source']], c['year'] or 9999, c['ids'][0])
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

    # ---- citations --------------------------------------------------------------------------------------------
    old = set()
    for p in OLD:
        old.update(r['work_id'] for r in rd(p))
    R['old_crosswalk_works'] = len(old)
    R['new_works_also_in_old_crosswalks'] = len(old & set(cid))
    pairs = {}
    corpus_rows = matched_old = matched_new = matched_any = 0
    per_source_rows = Counter()
    for r in rd(CORPUS / 'strict-citations.csv.gz'):
        corpus_rows += 1
        w = r['work_id']
        o, n = w in old, w in cid
        matched_old += o
        matched_new += n and not o
        matched_any += o or n
        if n and not o:
            c = chosen[w]
            per_source_rows[c['source']] += 1
            key = (r['dissertation_id'], cid[w])
            if key not in pairs:
                pairs[key] = (c['source'], c['basis'])
            works[cid[w]]['theses'].add(r['dissertation_id'])
    R['cites_pairs'] = len(pairs)
    report['corpus'] = dict(citations=corpus_rows, matched_before=matched_old, matched_new=matched_new,
                            matched_after=matched_any, rate_before=round(matched_old / corpus_rows, 4),
                            rate_after=round(matched_any / corpus_rows, 4), new_citations_by_source=dict(per_source_rows),
                            note='citations = rows of strict-citations.csv.gz (dissertation, cited corpus work); before = '
                                 'the three older crosswalks behind data/graph/cites.csv.gz; after = those or this table')
    write_csv(args.out / 'cites.csv.gz', ['dissertation_id', 'work', 'source', 'basis'],
              ((d, w, s, b) for (d, w), (s, b) in sorted(pairs.items())), report)
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
    report['precedence'] = ('LC > Crossref > OpenAlex; OpenAlex DOI replaced by the Crossref DOI where the agreement check '
                            'differs (unless reviewed `openalex`; `both` keeps the OpenAlex DOI as an alias); OpenAlex rows '
                            'after the Crossref guards (part markers, notices, other venue + other year)')
    (args.out / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: report[k] for k in ('files', 'corpus', 'openalex_guards_removed', 'counts')}, indent=1))


if __name__ == '__main__':
    main()
