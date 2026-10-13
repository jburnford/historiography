#!/usr/bin/env python3
"""Apply the user's placement decisions of 2026-10-12 (Q28, Q45, Q73, Q80) to groups.json and the drafts.

The user agreed with the data answers: Backhouse's primary placement moves to
cdn_immigration_ethnicity, Owram's to cdn_sixties and Bliss's to cdn_political_national. Every
existing roster row is kept; only the primary placement changes. Idempotent. Run from anywhere.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
MOVES = {  # person_id: (candidate name, old primary, new primary, question numbers)
    'constance_backhouse': ('Backhouse, Constance', 'moral_regulation', 'cdn_immigration_ethnicity', (28,)),
    'doug_owram': ('Owram, Doug', 'cdn_intellectual_cultural', 'cdn_sixties', (45,)),
    'michael_bliss': ('Bliss, Michael', 'who_killed_debate', 'cdn_political_national', (73, 80)),
}
DECIDED = 'user decision 2026-10-12'
TEXT = {  # exact prose replacements, by draft
    'cdn_political_national': [("Bliss's primary placement is held for the user (Q73).",
                                "Bliss's primary placement is here, with a debate roster row there (Q73, user decision 2026-10-12).")],
    'who_killed_debate': [("Bliss's primary placement is held for the user (Q80).",
                           "Bliss's primary placement is cdn_political_national; this entry keeps his debate row (Q80, user decision 2026-10-12).")],
}


def move_name(lst, name, add):
    lst[:] = [x for x in lst if x != name] + ([name] if add else [])


def main():
    spec_path = HERE / 'groups.json'
    spec = json.loads(spec_path.read_text())
    for pid, (name, old, new, _) in MOVES.items():
        for g in spec['groups']:
            if g['id'] == old:
                move_name(g['primary'], name, False)
                if name not in g['also']:
                    g['also'].append(name)
            if g['id'] == new:
                move_name(g['also'], name, False)
                if name not in g['primary']:
                    g['primary'].append(name)
    notes = spec.setdefault('consolidation_notes', [])
    note = ('Primary placements moved by user decision 2026-10-12 (Q28, Q45, Q73/Q80): Backhouse -> '
            'cdn_immigration_ethnicity, Owram -> cdn_sixties, Bliss -> cdn_political_national; all roster rows kept.')
    if note not in notes:
        notes.append(note)
    spec_path.write_text(json.dumps(spec, indent=1, ensure_ascii=False))

    for path in sorted((HERE / 'drafts').glob('*/entry-draft.json')):
        gid = path.parent.name
        d = json.loads(path.read_text())
        node = d['node']
        for row in node.get('representative_people', []):
            if row['person_id'] not in MOVES:
                continue
            name, old, new, _ = MOVES[row['person_id']]
            row['proposed_primary_placement'] = new
            row.pop('placement_status', None)
            pl = row.get('placement')
            if pl:
                pl['primary'] = [new]
                pl['also'] = [g for g in dict.fromkeys(pl.get('also', []) + [old]) if g != new]
            row['placement_decision'] = f'primary {new} ({DECIDED})'
        for old_text, new_text in TEXT.get(gid, []):
            if old_text in node.get('scope_note', ''):
                node['scope_note'] = node['scope_note'].replace(old_text, new_text)
        qs = {q: (pid, new) for pid, (_, _, new, nums) in MOVES.items() for q in nums}
        for r in d.get('question_resolutions', []):
            if r['q'] in qs and r['status'] == 'held_for_user':
                pid, new = qs[r['q']]
                r['status'] = 'applied'
                r['summary'] += f' Applied after the {DECIDED}: {pid} primary placement is now {new}; roster rows kept.'
        path.write_text(json.dumps(d, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
