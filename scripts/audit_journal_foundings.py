#!/usr/bin/env python3
"""Reproduce revision 1.112 preservation checks and the journal subject gap matrix."""
import json
from pathlib import Path

try:
    from .build_journal_catalogue import make_catalogue
    from .validate_journal_catalogue import validate_catalogue
except ImportError:
    from build_journal_catalogue import make_catalogue
    from validate_journal_catalogue import validate_catalogue

ROOT = Path(__file__).resolve().parents[1]


def main():
    before = json.loads((ROOT / 'drafts/historiography-1920-2000.v1.111.json').read_text())
    after = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    assert after['revision_history'][-1]['version'] == '1.112', 'Audit targets revision 1.112'
    old, new = before['journal_catalogue'], after['journal_catalogue']
    batch = json.loads((ROOT / 'data/journal-catalogue/venue-batches/founding-001.json').read_text())
    assert {k: v for k, v in before.items() if k not in ('journal_catalogue', 'revision_history')} == {
        k: v for k, v in after.items() if k not in ('journal_catalogue', 'revision_history')}
    assert after['revision_history'][:-1] == before['revision_history']
    assert new['edges'] == old['edges'] + batch['edges']
    assert new['sources'] == old['sources'] + batch['sources']
    for key in old.keys() - {'nodes', 'sources', 'edges'}:
        assert old[key] == new[key], key
    by_id = {n['id']: n for n in new['nodes']}
    assert [n['id'] for n in old['nodes']] == [n['id'] for n in new['nodes']]
    changes = []
    for prev in old['nodes']:
        node = by_id[prev['id']]
        keys = sorted(k for k in prev.keys() | node.keys() if prev.get(k) != node.get(k))
        assert set(keys) <= {'source_ids', 'publication_role'}, (node['id'], keys)
        if keys:
            assert node['id'] in batch['expected_node_fingerprints']
            assert node['publication_role'] == 'research_journal'
            assert set(prev['source_ids']) <= set(node['source_ids'])
            changes.append(dict(journal_id=node['id'], label=node['label'], fields=keys))
    assert not validate_catalogue(new, after['nodes'])
    assert new == make_catalogue()
    assert new == json.loads((ROOT / 'data/journal-catalogue/catalogue.json').read_text())
    matrix = []
    for subject in new['nodes']:
        if subject['entry_kind'] != 'publication_subject':
            continue
        rows = [r for r in new['subject_classifications'] if r['subject_id'] == subject['id']]
        checked = sorted({r['journal_id'] for r in rows if r.get('status', 'checked') == 'checked'})
        provisional = sorted({r['journal_id'] for r in rows if r.get('status') == 'provisional'} - set(checked))
        matrix.append(dict(subject_id=subject['id'], category_path=subject['category_path'],
                           checked_candidate_count=len(checked), checked_journal_ids=checked,
                           provisional_only_candidate_count=len(provisional),
                           provisional_only_journal_ids=provisional,
                           atlas_node_ids=subject.get('atlas_node_ids', []),
                           classification_ids=[r['id'] for r in rows]))
    findings = []
    selections = [
        ('public_history', 'Heritage and public history', ['journal_d990835e95820881'],
         ['oral/public_authority', 'memory/urban_landscape_practice', 'geography/urban_public_history'],
         'Dedicated account of professional/public practice and its methods; existing public-memory and oral-history approaches remain relevant.'),
        ('medical_history', 'Medicine and health', ['journal_6d9388bf4f2e1a99'],
         ['epistemology/concepts_norms', 'science/african_health_healing', 'science/human_sciences_professions', 'africanhist/health_healing'],
         'Dedicated field trajectory connecting professional, social, patient and colonial histories; Roy Porter and African healing are already represented.'),
        ('urban_history', 'Urban', ['journal_2b8522c13948819d', 'journal_97cc033e49a4f22b'],
         ['environment/urban_hinterland', 'geography/urban_public_history', 'memory/urban_landscape_practice', 'queer/communities'],
         'Dedicated account of urban historiography and its methodological disagreements; cities already occur in several substantive approaches.')]
    atlas = {n['id']: n for n in after['nodes']}
    for key, label, journals, approaches, decision in selections:
        subject = next(s for s in matrix if s['category_path'][-1] == label)
        for jid in journals:
            assert by_id[jid]['entry_kind'] == 'periodical'
        for path in approaches:
            parent, strand = path.split('/')
            assert any(s['id'] == strand for s in atlas[parent]['strands'])
        findings.append(dict(id=key, priority='strong_candidate_for_dedicated_entry',
                             subject_id=subject['subject_id'], checked_candidate_count=subject['checked_candidate_count'],
                             example_journal_ids=journals, existing_approaches=approaches,
                             assessment=decision, evidence_report='founding-and-gaps-v1.112.md',
                             edge_status='deferred_until_a_sourced_target_entry_exists'))
    result = dict(revision='1.112', reviewed_on='2026-09-15',
                  historical_nodes=len(after['nodes']), historical_edges=len(after['edges']),
                  historical_content_unchanged=True, previous_venue_edges_unchanged=True,
                  dates_bibliography_subjects_unchanged=True, catalogue_reproduces=True,
                  candidate_ids_unchanged=True, journal_edges_before=len(old['edges']),
                  journal_edges_after=len(new['edges']), added_edges=batch['edges'],
                  added_source_ids=[s['id'] for s in batch['sources']], changed_journals=changes,
                  findings=findings, subject_matrix=matrix,
                  limitations=['Subject counts are checked candidate classifications, not worldwide totals or a ranking.',
                               'Examples are selected independently and need not carry the counted category.',
                               'A missing correspondence is a review lead, not proof of missing historical content.',
                               'Gap priorities are editorial assessments supported and qualified in the report.'])
    output = ROOT / 'feedback/journals/founding-and-gaps-v1.112.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'Preservation and rebuild checks passed; {len(matrix)} subject categories; {len(findings)} priority gaps.')


if __name__ == '__main__':
    main()
