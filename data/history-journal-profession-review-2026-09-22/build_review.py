"""Rebuild the editorial working selection from the frozen Crossref ORCID index."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import duckdb
from decisions import DECISIONS

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'history-orcid-fanout-2026-09-22'
DATABASE = SOURCE / 'generated/v1/orcid-index.duckdb'
DEMO = '0000-0002-1825-0097'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(name, rows):
    with (HERE / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()})


def main():
    before_hash = sha256(DATABASE)
    inventory = json.loads((HERE / 'inventory.json').read_text())
    selection = json.loads((SOURCE / 'selection.json').read_text())
    assert len(inventory) == len(selection['journals']) == len(DECISIONS) == 819
    assert [r['journal_key'] for r in inventory] == [r['journal_key'] for r in selection['journals']]
    assert [r['review_number'] for r in inventory] == list(range(1, 820))
    con = duckdb.connect(str(DATABASE), read_only=True)
    venue_ids = {}
    venue_records = {}
    for key, identifier, record in con.execute('''
        SELECT DISTINCT m.journal_key, e.orcid_id, e.record_id
        FROM journal_memberships m JOIN orcid_evidence e USING(record_id)
        WHERE e.orcid_id <> ?
    ''', [DEMO]).fetchall():
        venue_ids.setdefault(key, set()).add(identifier)
        venue_records.setdefault(key, set()).add(record)
    reasons = {
        'likely_core': 'Editorial estimate: history or historical social science is the defining scholarly focus; likely historian-dominated for this working screen.',
        'mixed': 'Historical scholarship overlaps another disciplinary community; a historian or historical-social-scientist majority is not established.',
        'other_primary_community': 'Editorial estimate: another disciplinary community is primary; omit from the historian-focused working selection.',
        'uncertain': 'Insufficient scope evidence for a confident community estimate; hold for further review.',
    }
    reviewed = []
    group_ids = {}
    group_records = {}
    for row in inventory:
        decision = DECISIONS[row['review_number']]
        category = decision['category']
        exclusions = decision.get('exclusions', [])
        group = 'excluded' if exclusions or category == 'other_primary_community' else category
        key = row['journal_key']
        group_ids.setdefault(group, set()).update(venue_ids.get(key, set()))
        group_records.setdefault(group, set()).update(venue_records.get(key, set()))
        reason = decision.get('reason', reasons[category])
        if exclusions:
            reason += ' Applied user exclusion: ' + ', '.join(exclusions) + '.'
        reviewed.append({
            **row,
            'community_assessment': category,
            'working_group': group,
            'include_in_working_selection': group == 'likely_core',
            'exclusions': exclusions,
            'reason': reason,
            'evidence_basis': decision.get('evidence_basis', 'editorial_title_and_catalogue_subject_screen'),
            'scope_source_url': decision.get('scope_source_url', ''),
            'review_status': 'provisional_venue_screen_not_contributor_census',
            'reviewed_on': '2026-09-22',
            'non_demo_distinct_orcids': len(venue_ids.get(key, set())),
        })
    assert len({r['journal_key'] for r in reviewed}) == 819
    write_json('journal-review.json', reviewed)
    fields = ['review_number', 'journal_key', 'label', 'working_group', 'include_in_working_selection',
              'community_assessment', 'exclusions', 'subject_labels', 'publication_records',
              'non_demo_distinct_orcids', 'reason', 'evidence_basis', 'scope_source_url', 'review_status']
    write_csv('journal-review.csv', [{k: r[k] for k in fields} for r in reviewed])
    selected = [r for r in reviewed if r['include_in_working_selection']]
    selected_keys = {r['journal_key'] for r in selected}
    write_json('selected-journals.json', {
        'scope': 'Likely historian or historical-social-scientist majority; explicit archaeology, politics and general area-studies exclusions; provisional venue screen.',
        'source_selection_sha256': sha256(SOURCE / 'selection.json'),
        'journals': [r for r in selection['journals'] if r['journal_key'] in selected_keys],
    })
    write_csv('selected-journals.csv', [{k: r[k] for k in fields} for r in selected])
    con.execute('CREATE TEMP TABLE selected_venues(journal_key VARCHAR PRIMARY KEY)')
    con.executemany('INSERT INTO selected_venues VALUES (?)', [(key,) for key in sorted(selected_keys)])
    con.execute('''CREATE TEMP TABLE selected_evidence AS
        SELECT e.* FROM orcid_evidence e WHERE orcid_id <> ? AND EXISTS (
            SELECT 1 FROM journal_memberships m JOIN selected_venues s USING(journal_key)
            WHERE m.record_id = e.record_id)''', [DEMO])
    cursor = con.execute('''SELECT e.orcid_id,
        string_agg(DISTINCT e.name, ' | ' ORDER BY e.name) AS selected_deposited_names,
        count(DISTINCT e.record_id) AS selected_publication_records,
        count(DISTINCT e.credit_id) AS selected_contributor_credits,
        max(r.publication_year) AS latest_selected_publication_year,
        count(DISTINCT CASE WHEN r.publication_year >= 2020 THEN e.record_id END) AS selected_records_since_2020,
        bool_or(e.authenticated_orcid_deposited) AS any_selected_deposited_authenticated_flag
        FROM selected_evidence e JOIN records r USING(record_id)
        GROUP BY e.orcid_id ORDER BY e.orcid_id''')
    columns = [d[0] for d in cursor.description]
    candidates = [dict(zip(columns, row)) for row in cursor.fetchall()]
    flags = {}
    with (SOURCE / 'orcid-quality-flags.csv').open() as stream:
        for row in csv.DictReader(stream):
            flags.setdefault(row['orcid_id'], []).append(row['flag'])
    for row in candidates:
        row['identity_status'] = 'unreviewed'
        row['quality_flags'] = flags.get(row['orcid_id'], [])
    write_csv('orcid-candidates.csv', candidates)
    evidence_path = str(HERE / 'generated/selected-orcid-evidence.csv')
    (HERE / 'generated').mkdir(exist_ok=True)
    con.execute('''COPY (SELECT * FROM selected_evidence ORDER BY credit_evidence_id)
        TO $destination (HEADER, FORMAT CSV)''', {'destination': evidence_path})
    all_ids = set().union(*group_ids.values())
    core_ids = group_ids['likely_core']
    outside_ids = set().union(*(ids for group, ids in group_ids.items() if group != 'likely_core'))
    assert len(all_ids) == 62495 and DEMO not in all_ids
    assert {r['orcid_id'] for r in candidates} == core_ids
    assert len(candidates) == len(core_ids)
    assert not any(r['exclusions'] for r in selected)
    assert any(r['review_number'] == 406 for r in selected)
    assert sha256(DATABASE) == before_hash
    groups = {}
    for group in ('likely_core', 'mixed', 'uncertain', 'excluded'):
        rows = [r for r in reviewed if r['working_group'] == group]
        groups[group] = {
            'journal_title_contexts': len(rows),
            'contexts_with_non_demo_orcids': sum(r['non_demo_distinct_orcids'] > 0 for r in rows),
            'distinct_non_demo_orcids': len(group_ids.get(group, set())),
            'distinct_publication_records_with_non_demo_orcids': len(group_records.get(group, set())),
        }
    summary = {
        'review_date': '2026-09-22',
        'method': 'Every numbered title and available catalogue subject metadata screened editorially; targeted primary-source scope checks. Contributor self-identification not surveyed; not an exhaustive publisher-scope audit.',
        'groups': groups,
        'explicit_exclusion_contexts_by_reason_nonadditive': dict(Counter(x for r in reviewed for x in r['exclusions'])),
        'explicit_exclusion_contexts_union': sum(bool(r['exclusions']) for r in reviewed),
        'broad_non_demo_orcids': len(all_ids),
        'selected_non_demo_orcids': len(core_ids),
        'selected_orcids_with_selected_evidence_since_2020': sum(r['selected_records_since_2020'] > 0 for r in candidates),
        'selected_orcids_with_any_selected_deposited_authenticated_flag': sum(bool(r['any_selected_deposited_authenticated_flag']) for r in candidates),
        'selected_orcids_also_in_other_groups': len(core_ids & outside_ids),
        'orcids_only_outside_selection': len(all_ids - core_ids),
        'selected_orcids_with_existing_quality_flags': [r['orcid_id'] for r in candidates if r['quality_flags']],
        'source_index_sha256': before_hash,
        'source_selection_sha256': sha256(SOURCE / 'selection.json'),
        'inventory_sha256': sha256(HERE / 'inventory.json'),
        'decisions_sha256': sha256(HERE / 'decisions.py'),
        'validation': {'all_819_contexts_assigned_once': True, 'selection_matches_source_keys': True,
                       'candidate_ids_exactly_match_selected_venue_evidence': True,
                       'demonstration_orcid_excluded': True, 'explicit_exclusions_absent_from_selection': True,
                       'journal_of_british_studies_retained': True, 'source_database_hash_unchanged': True},
        'caveats': ['Groups overlap in people and cannot be added to obtain distinct people.',
                    'Title contexts include predecessors and editions, not 819 independent current journals.',
                    'ORCID deposits are unreviewed identity assertions; publication genre is unclassified.',
                    'Historical subfield journals include historians of art, law, education, science and economic thought.',
                    'Selected publication evidence does not establish employment, occupation, current activity or distinction.'],
    }
    write_json('summary.json', summary)
    print(json.dumps(summary, indent=2))
    con.close()


if __name__ == '__main__':
    main()
