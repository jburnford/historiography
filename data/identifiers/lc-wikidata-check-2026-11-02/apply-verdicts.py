"""Turn Sol's LC→Wikidata verdicts into a key-log proposal and contribution lists (2026-11-02).

For each entry folder with verdict.json:
- item is the LC person and the LC authority fits the key: `wd:<QID>` is attached to the key (members
  `wd-via:lc-p244`, `wd-checked:sol-2026-11-02`), unless that QID already anchors another key (queued);
- item is not the LC person: member `rejected:wd:<QID>` on the key, so key_lc_wikidata skips it, and the pair
  goes to wikidata-p244-errors.json (the item cites an LC authority that is someone else's);
- the LC authority does not fit the key, or anything `unclear`: queued for review.
Birth years Sol found against LC's or Wikidata's go to birth-year-errors.json.
Writes proposal.json, review-queue.json, summary.json here.

    python3 data/identifiers/lc-wikidata-check-2026-11-02/apply-verdicts.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifiers import State  # noqa: E402

state = State.load(ROOT / 'data/identifiers')
entries = {e['id']: e for e in json.loads((HERE / 'entries.json').read_text())}
ops, queue, wd_errors, births, summary = [], [], [], [], Counter()
def verdicts():
    for path in sorted(HERE.glob('p-*/verdict.json')):
        yield path, json.loads(path.read_text())
    for path in sorted(HERE.glob('g*/verdicts.json')):         # grouped runs (run-sol-groups.sh)
        for v in json.loads(path.read_text()):
            if v.get('id') in entries:
                yield path, v


for path, v in verdicts():
    e = entries[v['id']] if path.name == 'verdicts.json' else entries[path.parent.name]
    k, q, lc = e['key'], e['wikidata']['qid'], e['lc']['id']
    same, fits = v.get('item_is_lc_person'), v.get('lc_fits_key')
    summary[f'item_{same}/lc_fits_{fits}'] += 1
    src = f'lc-wikidata-check-2026-11-02/{path.parent.name}/{path.name}'
    row = dict(id=e['id'], key=k, label=e['key_label'], lc=lc, qid=q, lc_person=v.get('lc_person'),
               item_person=v.get('item_person'), right_qid=v.get('right_qid_for_lc_person'), notes=v.get('notes'))
    if state.keys[k]['status'] not in ('active', 'provisional') or state.anchor.get(f'lcnaf:{lc}') != k:
        summary['key_changed_since'] += 1
        queue.append(dict(kind='sol_pair_key_changed', **row))
        continue
    if fits != 'yes' or same not in ('yes', 'no'):
        queue.append(dict(kind='sol_lc_does_not_fit_key' if fits == 'no' else 'sol_unclear', **row))
        continue
    if same == 'no':
        if f'rejected:wd:{q}' not in state.members.get(k, set()):
            ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[f'rejected:wd:{q}'],
                            basis=f'Wikidata {q} cites LC {lc} but is another person: {v.get("item_person")} (Sol check, {src})'))
        wd_errors.append(row)
        if v.get('right_qid_for_lc_person'):
            queue.append(dict(kind='sol_suggests_other_qid', **row))
        continue
    yb = v.get('birth_year_supported')
    if 'birth_disagrees' in e['automatic_check_problems'] and yb:
        births.append(dict(row, lc_birth=e['lc']['birth_in_lc'], wikidata_births=e['wikidata']['births'], supported=yb))
    owner = state.anchor.get(f'wd:{q}')
    if owner == k:                                                 # applied in an earlier run
        summary['already_applied'] += 1
        continue
    if owner and owner != k:
        queue.append(dict(kind='sol_qid_on_other_key', owner=owner, owner_label=state.keys[owner]['label'], **row))
        continue
    if any(a.startswith('wd:') for a in state.keys[k]['anchors']):
        queue.append(dict(kind='sol_key_has_other_qid', **row))
        continue
    ops.append(dict(event='attach', key=k, anchors=[f'wd:{q}'], aliases=[], members=['wd-via:lc-p244', 'wd-checked:sol-2026-11-02'],
                    basis=f'Wikidata {q} cites LC {lc} (P244); the automatic check failed ({", ".join(e["automatic_check_problems"])}) '
                          f'and a source check found one person (Sol, {src})'))
    summary['attached'] += 1
(HERE / 'proposal.json').write_text(json.dumps(dict(basis='LC→Wikidata pairs checked by Sol agents', decided_by='review',
                                                    ops=ops), ensure_ascii=False, indent=1) + '\n')
(HERE / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
(HERE / 'wikidata-p244-errors.json').write_text(json.dumps(wd_errors, ensure_ascii=False, indent=1) + '\n')
(HERE / 'birth-year-errors.json').write_text(json.dumps(births, ensure_ascii=False, indent=1) + '\n')
(HERE / 'summary.json').write_text(json.dumps(dict(counts=dict(summary), queued=len(queue), p244_errors=len(wd_errors),
                                                   birth_year_errors=len(births)), indent=1) + '\n')
print(dict(summary), 'queued', len(queue))
