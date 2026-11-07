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


def cited_key(title):
    """title_key of a cited title, with a volume part inside it dropped ('The History of Sexuality, vol. 1, An
    Introduction' -> 'history of sexuality'), as title_key already does for a volume at the end of a graph label."""
    return title_key(CITED_VOLUME.sub('', title or '') or title)


def usable(tk):
    return len(tk) >= 10 and len(tk.split()) >= 2


def work_index():
    db = duckdb.connect(); db.execute("SET memory_limit = '4GB'")
    # authors and editors (an edited volume's people are in edited.parquet: 'The Invention of Tradition')
    rows = db.execute(f"""
        with people as (select "to" as work, "from" as person from '{GRAPH}/authored.parquet'
                        union all select "to", "from" from '{GRAPH}/edited.parquet')
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
    nameless = defaultdict(list)   # works with no person at all ('Seeing Like a State' as w-428793): title + year only
    for key, label, kind, year, names, lccn in rows:
        tks = {title_key(label)}
        if lccn and lc.get(lccn.strip()):
            tks.add(title_key(lc[lccn.strip()]))
        tks = {tk for tk in tks if usable(tk)}
        if not tks:
            continue
        fams = {family(a) for a in names or [] if a}
        fams = {f for f in fams if len(f) >= 2}
        for tk in tks:
            for fam in fams:
                idx[(tk, fam)].append((key, kind, year))
            if not fams and len(tk.split()) >= 3:
                nameless[tk].append((key, kind, year))
    idx[NAMELESS] = nameless
    doi = dict(db.execute(f"""select lower(substr(a, 5)), key from (select key, unnest(anchors) a from '{GRAPH}/work.parquet')
                              where a like 'doi:%'""").fetchall())
    return idx, doi


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
                tk, fam = cited_key(r['title']), family(r['surnames'][0])
                if not usable(tk) or len(fam) < 2:
                    stats['too_short'] += 1
                    continue
                y = r.get('year')
                pick, basis = lookup(idx, tk, fam, y)
                if not pick:
                    continue
                stats['matched_' + basis] += 1
                for key, kind, wy in pick:
                    o.write(json.dumps(dict(iid=iid, cit=i, citing_work=citing, work=key, work_kind=kind, work_year=wy,
                                            cited_kind=r['kind'], cited_year=y, basis=basis, n_works=len(pick),
                                            weight=1 + weight[i], conf=r.get('conf'), source=r.get('source', 'list'))) + '\n')
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
