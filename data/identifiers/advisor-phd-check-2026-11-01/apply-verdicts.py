"""Turn Sol's advisor-doctorate verdicts into a key-log proposal and review decisions (2026-11-01).

For each entry folder with verdict.json:
- `no`: the linked AHA record is a namesake's. Its author anchors (`aha-phd:<record>`, and harvested-thesis
  authors whose thesis is that dissertation) leave the advisor's key and become their own person; the
  advisor's key is relabelled with the advisor's name if it carried the dissertator's. The link is recorded
  as rejected in review-decisions.json, so key_aha does not make it again.
- `yes`: the link is recorded as kept.
- `unclear`: nothing.
Writes proposal.json and summary.json here and appends to data/identifiers/review-decisions.json.

    python3 data/identifiers/advisor-phd-check-2026-11-01/apply-verdicts.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from aha_links import fold  # noqa: E402
from identifiers import State  # noqa: E402

state = State.load(ROOT / 'data/identifiers')
entries = {e['id']: e for e in json.loads((HERE / 'entries.json').read_text())}
dec_path = ROOT / 'data/identifiers/review-decisions.json'
decisions = json.loads(dec_path.read_text())
done = {d.get('token') for d in decisions if d['kind'] == 'advisor_own_record_doubtful'}
ops, summary, rows = [], Counter(), []
for path in sorted(HERE.glob('aha-*/verdict.json')):
    v = json.loads(path.read_text())
    e = entries[path.parent.name]
    verdict = v.get('linked_record_is_theirs')
    summary[verdict] += 1
    doc = v.get('doctorate') or {}
    rows.append(dict(id=e['id'], advisor=e['advisor'], verdict=verdict, doctorate=doc, identified=v.get('advisor_identified')))
    if e['token'] in done or verdict not in ('yes', 'no'):
        continue
    rec = e['linked_record']['aha_record']
    k = state.anchor.get(f'aha:{e["token"]}')
    src = f'advisor-phd-check-2026-11-01/{e["id"]}/verdict.json'
    if verdict == 'yes':
        decisions.append(dict(kind='advisor_own_record_doubtful', keys=[k], token=e['token'], keep=True,
                              decision=f'AHA record {rec} is {e["advisor"]}\'s dissertation',
                              basis=f'Sol verification ({src}): {doc.get("institution")} {doc.get("year")}', date='2026-11-01'))
        continue
    if not k or state.anchor.get(f'aha-phd:{rec}') != k:
        summary['no_but_not_joined_in_log'] += 1
        continue
    work = state.lookup(f'aha-diss:{rec}')
    theirs = sorted({f'aha-phd:{rec}'} | {a for a in state.keys[k]['anchors'] if a.startswith('diss-author:')
                                           and state.lookup('diss-thesis:' + a.split(':', 1)[1]) == work})
    rest = state.keys[k]['anchors'] - set(theirs) - {f'aha:{e["token"]}'}
    if rest:
        summary['no_but_key_holds_other_anchors'] += 1
        rows[-1]['held'] = sorted(rest)
        continue
    basis = (f'AHA record {rec} ({e["linked_record"]["dissertator"]}, {e["linked_record"]["year"]}) is a namesake\'s: '
             f'advisor {e["advisor"]}\'s doctorate is {doc.get("institution")} {doc.get("year")} (Sol verification, {src})')
    ops += [dict(event='detach', key=k, anchors=theirs, members=[], basis=basis),
            dict(event='mint', key=f'new:{rec}', type='person', label=e['linked_record']['dissertator'], resolution='recorded',
                 anchors=theirs, aliases=[], members=[], basis=f'author of AHA dissertation record {rec}')]
    if fold(state.keys[k]['label']) == fold(e['linked_record']['dissertator']):
        ops.append(dict(event='relabel', key=k, label=e['advisor'], basis="the advisor's name"))
    decisions.append(dict(kind='advisor_own_record_doubtful', keys=[k], token=e['token'], keep=False,
                          decision=f'AHA record {rec} is not {e["advisor"]}\'s dissertation', basis=basis, date='2026-11-01'))
    summary['repaired'] += 1
(HERE / 'proposal.json').write_text(json.dumps(dict(basis='advisor doctorates verified by Sol agents', decided_by='review',
                                                    ops=ops), ensure_ascii=False, indent=1) + '\n')
(HERE / 'summary.json').write_text(json.dumps(dict(counts=dict(summary), rows=rows), ensure_ascii=False, indent=1) + '\n')
dec_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=1) + '\n')
print(dict(summary))
