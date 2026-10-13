#!/usr/bin/env python3
"""Apply the fixes for Sol's review of the 1.129 packet (release/sol-review-1.129.md) to the research
files; then rebuild the packet with scripts/apply_canadian_person_links.py --build. Idempotent.
"""
import json
from pathlib import Path

PKT = Path(__file__).resolve().parents[1]
DAY = '2026-10-13'
INTRO = dict(  # finding 1: a checked in-period passage for Wolfe (read by Claude, 2026-10-13)
    id='cpl129_wolfe_1999_intro',
    title=('Patrick Wolfe, Settler Colonialism and the Transformation of Anthropology: The Politics and Poetics of '
           'an Ethnographic Event (London and New York: Cassell, 1999), Introduction, "Text and Context: '
           'Anthropology and Settler Colonialism", pp. 1–2.'),
    url='https://api.pageplace.de/preview/DT0400.9781441195524_A23995824/preview-9781441195524_A23995824.pdf',
    citation=('Patrick Wolfe, Settler Colonialism and the Transformation of Anthropology (London and New York: '
              'Cassell, 1999), Introduction, pp. 1–2.'),
    verification=dict(status='supporting_page_checked', checked_on=DAY, note=(
        "Publisher preview PDF reproducing the 1999 Cassell edition (imprint page: 'First published 1999', ISBNs "
        "0-304-70339-7 and 0-304-70340-0). Pages 1–2 read: the book is 'a history not so much of anthropology itself "
        "as of its ideological entanglements' in the development of Australian settler colonialism; postcolonial "
        "theory works with 'an oddly monolithic ... notion of colonialism'; settler colonies 'were not primarily "
        "established to extract surplus value from indigenous labour' but are premised on displacing indigenes from "
        "the land; 'Settler colonies were (are) premised on the elimination of native societies ... The colonizers "
        "come to stay - invasion is a structure not an event' (p. 2). Later pages not read here.")),
    scope_note="Wolfe's own 1999 statement of the settler-colonial distinction and of 'invasion is a structure not an event'.")
TEXT = [  # (file, old, new)
    ('wolfe/entry-draft.json',
     "Promoted because Canadian History PhDs increasingly read him: 54 strict PhDs (2009–2026) cite his work, rising from 1.0% (2009–14) to 8.6% (2020–26). This entry presents the 1999 book, checked at contents and catalogue level only; the 2001 and 2006 essays are later readings.",
     "This entry presents the 1999 book. Its introduction (pp. 1–2, read) distinguishes settler from franchise colonies, holds that settler colonies 'were (are) premised on the elimination of native societies' and states that 'invasion is a structure not an event'; the rest of the book is checked at contents and catalogue level. The 2001 and 2006 essays are later readings."),
    ('wolfe/entry-draft.json',
     " Later readers attribute to him the formulation 'a structure, not an event' (Kauanui 2016 abstract); his own pages are unchecked.", ''),
    ('wolfe/entry-draft.json', 'Contents and catalogue level only; the book is unread.',
     "Introduction pp. 1–2 read: settler colonies 'were (are) premised on the elimination of native societies' and 'invasion is a structure not an event'. The rest of the book is checked at contents and catalogue level."),
    ('wolfe/entry-draft.json',
     "Canadian reception came later: 17 strict History PhDs cite the book, first in 2012; 54 cite any of his works (2009–2026), rising from 1.0% (2009–14) to 8.6% (2020–26).",
     "In the sampled corpus, 17 of 1,303 strict History doctoral dissertations dated 2009–2026 cite the book (earliest observed citation 2012) and 54 cite any of his works; the citation share rises from 1.0% (2009–14) to 8.6% (2020–26)."),
    ('wolfe/entry-draft.json',
     "The 2006 essay and the 'structure, not an event' formulation (attested through Kauanui 2016) are later readings, not evidence for this edge.",
     "The 2006 essay is a later reading, not evidence for this edge."),
    ('wolfe/entry-draft.json', "Contents and catalogue level only; the book's argument and its stance toward these anthropologists are unread.",
     "Introduction p. 1 read: the book is 'a history not so much of anthropology itself as of its ideological entanglements'. The chapters' stance toward these anthropologists is not read here."),
    ('edges/proposed-edges.json', ' Valverde is sympathetic but critical, and Pierson weighs Scott against experience and voice.',
     ' Valverde is sympathetic but critical.'),
    ('edges/proposed-edges.json', 'Full text read (Érudit PDF, id.erudit.org/iderudit/llt7cri01;',
     'Pages 67–68 and 82–87 read closely with their footnotes; the rest skimmed by keyword (Érudit PDF, id.erudit.org/iderudit/llt7cri01;'),
    ('edges/proposed-edges.json',
     'Any directed contribution edge should wait for post-2000 work registered as works and claims (e.g. Perry 2001; Hall 2002; Christie, ed., Households of Faith, 2002), per the deferral rule.',
     'A contribution supported only by post-2000 publications (e.g. Perry 2001; Hall 2002; Christie, ed., Households of Faith, 2002) requires the extension workflow; a checked 1990s passage could support an ordinary in-period edge.'),
]


def walk(o, fn):
    if isinstance(o, dict):
        return {k: walk(v, fn) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, fn) for v in o]
    return fn(o) if isinstance(o, str) else o


def main():
    hits = [0] * len(TEXT)
    for name in ('wolfe/entry-draft.json', 'edges/proposed-edges.json'):
        path = PKT / name
        data = json.loads(path.read_text())

        def fix(s):
            for i, (f, old, new) in enumerate(TEXT):
                if f == name and old in s:
                    s = s.replace(old, new)
                    hits[i] += 1
                elif f == name and new and new in s:
                    hits[i] += 1
            return s
        data = walk(data, fix)
        if name == 'wolfe/entry-draft.json':
            if all(s['id'] != INTRO['id'] for s in data['new_sources']):
                data['new_sources'].append(INTRO)
            for holder in [data['node']] + data['proposed_edges']:
                if INTRO['id'] not in holder['source_ids']:
                    holder['source_ids'].insert(1, INTRO['id'])
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    missed = [TEXT[i][1][:60] for i, n in enumerate(hits) if not n and TEXT[i][2]]
    if missed:
        raise SystemExit(f'No match: {missed}')
    print(f'{len(TEXT)} text fixes; intro source added')


if __name__ == '__main__':
    main()
