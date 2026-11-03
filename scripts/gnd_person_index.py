"""Index the GND's person authorities with the identifiers they are sameAs (2026-11-03).

Input: the DNB's CC0 dump authorities-gnd-person_lds.jsonld.gz (data.dnb.de/opendata, 1.4 GB; pretty-printed
expanded JSON-LD, one node per top-level object, two-space indented). Streamed line by line: a node starts at
a two-space `"@id"`, its properties are the two-space keys under it and their values the four-space `@id` /
`@value` lines. Output: gnd-persons.parquet, one row per GND person with an LC or Wikidata sameAs:
- gnd, kind (DifferentiatedPerson, ...), name (preferredNameForThePerson), birth, death;
- lc (id.loc.gov ids, rwo/agents or authorities/names), wd (QIDs), viaf, isni, gnd_alt (older GND ids the
  record is sameAs).

    python3 scripts/gnd_person_index.py /mnt/e/gnd/authorities-gnd-person_lds.jsonld.gz /mnt/e/gnd/gnd-persons.parquet
"""
import gzip
import json
import re
import subprocess
import sys

import pyarrow as pa
import pyarrow.parquet as pq

GND = 'https://d-nb.info/gnd/'
E = 'https://d-nb.info/standards/elementset/gnd#'
PROPS = {'@type': 'type', 'http://www.w3.org/2002/07/owl#sameAs': 'same', E + 'preferredNameForThePerson': 'name',
         E + 'dateOfBirth': 'birth', E + 'dateOfDeath': 'death'}
SAME = [('lc', re.compile(r'^https?://id\.loc\.gov/(?:rwo/agents|authorities/names)/([a-z]+[0-9]+)$')),
        ('wd', re.compile(r'^https?://www\.wikidata\.org/entity/(Q[0-9]+)$')),
        ('viaf', re.compile(r'^https?://viaf\.org/viaf/([0-9]+)$')),
        ('isni', re.compile(r'^https?://isni\.org/isni/([0-9X]{16})$')),
        ('gnd_alt', re.compile(r'^https?://d-nb\.info/gnd/([0-9X-]+)$'))]
SCHEMA = pa.schema([('gnd', pa.string()), ('kind', pa.string()), ('name', pa.string()), ('birth', pa.string()),
                    ('death', pa.string())] + [(s, pa.list_(pa.string())) for s, _ in SAME])
TOP_ID = '  "@id" : "'


def lines(path):
    """Decompress with zcat (several times faster than gzip in Python)."""
    try:
        p = subprocess.Popen(['zcat', path], stdout=subprocess.PIPE, bufsize=1 << 20)
        yield from (l.decode('utf-8') for l in p.stdout)
        p.wait()
    except FileNotFoundError:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            yield from f


def row(node):
    if not node or not node['gnd']:
        return None
    out = dict(gnd=node['gnd'], kind=next((t.rsplit('#', 1)[-1] for t in node.get('type', []) if '#' in t), ''),
               name=(node.get('name') or [''])[0], birth=(node.get('birth') or [''])[0],
               death=(node.get('death') or [''])[0], **{s: [] for s, _ in SAME})
    for u in node.get('same', []):
        for s, rx in SAME:
            m = rx.match(u)
            if m:
                out[s].append(m.group(1))
                break
    out['gnd_alt'] = [g for g in out['gnd_alt'] if g != node['gnd']]
    return out if out['lc'] or out['wd'] else None


def nodes(path):
    node, prop = None, None
    for line in lines(path):
        if line.startswith(TOP_ID):
            yield node
            uri = json.loads(line[9:].rstrip().rstrip(','))
            node, prop = dict(gnd=uri[len(GND):] if uri.startswith(GND) else None), None
        elif node is None or not node['gnd']:
            continue
        elif line.startswith('  "') and not line.startswith('   '):
            key, _, rest = line.strip().partition(' : ')
            prop = PROPS.get(json.loads(key))
            if prop and rest.startswith('[ "'):           # "@type" : [ "...", "..." ],
                node.setdefault(prop, []).extend(json.loads(rest.rstrip(',')))
                prop = None
        elif prop and line.startswith('    "@'):
            key, _, rest = line.strip().partition(' : ')
            if key in ('"@id"', '"@value"'):
                node.setdefault(prop, []).append(json.loads(rest.rstrip(',')))
    yield node


def main():
    src, dst = sys.argv[1:3]
    writer, batch, n = pq.ParquetWriter(dst, SCHEMA), [], 0
    for node in nodes(src):
        r = row(node)
        if r:
            batch.append(r)
        if len(batch) >= 100_000:
            writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
            n += len(batch)
            batch = []
            print(n, file=sys.stderr, flush=True)
    if batch:
        writer.write_table(pa.Table.from_pylist(batch, SCHEMA))
        n += len(batch)
    writer.close()
    print(f'{n} GND persons with LC or Wikidata sameAs -> {dst}')


if __name__ == '__main__':
    main()
