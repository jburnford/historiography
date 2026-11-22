"""Place layer: outside-reviewer groundings of ungrounded LC place headings (Sol, 2026-11-19, job 8) -> a tracked table.

Sol (Codex, web sources) read 4,858 headings from data/graph/places/ungrounded.csv.gz and, for each, followed
identifiers (LC authority -> Wikidata P244, GeoNames, CGNDB, GND, BnF, VIAF ...) to a Wikidata item, or said why not
(data/identifiers/sol-review-2026-11-19/8-ungrounded-places/). This script turns the reads into two tracked tables
read by scripts/places_build.py beside overrides.csv (overrides.csv stays for hand work):

  data/graph/places/sol-groundings-2026-11-21.csv.gz   heading, parent, thesaurus, qid -> grounded (lc rows) or
                                                        Canadiana/other-thesaurus rows ('fr', the overrides form)
  data/graph/places/sol-not-places-2026-11-21.csv      heading, parent -> not a place (peoples, categories ...):
                                                        listed apart in ungrounded.csv.gz, not counted as ungrounded

A row is adopted only when (a) Sol's verdict is `grounded` in a stratum that passed the hand audit
(data/graph/places/audit/sol-groundings-audit-2026-11-21.csv) and (b) it passes every machine check below, run on
Wikidata facts fetched by exact QID from QLever (no name search):
  exists     the item has a label and is not a redirect
  ident      an identifier Sol cites (LC id, GeoNames, CGNDB, GND, BnF, VIAF ...) is held by the item exactly
             (the heading's LC id as P244 counts first)
  name       the heading's name (qualifier stripped, accents folded) matches a label or alias of the item, or shares
             its distinctive word
  place      the item has a geographic class (places_build.kind_of) and is not a people, nation or band
  lc_other   the heading's LC id is not held as P244 by a different item
  collide    the QID is not already the place of a different LC heading in places.csv.gz unless the new heading is a
             name form of the same place (same name, or a non-LC-thesaurus form), and the kinds agree (a township or
             county qualifier never joins a settlement)

    python3 scripts/places_sol_groundings.py clean      # latest verdict per case -> build/places/sol-groundings/
    python3 scripts/places_sol_groundings.py fetch      # QLever facts by QID, cached
    python3 scripts/places_sol_groundings.py check      # machine checks -> build/places/sol-groundings/checked.jsonl
    python3 scripts/places_sol_groundings.py table      # tracked tables, held list and report (audit/)
    python3 scripts/places_sol_groundings.py report     # after places_build.py: before (git HEAD) -> after counts
"""
import csv
import gzip
import io
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/identifiers/sol-review-2026-11-19/8-ungrounded-places'
W = ROOT / 'build/places/sol-groundings'
OUT = ROOT / 'data/graph/places'
TABLE = OUT / 'sol-groundings-2026-11-21.csv.gz'
NOT_PLACES = OUT / 'sol-not-places-2026-11-21.csv'
AUDIT = OUT / 'audit/sol-groundings-audit-2026-11-21.csv'
HELD = OUT / 'audit/sol-groundings-held-2026-11-21.csv'      # Sol `grounded` rows not adopted, with the reason
PROVENANCE = 'Sol (Codex) read 2026-11-19, job 8-ungrounded-places; audited 2026-11-21'
ENDPOINT = 'https://qlever.dev/api/wikidata'
UA = 'historiography-places/1.0 (research; single worker)'
PREFIX = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""
SOUTH_ASIA = {'Q854', 'Q668', 'Q843', 'Q902', 'Q837', 'Q917', 'Q826', 'Q889', 'Q129286', 'Q1775277', 'Q83891'}
# the jurisdiction type a heading names in its qualifier or last word ('Waterloo (Ont. : Township)', 'Dundas (County)',
# 'Malakand Division', French 'Canton', 'Comte'): such a heading is a unit, not the settlement of the same name, and two
# headings of different unit types never share one place
UNIT_TYPES = [('township', r'Township|Canton|Twp\.?'), ('county', r'County|Counties|Comt[eé]|Shire'),
              ('regional', r'Regional municipality|Municipalit[eé] r[eé]gionale|Regional district|R[eé]gion administrative'),
              ('municipality', r'Municipality|Municipalit[eé]|Rural municipality|Unitary authority|Metropolitan borough'),
              ('parish', r'Parish|Paroisse'), ('district', r'District|Division|Bezirk|Kreis|Taluk|Tahsil'),
              ('province', r'Province|State|Department|D[eé]partement|Prefecture|Princely State|Region|R[eé]gion|Dept\.')]


def unit_type(h):
    m = re.search(r'\(([^)]*)\)\s*$', h or '')
    part = m.group(1).split(' : ')[-1] if m else ''
    last = re.sub(r'\s*\([^)]*\)\s*$', '', h or '')
    for t, rx in UNIT_TYPES:
        if re.fullmatch(rf'(?i)\s*({rx})\s*', part) or re.search(rf'(?i)\s({rx})$', last):
            return t
    return ''



# ---- clean -----------------------------------------------------------------------------------------------------
def clean():
    q = {r['case']: r for r in csv.DictReader(open(SRC / 'queue.csv', encoding='utf-8'))}
    latest, hist = {}, defaultdict(list)
    for line in open(SRC / 'verdicts.jsonl', encoding='utf-8'):
        d = json.loads(line)
        c = d.get('supersedes') or d['case']
        hist[c].append((d['verdict'], d.get('qid')))
        latest[c] = d
    W.mkdir(parents=True, exist_ok=True)
    with open(W / 'clean.jsonl', 'w', encoding='utf-8') as fh:
        for c in sorted(latest):
            d, r = dict(latest[c]), q[c]
            d.update(q_heading=r['heading'], q_parent=r['parent'], route=r['route'], q_lc_id=r['lc_id'],
                     q_reason=r['reason'], priority=r['priority'], q_uses=int(r['uses']), books=int(r['books']),
                     n_lines=len(hist[c]))
            fh.write(json.dumps(d, ensure_ascii=False) + '\n')
    rep = [dict(case=c, heading=q[c]['heading'], parent=q[c]['parent'],
                history=' > '.join(f'{v}:{x or ""}' for v, x in h)) for c, h in sorted(hist.items()) if len(set(h)) > 1]
    with open(OUT / 'audit/sol-groundings-repeat-conflicts-2026-11-21.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['case', 'heading', 'parent', 'history'])
        w.writeheader()
        w.writerows(rep)
    print('cases', len(latest), 'queue', len(q), 'repeat conflicts', len(rep))


def rows():
    return [json.loads(l) for l in open(W / 'clean.jsonl', encoding='utf-8')]


# ---- fetch -----------------------------------------------------------------------------------------------------
def post(query):
    data = urllib.parse.urlencode({'query': PREFIX + query}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={'Accept': 'text/tab-separated-values', 'User-Agent': UA})
    for attempt in range(4):
        try:
            return urllib.request.urlopen(req, timeout=600).read().decode()
        except Exception as e:      # noqa: BLE001 (network)
            print('  retry', attempt, e, flush=True)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError('QLever failed')


def cl(v):
    v = v.strip()
    if v.startswith('<http://www.wikidata.org/entity/'):
        return v.rsplit('/', 1)[-1].rstrip('>')
    if v.startswith('"'):
        return v[1:v.rfind('"')].replace('\\"', '"').replace('\\\\', '\\')
    return v


def run(name, template, values, batch, kind='qid'):
    path = W / f'{name}.tsv'
    if path.exists():
        return
    out, header = [], None
    values = sorted(values)
    for i in range(0, len(values), batch):
        v = ' '.join(('wd:' + x) if kind == 'qid' else json.dumps(x) for x in values[i:i + batch])
        lines = list(csv.reader(io.StringIO(post(template.format(v=v))), delimiter='\t', quoting=csv.QUOTE_NONE))
        header = [h.lstrip('?') for h in lines[0]]
        out += [[cl(x) for x in r] for r in lines[1:] if r]
        print(f'  {name} {min(i + batch, len(values))}/{len(values)} rows {len(out)}', flush=True)
        time.sleep(1)
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(header)
        w.writerows(out)


def lc_ids(text):
    return set(re.findall(r'\b((?:n|nb|nr|no|sh|sj|gf)\d{6,11})\b', text or ''))


def cited(d):
    """Every identifier-shaped token in Sol's basis, reason and evidence (facts and URLs)."""
    text = ' '.join([d.get('basis') or '', d.get('reason') or '', d.get('lc_authority') or ''] +
                    [f"{e.get('fact', '')} {e.get('url', '')}" for e in d.get('evidence') or []])
    toks = set(re.findall(r'[A-Za-z0-9][A-Za-z0-9_\-]{3,}', text.replace('%20', ' ')))
    return text, {t for t in toks if (any(ch.isdigit() for ch in t) and not re.fullmatch(r'1[0-9]{3}|20[0-9]{2}', t))
                  or re.fullmatch(r'[A-Z]{5}', t)}


def fetch():
    R = [d for d in rows() if d['verdict'] == 'grounded' and d.get('qid')]
    qids = {d['qid'] for d in R} | {'Q2082'}
    run('extids', """SELECT ?i ?pid ?v WHERE {{ VALUES ?i {{ {v} }} ?prop wikibase:directClaim ?p ;
                     wikibase:propertyType wikibase:ExternalId . ?i ?p ?v . BIND(STRAFTER(STR(?prop), 'entity/') AS ?pid) }}""",
        qids, 150)
    run('names', """SELECT ?i ?n WHERE {{ VALUES ?i {{ {v} }} {{ ?i rdfs:label ?n }} UNION {{ ?i skos:altLabel ?n }} }}""",
        qids, 300)
    run('p31', """SELECT ?i ?c ?cl WHERE {{ VALUES ?i {{ {v} }} ?i wdt:P31 ?c OPTIONAL {{ ?c rdfs:label ?cl FILTER(lang(?cl) = 'en') }} }}""",
        qids, 500)
    run('redirects', "SELECT ?i ?t WHERE {{ VALUES ?i {{ {v} }} ?i owl:sameAs ?t }}", qids, 1000)
    lcs = set()
    for d in R:
        lcs |= lc_ids(d.get('q_lc_id')) | lc_ids(d.get('lc_authority'))
    run('p244rev', "SELECT ?x ?v WHERE {{ VALUES ?v {{ {v} }} ?x wdt:P244 ?v }}", lcs, 1000, kind='str')
    # Wikidata facts for the build (places_wikidata.py), for QIDs the build does not hold yet
    sys.path.insert(0, str(ROOT / 'scripts'))
    import places_build as pb
    basic = pb.wd_tables()[0]
    new = sorted(qids - set(basic))
    (ROOT / 'build/places/qids-extra4.csv').write_text('\n'.join(new) + '\n')
    print(len(new), 'QIDs without cached Wikidata facts -> build/places/qids-extra4.csv')


# ---- check -----------------------------------------------------------------------------------------------------
def fold(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = s.replace('ʻ', '').replace('ʼ', '').replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


STOP = {'the', 'of', 'and', 'de', 'la', 'le', 'du', 'des', 'saint', 'st', 'sainte', 'ste', 'san', 'santa', 'lake', 'river',
        'mount', 'north', 'south', 'east', 'west', 'new', 'great', 'little', 'region', 'county', 'province', 'district',
        'city', 'island', 'islands', 'valley', 'fort', 'port', 'el', 'al', 'les', 'los', 'las', 'del', 'di', 'da', 'do',
        'van', 'von', 'upper', 'lower', 'bay', 'site', 'state', 'township', 'india', 'canada', 'england', 'france'}


def base(h):
    return re.sub(r'\s*\([^)]*\)\s*$', '', h or '').strip()


def tsvd(name):
    p = W / f'{name}.tsv'
    return list(csv.DictReader(open(p, encoding='utf-8'), delimiter='\t')) if p.exists() else []


def check():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import places_build as pb
    basic, kinds, p131, anc, p17, alias, peoples, succ, preds = pb.wd_tables()
    ext = defaultdict(lambda: defaultdict(set))
    for r in tsvd('extids'):
        ext[r['i']][r['pid']].add(r['v'])
    names = defaultdict(set)
    for r in tsvd('names'):
        names[r['i']].add(fold(r['n']))
    p31 = defaultdict(set)
    for r in tsvd('p31'):
        p31[r['i']].add(f"{r['c']} {r.get('cl', '')}".strip())
    redir = {r['i']: r['t'] for r in tsvd('redirects')}
    p244rev = defaultdict(set)
    for r in tsvd('p244rev'):
        p244rev[r['v']].add(r['x'])
    places = {r['qid']: r for r in csv.DictReader(gzip.open(OUT / 'places.csv.gz', 'rt', encoding='utf-8'))}
    R = rows()
    by_qid = defaultdict(list)
    for d in R:
        if d['verdict'] == 'grounded' and d.get('qid'):
            by_qid[d['qid']].append(d)
    # an LC twin (same heading and parent, LC route) that Sol left unclear or ungrounded holds the non-LC row
    lc_twin = {(d['q_heading'], d['q_parent']): d for d in R if d['route'] != 'not-used'}
    out = []
    for d in R:
        if d['verdict'] != 'grounded' or not d.get('qid'):
            continue
        q = d['qid']
        k = {}
        b = basic.get(q)
        k['exists'] = bool(names.get(q)) and q not in redir
        # identifiers
        text, toks = cited(d)
        heading_lc = (lc_ids(d.get('q_lc_id')) | lc_ids(d.get('lc_authority')))
        held = {v for vs in ext[q].values() for v in vs}
        hits = []
        if heading_lc & ext[q].get('P244', set()):
            hits.append('P244=' + ','.join(sorted(heading_lc & ext[q]['P244'])))
        for pid, vs in ext[q].items():
            for v in vs:
                if pid != 'P244' and len(v) >= 4 and (v in toks or v in text and len(v) >= 6 and not v.isalpha()):
                    hits.append(f'{pid}={v}')
        k['ident'] = bool(hits)
        k['ident_hits'] = sorted(set(hits))[:8]
        k['p244_heading'] = bool(heading_lc & ext[q].get('P244', set()))
        # name
        hb = fold(base(d['q_heading']))
        hw = {w for w in hb.split() if len(w) >= 4 and w not in STOP}
        nm = names.get(q, set())
        k['name'] = bool(hb) and (hb in nm or any(hb in n or n in hb for n in nm if len(n) >= 4)
                                  or bool(hw & {w for n in nm for w in n.split()})
                                  or (len(hb) >= 5 and any(SequenceMatcher(None, hb, n).ratio() >= 0.8 for n in nm)))
        # place
        kd = pb.kind_of(q, kinds, basic) if b else None
        k['kind'] = kd
        nat = peoples.get(q) and (kd in ('other', 'structure', None) or pb.NATION_LABEL.search((b or {}).get('label', '')))
        humanish = any(c.split()[0] in ('Q5', 'Q43229', 'Q4830453', 'Q1656682', 'Q41710', 'Q33829', 'Q2472587', 'Q13406463',
                                         'Q4167836', 'Q17442446') for c in p31.get(q, ()))
        k['place'] = bool(b) and kd not in (None, 'other') and not nat and not (humanish and kd in ('structure',))
        k['place_facts'] = bool(b)
        # LC id held by a different item
        other = {x for l in heading_lc for x in p244rev.get(l, ()) if x != q}
        k['lc_other'] = sorted(other)
        # collisions
        pl = places.get(q)
        col = ''
        ut = unit_type(d['q_heading'])
        if pl and pl.get('lc_heading'):
            old = pl['lc_heading']
            if unit_type(old) != ut:
                col = f'QID already the place of LC "{old}"; unit types differ ({unit_type(old) or "none"} vs {ut or "none"})'
        others = [x for x in by_qid[q] if x is not d]
        if not col and others:
            units = {unit_type(x['q_heading']) for x in by_qid[q]}
            if len(units) > 1:
                col = 'QID given to headings of different unit types: ' + '; '.join(sorted(
                    {x['q_heading'] for x in others if unit_type(x['q_heading']) != ut})[:4])
        k['collide'] = col
        twin = lc_twin.get((d['q_heading'], d['q_parent']))
        k['lc_twin_unclear'] = d['route'] == 'not-used' and bool(twin) and (twin['verdict'] != 'grounded' or twin.get('qid') != q)
        k['pass'] = (k['exists'] and k['ident'] and k['name'] and k['place'] and not k['lc_other'] and not col
                     and not k['lc_twin_unclear'])
        # stratum
        cq = d.get('country_qid') or ''
        cqs = set(cq if isinstance(cq, list) else re.findall(r'Q\d+', str(cq)))
        ctx = f"{d['q_heading']} {d['q_parent']}"
        if 'Q16' in cqs or re.search(r'\b(Canada|Ont\.|Que\.|Québec|Quebec|B\.C\.|Alta\.|Sask\.|Man\.|N\.S\.|N\.B\.|Nfld|N\.L\.|P\.E\.I|N\.W\.T|Yukon|Nunavut)\b', ctx):
            st = 'canada'
        elif cqs & SOUTH_ASIA or re.search(r'\b(India|Sri Lanka|Ceylon|Pakistan|Bangladesh|Nepal|Bhutan|Princely State)\b', ctx):
            st = 'south-asia'
        else:
            st = 'other'
        out.append(dict(case=d['case'], heading=d['q_heading'], parent=d['q_parent'], route=d['route'], uses=d['q_uses'],
                        lc_id=d['q_lc_id'] or d.get('lc_authority') or '', qid=q, qid_label=d.get('qid_label'),
                        confidence=d['confidence'], stratum=st, priority=d['priority'], basis=d.get('basis'), **k))
    with open(W / 'checked.jsonl', 'w', encoding='utf-8') as fh:
        for o in out:
            fh.write(json.dumps(o, ensure_ascii=False) + '\n')
    c = Counter()
    for o in out:
        for f in ('exists', 'ident', 'name', 'place', 'place_facts', 'p244_heading', 'lc_twin_unclear', 'pass'):
            c[(f, bool(o[f]))] += 1
        c[('lc_other', bool(o['lc_other']))] += 1
        c[('collide', bool(o['collide']))] += 1
    print(len(out), 'grounded rows')
    for kk, v in sorted(c.items()):
        print(' ', kk, v)
    print(Counter((o['stratum'], o['confidence'], o['pass']) for o in out))


# ---- table -----------------------------------------------------------------------------------------------------
def adopted_strata():
    """Strata whose audit reached 95% (data/graph/places/audit/sol-groundings-audit-2026-11-21.csv)."""
    agree = defaultdict(lambda: [0, 0])
    for r in csv.DictReader(open(AUDIT, encoding='utf-8')):
        if r['sol_verdict'] != 'grounded':
            continue
        agree[(r['stratum'], r['confidence'])][1] += 1
        agree[(r['stratum'], r['confidence'])][0] += r['agree'] == 'y'
    return {k for k, (a, n) in agree.items() if n and a / n >= 0.95}, dict(agree)


def table():
    ok, agree = adopted_strata()
    C = [json.loads(l) for l in open(W / 'checked.jsonl', encoding='utf-8')]
    R = {d['case']: d for d in rows()}
    keep, held = [], []
    for o in C:
        d = R[o['case']]
        if not o['pass']:
            why = [f for f in ('ident', 'name', 'place', 'exists') if not o[f]]
            why += ['lc_other: LC id is P244 of ' + ','.join(o['lc_other'])] if o['lc_other'] else []
            why += ['collide: ' + o['collide']] if o['collide'] else []
            why += ['lc_twin: the LC twin of this non-LC heading is not grounded to the same QID'] if o['lc_twin_unclear'] else []
            held.append(dict(o, held='machine check: ' + '; '.join(why), checks=' '.join(w.split(':')[0] for w in why)))
            continue
        if (o['stratum'], o['confidence']) not in ok:
            held.append(dict(o, held=f"stratum {o['stratum']}/{o['confidence']} below the audit bar"))
            continue
        keep.append(dict(heading=o['heading'], parent=o['parent'], thesaurus='fr' if o['route'] == 'not-used' else 'lc',
                         qid=o['qid'], qid_label=o['qid_label'], uses=o['uses'], lc_id=o['lc_id'],
                         basis=f"{d.get('basis') or ''} [identifier check: {', '.join(o['ident_hits'])}]",
                         confidence=o['confidence'], case=o['case'], provenance=PROVENANCE))
    # one QID per (heading, parent, thesaurus)
    seen = Counter((k['heading'], k['parent'], k['thesaurus']) for k in keep)
    dup = {x for x, n in seen.items() if n > 1}
    clash = {x for x in dup if len({k['qid'] for k in keep if (k['heading'], k['parent'], k['thesaurus']) == x}) > 1}
    keep = [k for k in keep if (k['heading'], k['parent'], k['thesaurus']) not in clash]
    uniq = {}
    for k in keep:
        uniq.setdefault((k['heading'], k['parent'], k['thesaurus']), k)
    keep = sorted(uniq.values(), key=lambda k: (-k['uses'], k['heading']))
    fields = ['heading', 'parent', 'thesaurus', 'qid', 'qid_label', 'uses', 'lc_id', 'confidence', 'case', 'basis', 'provenance']
    with gzip.open(TABLE, 'wt', newline='', encoding='utf-8', compresslevel=9) as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(keep)
    with open(HELD, 'w', newline='', encoding='utf-8') as fh:
        hf = ['case', 'heading', 'parent', 'route', 'uses', 'qid', 'qid_label', 'confidence', 'stratum', 'checks', 'held']
        w = csv.DictWriter(fh, fieldnames=hf, extrasaction='ignore')
        w.writeheader()
        w.writerows(sorted(held, key=lambda h: -h['uses']))
    # not a place: Sol high confidence, audited class
    npl = [d for d in R.values() if d['verdict'] == 'not-a-place']
    np_ok = audit_ok('not-a-place')
    with open(NOT_PLACES, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['heading', 'parent', 'thesaurus', 'uses', 'reason', 'case', 'provenance'])
        w.writeheader()
        for d in sorted(npl, key=lambda d: -d['q_uses']):
            if np_ok and d['confidence'] == 'high':
                w.writerow(dict(heading=d['q_heading'], parent=d['q_parent'], thesaurus='fr' if d['route'] == 'not-used' else 'lc',
                                uses=d['q_uses'], reason=(d.get('reason') or '')[:300], case=d['case'], provenance=PROVENANCE))
    rep = dict(adopted_strata=sorted('/'.join(x) for x in ok), audit={'/'.join(k): v for k, v in agree.items()},
               grounded_rows=len(C), adopted=len(keep), adopted_uses=sum(k['uses'] for k in keep),
               held=len(held), held_by_reason=Counter('machine check' if h['held'].startswith('machine') else 'stratum below bar'
                                                      for h in held),
               held_machine_failed_check=Counter(c for h in held for c in h.get('checks', '').split()),
               held_uses=sum(h['uses'] for h in held),
               key_clash=len(clash), not_places=sum(1 for d in npl if np_ok and d['confidence'] == 'high'))
    (OUT / 'audit/sol-groundings-report-2026-11-21.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=dict) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=dict))


def audit_ok(verdict):
    n = a = 0
    for r in csv.DictReader(open(AUDIT, encoding='utf-8')):
        if r['sol_verdict'] == verdict:
            n += 1
            a += r['agree'] == 'y'
    return n > 0 and a / n >= 0.95


# ---- report: before (git HEAD tables) -> after (the rebuilt tables) ---------------------------------------------
def report():
    """Ungrounded headings and uses before -> after, overall and for headings on works about Canada or South Asia (the
    scope is fixed on the rebuilt tables: a heading counts for a region when one of its books is tagged to the region or
    a place within it); new places; works newly tagged; top newly grounded headings; Canadian probes."""
    import subprocess
    import duckdb

    def head_csv(name):
        raw = subprocess.run(['git', 'show', f'HEAD:data/graph/places/{name}'], cwd=ROOT, capture_output=True, check=True).stdout
        return list(csv.DictReader(io.StringIO(gzip.decompress(raw).decode('utf-8'))))

    def cur_csv(name):
        return list(csv.DictReader(gzip.open(OUT / name, 'rt', encoding='utf-8')))

    NOT = ('not a place:', 'a category of countries', 'a people, nation or band')
    ug0, ug1 = head_csv('ungrounded.csv.gz'), cur_csv('ungrounded.csv.gz')
    pl0, pl1 = {r['qid'] for r in head_csv('places.csv.gz')}, {r['qid']: r for r in cur_csv('places.csv.gz')}
    hier = cur_csv('place-hierarchy.csv.gz')
    kids = defaultdict(set)
    for r in hier:
        if not r['basis'].startswith(('overlaps', 'part-predecessor', 'region-contains')):
            kids[r['parent']].add(r['child'])

    def closure(roots):
        out, todo = set(roots), list(roots)
        while todo:
            for k in kids.get(todo.pop(), ()):
                if k not in out:
                    out.add(k)
                    todo.append(k)
        return out
    regions = {'Canada': closure({'Q16'}), 'South Asia': closure({'Q771405', 'Q854', 'Q668', 'Q843', 'Q902', 'Q837', 'Q917', 'Q826'}),
               'Sri Lanka': closure({'Q854'})}
    c = duckdb.connect()
    c.execute("SET memory_limit='3GB'; SET threads=2")
    c.execute(f"CREATE TABLE wp AS SELECT work, qid FROM read_csv('{OUT}/work-places.csv.gz', all_varchar=true)")
    c.execute(f"CREATE TABLE u AS SELECT key, heading, coalesce(parent, '') parent FROM '{ROOT}/build/places/uses.parquet'")
    scope = {}
    for name, qs in regions.items():
        c.execute('CREATE OR REPLACE TABLE rq AS SELECT unnest($q) qid', dict(q=sorted(qs)))
        scope[name] = {(h, p) for h, p in c.execute('''SELECT DISTINCT u.heading, u.parent FROM u JOIN wp ON wp.work = u.key
                                                        JOIN rq ON rq.qid = wp.qid''').fetchall()}

    def tally(ug):
        out = {}
        for name in ['all'] + list(regions):
            rows = [r for r in ug if not r['reason'].startswith(NOT) and (name == 'all' or (r['heading'], r['parent']) in scope[name])]
            out[name] = dict(headings=len(rows), uses=sum(int(r['uses']) for r in rows))
        out['not_places'] = dict(headings=sum(r['reason'].startswith(NOT) for r in ug),
                                 uses=sum(int(r['uses']) for r in ug if r['reason'].startswith(NOT)))
        return out
    w0 = {r['work'] for r in head_csv('work-places.csv.gz')}
    rows1 = cur_csv('work-places.csv.gz')
    w1 = {r['work'] for r in rows1}
    sol_rows = [r for r in rows1 if r['confidence'] == 'lc-sol']
    k0 = {(r['heading'], r['parent']) for r in ug0}
    k1 = {(r['heading'], r['parent']) for r in ug1}
    newly = [r for r in ug0 if (r['heading'], r['parent']) not in k1]
    tab = {(r['heading'], r['parent'], r['thesaurus']): r for r in csv.DictReader(gzip.open(TABLE, 'rt', encoding='utf-8'))}
    top = []
    for r in sorted(newly, key=lambda r: -int(r['uses'])):
        t = tab.get((r['heading'], r['parent'], 'fr' if r['route'] == 'not-used' else 'lc'))
        top.append(dict(heading=r['heading'], parent=r['parent'], uses=int(r['uses']), qid=t['qid'] if t else '',
                        label=t['qid_label'] if t else '(not a place or other)'))
    probes = [r for r in ug0 + ug1 if re.search(r'Northwest, Canadian|Prince Albert|Saskatchewan|St\. John', r['heading'] + ' ' + r['parent'])]
    pr = {}
    for r in probes:
        k = (r['heading'], r['parent'])
        pr.setdefault(k, dict(heading=r['heading'], parent=r['parent'], uses=int(r['uses']), before=None, after='grounded'))
    for r in ug0:
        if (r['heading'], r['parent']) in pr:
            pr[(r['heading'], r['parent'])]['before'] = r['reason'][:60]
    for r in ug1:
        if (r['heading'], r['parent']) in pr:
            pr[(r['heading'], r['parent'])]['after'] = r['reason'][:60]
    for k, v in pr.items():
        t = tab.get((k[0], k[1], 'lc')) or tab.get((k[0], k[1], 'fr'))
        if t and v['after'] == 'grounded':
            v['after'] = f"grounded {t['qid']} {t['qid_label']}"
    rep = dict(before=tally(ug0), after=tally(ug1), places_before=len(pl0), places_after=len(pl1),
               new_places=sorted(((q, pl1[q]['label'], int(pl1[q]['works'])) for q in set(pl1) - pl0), key=lambda x: -x[2])[:40],
               new_places_count=len(set(pl1) - pl0), works_tagged_before=len(w0), works_tagged_after=len(w1),
               works_newly_tagged=len(w1 - w0), lc_sol_rows=len(sol_rows), lc_sol_works=len({r['work'] for r in sol_rows}),
               headings_newly_grounded=len(newly), top_newly_grounded=top[:20],
               probes=sorted(pr.values(), key=lambda v: -v['uses'])[:40])
    (OUT / 'audit/sol-groundings-before-after-2026-11-22.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('new_places', 'probes')}, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    {'clean': clean, 'fetch': fetch, 'check': check, 'table': table, 'report': report}[sys.argv[1]]()
