"""Geographic name authorities (MARC 151) from LC's names MADS/RDF dump, with the Wikidata QIDs LC records on them.

Streams one JSON-LD record per line (names.madsrdf.jsonld.gz from id.loc.gov, local copy of 2026-10-30) and keeps
records typed madsrdf:Geographic: id (n...), authoritative label, MARC key, variant labels, QIDs and GeoNames ids
named in madsrdf:identifiesRWO / external-authority links. Also works for subjects.madsrdf.jsonld.gz (LCSH).

    python3 -I lc_geo_authorities.py IN.jsonld.gz OUT.parquet
"""
import gzip
import json
import re
import sys

import pyarrow as pa
import pyarrow.parquet as pq

QID = re.compile(r'wikidata\.org/entity/(Q\d+)')
GEON = re.compile(r'(?:sws\.)?geonames\.org/(\d+)')


def ids(v):
    out = []
    for x in (v if isinstance(v, list) else [v]):
        if isinstance(x, dict):
            x = x.get('@id', '')
        out.append(str(x))
    return out


def plain(v):
    """The romanised value of a MADS literal: a string, a {'@value'} dict, or a list of those where the
    script variants carry an @language tag (zxx-Arab, ...) and the romanised form does not."""
    if isinstance(v, list):
        untagged = [x for x in v if isinstance(x, str) or (isinstance(x, dict) and '@language' not in x)]
        v = (untagged or v)[0] if v else None
    if isinstance(v, dict):
        v = v.get('@value')
    return v


def main():
    src, dst = sys.argv[1], sys.argv[2]
    rows, n = [], 0
    with gzip.open(src, 'rt', encoding='utf-8') as fh:
        for line in fh:
            n += 1
            if 'madsrdf:Geographic' not in line:
                continue
            try:
                g = json.loads(line).get('@graph', [])
            except ValueError:
                continue
            nodes = {x.get('@id'): x for x in g}
            for x in g:
                t = x.get('@type', [])
                t = t if isinstance(t, list) else [t]
                if 'madsrdf:Geographic' not in t or 'madsrdf:Authority' not in t:
                    continue
                links = []
                for k in ('madsrdf:identifiesRWO', 'madsrdf:hasCloseExternalAuthority', 'madsrdf:hasExactExternalAuthority'):
                    links += ids(x.get(k, []))
                variants = []
                for v in ids(x.get('madsrdf:hasVariant', [])):
                    lab = plain(nodes.get(v, {}).get('madsrdf:variantLabel'))
                    if lab:
                        variants.append(str(lab))
                label = plain(x.get('madsrdf:authoritativeLabel'))
                rows.append(dict(id=x['@id'].rsplit('/', 1)[-1], label=str(label or ''), marckey=str(plain(x.get('bflc:marcKey')) or ''),
                                 variants=variants, qids=sorted({m for l in links for m in QID.findall(l)}),
                                 geonames=sorted({m for l in links for m in GEON.findall(l)})))
    pq.write_table(pa.Table.from_pylist(rows), dst, compression='zstd')
    print('lines', n, 'geographic authorities', len(rows), 'with QID', sum(1 for r in rows if r['qids']))


if __name__ == '__main__':
    main()
