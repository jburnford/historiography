"""Check the reviewed 1.223 subset without treating the whole queue as complete.

These checks bind the accepted delta to independent dossier reviews, rather than
using the resulting degree or an edge quota as evidence of completed research.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch, EDGE_KEYS, serial

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/field-research/dedicated-historians-resumed-2026-10-28'
PACKET_DIR = ROOT / 'data/extension-2026/dedicated-historians-resumed-2026-10-28-batch18'
SELECTION = AUDIT / 'publication-selection-1.223.json'
OWNER_FILES = {'context.json', 'proposals.json', 'sources.json', 'held-cases.json',
               'case-review.json', 'README.md'}
STATUSES = {'supporting_page_checked', 'bibliographic_metadata_checked', 'not_checked'}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def claim_key(edge):
    pair = (edge['source'], edge['target'])
    if edge['relationship_kind'] == 'comparison':
        pair = tuple(sorted(pair))
    return (*pair, edge['relationship_kind'])


class HistorianResumed1223Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = read(SELECTION)
        cls.spacing = read(PACKET_DIR / 'text-spacing.json')
        cls.subjects = cls.selection['person_ids']
        cls.request = read(AUDIT / 'request-baseline.json')
        cls.manifest = read(PACKET_DIR / 'manifest.json')
        cls.verification = read(PACKET_DIR / 'verification.json')
        cls.batch = Batch(PACKET_DIR)
        cls.packet = read(cls.batch.packet)
        cls.receipt = read(cls.batch.out / 'acceptance.json')
        cls.before = cls.batch.baseline()
        # This checks the accepted historical revision even after later releases.
        cls.after = cls.batch.check()
        cls.added = cls.after['edges'][len(cls.before['edges']):]
        cls.proposals, cls.new_sources, cls.addenda = {}, {}, {}
        cls.new_source_addenda = {}
        cls.proposal_owners = {}
        old_source_ids = {row['id'] for row in cls.before['sources']}
        for subject in cls.subjects:
            for proposal in read(AUDIT / subject / 'proposals.json')['proposals']:
                pid = proposal['proposal_id']
                if pid in cls.proposals:
                    raise AssertionError('Repeated dossier proposal ID: ' + pid)
                cls.proposals[pid] = proposal
                cls.proposal_owners[pid] = subject
            doc = read(AUDIT / subject / 'sources.json')
            for row in doc['sources']:
                source = row.get('source_record', row)
                sid = source['id']
                if sid in cls.new_sources and cls.new_sources[sid] != source:
                    raise AssertionError('Conflicting source identity: ' + sid)
                cls.new_sources[sid] = source
            for sid, note in doc.get('source_addenda', {}).items():
                if sid in old_source_ids:
                    cls.addenda.setdefault(sid, []).append(note)
                else:
                    cls.new_source_addenda.setdefault(sid, []).append(
                        {'person_id': subject, 'verification': note})

    def test_publication_selection_is_a_pinned_subset_of_the_original_request(self):
        self.assertEqual(self.selection['baseline_revision'], '1.222')
        self.assertEqual(self.selection['research_baseline_graph_sha256'],
                         self.request['baseline_graph_sha256'])
        self.assertEqual(len(self.subjects), len(set(self.subjects)))
        self.assertTrue(self.subjects)
        self.assertLess(len(self.subjects), len(self.request['remaining_person_ids']))
        self.assertLessEqual(set(self.subjects), set(self.request['remaining_person_ids']))
        remaining = self.selection['remaining_person_ids']
        self.assertEqual(len(remaining), len(set(remaining)))
        self.assertFalse(set(self.subjects).intersection(remaining))
        self.assertFalse(set(self.subjects) & set(self.selection['previously_implemented_person_ids']))
        self.assertEqual(set(self.subjects) | set(remaining) | set(self.selection['previously_implemented_person_ids']),
                         set(self.request['remaining_person_ids']))
        self.assertEqual(self.verification['reviewed_dossiers'], len(self.subjects))
        self.assertEqual(self.verification['remaining_priority_dossiers'], len(remaining))
        self.assertEqual(self.manifest['person_ids'], self.subjects)
        self.assertFalse(set(self.subjects) & set(self.request['excluded_person_ids']))
        self.assertEqual(len(self.subjects), 3)
        self.assertEqual(self.before['revision_history'][-1]['version'], '1.222')
        self.assertEqual(hashlib.sha256(serial(self.before).encode()).hexdigest(),
                         self.selection['baseline_graph_sha256'])
        self.assertEqual({k: len(self.before[k]) for k in self.selection['baseline_counts']},
                         self.selection['baseline_counts'])
        # The published selection itself must be a frozen input, not inferred
        # later from whoever happens to have enough relationships.
        relative = str(SELECTION.relative_to(ROOT))
        self.assertEqual(self.manifest['input_sha256'][relative], sha(SELECTION))

    def test_every_selected_dossier_has_an_exact_independent_pass(self):
        inputs = self.manifest['input_sha256']
        for subject in self.subjects:
            folder = AUDIT / subject
            review = read(folder / 'independent-review.json')
            self.assertEqual(review['person_id'], subject)
            self.assertTrue(review['verdict'].lower().startswith('pass'), subject)
            self.assertFalse(review.get('blocking_findings'), subject)
            self.assertLessEqual(OWNER_FILES, set(review['reviewed_sha256']), subject)
            for filename, digest in review['reviewed_sha256'].items():
                self.assertNotIn('raw', Path(filename).parts)
                path = folder / filename
                self.assertEqual(sha(path), digest, (subject, filename))
                self.assertEqual(inputs[str(path.relative_to(ROOT))], digest,
                                 (subject, filename, 'not frozen in merged manifest'))
            path = folder / 'independent-review.json'
            self.assertEqual(inputs[str(path.relative_to(ROOT))], sha(path))
            proposals = read(folder / 'proposals.json')
            self.assertEqual(proposals['person_id'], subject)
            self.assertEqual(len(proposals['proposals']), review['proposal_count'])
            self.assertEqual(read(folder / 'context.json')['baseline_graph_sha256'],
                             self.request['baseline_graph_sha256'])
            self.assertTrue(review.get('passage_checks'), subject)

    def test_source_access_and_spacing_are_bound_to_reviewed_inputs(self):
        for subject in self.subjects:
            access = read(AUDIT / subject / 'source-access-review-2026-10-30.json')
            review = read(AUDIT / subject / 'independent-review.json')
            self.assertEqual(access['verdict'], 'pass')
            self.assertEqual(access['reviewed_sha256'], review['reviewed_sha256'])
            self.assertFalse(access['blocking_findings'])
        for key, row in self.spacing.items():
            self.assertEqual(row['old'].replace(' ', ''), row['new'].replace(' ', ''), key)
        from scripts.source_hosts import findings
        self.assertFalse(findings(json.dumps(self.packet, ensure_ascii=False)))

    def test_frozen_packet_and_receipt_reconstruct_the_exact_accepted_delta(self):
        freeze = read(PACKET_DIR / 'freeze.json')
        for name, digest in freeze['files_sha256'].items():
            self.assertEqual(sha(PACKET_DIR / name), digest, name)
        for name, digest in self.manifest['input_sha256'].items():
            self.assertEqual(sha(ROOT / name), digest, name)
        self.assertEqual(sha(self.batch.packet), self.receipt['packet_sha256'])
        self.assertEqual(sha(self.batch.packet), freeze['packet_sha256'])
        self.assertEqual(self.receipt['revision'], '1.223')
        self.assertEqual(self.packet['baseline_revision'], '1.222')
        self.assertEqual(self.after['revision_history'][-1]['version'], '1.223')
        digest = hashlib.sha256(serial(self.after).encode()).hexdigest()
        self.assertEqual(digest, self.receipt['production_sha256'])
        self.assertEqual(digest, self.verification['expected_production_sha256'])
        self.assertEqual(self.receipt['baseline_sha256'], self.selection['baseline_graph_sha256'])
        for table, length in self.receipt['previous_table_lengths'].items():
            self.assertEqual(length, len(self.before[table]), table)
        self.assertEqual(self.verification['counts'],
                         {k: len(self.after[k]) for k in self.verification['counts']})
        self.assertEqual(self.verification['new_edges'], len(self.added))
        self.assertEqual(self.verification['new_sources'], len(self.packet['sources']))
        self.assertEqual(self.verification['source_addenda'], len(self.packet['source_addenda']))

    def test_each_published_claim_retains_the_exact_approved_evidence(self):
        packet_edges = {e['proposal_id']: e for e in self.packet['edges']}
        accepted_edges = {e['proposal_id']: e for e in self.added}
        self.assertEqual(set(packet_edges), set(self.proposals))
        self.assertEqual(set(accepted_edges), set(self.proposals))
        normalizations = {
            pid: dict(person_id=self.proposal_owners[pid],
                      **{'from': 'connection', 'to': 'critique'})
            for pid, row in self.proposals.items()
            if row['relationship_kind'] == 'critique' and row['type'] == 'connection'
        }
        self.assertEqual(self.manifest.get('legacy_type_normalizations', {}), normalizations)
        for pid, proposal in self.proposals.items():
            edge, accepted = packet_edges[pid], accepted_edges[pid]
            for field in EDGE_KEYS:
                if proposal.get(field) is not None:
                    expected = (normalizations[pid]['to']
                                if field == 'type' and pid in normalizations
                                else proposal[field])
                    if field in ('relationship', 'evidence_note'):
                        expected = self.spacing.get(f'edges|{pid}|{field}', {}).get('new', expected)
                    self.assertEqual(edge.get(field), expected, (pid, field))
            self.assertEqual({k: v for k, v in accepted.items() if k != 'id'}, edge, pid)
            # Exact evidence_note preservation protects mediator, coauthor,
            # edition, speaker and access qualifications together, instead of
            # checking a few hand-picked words that could still hide omissions.
            self.assertTrue(proposal['evidence_note'].strip(), pid)
            self.assertTrue(proposal['primary_locators'], pid)
            self.assertTrue(proposal['source_ids'], pid)
            self.assertEqual(edge['directed'], edge['relationship_kind'] != 'comparison', pid)
            self.assertEqual(edge['type'],
                             'critique' if edge['relationship_kind'] == 'critique' else 'connection', pid)
            self.assertTrue(set(self.subjects).intersection((edge['source'], edge['target'])), pid)

    def test_existing_endpoints_and_distinct_claim_categories_are_preserved(self):
        nodes = {n['id'] for n in self.before['nodes']}
        old = {claim_key(e) for e in self.before['edges']}
        added = [claim_key(e) for e in self.added]
        self.assertEqual(len(added), len(set(added)))
        self.assertFalse(old.intersection(added))
        for edge in self.added:
            self.assertIn(edge['source'], nodes)
            self.assertIn(edge['target'], nodes)
            # Queue exclusion does not ban another subject's bounded resource.
            self.assertNotIn('alexis_de_tocqueville', self.subjects)
        tocqueville = 'alexis_de_tocqueville'
        self.assertEqual(next(n for n in self.before['nodes'] if n['id'] == tocqueville),
                         next(n for n in self.after['nodes'] if n['id'] == tocqueville))
        ids = [e['id'] for e in self.after['edges']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.before['edges'], self.after['edges'][:len(self.before['edges'])])

    def test_only_edge_cited_new_sources_enter_production(self):
        old_ids = {s['id'] for s in self.before['sources']}
        cited = {sid for edge in self.added for sid in edge['source_ids']}
        expected = {sid: deepcopy(source) for sid, source in self.new_sources.items() if sid in cited}
        crosswalk = self.manifest.get('new_source_reading_addenda', {})
        self.assertEqual(set(crosswalk), set(self.new_source_addenda))
        for sid, owner_rows in self.new_source_addenda.items():
            self.assertIn(sid, expected)
            original = self.new_sources[sid]
            prefix = original.get('verification', {}).get('note', '')
            normalized_rows = []
            for row in owner_rows:
                note = deepcopy(row['verification'])
                if isinstance(note, str):
                    note = dict(status='supporting_page_checked',
                                checked_on=self.packet['prepared'], note=note)
                if prefix and note['note'].startswith(prefix):
                    note['note'] = note['note'][len(prefix):].strip()
                normalized_rows.append(dict(person_id=row['person_id'], verification=note))
                verification = expected[sid].setdefault('verification', {})
                verification['note'] = (verification.get('note', '') +
                    f" Addendum {note['checked_on']}: {note['note']}").strip()
                if note['status'] == 'supporting_page_checked':
                    verification['status'] = note['status']
                    verification['checked_on'] = note['checked_on']
            self.assertEqual(crosswalk[sid], normalized_rows, sid)
        for sid, source in expected.items():
            for field in ('title', 'citation'):
                source[field] = self.spacing.get(f'sources|{sid}|{field}', {}).get('new', source[field])
            source['verification']['note'] = self.spacing.get(f'sources|{sid}|verification.note', {}).get('new', source['verification']['note'])
        actual = {s['id']: s for s in self.packet['sources']}
        self.assertFalse(old_ids.intersection(actual))
        self.assertEqual(actual, expected)
        self.assertEqual(set(self.manifest['excluded_uncited_new_sources']),
                         set(self.new_sources) - set(expected))
        self.assertEqual(self.manifest['new_source_count'], len(expected))
        self.assertEqual(self.manifest['new_edge_count'], len(self.proposals))
        self.assertLessEqual(cited, old_ids | set(actual))
        self.assertEqual(self.after['sources'][len(self.before['sources']):], self.packet['sources'])
        for sid, source in actual.items():
            self.assertIn(source['verification']['status'], STATUSES, sid)
            self.assertTrue(source['verification']['note'].strip(), sid)
            self.assertTrue(source.get('url'), sid)
        all_sources = {s['id']: s for s in self.after['sources']}
        for edge in self.added:
            self.assertTrue(any(all_sources[sid].get('verification', {}).get('status')
                                == 'supporting_page_checked' for sid in edge['source_ids']),
                            edge['proposal_id'])

    def test_old_source_records_receive_only_exact_append_only_reading_notes(self):
        current = {s['id']: s for s in self.after['sources']}
        prior = self.receipt['prior_records']['sources']
        self.assertEqual(set(prior), set(self.packet['source_addenda']))
        self.assertEqual(set(self.packet['source_addenda']), set(self.addenda))
        for old in self.before['sources']:
            after = deepcopy(current[old['id']])
            add = self.packet['source_addenda'].get(old['id'])
            if add:
                self.assertEqual(prior[old['id']], old)
                prefix = old.get('verification', {}).get('note', '')
                expected = (prefix + f" Addendum {add['checked_on']}: {add['note']}").strip()
                self.assertEqual(after['verification']['note'], expected)
                for owner_add in self.addenda[old['id']]:
                    note = owner_add if isinstance(owner_add, str) else owner_add['note']
                    if prefix and note.startswith(prefix):
                        note = note[len(prefix):].strip()
                    owners = [pid for pid in self.subjects if old['id'] in read(AUDIT / pid / 'sources.json').get('source_addenda', {})]
                    for owner in owners:
                        note = self.spacing.get(f'addenda|{old["id"]}|{owner}', {}).get('new', note)
                    self.assertIn(note, add['note'], old['id'])
                expected_status = (add['status'] if add['status'] == 'supporting_page_checked'
                                   else old.get('verification', {}).get('status'))
                self.assertEqual(after['verification'].get('status'), expected_status)
                if add['status'] == 'supporting_page_checked':
                    self.assertEqual(after['verification']['checked_on'], add['checked_on'])
                after['verification'] = old.get('verification', {})
            self.assertEqual(after, old, old['id'])

    def test_no_biography_field_identity_or_dissertation_data_are_changed(self):
        # Whole-table equality also protects all existing group rosters,
        # biography/life facts, work chronologies, layers, claims and any
        # dissertation-derived counts without guessing their field names.
        self.assertEqual(set(self.before), set(self.after))
        for field in set(self.before) - {'edges', 'sources', 'revision_history'}:
            self.assertEqual(self.before[field], self.after[field], field)
        self.assertEqual(self.before['revision_history'], self.after['revision_history'][:-1])
        for field in ('nodes', 'people_updates', 'new_people', 'roster_edges', 'edge_revisions',
                      'roster_additions', 'text_revisions', 'field_sets', 'layers_set',
                      'periods_set', 'source_field_sets', 'node_list_additions', 'claim_reviews',
                      'strand_list_additions', 'new_strands', 'roster_list_additions'):
            self.assertFalse(self.packet.get(field), field)
        self.assertEqual(self.receipt['counts']['new_person_entries'], 0)
        self.assertEqual(self.receipt['counts']['new_edges'], len(self.proposals))
        self.assertEqual(self.receipt['counts']['new_sources'], len(self.packet['sources']))
        self.assertEqual(self.receipt['counts']['source_addenda'], len(self.packet['source_addenda']))


if __name__ == '__main__':
    unittest.main()
