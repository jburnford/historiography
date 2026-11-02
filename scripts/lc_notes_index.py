"""Index what LC's name authorities say about people's careers, from the id.loc.gov MADS/RDF bulk dump (2026-11-02).

Companion to scripts/lc_names_index.py (whose table every LC route reads; it is left as it is). Two tables:
- personal-notes.parquet, one row per personal-name authority with any of:
  - notes: the 670 citations with the data found ('source :: note'; e.g. 'Wikipedia ... :: was Sterling
    Professor of History at Yale University from 1993 to 2008', 'His diss. ... :: Thesis (Ph.D.)--Yale');
  - affiliations: MARC 373 (madsrdf:hasAffiliation on the RWO): organisation id, start, end;
  - fields: MARC 372 fields of activity (labels, or ids where the value is a link);
- organisations.parquet: id -> authorised label for every corporate-name authority (373 links point to them).

    python3 scripts/lc_notes_index.py /mnt/e/lc-authorities/names.madsrdf.jsonld.gz /mnt/e/lc-authorities
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

from lc_names_index import BASE, chunks, ids, many, val

NOTES = pa.schema([('lcid', pa.string()), ('notes', pa.list_(pa.string())),
                   ('affiliations', pa.list_(pa.struct([('org', pa.string()), ('start', pa.string()), ('end', pa.string())]))),
                   ('fields', pa.list_(pa.string()))])
ORGS = pa.schema([('id', pa.string()), ('label', pa.string())])


def record(line):
    o = orjson.loads(line)
    graph = {n.get('@id'): n for n in o.get('@graph', [])}
    main = graph.get(BASE + o.get('@id', ''))
    if not main:
        return None, None
    types = set(many(main.get('@type')))
    lcid = o['@id'].rsplit('/', 1)[-1]
    if 'madsrdf:CorporateName' in types:
        return None, dict(id=lcid, label=val(main.get('madsrdf:authoritativeLabel')) or val(main.get('madsrdf:variantLabel')))
    if 'madsrdf:PersonalName' not in types:
        return None, None
    notes = []
    for i in ids(main.get('madsrdf:hasSource')):
        s = graph.get(i, {})
        note = val(s.get('madsrdf:citationNote'))
        if note:
            src = ' / '.join(x if isinstance(x, str) else x.get('@id', '') for x in many(s.get('madsrdf:citationSource')))
            notes.append(f'{src} :: {note}')
    affiliations, fields = [], []
    for r in ids(main.get('madsrdf:identifiesRWO')):
        node = graph.get(r, {})
        for a in ids(node.get('madsrdf:hasAffiliation')):
            a = graph.get(a, {})
            org = ids(a.get('madsrdf:organization'))
            if org:
                affiliations.append(dict(org=org[0].rsplit('/', 1)[-1], start=val(a.get('madsrdf:affiliationStart')),
                                         end=val(a.get('madsrdf:affiliationEnd'))))
        for f in many(node.get('madsrdf:fieldOfActivity')):
            n = graph.get(f.get('@id'), f) if isinstance(f, dict) else {}
            label = val(n.get('rdfs:label')) or val(n.get('madsrdf:authoritativeLabel'))
            fields.append(label or (n.get('@id', '') if not n.get('@id', '').startswith('_:') else ''))
    if not (notes or affiliations or fields):
        return None, None
    return dict(lcid=lcid, notes=notes, affiliations=affiliations, fields=[f for f in fields if f]), None


def batch(lines):
    people, orgs = [], []
    for line in lines:
        if b'PersonalName' not in line and b'CorporateName' not in line:
            continue
        try:
            p, c = record(line)
        except (orjson.JSONDecodeError, KeyError, TypeError, AttributeError):
            continue
        if p:
            people.append(p)
        if c and c['label']:
            orgs.append(c)
    return people, orgs


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    pw = pq.ParquetWriter(out / 'personal-notes.parquet', NOTES, compression='zstd')
    ow = pq.ParquetWriter(out / 'organisations.parquet', ORGS, compression='zstd')
    n_people = n_orgs = 0
    with Pool(12) as pool:
        for k, (people, orgs) in enumerate(pool.imap(batch, chunks(src), chunksize=1), 1):
            if people:
                pw.write_table(pa.Table.from_pylist(people, schema=NOTES))
                n_people += len(people)
            if orgs:
                ow.write_table(pa.Table.from_pylist(orgs, schema=ORGS))
                n_orgs += len(orgs)
            if k % 200 == 0:
                print(f'{k * 5000:,} records read, {n_people:,} people with notes, {n_orgs:,} organisations', flush=True)
    pw.close()
    ow.close()
    print(f'done: {n_people:,} people with notes, {n_orgs:,} organisations', flush=True)


if __name__ == '__main__':
    main()
