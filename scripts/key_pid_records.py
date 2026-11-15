"""Identifiers, possible duplicates, conflicts and institution keys from the ORCID records and Wikidata items of every
anchored person key (2026-11-14; §8 class 42). Reads scripts/pid_records.py's tables in data/graph/pid-records/ and
data/graph/institutions-unkeyed.csv.gz (scripts/export_affiliations.py); writes, never applies:

- data/identifiers/wikidata-orcid-read-2026-11-14/proposal.json: `attach` of the external identifiers on a key's own
  Wikidata item (lcnaf P244, viaf P214, gnd P227, isni P213, idref P269, orcid P496, cristin P2287, and the national
  authority / researcher ids below) where no other key holds the identifier and the key holds no different value of a
  single-valued scheme (lcnaf, orcid, cristin, gnd, idref, lattes, ...); decided_by rule; validated by a dry run on the
  key-log cache;
- possible-duplicates.csv: the identifier is already on ANOTHER person key (two keys sharing an LC / VIAF / ORCID
  through Wikidata: strong merge candidates), with works held, ranked;
- conflicts.csv + the report's counts by kind: candidates for wrong anchors (an item P496 or P244 that differs from the
  key's orcid:/lcnaf: anchor, a Wikidata birth year that makes a held thesis or the first work implausible, an item that
  is not a human, a redirected item, an ORCID whose doctorate or employment contradicts the key's other facts, an ORCID
  iD with a bad check digit, a deactivated or missing ORCID record, a person who died before ORCID existed);
- institutions-proposal.json: `mint` of an institution key for every ROR organisation the records reach that the key
  log has not keyed (anchor ror:<id>, members inst-name:<printed name>, ror-wikidata:<QID>), as scripts/key_institutions.py.

    python3 scripts/key_pid_records.py
"""
import collections, csv, gzip, json, os, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import duckdb
import identifiers as I
import keylog_snapshot as KS

ROOT = Path(__file__).resolve().parents[1]
PR = ROOT / 'data/graph/pid-records'
OUT = ROOT / 'data/identifiers/wikidata-orcid-read-2026-11-14'
G = ROOT / 'build/graph'
LIFE = ROOT / 'data/person-facts/life-years.csv.gz'
UNKEYED = ROOT / 'data/graph/institutions-unkeyed.csv.gz'
AFF = ROOT / 'data/graph/affiliations.csv.gz'
# schemes proposed as anchors. Existing namespaces: lcnaf, viaf, gnd, isni, idref, orcid (PUBLIC_SCHEMES). New ones
# (cristin and the national authorities) need adding to identifiers.PUBLIC_SCHEMES to count toward `established`
# and to graph_explorer.LINKS to be linked on the page; nothing else in the key log checks a namespace.
ANCHOR_SCHEMES = {'lcnaf', 'viaf', 'gnd', 'isni', 'idref', 'orcid', 'cristin', 'bnf', 'nta', 'ndl', 'nkc', 'bne',
                  'sbn', 'nla', 'noraf', 'lattes', 'selibr', 'libris', 'nukat', 'cinii', 'dialnet', 'mgp'}
# one value per person by design: a different value on the key is a conflict, not a second anchor (VIAF and ISNI
# clusters split and merge, so a person can hold two)
SINGLE = {'lcnaf', 'orcid', 'cristin', 'gnd', 'idref', 'bnf', 'nta', 'ndl', 'lattes', 'mgp', 'dialnet'}
NEW_SCHEMES = sorted(ANCHOR_SCHEMES - I.PUBLIC_SCHEMES)
SEVERITY = {'wd_not_human': 1, 'wd_orcid_differs': 1, 'orcid_bad_checksum': 1, 'orcid_died_before_orcid': 2,
            'wd_lcnaf_differs': 2, 'birth_vs_thesis': 2, 'orcid_doctorate_elsewhere': 3, 'orcid_name_differs': 3,
            'orcid_employment_before_birth': 3, 'birth_vs_first_work': 4, 'wd_single_scheme_differs': 4,
            'wd_redirected': 5, 'orcid_deactivated': 5, 'orcid_not_found': 5}


def norm(scheme, v):
    v = (v or '').strip()
    if scheme == 'isni':
        return v.replace(' ', '').upper()
    if scheme == 'lcnaf':
        return v.replace(' ', '')
    if scheme == 'orcid':
        return v.upper() if re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dXx]', v) else None
    return v


def orcid_ok(o):
    """ISO 7064 11,2 check digit."""
    d = o.replace('-', '')
    if not re.fullmatch(r'\d{15}[\dX]', d):
        return False
    t = 0
    for c in d[:-1]:
        t = (t + int(c)) * 2
    r = (12 - t % 11) % 11
    return d[-1] == ('X' if r == 10 else str(r))


def fam(s):
    s = re.sub(r'\(.*?\)', '', s or '').strip()
    if ',' in s:
        s = s.split(',')[0]
    else:
        s = (s.split() or [''])[-1]
    s = s.lower().replace('ø', 'o').replace('æ', 'ae').replace('ß', 'ss').replace('ł', 'l').replace('đ', 'd')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-z]', '', s)
    return re.sub(r'([aou])e', r'\1', s)       # 'Ruepke' and 'Rüpke' (read as 'Rupke') agree


def rd(name):
    with gzip.open(PR / name, 'rt', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    I.State.load = lambda *a, **k: (_ for _ in ()).throw(SystemExit('refusing a full replay'))
    state = KS.read_state()
    db = duckdb.connect(); db.execute('SET enable_progress_bar=false')
    works = dict(db.execute(f"""SELECT "from", count(DISTINCT "to") FROM '{G}/authored.parquet' GROUP BY 1""").fetchall())
    label = dict(db.execute(f"SELECT key, label FROM '{G}/person.parquet'").fetchall())
    theses = collections.defaultdict(list)
    for p, w, y, inst in db.execute(f"""SELECT a."from", w.key, w.year, b."to" FROM '{G}/authored.parquet' a
            JOIN '{G}/work.parquet' w ON w.key = a."to" LEFT JOIN '{G}/awarded_by.parquet' b ON b."from" = w.key
            WHERE w.kind = 'thesis' AND a.evidence = 'keylog'""").fetchall():
        theses[p].append((w, y, inst))
    first_work = dict(db.execute(f"""SELECT a."from", min(w.year) FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w
            ON w.key = a."to" WHERE a.evidence = 'keylog' AND w.year BETWEEN 1500 AND 2100 GROUP BY 1""").fetchall())
    live = lambda k: (state.keys.get(k) or {}).get('status') in ('active', 'provisional')

    def holder(anchor):
        ks = [k for k in state.lookup(anchor) if state.keys[k]['type'] == 'person']
        return ks

    def own(key, scheme):
        return {a.split(':', 1)[1] for a in (state.keys.get(key) or {}).get('anchors', ()) if a.startswith(scheme + ':')}

    rep = collections.Counter()
    conflicts, dups, ops = [], [], []
    # ---- identifiers on the Wikidata item
    by_key = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rd('identifiers.csv.gz'):
        if r['source'] != 'wikidata' or r['scheme'] not in ANCHOR_SCHEMES:
            if r['source'] == 'orcid':
                rep[f"orcid record identifier {r['scheme']}"] += 1
            continue
        v = norm(r['scheme'], r['value'])
        if v:
            by_key[(r['person'], r['via'])][r['scheme']].add(v)
    seen_anchor = collections.defaultdict(set)      # a value proposed for two keys in this round
    for (key, via), schemes in by_key.items():
        for scheme, vals in schemes.items():
            for v in vals:
                seen_anchor[f'{scheme}:{v}'].add(key)
    for (key, via), schemes in sorted(by_key.items()):
        if not live(key):
            rep['key no longer live'] += 1
            continue
        add = []
        for scheme, vals in sorted(schemes.items()):
            mine = own(key, scheme)
            if scheme in SINGLE and mine and not (vals & mine):
                kind = {'orcid': 'wd_orcid_differs', 'lcnaf': 'wd_lcnaf_differs'}.get(scheme, 'wd_single_scheme_differs')
                conflicts.append(dict(kind=kind, person=key, label=label.get(key, ''), via=via,
                                      detail=f'item {scheme} {sorted(vals)} vs key {sorted(mine)}', works=works.get(key, 0)))
                rep[f'held: {scheme} differs from the key'] += 1
                continue
            if scheme in SINGLE and len(vals) > 1:
                rep[f'held: item has {len(vals)} {scheme} values'] += 1
                continue
            for v in sorted(vals):
                a = f'{scheme}:{v}'
                if v in mine:
                    rep[f'already on the key: {scheme}'] += 1
                    continue
                h = [k for k in holder(a) if k != key]
                if h:
                    for o in h:
                        dups.append(dict(person=key, label=label.get(key, ''), works=works.get(key, 0), other=o,
                                         other_label=label.get(o, ''), other_works=works.get(o, 0), scheme=scheme, value=v, via=via))
                    rep[f'collision: {scheme} on another key'] += 1
                    continue
                if len(seen_anchor[a]) > 1:
                    rep[f'held: {scheme} on two keys\' items this round'] += 1
                    continue
                add.append(a)
                rep[f'attach {scheme}'] += 1
        if add:
            ops.append(dict(event='attach', key=key, anchors=sorted(add), aliases=[], members=[], decided_by='rule',
                            basis=f"external identifiers on the key's own Wikidata item {via[3:]} (P244/P214/P227/P213/P269/"
                                  f"P496/P2287 and national authorities), read 2026-11-14; no other key holds them "
                                  f"(scripts/pid_records.py, scripts/key_pid_records.py)"))
    # ---- facts: not human, redirect
    facts = rd('facts.csv.gz')
    inst_of = collections.defaultdict(set)
    oname = {}
    for r in facts:
        if r['fact'] == 'instance_of':
            inst_of[(r['person'], r['via'])].add(r['qid'])
        elif r['fact'] == 'redirect':
            conflicts.append(dict(kind='wd_redirected', person=r['person'], label=label.get(r['person'], ''), via=r['via'],
                                  detail=f"item redirects to {r['qid']}", works=works.get(r['person'], 0)))
        elif r['fact'] == 'name':
            oname[r['person']] = r['label']
    for (p, via), qs in inst_of.items():
        if 'Q5' not in qs:
            conflicts.append(dict(kind='wd_not_human', person=p, label=label.get(p, ''), via=via,
                                  detail=f"P31 {sorted(qs)}", works=works.get(p, 0)))
    # ---- life years vs theses and first works (Wikidata years from the harvest)
    wdlife = {}
    with gzip.open(PR / 'life-dates.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if int(r['precision']) >= 9 and r['prop'] == 'P569':
                y = int(re.match(r'^[+]?(-?\d+)', r['time']).group(1))
                wdlife[r['qid']] = min(wdlife.get(r['qid'], y), y)
    wd_of = {}
    for (p, via) in inst_of:
        wd_of[p] = via[3:]
    for p, q in wd_of.items():
        b = wdlife.get(q)
        if b is None:
            continue
        for w, y, _ in theses.get(p, ()):
            if y and (y - b < 20 or y - b > 80):
                conflicts.append(dict(kind='birth_vs_thesis', person=p, label=label.get(p, ''), via=f'wd:{q}',
                                      detail=f'Wikidata birth {b}; thesis {w} {y} (age {y - b})', works=works.get(p, 0)))
        fw = first_work.get(p)
        if fw and fw - b < 15 and not any(y and 20 <= y - b <= 80 for _, y, _ in theses.get(p, ())):
            conflicts.append(dict(kind='birth_vs_first_work', person=p, label=label.get(p, ''), via=f'wd:{q}',
                                  detail=f'Wikidata birth {b}; first key-log work {fw}', works=works.get(p, 0)))
    # ---- ORCID records vs the key
    life = {}
    with gzip.open(LIFE, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            life[r['key']] = (int(r['birth']) if r['birth'] else None, int(r['death']) if r['death'] else None)
    ot = json.loads(Path('/mnt/e/orcid-keys-2026-11-14/targets.json').read_text())
    status = {}
    sp = Path('/mnt/e/orcid-keys-2026-11-14/status.jsonl')
    if sp.exists():
        for l in sp.read_text().splitlines():
            x = json.loads(l); status[x['id']] = x['status']
    for oid, keys in ot.items():
        for k in keys:
            if not orcid_ok(oid):
                conflicts.append(dict(kind='orcid_bad_checksum', person=k, label=label.get(k, ''), via=f'orcid:{oid}',
                                      detail='check digit fails', works=works.get(k, 0)))
            elif status.get(oid) == 409:
                conflicts.append(dict(kind='orcid_deactivated', person=k, label=label.get(k, ''), via=f'orcid:{oid}',
                                      detail='pub.orcid.org 409 (deactivated or locked)', works=works.get(k, 0)))
            elif status.get(oid) == 404:
                conflicts.append(dict(kind='orcid_not_found', person=k, label=label.get(k, ''), via=f'orcid:{oid}',
                                      detail='pub.orcid.org 404', works=works.get(k, 0)))
            b, d = life.get(k, (None, None))
            if d and d < 2008:
                conflicts.append(dict(kind='orcid_died_before_orcid', person=k, label=label.get(k, ''), via=f'orcid:{oid}',
                                      detail=f'death {d}; ORCID began 2012', works=works.get(k, 0)))
    pid = rd('affiliations.csv.gz')
    def toks(x):
        return {fam(t) for t in re.split(r'[\s,.\-‐]+', x or '') if len(fam(t)) >= 3}

    def family_toks(lab):
        lab = re.sub(r'\(.*?\)|,?\s*\d{4}.*$', '', lab or '')
        parts = lab.split(',', 1)[0] if ',' in lab else ' '.join(lab.split()[1:])
        return toks(parts)
    for p, nm in oname.items():     # no family-name word of the key's label in the ORCID record's names
        given, family, credit = (nm.split(' | ') + ['', '', ''])[:3]
        others = ' '.join(x['label'] for x in facts if x['person'] == p and x['fact'] == 'other_name') if False else ''
        ft = family_toks(label.get(p, ''))
        if family and ft and not (ft & toks(' '.join((given, family, credit, others)))):
            conflicts.append(dict(kind='orcid_name_differs', person=p, label=label.get(p, ''), via='',
                                  detail=f'ORCID name {given} {family} / {credit}', works=works.get(p, 0)))
    # doctorate on ORCID at another institution, in the years of the key's own thesis
    aff_inst = collections.defaultdict(list)
    with gzip.open(AFF, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['source'] == 'orcid' and r.get('kind') == 'education':
                aff_inst[r['person']].append(r)
    DOC = re.compile(r'\b(ph\.?\s?d|d\.?\s?phil|doctor|doctorat|dr\.? phil|promotion|doutorado|doctorado)', re.I)
    for p, rows in aff_inst.items():
        th = [(w, y, i) for w, y, i in theses.get(p, ()) if y and i]
        docs = [r for r in rows if DOC.search(r['rank'] or '')]
        if not th or not docs:
            continue
        if any(r['institution'] == i for r in docs for _, _, i in th):
            continue
        for r in docs:
            ry = int(r['last_year'] or r['first_year'] or 0)
            for w, y, i in th:
                if ry and abs(ry - y) <= 3:
                    conflicts.append(dict(kind='orcid_doctorate_elsewhere', person=p, label=label.get(p, ''), via='orcid',
                                          detail=f"ORCID doctorate {r['printed']} {ry} ({r['institution']}) vs thesis {w} {y} at {i}",
                                          works=works.get(p, 0)))
    for r in pid:
        if r['source'] == 'orcid' and r['kind'] == 'employment' and r['start_year']:
            b, _ = life.get(r['person'], (None, None))
            if b and int(r['start_year']) < b + 16:
                conflicts.append(dict(kind='orcid_employment_before_birth', person=r['person'], label=label.get(r['person'], ''),
                                      via=r['via'], detail=f"employment {r['org_name']} from {r['start_year']}; birth {b}",
                                      works=works.get(r['person'], 0)))
    # ---- write
    proposal = dict(basis="External identifiers on each person key's own Wikidata item, read for every key with a wd: anchor "
                          "(2026-11-14, §8 class 42); attached only where no other key holds the identifier",
                    decided_by='rule', ops=ops)
    # two files: the namespaces the log already uses plus cristin (proposal.json), and the national authorities that
    # need registering first (proposal-national-authorities.json); each validated by its own dry run
    MAIN = I.PUBLIC_SCHEMES | {'cristin'}
    split = {'proposal.json': [], 'proposal-national-authorities.json': []}
    for o in ops:
        for name, keep in (('proposal.json', lambda a: a.split(':', 1)[0] in MAIN),
                           ('proposal-national-authorities.json', lambda a: a.split(':', 1)[0] not in MAIN)):
            an = [a for a in o['anchors'] if keep(a)]
            if an:
                split[name].append(dict(o, anchors=an))
    for name, part in split.items():
        prop = dict(proposal, ops=part)
        if name != 'proposal.json':
            prop['basis'] += '; national authority namespaces not yet in identifiers.PUBLIC_SCHEMES'
        (OUT / name).write_text(json.dumps(prop, ensure_ascii=False, indent=0) + '\n')
        events, _ = I.materialise(state, prop, 'dry-run', 'dry-run', inplace=True)
        rep[f'dry_run_events {name}'] = len(events)
        rep[f'ops {name}'] = len(part)
        rep[f'anchors {name}'] = sum(len(o['anchors']) for o in part)
    dups.sort(key=lambda r: (-min(r['works'], r['other_works']), -(r['works'] + r['other_works'])))
    with open(OUT / 'possible-duplicates.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['person', 'label', 'works', 'other', 'other_label', 'other_works', 'scheme', 'value', 'via'])
        w.writeheader(); w.writerows(dups)
    # dedupe conflicts
    cseen, cl = set(), []
    for c in conflicts:
        k = (c['kind'], c['person'], c['detail'])
        if k not in cseen:
            cseen.add(k); cl.append(c)
    cl.sort(key=lambda c: (SEVERITY.get(c['kind'], 9), -int(c['works'] or 0)))
    with open(OUT / 'conflicts.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['kind', 'severity', 'person', 'label', 'works', 'via', 'detail'])
        w.writeheader()
        for c in cl:
            w.writerow(dict(c, severity=SEVERITY.get(c['kind'], 9)))
    # ---- institutions: mint proposals for the unkeyed ROR organisations
    iops = []
    if UNKEYED.exists():
        with gzip.open(UNKEYED, 'rt', newline='', encoding='utf-8') as f:
            for n, r in enumerate(csv.DictReader(f)):
                if state.lookup(f"ror:{r['ror']}"):
                    continue
                names = {r['name']} | {x.strip() for x in r['printed'].split(' | ') if x.strip()}
                iops.append(dict(event='mint', key=f'new:{n}', type='institution', label=r['name'], resolution='established',
                                 anchors=[f"ror:{r['ror']}"], aliases=[],
                                 members=sorted({f'inst-name:{x}' for x in names} | ({f"ror-wikidata:{r['wikidata'].split(';')[0]}"} if r['wikidata'] else set())),
                                 basis='ROR organisation reached by the ORCID record or Wikidata item of a person key (2026-11-14)'))
    iprop = dict(basis='institution keying: ROR organisations reached by ORCID/Wikidata affiliations (2026-11-14)',
                 decided_by='build', ops=iops)
    (OUT / 'institutions-proposal.json').write_text(json.dumps(iprop, ensure_ascii=False, indent=0) + '\n')
    ev2, _ = I.materialise(state, iprop, 'dry-run', 'dry-run', inplace=True)
    out = dict(attach_ops=len(ops), anchors=sum(len(o['anchors']) for o in ops),
               anchors_by_scheme=dict(collections.Counter(a.split(':', 1)[0] for o in ops for a in o['anchors'])),
               new_namespaces_needing_registration=[s for s in NEW_SCHEMES if any(a.startswith(s + ':') for o in ops for a in o['anchors'])],
               possible_duplicates=len(dups), possible_duplicate_pairs=len({(d['person'], d['other']) for d in dups}),
               possible_duplicates_by_scheme=dict(collections.Counter(d['scheme'] for d in dups)),
               conflicts=len(cl), conflicts_by_kind=dict(collections.Counter(c['kind'] for c in cl)),
               institution_mints=len(iops), institution_dry_run_events=len(ev2), counts=dict(sorted(rep.items())), applied='no')
    (OUT / 'report.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))
    for p in ('p-7813', 'p-12778', 'p-24137', 'p-4256', 'p-21351', 'p-53033', 'p-143231', 'p-37340'):
        print('PROBE', p, [o['anchors'] for o in ops if o['key'] == p], [c['kind'] + ': ' + c['detail'] for c in cl if c['person'] == p],
              [d['scheme'] + ' ' + d['other'] for d in dups if d['person'] == p])


if __name__ == '__main__':
    main()
