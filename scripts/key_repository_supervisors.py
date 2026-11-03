"""Supervisors named by thesis repositories -> the key log (lesson 6 of the user's probes; 2026-11-03).

The AHA directory names advisors for North American history PhDs only. The corpus's own records name them for
8,236 doctorates (doctorates.json `advisors`, from the repositories: dc.contributor.advisor in Canadian and US
DSpace, DataCite supervisors for Oxford DPhils, theses.fr `directeurs_these` with IdRef ids, CAPES
orientadores with CAPES person ids). Theses listing more than two are left out (committee lists, not supervisors;
US records list up to seven). For each named supervisor of a keyed thesis (`diss-thesis:<id>`):
- **the advisor in the source**: `idref:<ppn>` (France; IdRef, the French national authority, a public PID),
  `capes-person:<id>` (Brazil, the only orientador), else `repo-advisor:<institution>|<given family>` (one
  person per name in one institution's records; `advisor_names` splits fields naming several people and drops
  honorifics and roles);
- **joined to a keyed person** when
  - the thesis already has a supervisor in the log (an AHA advisor of the same thesis) whose name agrees with
    the repository's (key_registry.names_compatible): one thesis, one name;
  - the IdRef id is the P269 of a Wikidata item a key holds;
  and only when every such join of the anchor reaches the same key (two keys: listed, not joined);
  otherwise minted, `recorded`;
- a `supervised` claim (`repo-sup:<thesis id>:<advisor anchor>`) to the thesis, unless that person already
  supervises it.

    python3 scripts/key_repository_supervisors.py --out data/identifiers/repository-supervisors-2026-11-03
"""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_registry import names_compatible
from review_atlas_qids import sparql

D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
FRANCE = ROOT / 'data/field-research/france-theses-2026-10-30/candidates.json'


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+', s))


ROLE = re.compile(r'\b(dr|prof|professor|supervisors?|co-supervisors?|advisors?|co-advisors?|directeur|directrice|'
                  r'orientador|orientadora|committee chair|chair|ph\.?\s?d)\b\.?', re.I)
UNIT = re.compile(r'\b(department|dept|faculty|school|university|college|institute|centre|center|programme|program)\b', re.I)


def advisor_names(raw):
    """The people in one advisor field, each as 'Given Family'. Repositories put several people in one field
    ('Angus Burgin, Francois Furstenberg'; 'David Mills, Department of History & Classics; Nancy Van Styvendale,
    Faculty of Native Studies') and honorifics or roles into names ('Dr Thomas A Schwartz', 'Paula C Clarke
    supervisor'); 'Schwartz, Thomas A.' is one person, family name first."""
    out = []
    for part in re.split(r';|\band\b|&| / ', raw):
        segs = [x.strip(' .') for x in part.split(',') if x.strip(' .') and not UNIT.search(x) and not re.match(r'\s*\d', x)]
        if len(segs) >= 2 and all(len(x.split()) >= 2 for x in segs):
            people = segs                                  # 'Angus Burgin, Francois Furstenberg'
        elif len(segs) == 2:
            people = [f'{segs[1]} {segs[0]}']              # 'Schwartz, Thomas A.'
        else:
            people = segs[:1]
        for x in people:
            x = ' '.join(ROLE.sub(' ', x).split()).strip(' .()-')
            if len(norm(x).split()) >= 2:
                out.append(x)
    return out


def idref_items(ppns, cache):
    """IdRef id -> QIDs whose P269 it is."""
    out = defaultdict(set)
    ppns = sorted(ppns)
    for i in range(0, len(ppns), 200):
        part = ppns[i:i + 200]
        query = 'SELECT ?item ?id WHERE { VALUES ?id { %s } ?item wdt:P269 ?id }' % ' '.join(f'"{x}"' for x in part)
        for r in sparql(query, cache, 'idref-' + hashlib.sha1(query.encode()).hexdigest()[:12]):
            out[r['id']['value']].add(r['item']['value'].rsplit('/', 1)[-1])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--cache', type=Path, default=ROOT / 'data/field-research/repository-supervisors-2026-11-03/raw')
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    state = State.load(args.state)
    doctorates = json.loads((D / 'doctorates.json').read_text())
    idref = {}                                  # (nnt, normalised name) -> IdRef id
    for c in json.loads(FRANCE.read_text()):
        for a in c.get('directeurs_these') or []:
            if a.get('idref'):
                idref[c['nnt'], norm(f"{a.get('prenom', '')} {a.get('nom', '')}")] = a['idref']
    supervisors = defaultdict(set)              # work key -> supervisor keys in the log
    for claim, subj, pred, obj in state.relations('supervised'):
        if len(subj) == 1 and len(obj) == 1:
            supervisors[obj[0]].add(subj[0])
    report, rows = Counter(), []                # rows: (advisor anchor, name, thesis id, work key)
    for d in doctorates:
        names = list(dict.fromkeys(n for a in d.get('advisors') or [] for n in advisor_names(a)))
        if not names:
            continue
        if len(names) > 2:
            report['theses_committee_lists_skipped'] += 1
            continue
        work = state.lookup(f'diss-thesis:{d["id"]}')
        if len(work) != 1:
            report['theses_not_keyed'] += 1
            continue
        report['theses'] += 1
        for name in names:
            if d.get('nnt') and (d['nnt'], norm(name)) in idref:
                anchor = f'idref:{idref[d["nnt"], norm(name)]}'
            elif d.get('capes_advisor_id') and len(names) == 1:
                anchor = f'capes-person:{d["capes_advisor_id"]}'
            else:
                anchor = f'repo-advisor:{d["institution"]}|{norm(name)}'
            rows.append((anchor, name, d['id'], work[0]))
    qids = idref_items({a[6:] for a, *_ in rows if a.startswith('idref:')}, args.cache)
    joins, label = defaultdict(set), {}         # advisor anchor -> keys it is joined to
    for anchor, name, tid, work in rows:
        label.setdefault(anchor, name)
        if anchor in state.anchor:
            joins[anchor].add(state.anchor[anchor])
            continue
        same = [k for k in supervisors.get(work, ()) if names_compatible(state.keys[k]['label'], name)]
        if len(same) == 1:
            joins[anchor].add(same[0])
        elif len(same) > 1:
            joins[anchor].add('several')
        if anchor.startswith('idref:'):
            for q in qids.get(anchor[6:], ()):
                ks = [k for k in state.lookup(f'wd:{q}') if state.keys[k]['type'] == 'person']
                if len(ks) == 1 and names_compatible(state.keys[ks[0]]['label'], name):
                    joins[anchor].add(ks[0])
    queue, clusters, owner, by_key = [], [], {}, defaultdict(set)
    for anchor in sorted(label):
        ks = joins.get(anchor, set())
        if len(ks) > 1 or 'several' in ks:
            queue.append(dict(kind='repository_advisor_reaches_several_keys', anchor=anchor, name=label[anchor],
                              keys=sorted(k for k in ks if k != 'several')))
            report['advisor_reaches_several_keys'] += 1
            continue
        if ks:
            k = next(iter(ks))
            owner[anchor] = k
            if anchor in state.anchor:
                report['advisor_already_keyed'] += 1
            else:
                by_key[k].add(anchor)
                report['advisor_joined'] += 1
        else:
            owner[anchor] = None
            clusters.append(dict(type='person', label=label[anchor], anchors={anchor}, members=set(), aliases=set(),
                                 resolution='established' if anchor.startswith('idref:') else 'recorded',
                                 basis='supervisor named in the thesis repository record'))
            report['advisor_minted'] += 1
    for k, anchors in sorted(by_key.items()):      # one cluster per key: its spellings and institutions together
        clusters.append(dict(type='person', label=state.keys[k]['label'], anchors=anchors | {sorted(state.keys[k]['anchors'])[0]},
                             members=set(), aliases=set(), resolution='established',
                             basis=f'supervisor in thesis repository records of theses the log already gives to '
                                   f'{state.keys[k]["label"]} (same thesis, names agree), or the IdRef id of their Wikidata item'))
    ops, assign, held = plan(state, clusters)
    claims = set()
    for anchor, name, tid, work in rows:
        k = owner.get(anchor, 'skip')
        if k == 'skip':
            continue
        c = f'repo-sup:{tid}:{anchor}'
        if c in state.anchor or c in claims or (k and k in supervisors.get(work, ())):
            report['supervised_already'] += 1
            continue
        claims.add(c)
        ops.append(dict(event='mint', key=f'new:claim-{len(claims)}', type='claim', label='', resolution='recorded',
                        anchors=[c], relation=dict(subject=anchor, predicate='supervised', object=f'diss-thesis:{tid}'),
                        basis='supervisor named in the thesis repository record (doctorates.json advisors)'))
    report['supervised_claims'] = len(claims)
    materialise(state, dict(basis='repository supervisors', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='supervisors named by thesis repositories (Canadian and US DSpace, Oxford/DataCite, theses.fr, CAPES)',
        decided_by='build', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held),
                   review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
