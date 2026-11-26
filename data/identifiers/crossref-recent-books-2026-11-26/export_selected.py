"""Spark, last step of the recent-books round (2026-11-26): the metadata of the books that pass at least one route at
its loosest (an ORCID on one person key; one citing history-slice record; a review pair that is not refused), with
their records (alternates) and contributors, and the review pairs with their review records. Metadata only; these
files come back to the round folder as CSV.

    python -I export_selected.py OUT
"""
import sys
import duckdb

OUT = sys.argv[1]
c = duckdb.connect(f'{OUT}/work.duckdb', read_only=True)
c.execute("SET threads=12; SET memory_limit='24GB'")
REFUSED = ("'book has no known author'", "'dated before the book'", "'dated more than eight years after the book'",
           "'record author shares a family name with the book'", "'printed author is not the book author'")
c.execute(f"""CREATE TEMP TABLE pairs AS SELECT * FROM '{OUT}/review-pairs.parquet'
              WHERE reason IS NULL OR reason NOT IN ({', '.join(REFUSED)})""")
c.execute(f"""CREATE TEMP TABLE sel AS SELECT * FROM '{OUT}/books.parquet' b WHERE excluded IS NULL AND
              (len(orcid_keys) > 0 OR cites > 0 OR cluster IN (SELECT cluster FROM pairs)
               OR cluster IN (SELECT unnest(twin_clusters) FROM pairs))""")
c.execute(f"""COPY (SELECT cluster, rep, year, rep_year, n_records, shared, cites, orcid_history,
                    array_to_string(orcid_keys, ';') orcid_keys, array_to_string(fams, ';') fams,
                    array_to_string(isbns, ';') isbns FROM sel) TO '{OUT}/x-books.csv.gz' (HEADER, COMPRESSION gzip)""")
c.execute(f"""COPY (SELECT r.cluster, r.doi, r.type, r.title, r.subtitle, r.publisher, r.prefix, r.year,
                    array_to_string(r.isbns, ';') isbns FROM '{OUT}/records.parquet' r SEMI JOIN sel USING (cluster))
              TO '{OUT}/x-records.csv.gz' (HEADER, COMPRESSION gzip)""")
c.execute(f"""COPY (SELECT lower(a.doi) doi, a.role, a.seq, a.given, a.family, a.name, a.orcid FROM cba a
                    WHERE lower(a.doi) IN (SELECT doi FROM '{OUT}/records.parquet' r SEMI JOIN sel USING (cluster))
                    ORDER BY 1, 2, 3) TO '{OUT}/x-contributors.csv.gz' (HEADER, COMPRESSION gzip)""")
c.execute(f"""COPY (SELECT doi, seg, cluster, eq, how, stratum, printed_names, review_year, book_year, title_words, shared,
                    fam_in_title, fam_in_names, reason, array_to_string(twin_clusters, ';') twin_clusters FROM pairs)
              TO '{OUT}/x-review-pairs.csv.gz' (HEADER, COMPRESSION gzip)""")
c.execute(f"""COPY (SELECT doi, title, subtitle, container, issn, year, type, page, publisher,
                    array_to_string(list_transform(people, lambda p: trim(coalesce(p.given, '') || ' ' || coalesce(p.family, p.name, ''))), '; ') reviewers,
                    array_to_string(list_filter(list_transform(people, lambda p: regexp_extract(coalesce(p.orcid, ''), '([0-9X-]{{19}})$', 1)), lambda x: x <> ''), '; ') orcids
                    FROM '{OUT}/review-records.parquet') TO '{OUT}/x-review-records.csv.gz' (HEADER, COMPRESSION gzip)""")
for t in ('books', 'records', 'contributors', 'review-pairs', 'review-records'):
    print(t, c.execute(f"SELECT count(*) FROM '{OUT}/x-{t}.csv.gz'").fetchone()[0])
