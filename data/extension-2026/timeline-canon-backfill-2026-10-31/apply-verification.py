#!/usr/bin/env python3
"""Apply Claude's independent verification to Sol's backfill drafts (2026-10-31).

Sol 6.1 (Codex) researched one historian per agent; three Claude verification agents then opened every
cited passage (review-A/B/C.json, copied here from the session scratchpad: verdict, checked URL, the phrase
seen, reason, corrections). This script, run once:
- keeps Sol's draft as <person>/entry-draft.researcher.json;
- writes <person>/entry-draft.json with a `review` on every proposal; `hold` -> include: false; `adjust` ->
  the verifier's corrected sentence and fields, with the reason appended to the evidence note;
- applies the coordinator decisions in DECISIONS (duplicates across drafts, the co-authorship convention,
  replacement sources the verifier read);
- drops new sources no included edge cites (unread CV, inaccessible pages, duplicates' copies).
"""
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
DAY = '2026-10-31'
REVIEWER = 'Claude (independent verification agent; coordinator decisions by Claude)'
reviews = {}
for part in 'ABC':
    for r in json.loads((HERE / f'review-{part}.json').read_text()):
        reviews[(r['person'], r['proposal_id'])] = r

# Coordinator decisions on top of the verdicts.
DUPLICATE = {   # (person, proposal) -> the proposal it duplicates; held so the pair is applied once
    ('patrick_geary', 'pg_bf_01'): 'barbara_h_rosenwein/rosenwein_bf_03',
    ('t_m_devine', 'devine_bf_01'): 'john_m_mackenzie/jmm_bf_02',
    ('t_m_devine', 'devine_bf_02'): 't_c_smout/smout_bf_02',
}
EXTRA_SOURCES = {   # proposal -> sources added (the duplicate's verified source, or a verifier's replacement)
    ('john_m_mackenzie', 'jmm_bf_02'): ['bf_mackenzie_devine_introduction_2011'],
}
SOURCE_SETS = {   # proposal -> replacement source list
    ('charles_s_maier', 'maier_bf_03'): ['bf_queens_ghi_partners', 'bf_shaw_harvard_magazine_2014'],
    ('t_c_smout', 'smout_bf_02'): ['bf_hames_print_culture_2025'],
}
TEXT_FIXES = {
    ('james_rodger_miller', 'jrm_bf_01'): ("In Donald Wright’s 2013 biography of Creighton",
                                           "In Donald Wright’s Dictionary of Canadian Biography entry on Creighton (2013)"),
}
NEW_SOURCES = {
    'charles_s_maier': [
        {'id': 'bf_queens_ghi_partners', 'title': "Queen's University Global History Initiative, 'Partners' (web page, undated).",
         'citation': "Queen's University Global History Initiative, 'Partners' (web page, undated).",
         'url': 'https://www.queensu.ca/ghi/partners',
         'verification': {'status': 'supporting_page_checked', 'checked_on': DAY,
                          'note': "Read at Claude verification: the Harvard University Weatherhead Initiative on Global History entry says the initiative 'was founded in 2012' and names Sven Beckert and Charles S. Maier as its chairs."}},
        {'id': 'bf_shaw_harvard_magazine_2014',
         'title': "Jonathan Shaw, 'History turns toward the global, the scientific, and the quantitative', Harvard Magazine, 15 October 2014.",
         'citation': "Jonathan Shaw, 'History turns toward the global, the scientific, and the quantitative', Harvard Magazine, 15 October 2014.",
         'url': 'https://www.harvardmagazine.com/humanities/harvard-sven-beckert',
         'verification': {'status': 'supporting_page_checked', 'checked_on': DAY,
                          'note': "Read at Claude verification: Beckert 'co-directs WIGH'; Maier is introduced as 'His WIGH co-director'."}},
    ],
}
SOURCE_NOTES = {   # where the passage was actually read, when not at the recorded URL
    'bf_correia_thompson_interview_2019': " [Claude verification 2026-10-31: the DOI landing page returned 502/504; the same article was read on the journal's own site (revistatopoi.org), printed p. 16 and n. 13.]",
    'bf_mackenzie_devine_introduction_2011': " [Claude verification 2026-10-31: read in the publisher's licensed preview, not at the DOI.]",
}


def main():
    drafts = sorted(p for p in HERE.iterdir() if (p / 'entry-draft.json').exists())
    used, counts = set(), {'verified': 0, 'adjust': 0, 'hold': 0, 'duplicate': 0}
    loaded = {}
    for d in drafts:
        researcher = d / 'entry-draft.researcher.json'
        if not researcher.exists():
            shutil.copy(d / 'entry-draft.json', researcher)
        draft = json.loads(researcher.read_text())
        person = d.name
        draft['review_status'] = 'reviewed'
        draft['new_sources'] += NEW_SOURCES.get(person, [])
        for e in draft['proposed_edges']:
            key = (person, e['proposal_id'])
            r = reviews[key]
            review = {'verdict': r['verdict'], 'reviewer': REVIEWER, 'checked_on': DAY, 'checked_url': r.get('checked_url'),
                      'phrase_seen': r.get('supporting_phrase'), 'reason': r.get('reason')}
            if r['verdict'] == 'hold':
                e['include'] = False
            elif r['verdict'] == 'adjust':
                e['relationship'] = r['corrected_relationship']
                for k, v in (r.get('corrected_fields') or {}).items():
                    if k in ('source', 'target', 'relationship_kind', 'directed', 'map_label', 'type'):
                        e[k] = v
                e['evidence_note'] += f" [Claude verification {DAY}, adjusted: {r['reason']}]"
            if key in DUPLICATE:
                e['include'] = False
                review['duplicate_of'] = DUPLICATE[key]
                counts['duplicate'] += 1
            if key in SOURCE_SETS:
                e['source_ids'] = SOURCE_SETS[key]
            e['source_ids'] = list(dict.fromkeys(e['source_ids'] + EXTRA_SOURCES.get(key, [])))
            if key in TEXT_FIXES:
                old, new = TEXT_FIXES[key]
                assert old in e['relationship'], key
                e['relationship'] = e['relationship'].replace(old, new)
            if e.get('relationship_kind') == 'critique':
                e['type'] = 'critique'
            # co-authorship and co-editing between two people: undirected comparison (graph convention)
            if e.get('directed') is False and e.get('relationship_kind') == 'contribution':
                e['relationship_kind'] = 'comparison'
            e['review'] = review
            counts[r['verdict']] += 1
            if e.get('include') is not False:
                used.update(e['source_ids'])
        loaded[d] = draft
    for d, draft in loaded.items():
        kept, dropped = [], []
        for s in draft['new_sources']:
            (kept if s['id'] in used else dropped).append(s)
            if s['id'] in SOURCE_NOTES:
                s['verification']['note'] += SOURCE_NOTES[s['id']]
        draft['new_sources'] = kept
        if dropped:
            draft['sources_not_applied'] = [{'id': s['id'], 'reason': 'not cited by any applied edge after verification'} for s in dropped]
        (d / 'entry-draft.json').write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n')
    applied = sum(1 for dr in loaded.values() for e in dr['proposed_edges'] if e.get('include') is not False)
    print(counts, 'applied edges:', applied)


if __name__ == '__main__':
    main()
