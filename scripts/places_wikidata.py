"""Place layer, step 2: Wikidata facts for the place QIDs, by exact QID joins on QLever (2026-11-18).

No name search: every query is keyed by QID (VALUES). Reads a list of QIDs (one per line) and writes one TSV per
query to OUT (default build/places/wd/, git-ignored; a cache: queries already written are not rerun):
  basic.tsv     label (en), sitelinks, area (normalised m2, max), inception and dissolution years
  aliases.tsv   English aliases
  kinds.tsv     membership in the kind classes below (P31/P279*)
  p131.tsv      direct P131 (located in the administrative territorial entity)
  anc.tsv       P131+ ancestors (the walk is filtered later, in places_build.py)
  p17.tsv       country (P17)
  succ.tsv      P1365 (replaces) and P1366 (replaced by)
  p361.tsv      P361 (part of) and P706 (located in/on physical feature), for regions and features
Period-node predecessors are pulled in a second round (`--preds`) for the territories that need them.

    python3 scripts/places_wikidata.py build/places/qids.csv [--out build/places/wd]
"""
import argparse
import csv
import io
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://qlever.dev/api/wikidata'
UA = 'historiography-places/1.0 (research; single worker)'
PREFIX = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX psn: <http://www.wikidata.org/prop/statement/value-normalized/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""
# kind classes (labels checked on QLever 2026-11-18)
CLASSES = {
    'Q6256': 'country', 'Q3624078': 'sovereign state', 'Q1763527': 'constituent country',
    'Q3024240': 'historical country', 'Q133156': 'colony', 'Q164142': 'protectorate', 'Q19953632': 'former administrative territorial entity',
    'Q1620908': 'historical region', 'Q417175': 'kingdom',
    'Q10864048': 'first-level administrative division', 'Q107390': 'federated state', 'Q56061': 'administrative territorial entity',
    'Q486972': 'human settlement', 'Q515': 'city',
    'Q82794': 'region', 'Q5107': 'continent',
    'Q271669': 'landform', 'Q15324': 'body of water', 'Q23442': 'island', 'Q4022': 'river', 'Q8502': 'mountain',
    'Q46831': 'mountain range', 'Q473972': 'protected area', 'Q839954': 'archaeological site',
    'Q34442': 'road', 'Q83620': 'thoroughfare', 'Q43229': 'organization', 'Q41176': 'building', 'Q811979': 'built structure',
    'Q3918': 'university',
}
QUERIES = {
    'basic': """SELECT ?i (SAMPLE(?l) AS ?label) (SAMPLE(?sl) AS ?sitelinks) (MAX(?ar) AS ?area) (MIN(YEAR(?inc)) AS ?inception)
                (MAX(YEAR(?dis)) AS ?dissolved) WHERE {{ VALUES ?i {{ {v} }}
                OPTIONAL {{ ?i rdfs:label ?l FILTER(lang(?l) = 'en') }} OPTIONAL {{ ?i wikibase:sitelinks ?sl }}
                OPTIONAL {{ ?i p:P2046/psn:P2046/wikibase:quantityAmount ?ar }}
                OPTIONAL {{ ?i wdt:P571 ?inc }} OPTIONAL {{ ?i wdt:P576 ?dis }} }} GROUP BY ?i""",
    'aliases': "SELECT ?i ?a WHERE {{ VALUES ?i {{ {v} }} ?i skos:altLabel ?a FILTER(lang(?a) = 'en') }}",
    'kinds': "SELECT DISTINCT ?i ?c WHERE {{ VALUES ?i {{ {v} }} VALUES ?c {{ " + ' '.join('wd:' + q for q in CLASSES) +
             " }} ?i wdt:P31/wdt:P279* ?c }}",
    'p131': "SELECT ?i ?a WHERE {{ VALUES ?i {{ {v} }} ?i wdt:P131 ?a }}",
    'anc': "SELECT DISTINCT ?i ?a WHERE {{ VALUES ?i {{ {v} }} ?i wdt:P131+ ?a }}",
    'p17': "SELECT ?i ?a WHERE {{ VALUES ?i {{ {v} }} ?i wdt:P17 ?a }}",
    'succ': """SELECT ?i ?rel ?a WHERE {{ VALUES ?i {{ {v} }} {{ ?i wdt:P1365 ?a BIND('replaces' AS ?rel) }} UNION
               {{ ?i wdt:P1366 ?a BIND('replaced_by' AS ?rel) }} }}""",
    'p361': """SELECT ?i ?rel ?a WHERE {{ VALUES ?i {{ {v} }} {{ ?i wdt:P361 ?a BIND('part_of' AS ?rel) }} UNION
               {{ ?i wdt:P706 ?a BIND('on_feature' AS ?rel) }} }}""",
    # peoples, ethnic groups and organisations of peoples (out of scope for the place layer: user 2026-11-18)
    'peoples': """SELECT DISTINCT ?i ?c WHERE {{ VALUES ?i {{ {v} }} VALUES ?c {{ wd:Q41710 wd:Q2472587 wd:Q33829 wd:Q7210356 }}
                  ?i wdt:P31/wdt:P279* ?c }}""",
    # predecessors of a territory (P1365 or inverse P1366, transitive), for period nodes
    'preds': """SELECT DISTINCT ?i ?a WHERE {{ VALUES ?i {{ {v} }} ?i (wdt:P1365|^wdt:P1366)+ ?a }}""",
}


def post(q, timeout=900):
    data = urllib.parse.urlencode({'query': PREFIX + q}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={'Accept': 'text/tab-separated-values', 'User-Agent': UA})
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=timeout).read().decode()
        except Exception as e:      # noqa: BLE001 (network)
            print('  retry', attempt, e)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError('QLever failed')


def clean(v):
    v = v.strip()
    if v.startswith('<http://www.wikidata.org/entity/'):
        return v.rsplit('/', 1)[-1].rstrip('>')
    if v.startswith('"'):
        body = v[1:v.rfind('"')]
        return body.replace('\\"', '"').replace('\\\\', '\\')
    return v


def run(name, qids, out, batch=1500):
    path = out / f'{name}.tsv'
    if path.exists():
        print(name, 'cached')
        return
    rows, header = [], None
    for i in range(0, len(qids), batch):
        v = ' '.join('wd:' + q for q in qids[i:i + batch])
        text = post(QUERIES[name].format(v=v))
        lines = list(csv.reader(io.StringIO(text), delimiter='\t', quoting=csv.QUOTE_NONE))
        header = [h.lstrip('?') for h in lines[0]]
        rows += [[clean(x) for x in r] for r in lines[1:] if r]
        print(f'  {name} {i + batch}/{len(qids)} rows {len(rows)}', flush=True)
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(header)
        w.writerows(rows)
    print(name, len(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('qids')
    ap.add_argument('--out', type=Path, default=ROOT / 'build/places/wd')
    ap.add_argument('--queries', default='basic,aliases,kinds,p131,anc,p17,succ,p361')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    qids = sorted({l.strip() for l in open(args.qids) if l.strip().startswith('Q')})
    print(len(qids), 'QIDs')
    for name in args.queries.split(','):
        run(name, qids, args.out)


if __name__ == '__main__':
    main()
