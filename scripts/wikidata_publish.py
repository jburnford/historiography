"""Key log -> QuickStatements batches for Wikidata (2026-11-02). Writes a batch and a report; publishes nothing.

For each person key named, the facts the key log and its sources hold are compared with the person's current
Wikidata item. Only missing statements are written, each with a reference. The user reviews the batch and runs it
in QuickStatements under their own account; the item is read back afterwards. The steps, per person:
- **The item.** The key's `wd:` anchor; else the item citing the key's LC authority (P244); else the item that
  the key's GND record (lobid) gives as sameAs, as for Cunfer and Handy. Merged items count once (redirects). Without an item the person is listed
  under `needs_item` with any humans whose label is exactly their name, to check by hand (a new item is a separate decision); without LC, QID or ORCID under `needs_identifiers`.
- **P244 LC authority**, if the item lacks it (stated in the LC Name Authority File).
- **P69 educated at**, the school of the person's own dissertation in the log (its institution's ROR -> QID
  through Wikidata P6782), with P512 doctorate and P582 the year. Referenced to the thesis's repository record
  when the corpus holds one (`item_url`), else the AHA directory.
- **P184 doctoral advisor**: each `supervised` claim on that dissertation whose supervisor has a QID.
- **P108 employer**: an institution named in a clause of the LC authority's own notes (id.loc.gov) that speaks of
  a post ('assoc. prof. of history, Univ. of Saskatchewan'), not of a doctorate or a press; referenced to LC. Supervising a thesis at a school is not taken as employment.
Never written: closed ORCID iDs, birth dates, anything resting on name or topic alone.

    python3 scripts/wikidata_publish.py --keys p-806 p-66152 --out data/identifiers/wikidata-publish-2026-11-02/usask
"""
import argparse
import glob
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State
from key_aha_career import DOCTORATE, JOB

UA = 'historiography-kg research (jic823@usask.ca)'
WDQS = 'https://query.wikidata.org/sparql'
AHA_URL = 'https://secure.historians.org/members/services/cgi-bin/memberdll.dll/info?wrp=dissertations.htm'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
LC_NAF, PHD = 'Q18912790', 'Q752297'
TODAY = time.strftime('+%Y-%m-%dT00:00:00Z/11')


def get_json(url, accept='application/json'):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 — network: back off and retry, then give up
            if attempt == 3:
                print(f'  {url}: {e}')
                return None
            time.sleep(5 * (attempt + 1))


def sparql(query):
    d = get_json(WDQS + '?' + urllib.parse.urlencode({'query': query, 'format': 'json'}), 'application/sparql-results+json')
    time.sleep(1)
    return d['results']['bindings'] if d else []


def entity(qid):
    d = get_json(f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json')
    return next(iter(d['entities'].values())) if d else None


def exact_label(label):
    """Humans whose English or default label is the key's name, as candidates for a person to check by hand
    (the vector search missed Myron Gutmann and Keith Thor Carlson; exact labels found them)."""
    fam, comma, giv = label.partition(', ')
    name = f'{giv} {fam}' if comma else label
    rows = sparql('SELECT ?i ?d WHERE { VALUES ?l { "%s"@en "%s"@mul } ?i rdfs:label ?l ; wdt:P31 wd:Q5 . '
                  'OPTIONAL { ?i schema:description ?d FILTER(lang(?d)="en") } }' % (name, name))
    return sorted({(r['i']['value'].rsplit('/', 1)[1], r.get('d', {}).get('value', '')) for r in rows})


def claim_values(ent, prop):
    out = set()
    for c in (ent or {}).get('claims', {}).get(prop, []):
        v = c['mainsnak'].get('datavalue', {}).get('value')
        out.add(v.get('id') if isinstance(v, dict) else v)
    return out


def lc_notes(lcid):
    d = get_json(f'https://id.loc.gov/authorities/names/{lcid}.madsrdf.json') or []
    notes = []
    for n in d:
        for k, v in n.items():
            if k.endswith('citationNote') or k.endswith('citationSource'):
                notes += [x.get('@value') for x in v if isinstance(x, dict) and x.get('@value')]
    return notes


def gnd_wikidata(lcid):
    d = get_json('https://lobid.org/gnd/search?' + urllib.parse.urlencode(
        {'q': f'sameAs.id:"http://id.loc.gov/rwo/agents/{lcid}"', 'format': 'json'}))
    qids = set()
    for m in (d or {}).get('member', []):
        for s in m.get('sameAs', []):
            if s['id'].startswith('http://www.wikidata.org/entity/Q'):
                qids.add(s['id'].rsplit('/', 1)[1])
    return qids


def repository_urls():
    urls = {}
    for f in glob.glob(str(CORPUS / 'downloads*.jsonl')):
        for line in open(f, encoding='utf-8'):
            if '"item_url"' in line:
                r = json.loads(line)
                urls[r['id']] = r['item_url']
    return urls


def ref(url=None, lc=None):
    if lc:
        return f'S248|{LC_NAF}|S244|"{lc}"|S813|{TODAY}'
    return f'S854|"{url or AHA_URL}"|S813|{TODAY}'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--keys', nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    urls = repository_urls()
    ror_qid = {}

    def qid_of_institution(i):
        ror = next((a[4:] for a in state.keys[i]['anchors'] if a.startswith('ror:')), None)
        if ror and ror not in ror_qid:
            rows = sparql(f'SELECT ?i WHERE {{ ?i wdt:P6782 "{ror}" }}')
            ror_qid[ror] = rows[0]['i']['value'].rsplit('/', 1)[1] if len(rows) == 1 else None
        return ror_qid.get(ror)

    def anchors(k, scheme):
        return sorted(a.split(':', 1)[1] for a in state.keys[k]['anchors'] if a.startswith(scheme + ':'))

    lines, report = [], dict(people=[], needs_item=[], needs_identifiers=[])
    for key in args.keys:
        k = state.lookup(key)[0]
        label, wd, lc = state.keys[k]['label'], anchors(k, 'wd'), anchors(k, 'lcnaf')
        row = dict(key=k, label=label, lc=lc, wd=wd, added=[], notes=[])
        if not wd and lc:
            rows = sparql(f'SELECT ?i WHERE {{ ?i wdt:P244 "{lc[0]}" }}')
            wd = [r['i']['value'].rsplit('/', 1)[1] for r in rows] or sorted(gnd_wikidata(lc[0]))
            if wd:
                row['notes'].append(f'item found through {"P244" if rows else "GND"}: {wd}')
        ents = {}
        for x in wd:                                    # merged items redirect: keep the target once
            e = entity(x)
            if e:
                ents[e['id']] = e
        if len(ents) != 1:
            found = [] if ents else exact_label(label)
            (report['needs_item'] if lc or anchors(k, 'orcid') else report['needs_identifiers']).append(
                dict(key=k, label=label, lc=lc, wd=sorted(ents), exact_label_candidates=found))
            continue
        (q, ent), = ents.items()
        row['wd'] = q
        if lc and lc[0] not in claim_values(ent, 'P244'):
            lines.append(f'{q}|P244|"{lc[0]}"|S248|{LC_NAF}|S813|{TODAY}')
            row['added'].append('P244')
        have69, have184 = claim_values(ent, 'P69'), claim_values(ent, 'P184')
        for claim, subj, pred, obj in state.relations('authored'):
            if subj != [k] or len(obj) != 1:
                continue
            w = obj[0]
            wa = state.keys[w]['anchors']
            if not any(a.startswith(('aha-diss:', 'diss-thesis:', 'wrap:')) for a in wa):
                continue
            year = next((m[5:9] for m in state.members.get(w, ()) if m.startswith('year:')), None)
            inst = next((state.lookup(m.split(':', 1)[1]) for m in state.members.get(w, ()) if m.startswith('awarded-by:')), [])
            thesis_url = next((urls[a.split(':', 1)[1]] for a in wa if a.startswith('diss-thesis:') and a.split(':', 1)[1] in urls), None)
            thesis_url = thesis_url or next((f'https://wrap.warwick.ac.uk/{a[5:]}/' for a in wa if a.startswith('wrap:')), None)
            school = qid_of_institution(inst[0]) if len(inst) == 1 else None
            if school and school not in have69:
                qual = f'|P512|{PHD}' + (f'|P582|+{year}-00-00T00:00:00Z/9' if year else '')
                lines.append(f'{q}|P69|{school}{qual}|{ref(thesis_url)}')
                row['added'].append(f'P69 {state.keys[inst[0]]["label"]} {year or ""}')
            elif not school:
                row['notes'].append(f'thesis {w}: no school QID')
            for _, s2, _, o2 in state.relations('supervised'):
                if o2 == [w] and len(s2) == 1:
                    adv = anchors(s2[0], 'wd')
                    if len(adv) == 1 and adv[0] not in have184:
                        lines.append(f'{q}|P184|{adv[0]}|{ref(thesis_url)}')
                        row['added'].append(f'P184 {state.keys[s2[0]]["label"]}')
                    elif not adv:
                        row['notes'].append(f'advisor {state.keys[s2[0]]["label"]} has no QID')
        if lc:
            raw = lc_notes(lc[0])
            row['lc_notes'] = ' | '.join(raw)[:600]
            clauses = [c for n in raw for c in re.split(r'[;()]', n)]
            notes = ' '.join(c for c in clauses if JOB.search(c) and not DOCTORATE.search(c)).replace(' Press', ' PRESS')
            have108 = claim_values(ent, 'P108')
            for i, v in state.keys.items():
                if v['type'] != 'institution' or v['status'] != 'active':
                    continue
                name = re.sub(r'^The ', '', v['label'])
                short = name.replace('University of ', 'Univ. of ')
                if re.search(rf'(?:{re.escape(name)}|{re.escape(short)})(?! PRESS)', notes):
                    iq = qid_of_institution(i)
                    if iq and iq not in have108:
                        lines.append(f'{q}|P108|{iq}|{ref(lc=lc[0])}')
                        row['added'].append(f'P108 {v["label"]} (LC notes)')
        if not (ent or {}).get('descriptions', {}).get('en'):
            row['notes'].append('no English description: write one by hand')
        report['people'].append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix('.qs').write_text('\n'.join(lines) + '\n')
    args.out.with_suffix('.report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    print(len(lines), 'statements;', len(report['people']), 'people with items;', len(report['needs_item']), 'need items;',
          len(report['needs_identifiers']), 'need identifiers')


if __name__ == '__main__':
    main()
