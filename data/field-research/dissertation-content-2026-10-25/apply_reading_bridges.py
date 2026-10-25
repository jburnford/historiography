"""Apply five named-work bridges, preserving the frozen numerical source series."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / 'data/dissertation-layer/links.json'


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    before = json.loads((HERE / 'reading-links-before.json').read_text())
    current = json.loads(TARGET.read_text())
    if current != before:
        raise ValueError('Reading selection changed since the pinned baseline; review before reapplying')
    graph_path = ROOT / 'historiography-1920-2000.json'
    graph = json.loads(graph_path.read_text())
    people = {p['id']: p for p in graph['people']}
    nodes = {n['id']: n for n in graph['nodes']}
    candidates = json.loads((HERE / 'reading-bridge-candidates.json').read_text())['candidates']
    notes = {
        'james_c_scott': 'James C. Scott is linked through the named resistance/state books in his new entry. This does not merge other Scott keys or independently verify every attribution assigned to this first-author key.',
        'henri_lefebvre': 'Henri Lefebvre is linked through the named French original and English translation in the spatial-history strand. Translation dates and Donald Nicholson-Smith’s credit remain distinct. Neither record is added to the other’s count.',
        'lauren_benton': 'Lauren Benton is identified through Law and Colonial Cultures and A Search for Sovereignty. The corpus key retains an inherited a; this is not an accepted middle initial. The link does not independently verify every assigned attribution or collapse imprint and platform dates.',
        'william_m_reddy': 'William M. Reddy is identified through The Navigation of Feeling. Author totals also include other attributed first-author works, including labour history; they are not an estimate of emotions-history readership.',
        'barbara_h_rosenwein': 'Barbara H. Rosenwein is identified through the named 2002 essay and Emotional Communities. First-author totals cover other attributed works too, including medieval studies. The link is not a count of adherents to one method.',
    }
    evidence = {
        'james_c_scott': ('https://yalebooks.yale.edu/book/9780300252989/seeing-like-a-state/', 'Publisher title/author metadata identifies James C. Scott; this page describes the 2020 reissue, not the original publication date.'),
        'henri_lefebvre': ('https://www.wiley-vch.de/en/areas-interest/humanities-social-sciences/the-production-of-space-978-0-631-18177-4', 'Publisher metadata credits Henri Lefebvre and translator Donald Nicholson-Smith. Edition/format details do not establish citation-by-citation identity.'),
        'lauren_benton': ('https://www.cambridge.org/core/books/search-for-sovereignty/1FCB3767F56B64879CF13618A139866A', 'Publisher author/title metadata identifies Lauren Benton. The new packet separately verifies the 2010 imprint copyright leaf and retains platform-date discrepancies.'),
        'william_m_reddy': ('https://www.cambridge.org/core/books/navigation-of-feeling/83059CF2A4ECACC12D5C38DC719D0B51', 'Publisher author/title metadata identifies William M. Reddy. The field packet separately records his own preface/interview reading.'),
        'barbara_h_rosenwein': ('https://www.luc.edu/facultyauthors/barbarahrosenweinphd/', 'Author institutional bibliography identifies Barbara H. Rosenwein and Emotional Communities (2006); the field packet also records the primary 2002 essay’s author credit.'),
    }
    review = []
    for candidate in candidates:
        pid = candidate['person_id']; assert pid in people
        work_ids = [r['work_id'] for r in candidate['verified_work_credits']]
        current['people'][pid] = {'source': candidate['source'], 'works': work_ids,
                                  'review_note': notes[pid]}
        contexts = [n['id'] for n in graph['nodes'] if n['id'] == people[pid].get('node_id') or
                    any(r['person_id'] == pid for r in n.get('representative_people', []))]
        assert contexts
        url, scope = evidence[pid]
        review.append({**candidate, 'label': people[pid]['label'], 'teaching_context_ids': contexts,
            'primary_evidence': {'url': url, 'checked_on': '2026-10-25', 'scope': scope},
            'decision': 'Accept a selected bibliography-name bridge only; no authority merge, new membership or influence claim.',
            'review_note': notes[pid]})
    assert {'william_m_reddy', 'barbara_h_rosenwein'} <= {r['person_id'] for r in nodes['history_of_emotions']['representative_people']}
    current['entries']['history_of_emotions'] = ['william_m_reddy', 'barbara_h_rosenwein']
    current['entry_comparisons']['history_of_emotions'] = {
        'intro': 'Compare two selected methodological interventions: Reddy’s emotives and emotional regimes, and Rosenwein’s critique and emotional communities. These are distinct approaches within a wider field.',
        'question': 'How do citations to these selected works vary across sampled regions and degree cohorts? Citations can be critical or factual; author comparisons include their other attributed works too and do not measure the size of this field.',
        'default_view': 'works',
        'works': [
            {'person_id': 'william_m_reddy', 'work': 'W:reddy|navigation of feeling'},
            {'person_id': 'barbara_h_rosenwein', 'work': 'W:rosenwein|worrying about emotions in history|a'},
        ]}
    current['reviewed_on'] = '2026-10-25'
    write(TARGET, current)
    output = ROOT / 'data/dissertation-layer/reviews/dissertation-content-2026-10-25.json'
    write(output, {'schema': 'teaching_reading_bridge_review/1', 'date': '2026-10-25', 'snapshot': '2026-10-23',
        'graph_revision': graph['revision_history'][-1]['version'],
        'graph_sha256': hashlib.sha256(graph_path.read_bytes()).hexdigest(),
        'new_people': review, 'new_entry_selections': {'history_of_emotions': current['entries']['history_of_emotions']},
        'limits': ['All-credit release author counts are not substituted for public dated first-author counts.',
            'Old twenty people/four field selections and their questions remain unchanged.',
            'No new source exceptions, numerical series, denominator populations, family analyses or authority merges.',
            'Different work/title/translation keys are not added together.']})
    print('Added five reviewed profile bridges and one two-work emotions comparison.')


if __name__ == '__main__':
    main()
