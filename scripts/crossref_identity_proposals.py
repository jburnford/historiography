#!/usr/bin/env python3
"""Job B, last step (local, read-only on the graph): key-log proposals from the Crossref identity evidence
(2026-11-17). Writes proposals only; nothing is applied.

  python3 scripts/crossref_identity_proposals.py DIR PERSONS_PARQUET (b_persons.parquet of crossref_identity_inputs.py)

Reads DIR/orcid-evidence.csv.gz and DIR/orcid-two-keys.csv.gz (from scripts/crossref_identity_evidence.py) and
writes DIR/01-orcid-attaches.json, DIR/02-orcid-split-key-merges.json, DIR/held.json and adds counts to
DIR/proposal-counts.json.

(a) attach orcid:X to a key with no ORCID anchor when: X sits on name-matched contributor rows of 2+ of the key's
    works (a short form or nickname of the given name does not count), at least one with the given name written out
    in full; X is on no other key (anchored or
    name-matched); X is the only such ORCID of the key; and at least 90% of every Crossref row carrying X prints
    a family that agrees with the key's (the ORCID's whole Crossref record names this person).
    The key's label must have no namesake: no other key whose label agrees with it in full or by initial.
(c) merge two keys one ORCID joins only when: the labels agree (family, and given names in full or by initial; a
    short form or nickname is not accepted); at least 90% of the ORCID's Crossref rows print a family agreeing
    with each key; no identifier scheme conflicts (each key holding a different
    orcid / lcnaf / wd / gnd / viaf / isni / idref); and a second independent fact: a DOI work credited to both
    keys, or the same institution printed on both keys' works within 3 years. The key that holds the ORCID anchor
    survives, else the more cited.
"""
import csv
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crossref_names import forms, name_level, fam_agree  # noqa: E402

SCHEMES = ('orcid', 'lcnaf', 'wd', 'gnd', 'viaf', 'isni', 'idref')


def lst(v):
    v = (v or '').strip()
    if v in ('', '[]', 'NULL'):
        return []
    return [x.strip().strip("'\"") for x in v.strip('[]').split(',') if x.strip()]


def label_level(la, lb):
    """Best agreement of two key labels: 'full' / 'initial' / None ('variant' = a short form: not accepted)."""
    best = None
    for fa, _, ga in forms(la):
        for fb, _, gb in forms(lb):
            if fam_agree(fa, fb):
                lev = name_level(ga, gb)
                if lev == 'full':
                    return 'full'
                if lev == 'initial':
                    best = 'initial'
    return best


def scheme_conflict(aa, ab):
    out = []
    for s in SCHEMES:
        xa = {a for a in aa if a.startswith(s + ':')}
        xb = {a for a in ab if a.startswith(s + ':')}
        if xa and xb and not (xa & xb):
            out.append(s)
    return out


def namesakes(persons_parquet, keys):
    """Keys among `keys` whose label agrees (same family, given names 'full' or 'initial') with another key's."""
    import duckdb
    from collections import defaultdict
    labels = dict(duckdb.sql(f"select key, label from '{persons_parquet}'").fetchall())
    by_fam = defaultdict(list)
    for k, lab in labels.items():
        for f, _, g in forms(lab or ''):
            by_fam[f].append((k, g))
    out = {}
    for k in keys:
        for f, _, g in forms(labels.get(k) or ''):
            for k2, g2 in by_fam.get(f, ()):
                if k2 != k and name_level(g, g2) in ('full', 'initial'):
                    out.setdefault(k, []).append(k2)
    return out


def main(d, persons_parquet):
    d = Path(d)
    ops_a, held = [], []
    with gzip.open(d / 'orcid-evidence.csv.gz', 'rt') as fh:
        rows = list(csv.DictReader(fh))
    share_of = {(r['person'], r['orcid']): float(r['name_share']) if r['name_share'] else None for r in rows}
    ns = namesakes(persons_parquet, {r['person'] for r in rows if r['cls'] == 'a'})
    for r in rows:
        if r['cls'] != 'a':
            continue
        why = []
        if r['in_c'] == 'true':
            why.append('orcid-on-another-key')
        if int(r['n_full'] or 0) + int(r['n_initial'] or 0) < 2:
            why.append('fewer-than-2-works-without-a-short-form')
        if int(r['key_n_orcids_2plus'] or 0) != 1:
            why.append('several-candidate-orcids')
        share = float(r['name_share']) if r['name_share'] not in ('', None) else 0.0
        if share < 0.9:
            why.append(f'orcid-record-names-other-family:{share:.2f}')
        if r['person'] in ns:
            why.append('namesake-keys:' + '|'.join(sorted(ns[r['person']])[:5]))
        if why:
            held.append(dict(kind='attach', key=r['person'], orcid=r['orcid'], reasons=why))
            continue
        auth = ' (authenticated by ORCID)' if r['authenticated'] == 'true' else ''
        ops_a.append(dict(event='attach', key=r['person'], anchors=['orcid:' + r['orcid']], aliases=[], members=[],
                          basis=(f"Crossref March 2026 data file: ORCID {r['orcid']}{auth} on the name-matched contributor row of "
                                 f"{r['n_works']} DOI works credited to this key ({r['y_min']}-{r['y_max']}; printed "
                                 f"'{r['names_on_record']}'); {share:.0%} of the ORCID's Crossref rows print an agreeing family; "
                                 f"on no other key (crossref-identity-2026-11-17)")))
    ops_c = []
    with gzip.open(d / 'orcid-two-keys.csv.gz', 'rt') as fh:
        pairs = list(csv.DictReader(fh))
    taken = set()
    for p in pairs:
        why = []
        lev = label_level(p['l1'], p['l2'])
        if lev is None:
            why.append('labels-disagree')
        for k in (p['k1'], p['k2']):
            sh = share_of.get((k, p['orcid']))
            if sh is not None and sh < 0.9:
                why.append(f'orcid-record-names-other-family:{k}:{sh:.2f}')
        conf = scheme_conflict(lst(p['a1']), lst(p['a2']))
        if conf:
            why.append('scheme-conflict:' + '|'.join(conf))
        sd, sa = int(p['shared_dois'] or 0), int(p['shared_aff'] or 0)
        if not (sd or sa):
            why.append('no-second-fact')
        if p['k1'] in taken or p['k2'] in taken:
            why.append('key-in-another-pair')
        if why:
            held.append(dict(kind='merge', k1=p['k1'], k2=p['k2'], orcid=p['orcid'], reasons=why))
            continue
        o = 'orcid:' + p['orcid']
        a1, a2 = lst(p['a1']), lst(p['a2'])
        c1, c2 = float(p['c1'] or 0), float(p['c2'] or 0)
        if o in a1 or (o not in a2 and c1 >= c2):
            into, key = p['k1'], p['k2']
        else:
            into, key = p['k2'], p['k1']
        taken.update((into, key))
        facts = []
        if sd:
            facts.append(f'{sd} DOI work(s) credited to both keys')
        if sa:
            facts.append(f'{sa} shared printed institution span(s) within 3 years')
        ops_c.append(dict(event='merge', key=key, into=into, decided_by='rule',
                          basis=(f"Crossref March 2026 data file: ORCID {p['orcid']} on the name-matched contributor rows of works "
                                 f"of both keys ({p['l1']} / {p['l2']}); second fact: {'; '.join(facts)} "
                                 f"(crossref-identity-2026-11-17)")))
    json.dump(dict(basis='ORCID on name-matched Crossref contributor rows of works credited to keys without an ORCID anchor '
                         '(scripts/crossref_identity_evidence.py, crossref_identity_proposals.py; Crossref March 2026)',
                   decided_by='rule', ops=ops_a), open(d / '01-orcid-attaches.json', 'w'), indent=1, ensure_ascii=False)
    json.dump(dict(basis='one ORCID on two person keys plus a second independent fact (shared DOI work or printed '
                         'institution) (scripts/crossref_identity_proposals.py; Crossref March 2026)',
                   decided_by='rule', ops=ops_c), open(d / '02-orcid-split-key-merges.json', 'w'), indent=1, ensure_ascii=False)
    json.dump(held, open(d / 'held.json', 'w'), indent=0, ensure_ascii=False)
    print('attach', len(ops_a), 'merge', len(ops_c), 'held', len(held))
    return len(ops_a), len(ops_c), len(held)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
