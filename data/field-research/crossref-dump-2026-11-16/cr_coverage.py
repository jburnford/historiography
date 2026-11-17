import duckdb, sys
P="/mnt/data/jic823/crossref-2026-parquet"; T="/mnt/data/jic823/tools/crossref-extract"
c=duckdb.connect(); c.sql("set threads=12; set memory_limit='48GB'")
c.sql(f"""create table g as select replace(upper(issn),'-','') i, any_value(journal) gj, sum(held) held, sum(held_citing) held_citing,
          sum(held_post2020) held_post2020 from '{T}/graph-issn.csv' group by 1""")
c.sql(f"""create table j as
 with w as (select *, replace(upper(split_part(issn,' ',1)),'-','') i1, replace(upper(split_part(issn,' ',2)),'-','') i2
            from '{P}/works/*.parquet' where type='journal-article' and issn is not null)
 select i1, mode(container) journal, any_value(publisher) publisher, any_value(nullif(i2,'')) i2,
   count(*) articles, min(year) y0, max(year) y1,
   count(*) filter (where n_refs>0) with_refs, sum(n_refs) refs,
   count(*) filter (where year>2020) post2020, count(*) filter (where year>2020 and n_refs>0) post2020_with_refs,
   count(*) filter (where year between 2000 and 2020) y2000_20, count(*) filter (where year between 2000 and 2020 and n_refs>0) y2000_20_with_refs,
   count(*) filter (where year<2000) pre2000, count(*) filter (where year<2000 and n_refs>0) pre2000_with_refs
 from w group by 1""")
c.sql("""create table h as select j.*, coalesce(g1.gj,g2.gj) graph_journal, coalesce(g1.held,g2.held,0) held,
   coalesce(g1.held_citing,g2.held_citing,0) held_citing
 from j left join g g1 on g1.i=j.i1 left join g g2 on g2.i=j.i2
 where regexp_matches(lower(j.journal),'histor|histoi|geschicht|storia|storic|past (&|and) present|annales|speculum|isis|medieval|mediev|antiquity|ancient|byzant|renaissance|early modern|victorian|eighteenth|slavic review|william and mary')
    or coalesce(g1.held,g2.held,0)>=100""")
c.sql(f"copy (select * from h order by articles desc) to '{T}/journal-coverage.csv' (header)")
print(c.sql("select count(*) journals, sum(articles) articles, sum(with_refs) with_refs, sum(refs) refs, sum(held) held, sum(held_citing) held_citing from h"))
print(c.sql("select count(*) journals, sum(articles) articles, sum(with_refs) with_refs, sum(refs) refs from h where regexp_matches(lower(journal),'histor|histoi|geschicht|storia')"))
