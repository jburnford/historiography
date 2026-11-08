"""Qwen note citations -> read-only match candidates against the graph, for the 49,782 articles of the Fir run
(2026-11-07). These are the articles where the rules left many pieces unparsed, partial or unresolved.

Inputs (E:):
- llm-note-answers/part-*/answers.jsonl (jstor_llm_notes.py on Fir; append-only, so the last ok row per request is kept);
- llm-note-items/part-*.jsonl, for the article, era and journal of each request.

Per article, back-references (ibid / short / author-date) are resolved in note order as in jstor_llm_eval.resolve. A
`work` citation with a title and an author is matched as jstor_match_candidates.py matches the rule rows
(match_citation: every author tried, spaceless titles, online-first article years): the main
title key plus an author family; LC titles for works with an LCCN; basis strong / edition? / no_year / title+year. The
row weight is 1 plus the number of resolved back-references to the citation, as for the rules.

Output (E:, not committed): /mnt/e/jstor-fulltext-2026-11-06/match-candidates-qwen.parquet. Fields are those of
match-candidates.parquet (iid, cit, citing_work, work, work_kind, work_year, cited_kind, cited_year, basis, n_works,
weight, conf, source='qwen') plus `rules_had`: the rule candidates had this (iid, work).

Counts on stdout, including rule edges in these articles that Qwen does not find.

    python3 jstor_llm_note_matches.py
"""
import glob, json, os, sqlite3, sys, time
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jstor_match_candidates as M  # noqa: E402
import jstor_llm_eval as V  # noqa: E402

E = '/mnt/e/jstor-fulltext-2026-11-06'
OUT = f'{E}/match-candidates-qwen.parquet'


def main():
    t0 = time.time()
    idx, doi_work = M.work_index()
    c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
    item_doi = {i.split(':')[-1]: (d or '').lower() for i, d in c.execute('select item_id, doi from records where included')}
    print('work keys', len(idx), round(time.time() - t0), 's', flush=True)
    db = duckdb.connect(); db.execute("SET memory_limit = '3GB'")
    C = Counter(); rows = []; arts = set()
    for part in sorted(glob.glob(f'{E}/llm-note-items/part-*.jsonl')):
        name = os.path.basename(part)[:-6]
        reqs = defaultdict(list)
        for l in open(part, encoding='utf-8'):
            r = json.loads(l)
            reqs[r['iid']].append((r['first'], r['id']))
        ans = {}
        fn = f'{E}/llm-note-answers/{name}/answers.jsonl'
        for l in open(fn, encoding='utf-8'):
            a = json.loads(l)
            if a.get('ok'):
                ans[a['id']] = a['citations']
        for iid, rs in reqs.items():
            arts.add(iid)
            rs.sort()
            cits = []
            for _, rid in rs:
                if rid not in ans:
                    C['requests_failed'] += 1
                    continue
                cits.extend(x for x in ans[rid] if isinstance(x, dict))
            V.resolve(cits)
            weight = Counter(x['ref'] for x in cits if x.get('ref') is not None)
            citing = doi_work.get(item_doi.get(iid, ''))
            for i, x in enumerate(cits):
                C['citations'] += 1
                if x.get('type') != 'work' or x.get('kind') == 'primary':
                    continue
                au = x.get('authors') or []
                if not x.get('title') or not au:
                    continue
                C['work_citations'] += 1
                y = x.get('year') if isinstance(x.get('year'), int) else None
                names = [a for a in au if isinstance(a, str)]
                pick, basis, route, rank = M.match_citation(idx, x['title'], names, y, x.get('kind'))
                if not pick:
                    continue
                C['matched_' + basis] += 1
                C['route_' + route] += 1
                C['later_author'] += bool(rank)
                for key, kind, wy in pick:
                    rows.append((iid, i, citing, key, kind, wy, x.get('kind'), y, basis, len(pick), 1 + weight[i], None, 'qwen', route, rank))
        print(name, len(rows), round(time.time() - t0), 's', flush=True)
    db.execute("""create table q (iid varchar, cit int, citing_work varchar, work varchar, work_kind varchar, work_year int,
                  cited_kind varchar, cited_year int, basis varchar, n_works int, weight int, conf double, source varchar,
                  route varchar, author_rank int)""")
    db.executemany("insert into q values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    db.execute("create table a (iid varchar)"); db.executemany("insert into a values (?)", [(i,) for i in arts])
    db.execute(f"""create table r as select distinct iid::varchar iid, work from '{E}/match-candidates.parquet'
                   where iid::varchar in (select iid from a) and basis in ('strong','title+year') and n_works = 1""")
    db.execute("create table out as select q.*, (q.iid, q.work) in (select (iid, work) from r) rules_had from q")
    db.execute(f"copy out to '{OUT}.tmp' (format parquet)")
    os.replace(OUT + '.tmp', OUT)
    print(json.dumps(dict(C), indent=1))
    print(db.execute("""select basis, count(*) n, count(distinct (iid, work)) pairs, count(*) filter (where n_works = 1) single,
                        count(distinct (iid, work)) filter (where rules_had) rules_had from out group by 1 order by 2 desc""").fetchdf().to_string())
    clean = "basis in ('strong','title+year') and n_works = 1"
    q = db.execute(f"select count(distinct (iid, work)) from out where {clean}").fetchone()[0]
    both = db.execute(f"select count(distinct (iid, work)) from out where {clean} and rules_had").fetchone()[0]
    rr = db.execute("select count(*) from r").fetchone()[0]
    print(f'clean (article, work) pairs in these {len(arts)} articles: rules {rr}, qwen {q}, both {both}, '
          f'qwen only {q - both}, rules only {rr - both}')
    print(round(time.time() - t0), 's')


if __name__ == '__main__':
    main()
