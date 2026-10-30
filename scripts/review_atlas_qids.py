"""Systematic review of the atlas people's Wikidata QIDs (data/people-wikidata.json).

Read-only against the sheet. For every accepted QID it fetches, from the Wikidata Query Service: labels
and aliases in all languages, English description, instance-of, birth/death, occupations, sitelink
count and redirect status. Each person gets mechanical checks plus independent evidence:
- dissertation graph: the QID the dissertation grounding chose for the same person, through the canon-map
  key joins (`diss-person:` anchors in data/identifiers) or an exact name-key candidate in cited-people.csv;
- person registry v12: a QID reached from an ORCID that the registry ties to this atlas person.

Verdicts:
- `wrong`: the item is missing or not a human, or the name is incompatible;
- `suspect`: an independent route disagrees, the occupations are all unscholarly, or the dates are
  impossible for someone cited in the atlas;
- `confirmed`: the name is compatible and an independent route agrees, or the QID was individually
  reviewed;
- `plausible`: the name is compatible, the item is human, and nothing disagrees, but there is no
  independent confirmation.

    python3 scripts/review_atlas_qids.py --out data/field-research/atlas-qid-review-2026-10-30
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import State
from identity_routes import fold, tokens

ROOT = Path(__file__).resolve().parents[1]
WDQS = 'https://query.wikidata.org/sparql'
UA = 'HistoriographyResearch/1.0 (jic823@usask.ca; atlas QID review)'
SHEET = ROOT / 'data/people-wikidata.json'
CITED = ROOT / 'data/field-research/dissertation-citations-2026-10-11/cited-people.csv'
REGISTRY = ROOT / 'data/person-registry/generated/v12/registry.duckdb'
REVIEWED_METHODS = {None, 'reviewed_mcp', 'roster_orcid_corroborated_2026-09-26', 'qid_review_2026-10-30'}
SCHOLARLY = re.compile(r'histor|scholar|professor|academic|lecturer|teacher|researcher|philosoph|sociolog|anthropolog|'
                       r'economi|geograph|archaeolog|politic(al)? scien|theorist|critic|writer|author|journalist|essayist|'
                       r'librarian|archivist|editor|linguist|psycholog|psychoanalys|theolog|classicist|demograph|'
                       r'scientist|jurist|lawyer|educator|folklor|ethnolog|museum|curator|novelist|poet|biograph|'
                       r'translator|feminist|activist|orientalist|sinolog|egyptolog|byzantin|medievalist|musicolog|'
                       r'art histor|statistician|mathematic|physician|engineer|diplomat|politician|civil servant|'
                       r'priest|minister|rabbi|clergy|missionary|anarchist|revolutionary|trade unionist|organizer')


def sparql(query, cache, name):
    path = cache / f'{name}.json'
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(5):
        req = urllib.request.Request(WDQS + '?' + urllib.parse.urlencode({'query': query, 'format': 'json'}),
                                     headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                rows = json.load(r)['results']['bindings']
            path.write_text(json.dumps(rows))
            time.sleep(1.5)
            return rows
        except Exception as e:  # WDQS throttles with 429/503; back off and retry
            print(f'  {name}: {e}; retry {attempt + 1}', flush=True)
            time.sleep(15 * (attempt + 1))
    raise SystemExit(f'WDQS failed for {name}')


def fetch(qids, cache):
    cache.mkdir(parents=True, exist_ok=True)
    info = {q: dict(labels=set(), desc='', p31=set(), birth=set(), death=set(), occ=set(), sitelinks=0, redirect='',
                    exists=False) for q in qids}
    qids = sorted(qids)
    for i in range(0, len(qids), 100):
        chunk = qids[i:i + 100]
        values = ' '.join(f'wd:{q}' for q in chunk)
        part = hashlib.sha1(values.encode()).hexdigest()[:12]     # cache by content, not position
        for row in sparql(f"""SELECT ?q ?target WHERE {{ VALUES ?q {{ {values} }} ?q owl:sameAs ?target }}""", cache, f'redirect-{part}'):
            info[row['q']['value'].rsplit('/', 1)[1]]['redirect'] = row['target']['value'].rsplit('/', 1)[1]
        for row in sparql(f"""SELECT ?q ?l WHERE {{ VALUES ?q {{ {values} }} {{ ?q rdfs:label ?l }} UNION {{ ?q skos:altLabel ?l }} }}""",
                          cache, f'labels-{part}'):
            info[row['q']['value'].rsplit('/', 1)[1]]['labels'].add(row['l']['value'])
            info[row['q']['value'].rsplit('/', 1)[1]]['exists'] = True
        for row in sparql(f"""SELECT ?q ?desc ?links ?p31 ?b ?d ?occL WHERE {{ VALUES ?q {{ {values} }}
              OPTIONAL {{ ?q schema:description ?desc FILTER(lang(?desc) = "en") }}
              OPTIONAL {{ ?q wikibase:sitelinks ?links }}
              OPTIONAL {{ ?q wdt:P31 ?p31 }}
              OPTIONAL {{ ?q wdt:P569 ?b }} OPTIONAL {{ ?q wdt:P570 ?d }}
              OPTIONAL {{ ?q wdt:P106 ?occ . ?occ rdfs:label ?occL FILTER(lang(?occL) = "en") }} }}""", cache, f'facts-{part}'):
            r = info[row['q']['value'].rsplit('/', 1)[1]]
            r['desc'] = row.get('desc', {}).get('value', r['desc'])
            r['sitelinks'] = int(row.get('links', {}).get('value', r['sitelinks']))
            for k, f in (('p31', 'p31'), ('birth', 'b'), ('death', 'd'), ('occ', 'occL')):
                if f in row:
                    r[k].add(row[f]['value'].rsplit('/', 1)[-1] if k == 'p31' else row[f]['value'][:10] if k in ('birth', 'death') else row[f]['value'])
    return info


def name_compatible(atlas_label, labels):
    """Some label or alias carries the atlas surname, and the first given names agree (or initials do)."""
    atlas_label = re.sub(r'\s*\(.*?\)|\s+/.*$', '', atlas_label)    # 'Hayden White / narrative theory'
    a = tokens(atlas_label)
    if not a:
        return False
    surname, given = a[-1], a[:-1]
    for lab in labels:
        t = tokens(lab)
        if surname not in t and fold(atlas_label) != fold(lab):
            continue
        rest = [x for x in t if x != surname]
        if not given or not rest or fold(atlas_label) == fold(lab):
            return True
        if given[0] == rest[0] or (len(given[0]) == 1 and rest[0][0] == given[0]) or (len(rest[0]) == 1 and given[0][0] == rest[0]):
            return True
    return False


def independent(sheet_people):
    """atlas person id -> {source: qid} from the dissertation graph and the registry."""
    out = defaultdict(dict)
    log = ROOT / 'data/identifiers/events.jsonl'
    if log.exists():
        state = State.load(log)
        diss_key = defaultdict(list)
        for key, rec in state.keys.items():
            atlas = [a[len('atlas:person:'):] for a in rec['anchors'] if a.startswith('atlas:person:')]
            diss = [a[len('diss-person:'):] for a in rec['anchors'] if a.startswith('diss-person:')]
            for p in atlas:
                diss_key[p] += diss
    else:
        diss_key = {}
    cited = {}
    with CITED.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['qid'] and (r['atlas_person_candidate'] or True):
                cited[r['person_key']] = (r['qid'], r['qid_basis'], r['atlas_person_candidate'])
    by_candidate = defaultdict(list)
    for k, (q, basis, cand) in cited.items():
        if cand:
            by_candidate[cand].append((k, q, basis))
    for pid in sheet_people:
        for k in diss_key.get(pid, []):
            if k in cited:
                out[pid]['dissertation_joined'] = cited[k][0]
        cands = by_candidate.get(pid, [])
        if len(cands) == 1 and 'dissertation_joined' not in out[pid]:
            out[pid]['dissertation_name_key'] = f'{cands[0][1]}:{cands[0][2]}'
    db = duckdb.connect(str(REGISTRY), read_only=True)
    rows = db.execute("""SELECT DISTINCT substr(i1.node, 14) AS atlas, substr(i2.node, 4) AS qid, l.basis
                         FROM individuals i1 JOIN individuals i2 USING (individual_id)
                         JOIN person_links l ON (l.a = i2.node OR l.b = i2.node)
                         WHERE i1.node LIKE 'atlas:person:%' AND i2.node LIKE 'wd:%' AND l.basis NOT LIKE '%atlas%'""").fetchall()
    for atlas, qid, basis in rows:
        out[atlas].setdefault('registry', set()).add(qid)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    sheet = json.loads(SHEET.read_text())
    people = [r for r in sheet['people'] if r.get('status') == 'accepted' and r.get('wikidata')]
    info = fetch({r['wikidata']['qid'] for r in people}, args.out / 'raw')
    indep = independent({r['person_id'] for r in people})
    rows = []
    for r in people:
        q = r['wikidata']['qid']
        method = r['wikidata'].get('method')
        w = info[q]
        flags = []
        if w['redirect']:
            flags.append(f'redirect_to_{w["redirect"]}')
        if not w['exists'] and not w['redirect']:
            flags.append('missing_item')
        if w['exists'] and 'Q5' not in w['p31']:
            flags.append('not_human')
        name_ok = name_compatible(r['label'], w['labels'])
        if w['exists'] and not name_ok:
            flags.append('name_incompatible')
        if w['occ'] and not any(SCHOLARLY.search(o) for o in w['occ']):
            flags.append('occupations_unscholarly')
        if not w['occ']:
            flags.append('no_occupation')
        births = sorted(w['birth'])
        if births and births[0][:4].lstrip('-').isdigit() and int(births[0][:4].lstrip('-') or 0) > 2005:
            flags.append('born_after_2005')
        ind = indep.get(r['person_id'], {})
        others = {}
        if 'dissertation_joined' in ind:
            others['dissertation_joined'] = ind['dissertation_joined']
        if 'dissertation_name_key' in ind:
            others['dissertation_name_key'] = ind['dissertation_name_key'].split(':')[0]
        for x in ind.get('registry', ()):
            others.setdefault('registry', x)
        agree = sorted(k for k, v in others.items() if v == q)
        disagree = sorted(f'{k}={v}' for k, v in others.items() if v != q)
        if disagree:
            flags.append('independent_disagrees')
        manual = r['wikidata'].get('review_2026_10_30', '')
        if manual.startswith('confirmed'):
            agree.append('manual_review_2026-10-30')
            flags = [f for f in flags if f not in ('occupations_unscholarly', 'independent_disagrees', 'name_incompatible')]
            disagree = []
        if 'missing_item' in flags or 'not_human' in flags or 'name_incompatible' in flags:
            verdict = 'wrong'
        elif disagree or 'occupations_unscholarly' in flags or 'born_after_2005' in flags:
            verdict = 'suspect'
        elif agree or method in REVIEWED_METHODS:
            verdict = 'confirmed'
        else:
            verdict = 'plausible'
        rows.append(dict(person_id=r['person_id'], atlas_label=r['label'], qid=q, method=method or 'reviewed_mcp',
                         verdict=verdict, flags=' '.join(flags), agree=' '.join(agree), disagree=' '.join(disagree),
                         wd_label=next(iter(sorted(w['labels'])), '') if not name_ok else '',
                         wd_description=w['desc'], birth=births[0] if births else '', death=min(w['death'], default=''),
                         occupations='; '.join(sorted(w['occ']))[:200], sitelinks=w['sitelinks']))
    graph = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', 'HEAD:historiography-1920-2000.json'],
                                      capture_output=True, text=True, check=True).stdout)
    for r in rows:
        r.setdefault('works_checked', '')
    upgraded = works_evidence(rows, graph, args.out / 'raw')
    for r in rows:
        r.setdefault('lcnaf', '')
    upgraded_lc = lc_evidence(rows, graph, args.out / 'raw')
    args.out.mkdir(parents=True, exist_ok=True)
    order = {'wrong': 0, 'suspect': 1, 'plausible': 2, 'confirmed': 3}
    rows.sort(key=lambda x: (order[x['verdict']], x['method'], x['person_id']))
    with open(args.out / 'review.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    summary = dict(reviewed=len(rows), upgraded_by_works=upgraded, upgraded_by_lc=upgraded_lc, verdicts=dict(Counter(r['verdict'] for r in rows)),
                   by_method=dict(sorted(Counter(f"{r['method']} / {r['verdict']}" for r in rows).items())),
                   flags=dict(Counter(f for r in rows for f in r['flags'].split() if f)))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))



# --- second pass: works evidence for the `plausible` QIDs ---------------------------------------------

def atlas_texts(graph):
    """person id -> the atlas text that credits them: role contexts, their sources' citations, and
    (for person entries) representative works."""
    sources = {s['id']: f"{s.get('title', '')} {s.get('citation', '')}" for s in graph['sources']}
    out = defaultdict(list)

    def walk(x):
        if isinstance(x, dict):
            if x.get('person_id'):
                out[x['person_id']].append(x.get('context', ''))
                out[x['person_id']] += [sources.get(s, '') for s in x.get('source_ids', [])]
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(graph['nodes'])
    for n in graph['nodes']:
        out[n['id']] += [n.get('representative_figures_and_works', '')] + [sources.get(s, '') for s in n.get('source_ids', [])]
    return {k: folded(' '.join(v)) for k, v in out.items()}


def folded(s):
    return ' '.join(tokens(s))


def works_evidence(rows, graph, cache):
    """Upgrade `plausible` to `confirmed` when a Wikidata work by the QID (P50) has a title of three or more
    words that the atlas credits to this person; mark `no_works_match` otherwise."""
    texts = atlas_texts(graph)
    todo = [r for r in rows if r['verdict'] == 'plausible']
    works = defaultdict(set)
    qids = sorted({r['qid'] for r in todo})
    for i in range(0, len(qids), 40):
        values = ' '.join(f'wd:{q}' for q in qids[i:i + 40])
        for row in sparql(f"""SELECT ?q ?t WHERE {{ VALUES ?q {{ {values} }} ?w wdt:P50 ?q .
              ?w rdfs:label ?t FILTER(lang(?t) IN ("en", "fr", "de", "it", "es")) }}""", cache,
                          'works-' + hashlib.sha1(values.encode()).hexdigest()[:12]):
            works[row['q']['value'].rsplit('/', 1)[1]].add(row['t']['value'])
    upgraded = 0
    for r in todo:
        text = texts.get(r['person_id'], '')
        hits = sorted({t for t in works.get(r['qid'], ()) if len(tokens(t)) >= 3 and f' {folded(t)} ' in f' {text} '})
        r['works_checked'] = len(works.get(r['qid'], ()))
        if hits:
            r['verdict'] = 'confirmed'
            r['agree'] = (r['agree'] + ' works:' + '|'.join(hits[:2])).strip()
            upgraded += 1
        else:
            r['flags'] = (r['flags'] + (' no_works_match' if works.get(r['qid']) else ' no_works_on_wikidata')).strip()
    return upgraded



# --- third pass: LC authority sources for the remaining `plausible` QIDs -------------------------------

LC_AUTH = 'https://id.loc.gov/authorities/names/{}.marcxml.xml'


def lc_record(lcid, cache):
    path = cache / f'lc-{lcid}.xml'
    if not path.exists():
        req = urllib.request.Request(LC_AUTH.format(lcid), headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                path.write_bytes(r.read())
        except Exception as e:
            print(f'  LC {lcid}: {e}', flush=True)
            return None
        time.sleep(1.0)
    return path.read_text(encoding='utf-8', errors='replace')


def lc_titles(xml):
    """Titles cited in 670 fields ('His The making of the English working class, 1963:'), plus the
    undifferentiated flag (008/32 = b)."""
    f008 = re.search(r'tag="008"[^>]*>([^<]*)<', xml)
    titles = []
    for m in re.finditer(r'tag="670".*?</(?:marcxml:)?datafield>', xml, re.S):
        a = re.search(r'code="a"[^>]*>([^<]*)<', m.group(0))
        if a:
            t = re.sub(r'^(?:his|her|their|its|author\'s)\s+', '', a.group(1).strip(), flags=re.I)
            t = re.split(r',\s*(?:c|p)?\d{4}|:\s*$|\s*\[', t)[0]
            titles.append(t.strip(' .,:;'))
    return titles, bool(f008 and len(f008.group(1)) > 32 and f008.group(1)[32] == 'b')


def lc_evidence(rows, graph, cache):
    texts = atlas_texts(graph)
    todo = [r for r in rows if r['verdict'] == 'plausible']
    lcnaf = defaultdict(set)
    qids = sorted({r['qid'] for r in todo})
    for i in range(0, len(qids), 100):
        values = ' '.join(f'wd:{q}' for q in qids[i:i + 100])
        for row in sparql(f"SELECT ?q ?lc WHERE {{ VALUES ?q {{ {values} }} ?q wdt:P244 ?lc }}", cache,
                          'p244-' + hashlib.sha1(values.encode()).hexdigest()[:12]):
            lcnaf[row['q']['value'].rsplit('/', 1)[1]].add(row['lc']['value'])
    upgraded = 0
    for r in todo:
        ids = sorted(lcnaf.get(r['qid'], ()))
        r['lcnaf'] = ' '.join(ids)
        if not ids:
            r['flags'] = (r['flags'] + ' no_lcnaf').strip()
            continue
        text = f" {texts.get(r['person_id'], '')} "
        hits, undiff = [], False
        for lcid in ids:
            xml = lc_record(lcid, cache)
            if not xml:
                continue
            titles, u = lc_titles(xml)
            undiff |= u
            hits += [t for t in titles if len(tokens(t)) >= 3 and f' {folded(t)} ' in text]
        if undiff:
            r['flags'] = (r['flags'] + ' lc_undifferentiated').strip()
        elif hits:
            r['verdict'] = 'confirmed'
            r['agree'] = (r['agree'] + ' lc670:' + hits[0][:60]).strip()
            upgraded += 1
        else:
            r['flags'] = (r['flags'] + ' lc_no_title_match').strip()
    return upgraded


if __name__ == '__main__':
    main()
