#!/usr/bin/env python3
"""Job A, last step (spark): results.parquet of scripts/crossref_cited_match.py -> crosswalk / held / report and the
hand-check sample (2026-11-17).

  python3 -I crossref_cited_finalize.py sample          writes a/sample.csv (40 exact, 40 strong, 20 weak, seed 17)
  python3 -I crossref_cited_finalize.py export CLASSES  writes a/out/{crosswalk,held}.csv.gz and report.json;
                                                        CLASSES = the classes the hand check admits (e.g. exact,strong)
"""
import json
import sys
import time

import duckdb

W = '/mnt/data/jic823/crossref-work-b/a'
IN = '/mnt/data/jic823/crossref-work-b/in'


def con():
    db = duckdb.connect()
    db.execute(f"set threads=6; set memory_limit='24GB'; set temp_directory='{W}/tmp'")
    db.execute(f"create view r as select * from '{W}/results.parquet'")
    db.execute(f"create view t as select * from '{IN}/targets.parquet'")
    return db


def sample():
    db = con()
    db.execute(f"""copy (
        with s as (select *, row_number() over (partition by cls order by hash(key || 'seed17')) rn from r where margin_ok)
        select cls, key, kind, t_title, t_year, t_families, t_journal, doi, cr_type, cr_title, cr_subtitle, cr_year,
               cr_container, cr_publisher, cfam, tsim, sub, author, year, journal, flags, twins, runner_up, runner_score, score
        from s where (cls='exact' and rn<=40) or (cls='strong' and rn<=40) or (cls='weak' and rn<=20) order by cls, rn)
        to '{W}/sample.csv' (header)""")


def export(classes):
    import os
    db = con()
    os.makedirs(f'{W}/out', exist_ok=True)
    keep = ','.join(f"'{c}'" for c in classes)
    ev = """'tsim=' || tsim || ';subtitle=' || sub || ';author=' || author || coalesce(':' || nullif(fam_hit,''), '')
            || ';year=' || year || coalesce('(' || dy || ')', '') || ';journal=' || journal || ';cr_type=' || cr_type
            || coalesce(';flags=' || nullif(flags, ''), '') || coalesce(';twins=' || nullif(twins, ''), '')"""
    db.execute(f"""copy (select key work, doi, cls class, score, {ev} evidence, cr_year, kind, german
        from r where margin_ok and cls in ({keep}) order by key) to '{W}/out/crosswalk.csv.gz' (header, compression gzip)""")
    db.execute(f"""copy (select key work, doi, cls class, score,
        case when not margin_ok then 'no-margin' else 'class-below-bar' end reason, {ev} evidence,
        runner_up, runner_cls, runner_score, cr_year, kind, german
        from r where not margin_ok or cls not in ({keep}) order by key) to '{W}/out/held.csv.gz' (header, compression gzip)""")
    rep = {}
    rep['targets'] = db.execute('select count(*) from t').fetchone()[0]
    rep['targets_by_kind'] = dict(db.execute('select kind, count(*) from t group by 1').fetchall())
    rep['with_a_token_in_crossref'] = db.execute(f"select count(*) from '{W}/pick.parquet'").fetchone()[0]
    rep['with_candidates'] = db.execute(f"select count(distinct key) from '{W}/cand.parquet'").fetchone()[0]
    rep['scored_any_class'] = db.execute('select count(*) from r').fetchone()[0]
    rep['best_by_class'] = dict(db.execute('select cls, count(*) from r group by 1').fetchall())
    rep['best_by_class_with_margin'] = dict(db.execute('select cls, count(*) from r where margin_ok group by 1').fetchall())
    rep['no_margin_by_class'] = dict(db.execute('select cls, count(*) from r where not margin_ok group by 1').fetchall())
    rep['crosswalk_classes'] = classes
    rep['crosswalk_rows'] = db.execute(f"select count(*) from r where margin_ok and cls in ({keep})").fetchone()[0]
    rep['held_rows'] = db.execute(f"select count(*) from r where not margin_ok or cls not in ({keep})").fetchone()[0]
    rep['crosswalk_by_kind'] = dict(db.execute(f"select kind, count(*) from r where margin_ok and cls in ({keep}) group by 1").fetchall())
    rep['crosswalk_flags'] = dict(db.execute(f"""select coalesce(nullif(flags,''),'none'), count(*) from r
        where margin_ok and cls in ({keep}) group by 1""").fetchall())
    rep['crosswalk_with_twins'] = db.execute(f"select count(*) from r where margin_ok and cls in ({keep}) and twins <> ''").fetchone()[0]
    rep['crosswalk_citations'] = int(db.execute(f"select sum(cited) from r where margin_ok and cls in ({keep})").fetchone()[0] or 0)
    g = db.execute(f"""select count(*), count(*) filter (where key in (select key from r where margin_ok and cls in ({keep}))),
        count(*) filter (where key in (select key from r)) from t where german""").fetchone()
    rep['german'] = dict(targets=g[0], crosswalk=g[1], any_class=g[2], crosswalk_rate=round(g[1] / g[0], 4) if g[0] else None,
                         by_kind={k: [n, m] for k, n, m in db.execute(f"""select kind, count(*), count(*) filter (where key in
                             (select key from r where margin_ok and cls in ({keep}))) from t where german group by 1""").fetchall()})
    nk = {k: [n, m] for k, n, m in db.execute(f"""select kind, count(*), count(*) filter (where key in (select key from r
          where margin_ok and cls in ({keep}))) from t group by 1""").fetchall()}
    rep['rate_by_kind'] = {k: dict(targets=n, crosswalk=m, rate=round(m / n, 4)) for k, (n, m) in nk.items()}
    o = db.execute(f"""select count(distinct r.doi), count(distinct r.doi) filter (where a.orcid is not null)
        from r left join '{W}/cand_auth.parquet' a on a.doi = r.doi and a.role = 'author'
        where r.margin_ok and r.cls in ({keep})""").fetchone()
    rep['crosswalk_dois_with_an_author_orcid'] = dict(dois=o[0], with_orcid=o[1])
    # why unmatched
    rep['unmatched'] = dict(
        no_title_token_in_crossref=rep['targets'] - rep['with_a_token_in_crossref'],
        token_but_no_candidate_of_the_kind=rep['with_a_token_in_crossref'] - rep['with_candidates'],
        candidates_below_every_class=rep['with_candidates'] - rep['scored_any_class'],
        no_margin=sum(rep['no_margin_by_class'].values()),
        class_below_bar=rep['held_rows'] - sum(rep['no_margin_by_class'].values()))
    # diagnostic: unmatched books by year band (Crossref book coverage is mostly recent publishers' backlists)
    rep['books_by_year_band'] = {b: dict(targets=n, crosswalk=m) for b, n, m in db.execute(f"""
        select case when coalesce(first_year, year) < 1950 then 'pre-1950' when coalesce(first_year, year) < 1990 then '1950-1989'
                    when coalesce(first_year, year) < 2010 then '1990-2009' when coalesce(first_year, year) >= 2010 then '2010+' else 'undated' end b,
               count(*), count(*) filter (where key in (select key from r where margin_ok and cls in ({keep})))
        from t where kind='book' group by 1 order by 1""").fetchall()}
    json.dump(rep, open(f'{W}/out/report.json', 'w'), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    if sys.argv[1] == 'sample':
        sample()
    else:
        export(sys.argv[2].split(','))
