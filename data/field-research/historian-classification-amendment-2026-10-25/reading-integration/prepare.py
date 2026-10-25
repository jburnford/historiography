"""Prepare the three historian bridges and Anderson comparison; no public writes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REVIEW = ROOT/'data/dissertation-layer/reviews/historian-amendment-2026-10-25.json'
TARGETS = {
 'benedict_anderson': dict(folder='historian-anderson-2026-10-25', source='P:anderson|benedict r', works=[
     'W:anderson|imagined communities', 'W:anderson|under three flags', 'W:anderson|spectre of comparisons']),
 'immanuel_wallerstein': dict(folder='historian-wallerstein-2026-10-25', source='P:wallerstein|immanuel', works=[
     'W:wallerstein|modern world system', 'W:wallerstein|world systems analysis']),
 'sidney_mintz': dict(folder='historian-mintz-2026-10-25', source='P:mintz|sidney w', works=[
     'W:mintz|sweetness and power', 'W:mintz|birth of african american culture']),
}
NOTES = {
 'benedict_anderson': 'Identified through Imagined Communities, Under Three Flags and The Spectre of Comparisons. The displayed 716 is the frozen first-author key, not 716 individually verified Benedict Anderson attributions: the key contains known attribution errors and title/translation variants. A separate audit of 16 positively matched Imagined Communities title and translation keys gives a deduplicated union of 685 of these 716 dissertations (95.7%); it leaves the frozen keys and plotted main-key count unchanged. That main key has 641 dated dissertations (647 including undated records) and does not isolate the 1983 original or 1991 revision. Under Three Flags (2005) was retitled The Age of Globalization (2013); these do not supply independent book totals. Work counts overlap, and no remainder is described as readers of other books. Title identity and citation presence do not establish whole-book reading, agreement or influence.',
 'immanuel_wallerstein': 'Identified through The Modern World-System and World-Systems Analysis: An Introduction. The normalized Modern World-System key may pool volumes or editions: its 54 dated dissertations must not be described as 54 for volume I alone. Original volumes (1974, 1980, 1989, 2011) and revised editions remain distinct in the biography. The 119 author-key total is not a citation-by-citation attribution audit; other keys are not merged. No new full-book reading or inference of influence.',
 'sidney_mintz': 'Identified through Sweetness and Power and the jointly authored Birth of African-American Culture, with Richard Price credited. The latter is the 1992 retitled reissue with a new preface of their 1976 An Anthropological Approach to the Afro-American Past; original and reissue titles/dates remain distinct. Sweetness and Power’s 1985 original is separate from the linked 1986 Penguin manifestation. The 127 is one first-author key, not all-credit authorship or a citation-by-citation attribution audit; no variant-key totals or influence claims are merged.',
}
COMPARISON = dict(
 intro='Imagined Communities appears in 641 of the 716 dated dissertations assigned to this first-author key (89.5%). Compare the main work key with two other named books across sampled regions and degree cohorts. Edition, translation and title-variant keys are not added together.',
 question='How concentrated is this sampled citation record on Imagined Communities across regions and degree cohorts? Compare the books with the underlying first-author key and inspect the named dissertation examples. Citation presence alone does not establish agreement or influence.',
 observation='Across 16 positively matched Imagined Communities title and translation keys, a separate audit finds a deduplicated union of 685 of the 716 dated dissertations (95.7%). The plots show the separate work keys: Imagined Communities at 641, Under Three Flags at 16 and The Spectre of Comparisons at 14. The 685 union is deduplicated by dissertation, not a sum of work counts. The frozen author denominator includes unresolved and other-author attributions. Title-family identity does not establish whole-book reading, approval or influence.',
 default_view='works', works=[dict(person_id='benedict_anderson', work=k) for k in TARGETS['benedict_anderson']['works']])

def read(path):
    return json.loads(path.read_text())

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    baseline = read(HERE/'baseline.json')
    counts = read(HERE/'count-witnesses.json')
    graph = read(ROOT/'historiography-1920-2000.json')
    nodes = {n['id']:n for n in graph['nodes']}
    graph_sources = {s['id']:s for s in graph['sources']}
    audit_path = HERE.parent/'anderson-book-identity'
    audit_counts = read(audit_path/'counts.json')
    audit_decisions = read(audit_path/'decisions.json')
    audit_sources = read(audit_path/'sources.json')
    positive = [r for r in audit_decisions['decisions'] if r['assigned_to_book_union']]
    assert len(positive) == 16
    assert audit_counts['metrics']['GLOBAL']['confirmed_book_title_family_union'] == 685
    family_review = dict(audit_directory=str(audit_path.relative_to(ROOT)),
        input_sha256={name:file_hash(audit_path/name) for name in
            ('counts.json','decisions.json','sources.json','citation-unions.json')},
        metrics=audit_counts['metrics'], classification_counts=audit_counts['classification_work_key_counts'],
        positive_work_keys=[r['work_id'] for r in positive],
        primary_identity_decisions=[{k:r[k] for k in ('work_id','classification','rationale','source_ids','limits')}
                                    for r in positive],
        identity_sources=audit_sources['sources'],
        scope='Dissertation-ID union of positively matched title-family keys; no source key, authority merge, numeric-series change or claim of whole-book reading.')
    links = deepcopy(baseline['links'])
    registry = deepcopy(baseline['registry'])
    labels = read(ROOT/'data/field-research/dissertation-citations-2026-10-11/summary/explorer/explorer.json')['labels']
    label_map = {r['key']:(i,r) for i,r in enumerate(labels)}
    next_id = len(labels) + sum(r['id'] >= len(labels) for r in registry['sources'])
    original = {r['index']['key'] for r in baseline['sources']}
    people_review, unresolved = [], []
    for pid, selection in TARGETS.items():
        path = ROOT/'data/extension-2026'/selection['folder']/pid/'entry-draft.json'
        if not path.exists():
            unresolved.append(dict(person_id=pid, reason='Primary biography packet is not yet available.'))
            draft, node, available = {}, None, graph_sources
        else:
            draft = read(path)
            node = nodes.get(pid, draft['node'])
            available = {**{s['id']:s for s in draft.get('new_sources', [])}, **graph_sources}
        links['people'][pid] = dict(source=selection['source'], works=selection['works'], review_note=NOTES[pid])
        credits = []
        for key in selection['works']:
            row = counts['sources'][key]
            work = row['release_work_metadata']
            assert work['first_author_key'] == selection['source'][2:], key
            if key not in original:
                if key in label_map:
                    sid, label = label_map[key]
                else:
                    sid = next_id
                    next_id += 1
                    label = dict(key=key, short=work['first_author'].split(',')[0]+', '+work['title'].split(':')[0],
                                 full=work['title'], year=int(work['year']) if work['year'].isdigit() else None,
                                 author=work['first_author'])
                registry['sources'].append({**label, 'id':sid, 'source_index':baseline['source_count'] + len(registry['sources'])-len(baseline['registry']['sources'])})
            events, witnesses = [], []
            if node:
                if key == 'W:wallerstein|modern world system':
                    events = [e for e in node['chronology']['events'] if 'Modern World-System' in e['label']]
                elif key == 'W:mintz|birth of african american culture':
                    events = [e for e in node['chronology']['events'] if 'Richard Price' in e['label']]
                elif key == 'W:mintz|sweetness and power':
                    events = [e for e in node['chronology']['events'] if 'Sweetness and Power' in e['label']]
                else:
                    main = work['title'].split(':')[0].removeprefix('The ')
                    events = [e for e in node['chronology']['events'] if main.casefold() in e['label'].casefold()]
                for source_id in dict.fromkeys(s.removeprefix('graph:') for e in events for s in e['source_ids']):
                    source = available[source_id]
                    witnesses.append(dict(source_id=source_id, url=source.get('url'), verification=source.get('verification', {})))
                if not events or not witnesses:
                    unresolved.append(dict(person_id=pid, work_id=key, reason='No source-reviewed named event matched the exact work selection.'))
            credits.append(dict(work_id=key, release_metadata=work,
                dated_dissertations=row['n'], strict_with_or_without_year=row['strict_with_or_without_year'],
                series=row['series'], n_region=row['n_region'], biography_events=events, primary_evidence=witnesses,
                source_scope='existing_exported_source' if key in original else 'reviewed_counts_only_exception'))
        people_review.append(dict(person_id=pid, source=selection['source'], decision='prepared_named_work_bridge',
            dated_first_author_dissertations=counts['sources'][selection['source']]['n'],
            bibliography_packet=str(path.relative_to(ROOT)), bibliography_packet_sha256=file_hash(path) if path.exists() else None,
            biography_reading_scope=node.get('scope_note') if node else None,
            work_credits=credits, review_note=NOTES[pid]))
    links['person_comparisons'] = {**links.get('person_comparisons', {}), 'benedict_anderson': COMPARISON}
    assert len(links['people']) == 116 and len(links['entries']) == 5
    assert len(registry['sources']) == 18
    assert registry['sources'][:16] == baseline['registry']['sources']
    review = dict(schema='teaching_reading_bridge_review/1', date='2026-10-25', snapshot='2026-10-23',
        status='prepared_not_applied', graph_revision=graph['revision_history'][-1]['version'],
        graph_sha256=file_hash(ROOT/'historiography-1920-2000.json'), people=people_review,
        person_comparisons={'benedict_anderson':COMPARISON}, unresolved=unresolved,
        expected_counts=dict(people=116, field_panels=5, sources=4055, reviewed_exceptions=18),
        preservation_baseline='data/field-research/historian-classification-amendment-2026-10-25/reading-integration/baseline.json',
        count_witness='data/field-research/historian-classification-amendment-2026-10-25/reading-integration/count-witnesses.json',
        anderson_attribution_holds=counts['anderson_metadata_attribution_holds'],
        anderson_book_family_review=family_review,
        limits=['The main 641/716 comparison concerns frozen work/name keys; known attribution problems remain explicit.',
                'All 4053 previous source IDs, positions, index metadata and numeric fields remain fixed; only the Anderson source works list gains the two newly exported books.',
                'All 113 old profiles and five field panels remain exact. The personal comparison belongs only to Anderson.',
                'No count sum across editions, translations, title variants, author identities or selected works. No inference of adoption or influence.',
                'Wallerstein’s normalized multi-volume key is not volume I-only. Richard Price’s coauthorship and Mintz/Price’s 1976/1992 distinction are retained.'])
    for name, value in [('candidate-links.json',links), ('candidate-reviewed-source-ids.json',registry)]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    REVIEW.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(candidate_people=len(links['people']), source_registry=len(registry['sources']), unresolved=unresolved,
                         new_registry=registry['sources'][16:]),ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
