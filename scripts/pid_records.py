"""Read the Wikidata item and the ORCID record of EVERY person key that holds the identifier (2026-11-14; §8 class 42).

Probe: Hilde Leikny Sommerseth p-7813 (orcid:0000-0001-7070-8184, wd:Q73387091) had no affiliation, although her
Wikidata item states her employer (P108 UiT) and her ORCID record lists UiT. The employment harvest of 2026-09/10
(data/field-research/historian-positions-2026-10-29) read only people found by a Wikidata query for
occupation=historian with an ORCID; keys that gained wd:/orcid: anchors by any other route were never read for
anything but works. This step reads both records by identifier for every anchored person key, so a new anchor is
read on the next run without a hand-made list (the targets come from the key-log cache every time; cached
identifiers are not fetched again unless --refresh).

Identifiers only: no name search, no search API. Raw responses stay on E: and never go into git.

    python3 scripts/pid_records.py targets                  # anchored person keys from build/keylog-state.sqlite
    python3 scripts/pid_records.py wikidata                 # QLever, VALUES batches (resumable)
    python3 scripts/pid_records.py orcid [--rate 6]         # pub.orcid.org v3.0 /record (resumable)
    python3 scripts/pid_records.py export                   # parse both caches -> data/graph/pid-records/

Outputs (tracked, facts only; scripts/export_affiliations.py, build_life_years.py, key_pid_record_ids.py read them):
- data/graph/pid-records/affiliations.csv.gz: person key, source (orcid / wikidata), kind (employment / education /
  qualification / position), organisation name, its ROR, GRID, Ringgold or Wikidata id, country, role, department,
  degree, start and end years, the identifier the row was read from;
- data/graph/pid-records/identifiers.csv.gz: external identifiers on the Wikidata item (P244 LC, P214 VIAF, ...) and
  on the ORCID record (Scopus, ResearcherID, ...), with the key's own anchor of the same scheme when it has one;
- data/graph/pid-records/advisors.csv.gz: Wikidata P184 / P185 pairs, keyed on both sides where the item is on a key;
- data/graph/pid-records/life-dates.csv.gz: Wikidata P569 / P570 with precision (year precision or finer is used);
- data/graph/pid-records/facts.csv.gz: P106 occupation, P101 field of work, P27 citizenship (QID and English label);
- data/graph/pid-records/coverage.json: fetched, empty, private, failed, by harvest.
No identity or ethnicity statement is read (no P172; OCAP practice), and no gender (P21).
"""
import argparse, collections, csv, gzip, hashlib, json, os, re, sqlite3, sys, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DB = ROOT / 'build/keylog-state.sqlite'
WD_DIR = Path('/mnt/e/wikidata-keys-2026-11-14')
OR_DIR = Path('/mnt/e/orcid-keys-2026-11-14')
OUT = ROOT / 'data/graph/pid-records'
UA = 'historiography-kg/1.0 (research; identifier reads)'
QLEVER = 'https://qlever.dev/api/wikidata'
P = ('PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> '
     'PREFIX p: <http://www.wikidata.org/prop/> PREFIX ps: <http://www.wikidata.org/prop/statement/> '
     'PREFIX pq: <http://www.wikidata.org/prop/qualifier/> PREFIX psv: <http://www.wikidata.org/prop/statement/value/> '
     'PREFIX wikibase: <http://wikiba.se/ontology#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> '
     'PREFIX owl: <http://www.w3.org/2002/07/owl#> ')
# external identifiers worth reading for linking (scheme name used in the tables; anchor namespace where the key log
# already has one). Google Scholar (P1960) is not needed.
WD_IDS = {'P244': 'lcnaf', 'P214': 'viaf', 'P227': 'gnd', 'P213': 'isni', 'P269': 'idref', 'P496': 'orcid',
          'P2287': 'cristin', 'P268': 'bnf', 'P1006': 'nta', 'P906': 'selibr', 'P5587': 'libris', 'P1207': 'nukat',
          'P349': 'ndl', 'P271': 'cinii', 'P1007': 'lattes', 'P1607': 'dialnet', 'P549': 'mgp', 'P1153': 'scopus',
          'P1053': 'researcherid', 'P10283': 'openalex', 'P4012': 'semanticscholar', 'P1015': 'noraf',
          'P409': 'nla', 'P1271': 'nkc', 'P950': 'bne', 'P396': 'sbn', 'P1375': 'nsk', 'P691': 'nkc-aut',
          'P1280': 'cantic', 'P8189': 'nli', 'P3430': 'snac', 'P1053 ': 'researcherid', 'P8034': 'vatican',
          'P1695': 'nlp', 'P7859': 'worldcat', 'P245': 'ulan', 'P1960': None}
WD_IDS = {k.strip(): v for k, v in WD_IDS.items() if v}
WD_FACTS = {'P106': 'occupation', 'P101': 'field', 'P27': 'citizenship', 'P31': 'instance_of'}
WD_PEOPLE = {'P184': 'doctoral_advisor', 'P185': 'doctoral_student'}
STMT = {'P108': 'employment', 'P69': 'education', 'P39': 'position'}


def targets():
    """{'wd': {qid: [keys]}, 'orcid': {id: [keys]}} for live person keys, from the key-log cache (read only)."""
    con = sqlite3.connect(f'file:{CACHE_DB}?mode=ro', uri=True)
    out = {'wd': collections.defaultdict(list), 'orcid': collections.defaultdict(list)}
    for scheme in ('wd', 'orcid'):     # one range scan per scheme (an OR makes SQLite scan the whole anchor table)
        for a, k in con.execute("""SELECT a.anchor, a.key FROM anchor a CROSS JOIN keys k ON k.key = a.key
                                   WHERE a.anchor >= ? AND a.anchor < ?
                                   AND k.type = 'person' AND k.status IN ('active', 'provisional')""", (scheme + ':', scheme + ';')):
            s, v = a.split(':', 1)
            out[s][v].append(k)
    return out


def write_targets():
    t = targets()
    WD_DIR.mkdir(parents=True, exist_ok=True); OR_DIR.mkdir(parents=True, exist_ok=True)
    (WD_DIR / 'targets.json').write_text(json.dumps(t['wd']))
    (OR_DIR / 'targets.json').write_text(json.dumps(t['orcid']))
    print('wd', len(t['wd']), 'orcid', len(t['orcid']))
    return t


# ---------------------------------------------------------------- Wikidata (QLever)
def qlever(q, tries=8):
    for t in range(tries):
        try:
            req = urllib.request.Request(QLEVER, data=urllib.parse.urlencode({'query': P + q}).encode(),
                                         headers={'Accept': 'application/sparql-results+json', 'User-Agent': UA,
                                                  'Content-Type': 'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)['results']['bindings']
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get('Retry-After') or 0) or 20 * (t + 1)
            print('qlever http', e.code, 'retry in', wait, flush=True); time.sleep(wait)
        except Exception as e:
            print('qlever', type(e).__name__, e, flush=True); time.sleep(20 * (t + 1))
    return None


def v(b, k):
    x = b.get(k)
    if not x:
        return None
    s = x['value']
    return s.rsplit('/', 1)[-1] if s.startswith('http://www.wikidata.org/entity/') else s


def wd_person_queries(vals):
    stm = ' '.join(f'("{pid}" p:{pid} ps:{pid})' for pid in STMT)
    ids = ' '.join(f'wdt:{pid}' for pid in list(WD_IDS) + list(WD_FACTS) + list(WD_PEOPLE))
    return {
        'stmt': ('SELECT ?q ?prop ?st ?v ?start ?end ?pit ?degree ?thesis ?role ?of WHERE { VALUES ?q { %s } '
                 'VALUES (?prop ?pp ?ps) { %s } ?q ?pp ?st . ?st ?ps ?v . ?st wikibase:rank ?rk . '
                 'FILTER(?rk != wikibase:DeprecatedRank) '
                 'OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end } OPTIONAL { ?st pq:P585 ?pit } '
                 'OPTIONAL { ?st pq:P512 ?degree } OPTIONAL { ?st pq:P1026 ?thesis } '
                 'OPTIONAL { ?st pq:P2868|pq:P794|pq:P39 ?role } OPTIONAL { ?st pq:P642|pq:P108|pq:P2389 ?of } }') % (vals, stm),
        'vals': 'SELECT ?q ?p ?v WHERE { VALUES ?q { %s } VALUES ?p { %s owl:sameAs } ?q ?p ?v }' % (vals, ids),
        'life': ('SELECT ?q ?prop ?t ?prec WHERE { VALUES ?q { %s } VALUES (?prop ?pp ?psv) { ("P569" p:P569 psv:P569) '
                 '("P570" p:P570 psv:P570) } ?q ?pp ?st . ?st ?psv ?tv . ?tv wikibase:timeValue ?t ; wikibase:timePrecision ?prec . '
                 '?st wikibase:rank ?rk . FILTER(?rk != wikibase:DeprecatedRank) }') % vals,
        'label': ('SELECT ?q ?l WHERE { VALUES ?q { %s } ?q rdfs:label ?l . FILTER(lang(?l) = "en" || lang(?l) = "mul") }') % vals,
    }


def harvest_wikidata(batch=400, refresh=False):
    t = json.loads((WD_DIR / 'targets.json').read_text())
    bdir = WD_DIR / 'batches'; bdir.mkdir(parents=True, exist_ok=True)
    done = set() if refresh else {l.strip() for f in bdir.glob('*.qids') for l in f.read_text().split()}
    todo = sorted(q for q in t if q not in done and re.fullmatch(r'Q\d+', q))
    print('wikidata: targets', len(t), 'cached', len(done), 'to fetch', len(todo), flush=True)
    for i in range(0, len(todo), batch):
        qs = todo[i:i + batch]
        name = f'{time.strftime("%Y%m%dT%H%M%S")}-{hashlib.sha1(" ".join(qs).encode()).hexdigest()[:10]}'
        vals = ' '.join('wd:' + q for q in qs)
        res = {}
        for k, q in wd_person_queries(vals).items():
            res[k] = qlever(q)
            if res[k] is None:
                raise SystemExit(f'QLever gave up on batch {i} ({k}); rerun to resume')
            time.sleep(1.5)
        with gzip.open(bdir / f'{name}.json.gz', 'wt') as f:
            json.dump(res, f)
        (bdir / f'{name}.qids').write_text('\n'.join(qs))
        print(f'{i + len(qs)}/{len(todo)}', {k: len(x) for k, x in res.items()}, flush=True)
    harvest_wd_items()
    harvest_wd_parents()


def wd_person_rows():
    for f in sorted((WD_DIR / 'batches').glob('*.json.gz')):
        with gzip.open(f, 'rt') as fh:
            yield f.name[:-8], json.load(fh)


def harvest_wd_items(batch=500):
    """Labels, ROR (P6782), country, and the organisation an office belongs to (P2389, P361) of every item the
    person statements point to (employers, schools, offices, degrees, roles, occupations, fields, countries)."""
    want = set()
    for _, res in wd_person_rows():
        for b in res['stmt']:
            for k in ('v', 'degree', 'role', 'of'):
                x = v(b, k)
                if x and re.fullmatch(r'Q\d+', x):
                    want.add(x)
        for b in res['vals']:
            if b['p']['value'].rsplit('/', 1)[-1] in WD_FACTS:
                x = v(b, 'v')
                if x and re.fullmatch(r'Q\d+', x):
                    want.add(x)
    path = WD_DIR / 'items.json'
    have = json.loads(path.read_text()) if path.exists() else {}
    # offices: their organisation is fetched in a second round
    for rnd in range(2):
        todo = sorted(want - set(have))
        print('items: want', len(want), 'to fetch', len(todo), flush=True)
        for i in range(0, len(todo), batch):
            qs = todo[i:i + batch]
            vals = ' '.join('wd:' + q for q in qs)
            got = {q: dict(label=None, ror=[], country=[], org=[], grid=[]) for q in qs}
            for b in qlever('SELECT ?i ?l WHERE { VALUES ?i { %s } ?i rdfs:label ?l . FILTER(lang(?l) = "en" || lang(?l) = "mul") }' % vals) or []:
                if b['l'].get('xml:lang') == 'en' or not got[v(b, 'i')]['label']:
                    got[v(b, 'i')]['label'] = b['l']['value']
            time.sleep(1)
            for b in qlever('SELECT ?i ?p ?x WHERE { VALUES ?i { %s } VALUES ?p { wdt:P6782 wdt:P17 wdt:P2389 wdt:P2427 } ?i ?p ?x }' % vals) or []:
                key = {'P6782': 'ror', 'P17': 'country', 'P2389': 'org', 'P2427': 'grid'}[b['p']['value'].rsplit('/', 1)[-1]]
                got[v(b, 'i')][key].append(v(b, 'x'))
            time.sleep(1)
            nolabel = [q for q in qs if not got[q]['label']]
            if nolabel:     # any language
                for b in qlever('SELECT ?i (SAMPLE(?l) AS ?lab) WHERE { VALUES ?i { %s } ?i rdfs:label ?l } GROUP BY ?i'
                                % ' '.join('wd:' + q for q in nolabel)) or []:
                    got[v(b, 'i')]['label'] = b['lab']['value']
                time.sleep(1)
            have.update(got)
            path.write_text(json.dumps(have))
            print(f'items {i + len(qs)}/{len(todo)}', flush=True)
        want |= {o for q in want if q in have for o in have[q]['org']}
    for q in have:
        for o in have[q]['org']:
            want.add(o)


def harvest_wd_parents(batch=500):
    """The parent organisation (P361 part of, P749 parent organisation) of every item, and that parent's ROR: a college
    of Oxford, Harvard Law School or a faculty is grounded at university level, as the existing groundings are."""
    path = WD_DIR / 'items.json'
    have = json.loads(path.read_text())
    todo = sorted(q for q, v in have.items() if 'parent' not in v)
    print('parents: to fetch', len(todo), flush=True)
    for i in range(0, len(todo), batch):
        qs = todo[i:i + batch]
        for q in qs:
            have[q]['parent'] = []
        for b in qlever('SELECT ?i ?x WHERE { VALUES ?i { %s } ?i wdt:P361|wdt:P749 ?x }' % ' '.join('wd:' + q for q in qs)) or []:
            x = v(b, 'x')
            if x and re.fullmatch(r'Q\d+', x):
                have[v(b, 'i')]['parent'].append(x)
        time.sleep(1)
        path.write_text(json.dumps(have))
    missing = sorted({x for q in have.values() for x in q.get('parent', [])} - set(have))
    print('parents: new parent items', len(missing), flush=True)
    for i in range(0, len(missing), batch):
        qs = missing[i:i + batch]
        got = {q: dict(label=None, ror=[], country=[], org=[], grid=[], parent=[]) for q in qs}
        for b in qlever('SELECT ?i ?p ?x WHERE { VALUES ?i { %s } VALUES ?p { wdt:P6782 wdt:P17 rdfs:label } ?i ?p ?x . '
                        'FILTER(?p != rdfs:label || lang(?x) = "en") }' % ' '.join('wd:' + q for q in qs)) or []:
            pp = b['p']['value'].rsplit('/', 1)[-1].rsplit('#', 1)[-1]
            if pp == 'label':
                got[v(b, 'i')]['label'] = b['x']['value']
            else:
                got[v(b, 'i')]['ror' if pp == 'P6782' else 'country'].append(v(b, 'x'))
        have.update(got)
        time.sleep(1)
        path.write_text(json.dumps(have))


# ---------------------------------------------------------------- ORCID
class Rate:
    def __init__(self, per_s):
        self.gap, self.lock, self.next = 1.0 / per_s, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next)
            self.next = t + self.gap
        time.sleep(max(0.0, t - time.monotonic()))


def orcid_path(oid):
    return OR_DIR / 'records' / oid[-4:-2] / f'{oid}.json.gz'


def harvest_orcid(rate=6.0, workers=4, refresh=False):
    t = json.loads((OR_DIR / 'targets.json').read_text())
    statf = OR_DIR / 'status.jsonl'
    status = {}
    if statf.exists():
        for l in statf.read_text().splitlines():
            r = json.loads(l); status[r['id']] = r['status']
    todo = [o for o in sorted(t) if refresh or not (orcid_path(o).exists() or status.get(o) in (404, 409, 410))]
    print('orcid: targets', len(t), 'to fetch', len(todo), flush=True)
    lim, lock, q = Rate(rate), threading.Lock(), list(reversed(todo))
    stats = collections.Counter()
    pause = {'until': 0.0}

    def one(oid):
        url = f'https://pub.orcid.org/v3.0/{oid}/record'
        for attempt in range(12):
            while time.monotonic() < pause['until']:
                time.sleep(1)
            lim.wait()
            try:
                req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                p = orcid_path(oid); p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix('.tmp'); tmp.write_bytes(gzip.compress(body)); os.replace(tmp, p)
                return 200
            except urllib.error.HTTPError as e:
                if e.code in (404, 409, 410):
                    return e.code
                if e.code in (429, 503, 502, 500, 504):     # the whole client stands back, longer each time
                    with lock:
                        pause['n'] = pause.get('n', 0) + 1
                        wait = int(e.headers.get('Retry-After') or 0) or min(600, 60 * pause['n'])
                        pause['until'] = max(pause['until'], time.monotonic() + wait)
                        print('orcid', e.code, 'pausing', wait, 's', flush=True)
                    continue
                return e.code
            except Exception:
                time.sleep(5 * (attempt + 1))
        return 'failed'

    def worker():
        while True:
            with lock:
                if not q:
                    return
                oid = q.pop()
            s = one(oid)
            with lock:
                stats[s] += 1
                if s != 200:
                    with statf.open('a') as fh:
                        fh.write(json.dumps(dict(id=oid, status=s, at=time.strftime('%Y-%m-%dT%H:%M:%S'))) + '\n')
                n = sum(stats.values())
                if n % 500 == 0:
                    print(n, len(todo), dict(stats), flush=True)
    ths = [threading.Thread(target=worker) for _ in range(workers)]
    for th in ths:
        th.start()
    for th in ths:
        th.join()
    print('orcid done', dict(stats), flush=True)


# ---------------------------------------------------------------- export
def year_of(s):
    m = re.match(r'^[+]?(-?\d{1,4})-', s or '')
    return int(m.group(1)) if m else None


def odate(d):
    try:
        return int(d['year']['value']) if d and d.get('year') else None
    except (TypeError, ValueError):
        return None


def export():
    OUT.mkdir(parents=True, exist_ok=True)
    tw = json.loads((WD_DIR / 'targets.json').read_text())
    to = json.loads((OR_DIR / 'targets.json').read_text())
    items = json.loads((WD_DIR / 'items.json').read_text()) if (WD_DIR / 'items.json').exists() else {}
    lab = lambda q: (items.get(q) or {}).get('label') or ''
    cov = dict(wikidata=collections.Counter(), orcid=collections.Counter())
    aff, ids, adv, life, facts = [], [], [], [], []
    idcount = collections.Counter()
    # ---- Wikidata
    seen = set()
    for _, res in wd_person_rows():
        stm = collections.defaultdict(lambda: dict(start=set(), end=set(), pit=set(), degree=set(), thesis=set(), role=set(), of=set()))
        per_q = collections.Counter()
        for b in res['stmt']:
            q, prop, st, val = v(b, 'q'), v(b, 'prop'), b['st']['value'], v(b, 'v')
            d = stm[(q, prop, st, val)]
            per_q[q] += 1
            for k in ('start', 'end', 'pit'):
                if v(b, k):
                    d[k].add(year_of(v(b, k)))
            for k in ('degree', 'thesis', 'role', 'of'):
                if v(b, k):
                    d[k].add(v(b, k))
        for (q, prop, st, val), d in stm.items():
            kind = STMT[prop]
            org = val
            role = ''
            if kind == 'position':      # an office: its organisation from the qualifier or the office item (P2389)
                role = lab(val)
                orgs = sorted(d['of']) or (items.get(val) or {}).get('org', [])
                if not orgs:
                    continue
                org = orgs[0]
            else:
                role = '; '.join(sorted(filter(None, (lab(x) for x in d['role']))))
            it = items.get(org) or {}
            if not it.get('ror'):           # a college or faculty: its parent's ROR (university level)
                prs = [p for p in it.get('parent', []) if (items.get(p) or {}).get('ror')]
                if len(prs) == 1:
                    it = dict(it, ror=items[prs[0]]['ror'], grid=[])
            ys = lambda s: sorted(y for y in s if y is not None)
            st0, en0, pit = ys(d['start']), ys(d['end']), ys(d['pit'])
            for key in tw.get(q, []):
                aff.append(dict(person=key, source='wikidata', kind=kind, org_name=lab(org) or org, org_ror=';'.join(it.get('ror', [])),
                                org_grid=';'.join(it.get('grid', [])), org_ringgold='', org_wd=org,
                                country=';'.join(lab(c) for c in it.get('country', [])), role=role, department='',
                                degree='; '.join(sorted(filter(None, (lab(x) for x in d['degree'])))),
                                start_year=(st0[0] if st0 else (pit[0] if pit else '')), end_year=(en0[-1] if en0 else (pit[-1] if pit else '')),
                                thesis=';'.join(sorted(d['thesis'])), via=f'wd:{q}'))
        vals = collections.defaultdict(lambda: collections.defaultdict(set))
        for b in res['vals']:
            vals[v(b, 'q')][b['p']['value'].rsplit('/', 1)[-1].replace('#', ':')].add(v(b, 'v'))
        for b in res['life']:
            life.append((v(b, 'q'), v(b, 'prop'), b['t']['value'], int(float(b['prec']['value']))))
        labelled = {v(b, 'q') for b in res['label']}
        for q in set(vals) | labelled | set(per_q):
            seen.add(q)
        for q, ps in vals.items():
            for pid, vs in ps.items():
                if pid in WD_IDS:
                    for x in sorted(vs):
                        idcount[('wikidata', WD_IDS[pid])] += 1
                        for key in tw.get(q, []):
                            ids.append(dict(person=key, source='wikidata', via=f'wd:{q}', scheme=WD_IDS[pid], prop=pid, value=x))
                elif pid in WD_FACTS:
                    for x in sorted(vs):
                        for key in tw.get(q, []):
                            facts.append(dict(person=key, via=f'wd:{q}', fact=WD_FACTS[pid], qid=x, label=lab(x)))
                elif pid in WD_PEOPLE:
                    for x in sorted(vs):
                        a, s = (x, q) if pid == 'P184' else (q, x)
                        adv.append(dict(advisor_qid=a, student_qid=s, prop=pid))
                elif pid == 'owl:sameAs':
                    for x in vs:
                        for key in tw.get(q, []):
                            facts.append(dict(person=key, via=f'wd:{q}', fact='redirect', qid=x, label=''))
    fetched = {l.strip() for f in (WD_DIR / 'batches').glob('*.qids') for l in f.read_text().split()}
    cov['wikidata'].update(targets=len(tw), fetched=len(fetched & set(tw)), with_statements=len(seen & set(tw)),
                           empty_or_deleted=len((fetched & set(tw)) - seen), not_fetched=len(set(tw) - fetched),
                           with_employer=len({r['via'] for r in aff if r['kind'] == 'employment'}),
                           with_education=len({r['via'] for r in aff if r['kind'] == 'education'}))
    # ---- ORCID
    statf = OR_DIR / 'status.jsonl'
    status = {}
    if statf.exists():
        for l in statf.read_text().splitlines():
            r = json.loads(l); status[r['id']] = r['status']
    for oid, keys in sorted(to.items()):
        p = orcid_path(oid)
        if not p.exists():
            s = status.get(oid, 'not fetched')
            cov['orcid'][{404: 'not_found', 409: 'deactivated_or_locked', 410: 'gone'}.get(s, f'failed_{s}')] += 1
            continue
        try:
            rec = json.loads(gzip.decompress(p.read_bytes()))
        except Exception:
            cov['orcid']['unreadable'] += 1; continue
        cov['orcid']['fetched'] += 1
        acts = rec.get('activities-summary') or {}
        n = 0
        for sect, kind in (('employments', 'employment'), ('educations', 'education'), ('qualifications', 'qualification'),
                           ('invited-positions', 'position'), ('distinctions', None), ('memberships', None), ('services', None)):
            if not kind:
                continue
            for g in ((acts.get(sect) or {}).get('affiliation-group') or []):
                for s in g.get('summaries') or []:
                    e = next(iter(s.values()))
                    org = e.get('organization') or {}
                    dis = org.get('disambiguated-organization') or {}
                    src, did = (dis.get('disambiguation-source') or ''), (dis.get('disambiguated-organization-identifier') or '')
                    n += 1
                    for key in keys:
                        aff.append(dict(person=key, source='orcid', kind=kind, org_name=org.get('name') or '',
                                        org_ror=did.rsplit('/', 1)[-1] if src == 'ROR' else '',
                                        org_grid=did if src == 'GRID' else '', org_ringgold=did if src == 'RINGGOLD' else '',
                                        org_wd='', country=(org.get('address') or {}).get('country') or '',
                                        role=e.get('role-title') or '', department=e.get('department-name') or '', degree='',
                                        start_year=odate(e.get('start-date')) or '', end_year=odate(e.get('end-date')) or '',
                                        thesis='', via=f'orcid:{oid}'))
        person = rec.get('person') or {}
        for x in ((person.get('external-identifiers') or {}).get('external-identifier') or []):
            idcount[('orcid', x.get('external-id-type'))] += 1
            for key in keys:
                ids.append(dict(person=key, source='orcid', via=f'orcid:{oid}', scheme=(x.get('external-id-type') or '').lower(),
                                prop='', value=x.get('external-id-value') or ''))
        for x in ((person.get('other-names') or {}).get('other-name') or []):
            for key in keys:
                facts.append(dict(person=key, via=f'orcid:{oid}', fact='other_name', qid='', label=x.get('content') or ''))
        nm = person.get('name') or {}
        if nm:
            for key in keys:
                facts.append(dict(person=key, via=f'orcid:{oid}', fact='name', qid='',
                                  label=' | '.join(str((nm.get(k) or {}).get('value') or '') for k in ('given-names', 'family-name', 'credit-name'))))
        cov['orcid']['with_affiliation' if n else 'no_affiliation'] += 1
        if not acts or not any(((acts.get(s) or {}).get('affiliation-group') or (acts.get(s) or {}).get('group'))
                               for s in ('employments', 'educations', 'qualifications', 'works', 'fundings', 'peer-reviews')):
            cov['orcid']['empty_or_private'] += 1
    cov['orcid']['targets'] = len(to)
    # ---- write
    def w(name, rows, cols):
        with gzip.open(OUT / name, 'wt', newline='', encoding='utf-8') as f:
            wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
    w('affiliations.csv.gz', sorted(aff, key=lambda r: (r['person'], r['source'], r['kind'], str(r['start_year']))),
      ['person', 'source', 'kind', 'org_name', 'org_ror', 'org_grid', 'org_ringgold', 'org_wd', 'country', 'role', 'department',
       'degree', 'start_year', 'end_year', 'thesis', 'via'])
    w('identifiers.csv.gz', sorted(ids, key=lambda r: (r['person'], r['scheme'], r['value'])),
      ['person', 'source', 'via', 'scheme', 'prop', 'value'])
    w('facts.csv.gz', sorted(facts, key=lambda r: (r['person'], r['fact'], r['qid'], r['label'])), ['person', 'via', 'fact', 'qid', 'label'])
    keyed = lambda q: tw.get(q, [])
    advrows = {}
    for r in adv:
        k = (r['advisor_qid'], r['student_qid'])
        a = advrows.setdefault(k, dict(advisor_qid=k[0], student_qid=k[1], props=set()))
        a['props'].add(r['prop'])
    w('advisors.csv.gz', [dict(advisor_qid=a, student_qid=s, props=' '.join(sorted(r['props'])),
                               advisor_keys=' '.join(keyed(a)), student_keys=' '.join(keyed(s)))
                          for (a, s), r in sorted(advrows.items())],
      ['advisor_qid', 'student_qid', 'props', 'advisor_keys', 'student_keys'])
    w('life-dates.csv.gz', [dict(qid=q, prop=p, time=t, precision=pr) for q, p, t, pr in sorted(set(life))],
      ['qid', 'prop', 'time', 'precision'])
    # the life-years cache scripts/build_life_years.py reads ({qid: [birth, death]}: the earliest year of year precision
    # or finer, as scripts/wd_life_years.py), kept on E: beside the earlier caches
    ly = {q: [None, None] for q in fetched & set(tw)}
    for q, prop, t, pr in set(life):
        y = year_of(t)
        if pr >= 9 and y is not None and q in ly:
            i = 0 if prop == 'P569' else 1
            ly[q][i] = y if ly[q][i] is None else min(ly[q][i], y)
    (Path('/mnt/e/kg-facts') / 'wd-life-years-2026-11-14.json').write_text(json.dumps(ly))
    cov['wikidata']['with_birth_year'] = sum(1 for x in ly.values() if x[0] is not None)
    cov['wikidata']['with_death_year'] = sum(1 for x in ly.values() if x[1] is not None)
    cov['identifiers_by_scheme'] ={f'{s}:{k}': n for (s, k), n in sorted(idcount.items(), key=lambda x: -x[1])}
    cov['affiliation_rows'] = dict(collections.Counter(f"{r['source']}:{r['kind']}" for r in aff))
    cov['advisor_pairs'] = dict(both_keyed=sum(1 for a, s in advrows if keyed(a) and keyed(s)),
                                one_side_keyed=sum(1 for a, s in advrows if bool(keyed(a)) != bool(keyed(s))), total=len(advrows))
    cov = {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in cov.items()}
    (OUT / 'coverage.json').write_text(json.dumps(cov, indent=1) + '\n')
    print(json.dumps({k: v for k, v in cov.items() if k != 'identifiers_by_scheme'}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('cmd', choices=['targets', 'wikidata', 'items', 'parents', 'orcid', 'export'])
    ap.add_argument('--rate', type=float, default=6.0)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--refresh', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'targets':
        write_targets()
    elif a.cmd == 'wikidata':
        harvest_wikidata(refresh=a.refresh)
    elif a.cmd == 'items':
        harvest_wd_items()
    elif a.cmd == 'parents':
        harvest_wd_parents()
    elif a.cmd == 'orcid':
        harvest_orcid(a.rate, a.workers, a.refresh)
    else:
        export()


if __name__ == '__main__':
    main()
