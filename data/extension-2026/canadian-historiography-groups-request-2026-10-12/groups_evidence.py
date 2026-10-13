#!/usr/bin/env python3
"""Evidence for the proposed Canadian historiography group entries (groups.json).

For each proposed group: its anchor people with citing-PhD counts (2009-2026 strict History
PhDs, identity-cleaned as in the scholar packet), the share of those PhDs engaging the group
(citing works by at least two of its anchor people), early (2009-14) and late (2020-26) shares,
and the group's most-cited works. Also checks that every Canadian historian in the scholar
packet has exactly one primary group. Run from the repository root:

    python3 data/extension-2026/canadian-historiography-groups-request-2026-10-12/groups_evidence.py
"""
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
SCHOLARS = ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12'
EARLY, LATE = (2009, 2014), (2020, 2026)


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def main():
    spec = json.loads((HERE / 'groups.json').read_text())
    groups = spec['groups']
    placements = spec.get('existing_entry_placements', {})
    cands = {r['name']: r for r in csv.DictReader((SCHOLARS / 'candidates.csv').open())}
    decisions = {r['person_key']: r for r in csv.DictReader((SCHOLARS / 'identity-decisions.csv').open())}
    g = json.loads((OUT / 'graph.json').read_text())
    nodes = {n['id']: n for n in g['nodes']}
    diss = {k: n for k, n in nodes.items() if n['type'] == 'Dissertation' and n.get('in_analysis')
            and n['year'] and 2009 <= n['year'] <= 2026}
    cites, works_of = defaultdict(set), defaultdict(set)
    for e in g['edges']:
        if e['type'] == 'CITES' and e['source'] in diss:
            cites[e['target']].add(e['source'])
        elif e['type'] == 'AUTHORED':
            works_of[e['source']].add(e['target'])

    def person_works(name):
        ws = set()
        for k in cands[name]['person_keys'].split('; '):
            foreign = {x.strip() for x in (decisions.get(k, {}).get('foreign_work_ids') or '').split(';') if x.strip()}
            ws |= works_of[k] - foreign
        for r in decisions.values():  # works moved to this person from a mixed record
            if r.get('move_to') and r['move_to'] in cands[name]['person_keys'].split('; '):
                ws |= {x.strip() for x in r['move_work_ids'].split(';') if x.strip()}
        return ws

    problems = []
    named = {n for gr in list(groups) + list(placements.values()) for n in gr['primary'] + gr['also']}
    problems += [f'not in the scholar packet: {n}' for n in sorted(named - cands.keys())]
    primary = Counter(n for gr in list(groups) + list(placements.values()) for n in gr['primary'])
    canadian = {n for n, r in cands.items() if r['person_type'] == 'canadian_historian'}
    problems += [f'no primary group: {n}' for n in sorted(canadian - primary.keys()) if n != 'Dickason, Olive Patricia']
    problems += [f'primary in {c} groups: {n}' for n, c in primary.items() if c > 1]

    early = {d for d in diss if EARLY[0] <= diss[d]['year'] <= EARLY[1]}
    late = {d for d in diss if LATE[0] <= diss[d]['year'] <= LATE[1]}
    rows, out = [], []
    for gr in groups:
        anchors = [n for n in gr['primary'] + gr['also'] if n in cands]
        pw = {n: person_works(n) for n in anchors}
        citing = {n: {d for w in ws for d in cites[w]} for n, ws in pw.items()}
        hits = Counter(d for c in citing.values() for d in c)
        engaged = {d for d, k in hits.items() if k >= 2}
        works = Counter()
        for ws in pw.values():
            for w in ws:
                works[w] = len(cites[w])
        e, l = len(engaged & early) / len(early), len(engaged & late) / len(late)
        res = dict(id=gr['id'], label=gr['label'], anchors=len(anchors), engaged_phds=len(engaged),
                   share=round(len(engaged) / len(diss), 4), share_ci95=wilson(len(engaged), len(diss)),
                   share_2009_14=round(e, 4), share_2020_26=round(l, 4),
                   trend='rising' if l > e * 1.25 else 'falling' if l < e * 0.8 else 'steady',
                   universities=len({diss[d]['institution'] for d in engaged}),
                   anchor_counts={n: len(citing[n]) for n in anchors},
                   top_works=[f"{nodes[w]['title']} ({nodes[w].get('year') or 'n.d.'}; {c})" for w, c in works.most_common(8)])
        out.append(res)
        rows.append([gr['id'], gr['label'], len(gr['primary']), len(anchors), len(engaged), res['share'],
                     res['share_2009_14'], res['share_2020_26'], res['trend'], res['universities'], gr['atlas_period_fit']])
    (HERE / 'evidence.json').write_text(json.dumps(dict(dissertations=len(diss), problems=problems, groups=out), indent=1, ensure_ascii=False))
    with (HERE / 'groups-summary.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'label', 'primary_people', 'anchor_people', 'engaged_phds', 'share', 'share_2009_14', 'share_2020_26', 'trend', 'universities', 'atlas_period_fit'])
        w.writerows(rows)
    render(spec, out, problems, len(diss))
    print('problems:', problems)
    for r in rows:
        print(r)


def render(spec, evidence, problems, n):
    """README for the packet, from groups.json and the evidence."""
    ev = {e['id']: e for e in evidence}
    L = ["""# Request: Canadian historiography group entries for the atlas

Prepared 2026-10-12. **Status: structure revised after the user's review; drafting next.**
Nothing is applied to the atlas; entries go through reviewed revision batches. This README is
generated by `groups_evidence.py` from `groups.json`.

## Why groups first
The atlas teaches historiography in Canada, but it has no field for Canadian historiography.
The user decided (2026-10-12) to create the Canadian group entries first and then attach the
person entries to them. The Canadian historians in
`../canadian-historiography-scholars-request-2026-10-12/` each have exactly one primary
placement: in a group below, or, for Canadian environmental historians, in the existing
Environmental history entry. The atlas already treats national schools as entries (Annales,
the US Progressives, History Workshop, Bielefeld); these follow that pattern.

## Structure
Engagement is the share of the """ + str(n) + """ strict History PhDs completed 2009–2026 that cite works
by at least two of the group's anchor people. Groups with more anchors score higher, so read
the trend rather than the level.

| Proposed entry | Primary people | Engaged PhDs | 2009–14 → 2020–26 | Atlas period |
| --- | ---: | ---: | --- | --- |
"""]
    for g in spec['groups']:
        e = ev[g['id']]
        L.append(f"| {g['label']} | {len(g['primary'])} | {e['engaged_phds']} ({e['share']:.0%}) | "
                 f"{e['share_2009_14']:.1%} → {e['share_2020_26']:.1%} ({e['trend']}) | {g['atlas_period_fit']} |\n")
    L.append("""
The settler-colonialism row counts its Canadian anchors. The settler packet's rising series
(0.7% → 12.8%) counts the core theory works.

## Reviewed decisions (user, 2026-10-12)
""")
    L += [f"- **{g['label']}:** {g['decision']}\n" for g in spec['groups'] if g.get('decision')]
    for entry, pl in spec.get('existing_entry_placements', {}).items():
        L.append(f"- **Existing entry `{entry}`:** {pl['note']} Primary: {', '.join(pl['primary'])}; "
                 f"also {', '.join(pl['also'])}.\n")
    L.append("\n## Each proposed entry\n")
    for g in spec['groups']:
        e = ev[g['id']]
        L.append(f"\n### {g['label']} (`{g['id']}`{', ' + g['entry_type'] if g.get('entry_type') else ''})\n{g['scope']}\n")
        L.append(f"- **Period:** {g['period']}.\n- **Related atlas entries:** {', '.join(g['related_atlas_entries'])}\n")
        L.append(f"- **Primary people:** {', '.join(g['primary'])}\n")
        if g['also']:
            L.append(f"- **Also anchoring:** {', '.join(g['also'])}\n")
        L.append(f"- **Most-cited works (citing PhDs, 2009–26):** {'; '.join(e['top_works'][:5])}\n")
    if spec.get('open_questions'):
        L.append("\n## Open questions\n")
        L += [f"- {q}\n" for q in spec['open_questions']]
    L.append("""
## Next step
For each group, draft an entry in the atlas's register: a description, a date label following
the atlas's milestone rules, roster people with roles, strands, and proposed relationships.
Every source is verified against a real record, as in
`../settler-colonialism-request-2026-10-12/`. The drafts go to Astra as one revision request,
and the person entries follow by tier.

## Files
- `groups.json`: the structure, decisions and open questions.
- `groups_evidence.py`: writes `evidence.json`, `groups-summary.csv` and this README. Run it
  from the repository root.
""")
    if problems:
        L.append("\n**Validation problems:** " + '; '.join(problems) + "\n")
    (HERE / 'README.md').write_text(''.join(L))


if __name__ == '__main__':
    main()
