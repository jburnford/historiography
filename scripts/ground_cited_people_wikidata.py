#!/usr/bin/env python3
"""Ground frequently cited people in the dissertation citation graph to Wikidata (QLever).

Candidates are humans whose English, French or multilingual label or alias equals one
of the person's printed names in "Given Surname" order (initials spaced and unspaced).
Tiers:
- ``title_verified``: exactly one candidate is the Wikidata author (P50) of a work whose
  main title matches a work the dissertations cite under this person.
- ``probable_historian``: no title evidence; among candidates named by the most complete
  printed form, exactly one is described as a historian (description or P106 historian).
- ``probable_canadian_academic``: otherwise exactly one of those (historians first) has a
  description naming Canada or Quebec and an academic or writing occupation.
- ``possible_sole_candidate`` (weakest): the only human with any of the full-name forms,
  whose item shows scholarship (academic description, historian occupation or a Library
  of Congress authority record).
With more than ten same-name candidates, a description-only match is accepted only if the
description is Canadian (a 'historian' label alone mis-chose Peter Jones and Max Weber).
Lifespan gate (not applied to title-verified candidates): excluded if dead more than ten
years before the 10th-percentile year of the cited works, or not yet 18 at the median.
Name forms come only from clean printed spellings (no parse debris), tried in order of
frequency: the most common spelling with any candidate decides ("Peter A. Russell" is not
matched through a rarer "Peter H. Russell" spelling under the same name key).
Everything else stays unresolved, with its candidates listed for review.
Output: ``person-wikidata.jsonl`` (one row per queried person).
"""
import argparse
import csv
from collections import defaultdict
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from build_dissertation_citation_graph import fold, title_key

ENDPOINT = 'https://qlever.dev/api/wikidata'
PREFIXES = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX schema: <http://schema.org/>
"""
HISTORIAN = 'Q201788'
# Personal names are language-independent, but Wikidata files aliases under arbitrary languages
# (J.R. Miller's short forms exist only as cs/de aliases), so look them up under many.
LANGS = ('en', 'fr', 'mul', 'de', 'es', 'it', 'nl', 'pt', 'cs', 'pl', 'sv', 'da', 'nb', 'fi', 'ca', 'ru', 'uk', 'he', 'ja')
SCHOLAR = re.compile(r'histor|professor|scholar|academic|universit|researcher|political scien|geograph|sociolog|'
                     r'anthropolog|archivist|economist|historien|professeur|chercheu', re.I)
ACADEMIC = re.compile(r'histor|professor|scholar|academic|universit|political scien|geograph|sociolog|criminolog|'
                      r'economist|anthropolog|archivist|librarian|writer|author|journalist|historien|professeur|chercheu|'
                      r'politolog|écrivain|auteur', re.I)


def post(query):
    data = urlencode({'query': PREFIXES + query}).encode()
    req = Request(ENDPOINT, data=data, headers={'Accept': 'text/tab-separated-values',
                                                'Content-Type': 'application/x-www-form-urlencoded'})
    for attempt in range(8):
        try:
            with urlopen(req, timeout=600) as r:
                rows = r.read().decode().splitlines()
            head = [h.lstrip('?') for h in rows[0].split('\t')]
            return [dict(zip(head, line.split('\t'))) for line in rows[1:]]
        except HTTPError as exc:  # 429: QLever rate limit, back off progressively
            if attempt == 7:
                raise
            time.sleep(60 * (attempt + 1) if exc.code == 429 else 15)
        except Exception:
            if attempt == 7:
                raise
            time.sleep(15)


def literal(v):
    m = re.match(r'^"(.*)"(?:@[\w-]+)?$', v)
    return m.group(1).replace('\\"', '"') if m else v


def qid(v):
    return v.rsplit('/', 1)[-1].rstrip('>')


def label_forms(names):
    """'Miller, J.R' -> {'J. R. Miller', 'J.R. Miller', 'J R Miller'}; keeps diacritics."""
    out = set()
    for n in names:
        if ',' not in n:
            continue
        sur, given = [x.strip(' .') for x in n.split(',', 1)]
        if not sur or not given:
            continue
        if sur.isupper():
            sur = sur.title()
        toks = re.findall(r"[^\s.]+\.?", given)
        if not toks:
            continue
        bare = [t.rstrip('.') for t in toks]
        dotted = [t + '.' if len(t) == 1 else t for t in bare]
        out.add(' '.join(dotted + [sur]))
        out.add(' '.join(bare + [sur]))
        if all(len(t) == 1 for t in bare):
            out.add(''.join(t + '.' for t in bare) + ' ' + sur)
    return {o for o in out if len(o) > 4}


def clean_variants(variants):
    """Printed spellings fit for label lookup: no parse debris (titles, digits, long runs)."""
    ok = [v for v in variants if ',' in v and not re.search(r'[\d:;?!()“”"‘’«»―‖]', v)
          and len(v.split(',', 1)[1].split()) <= 3 and len(v) <= 40]
    return ok[:4]


def label_middle(label):
    toks = re.findall(r"[^\s.]+", label)
    return toks[1][0].lower() if len(toks) >= 3 and len(toks[1].rstrip('.')) == 1 else None


def dominant_middle(variants):
    """Middle initial printed in at least 60% of the spellings that have one."""
    mids = []
    for v in variants:
        if ',' in v:
            toks = re.findall(r"[^\s.]+", v.split(',', 1)[1])
            if len(toks) >= 2:
                mids.append(toks[1][0].lower())
    if not mids:
        return None
    top = max(set(mids), key=mids.count)
    return top if mids.count(top) / len(mids) >= 0.6 else None


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--min-cited', type=int, default=3)
    parser.add_argument('--batch', type=int, default=40)
    parser.add_argument('--retry-tiers', nargs='*', default=[], help='re-query people whose last row has one of these tiers')
    args = parser.parse_args()
    graph = json.loads((args.out / 'graph.json').read_text())
    nodes = {n['id']: n for n in graph['nodes']}
    works_of, years_of = defaultdict(set), defaultdict(list)
    for e in graph['edges']:
        if e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'][2:].split('|')[1])
            years_of[e['source']].append(nodes[e['target']].get('year'))
    cache_path = args.out / 'person-wikidata.jsonl'
    rows_before = []
    if cache_path.exists():
        for line in cache_path.open():
            try:
                rows_before.append(json.loads(line))
            except json.JSONDecodeError:  # truncated by an interrupted run
                continue
    # done: settled by a row, or already searched with the current multilingual alias list
    done = {r['person'] for r in rows_before if r['tier'] not in args.retry_tiers or r.get('search_languages', 0) >= len(LANGS)}
    reviewed = set()
    if (args.out / 'person-wikidata-decisions.csv').exists():
        with (args.out / 'person-wikidata-decisions.csv').open(newline='') as f:
            reviewed = {r['person'] for r in csv.DictReader(f)}
    done |= reviewed
    people = [n for n in graph['nodes'] if n['type'] == 'Person' and n.get('cited_by_all', 0) >= args.min_cited
              and n['name_key_kind'] != 'corporate_or_single_name' and not n.get('qid') and n['id'] not in done]
    people.sort(key=lambda n: -n['cited_by_all'])
    names = json.loads((args.out / 'person-names.json').read_text()) if (args.out / 'person-names.json').exists() else {}
    print(f'{len(people)} people to ground', flush=True)
    with cache_path.open('a') as out:
        for i in range(0, len(people), args.batch):
            batch = people[i:i + args.batch]
            # Spellings in frequency order; the first spelling with any candidate decides.
            ordered = {p['id']: [label_forms([v]) for v in clean_variants(names.get(p['id'], [p['name']]))] for p in batch}
            forms = {k: set().union(*v) if v else set() for k, v in ordered.items()}
            values = ' '.join(f'("{esc(f)}"@{lang})' for fs in forms.values() for f in fs for lang in LANGS)
            cands = post(f"""SELECT ?l ?h ?d ?occ ?lab ?born ?died ?lc WHERE {{ VALUES (?l) {{ {values} }}
                {{ ?h rdfs:label ?l }} UNION {{ ?h skos:altLabel ?l }}
                ?h wdt:P31 wd:Q5 .
                OPTIONAL {{ ?h schema:description ?d . FILTER(LANG(?d) IN ("en","fr")) }}
                OPTIONAL {{ ?h wdt:P106 ?occ . FILTER(?occ = wd:{HISTORIAN}) }}
                OPTIONAL {{ ?h rdfs:label ?lab . FILTER(LANG(?lab) IN ("en","mul")) }}
                OPTIONAL {{ ?h wdt:P569 ?born }} OPTIONAL {{ ?h wdt:P570 ?died }} OPTIONAL {{ ?h wdt:P244 ?lc }} }}""")
            by_form = defaultdict(lambda: defaultdict(lambda: dict(desc=set(), historian=False)))
            facts = defaultdict(lambda: dict(labels=set(), born=set(), died=set(), lcnaf=False))
            for r in cands:
                c = by_form[fold(literal(r['l']))][qid(r['h'])]
                if r.get('d'):
                    c['desc'].add(literal(r['d']))
                c['historian'] |= bool(r.get('occ'))
                f = facts[qid(r['h'])]
                f['lcnaf'] |= bool(r.get('lc'))
                if r.get('lab'):
                    f['labels'].add(literal(r['lab']))
                for k in ('born', 'died'):
                    m = re.search(r'"?(-?\d{4})', r.get(k) or '')
                    if m:
                        f[k].add(int(m.group(1)))
            humans = sorted({q for f in by_form.values() for q in f})
            titles = defaultdict(set)
            for j in range(0, len(humans), 200):
                vals = ' '.join(f'wd:{q}' for q in humans[j:j + 200])
                for r in post(f"""SELECT ?h ?wl WHERE {{ VALUES ?h {{ {vals} }} ?w wdt:P50 ?h .
                        {{ ?w rdfs:label ?wl . FILTER(LANG(?wl) IN ("en","fr","mul")) }} UNION {{ ?w wdt:P1476 ?wl }} }}"""):
                    titles[qid(r['h'])].add(title_key(literal(r['wl'])))
            for p in batch:
                cand = {}
                group = next((g for g in ordered[p['id']] if any(by_form.get(fold(f)) for f in g)), set())
                for f in group:
                    for q, c in by_form.get(fold(f), {}).items():
                        cand.setdefault(q, dict(desc=set(), historian=False, specificity=0))
                        cand[q]['desc'] |= c['desc']
                        cand[q]['historian'] |= c['historian']
                        cand[q]['specificity'] = max(cand[q]['specificity'], len(fold(f).split()))
                cited = works_of[p['id']]
                # Gates: a candidate must have been alive and adult at the median publication
                # year of the cited works (10 years' grace for posthumous editions), and must not carry a
                # different middle initial from the person's usual printed one.
                ys = sorted(y for y in years_of[p['id']] if y)
                median = ys[len(ys) // 2] if ys else None  # robust to misparsed years
                earliest = ys[len(ys) // 10] if ys else None  # 10th percentile: classics in modern editions, robust to stray years
                middle = dominant_middle(names.get(p['id'], [p['name']]))
                # Title evidence first: a candidate who is the Wikidata author of a cited work is kept
                # whatever the gates say (Tocqueville is cited in modern editions of his own books).
                verified = sorted(q for q in cand if titles[q] & cited)
                for q in list(cand):
                    if q in verified:
                        continue
                    f = facts[q]
                    if ys and ((f['died'] and max(f['died']) + 10 < earliest) or
                               (f['born'] and min(f['born']) + 18 > median)):
                        cand.pop(q)
                    elif middle and any(m and m != middle for m in map(label_middle, f['labels'])):
                        cand.pop(q)
                # Prefer candidates named by the most complete printed form ("Robert Craig Brown").
                top = max((c['specificity'] for c in cand.values()), default=0)
                pool = {q: c for q, c in cand.items() if c['specificity'] == top}
                hist = sorted(q for q, c in pool.items() if c['historian'] or any(re.search(r'histor', d, re.I) for d in c['desc']))
                canadian = sorted(q for q in (hist or pool) if any(re.search(r'canad|québ|queb', d, re.I) and ACADEMIC.search(d)
                                                                     for d in pool[q]['desc']))
                # Many namesakes: a 'historian' description alone does not choose among them
                # (Peter Jones, Max Weber); only a Canadian historian or academic description does.
                if len(pool) > 10:
                    hist = [q for q in hist if any(re.search(r'canad|québ|queb', d, re.I) for d in pool[q]['desc'])]
                # Sole candidate: the item itself must show scholarship (academic description,
                # historian occupation or a Library of Congress authority record).
                sole = [q for q, c in pool.items() if any(SCHOLAR.search(d) for d in c['desc']) or c['historian']
                        or facts[q]['lcnaf']] if len(cand) == 1 and top >= 2 else []
                row = dict(person=p['id'], name=p['name'], cited_by_all=p['cited_by_all'], forms=sorted(forms[p['id']]),
                           search_languages=len(LANGS),
                           candidates=[dict(qid=q, desc=sorted(c['desc'])[:2], historian=c['historian'], specificity=c['specificity'],
                                            matched_titles=sorted(titles[q] & cited)[:5]) for q, c in sorted(cand.items())])
                if len(verified) == 1:
                    row.update(qid=verified[0], tier='title_verified')
                elif not verified and len(hist) == 1:
                    row.update(qid=hist[0], tier='probable_historian')
                elif not verified and len(canadian) == 1:
                    row.update(qid=canadian[0], tier='probable_canadian_academic')
                elif not verified and not hist and len(sole) == 1:
                    row.update(qid=sole[0], tier='possible_sole_candidate')
                else:
                    row.update(qid=None, tier='unresolved' if cand else 'no_candidate')
                out.write(json.dumps(row, ensure_ascii=False) + '\n')
            out.flush()
            print(f'{i + len(batch)}/{len(people)}', flush=True)
            time.sleep(5)


if __name__ == '__main__':
    main()
