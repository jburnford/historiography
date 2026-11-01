"""AHA dissertations, their authors and advisors -> the key log (PID-PLAN.md v2, rollout step 6). Writes a proposal; never mints.

Reads the AHA Directory of History Dissertations harvest (data/field-research/aha-dissertations-2026-10-13:
records.csv, genealogy/advisor-links.csv), the AHA historian directory
(data/field-research/aha-historians-2026-10-29/historians.csv) and a registry build.

- **Works.** Each dissertation record is a work (`aha-diss:<record>`), labelled with its title. Its
  department reaches an institution key through the ROR grounding (`inst-name:` members) and is recorded
  as a member (`awarded-by:i-N`), with the year (`year:<y>`).
- **People.**
  - Each dissertation's author is a person (`aha-phd:<record>`: the author of that record).
  - Each AHA advisor token is a person (`aha:<token>`; advisor ids and directory entries share one
    numbering). Directory-only historians are not keyed yet: only name and school tie them to their own
    dissertation record.
  - An advisor token joins the author of their own dissertation when the genealogy links them by name and
    date (`linked`, or a reviewed decision). `linked_by_topic` is not used: topic is not identity evidence
    (user, 2026-10-31). Those pairs are queued.
  - A dissertation the registry ties to an individual at the anchored or accepted tier (`phd_records`)
    brings that individual's anchors (atlas, ORCID, Wikidata, Open Library), so the author joins their
    existing key (Steven Ruggles: record 50721 -> ORCID -> p-6002). Probable ties are queued.
- **Supervision** is a relation between keys, not an identity. It is written beside the proposal as
  `supervision.csv` (advisor anchor, student anchor, work anchor, year) and can be resolved to keys once the
  proposal is applied.

    python3 scripts/key_aha.py --registry data/person-registry/generated/v13/registry.duckdb --out data/identifiers/aha-2026-11-01
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan

AHA = ROOT / 'data/field-research/aha-dissertations-2026-10-13'
DIRECTORY = ROOT / 'data/field-research/aha-historians-2026-10-29/historians.csv'
LINKED = {'linked', 'linked_by_decision'}
REGISTRY_TIERS = {'anchored', 'accepted'}


def individual_anchors(registry):
    """aha record -> (status, anchors of the registry individual that holds it)."""
    db = duckdb.connect(str(registry), read_only=True)
    people = {iid: (people, qids or []) for iid, people, qids in
              db.execute('SELECT individual_id, people, qids FROM individual_summary').fetchall()}
    out = {}
    for iid, status, aha_id in db.execute('SELECT individual_id, status, aha_id FROM phd_records').fetchall():
        members, qids = people.get(iid, ([], []))
        anchors = {f'atlas:person:{p.split(":", 1)[1]}' for p in members if p.startswith('atlas:')} | \
            {f'orcid:{p.split(":", 1)[1]}' for p in members if p.startswith('orcid:')} | {f'wd:{q}' for q in qids}
        if not anchors:
            anchors = {p for p in members if p.startswith('ol:')}
        out[aha_id] = (status, anchors, iid)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--registry', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state / 'events.jsonl')
    inst = {}
    for k, ms in state.members.items():
        if state.keys[k]['type'] == 'institution' and state.keys[k]['status'] == 'active':
            for m in ms:
                if m.startswith('inst-name:'):
                    inst[m[len('inst-name:'):]] = k
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        records = list(csv.DictReader(f))
    with (AHA / 'genealogy/advisor-links.csv').open(newline='', encoding='utf-8') as f:
        links = list(csv.DictReader(f))
    with DIRECTORY.open(newline='', encoding='utf-8') as f:
        directory = list(csv.DictReader(f))
    reg = individual_anchors(args.registry)
    report, queue = Counter(), []

    own = {}                                          # dissertation record -> advisor token
    token_name = {}
    for r in links:
        token_name[r['advisor_id']] = r['advisor']
        if r['status'] in LINKED and r['own_record']:
            own[r['own_record']] = r['advisor_id']
        elif r['status'] == 'linked_by_topic':
            queue.append(dict(kind='advisor_own_record_by_topic_only', token=r['advisor_id'], advisor=r['advisor'],
                              own_record=r['own_record']))
    for r in directory:
        token_name.setdefault(r['token'], r['name'])

    clusters, supervision = [], []
    tokens_used = set()
    for r in records:
        rid, title = r['id'], (r['title'] or '').strip()
        members = {f'year:{r["year"]}'} if r['year'] else set()
        if r['department'] in inst:
            members.add(f'awarded-by:{inst[r["department"]]}')
            report['works_with_institution_key'] += 1
        clusters.append(dict(type='work', label=title if title and title != '[No title]' else f'AHA dissertation {rid}',
                             anchors={f'aha-diss:{rid}'}, members=members, aliases=set(), resolution='established',
                             basis='AHA Directory of History Dissertations record'))
        anchors = {f'aha-phd:{rid}'}
        if rid in own:
            anchors.add(f'aha:{own[rid]}')
            tokens_used.add(own[rid])
            report['author_is_advisor_token'] += 1
        status, reg_anchors, iid = reg.get(rid, ('', set(), ''))
        if status in REGISTRY_TIERS and reg_anchors:
            anchors |= reg_anchors
            report['author_joined_registry_individual'] += 1
        elif status:
            queue.append(dict(kind='registry_phd_tie_probable', record=rid, author=r['dissertator'], individual=iid))
        clusters.append(dict(type='person', label=r['dissertator'], anchors=anchors, members=set(), aliases=set(),
                             resolution='established', basis=f'author of AHA dissertation record {rid}'))
        for t in filter(None, (r['advisor_ids'] or '').split('; ')):
            supervision.append(dict(advisor=f'aha:{t}', student=f'aha-phd:{rid}', work=f'aha-diss:{rid}', year=r['year'],
                                    source='AHA Directory of History Dissertations'))
    advisor_tokens = {s['advisor'][4:] for s in supervision}
    # Directory-only historians are not keyed yet: most also wrote a dissertation in records.csv, and only their
    # name and school tie the two, so keying both now would mint thousands of duplicates.
    report['directory_only_not_keyed'] = len({r['token'] for r in directory} - advisor_tokens - tokens_used)
    for t in sorted(advisor_tokens - tokens_used):
        clusters.append(dict(type='person', label=token_name.get(t, f'AHA historian {t}'), anchors={f'aha:{t}'},
                             members=set(), aliases=set(), resolution='established',
                             basis='AHA dissertation advisor'))
        report['token_only_people'] += 1

    # an anchor new to the log may belong to one cluster only (two records' authors tied to one individual)
    owners = defaultdict(list)
    for i, c in enumerate(clusters):
        for a in c['anchors']:
            if a not in state.anchor:
                owners[a].append(i)
    for a, idx in owners.items():
        if len(idx) > 1:
            queue.append(dict(kind='anchor_on_several_records', anchor=a, labels=[clusters[i]['label'] for i in idx]))
            for i in idx:
                clusters[i]['anchors'].discard(a)
            report['shared_anchor_dropped'] += 1
    clusters = [c for c in clusters if c['anchors']]
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='AHA keying', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='AHA dissertations (works), their authors and AHA historians (people)', decided_by='build', ops=ops),
        ensure_ascii=False) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    with (args.out / 'supervision.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['advisor', 'student', 'work', 'year', 'source'])
        w.writeheader()
        w.writerows(supervision)
    summary = dict(records=len(records), directory=len(directory), **dict(report), supervision_links=len(supervision),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held),
                   review_queue=dict(Counter(q['kind'] for q in queue + held)))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
