"""Prepare the eight reviewed bibliography gaps, without applying the packet."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVIEW = ROOT / 'data/field-research/dissertation-canon-review-2026-10-24/individual-work-review.json'
DAY = '2026-10-25'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    if (ROOT / 'data/production-batches/person-works-1.168/acceptance.json').exists():
        raise ValueError('Accepted packet is frozen; use apply_person_entries.py --check')
    graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    nodes = {n['id']: n for n in graph['nodes']}
    review = json.loads(REVIEW.read_text())
    rows = [r for r in review['results'] if r['decision'] == 'actual_new_work_gap']
    assert len(rows) == 8
    names = ['quentin_skinner', 'giovanni_levi', 'j_g_a_pocock', 'reinhart_koselleck', 'carlo_ginzburg']
    drafts = {n: {'prepared': DAY, 'status': 'proposal_for_review', 'proposed_edges': [], 'new_sources': []} for n in names}
    cfg = {'revision': '1.168', 'baseline_revision': '1.167', 'date': DAY,
        'batch_dir': 'person-works-1.168', 'persons': [], 'extras': names,
        'summary': 'Add eight distinct reviewed works/collections to five individual entries, with nine dated facts distinguishing the joint Ginzburg–Poni Italian original and partial French translation. Preserve component essay dates, editorial/translation credits, all earlier evidence and the two unresolved records. Carlo Poni gains a qualified bibliographic coauthor profile; no new arrows.',
        'authorization': 'User, 2026-10-25: continue after the completed dissertation-canon review. Coordinator is implementing its eight reviewed bibliographic gaps alongside the first thematic content packets. No publication authorized.',
        'rationale': 'The exact nineteen-row review identifies eight missing bibliographic objects, nine already represented translations/editions and two holds. This packet addresses only the eight objects. Metadata witnesses establish publication/edition facts; they do not establish eight new concepts or passage-level influence.',
        'field_sets': [], 'text_revisions': [], 'node_list_additions': []}
    additions = defaultdict(list)
    readings = defaultdict(list)
    accepted = []
    supplements = {
        'W:skinner|visions of politics': 'Visions of Politics (2002; three volumes: Regarding Method, Renaissance Virtues, Hobbes and Civil Science; collection publication, not the original date of each essay; generic corpus citations remain unassigned by volume).',
        'W:levi|on microhistory|a': '“On Microhistory” (1991, in Peter Burke, ed., New Perspectives on Historical Writing, Polity; distinguish the 1992 US edition and 2001 revised collection; chapter versions/body unread and uncollated here).',
        'W:pocock|virtue commerce and history': 'Virtue, Commerce, and History (1985 essay collection; earlier component dates remain distinct; collection body unread here).',
        'W:pocock|british history|a': '“British History: A Plea for a New Subject” (1975, Journal of Modern History 47(4), 601–621; separate comments by A. J. P. Taylor, Gordon Donaldson and Michael Hechter, 622–626, and Pocock reply, 626–628; issue metadata checked, bodies unread here).',
        'W:pocock|politics language and time': 'Politics, Language and Time (Atheneum first-edition collection, 1971; distinguish Methuen 1972; earlier essays keep their original dates; collection body unread here).',
        'W:koselleck|practice of conceptual history': 'The Practice of Conceptual History: Timing History, Spacing Concepts (Stanford, 2002 English collection, translated by Todd Samuel Presner with others, foreword by Hayden White; earlier essay dates remain distinct; collection body unread here).',
        'W:koselleck|lexperience de lhistoire': 'L’expérience de l’histoire (1997 French edited collection; edited and prefaced by Michael Werner; translated by Alexandre Escudier with Diane Meur, Marie-Claire Hoock and Jochen Hoock; not a single earlier German monograph or simply Le futur passé; component texts unread here).',
        'W:ginzburg|micro histoire|a': 'With Carlo Poni, “Il nome e il come: scambio ineguale e mercato storiografico” (1979), and “La micro-histoire” (1981 French partial translation, as identified by the reviewed article reference; versions not independently collated or read here).',
    }
    publication_meanings = {
        'W:skinner|visions of politics': 'Publication of the three-volume collection in 2002; earlier component essays retain their original dates.',
        'W:levi|on microhistory|a': 'Chapter in Peter Burke’s edited Polity collection, 1991; distinguish the 1992 US edition and the 2001 revised collection.',
        'W:pocock|virtue commerce and history': 'Publication of the essay collection in 1985; earlier component essays remain separately dated.',
        'W:koselleck|practice of conceptual history': 'Publication of an English translated collection in 2002; earlier essays retain their original dates.',
        'W:pocock|british history|a': 'Original article in Journal of Modern History 47(4), December 1975, pages 601–621; comments and reply are separate items.',
        'W:ginzburg|micro histoire|a': 'Joint Italian original in Quaderni storici 14(40), 1979, pages 181–190; the partial French translation in Le Débat 17 (1981) is separately dated.',
        'W:pocock|politics language and time': 'Atheneum first-edition collection, 1971; distinguish the 1972 Methuen edition and earlier component essays.',
        'W:koselleck|lexperience de lhistoire': 'French edited and translated collection, 1997; component essays retain their earlier dates where established.',
    }
    for i, row in enumerate(rows, 1):
        nid = row['node_id']; source_ids = []
        for j, witness in enumerate(row['source_checks'], 1):
            sid = f'dc168_work_{i:02d}_witness_{j:02d}'; source_ids.append(sid)
            drafts[nid]['new_sources'].append({'id': sid,
                'title': f"{row['person']}, {row['title']} — bibliographic witness {j}",
                'url': witness['url'], 'verification': {
                    'status': 'bibliographic_metadata_checked', 'checked_on': witness['checked_on'],
                    'note': witness['scope'].replace('jointItalian', 'joint Italian') + ' Checked in the frozen 2026-10-24 nineteen-work review and reused in this 2026-10-25 bibliography repair. No new full-work reading or passage-level relationship is asserted.'}})
        year = row['recommended_date']['year']
        event = {'id': f'dc168_work_{i:02d}', 'label': row['title'], 'kind': 'publication',
            'track': 'editions' if row['work_id']=='W:koselleck|lexperience de lhistoire' else 'contributions',
            'date': {'year': year, 'precision': 'year'},
            'source_ids': ['graph:' + s for s in source_ids],
            'support': publication_meanings[row['work_id']] + ' Bibliographic/edition fact only; body unread in this repair. Existing component dates and named mediation remain.'}
        if row['work_id'] == 'W:ginzburg|micro histoire|a':
            event['label'] = 'Ginzburg and Carlo Poni, “Il nome e il come” (joint Italian original)'
            additions[nid].append(event)
            translation = deepcopy(event)
            translation.update(id='dc168_ginzburg_poni_french_1981',
                label='Ginzburg and Carlo Poni, “La micro-histoire” (French partial translation)', track='editions')
            translation['date']['year'] = 1981
            translation['support'] = 'Le Débat 17 (December 1981), 133–136, joint authorship; the reviewed Annales article reference identifies this as a partial translation of the 1979 original. That version relationship is mediated and has not been independently collated.'
            additions[nid].append(translation)
            drafts[nid]['new_people'] = [{'id': 'carlo_poni', 'label': 'Carlo Poni',
                'identity_note': 'Named coauthor with Carlo Ginzburg in the reviewed 1979/1981 bibliographic witnesses. No authority-ID merge, demographic inference or independent whole-work interpretation.'}]
            drafts[nid]['roster_additions'] = [{'node': 'micro', 'row': {'person_id': 'carlo_poni',
                'role': 'contributor', 'context': 'Named coauthor with Ginzburg of the selected joint essay. This is a bibliographic association; neither an independently read methodological programme nor every claim made by Ginzburg is attributed to Poni.',
                'works': supplements[row['work_id']].replace('With Carlo Poni,', 'With Carlo Ginzburg,'), 'source_ids': source_ids, 'basis': 'source_review'}}]
        else:
            additions[nid].append(event)
        readings[nid].append(supplements[row['work_id']])
        cfg['node_list_additions'].append({'node': nid, 'field': 'source_ids', 'values': source_ids})
        accepted.append({'work_id': row['work_id'], 'node_id': nid, 'decision': 'bibliography_and_dated_publication_facts_only',
            'source_ids': source_ids, 'prior_review_decision': row['decision'], 'limits': row['recommended_action']})
    for nid in names:
        before = nodes[nid]['chronology']; after = deepcopy(before)
        after['events'].extend(additions[nid]); after['prepared_on'] = DAY
        if nid == 'reinhart_koselleck':
            after['label'] = 'Selected publications, translations and collections · 1959–2002'
        cfg['field_sets'].append({'node': nid, 'field': 'chronology', 'expect': before, 'value': after})
        old = nodes[nid]['representative_figures_and_works']
        cfg['text_revisions'].append({'node': nid, 'field': 'representative_figures_and_works',
            'old': old, 'new': old + ' Additional bibliographic selections: ' + ' '.join(readings[nid])})
        write(HERE / nid / 'entry-draft.json', drafts[nid])
    write(HERE / 'batch.json', cfg)
    write(HERE / 'research-notes.json', {'prepared_on': DAY, 'review': str(REVIEW.relative_to(ROOT)),
        'review_sha256': hashlib.sha256(REVIEW.read_bytes()).hexdigest(), 'accepted_objects': accepted,
        'selection_counts': review['decision_counts'], 'new_edges': 0,
        'limits': ['Collection publication is not the date every essay was first written or published.',
            'The nine edition/translation decisions and two holds remain unchanged in their frozen review.',
            'The French Ginzburg–Poni partial-translation relationship is mediated by an article reference, not a new collation.',
            'Bibliographic witnesses from the frozen review retain their actual check dates and body-unread limitations.',
            'Named coauthor, editor and translator credits do not imply an authority merge or intellectual influence.']})
    print('Prepared eight work objects, nine dated facts, one coauthor profile and no new arrows.')


if __name__ == '__main__':
    main()
