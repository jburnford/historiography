"""Read-only match candidates: JSTOR article citations -> existing graph works (deliverable 5, 2026-11-06).

Citations: rule rows on E: (rules/part-*.jsonl.gz, textnotes-rules.jsonl.gz) of kind book, article, chapter, thesis or
periodical with a title and an author. Each full citation carries a weight: 1 + the back-references (Ibid., short
forms, author-date) the parser resolved to it in the same article.
Works: build/graph/work.parquet with authors and editors (authored.parquet, edited.parquet -> person.parquet), read-only;
a work with an LCCN is also keyed by its LC title (/mnt/e/lc-bib-2016 records), since some labels are citation strings.

Match on (title_key, first-author family name), title_key as in build_dissertation_citation_graph (main title,
leading articles dropped). Only titles of 2+ words and 10+ characters. Basis:
  strong     - title + author (or editor) + year within 1 (or no year on the graph work)
  no_year    - title + author, the citation gives no year (main titles can be shared, so weaker than strong)
  edition?   - title + author, years further apart (reprints, translations, later editions)
  title+year - a graph work with no person on it ('Seeing Like a State' without an authored edge): title of 3+ words,
               held by that one work only, year within 1
`n_works` > 1 marks a key shared by several works (duplicates or namesakes): the KG session decides.
The citing JSTOR item is mapped to its own graph work through its DOI where the graph holds it.

Output (E:, not committed): /mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet; counts on stdout.

    python3 jstor_match_candidates.py
"""
import glob, gzip, json, os, re, sqlite3, sys, time
from collections import defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_dissertation_citation_graph import fold, title_key  # noqa: E402
import sys
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

E = '/mnt/e/jstor-fulltext-2026-11-06'
GRAPH = ROOT / 'build/graph'
LC_INDEX = '/mnt/e/lc-bib-2016/index'
KINDS = {'book', 'article', 'chapter', 'thesis', 'periodical'}


def family(label):
    """The last word of the folded family name, the same from either side: 'Von Eschen, Penny M.' (graph),
    'Eschen, Penny M. Von' and 'Penny M. Von Eschen' (notes) are all 'eschen'; 'Bertoloni Meli' is 'meli'."""
    label = re.sub(r',?\s+(?:Jr|Sr|II|III|IV)\.?$', '', (label or '').strip())
    part = label.split(',')[0] if ',' in label else (label.split() or [''])[-1]
    words = fold(part).split()
    return words[-1] if words else ''


CITED_VOLUME = re.compile(r',?\s*\b(?:vol(?:ume)?s?|tome|t|bd|band)\.?\s*(?:[ivxlc]+|\d+)\b.*$', re.I)


# a colon with no space after it still ends the main title ('The urban periphery and the rural fringe:West Ham's hybrid
# landscape'; KG session 2026-11-08); letters on both sides, so 'http://' and '12:3' are left alone
COLON_TIGHT = re.compile(r'(?<=[^\W\d_]):(?=[^\W\d_])')


def tkey(title):
    """title_key with a tight colon opened up: the key for graph labels and cited titles alike."""
    return title_key(COLON_TIGHT.sub(': ', title or ''))


def cited_key(title):
    """title_key of a cited title, with a volume part inside it dropped ('The History of Sexuality, vol. 1, An
    Introduction' -> 'history of sexuality'), as title_key already does for a volume at the end of a graph label."""
    return tkey(CITED_VOLUME.sub('', title or '') or title)


# one-word main titles that name a part or a genre, not a work
ONE_WORD_STOP = {'introduction', 'conclusion', 'conclusions', 'preface', 'foreword', 'epilogue', 'afterword', 'prologue',
                 'commentary', 'correspondence', 'memoirs', 'collected', 'selected', 'documents', 'papers', 'letters',
                 'writings', 'essays', 'history', 'histoire', 'geschichte', 'storia', 'historia', 'review', 'reviews',
                 'bibliography', 'appendix', 'chapter', 'proceedings', 'reports', 'report', 'journal', 'diary', 'notes',
                 'oeuvres', 'werke', 'opere', 'obras', 'works', 'complete', 'editorial', 'introduccion', 'einleitung'}


def usable(tk):
    """Two or more words and 10+ characters; or one word of 7+ letters that is not a part or genre name
    ('orientalism', 'capital', 'distinction', 2026-11-08: one-word titles were never matched). A work is only looked up
    with an author family (and NAMELESS needs 3 words), so a one-word title never matches on its own."""
    words = tk.split()
    if len(words) >= 2:
        return len(tk) >= 10
    return len(words) == 1 and len(tk) >= 7 and tk.isalpha() and tk not in ONE_WORD_STOP


def work_index():
    db = duckdb.connect(); db.execute("SET memory_limit = '4GB'")
    # authors and editors (an edited volume's people are in edited.parquet: 'The Invention of Tradition')
    rows = db.execute(f"""
        with people as (select "to" as work, "from" as person from {keylog(GRAPH, 'authored')}
                        union all select "to", "from" from {keylog(GRAPH, 'edited')})
        select w.key, w.label, w.kind, w.year, list(p.label) filter (where p.label is not null) as names, any_value(w.lccn) as lccn
        from '{GRAPH}/work.parquet' w
        left join people x on x.work = w.key
        left join '{GRAPH}/person.parquet' p on p.key = x.person
        where w.label is not null
        group by w.key, w.label, w.kind, w.year""").fetchall()
    # a work with an LCCN also answers to its LC title: atlas-keyed works carry citation strings as labels
    # ('E. P. Thompson: The Making of ...'), which title_key on the label misses (KG session, 2026-11-06)
    lc = dict(db.execute(f"""
        select trim(r.control), coalesce(r.title_a, r.title) from read_parquet('{LC_INDEX}/records-*.parquet') r
        where trim(r.control) in (select trim(lccn) from '{GRAPH}/work.parquet' where lccn is not null)""").fetchall())
    idx = defaultdict(list)
    nospace = defaultdict(list)    # title key without spaces + family: 'Westham' = 'West Ham' (KG session, 2026-11-08)
    nameless = defaultdict(list)   # works with no person at all ('Seeing Like a State' as w-428793): title + year only
    for key, label, kind, year, names, lccn in rows:
        tks = {tkey(label)}
        if lccn and lc.get(lccn.strip()):
            tks.add(tkey(lc[lccn.strip()]))
        # citation-string labels ('Patrick Wolfe, "Settler Colonialism and the Elimination of the Native," Journal of
        # Genocide Research …'; 'E. P. Thompson: The Making of …'): index the quoted title, and the part after a
        # leading author name (2026-11-08: about 2,400 such works, the canonical articles among them)
        q = QUOTED.search(label)
        if q:
            tks.add(tkey(q.group(1)))
        m = LEAD_NAME.match(label)
        if m and any(family(a) and family(a) in fold(m.group(1)) for a in names or []):
            tks.add(tkey(m.group(2)))
        tks = {tk for tk in tks if usable(tk)}
        if not tks:
            continue
        fams = {family(a) for a in names or [] if a}
        fams = {f for f in fams if len(f) >= 2}
        for tk in tks:
            for fam in fams:
                idx[(tk, fam)].append((key, kind, year))
                nospace[(tk.replace(' ', ''), fam)].append((key, kind, year))
            if not fams and len(tk.split()) >= 3:
                nameless[tk].append((key, kind, year))
    idx[NAMELESS] = nameless
    idx[NOSPACE] = nospace
    doi = dict(db.execute(f"""select lower(substr(a, 5)), key from (select key, unnest(anchors) a from '{GRAPH}/work.parquet')
                              where a like 'doi:%'""").fetchall())
    return idx, doi


QUOTED = re.compile(r'["\u201c\u2018]([^"\u201d\u2019]{8,}?)[,.]?["\u201d\u2019]')
LEAD_NAME = re.compile(r'^([^,:"\u201c]{3,80}?)[,:]\s+(?!\d)(.{8,})$')
NOSPACE = ('', 'nospace')   # slot for the spaceless fallback index
NAMELESS = ('', '')   # slot in the index for the title-only table of works without people


def lookup(idx, tk, fam, year):
    """-> (candidates, basis). Title + author first; a work without people only on title + year within 1, and only
    when that title belongs to one such work."""
    cands = idx.get((tk, fam))
    if cands:
        if not year:   # no year to check: two works can share a main title ('Beyond Kinder, Kueche, Kirche: ...' 1973 / 1976)
            return cands, 'no_year'
        strong = [w for w in cands if not w[2] or abs(w[2] - year) <= 1]
        return (strong, 'strong') if strong else (cands, 'edition?')
    nl = idx[NAMELESS].get(tk, [])
    if len(nl) == 1 and year and nl[0][2] and abs(nl[0][2] - year) <= 1:
        return nl, 'title+year'
    return [], None


def match_citation(idx, title, surnames, year, cited_kind):
    """-> (candidates, basis, route, family_rank). The rules for both the rule rows and the Qwen citations:
    - every cited author's family is tried in order, the first hit kept (KG session, 2026-11-08: 'Maitland's Moment'
      cited as Burns, Clifford, Peace; the graph work has Clifford only); family_rank is the 0-based position used;
    - no hit on the title key: the same key without spaces, with a family and the year within 1 ('Westham' / 'West
      Ham'): basis strong, route 'nospace';
    - a journal piece (cited as article, chapter or periodical) cited 1-2 years after a graph article's (or ORCID
      'other' work's) year is the print issue of an online-first article ('Soap and ghost acres': ORCID 2019, cited
      2021): basis strong, route 'online_first'. Books keep 'edition?'."""
    tk = cited_key(title)
    if not usable(tk):
        return [], None, None, None
    fams = list(dict.fromkeys(f for f in (family(a) for a in surnames or []) if len(f) >= 2))
    pick, basis, rank = [], None, None
    for n, fam in enumerate(fams or ['\0']):
        pick, basis = lookup(idx, tk, fam, year)
        if pick:
            rank = n
            break
    if not pick:
        if year:
            ns = tk.replace(' ', '')
            for n, fam in enumerate(fams):
                c = [w for w in idx[NOSPACE].get((ns, fam), []) if w[2] and abs(w[2] - year) <= 1]
                if c:
                    return c, 'strong', 'nospace', n
        return [], None, None, None
    if basis == 'edition?' and cited_kind in ('article', 'chapter', 'periodical') and year:
        # the rule parser often calls a journal article 'chapter' ('…', Social Science History 45); ORCID-keyed
        # articles are kind 'other'. Books never: a book cited later is an edition.
        p2 = [w for w in pick if w[1] in ('article', 'other') and w[2] and 1 <= year - w[2] <= 2]
        if p2:
            return p2, 'strong', 'online_first', rank
    return pick, basis, 'title', rank


DOI_RE = re.compile(r'\b10\.\d{4,9}/[^\s"<>]+', re.I)


def note_dois():
    """(iid, doi) for every distinct DOI printed in an item's notes: the JSTOR note lists and the notes cut from page
    text. Trailing punctuation is dropped."""
    for fn, field in ((f'{E}/references.jsonl.gz', 'references'), (f'{E}/textnotes-pieces.jsonl.gz', 'pieces')):
        if not os.path.exists(fn):
            continue
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            for line in f:
                if '10.' not in line:
                    continue
                r = json.loads(line)
                seen = set()
                for p in r[field]:
                    for m in DOI_RE.finditer(p if isinstance(p, str) else json.dumps(p)):
                        d = m.group().rstrip('.,;:)]}\'').lower()
                        if d not in seen:
                            seen.add(d)
                            yield r['iid'], d


def citations():
    files = sorted(glob.glob(f'{E}/rules/part-*.jsonl.gz')) + [f for f in [f'{E}/textnotes-rules.jsonl.gz'] if os.path.exists(f)]
    for fn in files:
        cur, rows = None, []
        with gzip.open(fn, 'rt', encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r['iid'] != cur:
                    if rows:
                        yield cur, rows
                    cur, rows = r['iid'], []
                rows.append(r)
        if rows:
            yield cur, rows


def main():
    t0 = time.time()
    idx, doi_work = work_index()
    print('work keys', len(idx), 'doi anchors', len(doi_work), round(time.time() - t0), 's', flush=True)
    c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
    item_doi = {i.split(':')[-1]: (d or '').lower() for i, d in c.execute('select item_id, doi from records where included')}
    out = f'{E}/match-candidates.jsonl.gz'
    stats = defaultdict(int)
    with gzip.open(out + '.tmp', 'wt', encoding='utf-8') as o:
        for iid, rows in citations():
            weight = defaultdict(int)
            for r in rows:
                if r.get('ref') is not None:
                    weight[r['ref']] += 1
            citing = doi_work.get(item_doi.get(iid, ''))
            for i, r in enumerate(rows):
                if r.get('kind') not in KINDS or not r.get('title') or not r.get('surnames'):
                    continue
                stats['citations'] += 1
                y = r.get('year')
                pick, basis, route, rank = match_citation(idx, r['title'], r['surnames'], y, r['kind'])
                if not pick:
                    continue
                stats['matched_' + basis] += 1
                stats['route_' + route] += 1
                if rank:
                    stats['later_author'] += 1
                    stats['later_author_ambiguous'] += len(pick) > 1
                for key, kind, wy in pick:
                    o.write(json.dumps(dict(iid=iid, cit=i, citing_work=citing, work=key, work_kind=kind, work_year=wy,
                                            cited_kind=r['kind'], cited_year=y, basis=basis, n_works=len(pick),
                                            weight=1 + weight[i], conf=r.get('conf'), source=r.get('source', 'list'),
                                            route=route, author_rank=rank)) + '\n')
        # DOIs printed in the notes (user, 2026-11-08: recent notes carry them; a route where they exist, not the base)
        for iid, doi in note_dois():
            w = doi_work.get(doi)
            if not w or doi == item_doi.get(iid):
                continue
            stats['route_doi'] += 1
            o.write(json.dumps(dict(iid=iid, cit=None, citing_work=doi_work.get(item_doi.get(iid, '')), work=w,
                                    work_kind=None, work_year=None, cited_kind=None, cited_year=None, basis='doi',
                                    n_works=1, weight=1, conf=None, source='doi', route='doi', author_rank=None)) + '\n')
    os.replace(out + '.tmp', out)
    db = duckdb.connect()
    db.execute(f"copy (select * from read_json_auto('{out}', sample_size=-1)) to '{E}/match-candidates.parquet.tmp' (format parquet)")
    os.replace(f'{E}/match-candidates.parquet.tmp', f'{E}/match-candidates.parquet')
    s = db.execute(f"""select count(*), count(distinct work), count(distinct iid), sum(weight),
                         count(*) filter (where n_works = 1), count(distinct iid) filter (where citing_work is not null)
                       from '{E}/match-candidates.parquet'""").fetchone()
    print(json.dumps(dict(stats), indent=1))
    print(f'candidate rows {s[0]}, distinct works {s[1]}, citing items {s[2]}, weighted citations {s[3]}, '
          f'unique-work rows {s[4]}, citing items with a graph work {s[5]}; {round(time.time() - t0)} s')


if __name__ == '__main__':
    main()
