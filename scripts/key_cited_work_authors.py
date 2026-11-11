"""Cited works' LC authors -> person keys and their works: a key-log PROPOSAL for selective promotion (2026-11-10).

The cited works matched on 2026-11-10 stay in two layers (data/graph/cited-works, scripts/export_cited_works.py): the
works are not keys, and their authors are credited in the graph only where data/identifiers/cited-work-authors-
2026-11-10 linked them. Owner (2026-11-10): promote people selectively. A person key is minted only when
- LC gives a name authority for the author (the record's 100/700 heading resolves to one; not undifferentiated, not
  deprecated), and the authority is on no key, and
- at least one of the author's matched works is cited by two or more theses (distinct dissertations, the exported
  table's `citing_theses`), and
- the linker found no name-compatible keyed person (state `none`, branch `no-compatible-name`). An author with a
  name-compatible key (`possible`; or `linked`, where the linker credited a key without the authority) is never minted
  beside a possible twin: the pair goes to held.json for a possible-same mark. `none` because every candidate was
  proven a different person (`only-proven-namesakes`) is held too, as a namesake situation that needs care.
  A key minted since the linker's graph (build/graph of 10:32) whose name agrees (link_cited_work_authors.name_level)
  holds the author as well.
For such a person the proposal mints the person (`lcnaf:` anchor, label: the authority's heading, established), their
matched works on their LCCNs (label: LC title, member `lc-first-year:`, established; an LCCN the log already holds
means that work key is used) and `authored` / `edited` claims (`lc-authored:<lccn>:<lcid>` per edition, as
key_lc_works makes them; endpoints `lcnaf:<lcid>` and the work's first LCCN), for all their matched works.
Second, for authors whose authority is already on a key (`exact`), works cited by two or more theses are minted (or
found) with the same claims: no new person.
Not used for promotion: works matched by the comma title forms (`lc-comma`, `corpus-comma`, `both-comma`; audited at
about 97% against 99% for the rest) and the statement-of-responsibility name form (`resp`: the heading kept is the
record's main entry, not a heading bearing the cited name). They stay in the graph layer with their basis.

Reads the key-log state through keylog_snapshot.read_state() (the SQLite cache; refuses a full replay), the exported
tables in data/graph/cited-works, the LC crosswalk and LC's name authorities on E: (read only). Writes
data/identifiers/cited-work-authors-promote-2026-11-10/: proposal.json[.gz] (decided_by rule), held.json, report.json,
sample-mints.json. The proposal is validated by identifiers.materialise on the read-only state (an in-memory dry run:
nothing is written to the log or the cache). It is not applied.

    python3 scripts/key_cited_work_authors.py
    # after review:  flock .keylog.lock python3 scripts/identifiers.py apply \\
    #                    data/identifiers/cited-work-authors-promote-2026-11-10/proposal.json.gz
"""
import argparse
import csv
import gzip
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identifiers as I  # noqa: E402
import keylog_snapshot as K  # noqa: E402
from link_cited_work_authors import forms, name_level  # noqa: E402

ROOT = I.ROOT
CITED = ROOT / 'data/graph/cited-works'
LC_XW = ROOT / 'data/identifiers/cited-works-lc-full-2026-11-10/crosswalk.csv.gz'
LC_NAMES = '/mnt/e/lc-authorities/personal-names.parquet'
LINKER_GRAPH = ROOT / 'build/graph/person.parquet'      # the person keys the linker saw (build of 10:32)
OUT = ROOT / 'data/identifiers/cited-work-authors-promote-2026-11-10'
COMMA = ('lc-comma', 'corpus-comma', 'both-comma')
MIN_THESES = 2


def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


def read_state():
    """keylog_snapshot.read_state(), but never the full replay it falls back to (10 GB on this machine)."""
    def refuse(*a, **k):
        raise SystemExit('key-log cache not usable: refusing a full replay; run keylog_snapshot.py rebuild under the lock')
    I.State.load = refuse
    return K.read_state()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=OUT)
    args = ap.parse_args()
    R = Counter()

    works = {r['id']: r for r in rd(CITED / 'works.csv.gz') if r['source'] == 'lc-full'}
    basis = {}
    for r in rd(LC_XW):                              # the crosswalk's basis per LCCN cluster id (title form/name form)
        basis.setdefault('lccn:' + r['lccns'].split(';')[0], r['basis'])
    by_lcid = defaultdict(list)                      # lcid -> author rows (one per cited work and role)
    for r in rd(CITED / 'authors.csv.gz'):
        if r['source'] != 'lc' or r['work'] not in works:
            continue
        if not r['source_person_id']:
            R['rows_without_authority'] += 1
            continue
        by_lcid[r['source_person_id'][len('lcnaf:'):]].append(r)
    R['authorities'] = len(by_lcid)

    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3")
    db.execute('CREATE TABLE want(lcid VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(x,) for x in by_lcid])
    auth = {lcid: dict(label=label, undiff=u, dep=d) for lcid, label, u, d in db.execute(
        f"SELECT lcid, label, undifferentiated, deprecated FROM read_parquet('{LC_NAMES}') WHERE lcid IN (SELECT lcid FROM want)"
    ).fetchall()}
    seen_keys = {k for (k,) in db.execute(f"SELECT key FROM '{LINKER_GRAPH}'").fetchall()}

    state = read_state()
    R['keylog_seq'] = state.seq
    withdrawn = I.withdrawn_claim_anchors(state)
    # person keys minted since the linker's graph: their names were never compared
    new_people = defaultdict(list)
    retired = tuple(I.RETIRED)
    for k, label in state.con.execute(
            f"SELECT key, label FROM keys WHERE type = 'person' AND status NOT IN ({','.join('?' * len(retired))})", retired):
        if k not in seen_keys:
            for f, form, g in forms(label):
                new_people[f].append((k, g, label))
    R['person_keys_new_since_linker'] = len({k for v in new_people.values() for k, _, _ in v})
    label_of = {}

    def person_label(k):
        if k not in label_of:
            rec = state.keys.get(k)
            label_of[k] = rec['label'] if rec else ''
        return label_of[k]

    def live_person(name):
        ks = [k for k in state.lookup(name) if (state.keys.get(k) or {}).get('type') == 'person']
        return ks

    def usable(r):
        b = basis.get(r['work'], '')
        return r['role'] in ('main', 'added', 'editor') and b.split('/')[0] not in COMMA

    ops, held, mints, minted_work = [], [], [], {}
    claim_seen = set()

    def work_anchor(wid):
        """The anchor a claim names for this cited work: an LCCN the log holds (one work key), else a new work."""
        w = works[wid]
        lccns = [x for x in w['lccns'].split(';') if x]
        owners = {k for x in lccns for k in state.lookup(f'lccn:{x}')}
        if len(owners) > 1:
            R['works_lccns_on_several_keys'] += 1
            return None
        if owners:
            R['works_found_in_log'] += 1
            return next(f'lccn:{x}' for x in lccns if state.lookup(f'lccn:{x}'))
        if wid not in minted_work:
            minted_work[wid] = f'lccn:{lccns[0]}'
            ops.append(dict(event='mint', key=f'new:w{len(ops)}', type='work', label=(w['title'] or '')[:250],
                            resolution='established', anchors=[f'lccn:{x}' for x in lccns], aliases=[],
                            members=[f"lc-first-year:{w['year']}"] if w['year'] else [],
                            basis=f"LC catalogue (Books All 2016) record of a book cited by {w['citing_theses']} "
                                  f"dissertation(s) in the corpus (cited-works-lc-full-2026-11-10, {basis.get(wid, '')})"))
            R['works_minted'] += 1
            R['works_minted_cited_2plus' if int(w['citing_theses']) >= MIN_THESES else 'works_minted_cited_1'] += 1
        return minted_work[wid]

    def plan_claim(lcid, r, count=True):
        """(predicate, claim anchors) for a row, or None: the claim exists, was withdrawn on review, or the work's
        LCCNs sit on several keys. No side effects."""
        pred = 'edited' if r['role'] == 'editor' else 'authored'
        lccns = [x for x in works[r['work']]['lccns'].split(';') if x]
        anchors = [f'lc-{pred}:{x}:{lcid}' for x in lccns]
        why = ('claim_exists' if any(a in claim_seen or state.anchor.get(a) for a in anchors) else
               'withdrawn_by_review' if any(a in withdrawn for a in anchors) else
               'work_on_several_keys' if len({k for x in lccns for k in state.lookup(f'lccn:{x}')}) > 1 else None)
        if why:
            R[f'{pred}_{why}'] += count
            return None
        return pred, anchors

    def claims(lcid, rows):
        n = 0
        for r in rows:
            plan = plan_claim(lcid, r)
            if not plan:
                continue
            pred, anchors = plan
            wa = work_anchor(r['work'])
            claim_seen.update(anchors)
            ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                            anchors=anchors, relation=dict(subject=f'lcnaf:{lcid}', predicate=pred, object=wa),
                            basis=f"LC record's {r['role']} heading resolves to this name authority; the dissertations "
                                  f"cite the book ({r['citing_theses']} theses)"))
            R[f'{pred}_claims'] += 1
            n += 1
        return n

    for lcid in sorted(by_lcid):
        rows = by_lcid[lcid]
        good = [r for r in rows if usable(r)]
        top = max((int(r['citing_theses']) for r in good), default=0)
        a = auth.get(lcid)
        owners = live_person(f'lcnaf:{lcid}')
        if len(owners) == 1:                         # the authority is on a key: attach the works cited 2+
            two = [r for r in good if int(r['citing_theses']) >= MIN_THESES]
            if two:
                R['exact_people_with_works'] += 1
                R['exact_claims'] += claims(lcid, two)
            continue
        if len(owners) > 1:
            R['authority_on_several_keys'] += 1
            continue
        if top < MIN_THESES:
            R['authorities_below_threshold'] += 1
            continue
        R['authorities_eligible'] += 1
        works_desc = [dict(work=r['work'], title=works[r['work']]['title'], year=works[r['work']]['year'],
                           role=r['role'], citing_theses=int(r['citing_theses'])) for r in good]
        base = dict(lcnaf=f'lcnaf:{lcid}', lc_heading=a['label'] if a else None, works=works_desc)
        if not a or a['undiff'] or a['dep']:
            held.append(dict(base, reason='authority undifferentiated, deprecated or not in the LC file'))
            R['held_authority_unusable'] += 1
            continue
        states = Counter(r['state'] for r in rows)
        if states['possible'] or states['linked']:
            cands = sorted({k for r in rows for c in (r['candidates'] or r['person_key'] or '').split('|') if c
                            for k in live_person(c)})
            held.append(dict(base, reason='name-compatible keyed person(s): mark possible-same, do not mint',
                             linker_states=dict(states), candidates=[dict(key=k, label=person_label(k)) for k in cands],
                             signals=sorted({r['signals'] for r in rows if r['signals']})))
            R['held_possible_twin'] += 1
            continue
        if any(r['branch'] == 'only-proven-namesakes' for r in rows):
            held.append(dict(base, reason='only proven namesakes among the keys (other LC authority or dates): needs care'))
            R['held_proven_namesakes'] += 1
            continue
        twins = []
        for f, form, g in forms(a['label']):
            twins += [(k, lab) for k, kg, lab in new_people.get(f, ()) if name_level(g, kg)]
        if twins:
            held.append(dict(base, reason='a person key minted since the linker ran bears a compatible name',
                             candidates=[dict(key=k, label=lab) for k, lab in sorted(set(twins))]))
            R['held_new_key_twin'] += 1
            continue
        if not any(plan_claim(lcid, r, count=False) for r in good):
            R['people_without_claims'] += 1            # nothing to credit: no person
            continue
        i = len(ops)
        ops.append(dict(event='mint', key=f'new:p{i}', type='person', label=a['label'], resolution='established',
                        anchors=[f'lcnaf:{lcid}'], aliases=[], members=[],
                        basis=f'LC name authority of the author of a book cited by {top} dissertations; no person key '
                              f'bears a compatible name (cited-work-authors-2026-11-10: none)'))
        claims(lcid, good)
        R['people_minted'] += 1
        mints.append(dict(lcnaf=f'lcnaf:{lcid}', lc_heading=a['label'], works=works_desc))

    R['held'] = len(held)
    proposal = dict(basis='cited works (LC 2016 books) of the dissertation corpus: their LC authors promoted where LC '
                          'names an authority, a work is cited by two or more theses and no keyed person could be the '
                          'same (owner 2026-11-10)', decided_by='rule', ops=ops)
    # dry run: validate the whole proposal on the read-only state (in memory; never flushed)
    events, names = I.materialise(state, proposal, 'dry-run', 'dry-run', inplace=True)
    R['dry_run_events'] = len(events)
    R['dry_run_new_keys'] = len(names)
    R['ops'] = len(ops)
    R['ops_by_type'] = dict(Counter(f"{o['event']}:{o.get('type', '')}" for o in ops))
    args.out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(proposal, ensure_ascii=False) + '\n'
    for p in (args.out / 'proposal.json', args.out / 'proposal.json.gz'):
        p.unlink(missing_ok=True)
    if len(body) > 50_000_000:
        with gzip.open(args.out / 'proposal.json.gz', 'wt', encoding='utf-8') as f:
            f.write(body)
    else:
        (args.out / 'proposal.json').write_text(body)
    (args.out / 'held.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    random.seed(20261110)
    sample = random.sample(mints, min(40, len(mints)))
    (args.out / 'sample-mints.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1) + '\n')
    rep = dict(sorted(R.items()))
    rep['rule'] = __doc__.split('\n\n')[1]
    (args.out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'rule'}, indent=1))


if __name__ == '__main__':
    main()
