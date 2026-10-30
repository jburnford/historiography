"""Index the LC Name Authority File's personal names from the id.loc.gov MADS/RDF bulk dump (PID-PLAN.md section 6).

Input: names.madsrdf.jsonld.gz from https://id.loc.gov/download/ (one JSON-LD record per line).
Output: one Parquet table, one row per personal-name authority:
- lcid (`n79021164`), label (the authorised heading), variants (400 forms);
- birth, death: the person's EDTF dates (madsrdf:birthDate / deathDate on the RWO; MARC 046);
- undifferentiated: in collection_NamesUndifferentiated (one record for several people; never an anchor);
- deprecated, use_instead: cancelled or replaced headings and the heading that replaces them;
- external: other identifiers the record links the person to (ISNI, ORCID, Wikidata, VIAF ...);
- sources: the 670 citations, which name the books the heading was established from;
- changed: the latest record change date.

    python3 scripts/lc_names_index.py /mnt/e/lc-authorities/names.madsrdf.jsonld.gz /mnt/e/lc-authorities/personal-names.parquet
"""
import gzip
import sys
from multiprocessing import Pool
from pathlib import Path

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

BASE = 'http://id.loc.gov'
UNDIFF = 'http://id.loc.gov/authorities/names/collection_NamesUndifferentiated'
SCHEMA = pa.schema([('lcid', pa.string()), ('label', pa.string()), ('variants', pa.list_(pa.string())),
                    ('birth', pa.string()), ('death', pa.string()), ('undifferentiated', pa.bool_()),
                    ('deprecated', pa.bool_()), ('use_instead', pa.list_(pa.string())),
                    ('external', pa.list_(pa.string())), ('sources', pa.list_(pa.string())),
                    ('changed', pa.string())])


def many(v):
    return v if isinstance(v, list) else [] if v is None else [v]


def val(v):
    v = many(v)
    if not v:
        return ''
    v = v[0]
    return v.get('@value', '') if isinstance(v, dict) else str(v)


def ids(v):
    return [x['@id'] for x in many(v) if isinstance(x, dict) and '@id' in x]


def record(line):
    o = orjson.loads(line)
    graph = {n.get('@id'): n for n in o.get('@graph', [])}
    main = graph.get(BASE + o.get('@id', ''))
    if not main:
        return None
    types = set(many(main.get('@type')))
    if 'madsrdf:PersonalName' not in types:
        return None
    deprecated = 'madsrdf:DeprecatedAuthority' in types
    label = val(main.get('madsrdf:authoritativeLabel')) or val(main.get('madsrdf:variantLabel'))
    variants = [val(graph.get(i, {}).get('madsrdf:variantLabel')) for i in ids(main.get('madsrdf:hasVariant'))]
    birth = death = ''
    external = []
    for r in ids(main.get('madsrdf:identifiesRWO')):
        if r.startswith(BASE + '/rwo/'):
            node = graph.get(r, {})
            birth, death = val(node.get('madsrdf:birthDate')), val(node.get('madsrdf:deathDate'))
        else:
            external.append(r)
    external += ids(main.get('madsrdf:hasCloseExternalAuthority')) + ids(main.get('madsrdf:hasExactExternalAuthority'))
    sources = [val(graph.get(i, {}).get('madsrdf:citationSource')) for i in ids(main.get('madsrdf:hasSource'))]
    changed = max((val(graph.get(i, {}).get('ri:recordChangeDate')) for i in ids(main.get('madsrdf:adminMetadata'))),
                  default='')
    use = [u.rsplit('/', 1)[-1] for u in ids(main.get('madsrdf:useInstead'))
           + ids(main.get('madsrdf:hasLaterEstablishedForm'))]
    return dict(lcid=o['@id'].rsplit('/', 1)[-1], label=label, variants=[v for v in variants if v],
                birth=birth, death=death, undifferentiated=UNDIFF in ids(main.get('madsrdf:isMemberOfMADSCollection')),
                deprecated=deprecated, use_instead=use, external=sorted(set(external)),
                sources=[s for s in sources if s], changed=changed)


def batch(lines):
    out, bad = [], 0
    for line in lines:
        if b'PersonalName' not in line:
            continue
        try:
            r = record(line)
        except (orjson.JSONDecodeError, KeyError, TypeError, AttributeError):
            bad += 1
            continue
        if r:
            out.append(r)
    return out, bad


def chunks(path, size=5000):
    buf = []
    with gzip.open(path, 'rb') as f:
        for line in f:
            buf.append(line)
            if len(buf) == size:
                yield buf
                buf = []
    if buf:
        yield buf


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    writer = pq.ParquetWriter(dst, SCHEMA, compression='zstd')
    rows = bad = 0
    with Pool(16) as pool:
        for k, (out, b) in enumerate(pool.imap(batch, chunks(src), chunksize=1), 1):
            bad += b
            if out:
                writer.write_table(pa.Table.from_pylist(out, schema=SCHEMA))
                rows += len(out)
            if k % 200 == 0:
                print(f'{k * 5000:,} records read, {rows:,} personal names, {bad} unparsed', flush=True)
    writer.close()
    print(f'done: {rows:,} personal names, {bad} unparsed -> {dst}', flush=True)


if __name__ == '__main__':
    main()
