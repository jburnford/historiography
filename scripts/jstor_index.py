"""Index JSTOR's metadata for matching cited works (2026-11-03).

Input: the JSTOR metadata export kept on E: (jstor_metadata_2026-10-23.jsonl.gz, 1.3 GB, one JSON object per
item; see /mnt/e/JSTOR_history_citation_graph for the history selection). Kept: journal articles, book chapters
and books with a title. Output: one parquet row per item: doi (the ithaka DOI, 10.2307/...), kind (article,
chapter, book), title, main (key_lc_works.title_key of the title before the first colon), whole (title_key of
the whole title), year, container (is_part_of), families (creators' last names, key_cited_works.family_of).

    python3 scripts/jstor_index.py /mnt/e/jstor_metadata_2026-10-23.jsonl.gz /mnt/e/jstor-index.parquet
"""
import subprocess
import sys

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

from key_cited_works import family_of
from key_lc_works import title_key

KIND = {('article', 'Journal'): 'article', ('book_part', 'Book'): 'chapter', ('book', 'Book'): 'book'}
SCHEMA = pa.schema([('doi', pa.string()), ('kind', pa.string()), ('title', pa.string()), ('main', pa.string()),
                    ('whole', pa.string()), ('year', pa.int32()), ('container', pa.string()),
                    ('families', pa.list_(pa.string()))])


def row(o):
    kind = KIND.get((o.get('content_type'), o.get('c5_data_type')))
    title = o.get('title')
    if not kind or not title or not o.get('ithaka_doi'):
        return None
    date = o.get('published_date') or ''
    return dict(doi=o['ithaka_doi'].lower(), kind=kind, title=title[:500], main=title_key(title.split(':')[0]),
                whole=title_key(title), year=int(date[:4]) if date[:4].isdigit() else None,
                container=(o.get('is_part_of') or '')[:300],
                families=sorted({f for c in o.get('creators') or [] if (f := family_of(c.get('last_name') or ''))}))


def main():
    src, dst = sys.argv[1:3]
    writer, batch, n = pq.ParquetWriter(dst, SCHEMA), [], 0
    p = subprocess.Popen(['zcat', src], stdout=subprocess.PIPE, bufsize=1 << 20)
    for line in p.stdout:
        r = row(orjson.loads(line))
        if r:
            batch.append(r)
        if len(batch) >= 200_000:
            writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
            n += len(batch)
            batch = []
            print(n, file=sys.stderr, flush=True)
    if batch:
        writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
        n += len(batch)
    writer.close()
    print(f'{n} JSTOR items -> {dst}')


if __name__ == '__main__':
    main()
