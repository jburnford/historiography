"""Cited works in JSTOR article notes that match no graph work: one row per (title_key, first-author family name),
fields only, with item counts, books first (KG session request, 2026-11-06).

Same citations, keys and graph index as jstor_match_candidates.py; a citation is unmatched when lookup() finds no graph
work ('strong', 'edition?' or 'title+year'). Per key: the most frequent printed title, first author (as parsed,
'Surname, Given'), year, kind, place, publisher and container; the spread of years (other editions); citing items
(distinct JSTOR items), weighted citations (with resolved Ibid./short forms) and mean parser confidence.

Output (E:, not committed): /mnt/e/jstor-fulltext-2026-11-06/unmatched-works.parquet, ordered books first, then by
citing items. Counts on stdout.

    python3 jstor_unmatched_works.py
"""
import gzip, json, os, sys, time
from collections import defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jstor_match_candidates as M  # noqa: E402

E = M.E


def main():
    t0 = time.time()
    idx, _ = M.work_index()
    print('work keys', len(idx), round(time.time() - t0), 's', flush=True)
    tmp = f'{E}/unmatched-cites.jsonl.gz'
    n = 0
    with gzip.open(tmp, 'wt', encoding='utf-8') as o:
        for iid, rows in M.citations():
            weight = defaultdict(int)
            for r in rows:
                if r.get('ref') is not None:
                    weight[r['ref']] += 1
            for i, r in enumerate(rows):
                if r.get('kind') not in M.KINDS or not r.get('title') or not r.get('surnames'):
                    continue
                tk, fam = M.cited_key(r['title']), M.family(r['surnames'][0])
                if not M.usable(tk) or len(fam) < 2 or M.lookup(idx, tk, fam, r.get('year'))[0]:
                    continue
                o.write(json.dumps(dict(tk=tk, fam=fam, iid=iid, title=r['title'][:300], author=(r.get('authors') or r['surnames'])[0],
                                        year=r.get('year'), kind=r['kind'], place=r.get('place'), publisher=r.get('publisher'),
                                        container=r.get('container'), weight=1 + weight[i], conf=r.get('conf'),
                                        source=r.get('source', 'list')), ensure_ascii=False) + '\n')
                n += 1
    print('unmatched citations', n, round(time.time() - t0), 's', flush=True)
    db = duckdb.connect(); db.execute("SET memory_limit = '4GB'"); db.execute("SET preserve_insertion_order = false")
    out = f'{E}/unmatched-works.parquet'
    db.execute(f"""
        copy (
          select tk as title_key, fam as author_family,
                 mode(title) as title, mode(author) as author, mode(year) as year, min(year) as year_min, max(year) as year_max,
                 mode(kind) as kind, mode(place) as place, mode(publisher) as publisher, mode(container) as container,
                 count(distinct iid) as citing_items, sum(weight) as citations, round(avg(conf), 2) as mean_conf,
                 count(*) filter (where source = 'text') as from_text
          from read_json('{tmp}', columns={{tk:'VARCHAR', fam:'VARCHAR', iid:'VARCHAR', title:'VARCHAR', author:'VARCHAR', year:'INTEGER',
                 kind:'VARCHAR', place:'VARCHAR', publisher:'VARCHAR', container:'VARCHAR', weight:'INTEGER', conf:'DOUBLE', source:'VARCHAR'}})
          group by tk, fam
          order by (mode(kind) = 'book') desc, citing_items desc, citations desc
        ) to '{out}.tmp' (format parquet)""")
    os.replace(out + '.tmp', out)
    os.remove(tmp)
    print(db.execute(f"""select kind, count(*) works, count(*) filter (where citing_items >= 2) cited_by_2plus,
                                count(*) filter (where citing_items >= 5) cited_by_5plus, sum(citations) citations
                         from '{out}' group by kind order by works desc""").df().to_string())
    print(round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
