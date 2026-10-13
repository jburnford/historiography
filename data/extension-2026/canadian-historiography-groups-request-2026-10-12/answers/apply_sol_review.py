#!/usr/bin/env python3
"""Apply the fixes for Sol's adversarial review of the 1.128 packet (release/sol-review-1.128.md).

Edits the group drafts in place with exact replacements; each must match at least once, so a
stale string fails loudly. Settler-colonialism fixes live in that packet's build_request.py.
Packet-level fixes (extension wording, later-intervention notes, drafting artefacts) live in
scripts/build_canadian_release_packet.py. Idempotent: a finding already applied is skipped.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DRAFTS = HERE / 'drafts'
REVIEW = 'Sol review 2026-10-12'

TEXT = [  # (finding, draft, old, new): applied to every string in entry-draft.json and literature.json
    (2, 'liberal_order_framework', 'These works predate the prospectus and are its roots, not applications of it.',
     "Curtis (1988) and Greer and Radforth (1992) predate the prospectus; Curtis's later books (2001, 2012) continue "
     "that work, and their relation to the framework is not checked here."),
    (3, 'native_newcomer', 'These studies predate the settler-colonial framework and do not adopt it.',
     'Most predate the settler-colonial framework; whether any adopts it was not checked.'),
    (4, 'native_newcomer', 'Ray’s later reconstruction of Indigenous traders reorients that subject',
     'Ray’s later study of Indigenous traders treats the same subject'),
    (4, 'native_newcomer', 'Contribution of a subject and evidence base, not influence on the field’s interpretations.',
     'Comparison only: shared subject matter. How Ray engaged Innis is not checked (catalogue level).'),
    (4, 'native_newcomer', 'Innis’s fur trade as a resource reworked by later historians',
     'Innis’s fur trade compared with its later reworking'),
    (5, 'who_killed_debate', "Reviewed Who Killed Canadian History? in RHAF (1998; title level, text unread);",
     "Reviewed Who Killed Canadian History? in RHAF (1998; title level, text unread, position not checked);"),
    (5, 'who_killed_debate', "Reviewed Who Killed Canadian History? in the Bulletin d'histoire politique (1999; title level, text unread).",
     "Reviewed Who Killed Canadian History? in the Bulletin d'histoire politique (1999; title level, text unread, position not checked)."),
    (7, 'cdn_intellectual_cultural', "One contributor's intervention, not the whole field's position.",
     "A critique of Granatstein's position within the debate by one intellectual historian, not the whole field's position."),
    (7, 'cdn_intellectual_cultural', 'An intellectual historian answers Granatstein',
     "An intellectual historian criticizes Granatstein's national history"),
    (8, 'cdn_regional', "In 1971 Buckner founded Acadiensis, complaining that historians remained 'obsessed with the great \"national\" themes'.",
     "Acadiensis was revived in 1971 on Ken Windsor's initiative, with Buckner as its editor; his first editorial complained "
     "that historians remained 'obsessed with the great \"national\" themes'."),
    (8, 'cdn_regional', "Founded Acadiensis (1971) against historians \"obsessed with the great 'national' themes\"",
     "Editor of the revived Acadiensis (1971), whose first editorial faulted historians \"obsessed with the great 'national' themes\""),
    (9, 'cdn_black_history',
     "The field became academic with Robin Winks's survey The Blacks in Canada (1971), which Walker reviewed critically, and James Walker's The Black Loyalists (1976)",
     "After earlier work by Landon, Riddell and Trudel, Robin Winks's survey The Blacks in Canada (1971), which Walker reviewed critically, and James Walker's The Black Loyalists (1976)"),
    (10, 'cdn_sixties', "Book-length accounts began with Kostash's", "Early book-length accounts include Kostash's"),
    (10, 'cdn_intellectual_cultural', 'From the 1990s a cultural history of invention and memory took over much of the ground.',
     'From the 1990s a cultural history of invention and memory developed alongside it.'),
    (12, 'liberal_order_framework', 'Proposes a "loyalist order framework" for 1750–1840 in place of a liberal one; argument read at title level only.',
     'Proposes a "loyalist order framework" for 1750–1840 (chapter title); how it relates to McKay\'s liberal order is not characterized here.'),
    (13, 'cdn_immigration_ethnicity',
     "Reviewers saw Anderson's racialization approach moving beyond earlier studies of white attitudes and prejudice (Stanley 1993), though Stanley added",
     "Timothy Stanley's review (1993) saw Anderson's racialization approach moving beyond earlier studies of white attitudes and prejudice, though he added"),
    (13, 'cdn_national_tradition', 'which urban historians later found indeterminate', 'which Donald Davis (1985) found indeterminate'),
    (16, '*', '(1999): 641ff.', '(1999): 641–66.'),
    (16, '*', 'Crossref DOI record (CHR 80:4, pp. 641–692, December 1999)',
     'Crossref DOI record (December 1999; its pp. 641–692 overlap Palmer’s article at 676–86 in the same '
     'issue and are wrong; 641–66 follows the RHAF 2000 bibliography, an indexed extract, per Sol’s review)'),
    (18, 'who_killed_debate', 'concurrent, separate debates linked through a few people, not texts;',
     "concurrent, separate debates with limited, one-way textual engagement (Dumont's 1999 review cites Ferretti and Létourneau);"),
]
SOURCE_NOTES = {  # record id -> passage appended to its verification note, wherever the record lives
    'cdng_buckner_2000': (8, ' Paragraphs 4–6 read on 2026-10-12 after the Sol review: Ken Windsor "initiated and eloquently '
                             'defended the creation of a journal"; David Earl showed it would be viable; Buckner "agreed to become '
                             'the editor"; the title was revived from David Russell Jack\'s journal (1901–08).'),
}
ROLES = {('who_killed_debate', 'bernard_dionne'): 'contributor', ('who_killed_debate', 'nadia_fahmy_eid'): 'contributor'}
RELS = {  # proposal id -> field updates (findings 4 and 7)
    'nnreq_rel_05': dict(relationship_kind='comparison', directed=False, type='connection'),
    'cic_rel_10': dict(relationship_kind='critique', directed=True, type='critique'),
}
COAUTHORS = {  # finding 11: (draft, strand) -> people credited as coauthors of a collective work
    ('cdn_black_history', 'community_women'): [('linda_carty', 'Linda Carty'), ('sylvia_hamilton', 'Sylvia Hamilton'),
                                               ('adrienne_shadd', 'Adrienne Shadd'), ('peggy_bristow', None),
                                               ('dionne_brand', None), ('afua_cooper', None)],
    ('quebec_historiography', 'women_in_quebec_history'): [('michele_jean', 'Michèle Jean'), ('marie_lavigne', 'Marie Lavigne'),
                                                           ('jennifer_stoddart', 'Jennifer Stoddart')],
}
COAUTHOR_NOTE = {
    'cdn_black_history': " The six coauthors of We're Rooted Here (1994) are Bristow, Brand, Carty, Cooper, Hamilton and Shadd; shared methods or positions are not inferred.",
    'quebec_historiography': ' The Collectif Clio (1982) was Micheline Dumont, Michèle Jean, Marie Lavigne and Jennifer Stoddart; shared methods or positions are not inferred.',
}


def walk(obj, fn):
    if isinstance(obj, dict):
        return {k: walk(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v, fn) for v in obj]
    return fn(obj) if isinstance(obj, str) else obj


def main():
    hits = {i: 0 for i in range(len(TEXT))}
    for gid in sorted(p.name for p in DRAFTS.iterdir() if (p / 'entry-draft.json').exists()):
        for name in ('entry-draft.json', 'literature.json'):
            path = DRAFTS / gid / name
            data = json.loads(path.read_text())

            def fix(s):
                for i, (_, g, old, new) in enumerate(TEXT):
                    if g in (gid, '*') and old in s:
                        s = s.replace(old, new)
                        hits[i] += 1
                    elif g in (gid, '*') and new in s:
                        hits[i] += 1  # already applied
                return s
            data = walk(data, fix)
            for rec in data.get('records', []) if name == 'literature.json' else []:
                if rec.get('id') in SOURCE_NOTES:
                    extra = SOURCE_NOTES[rec['id']][1]
                    if extra.strip() not in rec['verification'].get('note', ''):
                        rec['verification']['note'] = rec['verification'].get('note', '') + extra
            if name == 'entry-draft.json':
                node = data['node']
                for row in node['representative_people']:
                    if (gid, row['person_id']) in ROLES:
                        row['role'] = ROLES[(gid, row['person_id'])]
                for rel in data.get('proposed_relationships', []):
                    rel.update(RELS.get(rel['proposal_id'], {}))
                new_ids = {p['id'] for p in data.get('new_people', [])}
                for (g, sid), people in COAUTHORS.items():
                    if g != gid:
                        continue
                    strand = next(s for s in node['strands'] if s['id'] == sid)
                    for pid, label in people:
                        if pid not in strand['person_ids']:
                            strand['person_ids'].append(pid)
                        if label and pid not in new_ids:
                            data.setdefault('new_people', []).append(dict(id=pid, label=label, qid=None,
                                qid_note=f'Coauthor credit only ({REVIEW}, finding 11); not on the roster; no external identity checked.'))
                            new_ids.add(pid)
                    if COAUTHOR_NOTE[gid].strip() not in strand['focus']:
                        strand['focus'] += COAUTHOR_NOTE[gid]
                res = data.setdefault('question_resolutions', [])
                if not any(r.get('q') == 'sol_review' for r in res):
                    res.append(dict(q='sol_review', status='applied',
                                    summary=f'{REVIEW}: findings applied as listed in answers/apply_sol_review.py.'))
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    missed = [TEXT[i][:3] for i, n in hits.items() if not n]
    if missed:
        raise SystemExit(f'Replacements that matched nothing: {missed}')
    print(f'{len(TEXT)} text fixes applied; roles {len(ROLES)}; relationships {len(RELS)}; coauthor strands {len(COAUTHORS)}')


if __name__ == '__main__':
    main()
