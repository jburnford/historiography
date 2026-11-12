"""Preliminary canon comparison: who doctoral theses cite vs who journal articles (JSTOR) cite, 2010-2020
(2026-11-08, read-only from build/graph).

Measure: for each person key, the share of citing items (theses or articles of 2010-2020 with at least one citation
in the graph) that cite at least one work the key authored. Distinct items, not edges.

Groups, so that the national mix of the two corpora is not what is measured:
- theses by country (dissertation-citations-2026-10-11/dissertations.csv, joined on the diss-thesis: anchor):
  `en` = GB, US and English-language Canada; `fr` = France plus the French-language Quebec universities (Laval,
  Montréal, UQAM, Sherbrooke); `br` = Brazil and `mx` = Mexico, which have no matching journal group here;
- articles by journal language, the same lists as the coverage table (fr, it, de, es; otherwise en).

Caveats, preliminary:
- article citations count only when the cited work is a graph work, and graph works come mostly from dissertation
  bibliographies and LC, so the overlap is biased upward;
- person keys are not fully deduplicated; POSSIBLY_SAME edges are ignored.

Output: canon-compare-2010-2020.csv (counts only) beside this script, and a summary on stdout. With --no-editions,
CITES edges with edition = true (a later edition or translation cited) are left out: canon-compare-2010-2020-no-editions.csv.

    python3 canon_compare.py [--no-editions]
"""
import csv, re, sys
from pathlib import Path

import duckdb
import sys
sys.path.insert(0, '/home/jic823/historiography/scripts')
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

G = '/home/jic823/historiography/build/graph'
OUT = Path(__file__).resolve().parent / 'canon-compare-2010-2020.csv'
DISS = '/home/jic823/historiography/data/field-research/dissertation-citations-2026-10-11/dissertations.csv'
FR = ['Revue', 'Annales', 'Vingti', 'Mouvement social', 'Clio. Femmes', '20 & 21', "L'Actualit", 'Etudes d', 'Mélanges', 'Bulletin annuel']
IT = ['Archivio', 'Studi Storici', 'Quaderni']
DE = ['Geschichte und', 'Zeitschrift für', 'Historical Social Research', 'QUANTUM']
ES = ['Historia Social']


def jlang(j):
    for L, ks in (('fr', FR), ('it', IT), ('de', DE), ('es', ES)):
        if j and any(k in j for k in ks):
            return L
    return 'en'


def ilang(inst):
    i = inst or ''
    if re.search(r'Universit[ée] |Université|École|Ecole|Sorbonne|EHESS|Sciences Po', i) and 'Montréal' not in i and 'Laval' not in i and 'Sherbrooke' not in i and 'Québec' not in i:
        return 'fr'
    if re.search(r'Université (de Montréal|Laval|de Sherbrooke|du Québec)', i):
        return 'fr'
    if 'Universidade' in i:
        return 'pt'
    if re.search(r'Universidad|Colegio|Colmex', i):
        return 'es'
    return 'en'


def main():
    editions = '--no-editions' not in sys.argv
    db = duckdb.connect(); db.execute("SET memory_limit = '5GB'")
    # CITES with edition = true: a later edition or translation of the work was cited (KG session, 2026-11-08)
    db.execute(f"""create view cites as select * from '{G}/cites.parquet' {'' if editions else 'where not coalesce(edition, false)'}""")
    print('editions included' if editions else 'editions left out')
    db.create_function('jlang', jlang, ['VARCHAR'], 'VARCHAR')
    db.create_function('ilang', ilang, ['VARCHAR'], 'VARCHAR')
    QC = {'laval', 'montreal', 'uqam', 'sherbrooke', 'uqtr', 'uqac', 'uqar'}
    rows = []
    for r in csv.DictReader(open(DISS)):
        c = r['country']
        g = 'fr' if c == 'FR' or (c == 'CA' and r['institution'] in QC) else 'en' if c in ('GB', 'US', 'CA') else c.lower()
        rows.append(('diss-thesis:' + r['id'], g))
    db.execute("create table dl (anchor varchar, lang varchar)"); db.executemany("insert into dl values (?, ?)", rows)
    db.execute(f"""create table items as
        select w.key, w.kind,
               case when w.kind = 'article' then (case when w.journal is null then 'unknown' else jlang(w.journal) end)
                    else coalesce(min(dl.lang), 'unknown') end lang
        from '{G}/work.parquet' w
        left join (select key, unnest(anchors) an from '{G}/work.parquet' where kind = 'thesis') wa on wa.key = w.key
        left join dl on dl.anchor = wa.an
        where w.kind in ('thesis', 'article') and w.year between 2010 and 2020
          and w.key in (select "from" from cites)
        group by w.key, w.kind, w.journal""")
    print(db.execute("select kind, lang, count(*) from items group by all order by 1, 3 desc").fetchall())
    db.execute(f"""create table hits as
        select distinct it.key item, it.kind, it.lang, au."from" person
        from items it join cites c on c."from" = it.key
        join {keylog(G, 'authored')} au on au."to" = c."to" """)
    db.execute("create table tot as select kind, lang, count(*) n from items group by all")
    db.execute(f"""create table shares as
        select h.kind, h.lang, h.person, p.label, count(*) items, count(*) * 1.0 / any_value(t.n) sh
        from hits h join tot t using (kind, lang) join '{G}/person.parquet' p on p.key = h.person
        group by all""")
    rows = db.execute("""select kind, lang, person, label, items, round(sh, 5) from shares
                         where items >= 3 order by kind, lang, sh desc""").fetchall()
    out = OUT if editions else OUT.with_name(OUT.stem + '-no-editions.csv')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['kind', 'lang', 'person', 'label', 'citing_items', 'share']); w.writerows(rows)
    for lang in ('en', 'fr'):
        print(f'\n=== {lang}: theses vs articles, top 40 by thesis share, with article rank and share ===')
        print(db.execute(f"""
            with t as (select person, label, sh, rank() over (order by sh desc) r from shares where kind='thesis' and lang='{lang}'),
                 a as (select person, sh, rank() over (order by sh desc) r from shares where kind='article' and lang='{lang}')
            select t.r thesis_rank, t.label, round(100*t.sh,1) thesis_pct, a.r article_rank, round(100*a.sh,1) article_pct
            from t left join a using (person) order by t.r limit 40""").fetchdf().to_string(index=False))
        print(f'\n=== {lang}: top 40 by article share, with thesis rank ===')
        print(db.execute(f"""
            with t as (select person, sh, rank() over (order by sh desc) r from shares where kind='thesis' and lang='{lang}'),
                 a as (select person, label, sh, rank() over (order by sh desc) r from shares where kind='article' and lang='{lang}')
            select a.r article_rank, a.label, round(100*a.sh,1) article_pct, t.r thesis_rank, round(100*t.sh,1) thesis_pct
            from a left join t using (person) order by a.r limit 40""").fetchdf().to_string(index=False))
        print(db.execute(f"""
            with t as (select person from shares where kind='thesis' and lang='{lang}' qualify rank() over (order by sh desc) <= 100),
                 a as (select person from shares where kind='article' and lang='{lang}' qualify rank() over (order by sh desc) <= 100)
            select (select count(*) from t where person in (select person from a)) overlap_top100""").fetchall())


if __name__ == '__main__':
    main()
